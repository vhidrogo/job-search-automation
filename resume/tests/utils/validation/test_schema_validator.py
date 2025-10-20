import pytest
from pydantic import BaseModel, ConfigDict
from resume.utils.validation import validate_with_schema


class SampleSchema(BaseModel):
    """Test schema for validation tests."""
    model_config = ConfigDict(extra='forbid')
    
    name: str
    count: int


class TestValidateWithSchema:
    """Test suite for validate_with_schema() function."""
    
    VALID_DATA = {"name": "Alice", "count": 5}
    
    def test_validates_correct_data(self) -> None:
        """Validates that valid data passes schema validation."""
        result = validate_with_schema(self.VALID_DATA, SampleSchema)
        
        assert isinstance(result, SampleSchema)
        assert result.name == "Alice"
        assert result.count == 5
    
    def test_raises_error_for_missing_required_field(self) -> None:
        """Ensures ValueError is raised when required fields are missing."""
        invalid_data = {"name": "Alice"}
        
        with pytest.raises(ValueError, match="Pydantic validation failed"):
            validate_with_schema(invalid_data, SampleSchema)
    
    def test_raises_error_for_wrong_type(self) -> None:
        """Ensures ValueError is raised when field types don't match schema."""
        invalid_data = {"name": "Alice", "count": "not_an_int"}
        
        with pytest.raises(ValueError, match="Pydantic validation failed"):
            validate_with_schema(invalid_data, SampleSchema)
    
    def test_raises_error_for_extra_fields(self) -> None:
        """Ensures ValueError is raised for extra fields not in schema."""
        invalid_data = {"name": "Alice", "count": 5, "extra": "field"}
        
        with pytest.raises(ValueError, match="Pydantic validation failed"):
            validate_with_schema(invalid_data, SampleSchema)
