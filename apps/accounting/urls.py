from django.urls import path
from .views import (
    NominalAccountListAPIView,
    CreateNominalAccountAPIView,
    NominalAccountDetailAPIView,
    UpdateNominalAccountAPIView,
    ActivateNominalAccountAPIView,
    DeactivateNominalAccountAPIView,
)

urlpatterns = [
    path("", NominalAccountListAPIView.as_view(), name="account-list"),
    path("create", CreateNominalAccountAPIView.as_view(), name="account-create"),
    path("<int:pk>", NominalAccountDetailAPIView.as_view(), name="account-detail"),
    path("<int:pk>/update", UpdateNominalAccountAPIView.as_view(), name="account-update"),
    path("<int:pk>/activate", ActivateNominalAccountAPIView.as_view(), name="account-activate"),
    path("<int:pk>/deactivate", DeactivateNominalAccountAPIView.as_view(), name="account-dactivate"),
]

