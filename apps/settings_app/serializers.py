from rest_framework import serializers
from .models import Company
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