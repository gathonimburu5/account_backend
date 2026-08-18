from django.urls import path
from apps.accounts.views.user_views import (
    RegisterUserAPIView,
    CurrentUserAPIView,
    UserListAPIView,
    UserDetailAPIView,
    ChangePasswordAPIView,
    ActivateUserAPIView,
    DeactivateUserAPIView,
    LockUserAPIView,
    UnlockUserAPIView,
)

urlpatterns = [
    path("register/", RegisterUserAPIView.as_view(), name="user-register"),
    path("profile/", CurrentUserAPIView.as_view(), name="current-user"),
    path("user-list/", UserListAPIView.as_view(), name="user-list"),
    path("user/<int:pk>/", UserDetailAPIView.as_view(), name="user-detail"),
    path("change-password/", ChangePasswordAPIView.as_view(), name="change-password"),
    path("user/<int:pk>/activate/", ActivateUserAPIView.as_view(), name="user-activate"),
    path("user/<int:pk>/deactivate/", DeactivateUserAPIView.as_view(), name="user-deactivate"),
    path("user/<int:pk>/lock/", LockUserAPIView.as_view(), name="user-lock"),
    path("user/<int:pk>/unlock/", UnlockUserAPIView.as_view(), name="user-unlock"),
]
