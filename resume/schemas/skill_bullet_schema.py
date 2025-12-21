from typing import Annotated, List
from pydantic import BaseModel, Field, field_validator


class SkillsCategorySchema(BaseModel):
    """Represents a single skills category with associated skills.
    
    This schema validates individual skills categories returned by the LLM,
    ensuring they contain meaningful category names and valid skills lists.
    """
    
    order: Annotated[int, Field(ge=1, description="Relevance ranking, starting from 1")]
    category: Annotated[
        str,
        Field(
            min_length=3,
            max_length=100,
            description="The skills category name (e.g., 'Programming Languages')"
        )
    ]
    skills: Annotated[
        str,
        Field(
            min_length=2,
            max_length=500,
            description="Comma-separated list of technical skills"
        )
    ]
    
    @field_validator("category")
    @classmethod
    def validate_category_quality(cls, v: str) -> str:
        """Ensure category name is non-empty after stripping whitespace.
        
        Args:
            v: The category name to validate.
            
        Returns:
            The validated and stripped category name.
            
        Raises:
            ValueError: If the category is empty or contains only whitespace.
        """
        stripped = v.strip()
        if not stripped:
            raise ValueError("Category name cannot be empty or whitespace-only")
        return stripped
    
    @field_validator("skills")
    @classmethod
    def validate_skills_quality(cls, v: str) -> str:
        """Ensure skills string is non-empty after stripping whitespace.
        
        Args:
            v: The skills string to validate.
            
        Returns:
            The validated and stripped skills string.
            
        Raises:
            ValueError: If the skills string is empty or contains only whitespace.
        """
        stripped = v.strip()
        if not stripped:
            raise ValueError("Skills string cannot be empty or whitespace-only")
        return stripped


class SkillsListModel(BaseModel):
    """Represents the complete response from the LLM containing multiple skills categories.
    
    This schema validates that the LLM returns a properly structured list of skills
    categories and enforces constraints on the total number of categories generated.
    """
    
    skills_categories: List[SkillsCategorySchema] = Field(
        description="List of generated skills categories"
    )
    
    @field_validator("skills_categories")
    @classmethod
    def validate_category_count(cls, v: List[SkillsCategorySchema]) -> List[SkillsCategorySchema]:
        """Ensure at least one skills category is returned.
        
        Args:
            v: The list of skills categories to validate.
            
        Returns:
            The validated list of skills categories.
            
        Raises:
            ValueError: If the list is empty.
        """
        if not v:
            raise ValueError("Response must contain at least one skills category")
        return v
    
    def validate_max_count(self, max_category_count: int) -> None:
        """Validate that the number of categories does not exceed the configured maximum.
        
        Args:
            max_category_count: The maximum allowed number of skills categories.
            
        Raises:
            ValueError: If the category count exceeds the maximum.
        """
        if len(self.skills_categories) > max_category_count:
            raise ValueError(
                f"Response contains {len(self.skills_categories)} skills categories, "
                f"but maximum allowed is {max_category_count}"
            )
