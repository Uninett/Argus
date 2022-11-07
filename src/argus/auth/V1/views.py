from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from argus.drf.permissions import IsOwner
from argus.notificationprofile.models import DestinationConfig
from argus.notificationprofile.serializers import RequestDestinationConfigSerializer
from .serializers import RequestPhoneNumberSerializerV1, ResponsePhoneNumberSerializerV1, UserSerializerV1


class CurrentUserViewV1(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializerV1

    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)


@extend_schema_view(
    create=extend_schema(
        request=RequestPhoneNumberSerializerV1,
    ),
    update=extend_schema(
        request=RequestPhoneNumberSerializerV1,
    ),
    partial_update=extend_schema(
        request=RequestPhoneNumberSerializerV1,
    ),
)
class PhoneNumberViewV1(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = ResponsePhoneNumberSerializerV1
    write_serializer_class = RequestDestinationConfigSerializer
    queryset = DestinationConfig.objects.filter(media_id="sms").all()

    def list(self, request):
        serializer = self.serializer_class(self.queryset.filter(user=request.user), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, pk=None):
        if pk:
            destination = get_object_or_404(self.queryset.filter(user=request.user), pk=pk)
            serializer = self.write_serializer_class(
                destination, data={"media": "sms", "settings": request.data}, context={"request": request}
            )
        else:
            serializer = self.write_serializer_class(
                data={"media": "sms", "settings": request.data}, context={"request": request}
            )
        if serializer.is_valid():
            serializer.save(user=request.user)
            response_serializer = self.serializer_class(serializer.instance)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        response_serializer = self.serializer_class(
            data={"user": request.user.pk, "phone_number": serializer.data["settings"]["phone_number"]}
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        destination = get_object_or_404(self.queryset.filter(user=request.user), pk=pk)
        serializer = self.serializer_class(destination)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        if request.stream.method == "PUT":
            destination = self.queryset.filter(user=request.user).filter(pk=pk).first()
        elif request.stream.method == "PATCH":
            destination = get_object_or_404(self.queryset.filter(user=request.user), pk=pk)
        serializer = self.write_serializer_class(
            destination, data={"media": "sms", "settings": request.data}, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save(user=request.user)
            response_serializer = self.serializer_class(serializer.instance)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        response_serializer = self.serializer_class(
            data={"user": request.user.pk, "phone_number": serializer.data["settings"]["phone_number"]}
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        destination = get_object_or_404(self.queryset.filter(user=request.user), pk=pk)
        serializer = self.write_serializer_class(
            destination, data={"media": "sms", "settings": request.data}, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            response_serializer = self.serializer_class(serializer.instance)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        response_serializer = self.serializer_class(
            data={"user": request.user.pk, "phone_number": serializer.data["settings"]["phone_number"]}
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        destination = get_object_or_404(self.queryset.filter(user=request.user), pk=pk)
        destination.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
