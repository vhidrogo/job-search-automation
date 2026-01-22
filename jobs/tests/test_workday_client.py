import requests
from unittest.mock import Mock, patch

from django.test import TestCase

from jobs.clients import WorkdayClient, WorkdayCompanyConfig
from jobs.clients.exceptions import WorkdayClientError
from jobs.models import Company, WorkdayConfig


class TestWorkdayCompanyConfig(TestCase):
    def test_from_django_model(self):
        django_config = WorkdayConfig(
            company=Company.objects.create(name="Boeing"),
            base_url="https://boeing.wd1.myworkdayjobs.com",
            tenant="boeing",
            site="EXTERNAL_CAREERS",
            location_filters='{"Seattle": "abc"}',
        )

        dataclass_config = WorkdayCompanyConfig.from_django_model(django_config)

        self.assertEqual(dataclass_config.name, django_config.company.name)
        self.assertEqual(dataclass_config.base_url, django_config.base_url)
        self.assertEqual(dataclass_config.tenant, django_config.tenant)
        self.assertEqual(dataclass_config.site, django_config.site)
        self.assertEqual(dataclass_config.location_filters, django_config.location_filters)


class TestWorkdayClient(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.config = WorkdayCompanyConfig(
            name="Nordstrom",
            base_url="https://nordstrom.wd501.myworkdayjobs.com",
            tenant="nordstrom",
            site="nordstrom_careers",
            location_filters={},
        )
        cls.workday_client = WorkdayClient(cls.config)

    def setUp(self):
        patcher = patch("jobs.clients.workday_client.requests.post")
        self.mock_post = patcher.start()
        self.addCleanup(patcher.stop)

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "total": 0,
            "jobPostings": [],
        }

        self.mock_post.return_value = mock_response

    def test_fetch_jobs_returns_normalized_jobs(self):
        self.mock_post.return_value.json.return_value = {
            "total": 1,
            "jobPostings": [
                {
                    "title": "Software Engineer",
                    "locationsText": "Seattle, WA",
                    "externalPath": "/jobs/123",
                    "postedOn": "2024-05-11",
                }
            ]
        }

        jobs = self.workday_client.fetch_jobs()

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["company_name"], self.config.name)
        self.assertEqual(jobs[0]["title"], "Software Engineer")

    def test_fetch_jobs_returns_empty_list_when_no_jobs(self):
        jobs = self.workday_client.fetch_jobs()
        self.assertEqual(jobs, [])

    def test_fetch_jobs_applies_location_filters(self):
        config = WorkdayCompanyConfig(
            name="Company",
            base_url="url",
            tenant="tenant",
            site="site",
            location_filters={
                "Seattle, WA": "abc123",
                "Chicago, IL": "xyz456",
                },
        )
        client = WorkdayClient(config)
        
        client.fetch_jobs()

        _, kwargs = self.mock_post.call_args
        payload = kwargs["json"]
        self.assertEqual(payload["appliedFacets"]["locations"], ["abc123", "xyz456"])

    def test_fetch_jobs_respects_max_results(self):
        self.mock_post.return_value.json.return_value = {
            "total": 2,
            "jobPostings": [
                {"title": "Job 1", "externalPath": "/job/1"},
                {"title": "Job 2", "externalPath": "/job/2"},
            ],
        }

        jobs = self.workday_client.fetch_jobs(max_results=1)

        self.assertEqual(len(jobs), 1)

    def test_fetch_jobs_raises_client_error_on_http_failure(self):
        self.mock_post.return_value.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

        with self.assertRaisesRegex(WorkdayClientError, r"HTTPError"):
            self.workday_client.fetch_jobs()

    def test_fetch_jobs_stops_when_api_returns_no_more_jobs(self):
        self.mock_post.return_value.json.return_value = {
            "jobPostings": [],
            "total": 10,
        }

        jobs = self.workday_client.fetch_jobs()

        self.assertEqual(jobs, [])
        self.assertEqual(self.mock_post.call_count, 1)
