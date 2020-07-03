from django.db import IntegrityError
from rest_framework import fields, serializers

from .fields import FilterManyToManyField, TimeslotForeignKeyField
from .models import Filter, NotificationProfile, TimeInterval, Timeslot
from .validators import FilterStringValidator


class TimeIntervalSerializer(serializers.ModelSerializer):
    ALL_DAY_KEY = "all_day"

    days = fields.MultipleChoiceField(choices=TimeInterval.Day.choices)

    class Meta:
        model = TimeInterval
        fields = ["days", "start", "end"]

    def validate(self, attrs):
        if attrs["start"] >= attrs["end"]:
            raise serializers.ValidationError("Start time must be before end time.")
        return attrs

    def to_internal_value(self, data):
        if data.get(self.ALL_DAY_KEY):
            data["start"] = TimeInterval.DAY_START
            data["end"] = TimeInterval.DAY_END

        return super().to_internal_value(data)

    def to_representation(self, instance: TimeInterval):
        instance_dict = super().to_representation(instance)
        if instance_dict["start"] == str(TimeInterval.DAY_START) and instance_dict["end"] == str(TimeInterval.DAY_END):
            instance_dict[self.ALL_DAY_KEY] = True

        return instance_dict


class TimeslotSerializer(serializers.ModelSerializer):
    time_intervals = TimeIntervalSerializer(many=True)

    class Meta:
        model = Timeslot
        fields = ["pk", "name", "time_intervals"]
        read_only_fields = ["pk"]

    def create(self, validated_data):
        time_intervals_data = validated_data.pop("time_intervals")
        try:
            timeslot = Timeslot.objects.create(**validated_data)
        except IntegrityError as e:
            name = validated_data["name"]
            if Timeslot.objects.filter(name=name).exists():
                raise serializers.ValidationError(
                    f"Timeslot with the name '{name}' already exists for the user {validated_data['user']}."
                )
            else:
                raise e

        for time_interval_data in time_intervals_data:
            TimeInterval.objects.create(timeslot=timeslot, **time_interval_data)

        return timeslot

    def update(self, timeslot: Timeslot, validated_data):
        time_intervals_data = validated_data.pop("time_intervals")

        timeslot.name = validated_data["name"]
        timeslot.save()

        # Replace existing time intervals with posted time intervals
        timeslot.time_intervals.all().delete()
        for time_interval_data in time_intervals_data:
            TimeInterval.objects.create(timeslot=timeslot, **time_interval_data)

        return timeslot


class FilterSerializer(serializers.ModelSerializer):
    filter_string = serializers.CharField(validators=[FilterStringValidator()])

    class Meta:
        model = Filter
        fields = ["pk", "name", "filter_string"]
        read_only_fields = ["pk"]


class NotificationProfileSerializer(serializers.ModelSerializer):
    timeslot = TimeslotForeignKeyField()
    filters = FilterManyToManyField(many=True)
    media = fields.MultipleChoiceField(choices=NotificationProfile.MEDIA_CHOICES)

    class Meta:
        model = NotificationProfile
        fields = ["pk", "timeslot", "filters", "media", "active"]
        read_only_fields = ["pk"]

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError as e:
            timeslot_pk = validated_data["timeslot"].pk
            if NotificationProfile.objects.filter(pk=timeslot_pk).exists():
                raise serializers.ValidationError(
                    f"NotificationProfile with Timeslot with pk={timeslot_pk} already exists."
                )
            else:
                raise e
