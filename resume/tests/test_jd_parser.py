import json
import pytest
from unittest.mock import MagicMock
from resume.utils.jd_parser import JDParser
from resume.schemas.jd_schema import JDModel


class TestJDParser:
    """Unit test suite for the JDParser util, ensuring robust validation,
    parsing, and error handling behavior across all key failure modes.
    """

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up a fresh JDParser instance with a mocked LLM client for each test."""
        self.parser = JDParser()
        self.parser.client = MagicMock()

    def test_happy_path(self) -> None:
        """Validates that JDParser correctly parses and validates a well-formed LLM JSON output."""
        valid_json = {
            "metadata": {
                "company": "Meta",
                "listing_job_title": "Software Engineer",
                "role": "Software Engineer",
                "work_setting": "Remote"
            },
            "requirements": [
                {"text": "Strong Python skills", "keywords": ["Python"], "relevance": 0.9, "order": 1}
            ]
        }

        self.parser.client.generate.return_value = json.dumps(valid_json)
        result: JDModel = self.parser.parse(jd_text="some job text")

        assert result.metadata.company == "Meta"
        assert result.requirements[0].keywords == ["Python"]
        assert result.metadata.work_setting == "Remote"

    def test_missing_input_raises_value_error(self) -> None:
        """Ensures that calling parse() without jd_text or jd_source raises a ValueError."""
        with pytest.raises(ValueError, match="Provide either jd_source"):
            self.parser.parse()

    def test_truncated_output_raises_value_error(self) -> None:
        """Simulates an incomplete LLM response and verifies a truncation error is raised."""
        self.parser.client.generate.return_value = '{"metadata": {"company": "Meta"'
        with pytest.raises(ValueError, match="LLM output truncated"):
            self.parser.parse(jd_text="some text")

    def test_invalid_json_raises_value_error(self) -> None:
        """Verifies that an invalid (non-JSON) LLM output raises a descriptive ValueError."""
        self.parser.client.generate.return_value = "{invalid json}"
        with pytest.raises(ValueError, match="Failed to parse LLM JSON output"):
            self.parser.parse(jd_text="some text")

    def test_invalid_schema_raises_value_error(self) -> None:
        """Ensures that when JSON passes parsing but fails Pydantic validation, a ValueError is raised."""
        invalid_json = {"metadata": {}, "requirements": []}
        self.parser.client.generate.return_value = json.dumps(invalid_json)
        with pytest.raises(ValueError, match="Pydantic validation failed"):
            self.parser.parse(jd_text="some text")
