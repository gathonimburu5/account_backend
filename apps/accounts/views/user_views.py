from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.parsers import FormParser, MultiPartParser
from commons.responses import CustomeResponse
from drf_spectacular.utils import extend_schema
from services.authentication_service import AuthenticationService
from apps.accounts.serializers import (
    RegisterUserSerializer,
    UserDetailsSerializer,
)

class RegisterUserAPIView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=RegisterUserSerializer,
        responses={201: UserDetailsSerializer},
        operation_id="register_user"
    )
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = AuthenticationService.register_user(request=request, validated_data=serializer.validated_data)
        response_serializer = UserDetailsSerializer(user)
        return CustomeResponse.success(message="User registered successfully.", data=response_serializer.data, status=status.HTTP_201_CREATED)
