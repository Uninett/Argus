from django.http import HttpResponse
from django.core import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user(request):
    data = serializers.serialize("json", [request.user])
    return HttpResponse(data, content_type="application/json")
