from rest_framework import fields, serializers

from .primitive_serializers import FilterBlobSerializer, FilterPreviewSerializer
from .media import MEDIA_CLASSES_DICT
from .models import DestinationConfig, Filter, Media, NotificationProfile, TimeRecurrence, Timeslot
from .validators import validate_filter_string


class TimeRecurrenceSerializer(serializers.ModelSerializer):
    ALL_DAY_KEY = "all_day"

    days = fields.MultipleChoiceField(choices=TimeRecurrence.Day.choices)

    class Meta:
        model = TimeRecurrence
        fields = [
            "days",
            "start",
            "end",
        ]

    def validate(self, attrs: dict):
        if attrs["start"] >= attrs["end"]:
            raise serializers.ValidationError("'start' must be before 'end'.")
        return attrs

    def to_internal_value(self, data: dict):
        if data.get(self.ALL_DAY_KEY):
            data["start"] = TimeRecurrence.DAY_START
            data["end"] = TimeRecurrence.DAY_END

        return super().to_internal_value(data)

    def to_representation(self, instance: TimeRecurrence):
        instance_dict = super().to_representation(instance)
        # `days` is initially represented as a set; this converts it into a sorted list
        # (`days` is stored sorted in the DB - see `TimeRecurrence.save()`)
        instance_dict["days"] = sorted(instance_dict["days"])

        if instance_dict["start"] == str(TimeRecurrence.DAY_START) and instance_dict["end"] == str(
            TimeRecurrence.DAY_END
        ):
            instance_dict[self.ALL_DAY_KEY] = True

        return instance_dict


class TimeslotSerializer(serializers.ModelSerializer):
    time_recurrences = TimeRecurrenceSerializer(many=True)

    class Meta:
        model = Timeslot
        fields = [
            "pk",
            "name",
            "time_recurrences",
        ]
        # "user" isn't in the list of fields so we can't use a UniqueTogetherValidator

    def validate_name(self, name):
        owner = self.context["request"].user
        qs = Timeslot.objects.filter(user=owner, name=name)
        if not qs.exists():  # create
            return name
        instance = getattr(self, "instance", None)  # update
        if instance and qs.filter(pk=instance.pk).exists():
            return name
        raise serializers.ValidationError(
            f'The name "{name}" is already in use for a another timeslot owned by user {owner}.'
        )

    def create(self, validated_data: dict):
        time_recurrences_data = validated_data.pop("time_recurrences")
        timeslot = Timeslot.objects.create(**validated_data)

        for time_recurrence_data in time_recurrences_data:
            TimeRecurrence.objects.create(timeslot=timeslot, **time_recurrence_data)

        return timeslot

    def update(self, timeslot: Timeslot, validated_data: dict):
        time_recurrences_data = validated_data.pop("time_recurrences", None)
        name = validated_data.pop("name", None)
        if name:
            timeslot.name = name
            timeslot.save()

        # Replace existing time recurrences with posted time recurrences
        if time_recurrences_data:
            timeslot.time_recurrences.all().delete()
            for time_recurrence_data in time_recurrences_data:
                TimeRecurrence.objects.create(timeslot=timeslot, **time_recurrence_data)

        return timeslot


class FilterSerializer(serializers.ModelSerializer):
    filter_string = serializers.CharField(
        validators=[validate_filter_string],
        help_text='Deprecated: Use "filter" instead',
    )
    filter = FilterBlobSerializer(required=False)

    class Meta:
        model = Filter
        fields = [
            "pk",
            "name",
            "filter_string",
            "filter",
        ]


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = [
            "slug",
            "name",
        ]


class JSONSchemaSerializer(serializers.Serializer):
    json_schema = serializers.JSONField()


class ResponseDestinationConfigSerializer(serializers.ModelSerializer):
    media = MediaSerializer()
    suggested_label = serializers.SerializerMethodField("get_suggested_label")

    class Meta:
        model = DestinationConfig
        fields = [
            "pk",
            "media",
            "label",
            "suggested_label",
            "settings",
        ]

    def get_suggested_label(self, destination: DestinationConfig) -> str:
        return f"{destination.media.name}: {MEDIA_CLASSES_DICT[destination.media.slug].get_label(destination)}"


class RequestDestinationConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationConfig
        fields = [
            "media",
            "label",
            "settings",
        ]

    def validate(self, attrs: dict):
        if self.instance and "media" in attrs.keys() and not attrs["media"].slug == self.instance.media.slug:
            raise serializers.ValidationError("Media cannot be updated, only settings.")
        if "settings" in attrs.keys():
            if type(attrs["settings"]) != dict:
                raise serializers.ValidationError("Settings has to be a dictionary.")
            if self.instance:
                attrs["settings"] = MEDIA_CLASSES_DICT[self.instance.media.slug].validate(
                    self, attrs, self.context["request"].user
                )
            else:
                attrs["settings"] = MEDIA_CLASSES_DICT[attrs["media"].slug].validate(
                    self, attrs, self.context["request"].user
                )

        return attrs

    def update(self, destination: DestinationConfig, validated_data: dict):
        updated_destination = MEDIA_CLASSES_DICT[destination.media.slug].update(destination, validated_data)

        if updated_destination:
            return updated_destination

        return super().update(destination, validated_data)


class DuplicateDestinationSerializer(serializers.Serializer):
    is_duplicate = serializers.BooleanField(read_only=True)


class ResponseNotificationProfileSerializer(serializers.ModelSerializer):
    timeslot = TimeslotSerializer()
    filters = FilterSerializer(many=True)
    destinations = ResponseDestinationConfigSerializer(many=True)

    class Meta:
        model = NotificationProfile
        fields = [
            "pk",
            "name",
            "timeslot",
            "filters",
            "destinations",
            "active",
        ]


class RequestNotificationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationProfile
        fields = [
            "name",
            "timeslot",
            "filters",
            "destinations",
            "active",
        ]

    def validate(self, attrs: dict):
        if attrs["timeslot"].user != self.context["request"].user:
            raise serializers.ValidationError("The user of 'timeslot' must be the same as the requesting user.")
        return attrs
