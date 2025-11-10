import pytest
from unittest.mock import ANY, Mock

from resume.clients import ClaudeClient
from resume.schemas import JDModel
from resume.services import JDParser
from tracker.models import LlmRequestLog


class TestJDParser:
    MOCK_JD_TEXT = "some JD text"
    MOCK_LLM_RESPONSE = '{"mocked": "response"}'
    MOCK_PARSED_JSON = {"mocked": "response"}
    MOCK_PROMPT = "filled prompt"
    MOCK_TEMPLATE = "prompt with placeholder"

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        self.mock_load_prompt = Mock(return_value=self.MOCK_TEMPLATE)
        self.mock_fill_placeholders = Mock(return_value=self.MOCK_PROMPT)
        self.mock_parse_llm_json = Mock(return_value=self.MOCK_PARSED_JSON)

        self.mock_jd_model = Mock(spec=JDModel)
        self.mock_validate_with_schema = Mock(return_value=self.mock_jd_model)

        monkeypatch.setattr("resume.services.jd_parser.load_prompt", self.mock_load_prompt)
        monkeypatch.setattr("resume.services.jd_parser.fill_placeholders", self.mock_fill_placeholders)
        monkeypatch.setattr("resume.services.jd_parser.parse_llm_json", self.mock_parse_llm_json)
        monkeypatch.setattr("resume.services.jd_parser.validate_with_schema", self.mock_validate_with_schema)

        self.mock_client = Mock(spec=ClaudeClient)
        self.mock_client.generate.return_value = self.MOCK_LLM_RESPONSE
        self.parser = JDParser(client=self.mock_client)

    def test_parse_returns_validated_data(self):
        result = self.parser.parse(jd_text=self.MOCK_JD_TEXT)

        self.mock_load_prompt.assert_called_once_with(self.parser.prompt_path)
        self.mock_fill_placeholders.assert_called_once_with(
            self.MOCK_TEMPLATE,
            {self.parser.placeholder: self.MOCK_JD_TEXT},
        )
        self.mock_client.generate.assert_called_once_with(
            self.MOCK_PROMPT,
            call_type=LlmRequestLog.CallType.PARSE_JD,
            model=ANY,
            max_tokens=ANY,
        )
        self.mock_parse_llm_json.assert_called_once_with(self.MOCK_LLM_RESPONSE)
        self.mock_validate_with_schema.assert_called_once_with(self.MOCK_PARSED_JSON, JDModel)
        assert result == self.mock_jd_model

    def test_parse_raises_when_no_path_or_text_provided(self):
        with pytest.raises(ValueError, match="Provide either jd_source"):
            self.parser.parse()
            