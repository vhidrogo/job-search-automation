"""Shared utilities for LLM-based services.

This module provides reusable helper functions for common LLM integration tasks:
- Loading prompt templates from files
- Filling placeholder variables in prompts
- Parsing JSON responses from LLM outputs
- Validating parsed data against Pydantic schemas

These utilities are designed to be shared across JDParser, ResumeWriter, 
ResumeMatcher, and other LLM-integrated services.
"""

from typing import Any, Dict, Type, TypeVar
from pydantic import BaseModel, ValidationError


T = TypeVar('T', bound=BaseModel)


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
