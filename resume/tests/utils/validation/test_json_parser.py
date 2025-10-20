import json
import pytest
from resume.utils.validation import parse_llm_json


class TestParseLLMJson:
    """Test suite for parse_llm_json() function."""
    
    VALID_JSON_OBJECT = {"key": "value", "count": 42}
    VALID_JSON_ARRAY = [{"id": 1, "name": "first"}, {"id": 2, "name": "second"}]
    
    def test_parses_plain_json_object(self) -> None:
        """Validates parsing of plain JSON object text."""
        json_text = json.dumps(self.VALID_JSON_OBJECT)
        
        result = parse_llm_json(json_text)
        
        assert result == self.VALID_JSON_OBJECT
    
    def test_parses_plain_json_array(self) -> None:
        """Validates parsing of plain JSON array text."""
        json_text = json.dumps(self.VALID_JSON_ARRAY)
        
        result = parse_llm_json(json_text)
        
        assert result == self.VALID_JSON_ARRAY
    
    def test_parses_json_object_with_code_blocks(self) -> None:
        """Validates parsing of JSON object wrapped in markdown code blocks."""
        json_text = f"```json\n{json.dumps(self.VALID_JSON_OBJECT)}\n```"
        
        result = parse_llm_json(json_text)
        
        assert result == self.VALID_JSON_OBJECT
    
    def test_parses_json_array_with_code_blocks(self) -> None:
        """Validates parsing of JSON array wrapped in markdown code blocks."""
        json_text = f"```json\n{json.dumps(self.VALID_JSON_ARRAY)}\n```"
        
        result = parse_llm_json(json_text)
        
        assert result == self.VALID_JSON_ARRAY
    
    def test_parses_json_object_with_extra_whitespace(self) -> None:
        """Validates parsing of JSON object with leading/trailing whitespace."""
        json_text = f"\n\n  {json.dumps(self.VALID_JSON_OBJECT)}  \n\n"
        
        result = parse_llm_json(json_text)
        
        assert result == self.VALID_JSON_OBJECT
    
    def test_parses_json_array_with_extra_whitespace(self) -> None:
        """Validates parsing of JSON array with leading/trailing whitespace."""
        json_text = f"\n\n  {json.dumps(self.VALID_JSON_ARRAY)}  \n\n"
        
        result = parse_llm_json(json_text)
        
        assert result == self.VALID_JSON_ARRAY
    
    def test_raises_error_for_truncated_object(self) -> None:
        """Ensures ValueError is raised for incomplete JSON object (missing closing brace)."""
        truncated_json = '{"key": "value", "count": 42'
        
        with pytest.raises(ValueError, match="LLM output truncated"):
            parse_llm_json(truncated_json)
    
    def test_raises_error_for_truncated_array(self) -> None:
        """Ensures ValueError is raised for incomplete JSON array (missing closing bracket)."""
        truncated_json = '[{"id": 1}, {"id": 2'
        
        with pytest.raises(ValueError, match="LLM output truncated"):
            parse_llm_json(truncated_json)
    
    def test_raises_error_for_invalid_json(self) -> None:
        """Ensures ValueError is raised for malformed JSON."""
        invalid_json = '{"key": "value", invalid}'
        
        with pytest.raises(ValueError, match="Failed to parse LLM JSON output"):
            parse_llm_json(invalid_json)
    
    def test_handles_nested_json_object(self) -> None:
        """Validates parsing of deeply nested JSON object structures."""
        nested_json = {"outer": {"inner": {"deep": "value"}}}
        json_text = json.dumps(nested_json)
        
        result = parse_llm_json(json_text)
        
        assert result == nested_json
    
    def test_handles_nested_json_array(self) -> None:
        """Validates parsing of nested JSON array structures."""
        nested_array = [{"items": [1, 2, 3]}, {"items": [4, 5, 6]}]
        json_text = json.dumps(nested_array)
        
        result = parse_llm_json(json_text)
        
        assert result == nested_array