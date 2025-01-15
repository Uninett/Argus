from dataclasses import dataclass


@dataclass
class ModalForm:
    form: int = None
    instance_id: int = None
    template_name: str = "htmx/_base_form_modal2.html"

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


class DeleteModalForm(ModalForm):
    button_title = "Delete title"
    header = "Delete header"
    submit_text = "Delete nao"
    explanation = "Delete explanation"
