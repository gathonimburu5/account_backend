from django.urls import path
from apps.accounts.views.auth_views import LoginUserAPIView, LogOutAPIView

urlpatterns = [
    path("login/", LoginUserAPIView.as_view(), name="user-login"),
    path("logout/", LogOutAPIView.as_view(), name="user-logout"),
]
