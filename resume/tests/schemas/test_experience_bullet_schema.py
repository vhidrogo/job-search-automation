# resume/tests/test_experience_bullet_schema.py
from unittest import TestCase
from pydantic import ValidationError
from resume.schemas.experience_bullet_schema import ExperienceBullet, BulletListModel


class ExperienceBulletTestCase(TestCase):
    """Test suite for ExperienceBullet schema validation."""
    
    VALID_BULLET_TEXT = "Built a real-time search API using Django and Postgres that reduced query latency by 80%"
    SHORT_TEXT = "Too short bullet"
    LONG_TEXT = "x" * 501
    WHITESPACE_TEXT = "   \n\t   "
    EMPTY_TEXT = ""
    
    def test_valid_bullet(self):
        """Test that valid bullet data passes validation."""
        bullet = ExperienceBullet(order=1, text=self.VALID_BULLET_TEXT)
        self.assertEqual(bullet.order, 1)
        self.assertEqual(bullet.text, self.VALID_BULLET_TEXT)
    
    def test_text_stripped_on_validation(self):
        """Test that whitespace is stripped from bullet text."""
        bullet = ExperienceBullet(order=1, text=f"  {self.VALID_BULLET_TEXT}  \n")
        self.assertEqual(bullet.text, self.VALID_BULLET_TEXT)
    
    def test_text_too_short(self):
        """Test that text below minimum length raises validation error."""
        with self.assertRaises(ValidationError) as cm:
            ExperienceBullet(order=1, text=self.SHORT_TEXT)
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('text',) and 'at least 20 characters' in str(e['msg']) for e in errors)
        )
    
    def test_text_too_long(self):
        """Test that text exceeding maximum length raises validation error."""
        with self.assertRaises(ValidationError) as cm:
            ExperienceBullet(order=1, text=self.LONG_TEXT)
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('text',) and 'at most 500 characters' in str(e['msg']) for e in errors)
        )
    
    def test_empty_text(self):
        """Test that empty text raises validation error."""
        with self.assertRaises(ValidationError) as cm:
            ExperienceBullet(order=1, text=self.EMPTY_TEXT)
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('text',) for e in errors)
        )
    
    def test_whitespace_only_text(self):
        """Test that whitespace-only text raises validation error."""
        with self.assertRaises(ValidationError) as cm:
            ExperienceBullet(order=1, text=self.WHITESPACE_TEXT)
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('text',) for e in errors)
        )
    
    def test_order_must_be_positive(self):
        """Test that order must be at least 1."""
        with self.assertRaises(ValidationError) as cm:
            ExperienceBullet(order=0, text=self.VALID_BULLET_TEXT)
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('order',) and 'greater than or equal to 1' in str(e['msg']) for e in errors)
        )
    
    def test_order_negative(self):
        """Test that negative order values raise validation error."""
        with self.assertRaises(ValidationError) as cm:
            ExperienceBullet(order=-1, text=self.VALID_BULLET_TEXT)
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('order',) for e in errors)
        )
    
    def test_missing_required_fields(self):
        """Test that missing required fields raise validation error."""
        with self.assertRaises(ValidationError) as cm:
            ExperienceBullet(order=1)
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('text',) and e['type'] == 'missing' for e in errors)
        )


class BulletListModelTestCase(TestCase):
    """Test suite for BulletListModel schema validation."""
    
    VALID_BULLET_TEXT_1 = "Built a real-time search API using Django and Postgres that reduced query latency by 80%"
    VALID_BULLET_TEXT_2 = "Automated ETL pipeline for customer analytics using Python and Airflow"
    
    def test_valid_bullet_list(self):
        """Test that valid bullet list passes validation."""
        bullets_data = [
            {"order": 1, "text": self.VALID_BULLET_TEXT_1},
            {"order": 2, "text": self.VALID_BULLET_TEXT_2}
        ]
        model = BulletListModel(bullets=bullets_data)
        self.assertEqual(len(model.bullets), 2)
        self.assertEqual(model.bullets[0].order, 1)
        self.assertEqual(model.bullets[1].text, self.VALID_BULLET_TEXT_2)
    
    def test_single_bullet_valid(self):
        """Test that a single bullet is valid."""
        bullets_data = [{"order": 1, "text": self.VALID_BULLET_TEXT_1}]
        model = BulletListModel(bullets=bullets_data)
        self.assertEqual(len(model.bullets), 1)
    
    def test_empty_bullet_list_fails(self):
        """Test that empty bullet list raises validation error."""
        with self.assertRaises(ValidationError) as cm:
            BulletListModel(bullets=[])
        errors = cm.exception.errors()
        self.assertTrue(
            any('at least one bullet' in str(e['msg']) for e in errors)
        )
    
    def test_invalid_bullet_in_list(self):
        """Test that invalid bullet in list raises validation error."""
        bullets_data = [
            {"order": 1, "text": self.VALID_BULLET_TEXT_1},
            {"order": 2, "text": "short"}
        ]
        with self.assertRaises(ValidationError) as cm:
            BulletListModel(bullets=bullets_data)
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'][0] == 'bullets' and e['loc'][1] == 1 for e in errors)
        )
    
    def test_validate_max_count_within_limit(self):
        """Test that validate_max_count passes when count is within limit."""
        bullets_data = [
            {"order": 1, "text": self.VALID_BULLET_TEXT_1},
            {"order": 2, "text": self.VALID_BULLET_TEXT_2}
        ]
        model = BulletListModel(bullets=bullets_data)
        try:
            model.validate_max_count(max_bullet_count=3)
        except ValueError:
            self.fail("validate_max_count raised ValueError unexpectedly")
    
    def test_validate_max_count_at_limit(self):
        """Test that validate_max_count passes when count equals limit."""
        bullets_data = [
            {"order": 1, "text": self.VALID_BULLET_TEXT_1},
            {"order": 2, "text": self.VALID_BULLET_TEXT_2}
        ]
        model = BulletListModel(bullets=bullets_data)
        try:
            model.validate_max_count(max_bullet_count=2)
        except ValueError:
            self.fail("validate_max_count raised ValueError unexpectedly")
    
    def test_validate_max_count_exceeds_limit(self):
        """Test that validate_max_count raises error when count exceeds limit."""
        bullets_data = [
            {"order": 1, "text": self.VALID_BULLET_TEXT_1},
            {"order": 2, "text": self.VALID_BULLET_TEXT_2},
            {"order": 3, "text": self.VALID_BULLET_TEXT_1}
        ]
        model = BulletListModel(bullets=bullets_data)
        with self.assertRaises(ValueError) as cm:
            model.validate_max_count(max_bullet_count=2)
        self.assertIn("contains 3 bullets", str(cm.exception))
        self.assertIn("maximum allowed is 2", str(cm.exception))
    
    def test_missing_bullets_field(self):
        """Test that missing bullets field raises validation error."""
        with self.assertRaises(ValidationError) as cm:
            BulletListModel()
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('bullets',) and e['type'] == 'missing' for e in errors)
        )
