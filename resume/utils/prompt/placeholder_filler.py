from typing import Dict


def fill_placeholders(template: str, replacements: Dict[str, str]) -> str:
    """Replace placeholder variables in a prompt template.
    
    Placeholders should be in the format {{VARIABLE_NAME}}. All placeholders
    in the template must have corresponding keys in the replacements dict.
    
    Args:
        template: The prompt template string containing placeholders.
        replacements: Dictionary mapping placeholder names to replacement values.
                     Keys should match placeholder names without the {{ }} syntax.
        
    Returns:
        The template string with all placeholders replaced.
        
    Raises:
        ValueError: If any placeholder in the template is not found in replacements.
    """
    result = template
    for key, value in replacements.items():
        placeholder = f"{{{{{key}}}}}"
        if placeholder not in result:
            raise ValueError(
                f"Placeholder '{placeholder}' not found in template"
            )
        result = result.replace(placeholder, str(value).strip())
    return result