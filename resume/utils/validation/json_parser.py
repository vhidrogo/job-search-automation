import json
from json_repair import repair_json
from typing import Any, Dict


def parse_llm_json(text: str) -> Dict[str, Any]:
    """Parse a cleaned JSON object or array from an LLM response.

    Normalizes typical LLM output formats before deserialization, including:
    - Raw JSON objects or arrays
    - JSON wrapped in ```json ... ``` code blocks
    - Extra whitespace or line breaks

    Args:
        text: Raw LLM response text containing JSON content.

    Returns:
        Parsed JSON data as a Python dictionary or list.

    Raises:
        ValueError: If the response appears truncated (missing closing brace/bracket).
        ValueError: If the JSON cannot be parsed even after repair.
    """
    cleaned = text.replace("```json", "").replace("```", "").strip()
    
    if not (cleaned.endswith("}") or cleaned.endswith("]")):
        raise ValueError("LLM output truncated = increase max_tokens or retry.")

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        try:
            repaired = repair_json(cleaned)
            
            return json.loads(repaired)
        except Exception as e:
            raise ValueError(
                f"Failed to parse or repair LLM JSON output: {e}\n\n{cleaned}"
            ) from e