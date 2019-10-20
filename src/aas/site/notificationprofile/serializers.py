from rest_framework import serializers

from .models import NotificationProfile


class NotificationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationProfile
        fields = ['pk', 'name', 'interval_start', 'interval_stop']

    pk = serializers.ReadOnlyField()
