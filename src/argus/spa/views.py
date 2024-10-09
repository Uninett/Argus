from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .utils import get_authentication_backend_name_and_type


class AuthMethodSerializer(serializers.Serializer):
    type = serializers.CharField(read_only=True)
    url = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)


@extend_schema_view(
    get=extend_schema(
        responses=AuthMethodSerializer,
    ),
)
class AuthMethodListView(APIView):
    http_method_names = ["get", "head", "options", "trace"]
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        data = get_authentication_backend_name_and_type(request=request)

        return Response(data)
