from pathlib import Path


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