import json
import pytest
from resume.utils.validation import parse_llm_json


class TestParseLLMJson:
    VALID_JSON_OBJECT = {"key": "value", "count": 42}
    VALID_JSON_ARRAY = [{"id": 1, "name": "first"}, {"id": 2, "name": "second"}]
    
    def test_parses_plain_json_object(self):
        json_text = json.dumps(self.VALID_JSON_OBJECT)
        result = parse_llm_json(json_text)
        assert result == self.VALID_JSON_OBJECT
    
    def test_parses_plain_json_array(self):
        json_text = json.dumps(self.VALID_JSON_ARRAY)
        result = parse_llm_json(json_text)
        assert result == self.VALID_JSON_ARRAY
    
    def test_parses_json_object_with_code_blocks(self):
        json_text = f"```json\n{json.dumps(self.VALID_JSON_OBJECT)}\n```"
        result = parse_llm_json(json_text)
        assert result == self.VALID_JSON_OBJECT
    
    def test_parses_json_array_with_code_blocks(self):
        json_text = f"```json\n{json.dumps(self.VALID_JSON_ARRAY)}\n```"
        result = parse_llm_json(json_text)
        assert result == self.VALID_JSON_ARRAY
    
    def test_parses_json_object_with_extra_whitespace(self):
        json_text = f"\n\n  {json.dumps(self.VALID_JSON_OBJECT)}  \n\n"
        result = parse_llm_json(json_text)
        assert result == self.VALID_JSON_OBJECT
    
    def test_parses_json_array_with_extra_whitespace(self):
        json_text = f"\n\n  {json.dumps(self.VALID_JSON_ARRAY)}  \n\n"
        result = parse_llm_json(json_text)
        assert result == self.VALID_JSON_ARRAY
    
    def test_raises_error_for_truncated_object(self):
        truncated_json = '{"key": "value", "count": 42'
        with pytest.raises(ValueError, match="LLM output truncated"):
            parse_llm_json(truncated_json)
    
    def test_raises_error_for_truncated_array(self):
        truncated_json = '[{"id": 1}, {"id": 2'
        with pytest.raises(ValueError, match="LLM output truncated"):
            parse_llm_json(truncated_json)

    def test_repairs_invalid_json_if_possible(self):
        repairable_invalid_json = '{"key": "value"]'
        result = parse_llm_json(repairable_invalid_json)
        assert result == {'key': 'value'}
    
    def test_raises_error_for_invalid_unrepairable_json(self):
        invalid_json = 'unrepairable json]'
        with pytest.raises(ValueError, match="Failed to parse or repair LLM JSON output"):
            parse_llm_json(invalid_json)
    
    def test_handles_nested_json_object(self):
        nested_json = {"outer": {"inner": {"deep": "value"}}}
        json_text = json.dumps(nested_json)
        result = parse_llm_json(json_text)
        assert result == nested_json
    
    def test_handles_nested_json_array(self):
        nested_array = [{"items": [1, 2, 3]}, {"items": [4, 5, 6]}]
        json_text = json.dumps(nested_array)
        result = parse_llm_json(json_text)
        assert result == nested_array