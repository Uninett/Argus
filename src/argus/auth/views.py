from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from argus.drf.permissions import IsOwner
from .models import PhoneNumber, User
from .serializers import BasicUserSerializer, PhoneNumberSerializer, UserSerializer


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class BasicUserDetail(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BasicUserSerializer
    queryset = User.objects.all()


class PhoneNumberViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = PhoneNumberSerializer
    queryset = PhoneNumber.objects.none()  # For basename-detection in router

    def get_queryset(self):
        return self.request.user.phone_numbers.all()
