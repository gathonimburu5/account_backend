from rest_framework.exceptions import ValidationError
from django.db import transaction
from apps.accounting.models import NominalAccount, AccountType

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
    @transaction.atomic
    def create_account(*, code, name, description="", account_type, parent=None, is_control_account=False, is_posting_account=True, is_active=True):
        code = code.strip().upper()
        if NominalAccount.objects.filter(code=code).exists():
            raise ValidationError({ "code":"A nominal account with this code already exists." })
        if parent:
            if not parent.is_active:
                raise ValidationError({ "parent":"An inactive account cannot be used as a parent." })
            if parent.is_posting_account:
                raise ValidationError({ "parent":"A posting account cannot have child accounts." })
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
            if NominalAccount.objects.filter(code=code).exclude(pk=account.pk).exists():
                raise ValidationError({ "code":"A nominal account with this code already exists." })
            account.code = code
        if name is not None:
            account.name = name.strip()
        if description is not None:
            account.description = description
        if account_type is not None:
            account.account_type = account_type
        if parent is not NorminalAccountService.UNSET:
            if parent.pk == account.pk:
                raise ValidationError({ "parent": ("An account cannot be its own parent.") })
            if not parent.is_active:
                raise ValidationError({ "parent": ("An inactive account cannot be used as a parent.") })
            if parent.is_posting_account:
                raise ValidationError({ "parent": ("A posting account cannot have child accounts.") })
            account.parent = parent
        if is_control_account is not None:
            account.is_control_account = is_control_account
        if is_posting_account is not None:
            account.is_posting_account = is_posting_account
        if (account.is_control_account and account.is_posting_account):
            raise ValidationError({ "detail": ("An account cannot be both a control account and a posting account.") })
        if is_active is not None:
            account.is_active = is_active
        account.save()
        return account

    @staticmethod
    @transaction.atomic
    def deactivate_account(*, account):
        if account.children.filter(is_active=True).exists():
            raise ValidationError({ "detail": ("An account with active child accounts cannot be deactivated.") })
        account.is_active = False
        account.save(update_fields=["is_active", "updated_at",])
        return account

    @staticmethod
    @transaction.atomic
    def activate_account(*, account):
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
        if AccountType.objects.filter(code=code).exists():
            raise ValidationError({ "code":"An account type with this code already exists." })
        if AccountType.objects.filter(name__iexact=name).exists():
            raise ValidationError({ "name":"An account type with this name already exists." })
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
    def update_account_type(*, account, code=None, name=None, description=None, category=None, normal_balance=None, is_active=None):
        if code is not None:
            code = code.strip().upper()
            