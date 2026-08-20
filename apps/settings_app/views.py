from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.parsers import FormParser, MultiPartParser
from commons.responses import CustomeResponse
from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404
from apps.accounts.permissions import HasPermission
from apps.settings_app.models import FinancialPeriod
from apps.settings_app.serializers import (
    CompanySerializer,
    CompanyRegisterSerializer,
    CurrencySerializer,
    CurrencyCreateSerializer,
    FinancialPeriodSerializer,
    FinancialPeriodCreateSerializer,
)
from services.settings_services import SettingService

class CompanyListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: CompanySerializer(many=True)}, operation_id="company_list")
    def get(self, request):
        company = SettingService.get_componies()
        serializer = CompanySerializer(company, many=True)
        return CustomeResponse.success(
            message="Retrieved successfully",
            status=status.HTTP_200_OK,
            data=serializer.data
        )
class CompanyCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(request=CompanyRegisterSerializer, responses={201: CompanySerializer}, operation_id="create_company")
    def post(self, request):
        serializer = CompanyRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = SettingService.create_company(request=request, validated_data=serializer.validated_data)
        serializer_response = CompanySerializer(company)
        return CustomeResponse.success(
            message="successfully created company.",
            status=status.HTTP_201_CREATED,
            data=serializer_response.data
        )
class CompanyDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: CompanySerializer}, operation_id="company_detail")
    def get(self, request, company_id):
        company = SettingService.get_company(company_id)
        serializer = CompanySerializer(company)
        return CustomeResponse.success(
            message="retrieved successfully.",
            status=status.HTTP_200_OK,
            data=serializer.data
        )
class CompanyUpdateApiView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(request=CompanyRegisterSerializer, responses={200: CompanySerializer}, operation_id="update_company")
    def put(self, request, company_id):
        company = SettingService.get_company(company_id)
        serializer = CompanyRegisterSerializer(company, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        company = SettingService.update_company(request=request, company=company, validated_data=serializer.validated_data)
        serializer_response = CompanySerializer(company)
        return CustomeResponse.success(
            message="successfully updated company.",
            status=status.HTTP_200_OK,
            data=serializer_response.data
        )
class CompanyActivateApiView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: CompanySerializer}, operation_id="activate_company")
    def patch(self, request, company_id):
        company = SettingService.get_company(company_id)
        company = SettingService.activate_company(request=request, company=company)
        serializer_response = CompanySerializer(company)
        return CustomeResponse.success(
            message="company activated successfully.",
            status=status.HTTP_200_OK,
            data=serializer_response.data
        )
class CompanyDeactivateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: CompanySerializer}, operation_id="deactivate_company")
    def patch(self, request, company_id):
        company = SettingService.get_company(company_id)
        company = SettingService.deactivate_company(request=request, company=company)
        serializer = CompanySerializer(company)
        return CustomeResponse.success(
            message="company deactivated successfully.",
            status=status.HTTP_200_OK,
            data=serializer.data
        )

class CurrencyListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: CurrencySerializer(many=True)}, operation_id="currency_list")
    def get(self, request):
        currencies = SettingService.get_currencies()
        serializer = CurrencySerializer(currencies, many=True)
        return CustomeResponse.success(
            message="retrieved successfully.",
            status=status.HTTP_200_OK,
            data=serializer.data
        )

class CurrencyCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser]

    @extend_schema(request=CurrencyCreateSerializer, responses={201: CurrencySerializer}, operation_id="create_currency")
    def post(self, request):
        serializer = CurrencyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        currency = SettingService.create_currency(request=request, validated_data=serializer.validated_data)
        serializer_response = CurrencySerializer(currency)
        return CustomeResponse.success(
            message="currency created successfully.",
            status=status.HTTP_201_CREATED,
            data=serializer_response.data
        )

class CurrencyDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: CurrencySerializer}, operation_id="currency_detail")
    def get(self, request, currency_id):
        currency = SettingService.get_currency(currency_id)
        serializer = CurrencySerializer(currency)
        return CustomeResponse.success(
            message="retrieved successfully.",
            status=status.HTTP_200_OK,
            data=serializer.data
        )

class CurrencyUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser]

    @extend_schema(request=CurrencyCreateSerializer, responses={200: CurrencySerializer}, operation_id="update_currency")
    def put(self, request, currency_id):
        currency = SettingService.get_currency(currency_id)
        serializer = CurrencyCreateSerializer(currency, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        currency = SettingService.update_currency(request=request, currency=currency, validated_data=serializer.validated_data)
        serializer_response = CurrencySerializer(currency)
        return CustomeResponse.success(
            message="currency updated successfully.",
            status=status.HTTP_200_OK,
            data=serializer_response.data
        )

class CurrencyActivateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: CurrencySerializer}, operation_id="activate_currency")
    def patch(self, request, currency_id):
        currency = SettingService.get_currency(currency_id)
        currency = SettingService.activate_currency(request=request, currency=currency)
        serializer = CurrencySerializer(currency)
        return CustomeResponse.success(
            message="currency activated successfully.",
            status=status.HTTP_200_OK,
            data=serializer.data
        )

class CurrencyDeactivateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: CurrencySerializer}, operation_id="deactivate_currency")
    def patch(self, request, currency_id):
        currency = SettingService.get_currency(currency_id)
        currency = SettingService.deactivate_currency(request=request, currency=currency)
        serializer = CurrencySerializer(currency)
        return CustomeResponse.success(
            message="currency deactivated successfully.",
            status=status.HTTP_200_OK,
            data=serializer.data
        )

class FinancialPeriodListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: FinancialPeriodSerializer(many=True)}, operation_id="period_list")
    def get(self, request):
        periods = SettingService.get_periods()
        serializer = FinancialPeriodSerializer(periods, many=True)
        return CustomeResponse.success(
            message="retrieved successfully.",
            status=status.HTTP_200_OK,
            data=serializer.data
        )
class CreateFinancialPeriodAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=FinancialPeriodCreateSerializer, responses={201: FinancialPeriodSerializer}, operation_id="create_period")
    def post(self, request):
        serializer = FinancialPeriodCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        period = SettingService.create_period(
            request=request,
            **serializer.validated_data,
        )
        serializer_response = FinancialPeriodSerializer(period)
        return CustomeResponse.success(
            message="financial period created successfully.",
            status=status.HTTP_201_CREATED,
            data=serializer_response.data
        )

class FinancialPeriodDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: FinancialPeriodSerializer}, operation_id="period_details")
    def get(self, request, pk):
        period = SettingService.get_period(pk)
        serializer = FinancialPeriodSerializer(period)
        return CustomeResponse.success(
            message="retrieve period",
            status=status.HTTP_200_OK,
            data=serializer.data
        )

class UpdateFinancialPeriodAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=FinancialPeriodCreateSerializer, responses={200: FinancialPeriodSerializer}, operation_id="update_period")
    def put(self, request, pk):
        period = get_object_or_404(FinancialPeriod, pk=pk)
        serializer = FinancialPeriodCreateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        period = SettingService.update_period(period=period, **serializer.validated_data)
        serializer_response = FinancialPeriodSerializer(period)
        return CustomeResponse.success(
            message="financial period updated successfully.",
            status=status.HTTP_200_OK,
            data=serializer_response.data
        )

class ActivateFinancialPeriodAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: FinancialPeriodSerializer}, operation_id="activate_period")
    def patch(self, request, pk):
        period = get_object_or_404(FinancialPeriod, pk=pk)
        period = SettingService.activate_period(period=period)
        serializer = FinancialPeriodSerializer(period)
        return CustomeResponse.success(
            message="financial period activated successfully.",
            status=status.HTTP_200_OK,
            data=serializer.data
        )

class DeactivateFinacialPeriodAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: FinancialPeriodSerializer}, operation_id="deactivate_period")
    def patch(self, request, pk):
        period = get_object_or_404(FinancialPeriod, pk=pk)
        period = SettingService.deactivate_period(period=period)
        serializer = FinancialPeriodSerializer(period)
        return CustomeResponse.success(
            message="finacial period deactivated successfully.",
            status=status.HTTP_200_OK,
            data=serializer.data
        )

class CloseFinancialPeriodAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: FinancialPeriodSerializer}, operation_id="close_period")
    def patch(self, request, pk):
        period = get_object_or_404(FinancialPeriod, pk=pk)
        period = SettingService.close_period(period=period)
        serializer = FinancialPeriodSerializer(period)
        return CustomeResponse.success(
            message="financial period closed successfully.",
            status=status.HTTP_200_OK,
            data=serializer.data
        )

class ActiveFinancialPeriodAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: FinancialPeriodSerializer}, operation_id="active_period")
    def get(self, request):
        period = SettingService.get_active_period()
        serializer = FinancialPeriodSerializer(period)
        return CustomeResponse.success(
            message="retrieve active period",
            status=status.HTTP_200_OK,
            data=serializer.data
        )
