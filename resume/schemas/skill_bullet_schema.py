from typing import Annotated, List
from pydantic import BaseModel, Field, field_validator


class SkillCategorySchema(BaseModel):
    """Represents a single skill category with associated skills.
    
    This schema validates individual skill categories returned by the LLM,
    ensuring they contain meaningful category names and valid skill lists.
    """
    
    order: Annotated[int, Field(ge=1, description="Relevance ranking, starting from 1")]
    category: Annotated[
        str,
        Field(
            min_length=3,
            max_length=100,
            description="The skill category name (e.g., 'Programming Languages')"
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
    
    @field_validator('category')
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
    
    @field_validator('skills')
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


class SkillBulletListModel(BaseModel):
    """Represents the complete response from the LLM containing multiple skill categories.
    
    This schema validates that the LLM returns a properly structured list of skill
    categories and enforces constraints on the total number of categories generated.
    """
    
    skill_categories: List[SkillCategorySchema] = Field(
        description="List of generated skill categories"
    )
    
    @field_validator('skill_categories')
    @classmethod
    def validate_category_count(cls, v: List[SkillCategorySchema]) -> List[SkillCategorySchema]:
        """Ensure at least one skill category is returned.
        
        Args:
            v: The list of skill categories to validate.
            
        Returns:
            The validated list of skill categories.
            
        Raises:
            ValueError: If the list is empty.
        """
        if not v:
            raise ValueError("Response must contain at least one skill category")
        return v
    
    def validate_max_count(self, max_category_count: int) -> None:
        """Validate that the number of categories does not exceed the configured maximum.
        
        Args:
            max_category_count: The maximum allowed number of skill categories.
            
        Raises:
            ValueError: If the category count exceeds the maximum.
        """
        if len(self.skill_categories) > max_category_count:
            raise ValueError(
                f"Response contains {len(self.skill_categories)} skill categories, "
                f"but maximum allowed is {max_category_count}"
            )
