from rest_framework import serializers
from drf_spectacular.utils import inline_serializer


# response serializers without bodies

NoContent204Serializer = inline_serializer("no content", {})
Forbidden403Serializer = inline_serializer("forbidden", {})


# response serializers with fixed bodies

Unauthorized401Serializer = inline_serializer(
    "unauthorized",
    {"detail": serializers.CharField(default="Authentication credentials were not provided.")},
)
