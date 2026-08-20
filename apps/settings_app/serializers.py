from rest_framework import serializers
from .models import Company, Currency, FinancialPeriod
from commons.utils import validate_upload_file

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = (
            "id",
            "name",
            "code",
            "registration_number",
            "registration_date",
            "kra_number",
            "email",
            "phone_number",
            "postal_address",
            "physical_address",
            "county",
            "logo",
            "is_active",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

class CompanyRegisterSerializer(serializers.Serializer):
    code = serializers.CharField(required=True, write_only=True)
    name = serializers.CharField(required=True, write_only=True)
    registration_number = serializers.CharField(required=True, write_only=True)
    registration_date = serializers.DateField(required=True, write_only=True)
    kra_number = serializers.CharField(required=True, write_only=True)
    email = serializers.EmailField(required=True, write_only=True)
    phone_number = serializers.CharField(required=True, max_length=15, write_only=True)
    postal_address = serializers.CharField(required=True, write_only=True)
    physical_address = serializers.CharField(required=True, write_only=True)
    county = serializers.CharField(required=True, write_only=True)
    logo = serializers.ImageField(required=False, validators=[validate_upload_file])

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = (
            "id",
            "code",
            "name",
            "country",
            "symbol",
            "decimal_places",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

class CurrencyCreateSerializer(serializers.Serializer):
    code = serializers.CharField(required=True, write_only=True)
    name = serializers.CharField(required=True, write_only=True)
    country = serializers.CharField(required=True, write_only=True)
    symbol = serializers.CharField(required=False, write_only=True)
    decimal_places = serializers.CharField(required=True, write_only=True)
    is_active = serializers.BooleanField(default=True)

class FinancialPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialPeriod
        fields = (
            "id",
            "name",
            "period",
            "month",
            "year",
            "start_date",
            "end_date",
            "status",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

class FinancialPeriodCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    month = serializers.IntegerField(min_value=1, max_value=12)
    year = serializers.IntegerField(min_value=2000, max_value=2100)

