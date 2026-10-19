from rest_framework.exceptions import ValidationError
from django.db import transaction
from apps.accounting.models import (NominalAccount, AccountType, Journal, JournalLine)
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum, Q, F, Value, DecimalField
from django.db.models.functions import Coalesce

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
    @staticmethod
    def _validate_period(financial_period, transaction_date):
        if (financial_period.status != financial_period.StatusChoices.ACTIVE):
            raise ValidationError({ "financial_period":"The financial period is not active." })
        if transaction_date < financial_period.start_date:
            raise ValidationError({ "transaction_date":"The transaction date cannot be after the financial period end date." })

    @staticmethod
    def _validate_lines(lines):
        if len(lines) < 0:
            raise ValidationError({ "lines":"A journal must contain at least two lines." })
        total_debit = Decimal("0.00")
        total_credit = Decimal("0.00")
        for line in lines:
            debit = Decimal(str(line.get("debit", "0.00")))
            credit = Decimal(str(line.get("credit", "0.00")))
            if debit < 0 or credit < 0:
                raise ValidationError({ "lines":"Debit and credit amounts cannot be negative." })
            if debit > 0 and credit > 0:
                raise ValidationError({ "lines":"A journal line cannot have both debit and credit amounts." })
            if debit == 0 and credit == 0:
                raise ValidationError({ "lines":"A journal line must contain either a debit or credit amount." })
            total_debit += debit
            total_credit += credit
        if total_debit != total_credit:
            raise ValidationError({ "lines":"The total debit must be equal total credit." })

    @staticmethod
    def _validate_accounts(lines):
        account_ids = [line["nominal_account"].pk for line in lines]
        accounts = (NominalAccount.objects.filter(pk__in=account_ids, is_active=True,).select_related("account_type"))
        accounts_by_id = {
            account.pk: account for account in accounts
        }
        for line in lines:
            account = accounts_by_id.get(line["nominal_account"].pk)
            if not account:
                raise ValidationError({ "lines":"One or more nominal accounts are invalid or inactive." })
            if not account.is_posting_account:
                raise ValidationError({ "lines":f"{account.code} - {account.name} is not a posting account." })

    @staticmethod
    def _generate_journal_number():
        last_journal = (
            Journal.objects.order_by("-id").first()
        )
        if not last_journal:
            next_number = 1
        else:
            try:
                next_number = (int(last_journal.journal_number.replace("JV-", "")) + 1)
            except ValueError:
                next_number = last_journal.id + 1
        return f"JV-{next_number:06d}"

    @staticmethod
    @transaction.atomic
    def create_journal(*, transaction_date, description, reference="", financial_period, lines, created_by,):
        NorminalAccountService._validate_period(financial_period, transaction_date)
        NorminalAccountService._validate_lines(lines)
        NorminalAccountService._validate_accounts(lines)
        journal_number = (NorminalAccountService._generate_journal_number())
        journal = Journal.objects.create(
            journal_number=journal_number,
            transaction_date=transaction_date,
            description=description,
            reference=reference,
            financial_period=financial_period,
            created_by=created_by,
            status=Journal.StatusChoices.DRAFT,
        )

        JournalLine.objects.bulk_create(
            [
                JournalLine(
                    journal=journal,
                    nominal_account=line["nominal_account"],
                    description=line.get("description", ""),
                    debit = line.get("debit", Decimal("0.00")),
                    credit = line.get("credit", Decimal("0.00")),
                )
                for line in lines
            ]
        )

        return NorminalAccountService.get_journal(journal.pk)

    @staticmethod
    @transaction.atomic
    def post_journal(*, journal, posted_by):
        if(journal.status != Journal.StatusChoices.DRAFT):
            raise ValidationError({ "detail":"Only draft journals can be posted." })
        NorminalAccountService._validate_period(journal.financial_period, journal.transaction_date)
        lines = list(journal.lines.all())
        NorminalAccountService._validate_lines(
            [
                {
                    "nominal_account": line.nominal_account,
                    "debit": line.debit,
                    "credit": line.credit,
                }
                for line in lines
            ]
        )

        journal.status = (Journal.StatusChoices.POSTED)
        journal.posted_by = posted_by
        journal.posted_at = timezone.now()

        journal.save(update_fields=[
            "status",
            "posted_by",
            "posted_at",
            "updated_at",
        ])

        return journal

    @staticmethod
    def get_general_ledger(*, nominal_account_id, start_date=None, end_date=None, financial_period_id=None):
        account = NominalAccount.objects.filter(pk=nominal_account_id, is_active=True).select_related("account_type").first()
        if not account:
            raise ValidationError("Nominal account not found or inactive")
        lines = JournalLine.objects.filter(nominal_account=account, journal_status=Journal.StatusChoices.POSTED,).select_related(
            "journal", "nominal_account", "nominal_account__account_type",
        )

        if financial_period_id is not None:
            lines = lines.filter(journal__financial_period_id=financial_period_id)
        opening_lines = lines
        if start_date:
            opening_lines = opening_lines.filter(journal__transaction_date__lt=start_date)
        opening_totals = opening_lines.aggregate(
            debit = Coalesce(Sum("debit"), Decimal("0.00")),
            credit=Coalesce(Sum("credit"), Decimal("0.00")),
        )
        opening_debit = opening_totals["debit"]
        opening_credit = opening_totals["credit"]

        if account.account_type.normal_balance == "DEBIT":
            opening_balance = opening_debit - opening_credit
        else:
            opening_balance = opening_credit - opening_debit

        period_lines = lines

        if start_date:
            period_lines = period_lines.filter(journal__transaction_date__gte=start_date)
        if end_date:
            period_lines = period_lines.filter(journal__transaction_date__lte=end_date)
        period_lines = period_lines.order_by(
            "journal__transaction_date", "journal__journal_number", "id"
        )

        totals = period_lines.aggregate(
            debit=Coalesce(Sum("debit"), Decimal("0.00")),
            credit=Coalesce(Sum("credit"), Decimal("0.00")),
        )

        total_debit = totals["debit"]
        total_credit = totals["credit"]

        running_balance = opening_balance
        ledger_lines = []

        for line in period_lines:
            if account.account_type.normal_balance == "DEBIT":
                running_balance += line.debit - line.credit
            else:
                running_balance += line.credit - line.debit

            ledger_lines.append({
                "journal_id": line.journal_id,
                "journal_number": line.journal.journal_number,
                "transaction_date": line.journal.transaction_date,
                "description": line.journal.description,
                "reference": line.journal.reference,
                "nominal_account_id": account.id,
                "nominal_account_code": account.code,
                "nominal_account_name": account.name,
                "debit": line.debit,
                "credit": line.credit,
                "balance": running_balance,
            })

        return {
            "nominal_account_id": account.id,
            "nominal_account_code": account.code,
            "nominal_account_name": account.name,
            "opening_balance": opening_balance,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "closing_balance": running_balance,
            "lines": ledger_lines,
        }

    @staticmethod
    def get_trial_balance(*, as_at_date):
        money_field = DecimalField(max_digits=18, decimal_places=2)
        accounts = NominalAccount.objects.filter(is_active=True, is_posting_account=True,).select_related(
            "account_type"           
        ).annotate(
            total_debit = Coalesce(
                sum(
                    "journal_lines__debit", 
                    filter=Q(
                        journal_lines__journal__status="POSTED", 
                        journal_lines__journal__transaction_date__lte=as_at_date,
                    ),
                ), Value(Decimal("0.00")), output_field=money_field,
            ),
            total_credit=Coalesce(
                sum(
                    "journal_lines__credit",
                    filter=Q(
                        journal_lines__journal__status="POSTED",
                        journal_lines__journal__transaction_date__lte=as_at_date,
                    ),
                ),
                Value(Decimal("0.00")), output_field=money_field
            ),
        ).order_by("code")

        account_rows = []
        total_debit = Decimal("0.00")
        total_credit = Decimal("0.00")

        for account in accounts:
            if account.account_type.normal_balance == "DEBIT":
                balance = account.total_debit - account.total_credit
            else:
                balance = account.total_redit - account.total_debit

            debit_balance = max(balance, Decimal("0.00"))
            credit_balance = max(-balance, Decimal("0.00"))

            account_rows.append({
                "nominal_account_id": account.id,
                "nominal_account_code": account.code,
                "nominal_account_name": account.name,
                "account_type": account.account_type.name,
                "debit_balance": debit_balance,
                "credit_balance": credit_balance,
            })

            total_debit += debit_balance
            total_credit += credit_balance

        return {
            "as_at_date": as_at_date,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "is_balanced": total_debit == total_credit,
            "accounts": account_rows,
        }

    @staticmethod
    def getProfitAndLoss(*, start_date, end_date):
        if start_date > end_date:
            raise ValidationError("Start date cannot be after end date")
        money_field = DecimalField(max_digits=18, decimal_places=2)
        accounts = NominalAccount.objects.filter(
            is_active=True, is_posting_account=True, account_type__category__in=["REVENUE", "EXPENSE"],
        ).select_related("account_type").annotate(
            total_debit = Coalesce(
                sum(
                    "journal_lines__debit",
                    filter=Q(
                        journal_lines__journal__status="POSTED",
                        journal_lines__journal__transaction_date__gte=start_date,
                        journal_lines__journal__transaction_date__lte=end_date,
                    ),
                ),
                Value(Decimal("0.00")),
                output_field=money_field,
            ),
            total_credit = Coalesce(
                sum(
                    "journal_lines__credit",
                    filter=Q(
                        journal_lines__journal__status="POSTED",
                        journal_lines__journal__transaction_date__gte=start_date,
                        journal_lines__journal__transaction_date__lte=end_date,
                    ),
                ),
                Value(Decimal("0.00")),
                output_field=money_field,
            ),
        ).order_by("code")

        revenue_accounts = []
        expense_accounts = []

        total_revenue = Decimal("0.00")
        total_expenses = Decimal("0.00")

        for account in accounts:
            if account.account_type.category == "REVENUE":
                amount = account.total_credit - account.total_debit
                if amount != 0:
                    revenue_accounts.append({
                        "nominal_account_id": account.id,
                        "nominal_account_code": account.code,
                        "nominal_account_name": account.name,
                        "amount": amount,
                    })
                total_revenue += amount
            elif account.account_type.category == "EXPENSE":
                amount = account.total_debit - account.total_credit
                if amount != 0:
                    expense_accounts.append({
                        "nominal_account_id": account.id,
                        "nominal_account_code": account.code,
                        "nominal_account_name": account.name,
                        "amount": amount,
                    })
                total_expenses += amount

        return {
            "start_date": start_date,
            "end_date": end_date,
            "revenue_accounts": revenue_accounts,
            "expense_accounts": expense_accounts,
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "net_profit_loss": total_revenue - total_expenses,
        }

    @staticmethod
    def getBalanceSheet(*, as_at_date):
        money_field = DecimalField(max_digits=18, decimal_places=2)

        accounts = NominalAccount.objects.filter(
            is_active=True,
            is_posting_account=True,
            account_type__category__in=[
                "ASSET",
                "LIABILITY",
                "EQUITY",
                "REVENUE",
                "EXPENSE",
            ],
        ).select_related("account_type").annotate(
            total_debit = Coalesce(
                sum(
                    "journal_lines__debit",
                    filter=Q(
                        journal_lines__journal__status="POSTED",
                        journal_lines__journal__transaction_date__lte=as_at_date,
                    ),
                ),
                Value(Decimal("0.00")),
                output_field=money_field,
            ),
            total_credit=Coalesce(
                sum(
                    "journal_lines__credit",
                    filter=Q(
                        journal_lines__journal__status="POSTED",
                        journal_lines__journal__transaction_date__lte=as_at_date,
                    ),
                ),
                Value(Decimal("0.00")),
                output_field=money_field,
            ),
        ).order_by("code")

        asset_accounts = []
        liability_accounts = []
        equity_accounts = []

        total_assets = Decimal("0.00")
        total_liabilities = Decimal("0.00")
        total_equity = Decimal("0.00")
        total_revenue = Decimal("0.00")
        total_expenses = Decimal("0.00")

        for account in accounts:
            category = account.account_type.category
            if category in ["ASSET", "EXPENSE"]:
                amount = account.total_debit - account.total_credit
            else:
                amount = account.total_credit - account.total_debit

            if category == "ASSET":
                if amount != 0:
                    asset_accounts.append({
                        "nominal_account_id": account.id,
                        "nominal_account_code": account.code,
                        "nominal_account_name": account.name,
                        "amount": amount,
                    })
                total_assets += amount
            elif category == "LIABILITY":
                if amount != 0:
                    liability_accounts.append({
                        "nominal_account_id": account.id,
                        "nominal_account_code": account.code,
                        "nominal_account_name": account.name,
                        "amount": amount,
                    })
                total_liabilities += amount
            elif category == "EQUITY":
                if amount != 0:
                    equity_accounts.append({
                        "nominal_account_id": account.id,
                        "nominal_account_code": account.code,
                        "nominal_account_name": account.name,
                        "amount": amount,
                    })
                total_equity += amount
            elif category == "REVENUE":
                total_revenue += amount
            elif category == "EXPENSE":
                total_expenses += amount

        current_year_profit_loss = total_revenue - total_expenses
        total_liabilities_and_equity = (total_liabilities + total_equity + current_year_profit_loss)
        difference = total_assets - total_liabilities_and_equity
        return {
            "as_at_date": as_at_date,
            "asset_accounts": asset_accounts,
            "liability_accounts": liability_accounts,
            "equity_accounts": equity_accounts,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "total_equity": total_equity,
            "current_year_profit_loss": current_year_profit_loss,
            "total_liabilities_and_equity": total_liabilities_and_equity,
            "difference": difference,
            "is_balanced": difference == Decimal("0.00"),
        }
