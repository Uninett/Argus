from argus.notificationprofile.models import DestinationConfig
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import PhoneNumber, User


class DestinationConfigInline(admin.TabularInline):
    model = DestinationConfig
    extra = 1


class UserAdminCustom(UserAdmin):
    inlines = [
        DestinationConfigInline,
    ]


class PhoneNumberAdmin(admin.ModelAdmin):
    list_display = ["user", "phone_number"]
    search_fields = ["user", "phone_number"]
    autocomplete_fields = ["user"]


admin.site.register(PhoneNumber, PhoneNumberAdmin)
admin.site.register(User, UserAdminCustom)
