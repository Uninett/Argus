from typing import ClassVar, Any

from django.forms.renderers import get_default_renderer
from django.forms.utils import RenderableMixin

# pydantic instead of dataclasses because the former has
# less surprises when subclassing
from pydantic import BaseModel


class Modal(RenderableMixin, BaseModel):
    renderer: ClassVar[Any] = get_default_renderer()

    model_config = {"arbitrary_types_allowed": True}

    opener_button_template_name: str = "htmx/_base_form_modal_button.html"
    template_name: str = "htmx/_base_form_modal_experimental.html"

    # needed by template
    button_class: str = "btn-primary"
    cancel_text: str = "Cancel"
    submit_text: str = "Ok"
    button_title: str
    dialog_id: str
    endpoint: str
    explanation: str
    header: str

    def get_context(self):
        modal_dict = dict(self)
        return {"modal": modal_dict}


class ConfirmationModal(Modal):
    pass


class DeleteModal(ConfirmationModal):
    button_title: str = "Delete"
    submit_text: str = "Delete"
