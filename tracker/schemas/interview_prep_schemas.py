from pydantic import BaseModel


class InterviewPrepBaseSchema(BaseModel):
    """Schema for base interview preparation content."""
    formatted_jd: str
    company_context: str
    primary_drivers: str
    background_narrative: str
    resume_defense_prep: str


class InterviewPrepSpecificSchema(BaseModel):
    """Schema for interview-specific preparation content."""
    prep_plan: str
    predicted_questions: str
    interviewer_questions: str
    technical_deep_dives: str
