from django.db import models
from django.core.validators import MinValueValidator
from apps.settings_app.models import FinancialPeriod
from apps.accounts.models import User

class AccountType(models.Model):
    class CategoryChoices(models.TextChoices):
        ASSET = "ASSET", "Asset"
        LIABILITY = "LIABILITY", "Liability"
        EQUITY = "EQUITY", "Equity"
        REVENUE = "REVENUE", "Revenue"
        EXPENSE = "EXPENSE", "Expense"

    class NorminalBalanceChoices(models.TextChoices):
        DEBIT = "DEBIT", "Debit"
        CREDIT = "CREDIT", "Credit"

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CategoryChoices.choices)
    normal_balance = models.CharField(max_length=10, choices=NorminalBalanceChoices.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code", ]

    def __str__(self):
        return f"{self.code} - {self.name}"

class NominalAccount(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    account_type = models.ForeignKey(AccountType, on_delete=models.PROTECT, related_name="nominal_accounts")
    parent = models.ForeignKey("self", on_delete=models.PROTECT, related_name="children", blank=True, null=True)
    is_control_account = models.BooleanField(default=False)
    is_posting_account = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code",]

    def __str__(self):
        return f"{self.code} - {self.name}"

class Journal(models.Model):
    class StatusChoices(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        POSTED = "POSTED", "Posted"
        REVERSED = "REVERSED", "Reversed"
        ACTIVE = "ACTIVE", "Active"

    journal_number = models.CharField(max_length=50, unique=True)
    transaction_date = models.DateField()
    description = models.TextField()
    reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.DRAFT)
    financial_period = models.ForeignKey(FinancialPeriod, on_delete=models.PROTECT, related_name="journals")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_journals")
    posted_at = models.DateTimeField(blank=True, null=True)
    posted_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="posted_journals", blank=True, null=True)
    reversed_journal = models.OneToOneField("self", on_delete=models.PROTECT, related_name="reversal_of", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-transaction_date", "-id"]

    def __str__(self):
        return self.journal_number

class JournalLine(models.Model):
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name="lines")
    nominal_account = models.ForeignKey(NominalAccount, on_delete=models.PROTECT, related_name="journal_lines")
    description = models.CharField(max_length=255, blank=True)
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0),],)
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0),],)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return (f"{self.journal.journal_number} - {self.nominal_account.code}")

