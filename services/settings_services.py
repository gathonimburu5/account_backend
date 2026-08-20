from django.db import transaction
from rest_framework.exceptions import ValidationError
from apps.settings_app.models import Company, Currency, FinancialPeriod
from calendar import monthrange
from datetime import date

class SettingService:
    @staticmethod
    def get_componies():
        return Company.objects.filter(is_active=True).order_by("name")

    @staticmethod
    def get_company(company_id):
        try:
            return Company.objects.get(pk=company_id, is_active=True,)
        except Company.DoesNotExist:
            raise ValidationError({ "detail": "Company not found." })

    @staticmethod
    @transaction.atomic
    def create_company(*, request, validated_data):
        code = validated_data["code"].strip().upper()
        if Company.objects.filter(code=code).exists():
            raise ValidationError({ "code": "A company with this code already exists." })
        validated_data["code"]=code
        company = Company.objects.create(**validated_data)
        return company

    @staticmethod
    @transaction.atomic
    def update_company(*, request, company, validated_data):
        code = validated_data.get("code")
        if code is not None:
            code = code.strip().upper()
            if code != company.code:
                if Company.objects.filter(code=code).exclude(pk=company.pk).exists():
                    raise ValidationError({ "code": "A company with this code already exists." })

            validated_data["code"] = code

        for field, value in company.items():
            setattr(company, field, value)

        company.save()
        return company

    @staticmethod
    @transaction.atomic
    def deactivate_company(*, request, company):
        company.is_active = False
        company.save(update_fields=["is_active", "updated_at"])
        return company

    @staticmethod
    @transaction.atomic
    def activate_company(*, request, company):
        company.is_active = True
        company.save(update_fields=["is_active", "updated_at"])
        return company

    @staticmethod
    def get_currencies():
        return Currency.objects.filter(is_active=True).order_by("code")

    @staticmethod
    def get_currency(currency_id):
        try:
            return Currency.objects.get(pk=currency_id, is_active=True,)
        except Currency.DoesNotExist:
            raise ValidationError({ "detail":"Currency not found." })

    @staticmethod
    @transaction.atomic
    def create_currency(*, request, validated_data):
        code = validated_data["code"].strip().upper()
        if Currency.objects.filter(code=code).exists():
            raise ValidationError({ "detail":"A currency with this code already exists." })
        validated_data["code"] = code
        currency = Currency.objects.create(**validated_data)
        return currency

    @staticmethod
    @transaction.atomic
    def update_currency(*, request, currency, validated_data):
        code = validated_data.get("code")
        if code is not None:
            code = code.strip().upper()
            if code != currency.code:
                if Currency.objects.filter(code=code).exclude(pk=currency.pk).exists():
                    raise ValidationError({ "detail":"A company with this code already exists." })
            validated_data["data"] = code

        for field, value in currency.items():
            setattr(currency, field, value)
        currency.save()
        return currency

    @staticmethod
    @transaction.atomic
    def activate_currency(*, request, currency):
        currency.is_active = True
        currency.save(update_fields=["is_active", "updated_at"])
        return currency

    @staticmethod
    @transaction.atomic
    def deactivate_currency(*, request, currency):
        currency.is_active = False
        currency.save(update_fields=["is_active", "updated_at"])

    @staticmethod
    def get_periods():
        return FinancialPeriod.objects.order_by("-year", "-month")

    @staticmethod
    def get_period(pk):
        try:
            return FinancialPeriod.objects.get(pk=pk)
        except FinancialPeriod.DoesNotExist:
            raise ValidationError({ "period":"Financial period not found." })

    @staticmethod
    @transaction.atomic
    def create_period(*, request, name, month, year):
        period = f"{month}/{year}"
        if FinancialPeriod.objects.filter(period=period).exists():
            raise ValidationError({ "period": "Financial period already exists." })
        last_day = monthrange(year, month)[1]
        financial_period = FinancialPeriod.objects.create(
            name=name,
            period=period,
            month=month,
            year=year,
            start_date=date(year, month, 1),
            end_date=date(year, month, last_day),
            status=FinancialPeriod.StatusChoices.INACTIVE,
        )
        return financial_period

    @staticmethod
    @transaction.atomic
    def update_period(*, period, name=None):
        if name is not None:
            period.name = name
        period.save()
        return period

    @staticmethod
    @transaction.atomic
    def activate_period(*, period):
        if period.status == FinancialPeriod.StatusChoices.CLOSED:
            raise ValidationError({ "detail": "Closed financial periods cannot be activated." })
        active_period = FinancialPeriod.objects.filter(status=FinancialPeriod.StatusChoices.ACTIVE).first()
        if active_period:
            active_period.status = (FinancialPeriod.StatusChoices.CLOSED)
            active_period.save(update_fields=["status", "updated_at"])

        # FinancialPeriod.objects.filter(status=FinancialPeriod.StatusChoices.ACTIVE).update(status=FinancialPeriod.StatusChoices.CLOSED)
        period.status = FinancialPeriod.StatusChoices.ACTIVE
        period.save(update_fields=["status", "updated_at"])
        return period

    @staticmethod
    @transaction.atomic
    def deactivate_period(*, period):
        if period.status == FinancialPeriod.StatusChoices.ACTIVE:
            period.status = FinancialPeriod.StatusChoices.INACTIVE
            period.save(update_fields=["status", "updated_at"])
        return period

    @staticmethod
    @transaction.atomic
    def close_period(*, period):
        period.status = FinancialPeriod.StatusChoices.CLOSED
        period.save(update_fields=["status", "updated_at"])
        return period

    @staticmethod
    def get_active_period():
        try:
            return FinancialPeriod.objects.get(status=FinancialPeriod.StatusChoices.ACTIVE)
        except FinancialPeriod.DoesNotExist:
            raise ValidationError({ "detail": "There is no active financial period." })

