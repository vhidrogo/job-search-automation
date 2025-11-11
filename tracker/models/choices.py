from django.db import models


class JobRole(models.TextChoices):
    ANALYTICS_ENGINEER = "Analytics Engineer"
    BUSINESS_ANALYST = "Business Analyst"
    BUSINESS_INTELLIGENCE_ENGINEER = "Business Intelligence Engineer"
    DATA_ANALYST = "Data Analyst"
    DATA_ENGINEER = "Data Engineer"
    SOFTWARE_ENGINEER = "Software Engineer"


class JobLevel(models.TextChoices):
    I = "I"
    II = "II"
    III = "III"
    SENIOR = "Senior"


class WorkSetting(models.TextChoices):
    ON_SITE = "On-site"
    HYBRID = "Hybrid"
    REMOTE = "Remote"


class ApplicationState(models.TextChoices):
    CALLBACK = "Callback"
    CLOSED = "Closed"
    REJECTED = "Rejected"