from django.db import transaction
from rest_framework.exceptions import ValidationError
from apps.settings_app.models import Company

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
