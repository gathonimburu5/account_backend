from django.urls import path
from .views import (
    CompanyListAPIView,
    CompanyCreateAPIView,
    CompanyDetailAPIView,
    CompanyUpdateApiView,
    CompanyActivateApiView,
    CompanyDeactivateAPIView,
    CurrencyListAPIView,
    CurrencyCreateAPIView,
    CurrencyDetailAPIView,
    CurrencyUpdateAPIView,
    CurrencyActivateAPIView,
    CurrencyDeactivateAPIView,
    FinancialPeriodListAPIView,
    CreateFinancialPeriodAPIView,
    FinancialPeriodDetailAPIView,
    UpdateFinancialPeriodAPIView,
    ActiveFinancialPeriodAPIView,
    DeactivateFinacialPeriodAPIView,
    CloseFinancialPeriodAPIView,
    ActivateFinancialPeriodAPIView,
)

urlpatterns = [
    # company urls
    path("company/", CompanyListAPIView.as_view(), name="company-list"),
    path("company/register/", CompanyCreateAPIView.as_view(), name="company-create"),
    path("company/<int:company_id>/", CompanyDetailAPIView.as_view(), name="company-detail"),
    path("company/<int:company_id>/update/", CompanyUpdateApiView.as_view(), name="company-update"),
    path("company/<int:company_id>/activate/", CompanyActivateApiView.as_view(), name="company-activate"),
    path("company/<int:company_id>/deactivate/", CompanyDeactivateAPIView.as_view(), name="company-deactivate"),
    # currency urls
    path("currency/", CurrencyListAPIView.as_view(), name="currency-list"),
    path("currency/register/", CurrencyCreateAPIView.as_view(), name="currency-create"),
    path("currency/<int:currency_id>/", CurrencyDetailAPIView.as_view(), name="currency-detail"),
    path("currency/<int:currency_id>/update/", CurrencyUpdateAPIView.as_view(), name="currency-update"),
    path("currency/<int:currency_id>/activate/", CurrencyActivateAPIView.as_view(), name="currency-activate"),
    path("currency/<int:currency_id>/deactivate/", CurrencyDeactivateAPIView.as_view(), name="currency-deactivate"),
    # financial period url
    path("financial-period/", FinancialPeriodListAPIView.as_view(), name="period-list"),
    path("financial-period/register/", CreateFinancialPeriodAPIView.as_view(), name="period-create"),
    path("financial-period/<int:pk>/", FinancialPeriodDetailAPIView.as_view(), name="period-detail"),
    path("financial-period/<int:pk>/update/", UpdateFinancialPeriodAPIView.as_view(), name="period-update"),
    path("financial-period/<int:pk>/activate/", ActivateFinancialPeriodAPIView.as_view(), name="period-activate"),
    path("financial-period/<int:pk>/deactivate/", DeactivateFinacialPeriodAPIView.as_view(), name="period-deactivate"),
    path("financial-period/<int:pk>/close/", CloseFinancialPeriodAPIView.as_view(), name="period-close"),
    path("financial-period/active/", ActiveFinancialPeriodAPIView.as_view(), name="active-period"),
]
