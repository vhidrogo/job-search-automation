# tracker/tests/models/test_requirement.py
from typing import List
from django.test import TestCase

from resume.schemas.jd_schema import RequirementSchema
from tracker.models.job import Job, JobLevel, JobRole, WorkSetting
from tracker.models.requirement import Requirement


class TestRequirementModel(TestCase):
    def setUp(self):
        self.job = Job.objects.create(
            company="Meta",
            listing_job_title="Software Engineer",
            role=JobRole.SOFTWARE_ENGINEER,
            level=JobLevel.II,
            location="Remote",
            work_setting=WorkSetting.REMOTE,
        )

    def test_bulk_create_from_parsed_creates_requirements(self):
        """Test that bulk_create_from_parsed correctly creates and persists Requirement instances from RequirementSchema models"""
        parsed_requirements: List[RequirementSchema] = [
            RequirementSchema(text="Strong Python skills", keywords=["Python"], relevance=0.9, order=0),
            RequirementSchema(text="Experience with Django", keywords=["Django"], relevance=0.8, order=1),
        ]

        created_reqs = Requirement.bulk_create_from_parsed(self.job, parsed_requirements)

        # Basic assertions
        self.assertEqual(len(created_reqs), 2)
        self.assertTrue(all(isinstance(r, Requirement) for r in created_reqs))
        self.assertEqual(Requirement.objects.count(), 2)

        # Verify first requirement's fields
        req1 = Requirement.objects.get(order=0, job=self.job)
        self.assertEqual(req1.text, "Strong Python skills")
        self.assertEqual(req1.keywords, ["Python"])
        self.assertAlmostEqual(req1.relevance, 0.9)
        self.assertEqual(req1.order, 0)

        # Verify second requirement's fields
        req2 = Requirement.objects.get(order=1, job=self.job)
        self.assertEqual(req2.text, "Experience with Django")
        self.assertEqual(req2.keywords, ["Django"])
        self.assertAlmostEqual(req2.relevance, 0.8)
        self.assertEqual(req2.order, 1)

    def test_bulk_create_from_parsed_with_empty_list(self):
        """Test that empty list creates no requirements"""
        created_reqs = Requirement.bulk_create_from_parsed(self.job, [])
        self.assertEqual(len(created_reqs), 0)
        self.assertEqual(Requirement.objects.count(), 0)

    def test_bulk_create_from_parsed_respects_batch_size(self):
        """Test that batch_size parameter is passed through"""
        parsed_requirements = [
            RequirementSchema(text=f"Requirement {i}", keywords=[f"Keyword{i}"], relevance=0.5, order=i)
            for i in range(5)
        ]

        created_reqs = Requirement.bulk_create_from_parsed(self.job, parsed_requirements, batch_size=2)
        self.assertEqual(len(created_reqs), 5)
        self.assertEqual(Requirement.objects.count(), 5)
