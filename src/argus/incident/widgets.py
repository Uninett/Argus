from datetime import datetime

from django.contrib.admin import widgets as admin_widgets
from django.forms import widgets

from argus.util.datetime_utils import get_infinity_repr


class AdminSplitDateTimeInfinity(admin_widgets.AdminSplitDateTime):
    template_name = "incident/admin/widgets/split_datetime_infinity.html"

    def __init__(self, initial_value: datetime, attrs=None):
        super().__init__(attrs)
        self.widgets = [*self.widgets, widgets.CheckboxInput()]
        self.initial_infinity_repr = get_infinity_repr(initial_value, str_repr=True)

    def decompress(self, value):
        # `value` is read from the rendered form, which means that
        # infinity instances have the value `9999-12-31 23:59:59` != `datetime.max`.
        # This necessitates adding the `initial_value` parameter to `__init__()` and checking it here.
        if self.initial_infinity_repr:
            return [None, None, True]
        return super().decompress(value) + [False]
