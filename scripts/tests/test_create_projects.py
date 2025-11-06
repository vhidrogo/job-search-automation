from django.test import TestCase

from resume.models import ExperienceRole
from scripts.create_projects import create_projects_from_data


class TestCreateProjectsFromData(TestCase):
    VALID_KEY = "navit"

    @classmethod
    def setUpTestData(cls):
        cls.role = ExperienceRole.objects.create(key=cls.VALID_KEY)

    def test_create_projects_from_data_creates_objects(self):
        short_name1 = "Sample Integration Project"
        short_name2 = "Sample Automation Project"
        projects = [
        	{
        	    "short_name": short_name1,
        	    "problem_context": "Sample problem context",
        	    "actions": [
        	        "Sample action 1",
        	        "Sample action 2"
        	    ],
        	    "tools": [
        	        "Tool A",
        	        "Tool B"
        	    ],
        	    "outcomes": [
        	        "Sample outcome 1",
        	        "Sample outcome 2"
        	    ],
        	    "impact_area": "Sample Area"
        	},
        	{
        	    "short_name": short_name2,
        	    "problem_context": "Sample problem context",
        	    "actions": [
        	        "Sample action 1",
        	        "Sample action 2"
        	    ],
        	    "tools": [
        	        "Tool A",
        	        "Tool B"
        	    ],
        	    "outcomes": [
        	        "Sample outcome 1",
        	        "Sample outcome 2"
        	    ],
        	    "impact_area": "Sample Area"
        	}
        ]

        result = create_projects_from_data(projects=projects, role_key=self.VALID_KEY, verbose=False)

        self.assertEqual(len(result), 2)
        result_names = [p.short_name for p in result]
        self.assertIn(short_name1, result_names)
        self.assertIn(short_name2, result_names)


    def test_create_projects_from_data_raises_when_no_role_found(self):
        with self.assertRaises(ExperienceRole.DoesNotExist):
            create_projects_from_data(projects=[], role_key="invalid")

    def test_create_projects_from_data_raises_when_missing_fields(self):
        invalid_projects = [{"invalid field": ""}]

        with self.assertRaises(ValueError):
            create_projects_from_data(projects=invalid_projects, role_key=self.VALID_KEY, verbose=False)
