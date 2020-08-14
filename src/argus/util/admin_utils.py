from typing import Callable

from django.contrib import admin
from django.db.models import QuerySet


class YesNoListFilter(admin.SimpleListFilter):
    YES = 1
    NO = 0

    title: str
    # Parameter for the filter that will be used in the URL query
    parameter_name: str

    get_filter_func: Callable[[], Callable[[QuerySet, bool], QuerySet]]

    def lookups(self, request, model_admin):
        return (
            (self.YES, "Yes"),
            (self.NO, "No"),
        )

    def queryset(self, request, queryset):
        try:
            value = int(self.value())
        except (TypeError, ValueError):
            return None

        if value not in {self.YES, self.NO}:
            return None

        return self.get_filter_func()(queryset, bool(value))


def list_filter_factory(
    title: str, filter_func: Callable[[QuerySet, bool], QuerySet],
):
    title = title.lower()
    new_class_name = f"{title.title().replace(' ', '')}ListFilter"
    new_class_members = {
        "title": title,
        "parameter_name": title.replace(" ", "_"),
        # Can't pass `filter_func` directly, as calling it from the new class (`self.filter_func()`)
        # will pass an extra `self` argument
        "get_filter_func": lambda _self: filter_func,
    }
    new_class = type(new_class_name, (YesNoListFilter,), new_class_members)
    return new_class
