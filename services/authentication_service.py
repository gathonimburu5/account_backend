from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from django.contrib.auth import authenticate
from apps.accounts.models import User, Role, Permission
from django.db import transaction

class AuthenticationService:
    @staticmethod
    @transaction.atomic
    def login(*, request, validated_data):
        email = validated_data["email"]
        password = validated_data["password"]
        user = authenticate(request=request, email=email, password=password)
        if user is None:
            raise ValidationError("Invalid email or password.")
        if not user.is_active:
            raise ValidationError("User account is inactive")
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user":{
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone_number": user.phone_number,
                "address": user.address,
                "date_of_birth": user.date_of_birth,
                "profile_picture": user.profile_picture.url if user.profile_picture else None,
            }
        }

    @staticmethod
    @transaction.atomic
    def logout(*, request, refresh_token):
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

        except Exception as e:
            raise ValidationError("Invalid token or token already blacklisted.")

    @staticmethod
    @transaction.atomic
    def register_user(*, request, validated_data):
        data = validated_data.copy()
        password = data.pop("password")
        data.pop("confirm_password", None)
        user = User.objects.create_user(password=password, **data)
        return user

    @staticmethod
    @transaction.atomic
    def change_password(*, user, request, validated_data):
        data = validated_data.copy()
        old_password = data.pop("old_password")
        new_password = data.pop("new_password")
        data.pop("confirm_new_password", None)
        if not user.check_password(old_password):
            raise ValidationError({ "old_password":"Old password is incorrect." })
        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])
        return user

    @staticmethod
    @transaction.atomic
    def update_user(*, user, request, validated_data):
        for attr, value in validated_data.items():
            setattr(user, attr, value)
        user.save()
        return user

    @staticmethod
    @transaction.atomic
    def activate_user(*, user, request):
        user.is_active = True
        user.save(update_fields=["is_active", "updated_at"])
        return user

    @staticmethod
    @transaction.atomic
    def deactivate_user(*, user, request):
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        return user

    @staticmethod
    @transaction.atomic
    def lock_user(*, user, request):
        user.is_locked = True
        user.is_active = False
        user.save(update_fields=["is_locked", "is_active", "updated_at"])
        return user

    @staticmethod
    @transaction.atomic
    def unlock_user(*, user, request):
        user.is_locked = False
        user.is_active = True
        user.save(update_fields=["is_locked", "is_active", "updated_at"])
        return user

    @staticmethod
    @transaction.atomic
    def delete_user(*, user, request):
        user.is_deleted = True
        user.is_active = False
        user.save(update_fields=["is_deleted", "is_active", "updated_at"])
        return user

class PermissionService:
    @staticmethod
    @transaction.atomic
    def create_permission(*, request, validated_data):
        code = validated_data["code"].strip().upper()
        if Permission.objects.filter(code=code).exists():
            raise ValidationError({ "code":"A permission with this code already exists." })

        validated_data["code"] = code
        permission = Permission.objects.create(**validated_data)
        return permission

    @staticmethod
    @transaction.atomic
    def update_permission(*, request, permission, validated_data):
        code = validated_data.get("code")

        if code is not None:
            code = code.strip().upper()

            if code != permission.code:
                if Permission.objects.filter(code=code).exclude(pk=permission.pk).exists():
                    raise ValidationError({ "code":"A permission with this code already exists." })

            validated_data["code"] = code

        for field, value in validated_data.items():
            setattr(permission, field, value)

        permission.save()
        return permission

    @staticmethod
    def get_permission(permission_id):
        return Permission.objects.get(pk=permission_id, is_active=True)

    @staticmethod
    def get_permissions():
        return Permission.objects.all().order_by("module", "code",)

    @staticmethod
    @transaction.atomic
    def deactivate_permission(*, request, permission):
        permission.is_active = False
        permission.save(update_fields=["is_active"])
        return permission

class RoleService:
    @staticmethod
    def get_roles():
        return Role.objects.prefetch_related("permissions").order_by("name")

    @staticmethod
    def get_role(pk):
        try:
            return Role.objects.prefetch_related("permissions").get(pk=pk)
        except Role.DoesNotExist:
            raise ValidationError({ "detail":"Role not found." })

    @staticmethod
    @transaction.atomic
    def create_role(*, request, validated_data):
        name = validated_data["name"].strip().upper()
        code = validated_data["code"].strip().upper()

        if Role.objects.filter(name=name).exists():
            raise ValidationError({ "name":"A role name with this name already exists." })

        if Role.objects.filter(code=code).exists():
            raise ValidationError({ "code":"A role with this code already exists." })

        validated_data["name"] = name
        validated_data["code"] = code
        role = Role.objects.create(**validated_data)
        return role

    @staticmethod
    @transaction.atomic
    def update_role(*, request, role, validated_data):
        name = validated_data.get("name")
        code = validated_data.get("code")

        if name is not None:
            name = name.strip().upper()
            if name != role.name:
                if Role.objects.filter(name=name).exclude(pk=role.pk).exists():
                    raise ValidationError({ "name": "A role with this name already exists." })

            validated_data["name"] = name

        if code is not None:
            code = code.strip().upper()
            if code != role.code:
                if Role.objects.filter(code=code).exclude(pk=role.pk).exists():
                    raise ValidationError({ "code": "A role with this code already exists." })

            validated_data["code"] = code

        for field, value in validated_data.items():
            setattr(role, field, value)

        role.save()
        return role

    @staticmethod
    @transaction.atomic
    def deactivate_role(*, request, role):
        role.is_active = False
        role.save(update_fields=["is_active", "updated_at"])
        return role

class UserRoleService:
    @staticmethod
    def get_user_roles(*, user):
        return user.roles.filter(is_active=True).order_by("name")

    @staticmethod
    @transaction.atomic
    def assign_role(*, user, role):
        if user.is_deleted:
            raise ValidationError({ "detail": "Cannot assign a role to a deleted user." })
        if user.is_locked:
            raise ValidationError({ "detail": "Cannot assign a role to a locked user." })
        if not role.is_active:
            raise ValidationError({ "detail": "Cannot assign an inactive role." })
        if user.roles.filter(pk=role.pk).exists():
            raise ValidationError({ "detail": "User already has this role." })
        user.roles.add(role)
        return role

    @staticmethod
    @transaction.atomic
    def remove_role(*, user, role):
        if not user.roles.filter(pk=role.pk).exists():
            raise ValidationError({ "detail": "User does not have this role." })
        user.roles.remove(role)
        return role

class RolePermissionService:
    @staticmethod
    def get_role_permissions(role):
        return role.permissions.filter(is_active=True).order_by("module", "code")

    @staticmethod
    @transaction.atomic
    def assign_permission(*, request, role, permission):
        if not role.is_active:
            raise ValidationError({ "detail": "Cannot assign permission to an inactive role." })
        if not permission.is_active:
            raise ValidationError({ "detail": "Cannot assign an inactive permission." })
        if role.permissions.filter(pk=permission.pk).exists():
            raise ValidationError({ "detail": "Permission is already assigned to this role." })

        role.permissions.add(permission)
        return permission

    @staticmethod
    @transaction.atomic
    def remove_permission(*, request, role, permission):
        if not role.permissions.filter(pk=permission.pk).exists():
            raise ValidationError({ "detail": "Permission is not assigned to this role." })

        role.permissions.remove(permission)
        return permission



