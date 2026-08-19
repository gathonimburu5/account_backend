from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.parsers import FormParser, MultiPartParser
from commons.responses import CustomeResponse
from drf_spectacular.utils import extend_schema
from services.authentication_service import AuthenticationService
from apps.accounts.models import (User)
from django.shortcuts import get_object_or_404
from apps.accounts.permissions import HasPermission
from apps.accounts.serializers import (
    RegisterUserSerializer,
    UserSerializer,
    PasswordChangeSerializer,
    UpdateUserSerializer,
)

class RegisterUserAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=RegisterUserSerializer,
        responses={201: UserSerializer},
        operation_id="register_user"
    )
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = AuthenticationService.register_user(request=request, validated_data=serializer.validated_data)
        response_serializer = UserSerializer(user)
        return CustomeResponse.success(message="User registered successfully.", data=response_serializer.data, status=status.HTTP_201_CREATED)

class CurrentUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserSerializer},
        operation_id="current_user"
    )
    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return CustomeResponse.success(message="Current user retrieved successfully.", data=serializer.data, status=status.HTTP_200_OK)

class UserListAPIView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    permission_code = "ACCOUNTS.USER.VIEW"

    @extend_schema(
        responses={200: UserSerializer(many=True)},
        operation_id="user_list"
    )
    def get(self, request):
        users = User.objects.filter(is_deleted=False).prefetch_related("roles")
        serializer = UserSerializer(users, many=True)
        return CustomeResponse.success(message="user list retrieved successfully.", data=serializer.data, status=status.HTTP_200_OK)

class UserDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser]

    def get_object(self, pk):
        return get_object_or_404(User.objects.prefetch_related("roles"), pk=pk, is_deleted=False)

    def get(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return CustomeResponse.error(message="user not found.", status=status.HTTP_400_BAD_REQUEST)
        serializer = UserSerializer(user)
        return CustomeResponse.success(message="user retrieved successfully.", data=serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=UpdateUserSerializer,
        responses={200, UserSerializer},
        operation_id="user_update"
    )
    def put(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return CustomeResponse.error(message="user not found.", status=status.HTTP_400_BAD_REQUEST)
        serializer = UpdateUserSerializer(user)
        serializer.is_valid(raise_exception=True)
        update_response = AuthenticationService.update_user(user=user, request=request, validated_data=serializer.validated_data)
        serializer_response = UserSerializer(update_response)
        return CustomeResponse.success(message="user updated successfully.", data=serializer_response.data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={200: "deleted successfully"},
        operation_id="user_deleted"
    )
    def delete(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return CustomeResponse.error(message="user not found.", status=status.HTTP_400_BAD_REQUEST)
        AuthenticationService.delete_user(user=user, request=request)
        return CustomeResponse.success(message="user deleted successfully.", status=status.HTTP_200_OK)

class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser]

    @extend_schema(
        request=PasswordChangeSerializer,
        responses={200: "Password changed successfully."},
        operation_id="password_change"
    )
    def patch(self, request):
        user = request.user
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthenticationService.change_password(user=user, request=request, validated_data=serializer.validated_data)
        return CustomeResponse.success(message="Password changed successfully.", status=status.HTTP_200_OK)

class ActivateUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: "activated successfully."},
        operation_id="activate_user"
    )
    def patch(self, request, pk):
        user = get_object_or_404(User.objects.prefetch_related("roles"), pk=pk, is_deleted=False)
        AuthenticationService.activate_user(user=user, request=request)
        return CustomeResponse.success(message="User activated successfully.", status=status.HTTP_200_OK)

class DeactivateUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: "Deactivated successfully."},
        operation_id="deactivate_user"
    )
    def patch(self, request, pk):
        user = get_object_or_404(User.objects.prefetch_related("roles"), pk=pk, is_deleted=False)
        AuthenticationService.deactivate_user(user=user, request=request)
        return CustomeResponse.success(message="User deactivated successfully.", status=status.HTTP_200_OK)


class LockUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: "Locked successfully."},
        operation_id="locked_user"
    )
    def patch(self, request, pk):
        user = get_object_or_404(User.objects.prefetch_related("roles"), pk=pk, is_deleted=False)
        AuthenticationService.lock_user(user=user, request=request)
        return CustomeResponse.success(message="User locked successfully", status=status.HTTP_200_OK)

class UnlockUserAPIView(APIView):
    permission_classes = [APIView]

    @extend_schema(
        responses={200: "Unlocked successfully"},
        operation_id="unlocked_user"
    )
    def patch(self, request, pk):
        user = get_object_or_404(User.objects.prefetch_related("roles"), pk=pk, is_deleted=False)
        AuthenticationService.unlock_user(user=user, request=request)
        return CustomeResponse.success(message="User unlocked successfully.", status=status.HTTP_200_OK)


