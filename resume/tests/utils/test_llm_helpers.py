import json
import pytest
from pathlib import Path
from pydantic import BaseModel, ConfigDict
from resume.utils.llm_helpers import (
    load_prompt,
    fill_placeholders,
    parse_json_response,
    validate_with_schema,
)


class SampleSchema(BaseModel):
    """Test schema for validation tests."""
    model_config = ConfigDict(extra='forbid')
    
    name: str
    count: int


class TestLoadPrompt:
    """Test suite for load_prompt() function."""
    
    VALID_PROMPT_CONTENT = "Test prompt content"
    
    def test_loads_existing_file(self, tmp_path: Path) -> None:
        """Validates that load_prompt successfully reads an existing file."""
        prompt_file = tmp_path / "test_prompt.md"
        prompt_file.write_text(self.VALID_PROMPT_CONTENT)
        
        result = load_prompt(str(prompt_file))
        
        assert result == self.VALID_PROMPT_CONTENT
    
    def test_raises_file_not_found_for_missing_file(self) -> None:
        """Ensures FileNotFoundError is raised for non-existent files."""
        with pytest.raises(FileNotFoundError, match="Prompt file not found"):
            load_prompt("/nonexistent/path/prompt.md")


class TestFillPlaceholders:
    """Test suite for fill_placeholders() function."""
    
    TEMPLATE = "Hello {{NAME}}, you have {{COUNT}} messages."
    
    def test_replaces_all_placeholders(self) -> None:
        """Validates that all placeholders are correctly replaced."""
        replacements = {"NAME": "Alice", "COUNT": "5"}
        
        result = fill_placeholders(self.TEMPLATE, replacements)
        
        assert result == "Hello Alice, you have 5 messages."
    
    def test_strips_whitespace_from_values(self) -> None:
        """Ensures replacement values are stripped of leading/trailing whitespace."""
        replacements = {"NAME": "  Bob  ", "COUNT": "  10  "}
        
        result = fill_placeholders(self.TEMPLATE, replacements)
        
        assert result == "Hello Bob, you have 10 messages."
    
    def test_raises_error_for_missing_placeholder(self) -> None:
        """Ensures ValueError is raised when a placeholder is not in the template."""
        replacements = {"NAME": "Alice", "COUNT": "5", "EXTRA": "unused"}
        
        with pytest.raises(ValueError, match="Placeholder '{{EXTRA}}' not found"):
            fill_placeholders(self.TEMPLATE, replacements)
    
    def test_handles_empty_template(self) -> None:
        """Validates behavior with an empty template string."""
        result = fill_placeholders("", {})
        
        assert result == ""


class TestParseJsonResponse:
    """Test suite for parse_json_response() function."""
    
    VALID_JSON_OBJECT = {"key": "value", "count": 42}
    VALID_JSON_ARRAY = [{"id": 1, "name": "first"}, {"id": 2, "name": "second"}]
    
    def test_parses_plain_json_object(self) -> None:
        """Validates parsing of plain JSON object text."""
        json_text = json.dumps(self.VALID_JSON_OBJECT)
        
        result = parse_json_response(json_text)
        
        assert result == self.VALID_JSON_OBJECT
    
    def test_parses_plain_json_array(self) -> None:
        """Validates parsing of plain JSON array text."""
        json_text = json.dumps(self.VALID_JSON_ARRAY)
        
        result = parse_json_response(json_text)
        
        assert result == self.VALID_JSON_ARRAY
    
    def test_parses_json_object_with_code_blocks(self) -> None:
        """Validates parsing of JSON object wrapped in markdown code blocks."""
        json_text = f"```json\n{json.dumps(self.VALID_JSON_OBJECT)}\n```"
        
        result = parse_json_response(json_text)
        
        assert result == self.VALID_JSON_OBJECT
    
    def test_parses_json_array_with_code_blocks(self) -> None:
        """Validates parsing of JSON array wrapped in markdown code blocks."""
        json_text = f"```json\n{json.dumps(self.VALID_JSON_ARRAY)}\n```"
        
        result = parse_json_response(json_text)
        
        assert result == self.VALID_JSON_ARRAY
    
    def test_parses_json_object_with_extra_whitespace(self) -> None:
        """Validates parsing of JSON object with leading/trailing whitespace."""
        json_text = f"\n\n  {json.dumps(self.VALID_JSON_OBJECT)}  \n\n"
        
        result = parse_json_response(json_text)
        
        assert result == self.VALID_JSON_OBJECT
    
    def test_parses_json_array_with_extra_whitespace(self) -> None:
        """Validates parsing of JSON array with leading/trailing whitespace."""
        json_text = f"\n\n  {json.dumps(self.VALID_JSON_ARRAY)}  \n\n"
        
        result = parse_json_response(json_text)
        
        assert result == self.VALID_JSON_ARRAY
    
    def test_raises_error_for_truncated_object(self) -> None:
        """Ensures ValueError is raised for incomplete JSON object (missing closing brace)."""
        truncated_json = '{"key": "value", "count": 42'
        
        with pytest.raises(ValueError, match="LLM output truncated"):
            parse_json_response(truncated_json)
    
    def test_raises_error_for_truncated_array(self) -> None:
        """Ensures ValueError is raised for incomplete JSON array (missing closing bracket)."""
        truncated_json = '[{"id": 1}, {"id": 2'
        
        with pytest.raises(ValueError, match="LLM output truncated"):
            parse_json_response(truncated_json)
    
    def test_raises_error_for_invalid_json(self) -> None:
        """Ensures ValueError is raised for malformed JSON."""
        invalid_json = '{"key": "value", invalid}'
        
        with pytest.raises(ValueError, match="Failed to parse LLM JSON output"):
            parse_json_response(invalid_json)
    
    def test_handles_nested_json_object(self) -> None:
        """Validates parsing of deeply nested JSON object structures."""
        nested_json = {"outer": {"inner": {"deep": "value"}}}
        json_text = json.dumps(nested_json)
        
        result = parse_json_response(json_text)
        
        assert result == nested_json
    
    def test_handles_nested_json_array(self) -> None:
        """Validates parsing of nested JSON array structures."""
        nested_array = [{"items": [1, 2, 3]}, {"items": [4, 5, 6]}]
        json_text = json.dumps(nested_array)
        
        result = parse_json_response(json_text)
        
        assert result == nested_array


class TestValidateWithSchema:
    """Test suite for validate_with_schema() function."""
    
    VALID_DATA = {"name": "Alice", "count": 5}
    
    def test_validates_correct_data(self) -> None:
        """Validates that valid data passes schema validation."""
        result = validate_with_schema(self.VALID_DATA, SampleSchema)
        
        assert isinstance(result, SampleSchema)
        assert result.name == "Alice"
        assert result.count == 5
    
    def test_raises_error_for_missing_required_field(self) -> None:
        """Ensures ValueError is raised when required fields are missing."""
        invalid_data = {"name": "Alice"}
        
        with pytest.raises(ValueError, match="Pydantic validation failed"):
            validate_with_schema(invalid_data, SampleSchema)
    
    def test_raises_error_for_wrong_type(self) -> None:
        """Ensures ValueError is raised when field types don't match schema."""
        invalid_data = {"name": "Alice", "count": "not_an_int"}
        
        with pytest.raises(ValueError, match="Pydantic validation failed"):
            validate_with_schema(invalid_data, SampleSchema)
    
    def test_raises_error_for_extra_fields(self) -> None:
        """Ensures ValueError is raised for extra fields not in schema."""
        invalid_data = {"name": "Alice", "count": 5, "extra": "field"}
        
        with pytest.raises(ValueError, match="Pydantic validation failed"):
            validate_with_schema(invalid_data, SampleSchema)
