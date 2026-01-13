import json
from unittest.mock import ANY, Mock

from django.test import TestCase
from django.utils import timezone

from tracker.models import JobRole, JobLevel, LlmRequestLog
from resume.clients import ClaudeClient
from resume.models import (
    ExperienceProject,
    ExperienceRole,
    ResumeTemplate,
    TemplateRoleConfig,
)
from resume.schemas import (
    BulletListModel,
    ExperienceBullet,
    SkillsListModel,
    SkillsCategorySchema,
    RequirementSchema,
)
from resume.services import ResumeWriter


class TestResumeWriter(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.experience_role = ExperienceRole.objects.create(
            key="role1",
            title="Software Engineer",
            company="Nav.it",
            start_date=timezone.now(),
            end_date=timezone.now(),
        )
        cls.template = ResumeTemplate.objects.create(
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.II,
        )
        TemplateRoleConfig.objects.create(
            template=cls.template,
            experience_role=cls.experience_role,
            order=1,
            max_bullet_count=1,
        )
        cls.tools = ["Python", "Django"]

        cls.requirement_text1 = "5+ years of Python experience"
        cls.requirement_text2 = "Experience with Django web framework"
        cls.requirement_keywords1 = ["Python", "experience"]
        cls.requirement_keywords2 = ["Django", "web framework"]
        cls.requirements = [
            RequirementSchema(
                text=cls.requirement_text1,
                keywords=cls.requirement_keywords1,
                relevance=0.95,
            ),
            RequirementSchema(
                text=cls.requirement_text2,
                keywords=cls.requirement_keywords2,
                relevance=0.90,
            ),
        ]

        cls.bullet_order1, cls.bullet_order2 = 1, 2
        cls.bullet_text1 = "Built real-time API using Django and Postgres that reduced query latency by 80%"
        cls.bullet_text2 = "Automated data pipeline with Python and Airflow, cutting processing time from 4 hours to 15 minutes"

        cls.skills_category1, cls.skills_category2 = "Programming Languages", "Databases"
        cls.skills_text1 = "Python, Java"
        cls.skills_text2 = "PostgreSQL, DynamoDB"

        cls.skills_response = json.dumps({
            "skills_categories": [
                {
                    "order": 1,
                    "category": cls.skills_category1,
                    "skills": cls.skills_text1,
                },
                {
                    "order": 2,
                    "category": cls.skills_category2,
                    "skills": cls.skills_text2,
                },
            ]
        })

    def setUp(self):
        self.mock_client = Mock(spec=ClaudeClient)
        self.resume_writer = ResumeWriter(client=self.mock_client)
    
    def test_generate_experience_bullets_returns_validated_bullets(self):
        project = ExperienceProject.objects.create(experience_role=self.experience_role)
        self.mock_client.generate.return_value = json.dumps({
            "bullets": [
                {
                    "order": 1,
                    "text": "Built real-time API using Django and Postgres",
                    "project_id": project.id,
                },
                {
                    "order": 2,
                    "text": "Automated data pipeline with Python and SQL",
                    "project_id": project.id,
                }
            ]
        })

        result = self.resume_writer.generate_experience_bullets(
            experience_role=self.experience_role,
            requirements=self.requirements,
            target_role=JobRole.SOFTWARE_ENGINEER,
            max_bullet_count=2,
        )
        
        self.mock_client.generate.assert_called_once_with(
            ANY,
            call_type=LlmRequestLog.CallType.RESUME_BULLETS,
            model=ANY,
            max_tokens=ANY,
        )
        expected = BulletListModel(
            bullets=[
                ExperienceBullet(
                    order=1,
                    text="Built real-time API using Django and Postgres",
                    project_id=project.id,
                ),
                ExperienceBullet(
                    order=2,
                    text="Automated data pipeline with Python and SQL",
                    project_id=project.id,
                ),
            ]
        )
        self.assertEqual(result, expected)

    def test_generate_experience_bullets_raises_when_no_projects(self):
        with self.assertRaises(ValueError) as cm:
            self.resume_writer.generate_experience_bullets(
                experience_role=self.experience_role,
                requirements=self.requirements,
                target_role=JobRole.SOFTWARE_ENGINEER,
                max_bullet_count=1,
            )

        error_msg = str(cm.exception)
        self.assertIn("No experience ", error_msg)
        self.assertIn(str(self.experience_role), error_msg)

    def test_generate_experience_bullets_raises_on_invalid_json(self):
        ExperienceProject.objects.create(experience_role=self.experience_role)
        self.mock_client.generate.return_value = "invalid json"

        with self.assertRaises(ValueError):
            self.resume_writer.generate_experience_bullets(
                experience_role=self.experience_role,
                requirements=self.requirements,
                target_role=JobRole.SOFTWARE_ENGINEER,
                max_bullet_count=1,
            )

    def test_generate_experience_bullets_raises_on_excess_bullets(self):
        ExperienceProject.objects.create(experience_role=self.experience_role)
        self.mock_client.generate.return_value = json.dumps({
            "bullets": [
                {
                    "order": 1,
                    "text": "Built real-time API using Django and Postgres",
                    "project_id": 1,
                },
                {
                    "order": 2,
                    "text": "Automated data pipeline with Python and SQL",
                    "project_id": 1,
                }
            ]
        })

        with self.assertRaises(ValueError) as cm:
            self.resume_writer.generate_experience_bullets(
                experience_role=self.experience_role,
                requirements=self.requirements,
                target_role=JobRole.SOFTWARE_ENGINEER,
                max_bullet_count=1,
            )

        self.assertIn(f"maximum allowed is 1", str(cm.exception))

    def test_generate_experience_bullets_builds_prompt_with_data(self):
        tools = "Python"
        actions = "Wrote API client"
        project = ExperienceProject.objects.create(
            experience_role=self.experience_role,
            tools=tools,
            actions=actions,
        )
        self.mock_client.generate.return_value = json.dumps({
            "bullets": [
                {
                    "order": 1,
                    "text": "Built real-time API using Django and Postgres",
                    "project_id": project.id,
                }
            ]
        })

        self.resume_writer.generate_experience_bullets(
            experience_role=self.experience_role,
            requirements=self.requirements,
            target_role=JobRole.SOFTWARE_ENGINEER,
            max_bullet_count=2,
        )

        prompt = self._get_prompt_arg()
        self.assertIn(JobRole.SOFTWARE_ENGINEER, prompt)
        self.assertIn(self.requirement_text1, prompt)
        self.assertIn(self.requirement_text2, prompt)
        self.assertIn(tools, prompt)
        self.assertIn(actions, prompt)
        self.assertIn(str(project.id), prompt)

    def _create_default_project_with_tools(self):
        ExperienceProject.objects.create(
            experience_role=self.experience_role,
            tools=self.tools,
        )

    def test_generate_skills_returns_validated_bullets(self):
        self._create_default_project_with_tools()
        self.mock_client.generate.return_value = self.skills_response

        result = self.resume_writer.generate_skills(
            template=self.template,
            requirements=self.requirements,
        )

        self.mock_client.generate.assert_called_once_with(
            ANY,
            call_type=LlmRequestLog.CallType.RESUME_SKILLS,
            model=ANY,
            max_tokens=ANY,
        )
        expected = SkillsListModel(
            skills_categories=[
                SkillsCategorySchema(
                    order=1,
                    category=self.skills_category1,
                    skills=self.skills_text1,
                ),
                SkillsCategorySchema(
                    order=2,
                    category=self.skills_category2,
                    skills=self.skills_text2,
                ),
            ]
        )
        self.assertEqual(result, expected)

    def test_generate_skills_raises_when_no_role_configs(self):
        self._create_default_project_with_tools()
        template = ResumeTemplate.objects.create()
        with self.assertRaises(ValueError) as cm:
            self.resume_writer.generate_skills(
                template=template,
                requirements=self.requirements,
            )

        error_msg = str(cm.exception)
        self.assertIn("No role configs found", error_msg)

    def test_generate_skills_raises_when_no_tools(self):
        ExperienceProject.objects.create(experience_role=self.experience_role)
        with self.assertRaises(ValueError) as cm:
            self.resume_writer.generate_skills(
                template=self.template,
                requirements=self.requirements,
            )

        error_msg = str(cm.exception)
        self.assertIn("No tools found", error_msg)
    
    def test_generate_skills_raises_when_no_projects(self):
        with self.assertRaises(ValueError) as cm:
            self.resume_writer.generate_skills(
                template=self.template,
                requirements=self.requirements,
            )

        error_msg = str(cm.exception)
        self.assertIn("No projects found", error_msg)

    def test_generate_skills_raises_on_invalid_json(self):
        self._create_default_project_with_tools()
        self.mock_client.generate.return_value = "invalid json"

        with self.assertRaises(ValueError):
            self.resume_writer.generate_skills(
                template=self.template,
                requirements=self.requirements,
            )

    def test_generate_skills_raises_on_excess_categories(self):
        self._create_default_project_with_tools()
        self.mock_client.generate.return_value = self.skills_response
        max_category_count = 1

        with self.assertRaises(ValueError) as cm:
            self.resume_writer.generate_skills(
                template=self.template,
                requirements=self.requirements,
                max_category_count=max_category_count,
            )

        self.assertIn(f"maximum allowed is {max_category_count}", str(cm.exception))

    def test_generate_skills_builds_prompt_with_requirement_keywords(self):
        self._create_default_project_with_tools()
        self.mock_client.generate.return_value = self.skills_response
        
        self.resume_writer.generate_skills(
            template=self.template,
            requirements=self.requirements,
        )
        
        prompt = self._get_prompt_arg()
        self.assertTrue(
            all(keyword in prompt for keyword in self.requirement_keywords1),
            f"Prompt does not include all unique keywords from requirement: {self.requirement_text1}.",
        )
        self.assertTrue(
            all(keyword in prompt for keyword in self.requirement_keywords2),
            f"Prompt does not include all unique keywords from requirement: {self.requirement_text2}.",
        )

    def test_generate_skills_prompt_includes_all_tools_for_all_included_roles(self):
        self._create_default_project_with_tools()
        role2 = ExperienceRole.objects.create(
            key="role2",
            title="Software Development Engineer",
            company="Amazon.com",
            start_date=timezone.now(),
            end_date=timezone.now(),
        )
        TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=role2,
            order=2,
            max_bullet_count=1,
        )
        role2_tools = ["Java", "AWS"]
        ExperienceProject.objects.create(
            experience_role=role2,
            tools=role2_tools,
        )
        self.mock_client.generate.return_value = self.skills_response
        
        self.resume_writer.generate_skills(
            template=self.template,
            requirements=self.requirements,
        )
        
        prompt = self._get_prompt_arg()
        self.assertTrue(
            all(tool in prompt for tool in self.tools),
            f"Prompt does not include all unique tools from role: {self.experience_role}.",
        )
        self.assertTrue(
            all(tool in prompt for tool in role2_tools),
            f"Prompt does not include all unique tools from role: {role2}.",
        )

    def test_generate_skills_prompt_excludes_tools_for_excluded_roles(self):
        self._create_default_project_with_tools()
        role2 = ExperienceRole.objects.create(
            key="role2",
            title="Software Development Engineer",
            company="Amazon.com",
            start_date=timezone.now(),
            end_date=timezone.now(),
        )
        role2_tools = ["Java", "AWS"]
        ExperienceProject.objects.create(
            experience_role=role2,
            tools=role2_tools,
        )
        self.mock_client.generate.return_value = self.skills_response
        
        self.resume_writer.generate_skills(
            template=self.template,
            requirements=self.requirements,
        )
        
        prompt = self._get_prompt_arg()
        self.assertTrue(all(tool not in prompt for tool in role2_tools))

    def _get_prompt_arg(self):
        self.mock_client.generate.assert_called_once()
        return self.mock_client.generate.call_args[0][0]
