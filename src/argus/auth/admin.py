from argus.notificationprofile.models import DestinationConfig
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


class DestinationConfigInline(admin.TabularInline):
    model = DestinationConfig
    extra = 1


class UserAdminCustom(UserAdmin):
    inlines = [
        DestinationConfigInline,
    ]


admin.site.register(User, UserAdminCustom)
