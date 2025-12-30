from django.db import models


class SearchRole(models.TextChoices):
    ANALYTICS_ENGINEER = "analytics_engineer", "Analytics Engineer"
    BUSINESS_ANALYST = "business_analyst", "Business Analyst"
    BUSINESS_INTELLIGENCE_ENGINEER = "business_intelligence_engineer", "Business Intelligence Engineer"
    DATA_ANALYST = "data_analyst", "Data Analyst"
    DATA_ENGINEER = "data_engineer", "Data Engineer"
    DATA_SCIENTIST = "data_scientist", "Data Scientist"
    SOFTWARE_ENGINEER = "software_engineer", "Software Engineer"
    SOLUTIONS_ENGINEER = "solutions_engineer", "Solutions Engineer"
