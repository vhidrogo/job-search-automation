from unittest import TestCase
from pydantic import ValidationError
from resume.schemas import MatchResultSchema


class TestMatchResultSchema(TestCase):
    """Test suite for MatchResultSchema validation."""
    
    VALID_UNMET_REQUIREMENTS = "Go,Kubernetes,Terraform"
    VALID_MATCH_RATIO = 0.75
    EMPTY_UNMET_REQUIREMENTS = ""
    PERFECT_MATCH_RATIO = 1.0
    ZERO_MATCH_RATIO = 0.0
    NEGATIVE_MATCH_RATIO = -0.1
    ABOVE_ONE_MATCH_RATIO = 1.1
    UNROUNDED_MATCH_RATIO = 0.666666
    WHITESPACE_UNMET = "   Go, Kubernetes   "
    
    def test_valid_match_result(self):
        """Test that valid match result data passes validation."""
        result = MatchResultSchema(
            unmet_requirements=self.VALID_UNMET_REQUIREMENTS,
            match_ratio=self.VALID_MATCH_RATIO
        )
        self.assertEqual(result.unmet_requirements, self.VALID_UNMET_REQUIREMENTS)
        self.assertEqual(result.match_ratio, self.VALID_MATCH_RATIO)
    
    def test_empty_unmet_requirements_valid(self):
        """Test that empty unmet requirements string is valid."""
        result = MatchResultSchema(
            unmet_requirements=self.EMPTY_UNMET_REQUIREMENTS,
            match_ratio=self.PERFECT_MATCH_RATIO
        )
        self.assertEqual(result.unmet_requirements, self.EMPTY_UNMET_REQUIREMENTS)
        self.assertEqual(result.match_ratio, self.PERFECT_MATCH_RATIO)
    
    def test_unmet_requirements_stripped(self):
        """Test that whitespace is stripped from unmet requirements."""
        result = MatchResultSchema(
            unmet_requirements=self.WHITESPACE_UNMET,
            match_ratio=self.VALID_MATCH_RATIO
        )
        self.assertEqual(result.unmet_requirements, "Go, Kubernetes")
    
    def test_match_ratio_rounded_to_two_decimals(self):
        """Test that match ratio is rounded to 2 decimal places."""
        result = MatchResultSchema(
            unmet_requirements=self.VALID_UNMET_REQUIREMENTS,
            match_ratio=self.UNROUNDED_MATCH_RATIO
        )
        self.assertEqual(result.match_ratio, 0.67)
    
    def test_match_ratio_at_zero(self):
        """Test that match ratio of 0.0 is valid."""
        result = MatchResultSchema(
            unmet_requirements=self.VALID_UNMET_REQUIREMENTS,
            match_ratio=self.ZERO_MATCH_RATIO
        )
        self.assertEqual(result.match_ratio, self.ZERO_MATCH_RATIO)
    
    def test_match_ratio_at_one(self):
        """Test that match ratio of 1.0 is valid."""
        result = MatchResultSchema(
            unmet_requirements=self.EMPTY_UNMET_REQUIREMENTS,
            match_ratio=self.PERFECT_MATCH_RATIO
        )
        self.assertEqual(result.match_ratio, self.PERFECT_MATCH_RATIO)
    
    def test_match_ratio_below_zero_fails(self):
        """Test that negative match ratio raises validation error."""
        with self.assertRaises(ValidationError) as cm:
            MatchResultSchema(
                unmet_requirements=self.VALID_UNMET_REQUIREMENTS,
                match_ratio=self.NEGATIVE_MATCH_RATIO
            )
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('match_ratio',) and 'greater than or equal to 0' in str(e['msg']) for e in errors)
        )
    
    def test_match_ratio_above_one_fails(self):
        """Test that match ratio above 1.0 raises validation error."""
        with self.assertRaises(ValidationError) as cm:
            MatchResultSchema(
                unmet_requirements=self.EMPTY_UNMET_REQUIREMENTS,
                match_ratio=self.ABOVE_ONE_MATCH_RATIO
            )
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('match_ratio',) and 'less than or equal to 1' in str(e['msg']) for e in errors)
        )
    
    def test_missing_unmet_requirements_field(self):
        """Test that missing unmet_requirements field raises validation error."""
        with self.assertRaises(ValidationError) as cm:
            MatchResultSchema(match_ratio=self.VALID_MATCH_RATIO)
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('unmet_requirements',) and e['type'] == 'missing' for e in errors)
        )
    
    def test_missing_match_ratio_field(self):
        """Test that missing match_ratio field raises validation error."""
        with self.assertRaises(ValidationError) as cm:
            MatchResultSchema(unmet_requirements=self.VALID_UNMET_REQUIREMENTS)
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('match_ratio',) and e['type'] == 'missing' for e in errors)
        )
    
    def test_invalid_match_ratio_type(self):
        """Test that non-numeric match ratio raises validation error."""
        with self.assertRaises(ValidationError) as cm:
            MatchResultSchema(
                unmet_requirements=self.VALID_UNMET_REQUIREMENTS,
                match_ratio="invalid"
            )
        errors = cm.exception.errors()
        self.assertTrue(
            any(e['loc'] == ('match_ratio',) for e in errors)
        )
