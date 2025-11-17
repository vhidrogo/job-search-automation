from django.core.validators import MinValueValidator
from django.db import models


class ContractJob(models.Model):
    """
        Represents a contract job offered through an external consulting company.

        Fields:
            - job: Base job this contract role is associated with.
            - consulting_company: Optional consulting company through which the contract is offered.
            - contract_length_months: Duration of the contract in months.
            - hourly_rate_min: Minimum hourly rate quoted in the contract.
            - hourly_rate_max: Maximum hourly rate quoted in the contract.
            - hourly_rate_submitted: Hourly rate submitted on the resume/application.
            - provides_benefits: Whether the contract provides benefits.
            - provides_pto: Whether the contract provides paid time off.
    """
    job = models.OneToOneField(
        "Job",
        on_delete=models.CASCADE,
        related_name="contract",
        help_text="Base job this contract role is associated with.",
    )
    consulting_company = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Company through which the contract is offered.",
    )
    contract_length_months = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        help_text="Duration of the contract in months.",
    )
    hourly_rate_min = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Minimum hourly rate quoted in the contract.",
    )
    hourly_rate_max = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Maximum hourly rate quoted in the contract.",
    )
    hourly_rate_submitted = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Hourly rate submitted on the resume/application.",
    )
    provides_benefits = models.BooleanField(
        default=False,
        help_text="Whether the contract provides benefits.",
    )
    provides_pto = models.BooleanField(
        default=False,
        help_text="Whether the contract provides paid time off.",
    )