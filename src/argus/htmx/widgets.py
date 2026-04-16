import json

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

    def value_from_datadict(self, data, files, name):
        # Filter out falsy values (like empty strings) from submitted values
        values = super().value_from_datadict(data, files, name)
        if values:
            return [v for v in values if v]
        return values


class SearchDropdownMultiSelect(DropdownMultiSelect):
    template_name = "htmx/forms/search_select_multiple.html"


class BadgeDropdownMultiSelect(DropdownMultiSelect):
    template_name = "htmx/forms/badge_dropdown_select_multiple.html"


class ButtonDropdownMultiSelect(DropdownMultiSelect):
    template_name = "htmx/forms/button_dropdown_select_multiple.html"

    def selected_count(self, name, value, attrs):
        count = 0
        for _, options, _ in self.optgroups(name, value, attrs):
            for option in options:
                if option.get("selected", False):
                    count += 1
        return count

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        # Overwrites the parent's has_selected, derived from count
        count = self.selected_count(name, context["widget"]["value"], context["widget"]["attrs"])
        context["widget"]["selected_count"] = count
        context["widget"]["has_selected"] = count > 0
        return context


class DropdownRadioSelect(forms.RadioSelect):
    template_name = "htmx/forms/dropdown_radio_select.html"
    option_template_name = "htmx/forms/radio_option.html"

    def __init__(self, badge_classes=None, **kwargs):
        super().__init__(**kwargs)
        self.badge_classes = badge_classes or {}

    def __deepcopy__(self, memo):
        obj = super().__deepcopy__(memo)
        obj.badge_classes = self.badge_classes.copy()
        memo[id(self)] = obj
        return obj

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        option["badge_class"] = self.badge_classes.get(str(value), "")
        return option

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["badge_classes"] = self.badge_classes
        context["widget"]["badge_classes_json"] = json.dumps(self.badge_classes)
        return context
