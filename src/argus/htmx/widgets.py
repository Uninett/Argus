from django import forms


class ExtraWidgetMixin:
    def __init__(self, extra=None, **kwargs):
        super().__init__(**kwargs)
        self.extra = {} if extra is None else extra

    def __deepcopy__(self, memo):
        obj = super().__deepcopy__(memo)
        obj.extra = self.extra.copy()
        memo[id(self)] = obj
        return obj

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["extra"] = self.extra
        return context


class DropdownMultiSelect(ExtraWidgetMixin, forms.CheckboxSelectMultiple):
    template_name = "htmx/forms/dropdown_select_multiple.html"
    option_template_name = "htmx/forms/checkbox_select_multiple.html"

    def __init__(self, partial_get, **kwargs):
        super().__init__(**kwargs)
        self.partial_get = partial_get

    def __deepcopy__(self, memo):
        obj = super().__deepcopy__(memo)
        obj.partial_get = self.partial_get
        memo[id(self)] = obj
        return obj

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["partial_get"] = self.partial_get
        widget_value = context["widget"]["value"]
        context["widget"]["has_selected"] = self.has_selected(name, widget_value, attrs)
        return context

    def has_selected(self, name, value, attrs):
        for _, options, _ in self.optgroups(name, value, attrs):
            for option in options:
                if option.get("selected", False):
                    return option.get("selected", False)
        return False


class BadgeDropdownMultiSelect(DropdownMultiSelect):
    template_name = "htmx/forms/badge_dropdown_select_multiple.html"
