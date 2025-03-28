from django.forms import Form

# pydantic instead of dataclasses because the former has
# less surprises when subclassing
from pydantic import BaseModel


class Modal(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    instance_id: int = None
    template_name: str = "htmx/_base_form_modal_experimental.html"
    bulk: bool = None
    single: bool = None

    # needed by template
    button_class: str = "btn-primary"
    cancel_text: str = "Cancel"
    submit_text: str = "Ok"
    button_title: str
    dialog_id: str
    endpoint: str
    explanation: str
    header: str

    def get_endpoint(self):
        if self.instance_id:
            return self.endpoint.format(self.instance_id)
        return self.endpoint


class ConfirmationModal(Modal):
    pass


class FormModal(Modal):
    form: Form
