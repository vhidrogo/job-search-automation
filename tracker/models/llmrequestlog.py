from django.db import models
from django.utils import timezone


class LlmRequestLog(models.Model):
    class CallType(models.TextChoices):
        GENERATE_INTERVIEW_PREP_BASE = "generate_interview_prep_base", "Generate Interview Prep Base"
        GENERATE_INTERVIEW_PREP_SPECIFIC = "generate_interview_prep_specific", "Generate Interview Prep Specific"
        PARSE_JD = "parse_jd", "Parse Job Description"
        RESUME_BULLETS = "resume_bullets", "Resume Bullets"
        RESUME_SKILLS = "resume_skills", "Resume Skills"

    timestamp = models.DateTimeField(default=timezone.now)
    call_type = models.CharField(max_length=32, choices=CallType.choices)
    model = models.CharField(max_length=64)
    input_tokens = models.PositiveIntegerField()
    output_tokens = models.PositiveIntegerField()

    def total_tokens(self):
        return self.input_tokens + self.output_tokens
