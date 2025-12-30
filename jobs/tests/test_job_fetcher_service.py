from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from jobs.clients.exceptions import JobFetcherClientError
from jobs.models import Company, JobListing, SearchRole, SearchRoleConfig
from jobs.services import JobFetcherService
from jobs.services.exceptions import JobFetcherServiceError
from tracker.models import Job


class TestJobFetcherService(TestCase):
    DEFAULT_COMPANY_NAME = "Acme"

    def setUp(self):
        self.company = Company.objects.create(name=self.DEFAULT_COMPANY_NAME)

        patcher = patch("jobs.services.job_fetcher_service.Company.get_job_fetcher")
        self.mock_get_fetcher = patcher.start()
        self.addCleanup(patcher.stop)

        self.mock_client = Mock()
        self.mock_client.fetch_jobs.return_value = [
            {
                "external_id": "JOB-1",
                "title": "Software Engineer",
                "location": "Seattle, WA",
                "url_path": "/job/1",
                "posted_on": "2024-01-01",
            }
        ]

        self.expected_stats_key = "Acme - Software Engineer"

        self.mock_get_fetcher.return_value = self.mock_client

        self.service = JobFetcherService()

        self.role = SearchRole.SOFTWARE_ENGINEER.value

    def test_fetch_and_sync_jobs_creates_new_job_listing(self):
        stats = self.service.fetch_and_sync_jobs(self.role)
        
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
            external_id="JOB-1",
        )

        self.assertEqual(job.title, "Software Engineer")
        self.assertEqual(job.search_role, self.role)
        self.assertFalse(job.is_stale)

    def test_fetch_and_sync_jobs_updates_existing_job_listing(self):
        JobListing.objects.create(
            company=self.company,
            external_id="JOB-1",
            title="Old Title",
            is_stale=False,
        )

        self.mock_client.fetch_jobs.return_value = [
            {
                "external_id": "JOB-1",
                "title": "Software Engineer",
                "location": "Seattle, WA",
                "url_path": "https://example.com/job/1",
                "posted_on": "2024-01-01",
            }
        ]

        stats = self.service.fetch_and_sync_jobs(self.role)

        self.assertEqual(
            stats[self.expected_stats_key],
            {
                "new": 0,
                "updated": 1,
                "total": 1,
            }
        )

        job = JobListing.objects.get(external_id="JOB-1")
        self.assertEqual(job.title, "Software Engineer")
        self.assertFalse(job.is_stale)

    def test_fetch_and_sync_jobs_marks_missing_jobs_as_stale(self):
        JobListing.objects.create(
            company=self.company,
            search_role=self.role,
            external_id="JOB-OLD",
            is_stale=False,
        )

        self.mock_client.fetch_jobs.return_value = []

        stats = self.service.fetch_and_sync_jobs(self.role)

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

        stats = self.service.fetch_and_sync_jobs(self.role)

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
            self.service.fetch_and_sync_jobs(self.role)

    def test_cleanup_stale_jobs_deletes_old_stale_jobs(self):
        days_old = JobFetcherService.STALE_JOB_CLEANUP_DAYS + 1
        JobListing.objects.create(
            company=self.company,
            external_id="JOB-STALE",
            last_fetched=timezone.now() - timezone.timedelta(days=days_old),
            is_stale=True,
        )
        
        self.mock_client.fetch_jobs.return_value = []

        self.service.fetch_and_sync_jobs(self.role)

        self.assertFalse(
            JobListing.objects.filter(external_id="JOB-STALE").exists()
        )

    def test_fetch_and_sync_jobs_sets_status_applied_for_existing_tracker_job(self):
        external_job_id = "JOB-1"

        Job.objects.create(
            company="Acme",
            external_job_id=external_job_id,
        )

        stats = self.service.fetch_and_sync_jobs(self.role)

        self.assertEqual(
            stats[self.expected_stats_key],
            {
                "new": 1,
                "updated": 0,
                "total": 1,
            }
        )

        job = JobListing.objects.get(external_id=external_job_id)
        self.assertEqual(job.status, JobListing.Status.APPLIED)

    def test_fetch_and_sync_jobs_sets_status_new_for_non_applied_job(self):
        self.service.fetch_and_sync_jobs(self.role)
        
        job = JobListing.objects.get(external_id="JOB-1")
        self.assertEqual(job.status, JobListing.Status.NEW)

    def test_fetch_and_sync_jobs_updates_status_to_applied_on_resync(self):
        external_job_id = "JOB-1"
        JobListing.objects.create(
            company=self.company,
            external_id=external_job_id,
            status=JobListing.Status.NEW,
        )
        Job.objects.create(company=self.company.name, external_job_id=external_job_id)

        stats = self.service.fetch_and_sync_jobs(self.role)

        self.assertEqual(
            stats[self.expected_stats_key],
            {
                "new": 0,
                "updated": 1,
                "total": 1,
            }
        )
        job = JobListing.objects.get(external_id=external_job_id)
        self.assertEqual(job.status, JobListing.Status.APPLIED)

    def test_fetch_and_sync_jobs_preserves_status_for_non_applied_existing_job(self):
        external_job_id = "JOB-1"
        updated_title = "Software Engineer"

        JobListing.objects.create(
            company=self.company,
            external_id=external_job_id,
            title="Old Title",
            status=JobListing.Status.INTERESTED,
        )

        self.service.fetch_and_sync_jobs(self.role)

        job = JobListing.objects.get(external_id=external_job_id)
        self.assertEqual(job.status, JobListing.Status.INTERESTED)
        self.assertEqual(job.title, updated_title)

    def test_fetch_and_sync_jobs_only_checks_applied_jobs_for_same_company(self):
        external_job_id = "JOB-1"
        other_company = Company.objects.create(
            name="Other Corp",
            active=True,
        )
        Job.objects.create(company=other_company.name, external_job_id=external_job_id)

        self.service.fetch_and_sync_jobs(search_role=self.role, company_name=self.DEFAULT_COMPANY_NAME)

        job = JobListing.objects.get(company=self.company, external_id=external_job_id)
        self.assertEqual(job.status, JobListing.Status.NEW)

    def test_fetch_and_sync_jobs_filters_excluded_terms(self):
        SearchRoleConfig.objects.create(
            role=self.role,
            exclude_terms=["Senior", "Staff"],
        )
        
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
        
        stats = self.service.fetch_and_sync_jobs(self.role)
        
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

    def test_fetch_and_sync_jobs_no_exclusions_when_config_missing(self):
        self.mock_client.fetch_jobs.return_value = [
            {
                "external_id": "JOB-1",
                "title": "Senior Software Engineer",
                "location": "Seattle, WA",
                "url_path": "/job/1",
                "posted_on": "2024-01-01",
            },
        ]
        
        stats = self.service.fetch_and_sync_jobs(self.role)
        
        self.assertEqual(
            stats[self.expected_stats_key],
            {
                "new": 1,
                "updated": 0,
                "total": 1,
            }
        )
        
        self.assertTrue(JobListing.objects.filter(external_id="JOB-1").exists())
