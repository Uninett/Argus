from django.views.generic import RedirectView, FormView

from .forms import StyleGuideForm


class IncidentListRedirectView(RedirectView):
    "Redirect to incident list, which may trigger a login"

    permanent = False
    query_string = False
    pattern_name = "htmx:incident-list"


class StyleGuideView(FormView):
    login_required = False
    template_name = "htmx/styleguide.html"
    http_method_names = ["get", "head", "options", "trace"]
    form_class = StyleGuideForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if not kwargs.get("data", None):
            kwargs["data"] = self.request.GET
        return kwargs

    def get_initial(self):
        if self.request.GET or self.request.POST:
            form_class = self.get_form_class()
            form = form_class(self.request.GET)
            form.is_valid()
            return form.cleaned_data
        return super().get_initial()

    def get(self, request, *args, **kwargs):
        if self.request.GET:
            form = self.get_form()
            form.is_valid()
            return self.form_invalid(form)
        return super().get(request, *args, **kwargs)
