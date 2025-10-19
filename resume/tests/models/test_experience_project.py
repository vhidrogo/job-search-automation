from django.test import TestCase

from resume.models import ExperienceProject, ExperienceRole


class TestExperienceProjectModel(TestCase):
    """Test suite for the ExperienceProject model."""

    ROLE_KEY = "navit"
    ROLE_COMPANY = "Nav.it"
    ROLE_TITLE = "Software Engineer"
    SHORT_NAME = "Search API Redesign"
    PROBLEM_CONTEXT = "Legacy search API was slow and difficult to maintain"
    ACTIONS = "implemented new REST API, rewrote query layer"
    TOOLS = "Django,Postgres,Redis"
    OUTCOMES = "reduced latency 80%, improved code maintainability"
    IMPACT_AREA = "Performance Optimization"

    def setUp(self) -> None:
        """Create a test ExperienceRole for use in tests."""
        self.role = ExperienceRole.objects.create(
            key=self.ROLE_KEY,
            company=self.ROLE_COMPANY,
            title=self.ROLE_TITLE,
        )

    def test_create_experience_project(self) -> None:
        """Test creating an ExperienceProject instance."""
        project = ExperienceProject.objects.create(
            experience_role=self.role,
            short_name=self.SHORT_NAME,
            problem_context=self.PROBLEM_CONTEXT,
            actions=self.ACTIONS,
            tools=self.TOOLS,
            outcomes=self.OUTCOMES,
            impact_area=self.IMPACT_AREA,
        )

        self.assertEqual(project.experience_role, self.role)
        self.assertEqual(project.short_name, self.SHORT_NAME)
        self.assertEqual(project.problem_context, self.PROBLEM_CONTEXT)
        self.assertEqual(project.actions, self.ACTIONS)
        self.assertEqual(project.tools, self.TOOLS)
        self.assertEqual(project.outcomes, self.OUTCOMES)
        self.assertEqual(project.impact_area, self.IMPACT_AREA)
        self.assertIsNotNone(project.id)

    def test_str_representation(self) -> None:
        """Test the string representation of ExperienceProject."""
        project = ExperienceProject.objects.create(
            experience_role=self.role,
            short_name=self.SHORT_NAME,
            problem_context=self.PROBLEM_CONTEXT,
            actions=self.ACTIONS,
            tools=self.TOOLS,
            outcomes=self.OUTCOMES,
            impact_area=self.IMPACT_AREA,
        )

        self.assertEqual(str(project), "Search API Redesign (Software Engineer – Nav.it)")

    def test_foreign_key_relationship(self) -> None:
        """Test the foreign key relationship with ExperienceRole."""
        project = ExperienceProject.objects.create(
            experience_role=self.role,
            short_name=self.SHORT_NAME,
            problem_context=self.PROBLEM_CONTEXT,
            actions=self.ACTIONS,
            tools=self.TOOLS,
            outcomes=self.OUTCOMES,
            impact_area=self.IMPACT_AREA,
        )

        self.assertEqual(self.role.projects.count(), 1)
        self.assertEqual(self.role.projects.first(), project)

    def test_cascade_delete(self) -> None:
        """Test that deleting a role cascades to its projects."""
        ExperienceProject.objects.create(
            experience_role=self.role,
            short_name=self.SHORT_NAME,
            problem_context=self.PROBLEM_CONTEXT,
            actions=self.ACTIONS,
            tools=self.TOOLS,
            outcomes=self.OUTCOMES,
            impact_area=self.IMPACT_AREA,
        )

        self.assertEqual(ExperienceProject.objects.count(), 1)
        self.role.delete()
        self.assertEqual(ExperienceProject.objects.count(), 0)

    def test_multiple_projects_for_same_role(self) -> None:
        """Test creating multiple projects for the same role."""
        project1 = ExperienceProject.objects.create(
            experience_role=self.role,
            short_name="Project Alpha",
            problem_context="Context A",
            actions="action A",
            tools="Tool A",
            outcomes="outcome A",
            impact_area="Area A",
        )
        project2 = ExperienceProject.objects.create(
            experience_role=self.role,
            short_name="Project Beta",
            problem_context="Context B",
            actions="action B",
            tools="Tool B",
            outcomes="outcome B",
            impact_area="Area B",
        )

        self.assertEqual(self.role.projects.count(), 2)
        self.assertIn(project1, self.role.projects.all())
        self.assertIn(project2, self.role.projects.all())

    def test_query_by_impact_area(self) -> None:
        """Test querying projects by impact_area."""
        ExperienceProject.objects.create(
            experience_role=self.role,
            short_name="Performance Project",
            problem_context=self.PROBLEM_CONTEXT,
            actions=self.ACTIONS,
            tools=self.TOOLS,
            outcomes=self.OUTCOMES,
            impact_area="Performance Optimization",
        )
        ExperienceProject.objects.create(
            experience_role=self.role,
            short_name="Engagement Project",
            problem_context="Different context",
            actions="different actions",
            tools="different tools",
            outcomes="different outcomes",
            impact_area="User Engagement",
        )

        performance_projects = ExperienceProject.objects.filter(
            impact_area="Performance Optimization"
        )
        self.assertEqual(performance_projects.count(), 1)
        self.assertEqual(performance_projects.first().short_name, "Performance Project")

    def test_empty_csv_fields(self) -> None:
        """Test that CSV fields can be empty strings."""
        project = ExperienceProject.objects.create(
            experience_role=self.role,
            short_name=self.SHORT_NAME,
            problem_context=self.PROBLEM_CONTEXT,
            actions="",
            tools="",
            outcomes="",
            impact_area=self.IMPACT_AREA,
        )

        self.assertEqual(project.actions, "")
        self.assertEqual(project.tools, "")
        self.assertEqual(project.outcomes, "")