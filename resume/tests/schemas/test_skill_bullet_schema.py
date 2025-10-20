from unittest import TestCase
from pydantic import ValidationError
from resume.schemas.skill_bullet_schema import SkillCategorySchema, SkillBulletListModel


class TestSkillCategorySchema(TestCase):
    """Test suite for SkillCategorySchema validation."""
    
    VALID_CATEGORY = "Programming Languages"
    VALID_SKILLS = "Python, Java, JavaScript, TypeScript"
    SHORT_CATEGORY = "XY"
    LONG_CATEGORY = "x" * 101
    SHORT_SKILLS = "P"
    LONG_SKILLS = "x" * 501
    WHITESPACE_CATEGORY = "   \n\t   "
    WHITESPACE_SKILLS = "   \n\t   "
    EMPTY_CATEGORY = ""
    EMPTY_SKILLS = ""
    
    def test_valid_skill_category(self):
        """Test that valid skill category data passes validation."""
        category = SkillCategorySchema(category=self.VALID_CATEGORY, skills=self.VALID_SKILLS)
        self.assertEqual(category.category, self.VALID_CATEGORY)
        self.assertEqual(category.skills, self.VALID_SKILLS)
    
    def test_category_stripped_on_validation(self):
        """Test that whitespace is stripped from category name."""
        category = SkillCategorySchema(
            category=f"  {self.VALID_CATEGORY}  \n",
            skills=self.VALID_SKILLS
        )
        self.assertEqual(category.category, self.VALID_CATEGORY)
    
    def test_skills_stripped_on_validation(self):
        """Test that whitespace is stripped from skills string."""
        category = SkillCategorySchema(
            category=self.VALID_CATEGORY,
            skills=f"  {self.VALID_SKILLS}  \n"
        )
        self.assertEqual(category.skills, self.VALID_SKILLS)
    
    def test_category_too_short(self):
        """Test that category below minimum length raises validation error."""
        with self.assertRaises(ValidationError) as cm:
            SkillCategorySchema(category=self.SHORT_CATEGORY, skills=self.VALID_SKILLS)
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('category',) and 'at least 3 characters' in str(e['msg']) for e in errors)
        )
    
    def test_category_too_long(self):
        """Test that category exceeding maximum length raises validation error."""
        with self.assertRaises(ValidationError) as cm:
            SkillCategorySchema(category=self.LONG_CATEGORY, skills=self.VALID_SKILLS)
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('category',) and 'at most 100 characters' in str(e['msg']) for e in errors)
        )
    
    def test_skills_too_short(self):
        """Test that skills string below minimum length raises validation error."""
        with self.assertRaises(ValidationError) as cm:
            SkillCategorySchema(category=self.VALID_CATEGORY, skills=self.SHORT_SKILLS)
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('skills',) and 'at least 2 characters' in str(e['msg']) for e in errors)
        )
    
    def test_skills_too_long(self):
        """Test that skills string exceeding maximum length raises validation error."""
        with self.assertRaises(ValidationError) as cm:
            SkillCategorySchema(category=self.VALID_CATEGORY, skills=self.LONG_SKILLS)
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('skills',) and 'at most 500 characters' in str(e['msg']) for e in errors)
        )
    
    def test_empty_category(self):
        """Test that empty category raises validation error."""
        with self.assertRaises(ValidationError) as cm:
            SkillCategorySchema(category=self.EMPTY_CATEGORY, skills=self.VALID_SKILLS)
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('category',) for e in errors)
        )
    
    def test_empty_skills(self):
        """Test that empty skills string raises validation error."""
        with self.assertRaises(ValidationError) as cm:
            SkillCategorySchema(category=self.VALID_CATEGORY, skills=self.EMPTY_SKILLS)
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('skills',) for e in errors)
        )
    
    def test_whitespace_only_category(self):
        """Test that whitespace-only category raises validation error."""
        with self.assertRaises(ValidationError) as cm:
            SkillCategorySchema(category=self.WHITESPACE_CATEGORY, skills=self.VALID_SKILLS)
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('category',) for e in errors)
        )
    
    def test_whitespace_only_skills(self):
        """Test that whitespace-only skills string raises validation error."""
        with self.assertRaises(ValidationError) as cm:
            SkillCategorySchema(category=self.VALID_CATEGORY, skills=self.WHITESPACE_SKILLS)
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('skills',) for e in errors)
        )
    
    def test_missing_required_fields(self):
        """Test that missing required fields raise validation error."""
        with self.assertRaises(ValidationError) as cm:
            SkillCategorySchema(category=self.VALID_CATEGORY)
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('skills',) and e['type'] == 'missing' for e in errors)
        )


class TestSkillBulletListModel(TestCase):
    """Test suite for SkillBulletListModel schema validation."""
    
    VALID_CATEGORY_1 = "Programming Languages"
    VALID_SKILLS_1 = "Python, Java, JavaScript"
    VALID_CATEGORY_2 = "Data & Visualization"
    VALID_SKILLS_2 = "PostgreSQL, Redis, D3.js"
    
    def test_valid_skill_category_list(self):
        """Test that valid skill category list passes validation."""
        categories_data = [
            {"category": self.VALID_CATEGORY_1, "skills": self.VALID_SKILLS_1},
            {"category": self.VALID_CATEGORY_2, "skills": self.VALID_SKILLS_2}
        ]
        model = SkillBulletListModel(skill_categories=categories_data)
        self.assertEqual(len(model.skill_categories), 2)
        self.assertEqual(model.skill_categories[0].category, self.VALID_CATEGORY_1)
        self.assertEqual(model.skill_categories[1].skills, self.VALID_SKILLS_2)
    
    def test_single_category_valid(self):
        """Test that a single skill category is valid."""
        categories_data = [{"category": self.VALID_CATEGORY_1, "skills": self.VALID_SKILLS_1}]
        model = SkillBulletListModel(skill_categories=categories_data)
        self.assertEqual(len(model.skill_categories), 1)
    
    def test_empty_category_list_fails(self):
        """Test that empty skill category list raises validation error."""
        with self.assertRaises(ValidationError) as cm:
            SkillBulletListModel(skill_categories=[])
        errors = cm.exception.errors()
        self.assertTrue(
            any('at least one skill category' in str(e['msg']) for e in errors)
        )
    
    def test_invalid_category_in_list(self):
        """Test that invalid skill category in list raises validation error."""
        categories_data = [
            {"category": self.VALID_CATEGORY_1, "skills": self.VALID_SKILLS_1},
            {"category": self.VALID_CATEGORY_2, "skills": "x"}
        ]
        with self.assertRaises(ValidationError) as cm:
            SkillBulletListModel(skill_categories=categories_data)
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'][0] == 'skill_categories' and e['loc'][1] == 1 for e in errors)
        )
    
    def test_validate_max_count_within_limit(self):
        """Test that validate_max_count passes when count is within limit."""
        categories_data = [
            {"category": self.VALID_CATEGORY_1, "skills": self.VALID_SKILLS_1},
            {"category": self.VALID_CATEGORY_2, "skills": self.VALID_SKILLS_2}
        ]
        model = SkillBulletListModel(skill_categories=categories_data)
        try:
            model.validate_max_count(max_category_count=3)
        except ValueError:
            self.fail("validate_max_count raised ValueError unexpectedly")
    
    def test_validate_max_count_at_limit(self):
        """Test that validate_max_count passes when count equals limit."""
        categories_data = [
            {"category": self.VALID_CATEGORY_1, "skills": self.VALID_SKILLS_1},
            {"category": self.VALID_CATEGORY_2, "skills": self.VALID_SKILLS_2}
        ]
        model = SkillBulletListModel(skill_categories=categories_data)
        try:
            model.validate_max_count(max_category_count=2)
        except ValueError:
            self.fail("validate_max_count raised ValueError unexpectedly")
    
    def test_validate_max_count_exceeds_limit(self):
        """Test that validate_max_count raises error when count exceeds limit."""
        categories_data = [
            {"category": self.VALID_CATEGORY_1, "skills": self.VALID_SKILLS_1},
            {"category": self.VALID_CATEGORY_2, "skills": self.VALID_SKILLS_2},
            {"category": "Cloud & DevOps", "skills": "AWS, Docker, Kubernetes"}
        ]
        model = SkillBulletListModel(skill_categories=categories_data)
        with self.assertRaises(ValueError) as cm:
            model.validate_max_count(max_category_count=2)
        self.assertIn("contains 3 skill categories", str(cm.exception))
        self.assertIn("maximum allowed is 2", str(cm.exception))
    
    def test_missing_skill_categories_field(self):
        """Test that missing skill_categories field raises validation error."""
        with self.assertRaises(ValidationError) as cm:
            SkillBulletListModel()
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('skill_categories',) and e['type'] == 'missing' for e in errors)
        )
