from typing import Callable, List, Sequence, Union

from django.contrib import admin
from django.contrib.admin.utils import quote
from django.db.models import Model, QuerySet
from django.urls import NoReverseMatch, reverse
from django.utils.html import format_html
from django.utils.text import capfirst


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
    title: str,
    filter_func: Callable[[QuerySet, bool], QuerySet],
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


def add_elements_to_deleted_objects(
    objs: Sequence[Model],
    to_delete: List[Union[str, list]],
    get_elements_func: Callable[[Model], Sequence[Model]],
    admin_site,
):
    new_to_delete = []
    num_objs = len(objs)
    obj_index = 0
    for element in to_delete:
        current_obj = objs[obj_index] if obj_index < num_objs else None
        if not isinstance(element, str) or str(current_obj) not in element:
            new_to_delete.append(element)
            continue

        new_to_delete.append(element)
        extra_elements = [admin_urlize(e, admin_site) for e in get_elements_func(current_obj)]
        new_to_delete.append(extra_elements)
        obj_index += 1

    return new_to_delete


def admin_urlize(obj: Model, admin_site):
    # Code based on https://github.com/django/django/blob/3.0.7/django/contrib/admin/utils.py#L121-L149
    opts = obj._meta

    no_edit_link = f"{capfirst(opts.verbose_name)}: {obj}"

    try:
        admin_url = reverse(f"{admin_site.name}:{opts.app_label}_{opts.model_name}_change", args=[quote(obj.pk)])
    except NoReverseMatch:
        # Change url doesn't exist -- don't display link to edit
        return no_edit_link

    # Display a link to the admin page.
    return format_html('{}: <a href="{}">{}</a>', capfirst(opts.verbose_name), admin_url, obj)
