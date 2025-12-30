from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from jobs.clients.exceptions import JobFetcherClientError
from jobs.models import Company, JobListing, SearchConfig
from jobs.services import JobFetcherService
from jobs.services.exceptions import JobFetcherServiceError
from tracker.models import Job


class TestJobFetcherService(TestCase):
    DEFAULT_COMPANY_NAME = "Acme"
    DEFAULT_SEARCH_TERM = "Software Engineer"
    DEFAULT_JOB_ID = "JOB-1"

    def setUp(self):
        self.company = Company.objects.create(name=self.DEFAULT_COMPANY_NAME)
        self.search_config = SearchConfig.objects.create(search_term=self.DEFAULT_SEARCH_TERM)

        patcher = patch("jobs.services.job_fetcher_service.Company.get_job_fetcher")
        self.mock_get_fetcher = patcher.start()
        self.addCleanup(patcher.stop)

        self.mock_client = Mock()
        self.mock_client.fetch_jobs.return_value = [
            {
                "external_id": self.DEFAULT_JOB_ID,
                "title": self.DEFAULT_SEARCH_TERM,
                "location": "Seattle, WA",
                "url_path": "/job/1",
                "posted_on": "2024-01-01",
            }
        ]

        self.expected_stats_key = "Acme - Software Engineer"

        self.mock_get_fetcher.return_value = self.mock_client

        self.service = JobFetcherService()

    def test_fetch_and_sync_jobs_creates_new_job_listing(self):
        stats = self.service.fetch_and_sync_jobs()
        
        self.assertIn(self.expected_stats_key, stats)
        self.assertEqual(
            stats[self.expected_stats_key],
            {
                "new": 1,
                "updated": 0,
                "total": 1,
            }
        )

        job = JobListing.objects.get(
            company=self.company,
            external_id=self.DEFAULT_JOB_ID,
        )

        self.assertEqual(job.title, self.DEFAULT_SEARCH_TERM)
        self.assertFalse(job.is_stale)

    def test_fetch_and_sync_jobs_updates_existing_job_listing(self):
        JobListing.objects.create(
            company=self.company,
            external_id=self.DEFAULT_JOB_ID,
            title="Old Title",
            is_stale=False,
        )

        stats = self.service.fetch_and_sync_jobs()

        self.assertEqual(
            stats[self.expected_stats_key],
            {
                "new": 0,
                "updated": 1,
                "total": 1,
            }
        )

        job = JobListing.objects.get(external_id=self.DEFAULT_JOB_ID)
        self.assertEqual(job.title, self.DEFAULT_SEARCH_TERM)
        self.assertFalse(job.is_stale)

    def test_fetch_and_sync_jobs_marks_missing_jobs_as_stale(self):
        JobListing.objects.create(
            company=self.company,
            external_id="JOB-OLD",
            is_stale=False,
        )
        self.mock_client.fetch_jobs.return_value = []

        stats = self.service.fetch_and_sync_jobs()

        self.assertEqual(
            stats[self.expected_stats_key],
            {
                "new": 0,
                "updated": 0,
                "total": 0,
            }
        )

        job = JobListing.objects.get(external_id="JOB-OLD")
        self.assertTrue(job.is_stale)

    def test_fetch_and_sync_jobs_handles_client_error(self):
        self.mock_client.fetch_jobs.side_effect = JobFetcherClientError("API failure")

        stats = self.service.fetch_and_sync_jobs()

        self.assertEqual(
            stats,
            {
                self.expected_stats_key: {
                    "error": "API failure"
                }
            }
        )
        self.assertEqual(JobListing.objects.count(), 0)

    def test_fetch_and_sync_jobs_raises_service_error_on_unexpected_exception(self):
        self.mock_client.fetch_jobs.side_effect = RuntimeError("boom")

        with self.assertRaises(JobFetcherServiceError):
            self.service.fetch_and_sync_jobs()

    def test_cleanup_stale_jobs_deletes_old_stale_jobs(self):
        days_old = JobFetcherService.STALE_JOB_CLEANUP_DAYS + 1
        JobListing.objects.create(
            company=self.company,
            external_id="JOB-STALE",
            last_fetched=timezone.now() - timezone.timedelta(days=days_old),
            is_stale=True,
        )
        self.mock_client.fetch_jobs.return_value = []

        self.service.fetch_and_sync_jobs()

        self.assertFalse(
            JobListing.objects.filter(external_id="JOB-STALE").exists()
        )

    def test_fetch_and_sync_jobs_sets_status_applied_for_existing_tracker_job(self):
        Job.objects.create(
            company="Acme",
            external_job_id=self.DEFAULT_JOB_ID,
        )

        stats = self.service.fetch_and_sync_jobs()

        self.assertEqual(
            stats[self.expected_stats_key],
            {
                "new": 1,
                "updated": 0,
                "total": 1,
            }
        )
        job = JobListing.objects.get(external_id=self.DEFAULT_JOB_ID)
        self.assertEqual(job.status, JobListing.Status.APPLIED)

    def test_fetch_and_sync_jobs_sets_status_new_for_non_applied_job(self):
        self.service.fetch_and_sync_jobs()
        
        job = JobListing.objects.get(external_id=self.DEFAULT_JOB_ID)
        self.assertEqual(job.status, JobListing.Status.NEW)

    def test_fetch_and_sync_jobs_updates_status_to_applied_on_resync(self):
        JobListing.objects.create(
            company=self.company,
            external_id=self.DEFAULT_JOB_ID,
            status=JobListing.Status.NEW,
        )
        Job.objects.create(company=self.company.name, external_job_id=self.DEFAULT_JOB_ID)

        stats = self.service.fetch_and_sync_jobs()

        self.assertEqual(
            stats[self.expected_stats_key],
            {
                "new": 0,
                "updated": 1,
                "total": 1,
            }
        )
        job = JobListing.objects.get(external_id=self.DEFAULT_JOB_ID)
        self.assertEqual(job.status, JobListing.Status.APPLIED)

    def test_fetch_and_sync_jobs_preserves_status_for_non_applied_existing_job(self):
        JobListing.objects.create(
            company=self.company,
            external_id=self.DEFAULT_JOB_ID,
            title="Old Title",
            status=JobListing.Status.INTERESTED,
        )

        self.service.fetch_and_sync_jobs()

        job = JobListing.objects.get(external_id=self.DEFAULT_JOB_ID)
        self.assertEqual(job.status, JobListing.Status.INTERESTED)
        self.assertEqual(job.title, self.DEFAULT_SEARCH_TERM)

    def test_fetch_and_sync_jobs_only_checks_applied_jobs_for_same_company(self):
        other_company = Company.objects.create(
            name="Other Corp",
            active=True,
        )
        Job.objects.create(company=other_company.name, external_job_id=self.DEFAULT_JOB_ID)

        self.service.fetch_and_sync_jobs(company_name=self.DEFAULT_COMPANY_NAME)

        job = JobListing.objects.get(company=self.company, external_id=self.DEFAULT_JOB_ID)
        self.assertEqual(job.status, JobListing.Status.NEW)

    def test_fetch_and_sync_jobs_filters_excluded_terms(self):
        self.search_config.exclude_terms = ["Senior"]
        self.search_config.save(update_fields=["exclude_terms"])
        
        self.mock_client.fetch_jobs.return_value = [
            {
                "external_id": "JOB-1",
                "title": "Software Engineer",
                "location": "Seattle, WA",
                "url_path": "/job/1",
                "posted_on": "2024-01-01",
            },
            {
                "external_id": "JOB-2",
                "title": "Senior Software Engineer",
                "location": "Seattle, WA",
                "url_path": "/job/2",
                "posted_on": "2024-01-01",
            },
        ]
        
        stats = self.service.fetch_and_sync_jobs()
        
        self.assertEqual(
            stats[self.expected_stats_key],
            {
                "new": 1,
                "updated": 0,
                "total": 1,
            }
        )
        
        self.assertTrue(JobListing.objects.filter(external_id="JOB-1").exists())
        self.assertFalse(JobListing.objects.filter(external_id="JOB-2").exists())

    def test_fetch_and_sync_jobs_does_not_sync_inactive_search_configs(self):
        self.search_config.active = False
        self.search_config.save(update_fields=["active"])
        
        stats = self.service.fetch_and_sync_jobs()
        
        self.assertEqual(stats, {})
        self.assertEqual(JobListing.objects.count(), 0)

    def test_fetch_and_sync_jobs_syncs_multiple_search_terms(self):
        SearchConfig.objects.create(search_term="Data Analyst")
        
        stats = self.service.fetch_and_sync_jobs()
        
        self.assertIn(self.expected_stats_key, stats)
        self.assertIn("Acme - Data Analyst", stats)
        self.assertEqual(len(stats), 2)

    def test_fetch_and_sync_jobs_filters_search_configs_by_keywords(self):
        SearchConfig.objects.create(search_term="Data Analyst")
        SearchConfig.objects.create(search_term="Data Engineer")
        
        stats = self.service.fetch_and_sync_jobs(keywords="analyst")
        
        self.assertIn("Acme - Data Analyst", stats)
        self.assertNotIn("Acme - Software Engineer", stats)
        self.assertNotIn("Acme - Data Engineer", stats)
        self.assertEqual(len(stats), 1)

    def test_fetch_and_sync_jobs_filters_search_configs_case_insensitive(self):
        SearchConfig.objects.create(search_term="Data Analyst")
        
        stats = self.service.fetch_and_sync_jobs(keywords="ANALYST")
        
        self.assertIn("Acme - Data Analyst", stats)
        self.assertEqual(len(stats), 1)

    def test_fetch_and_sync_jobs_syncs_multiple_companies_per_search_term(self):
        Company.objects.create(name="Other Company", active=True)
        
        stats = self.service.fetch_and_sync_jobs()
        
        self.assertIn(self.expected_stats_key, stats)
        self.assertIn("Other Company - Software Engineer", stats)
        self.assertEqual(len(stats), 2)

    def test_fetch_and_sync_jobs_does_not_sync_inactive_companies(self):
        self.company.active = False
        self.company.save(update_fields=["active"])
        
        stats = self.service.fetch_and_sync_jobs()
        
        self.assertEqual(stats, {})
        self.assertEqual(JobListing.objects.count(), 0)
