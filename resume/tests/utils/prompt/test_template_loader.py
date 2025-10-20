import pytest
from pathlib import Path

from resume.utils.prompt import load_prompt


class TestLoadPrompt:
    """Test suite for load_prompt() function."""
    
    VALID_PROMPT_CONTENT = "Test prompt content"
    
    def test_loads_existing_file(self, tmp_path: Path) -> None:
        """Validates that load_prompt successfully reads an existing file."""
        prompt_file = tmp_path / "test_prompt.md"
        prompt_file.write_text(self.VALID_PROMPT_CONTENT)
        
        result = load_prompt(str(prompt_file))
        
        assert result == self.VALID_PROMPT_CONTENT
    
    def test_raises_file_not_found_for_missing_file(self) -> None:
        """Ensures FileNotFoundError is raised for non-existent files."""
        with pytest.raises(FileNotFoundError, match="Prompt file not found"):
            load_prompt("/nonexistent/path/prompt.md")