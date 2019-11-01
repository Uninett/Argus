from rest_framework import serializers

from .models import NotificationProfile, Filter


class NotificationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationProfile
        fields = ['pk', 'name', 'interval_start', 'interval_stop']
        read_only_fields = ['pk']


class FilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filter
        fields = ['user', 'name', 'filter']
        read_only_fields = ["user"]
