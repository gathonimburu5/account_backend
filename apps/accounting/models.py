from django.db import models

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
