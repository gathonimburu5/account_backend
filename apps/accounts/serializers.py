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

class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
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
            "roles",
        )

        read_only_fields = (
            "id",
            "email",
            "created_at",
            "updated_at",
            "is_email_verified",
            "is_locked",
            "is_deleted",
        )

    def get_roles(self, obj):
        return [
            {
                "id": role.id,
                "name": role.name,
                "code": role.code,
            }
            for role in obj.roles.filter(is_active=True)
        ]

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class LogOutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password_stregth], min_length=8)
    confirm_new_password = serializers.CharField(write_only=True, required=True)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        django_validate_password(value)
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_new_password"]:
            raise serializers.ValidationError({ "confirm_new_password":"Password does not match." })
        return attrs

class UpdateUserSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False, write_only=True)
    last_name = serializers.CharField(required=False, write_only=True)
    phone_number = serializers.CharField(required=False, max_length=15, write_only=True)
    date_of_birth = serializers.DateField(required=False, write_only=True)
    address = serializers.CharField(required=False, write_only=True)

    def validate_phone_number(self, value):
        if value and User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("User with this phone number already exists.")
        return value

class PermissionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Permission
        fields = (
            "id",
            "code",
            "name",
            "description",
            "module",
            "is_active",
            "created_at",
        )

        read_only_fields = (
            "id",
            "created_at",
        )

class PermissionCreateUpdateSerializer(serializers.Serializer):
    code = serializers.CharField(required=True, max_length=50)
    name = serializers.CharField(required=True, max_length=100)
    module = serializers.CharField(required=True, max_length=100)
    is_active = serializers.BooleanField(default=True)
    description = serializers.CharField(required=False, allow_blank=True)

class RoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Role
        fields = (
            "id",
            "name",
            "code",
            "description",
            "permissions",
            "is_active",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

class RoleCreateUpdateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50, required=True)
    name = serializers.CharField(max_length=100, required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(default=True)

class AssignRoleSerializer(serializers.Serializer):
    role_id = serializers.IntegerField()

    def validate_role_id(self, value):
        try:
            role = Role.objects.get(pk=value, is_active=True)
        except Role.DoesNotExist:
            raise serializers.ValidationError({ "role":"Role not found or inactive." })
        return role

class AssignPermissionSerializer(serializers.Serializer):
    permission_id = serializers.IntegerField()

    def validate_permission_id(self, value):
        try:
            permission = Permission.objects.get(pk=value, is_active=True)
        except Permission.DoesNotExist:
            raise serializers.ValidationError({ "permission":"Permission not found or inactive." })
        return permission



