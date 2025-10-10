from argus.htmx.auth.views import LoginView as PlainArgusLoginView
from argus.auth.psa.utils import serialize_psa_authentication_backends


class PSALoginView(PlainArgusLoginView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        psa_backends = serialize_psa_authentication_backends()
        context["backends"].setdefault("external", []).extend(psa_backends)
        return context
