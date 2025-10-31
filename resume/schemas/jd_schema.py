from typing import Annotated, List, Optional
from pydantic import BaseModel, Field


class Metadata(BaseModel):
    company: str
    listing_job_title: str
    role: str
    specialization: Optional[str] = None
    level: Optional[str] = None
    location: Optional[str] = None
    work_setting: str
    min_experience_years: Optional[Annotated[int, Field(ge=0)]] = None
    min_salary: Optional[Annotated[int, Field(ge=0)]] = None
    max_salary: Optional[Annotated[int, Field(ge=0)]] = None


class RequirementSchema(BaseModel):
    text: str
    keywords: List[str]
    relevance: Annotated[float, Field(ge=0, le=1)]

class JDModel(BaseModel):
    metadata: Metadata
    requirements: List[RequirementSchema]
