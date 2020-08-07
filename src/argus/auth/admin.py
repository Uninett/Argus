from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User
from .models import PhoneNumber


class PhoneNumberAdmin(admin.ModelAdmin):
    list_display = ["user", "phone_number"]
    search_fields = ["user", "phone_number"]
    autocomplete_fields = ["user"]


admin.site.register(PhoneNumber, PhoneNumberAdmin)
admin.site.register(User, UserAdmin)
