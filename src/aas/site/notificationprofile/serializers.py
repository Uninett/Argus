from rest_framework import serializers

from .models import NotificationProfile


class NotificationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationProfile
        fields = ['user', 'name', 'interval_start', 'interval_stop']
