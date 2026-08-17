from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.parsers import FormParser
from commons.responses import CustomeResponse
from drf_spectacular.utils import extend_schema
from services.authentication_service import AuthenticationService
from apps.accounts.serializers import (
    LoginSerializer,
    LogOutSerializer
)

class LoginUserAPIView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [FormParser]

    @extend_schema(
        request=LoginSerializer,
        responses={ 200: "Successfully logged in.", 404: "Bad Request" },
        operation_id="user_login"
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = AuthenticationService.login(request=request, validated_data=serializer.validated_data)
        return CustomeResponse.success(message="User logged in successfully.", data=tokens, status=status.HTTP_200_OK)

class LogOutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=LogOutSerializer,
        responses={200: "Logout successfully."},
        operation_id="user_logout"
    )
    def post(self, request):
        serializer = LogOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthenticationService.logout(request=request, refresh_token=serializer.validated_data["refresh"])
        return CustomeResponse.success(message="Logout successfully", status=status.HTTP_200_OK)
