import json
from typing import List

from resume.schemas import RequirementSchema


def build_requirement_json(requirements: List[RequirementSchema]) -> str:
    """Serialize a list of RequirementSchema objects into JSON for LLM prompts.
    
    Uses `ensure_ascii=False` to preserve Unicode characters directly, avoiding
    unnecessary escape sequences and reducing token count for model input.
    """
    return json.dumps([r.model_dump() for r in requirements], ensure_ascii=False)
