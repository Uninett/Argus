from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, notification_profile):
        return notification_profile.user == request.user
