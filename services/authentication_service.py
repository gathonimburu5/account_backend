from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from django.contrib.auth import authenticate
from apps.accounts.models import User
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
            raise ValueError("Invalid token or token already blacklisted.")

    @staticmethod
    @transaction.atomic
    def register_user(*, request, validated_data):
        data = validated_data.copy()
        password = data.pop("password")
        data.pop("confirm_password", None)
        user = User.objects.create_user(password=password, **data)
        return user

