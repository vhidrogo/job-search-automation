"""Shared utilities for LLM-based services.

This module provides reusable helper functions for common LLM integration tasks:
- Loading prompt templates from files
- Filling placeholder variables in prompts
- Parsing JSON responses from LLM outputs
- Validating parsed data against Pydantic schemas

These utilities are designed to be shared across JDParser, ResumeWriter, 
ResumeMatcher, and other LLM-integrated services.
"""

import json
from pathlib import Path
from typing import Any, Dict, Type, TypeVar
from pydantic import BaseModel, ValidationError


T = TypeVar('T', bound=BaseModel)


def load_prompt(prompt_path: str) -> str:
    """Load a prompt template from a file.
    
    Args:
        prompt_path: Path to the prompt file (relative or absolute).
        
    Returns:
        The contents of the prompt file as a string.
        
    Raises:
        FileNotFoundError: If the prompt file does not exist.
        IOError: If the file cannot be read.
    """
    path = Path(prompt_path)
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return path.read_text()


def fill_placeholders(template: str, replacements: Dict[str, str]) -> str:
    """Replace placeholder variables in a prompt template.
    
    Placeholders should be in the format {{VARIABLE_NAME}}. All placeholders
    in the template must have corresponding keys in the replacements dict.
    
    Args:
        template: The prompt template string containing placeholders.
        replacements: Dictionary mapping placeholder names to replacement values.
                     Keys should match placeholder names without the {{ }} syntax.
        
    Returns:
        The template string with all placeholders replaced.
        
    Raises:
        ValueError: If any placeholder in the template is not found in replacements.
    """
    result = template
    for key, value in replacements.items():
        placeholder = f"{{{{{key}}}}}"
        if placeholder not in result:
            raise ValueError(
                f"Placeholder '{placeholder}' not found in template"
            )
        result = result.replace(placeholder, str(value).strip())
    return result


def parse_json_response(text: str) -> Dict[str, Any]:
    """Extract and parse JSON from an LLM response.
    
    Handles common LLM response formats including:
    - Plain JSON
    - JSON wrapped in ```json code blocks
    - Responses with extra whitespace
    
    Args:
        text: The raw LLM response text.
        
    Returns:
        The parsed JSON as a Python dictionary.
        
    Raises:
        ValueError: If the response appears truncated (doesn't end with '}').
        ValueError: If the JSON cannot be parsed.
    """
    cleaned = text.replace("```json", "").replace("```", "").strip()
    
    if not cleaned.strip().endswith("}"):
        raise ValueError(
            "LLM output truncated = increase max_tokens or retry."
        )
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse LLM JSON output: {e}\n\n{cleaned}"
        ) from e


def validate_with_schema(data: Dict[str, Any], schema: Type[T]) -> T:
    """Validate parsed JSON data against a Pydantic schema.
    
    Args:
        data: The parsed JSON data as a dictionary.
        schema: The Pydantic model class to validate against.
        
    Returns:
        An instance of the Pydantic model with validated data.
        
    Raises:
        ValueError: If validation fails, with details about validation errors.
    """
    try:
        return schema(**data)
    except ValidationError as e:
        raise ValueError(
            f"Pydantic validation failed: {e.errors()}"
        ) from e