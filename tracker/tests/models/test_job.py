from typing import List
from django.test import TestCase

from resume.schemas.jd_schema import Metadata
from tracker.models import Job, JobLevel, JobRole, Requirement, WorkSetting


class TestJobModel(TestCase):
    """Test that bulk_create_from_parsed correctly creates and persists Job instances from Metadata models"""
    def test_bulk_create_from_parsed_creates_jobs(self):
        parsed_jobs: List[Metadata] = [
            Metadata(
                company="Meta",
                listing_job_title="Software Engineer",
                role=JobRole.SOFTWARE_ENGINEER,
                specialization="Backend",
                level=JobLevel.II,
                location="Remote",
                work_setting=WorkSetting.REMOTE,
                min_experience_years=3,
                min_salary=120000,
                max_salary=150000,
            ),
            Metadata(
                company="Amazon",
                listing_job_title="Data Engineer",
                role=JobRole.DATA_ENGINEER,
                specialization=None,
                level=JobLevel.I,
                location="Seattle",
                work_setting=WorkSetting.ON_SITE,
                min_experience_years=2,
                min_salary=100000,
                max_salary=130000,
            ),
        ]

        created_jobs = Job.bulk_create_from_parsed(parsed_jobs)

        # Basic assertions
        self.assertEqual(len(created_jobs), 2)
        self.assertTrue(all(isinstance(j, Job) for j in created_jobs))
        self.assertEqual(Job.objects.count(), 2)
        
        # Verify first job's fields
        meta_job = Job.objects.get(company="Meta")
        self.assertEqual(meta_job.role, JobRole.SOFTWARE_ENGINEER)
        self.assertEqual(meta_job.listing_job_title, "Software Engineer")
        self.assertEqual(meta_job.specialization, "Backend")
        self.assertEqual(meta_job.level, JobLevel.II)
        self.assertEqual(meta_job.location, "Remote")
        self.assertEqual(meta_job.work_setting, WorkSetting.REMOTE)
        self.assertEqual(meta_job.min_experience_years, 3)
        self.assertEqual(meta_job.min_salary, 120000)
        self.assertEqual(meta_job.max_salary, 150000)
        
        # Verify second job's fields (especially None values)
        amazon_job = Job.objects.get(company="Amazon")
        self.assertEqual(amazon_job.role, JobRole.DATA_ENGINEER)
        self.assertIsNone(amazon_job.specialization)
        self.assertEqual(amazon_job.level, JobLevel.I)
        
    def test_bulk_create_from_parsed_with_empty_list(self):
        """Test that empty list creates no jobs"""
        created_jobs = Job.bulk_create_from_parsed([])
        self.assertEqual(len(created_jobs), 0)
        self.assertEqual(Job.objects.count(), 0)
    
    def test_bulk_create_from_parsed_respects_batch_size(self):
        """Test that batch_size parameter is passed through"""
        parsed_jobs = [
            Metadata(
                company=f"Company{i}",
                listing_job_title="Engineer",
                role=JobRole.SOFTWARE_ENGINEER,
                level=JobLevel.II,
                location="Remote",
                work_setting=WorkSetting.REMOTE,
            )
            for i in range(5)
        ]
        # This won't fail if batch_size is wrong, but ensures parameter works
        created_jobs = Job.bulk_create_from_parsed(parsed_jobs, batch_size=2)
        self.assertEqual(len(created_jobs), 5)
        self.assertEqual(Job.objects.count(), 5)

    def test_job_can_access_related_requirements(self):
        job = Job.objects.create(
            company="Meta",
            listing_job_title="Software Engineer",
            role=JobRole.SOFTWARE_ENGINEER,
            level=JobLevel.II,
            location="Remote",
            work_setting=WorkSetting.REMOTE,
        )

        Requirement.objects.create(
            job=job,
            text="Python experience",
            keywords="Python",
            relevance=1,
            order=1,
        )
        Requirement.objects.create(
            job=job,
            text="Django experience",
            keywords="Django",
            relevance=.9,
            order=2,
        )

        related = list(job.requirements.order_by("order"))
        self.assertEqual(len(related), 2)
        self.assertEqual(related[0].text, "Python experience")
        self.assertEqual(related[1].text, "Django experience")
