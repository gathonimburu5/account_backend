from django.db import models
from django.db.models import Q

class Company(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=100)
    registration_date = models.DateField()
    kra_number = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    postal_address = models.CharField(max_length=100)
    physical_address = models.CharField(max_length=200)
    county = models.CharField(max_length=100,)
    logo = models.ImageField(upload_to="companies/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Currency(models.Model):
    code = models.CharField(max_length=4, unique=True)
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10, blank=True, null=True)
    decimal_places = models.PositiveSmallIntegerField(default=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class FinancialPeriod(models.Model):
    class StatusChoices(models.TextChoices):
        INACTIVE = "INACTIVE", "Inactive"
        ACTIVE = "ACTIVE", "Active"
        CLOSED = "CLOSED", "Closed"

    name = models.CharField(max_length=100)
    period = models.CharField(max_length=7, unique=True)
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=StatusChoices.choices, default=StatusChoices.INACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year", "-month",]

        constraints = [
            models.UniqueConstraint(
                fields=["status"],
                condition=Q(
                    status="ACTIVE"
                ),
                name="only_one_active_financial_period"
            ),
        ]

    def __str__(self):
        return self.period


