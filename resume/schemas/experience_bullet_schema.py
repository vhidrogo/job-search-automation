from typing import Annotated, List
from pydantic import BaseModel, Field, field_validator


class ExperienceBullet(BaseModel):
    """Represents a single generated experience bullet for a resume.
    
    This schema validates individual bullet points returned by the LLM,
    ensuring they contain meaningful text and proper ordering for display.
    """
    
    order: Annotated[int, Field(ge=1, description="Priority ranking, starting from 1")]
    text: Annotated[
        str,
        Field(
            min_length=20,
            max_length=500,
            description="The bullet point text describing work accomplished"
        )
    ]
    
    @field_validator('text')
    @classmethod
    def validate_text_quality(cls, v: str) -> str:
        """Ensure bullet text is non-empty after stripping whitespace.
        
        Args:
            v: The bullet text to validate.
            
        Returns:
            The validated and stripped bullet text.
            
        Raises:
            ValueError: If the text is empty or contains only whitespace.
        """
        stripped = v.strip()
        if not stripped:
            raise ValueError("Bullet text cannot be empty or whitespace-only")
        return stripped


class BulletListModel(BaseModel):
    """Represents the complete response from the LLM containing multiple experience bullets.
    
    This schema validates that the LLM returns a properly structured list of bullets
    and enforces constraints on the total number of bullets generated.
    """
    
    bullets: List[ExperienceBullet] = Field(
        description="List of generated experience bullets"
    )
    
    @field_validator('bullets')
    @classmethod
    def validate_bullet_count(cls, v: List[ExperienceBullet]) -> List[ExperienceBullet]:
        """Ensure at least one bullet is returned.
        
        Args:
            v: The list of bullets to validate.
            
        Returns:
            The validated list of bullets.
            
        Raises:
            ValueError: If the list is empty.
        """
        if not v:
            raise ValueError("Response must contain at least one bullet")
        return v
    
    def validate_max_count(self, max_bullet_count: int) -> None:
        """Validate that the number of bullets does not exceed the configured maximum.
        
        Args:
            max_bullet_count: The maximum allowed number of bullets.
            
        Raises:
            ValueError: If the bullet count exceeds the maximum.
        """
        if len(self.bullets) > max_bullet_count:
            raise ValueError(
                f"Response contains {len(self.bullets)} bullets, "
                f"but maximum allowed is {max_bullet_count}"
            )
