from django.test import TestCase

from resume.schemas import RequirementSchema
from tracker.models import Job, Requirement


class TestRequirementModel(TestCase):
    def setUp(self):
        self.job = Job.objects.create()

    def test_bulk_create_from_parsed_creates_requirements(self):
        text1, text2 = "Strong Python skills", "Experience with Django"
        keywords1, keywords2 = ["Python"], ["Django"]
        relevance1, relevance2 = 0.9, 0.8

        requirements = [
            RequirementSchema(
                text=text1,
                keywords=keywords1,
                relevance=relevance1,
            ),
            RequirementSchema(
                text=text2,
                keywords=keywords2,
                relevance=relevance2,
            ),
        ]

        result = Requirement.bulk_create_from_parsed(self.job, requirements)

        self.assertEqual(len(result), 2)
        self.assertTrue(all(r.pk for r in result))
        self.assertTrue(all(r.job == self.job for r in result))

        texts = {r.text for r in result}
        keywords = {tuple(r.keywords) for r in result}
        relevances = {r.relevance for r in result}

        self.assertEqual(texts, {text1, text2})
        self.assertEqual(keywords, {tuple(keywords1), tuple(keywords2)})
        self.assertEqual(relevances, {relevance1, relevance2})

    def test_bulk_create_from_parsed_with_empty_list(self):
        result = Requirement.bulk_create_from_parsed(self.job, [])
        self.assertEqual(len(result), 0)
        self.assertEqual(Requirement.objects.count(), 0)
