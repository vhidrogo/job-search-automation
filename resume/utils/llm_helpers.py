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
from typing import Any, Dict, Type, TypeVar
from pydantic import BaseModel, ValidationError


T = TypeVar('T', bound=BaseModel)


def parse_json_response(text: str) -> Dict[str, Any]:
    """Extract and parse JSON from an LLM response.
    
    Handles common LLM response formats including:
    - Plain JSON objects or arrays
    - JSON wrapped in ```json code blocks
    - Responses with extra whitespace
    
    Args:
        text: The raw LLM response text.
        
    Returns:
        The parsed JSON as a Python dictionary or list.
        
    Raises:
        ValueError: If the response appears truncated (doesn't end with '}' or ']').
        ValueError: If the JSON cannot be parsed.
    """
    cleaned = text.replace("```json", "").replace("```", "").strip()
    
    if not (cleaned.endswith("}") or cleaned.endswith("]")):
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
