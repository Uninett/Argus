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
