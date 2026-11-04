from textwrap import dedent

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from argus.drf import permissions
from .models import User
from .serializers import (
    BasicUserSerializer,
    UserSerializer,
)


class CurrentUserView(APIView):
    serializer_class = UserSerializer

    @extend_schema(
        summary="Get details for the user that accesses this endpoint",
    )
    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(instance=request.user, context={"request": request})
        return Response(serializer.data)


class BasicUserDetail(generics.RetrieveAPIView):
    serializer_class = BasicUserSerializer
    permission_classes = [permissions.IsAdmin]
    queryset = User.objects.all()

    @extend_schema(
        summary="Get details for a user",
        description=dedent(
            """
            Get details for a user.

            Limited to admins.
            """
        ),
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
