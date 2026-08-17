from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .responses import CustomeResponse
from drf_spectacular.utils import extend_schema

class HealthCheckAPIView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        responses={200: "response here"}
    )
    def get(self, request):
        return Response({ "status":"OK", "service":"accounting-api" })