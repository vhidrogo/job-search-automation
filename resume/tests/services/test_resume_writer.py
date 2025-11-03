import json
from django.test import TestCase
from unittest.mock import Mock

from tracker.models import JobRole, JobLevel
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
    SkillBulletListModel,
    SkillCategorySchema,
    RequirementSchema,
)
from resume.services import ResumeWriter


class TestResumeWriter(TestCase):
    TARGET_ROLE = JobRole.SOFTWARE_ENGINEER
    MAX_BULLET_COUNT = 2

    @classmethod
    def setUpTestData(cls):
        cls.experience_role = ExperienceRole.objects.create(
            key="role1",
            title="Software Engineer",
            company="Nav.it",
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
        
        cls.bullet_response = json.dumps({
            "bullets": [
                {
                    "order": cls.bullet_order1,
                    "text": cls.bullet_text1,
                },
                {
                    "order": cls.bullet_order2,
                    "text": cls.bullet_text2
                }
            ]
        })

        cls.skill_category1, cls.skill_category2 = "Programming Languages", "Databases"
        cls.skill_text1 = "Python, Java"
        cls.skill_text2 = "PostgreSQL, DynamoDB"

        cls.skill_response = json.dumps({
            "skill_categories": [
                {
                    "category": cls.skill_category1,
                    "skills": cls.skill_text1,
                },
                {
                    "category": cls.skill_category2,
                    "skills": cls.skill_text2,
                },
            ]
        })

    def setUp(self):
        self.mock_client = Mock(spec=ClaudeClient)
        self.resume_writer = ResumeWriter(client=self.mock_client)
    
    def test_generate_experience_bullets_returns_validated_bullets(self):
        ExperienceProject.objects.create(experience_role=self.experience_role)
        self.mock_client.generate.return_value = self.bullet_response

        result = self.resume_writer.generate_experience_bullets(
            experience_role=self.experience_role,
            requirements=self.requirements,
            target_role=self.TARGET_ROLE,
            max_bullet_count=self.MAX_BULLET_COUNT,
        )
        
        self.mock_client.generate.assert_called_once()
        expected = BulletListModel(
            bullets=[
                ExperienceBullet(
                    order=self.bullet_order1,
                    text=self.bullet_text1,
                ),
                ExperienceBullet(
                    order=self.bullet_order2,
                    text=self.bullet_text2,
                ),
            ]
        )
        self.assertEqual(result, expected)

    def test_generate_experience_bullets_raises_when_no_projects(self):
        with self.assertRaises(ValueError) as cm:
            self.resume_writer.generate_experience_bullets(
                experience_role=self.experience_role,
                requirements=self.requirements,
                target_role=self.TARGET_ROLE,
                max_bullet_count=self.MAX_BULLET_COUNT,
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
                target_role=self.TARGET_ROLE,
                max_bullet_count=self.MAX_BULLET_COUNT,
            )

    def test_generate_experience_bullets_raises_on_excess_bullets(self):
        ExperienceProject.objects.create(experience_role=self.experience_role)
        self.mock_client.generate.return_value = self.bullet_response
        max_bullet_count = 1

        with self.assertRaises(ValueError) as cm:
            self.resume_writer.generate_experience_bullets(
                experience_role=self.experience_role,
                requirements=self.requirements,
                target_role=self.TARGET_ROLE,
                max_bullet_count=max_bullet_count,
            )

        self.assertIn(f"maximum allowed is {max_bullet_count}", str(cm.exception))

    def test_generate_experience_bullets_builds_prompt_with_data(self):
        short_name = "API Integration"
        actions = "Wrote API client"
        ExperienceProject.objects.create(
            experience_role=self.experience_role,
            short_name=short_name,
            actions=actions,
        )
        self.mock_client.generate.return_value = self.bullet_response

        self.resume_writer.generate_experience_bullets(
            experience_role=self.experience_role,
            requirements=self.requirements,
            target_role=self.TARGET_ROLE,
            max_bullet_count=2,
        )

        self.mock_client.generate.assert_called_once()
        prompt= self.mock_client.generate.call_args[0][0]

        self.assertIn(self.TARGET_ROLE, prompt)

        # Verify requirement data included in prompt
        self.assertIn(self.requirement_text1, prompt)
        self.assertIn(self.requirement_text2, prompt)
        
        # Verify project data included in prompt
        self.assertIn(short_name, prompt)
        self.assertIn(actions, prompt)

    def _create_default_project_with_tools(self):
        ExperienceProject.objects.create(
            experience_role=self.experience_role,
            tools=self.tools,
        )

    def test_generate_skill_bullets_returns_validated_bullets(self):
        self._create_default_project_with_tools()
        self.mock_client.generate.return_value = self.skill_response

        result = self.resume_writer.generate_skill_bullets(
            template=self.template,
            requirements=self.requirements,
        )

        self.mock_client.generate.assert_called_once()
        expected = SkillBulletListModel(
            skill_categories=[
                SkillCategorySchema(
                    category=self.skill_category1,
                    skills=self.skill_text1,
                ),
                SkillCategorySchema(
                    category=self.skill_category2,
                    skills=self.skill_text2,
                ),
            ]
        )
        self.assertEqual(result, expected)

    def test_generate_skill_bullets_raises_when_no_role_configs(self):
        self._create_default_project_with_tools()
        template = ResumeTemplate.objects.create()
        with self.assertRaises(ValueError) as cm:
            self.resume_writer.generate_skill_bullets(
                template=template,
                requirements=self.requirements,
            )

        error_msg = str(cm.exception)
        self.assertIn("No role configs found", error_msg)

    def test_generate_skill_bullets_raises_when_no_tools(self):
        ExperienceProject.objects.create(experience_role=self.experience_role)
        with self.assertRaises(ValueError) as cm:
            self.resume_writer.generate_skill_bullets(
                template=self.template,
                requirements=self.requirements,
            )

        error_msg = str(cm.exception)
        self.assertIn("No tools found", error_msg)
    
    def test_generate_skill_bullets_raises_when_no_projects(self):
        with self.assertRaises(ValueError) as cm:
            self.resume_writer.generate_skill_bullets(
                template=self.template,
                requirements=self.requirements,
            )

        error_msg = str(cm.exception)
        self.assertIn("No projects found", error_msg)

    def test_generate_skill_bullets_raises_on_invalid_json(self):
        self._create_default_project_with_tools()
        self.mock_client.generate.return_value = "invalid json"

        with self.assertRaises(ValueError):
            self.resume_writer.generate_skill_bullets(
                template=self.template,
                requirements=self.requirements,
            )

    def test_generate_skill_bullets_raises_on_excess_categories(self):
        self._create_default_project_with_tools()
        self.mock_client.generate.return_value = self.skill_response
        max_category_count = 1

        with self.assertRaises(ValueError) as cm:
            self.resume_writer.generate_skill_bullets(
                template=self.template,
                requirements=self.requirements,
                max_category_count=max_category_count,
            )

        self.assertIn(f"maximum allowed is {max_category_count}", str(cm.exception))

    def test_generate_skill_bullets_builds_prompt_with_requirement_keywords(self):
        self._create_default_project_with_tools()
        self.mock_client.generate.return_value = self.skill_response
        
        self.resume_writer.generate_skill_bullets(
            template=self.template,
            requirements=self.requirements,
        )
        
        self.mock_client.generate.assert_called_once()
        prompt = self.mock_client.generate.call_args[0][0]
        self.assertTrue(
            all(keyword in prompt for keyword in self.requirement_keywords1),
            f"Prompt does not include all unique keywords from requirement: {self.requirement_text1}.",
        )
        self.assertTrue(
            all(keyword in prompt for keyword in self.requirement_keywords2),
            f"Prompt does not include all unique keywords from requirement: {self.requirement_text2}.",
        )

    def test_generate_skill_bullets_prompt_includes_all_tools_for_all_included_roles(self):
        self._create_default_project_with_tools()
        role2 = ExperienceRole.objects.create(
            key="role2",
            title="Software Development Engineer",
            company="Amazon.com",
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
        self.mock_client.generate.return_value = self.skill_response
        
        self.resume_writer.generate_skill_bullets(
            template=self.template,
            requirements=self.requirements,
        )
        
        self.mock_client.generate.assert_called_once()
        prompt = self.mock_client.generate.call_args[0][0]
        self.assertTrue(
            all(tool in prompt for tool in self.tools),
            f"Prompt does not include all unique tools from role: {self.experience_role}.",
        )
        self.assertTrue(
            all(tool in prompt for tool in role2_tools),
            f"Prompt does not include all unique tools from role: {role2}.",
        )

    def test_generate_skill_bullets_prompt_excludes_tools_for_excluded_roles(self):
        self._create_default_project_with_tools()
        role2 = ExperienceRole.objects.create(
            key="role2",
            title="Software Development Engineer",
            company="Amazon.com",
        )
        role2_tools = ["Java", "AWS"]
        ExperienceProject.objects.create(
            experience_role=role2,
            tools=role2_tools,
        )
        self.mock_client.generate.return_value = self.skill_response
        
        self.resume_writer.generate_skill_bullets(
            template=self.template,
            requirements=self.requirements,
        )
        
        self.mock_client.generate.assert_called_once()
        prompt = self.mock_client.generate.call_args[0][0]
        self.assertTrue(all(tool not in prompt for tool in role2_tools))
