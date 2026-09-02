from rest_framework.exceptions import ValidationError
from django.db import transaction
from apps.accounting.models import (NominalAccount, AccountType, Journal, JournalLine)
from django.utils import timezone

class NorminalAccountService:
    UNSET = object()

    @staticmethod
    def get_accounts():
        return (NominalAccount.objects.select_related("parent").prefetch_related("children").order_by("code"))

    @staticmethod
    def get_active_accounts():
        return (NominalAccount.objects.filter(is_active=True).select_related("parent").order_by("code"))

    @staticmethod
    def get_account(pk):
        try:
            return (NominalAccount.objects.select_related("parent").get(pk=pk))
        except NominalAccount.DoesNotExist:
            raise ValidationError({ "detail": "Nominal account not found." })

    @staticmethod
    def _validate_parent(*, account=None, parent=None):
        if parent is None:
            return
        if account is not None and parent.pk == account.pk:
            raise ValidationError({ "parent": ("An account cannot be its own parent.") })
        if not parent.is_active:
            raise ValidationError({ "parent": ("An inactive account cannot be used as a parent.") })
        if parent.is_posting_account:
            raise ValidationError({ "parent": ("A posting account cannot have child accounts.") })
        if account is not None:
            current = parent
            while current is not None:
                if current.pk == account.pk:
                    raise ValidationError({ "parent":"This parent would create a circular account hierarchy." })
                current = current.parent

    @staticmethod
    def _validate_account_type(*, account_type):
        if account_type is None:
            raise ValidationError({ "account_type":"Account type is required." })
        if not account_type.is_active:
            raise ValidationError({ "account_type":"An inactive account type cannot be assigned to a nominal account." })

    @staticmethod
    def _validate_account_type_balance(*, category, normal_balance):
        debit_categories = {
            AccountType.CategoryChoices.ASSET,
            AccountType.CategoryChoices.EXPENSE,
        }

        credit_categories = {
            AccountType.CategoryChoices.LIABILITY,
            AccountType.CategoryChoices.EQUITY,
            AccountType.CategoryChoices.REVENUE,
        }

        if (category in debit_categories and normal_balance != AccountType.NorminalBalanceChoices.DEBIT):
            raise ValidationError({ "normal_balance":"Asset and Expense accounts must have a debit normal balance." })

        if (category in credit_categories and normal_balance != AccountType.NorminalBalanceChoices.CREDIT):
            raise ValidationError({ "normal_balance":"Liability, Equity and Revenue accounts must have a credit normal balance." })

    @staticmethod
    @transaction.atomic
    def create_account(*, code, name, description="", account_type, parent=None, is_control_account=False, is_posting_account=True, is_active=True):
        code = code.strip().upper()
        name = name.strip()
        if not code:
            raise ValidationError({ "code":"Account code is required." })
        if not name:
            raise ValidationError({ "name":"Account name is required." })

        if NominalAccount.objects.filter(code=code).exists():
            raise ValidationError({ "code":"A nominal account with this code already exists." })
        NorminalAccountService._validate_account_type(account_type=account_type)
        NorminalAccountService._validate_parent(parent=parent)
        if is_control_account and is_posting_account:
            raise ValidationError({ "detail":"An account cannot be both a control account and a posting account." })
        account = NominalAccount.objects.create(
            code=code,
            name=name,
            description=description,
            account_type=account_type,
            parent=parent,
            is_control_account=is_control_account,
            is_posting_account=is_posting_account,
            is_active=is_active
        )
        return account

    @staticmethod
    @transaction.atomic
    def update_account(*, account, code=None, name=None, description=None, account_type=None, parent=UNSET, is_control_account=None, is_posting_account=None, is_active=None):
        if code is not None:
            code = code.strip().upper()
            if not code:
                raise ValidationError({ "code":"Account code cannot be empty." })

            if NominalAccount.objects.filter(code=code).exclude(pk=account.pk).exists():
                raise ValidationError({ "code":"A nominal account with this code already exists." })
            account.code = code
        if name is not None:
            name = name.strip()
            if not name:
                raise ValidationError({ "name":"Account name cannot be empty." })
            account.name = name
        if description is not None:
            account.description = description
        if account_type is not None:
            NorminalAccountService._validate_account_type(account_type=account_type)
            account.account_type = account_type
        if parent is not NorminalAccountService.UNSET:
            NorminalAccountService._validate_parent(account=account, parent=parent)
            account.parent = parent
        if is_control_account is not None:
            account.is_control_account = is_control_account
        if is_posting_account is not None:
            if (is_posting_account and account.children.exists()):
                raise ValidationError({ "is_posting_account":"An account with child accounts cannot be a posting account." })
            account.is_posting_account = is_posting_account
        if (account.is_control_account and account.is_posting_account):
            raise ValidationError({ "detail": ("An account cannot be both a control account and a posting account.") })
        if is_active is not None:
            if(is_active and account.parent and not account.parent.is_active):
                raise ValidationError({ "is_active":"An account cannot be activated while its parent account is inactive." })
            if (not is_active and account.children.filter(is_active=True).exists()):
                raise ValidationError({ "is_active":"An account with active child accounts cannot be deactivated." })
            account.is_active = is_active
        account.save()
        return account

    @staticmethod
    @transaction.atomic
    def deactivate_account(*, account):
        if account.is_active:
            return account

        if account.children.filter(is_active=True).exists():
            raise ValidationError({ "detail": ("An account with active child accounts cannot be deactivated.") })

        account.is_active = False
        account.save(update_fields=["is_active", "updated_at",])
        return account

    @staticmethod
    @transaction.atomic
    def activate_account(*, account):
        if account.is_active:
            return account

        if account.parent and not account.parent.is_active:
            raise ValidationError({ "detail":"An account cannot be activated while its parent account is inactive." })

        account.is_active = True
        account.save(update_fields=["is_active", "updated_at",])
        return account

    @staticmethod
    def get_account_types():
        return AccountType.objects.order_by("code")
    @staticmethod
    def get_active_account_type():
        return AccountType.objects.filter(is_active=True).order_by("code")
    @staticmethod
    def get_account_type(pk):
        try:
            return AccountType.objects.get(pk=pk)
        except AccountType.DoesNotExist:
            raise ValidationError({ "detail":"Account type not found." })
    @staticmethod
    @transaction.atomic
    def create_account_type(*, code, name, description="", category, normal_balance, is_active=True):
        code = code.strip().upper()
        name = name.strip()
        if not code:
            raise ValidationError({ "code":"Account type code is required." })
        if not name:
            raise ValidationError({ "name":"Account type name is required." })
        if AccountType.objects.filter(code=code).exists():
            raise ValidationError({ "code":"An account type with this code already exists." })
        if AccountType.objects.filter(name__iexact=name).exists():
            raise ValidationError({ "name":"An account type with this name already exists." })
        NorminalAccountService._validate_account_type_balance(category=category, normal_balance=normal_balance)
        account = AccountType.objects.create(
            code=code,
            name=name,
            description=description,
            category=category,
            normal_balance=normal_balance,
            is_active=is_active,
        )
        return account

    @staticmethod
    @transaction.atomic
    def update_account_type(*, account_type, code=None, name=None, description=None, category=None, normal_balance=None, is_active=None):
        if code is not None:
            code = code.strip().upper()
            if not code:
                raise ValidationError({ "code":"Account type code cannot be empty." })
            if AccountType.objects.filter(code=code).exclude(pk=account_type.pk).exists():
                raise ValidationError({ "code":"An account type with this code already exists." })
            account_type.code = code

        if name is not None:
            name = name.strip()
            if not name:
                raise ValidationError({ "name":"Account type name cannot be empty." })
            if AccountType.objects.filter(name__iexact=name).exclude(pk=account_type.pk).exists():
                raise ValidationError({ "name":"An account type with this name already exists." })
            account_type.name = name

        if description is not None:
            account_type.description = description

        if category is not None:
            account_type.category = category

        if normal_balance is not None:
            account_type.normal_balance = normal_balance

        NorminalAccountService._validate_account_type_balance(category=account_type.category, normal_balance=account_type.normal_balance)

        if is_active is not None:
            if (not is_active and account_type.nominal_accounts.filter(is_active=True).exists()):
                raise ValidationError({ "is_active":"An account type with active nominal accounts cannot be deactivated." })
            account_type.is_active = is_active

        account_type.save()

        return account_type

    @staticmethod
    @transaction.atomic
    def deactivate_account_type(*, account_type):
        if not account_type.is_active:
            return account_type

        if account_type.nominal_accounts.filter(is_active=True).exists():
            raise ValidationError({ "detail":"An account type with active nominal accounts cannot be deactivated." })

        account_type.is_active = False
        account_type.save(update_fields=["is_active", "updated_at",])
        return account_type

    @staticmethod
    @transaction.atomic
    def activate_account_type(*, account_type):
        if account_type.is_active:
            return account_type

        account_type.is_active = True
        account_type.save(update_fields=["is_active", "updated_at",])
        return account_type

    @staticmethod
    def get_root_accounts():
        return (NominalAccount.objects.filter(parent__isnull=True, is_active=True).select_related("account_type").order_by("code"))

    @staticmethod
    def get_child_accounts(parent_id):
        return (NominalAccount.objects.filter(parent_id=parent_id, is_active=True).select_related("account_type").order_by("code"))

    @staticmethod
    def get_posting_accounts():
        return (NominalAccount.objects.filter(is_active=True, is_posting_account=True).select_related("account_type", "parent").order_by("code"))

    @staticmethod
    def get_control_accounts():
        return (NominalAccount.objects.filter(is_active=True, is_control_account=True).select_related("account_type", "parent").order_by("code"))
    @staticmethod
    def get_journals():
        return (Journal.objects.select_related(
            "financial_period",
            "created_by",
            "posted_by",
            "reversed_journal"
        ).prefetch_related(
            "lines__nominal_account"
        ).order_by("-transaction_date", "-id"))
    @staticmethod
    def get_journal(pk):
        try:
            return (
                Journal.objects.select_related(
                    "financial_period",
                    "created_by",
                    "posted_by",
                    "reversed_journal"
                ).prefetch_related(
                    "lines__nominal_account"
                ).get(pk=pk)
            )
        except Journal.DoesNotExist:
            raise ValidationError({ "detail": "Journal not found." })
    