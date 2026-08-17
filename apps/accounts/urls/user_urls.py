from django.urls import path
from apps.accounts.views.user_views import RegisterUserAPIView

urlpatterns = [
    path("register/", RegisterUserAPIView.as_view(), name="user-register"),
]
