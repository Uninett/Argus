from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User, Preferences
from argus.incident.models import SourceSystem
from argus.notificationprofile.models import DestinationConfig


class DestinationConfigInline(admin.TabularInline):
    model = DestinationConfig
    ordering = ["media", "label"]
    extra = 1

    def get_formset(self, request, obj=None, **kwargs):
        self.parent_obj = obj
        return super(DestinationConfigInline, self).get_formset(request, obj, **kwargs)

    def get_queryset(self, request):
        qs = super(DestinationConfigInline, self).get_queryset(request)
        return qs.filter(user=self.parent_obj)


class PreferencesInline(admin.TabularInline):
    model = Preferences


class SourceUserListFilter(admin.SimpleListFilter):
    title = "is incident source"
    parameter_name = "sourcesystem"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Yes"),
            ("no", "No"),
        )

    def queryset(self, request, queryset):
        ss = SourceSystem.objects.values_list("id", flat=True)
        if self.value() == "yes":
            return queryset.filter(id__in=ss)
        elif self.value() == "no":
            return queryset.exclude(id__in=ss)


class UserAdmin(DjangoUserAdmin):
    def sourcesystem__name(self, obj):
        sourcesystem = getattr(obj, "sourcesystem", None)
        if sourcesystem:
            return sourcesystem.name
        return None

    # inlines = [DestinationConfigInline]

    inlines = [PreferencesInline]
    list_filter = DjangoUserAdmin.list_filter + (SourceUserListFilter,)

    def has_delete_permission(self, request, obj=None):
        if obj:
            return not obj.is_used()
        return False


admin.site.register(User, UserAdmin)
