from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import (
    BasicUserSerializer,
    UserSerializer,
)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(instance=request.user, context={"request": request})
        return Response(serializer.data)


class BasicUserDetail(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BasicUserSerializer
    queryset = User.objects.all()
