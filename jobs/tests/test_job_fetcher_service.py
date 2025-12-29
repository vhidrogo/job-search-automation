from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from jobs.clients.exceptions import JobFetcherClientError
from jobs.models import Company, JobListing
from jobs.services import JobFetcherService
from jobs.services.exceptions import JobFetcherServiceError


class TestJobFetcherService(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Acme",
            active=True,
        )

        patcher = patch("jobs.services.job_fetcher_service.Company.get_job_fetcher")
        self.mock_get_fetcher = patcher.start()
        self.addCleanup(patcher.stop)

        self.mock_client = Mock()
        self.mock_client.fetch_jobs.return_value = [
            {
                "external_id": "JOB-1",
                "title": "Software Engineer",
                "location": "Seattle, WA",
                "url": "https://example.com/job/1",
                "posted_on": "2024-01-01",
            }
        ]

        self.mock_get_fetcher.return_value = self.mock_client

        self.service = JobFetcherService()

    def test_fetch_and_sync_jobs_creates_new_job_listing(self):
        stats = self.service.fetch_and_sync_jobs()

        self.assertEqual(
            stats,
            {
                "Acme": {
                    "new": 1,
                    "updated": 0,
                    "total": 1,
                }
            }
        )

        job = JobListing.objects.get(
            company=self.company,
            external_id="JOB-1",
        )

        self.assertEqual(job.title, "Software Engineer")
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
                "url": "https://example.com/job/1",
                "posted_on": "2024-01-01",
            }
        ]

        stats = self.service.fetch_and_sync_jobs()

        self.assertEqual(
            stats["Acme"],
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
            external_id="JOB-OLD",
            is_stale=False,
        )

        self.mock_client.fetch_jobs.return_value = []

        stats = self.service.fetch_and_sync_jobs()

        self.assertEqual(
            stats["Acme"],
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
                "Acme": {
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
