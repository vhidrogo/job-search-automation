import unittest

from resume.schemas import RequirementSchema
from resume.utils.prompt_content_builders import build_requirement_json


class TestBuildRequirementJson(unittest.TestCase):
    def test_basic_serialization(self):
        requirements = [
            RequirementSchema(
                text="Strong Python skills",
                keywords=["Python"],
                relevance=0.9,
            ),
            RequirementSchema(
                text="Experience with Django",
                keywords=["Django"],
                relevance=0.8,
            ),
        ]

        result = build_requirement_json(requirements)

        expected = (
            '[{"text": "Strong Python skills", "keywords": ["Python"], "relevance": 0.9}, '
            '{"text": "Experience with Django", "keywords": ["Django"], "relevance": 0.8}]'
        )

        self.assertEqual(result, expected)

    def test_empty_list(self):
        result = build_requirement_json([])
        self.assertEqual(result, "[]")

    def test_unicode_characters(self):
        requirements = [
            RequirementSchema(
                text="Familiar with naïve Bayes",
                keywords=["ML"],
                relevance=0.7,
            )
        ]

        result = build_requirement_json(requirements)

        expected = (
            '[{"text": "Familiar with naïve Bayes", "keywords": ["ML"], "relevance": 0.7}]'
        )

        self.assertEqual(result, expected)
