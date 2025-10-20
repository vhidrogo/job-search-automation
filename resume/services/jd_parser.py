from pathlib import Path
from resume.schemas.jd_schema import JDModel
from resume.clients.llm_client import ClaudeClient
from resume.utils.prompt import fill_placeholders
from resume.utils.llm_helpers import (
    load_prompt,
    parse_json_response,
    validate_with_schema,
)


class JDParser:
    """Parses job descriptions using an LLM to extract structured requirements and metadata.
    
    This service coordinates LLM calls to transform unstructured job description text
    into validated, structured data (JDModel) containing company metadata, job requirements,
    and relevance scores. It uses shared LLM helper utilities for prompt management,
    placeholder replacement, JSON parsing, and schema validation.
    """
    
    def __init__(
        self,
        client: ClaudeClient = None,
        prompt_path: str = "resume/prompts/parse_jd.md",
        placeholder: str = "JOB_DESCRIPTION",
    ):
        """Initialize the JD parser.
        
        Args:
            client: LLM client for API calls. Defaults to ClaudeClient if not provided.
            prompt_path: Path to the prompt template file.
            placeholder: Name of the placeholder variable in the prompt (without {{ }}).
        """
        self.client = client or ClaudeClient()
        self.prompt_path = prompt_path
        self.placeholder = placeholder
    
    def parse(
        self,
        jd_source: str = None,
        jd_text: str = None,
        model: str = None,
    ) -> JDModel:
        """Parse a job description into structured requirements and metadata.
        
        Args:
            jd_source: Path to a file containing the job description text.
            jd_text: Raw job description text as a string.
            model: Optional LLM model identifier to use for parsing.
            
        Returns:
            Validated JDModel instance containing parsed requirements and metadata.
            
        Raises:
            ValueError: If neither jd_source nor jd_text is provided.
            ValueError: If LLM output is truncated or malformed.
            ValueError: If parsed JSON fails schema validation.
        """
        if not jd_text and not jd_source:
            raise ValueError("Provide either jd_source (path) or jd_text (string)")
        
        jd_content = jd_text or Path(jd_source).read_text()
        
        prompt_template = load_prompt(self.prompt_path)
        prompt = fill_placeholders(prompt_template, {self.placeholder: jd_content})
        
        response_text = self.client.generate(prompt, model=model, max_tokens=4000)
        parsed_data = parse_json_response(response_text)
        validated_data = validate_with_schema(parsed_data, JDModel)
        
        return validated_data
