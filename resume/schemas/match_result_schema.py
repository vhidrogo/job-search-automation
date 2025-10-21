from typing import Annotated
from pydantic import BaseModel, Field, field_validator


class MatchResultSchema(BaseModel):
    """Represents the LLM evaluation result comparing requirements against generated resume content.
    
    This schema validates that the LLM returns properly formatted match evaluation data
    with valid unmet requirements and a normalized match ratio.
    """
    
    unmet_requirements: Annotated[
        str,
        Field(
            description="CSV string of requirement keywords not covered by the resume"
        )
    ]
    match_ratio: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            description="Fraction of requirements met (0.0 to 1.0)"
        )
    ]
    
    @field_validator('unmet_requirements')
    @classmethod
    def validate_unmet_requirements(cls, v: str) -> str:
        """Strip whitespace from unmet requirements string.
        
        Args:
            v: The unmet requirements CSV string to validate.
            
        Returns:
            The validated and stripped unmet requirements string.
        """
        return v.strip()
    
    @field_validator('match_ratio')
    @classmethod
    def validate_match_ratio_precision(cls, v: float) -> float:
        """Round match ratio to 2 decimal places.
        
        Args:
            v: The match ratio to validate.
            
        Returns:
            The match ratio rounded to 2 decimal places.
        """
        return round(v, 2)
