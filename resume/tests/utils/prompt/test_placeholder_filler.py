import pytest
from resume.utils.prompt import fill_placeholders


class TestFillPlaceholders:
    """Test suite for fill_placeholders() function."""
    
    TEMPLATE = "Hello {{NAME}}, you have {{COUNT}} messages."
    
    def test_replaces_all_placeholders(self) -> None:
        """Validates that all placeholders are correctly replaced."""
        replacements = {"NAME": "Alice", "COUNT": "5"}
        
        result = fill_placeholders(self.TEMPLATE, replacements)
        
        assert result == "Hello Alice, you have 5 messages."
    
    def test_strips_whitespace_from_values(self) -> None:
        """Ensures replacement values are stripped of leading/trailing whitespace."""
        replacements = {"NAME": "  Bob  ", "COUNT": "  10  "}
        
        result = fill_placeholders(self.TEMPLATE, replacements)
        
        assert result == "Hello Bob, you have 10 messages."
    
    def test_raises_error_for_missing_placeholder(self) -> None:
        """Ensures ValueError is raised when a placeholder is not in the template."""
        replacements = {"NAME": "Alice", "COUNT": "5", "EXTRA": "unused"}
        
        with pytest.raises(ValueError, match="Placeholder '{{EXTRA}}' not found"):
            fill_placeholders(self.TEMPLATE, replacements)
    
    def test_handles_empty_template(self) -> None:
        """Validates behavior with an empty template string."""
        result = fill_placeholders("", {})
        
        assert result == ""
