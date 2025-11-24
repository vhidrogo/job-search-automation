from django.db import models


class JobLevel(models.TextChoices):
    I = "I", "I"
    II = "II", "II"
    III = "III", "III"
    SENIOR = "Senior", "Senior"

class JobRole(models.TextChoices):
    ANALYTICS_ENGINEER = "analytics_engineer", "Analytics Engineer"
    BUSINESS_ANALYST = "business_analyst", "Business Analyst"
    BUSINESS_INTELLIGENCE_ENGINEER = "business_intelligence_engineer", "Business Intelligence Engineer"
    DATA_ANALYST = "data_analyst", "Data Analyst"
    DATA_ENGINEER = "data_engineer", "Data Engineer"
    DATA_SCIENTIST = "data_scientist", "Data Scientist"
    SOFTWARE_ENGINEER = "software_engineer", "Software Engineer"
    SOLUTIONS_ENGINEER = "solutions_engineer", "Solutions Engineer"


class WorkSetting(models.TextChoices):
    ON_SITE = "On-site"
    HYBRID = "Hybrid"
    REMOTE = "Remote"


class ApplicationState(models.TextChoices):
    CALLBACK = "Callback"
    CLOSED = "Closed"
    REJECTED = "Rejected"