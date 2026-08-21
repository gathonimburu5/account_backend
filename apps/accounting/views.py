from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.parsers import FormParser, MultiPartParser
from commons.responses import CustomeResponse
from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404
from apps.accounts.permissions import HasPermission
from apps.accounting.models import NominalAccount
from services.nominal_service import NorminalAccountService
from apps.accounting.serializers import (
    NominalAccountSerializer,
    NominalAccountCreateUpdateSerializer
)

class NominalAccountListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: NominalAccountSerializer(many=True)}, operation_id="account_list")
    def get(self, request):
        accounts = NorminalAccountService.get_accounts()
        serializer = NominalAccountSerializer(accounts, many=True)
        return CustomeResponse.success(
            message="retrieved successfully.",
            status=status.HTTP_200_OK,
            data=serializer.data
        )

class CreateNominalAccountAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser]

    @extend_schema(request=NominalAccountCreateUpdateSerializer, responses={201: NominalAccountSerializer}, operation_id="create_account")
    def post(self, request):
        serializer = NominalAccountCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = NorminalAccountService.create_account(**serializer.validated_data)
        serializer_response = NominalAccountSerializer(account)
        return CustomeResponse.success(
            message="nominal account created successfully.",
            status=status.HTTP_201_CREATED,
            data=serializer_response.data
        )

class NominalAccountDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: NominalAccountSerializer}, operation_id="account_detail")
    def get(self, request, pk):
        account = NorminalAccountService.get_account(pk)
        serializer = NominalAccountSerializer(account)
        return CustomeResponse.success(
            message="retrieved successfully.",
            status=status.HTTP_200_OK,
            data=serializer.data
        )

class UpdateNominalAccountAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser]

    @extend_schema(request=NominalAccountCreateUpdateSerializer, responses={200: NominalAccountSerializer}, operation_id="update_account")
    def put(self, request, pk):
        account = get_object_or_404(NominalAccount, pk=pk, is_active=True)
        serializer = NominalAccountCreateUpdateSerializer(account, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        account = NorminalAccountService.update_account(account=account, **serializer.validated_data)
        serializer_response = NominalAccountSerializer(account)
        return CustomeResponse.success(
            message="Nominal account updated successfully.",
            status=status.HTTP_200_OK,
            data=serializer_response.data
        )

class ActivateNominalAccountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: NominalAccountSerializer}, operation_id="activate_account")
    def patch(self, request, pk):
        account = get_object_or_404(NominalAccount, pk=pk, is_active=True)
        account = NorminalAccountService.activate_account(account=account)
        serializer = NominalAccountSerializer(account)
        return CustomeResponse.success(
            message="Nominal account activated successfully.",
            status=status.HTTP_200_OK,
            data=serializer.data
        )

class DeactivateNominalAccountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: NominalAccountSerializer}, operation_id="deactivate_account")
    def patch(self, request, pk):
        account = get_object_or_404(NominalAccount, pk=pk, is_active=True)
        account = NorminalAccountService.deactivate_account(account=account)
        serializer = NominalAccountSerializer(account)
        return CustomeResponse.success(
            message="Nominal account deactivated successfully.",
            status=status.HTTP_200_OK,
            data=serializer.data
        )
