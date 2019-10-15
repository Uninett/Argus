""" TODO: temporarily disabled until JSON parsing has been implemented for the new data model
import json
from datetime import MAXYEAR, date, datetime

from django.db.models.fields.related_descriptors import ForwardManyToOneDescriptor
from django.db.models.query_utils import DeferredAttribute
from django.utils import timezone

from .models import AlertHistory, AlertType, EventType, Subject, SubjectType


alert_fields = {
    'id':                 AlertHistory.alert_id,
    'on_maintenance':     AlertHistory.on_maintenance,
    'acknowledgement':    None,
    'event_history_url':  AlertHistory.event_history_url,
    'netbox_history_url': AlertHistory.netbox_history_url,
    'event_details_url':  AlertHistory.event_details_url,
    'device_groups':      None,
    'alert_type':         (AlertHistory.type,
                           AlertType,
                           {
                               'name':        AlertType.name,
                               'description': AlertType.description,
                           }),
    'event_type':         (AlertHistory.event_type,
                           EventType,
                           {
                               'id':          EventType.name,
                               'description': EventType.description,
                           }),
    'value':              AlertHistory.value,
    'severity':           AlertHistory.severity,
    'source':             AlertHistory.source,
    'device':             AlertHistory.device,
    'netbox':             AlertHistory.netbox,
    'start_time':         AlertHistory.start_time,
    'end_time':           AlertHistory.end_time,
}

subject_fields = {
    'subid':        Subject.subject_id,
    'subject':      Subject.name,
    'subject_url':  Subject.url,
    'subject_type': (Subject.type,
                     {
                         'name': SubjectType.name,
                     }),
}


# TODO: clean up this code:
def json_to_alert_hist(json_string):
    json_obj = json.loads(json_string)
    alert_hist = AlertHistory()

    # Extract subject fields from the JSON object
    subject_json_obj = {key: json_obj.pop(key) for key in subject_fields}
    subject_field_kwargs = {field.field_name: subject_json_obj[key] for key, field in subject_fields.items()
                            if type(field) is DeferredAttribute}
    subject_type, _created = SubjectType.objects.get_or_create(name=subject_json_obj['subject_type'])
    subject_field_kwargs['type'] = subject_type
    subject, _created = Subject.objects.get_or_create(**subject_field_kwargs)
    alert_hist.subject = subject

    # Parse the rest of the fields of the JSON object
    for key, value in json_obj.items():
        if key not in alert_fields:
            print(f"Missing field in the model for the key '{key}'!")
            continue

        field = alert_fields[key]
        if type(field) is DeferredAttribute:
            # TODO: move this logic to specific conversion classes for Text/CharFields
            if 'url' in field.field_name and value is None:
                value = ""
            setattr(alert_hist, field.field_name, value)
        elif type(field) is tuple:
            field, foreign_key_model, foreign_key_model_fields = field
            if type(field) is not ForwardManyToOneDescriptor:
                print(f"The type of the foreign key field for the key '{key}' is {type(field)} and not ForwardManyToOneDescriptor!")
                continue

            field_kwargs = {field.field_name: value[key] for key, field in foreign_key_model_fields.items()}
            obj, _created = foreign_key_model.objects.get_or_create(**field_kwargs)
            setattr(alert_hist, field.field.name, obj)
        elif field is None:
            continue

    # Fix timestamp format
    alert_hist.start_time = timezone.make_aware(datetime.fromisoformat(alert_hist.start_time))
    if alert_hist.end_time == 'infinity':
        alert_hist.end_time = date(MAXYEAR, 1, 1)  # TODO: other represenation..?
    else:
        alert_hist.end_time = timezone.make_aware(datetime.fromisoformat(alert_hist.end_time))

    return alert_hist
"""
