from textwrap import dedent

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from argus.drf import permissions
from .models import User
from .serializers import (
    BasicUserSerializer,
    UserSerializer,
)


@extend_schema_view(
    get=extend_schema(
        summary="Get details for the user that accesses this endpoint",
    ),
)
class CurrentUserView(APIView):
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        "blbl"
        serializer = self.serializer_class(instance=request.user, context={"request": request})
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        summary="Get details for a user",
        deprecated=True,
        description=dedent(
            """
            Get details for a user.

            Limited to admins.
            """
        ),
    )
)
class BasicUserDetail(generics.RetrieveAPIView):
    serializer_class = BasicUserSerializer
    permission_classes = [permissions.IsAdmin]
    queryset = User.objects.all()
