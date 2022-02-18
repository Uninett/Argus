from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
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
    post=extend_schema(
        request=RequestPhoneNumberSerializerV1,
        responses={201: ResponsePhoneNumberSerializerV1},
    ),
    # update=extend_schema(
    #     request=RequestPhoneNumberSerializerV1,
    # ),
    # partial_update=extend_schema(
    #     request=RequestPhoneNumberSerializerV1,
    # ),
)
class PhoneNumberViewV1(APIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = ResponsePhoneNumberSerializerV1
    write_serializer_class = RequestDestinationConfigSerializer

    def get(self, request, *args, **kwargs):
        data = [
            {"pk": destination.pk, "user": destination.user.pk, "phone_number": destination.settings["phone_number"]}
            for destination in DestinationConfig.objects.filter(media__slug="sms")
        ]
        serializer = self.serializer_class(data, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        data = {"media": "sms", "settings": request.data}
        serializer = self.write_serializer_class(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
