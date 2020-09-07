from django.contrib.auth import logout
from rest_framework import generics
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from argus.drf.permissions import IsOwner
from .models import PhoneNumber, User
from .serializers import BasicUserSerializer, PhoneNumberSerializer, UserSerializer


class ObtainNewAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        try:
            Token.objects.get(user=user).delete()
        except Token.DoesNotExist:
            pass
        token = Token.objects.create(user=user)
        return Response({"token": token.key})


class LogoutView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        user = request.user
        if hasattr(user, "auth_token"):
            user_token = request.user.auth_token
            user_token.delete()
        # Log out from session
        logout(request)

        return Response()


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

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)
