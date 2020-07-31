import secrets

from rest_framework import generics, mixins, serializers, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from argus.auth.models import User
from .forms import AddSourceSystemForm
from .models import (
    ActiveIncident,
    Incident,
    ObjectType,
    ParentObject,
    ProblemType,
    SourceSystem,
    SourceSystemType,
)
from .permissions import IsOwnerOrReadOnly, IsSuperuserOrReadOnly
from .serializers import (
    IncidentSerializer,
    ObjectTypeSerializer,
    ParentObjectSerializer,
    ProblemTypeSerializer,
    SourceSystemSerializer,
    SourceSystemTypeSerializer,
)


class SourceSystemTypeList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SourceSystemTypeSerializer
    queryset = SourceSystemType.objects.all()


class SourceSystemList(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrReadOnly]
    queryset = SourceSystem.objects.all()
    serializer_class = SourceSystemSerializer

    def create(self, request, *args, **kwargs):
        # Reuse the logic in the form that's used on the admin page
        form = AddSourceSystemForm(request.data)
        if not form.is_valid():
            # If the form is invalid because the username is unavailable:
            if User.objects.filter(username=form.data["username"]).exists():
                self._set_available_username(form)
            else:
                raise serializers.ValidationError(form.errors)

        source_system = form.save()
        serializer = SourceSystemSerializer(source_system)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @staticmethod
    def _set_available_username(form: AddSourceSystemForm):
        random_suffix = secrets.token_hex(3).upper()  # 16.8 million distinct values
        username = f"{form.data['username']}_{random_suffix}"
        form.data["username"] = username
        form.full_clean()  # re-checks for errors
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)


class SourceSystemDetail(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    queryset = SourceSystem.objects.all()
    serializer_class = SourceSystemSerializer


class IncidentViewSet(
    mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet,
):
    queryset = Incident.objects.prefetch_default_related().select_related("active_state")
    serializer_class = IncidentSerializer

    @action(detail=True, methods=["put"])
    def active(self, request, pk=None):
        if type(request.data) is not dict:
            raise serializers.ValidationError("The request body must contain JSON.")

        new_active_state = request.data.get("active")
        if new_active_state is None or type(new_active_state) is not bool:
            raise serializers.ValidationError("Field 'active' with a boolean value is missing from the request body.")
        incident = self.get_object()
        if new_active_state:
            ActiveIncident.objects.get_or_create(incident=incident)
        else:
            if hasattr(incident, "active_state"):
                incident.active_state.delete()

        incident = self.get_object()
        serializer = self.serializer_class(incident)
        return Response(serializer.data)

    @action(detail=True, methods=["put"])
    def ticket_url(self, request, pk=None):
        new_ticket_url = request.data.get("ticket_url")
        incident = self.get_object()
        new_incident = self.serializer_class(incident, data={"ticket_url": new_ticket_url}, partial=True)
        new_incident.is_valid(raise_exception=True)
        new_incident.save()
        return Response(new_incident.data)


class ActiveIncidentList(generics.ListAPIView):
    serializer_class = IncidentSerializer

    def get_queryset(self):
        return Incident.objects.active().prefetch_default_related()


@api_view(["PUT"])
def change_incident_active_view(request, incident_pk):
    if type(request.data) is not dict:
        raise serializers.ValidationError("The request body must contain JSON.")

    new_active_state = request.data.get("active")
    if new_active_state is None or type(new_active_state) is not bool:
        raise serializers.ValidationError("Field 'active' with a boolean value is missing from the request body.")

    incident = Incident.objects.get(pk=incident_pk)
    if new_active_state:
        ActiveIncident.objects.get_or_create(incident=incident)
    else:
        if hasattr(incident, "active_state"):
            incident.active_state.delete()

    # Re-fetch the incident to get updated state after creating/deleting ActiveIncident object
    incident = Incident.objects.get(pk=incident_pk)
    serializer = IncidentSerializer(incident)
    return Response(serializer.data)


@api_view(["GET"])
def get_all_meta_data_view(request):
    source_systems = SourceSystemSerializer(SourceSystem.objects.select_related("type"), many=True)
    object_types = ObjectTypeSerializer(ObjectType.objects.all(), many=True)
    parent_objects = ParentObjectSerializer(ParentObject.objects.all(), many=True)
    problem_types = ProblemTypeSerializer(ProblemType.objects.all(), many=True)
    data = {
        "sourceSystems": source_systems.data,
        "objectTypes": object_types.data,
        "parentObjects": parent_objects.data,
        "problemTypes": problem_types.data,
    }
    return Response(data)
