from .forms import SimplePreferenceForm


def setup_preference_forms(request) -> dict[str, SimplePreferenceForm]:
    "Prepare the preference forms for rendering"

    forms = {}
    for form_class in SimplePreferenceForm.__subclasses__():
        form = form_class(request=request)
        if form.choices and len(form.choices) == 1:
            # Hide forms with no real choices
            continue
        forms[form.fieldname] = form
    return forms
