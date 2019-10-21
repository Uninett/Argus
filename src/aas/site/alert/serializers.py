from rest_framework import serializers

from .models import Alert


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = ['pk', 'timestamp', 'source', 'alert_id', 'object', 'parent_object', 'details_url', 'problem_type', 'description']
        read_only_fields = ['pk']
