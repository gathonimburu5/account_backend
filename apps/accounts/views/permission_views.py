from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.parsers import FormParser, MultiPartParser
from commons.responses import CustomeResponse
from drf_spectacular.utils import extend_schema
from services.authentication_service import PermissionService, RoleService
from apps.accounts.models import (Role, Permission, User)
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from apps.accounts.serializers import (
    PermissionSerializer,
    RoleSerializer,
    AssignRoleSerializer
)

class PermissionListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser]

    @extend_schema(
        responses={200: PermissionSerializer(many=True)},
        operation_id="permission_list"
    )
    def get(self, request):
        permissions = PermissionService.get_permissions()
        serializer = PermissionSerializer(permissions, many=True)
        return CustomeResponse.success(message="Retrieved successfully", data=serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=PermissionSerializer,
        responses={201: PermissionSerializer},
        operation_id="create_permission"
    )
    def post(self, request):
        serializer = PermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        permission = PermissionService.create_permission(request=request, validated_data=serializer.validated_data)
        serializer_response = PermissionSerializer(permission)
        return CustomeResponse.success(message="Permission created successfully.", data=serializer_response.data, status=status.HTTP_201_CREATED)

class PermissionDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser]

    @extend_schema(responses={200: PermissionSerializer}, operation_id="permission_detail")
    def get(self, request, pk):
        permission = PermissionService.get_permission(pk)
        serializer = PermissionSerializer(permission)
        return CustomeResponse.success(message="Retrieved successfully.", data=serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=PermissionSerializer,
        responses={200: PermissionSerializer},
        operation_id="update_permission"
    )
    def patch(self, request, pk):
        permission = PermissionService.get_permission(pk)
        serializer = PermissionSerializer(permission, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        permission = PermissionService.update_permission(request=request, permission=permission, validated_data=serializer.validated_data)
        serializer_response = PermissionSerializer(permission)
        return CustomeResponse.success(message="Successfully updated permission.", data=serializer_response.data, status=status.HTTP_200_OK)

    @extend_schema(responses={200: "deactivate permission"}, operation_id="deactivate_permission")
    def delete(self, request, pk):
        permission = PermissionService.get_permission(pk)
        PermissionService.deactivate_permission(request=request, permission=permission)
        return CustomeResponse.success(message="Successfully deactivated permission.", status=status.HTTP_200_OK)

class RoleListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser]

    @extend_schema(responses={200:RoleSerializer}, operation_id="role_list")
    def get(self, request):
        roles = RoleService.get_roles()
        serializer = RoleSerializer(roles, many=True)
        return CustomeResponse.success(data=serializer.data)

    @extend_schema(request=RoleSerializer, responses={201:RoleSerializer}, operation_id="create_role")
    def post(self, request):
        serializer = RoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = RoleService.create_role(request=request, validated_data=serializer.validated_data)
        serializer_response = RoleSerializer(role)
        return CustomeResponse.success(
            message="Successfully created role.",
            data= serializer_response.data,
            status=status.HTTP_201_CREATED
        )

class RoleDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser]

    @extend_schema(responses={200: RoleSerializer}, operation_id="role_detail")
    def get(self, request, pk):
        role = RoleService.get_role(pk)
        serializer = RoleSerializer(role)
        return CustomeResponse.success(
            message="Retrieved successfully",
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @extend_schema(request=RoleSerializer, responses={200:RoleSerializer}, operation_id="update_role")
    def patch(self, request, pk):
        role = RoleService.get_role(pk)
        serializer = RoleSerializer(role, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        role = RoleService.update_role(request=request, validated_data=serializer.validated_data)
        serializer_response = RoleSerializer(role)
        return CustomeResponse.success(
            message="Role updated successfully.",
            data=serializer_response.data,
            status=status.HTTP_200_OK
        )

    @extend_schema(responses={200: "deactivated successfully"}, operation_id="role_deactivate")
    def delete(self, request, pk):
        role = RoleService.get_role(pk)
        RoleService.deactivate_role(request=request, role=role)
        return CustomeResponse.success(
            message="Role successfully deactivated",
            status=status.HTTP_200_OK
        )

class UserRoleListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser]

    @extend_schema(responses={200: RoleSerializer}, operation_id="user_role_list")
    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id, is_deleted=False)
        roles = RoleService.get_user_roles(user=user)
        serializer = RoleSerializer(roles, many=True)
        return CustomeResponse.success(
            message="retrieved successfully",
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @extend_schema(request=AssignRoleSerializer, responses={200: RoleSerializer}, operation_id="assign_role")
    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id, is_deleted=False)
        serializer = AssignRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = RoleService.assign_role(user=user, role=serializer.validated_data["role_id"])
        serializer_response = RoleSerializer(role)
        return CustomeResponse.success(
            message="successfully assigned role to user",
            data=serializer_response.data,
            status=status.HTTP_201_CREATED
        )
class UserRoleDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={204: "successfully removed"}, operation_id="remove_assigned_role")
    def delete(self, request, user_id, role_id):
        user = get_object_or_404(User, pk=user_id, is_deleted=False)
        role = user.roles.filter(pk=role_id).first()
        if not role:
            raise NotFound("Role is not assigned to this user.")
        RoleService.remove_role(user=user, role=role)
        return CustomeResponse.success(
            message="successfully removed role.",
            status=status.HTTP_204_NO_CONTENT
        )

