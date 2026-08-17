from rest_framework import serializers
from .models import User, Role, Permission
from commons.validators import validate_password_stregth
from commons.utils import validate_file_size
from django.contrib.auth.password_validation import validate_password as django_validate_password

class RegisterUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=False, write_only=True)
    last_name = serializers.CharField(required=False, write_only=True)
    phone_number = serializers.CharField(required=False, max_length=15, write_only=True)
    date_of_birth = serializers.DateField(required=False, write_only=True)
    address = serializers.CharField(required=False, write_only=True)
    profile_picture = serializers.ImageField(required=False, validators=[validate_file_size])
    password = serializers.CharField(write_only=True, min_length=8, validators=[validate_password_stregth])
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "date_of_birth",
            "address",
            "profile_picture",
            "password",
            "confirm_password",
        )

    def validate_phone_number(self, value):
        if value and User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")

        django_validate_password(value)
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password":"Password do not match."})
        return attrs

class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "date_of_birth",
            "address",
            "profile_picture",
            "created_at",
            "updated_at",
            "is_email_verified",
            "is_locked",
            "is_deleted",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "is_email_verified",
            "is_locked",
            "is_deleted",
        )

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class LogOutSerializer(serializers.Serializer):
    refresh = serializers.CharField()






