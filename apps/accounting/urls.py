from django.urls import path
from .views import (
    NominalAccountListAPIView, CreateNominalAccountAPIView, NominalAccountDetailAPIView, UpdateNominalAccountAPIView, ActivateNominalAccountAPIView, DeactivateNominalAccountAPIView,
    AccountTypeListAPIView, CreateAccountTypeAPIView, AccountTypeDetailAPIView, UpdateAccountTypeAPIView, ActivateAccountTypeAPIView, DeactivateAccountTypeAPIView, ActiveAccountTypeAPIView,
    RootNominalAccountListAPIView, ChildrenNominalAccountAPIView, PostingNominalAccountsAPIView, ControlNominalAccountAPIView
)

urlpatterns = [
    path("accounts", NominalAccountListAPIView.as_view(), name="account-list"),
    path("accounts-roots", RootNominalAccountListAPIView.as_view(), name="root-account-list"),
    path("accounts/<int:pk>/children", ChildrenNominalAccountAPIView.as_view(), name="children-account-list"),
    path("accounts-posting", PostingNominalAccountsAPIView.as_view(), name="posting-account-list"),
    path("accounts-control", ControlNominalAccountAPIView.as_view(), name="control-account-list"),
    path("accounts/create", CreateNominalAccountAPIView.as_view(), name="account-create"),
    path("accounts/<int:pk>", NominalAccountDetailAPIView.as_view(), name="account-detail"),
    path("accounts/<int:pk>/update", UpdateNominalAccountAPIView.as_view(), name="account-update"),
    path("accounts/<int:pk>/activate", ActivateNominalAccountAPIView.as_view(), name="account-activate"),
    path("accounts/<int:pk>/deactivate", DeactivateNominalAccountAPIView.as_view(), name="account-dactivate"),
    path("account-types", AccountTypeListAPIView.as_view(), name="account-type-list"),
    path("account-types/create", CreateAccountTypeAPIView.as_view(), name="account-type-create"),
    path("account-types/<int:pk>", AccountTypeDetailAPIView.as_view(), name="account-type-details"),
    path("account-types/<int:pk>/update", UpdateAccountTypeAPIView.as_view(), name="account-type-update"),
    path("account-types/<int:pk>/activate", ActivateAccountTypeAPIView.as_view(), name="account-type-activate"),
    path("account-types/<int:pk>/deactivate", DeactivateAccountTypeAPIView.as_view(), name="account-type-deactivate"),
    path("account-types/active", ActiveAccountTypeAPIView.as_view(), name="account-type-active"),
]

