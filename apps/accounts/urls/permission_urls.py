from django.urls import path
from apps.accounts.views.permission_views import (
    PermissionListAPIView,
    PermissionDetailAPIView,
    RoleListAPIView,
    RoleDetailAPIView,
    UserRoleListAPIView,
    UserRoleDetailAPIView,
)

urlpatterns = [
    path("permission/", PermissionListAPIView.as_view(), name="permission-list"),
    path("permission/<int:pk>/", PermissionDetailAPIView.as_view(), name="permission-details"),
    path("role/", RoleListAPIView.as_view(), name="role-list"),
    path("role/<int:pk>/", RoleDetailAPIView.as_view(), name="role-details"),
    path("users/<int:user_id>/roles/", UserRoleListAPIView.as_view(), name="user-role-list"),
    path("users/<int:user_id>/roles/<int:role_id>/", UserRoleDetailAPIView.as_view(), name="user-role-details"),
]
