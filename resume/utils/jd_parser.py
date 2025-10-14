import json
from pathlib import Path
from pydantic import ValidationError
from resume.schemas.jd_schema import JDModel
from resume.services.llm_client import ClaudeClient

class JDParser:
    def __init__(
            self, 
            client: ClaudeClient = None, 
            prompt_path: str = "resume/prompts/parse_jd.md",
            placeholder: str = "{{JOB_DESCRIPTION}}",
            ):
        self.client = client or ClaudeClient()
        self.prompt_path = Path(prompt_path)
        self.placeholder = placeholder

    def _load_prompt(self) -> str:
        return self.prompt_path.read_text()
    
    def _insert_jd(self, jd_text: str) -> str:
        prompt_template = self._load_prompt()

        return prompt_template.replace(self.placeholder, jd_text.strip())
    
    def _parse_json_response(self, text: str):
        text = text.replace("```json", "").replace("```", "").strip()

        if not text.strip().endswith("}"):
            raise ValueError("LLM output truncated = increase max_tokens or retry.")

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM JSON output: {e}\n\n{text}")
        
    def _validate_schema(self, data: dict) -> JDModel:
        try:
            return JDModel(**data)
        except ValidationError as e:
            raise ValueError(f"Pydantic validation failed: {e.errors()}") from e
    
    def parse(self, jd_source: str = None, jd_text: str = None, model: str = None):
        if not jd_text and not jd_source:
            raise ValueError("Provide either jd_source (path) or jd_text (string)")
        
        jd_content = jd_text or Path(jd_source).read_text()
        prompt = self._insert_jd(jd_content)
        response_text = self.client.generate(prompt, model=model, max_tokens=4000)
        parsed_data = self._parse_json_response(response_text)
        validated_data = self._validate_schema(parsed_data)
        
        return validated_data