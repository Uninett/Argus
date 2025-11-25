from typing import Literal
from django import template
from django.contrib.messages.storage.base import Message
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from .. import defaults

register = template.Library()


@register.filter
def tagvalues(incident, key) -> list:
    """Return values of tags with key KEY for incident INCIDENT

    There can be multiple tags with the same key
    """
    fallback = []
    if incident and key:
        tags = incident.deprecated_tags
        return [str(tag.value) for tag in tags if tag.key == key]
    return fallback


@register.filter
def is_acked_by(incident, group: str) -> bool:
    fallback = False
    if incident is not None and group:
        return incident.is_acked_by(group)
    return fallback


@register.filter
def pp_level(level: int) -> str:
    level = str(level)
    mapping = {
        "1": "Critical",
        "2": "High",
        "3": "Moderate",
        "4": "Low",
        "5": "Information",
    }
    fallback = mapping["5"]
    if level not in mapping:
        return fallback
    return mapping[level]


@register.filter
def fieldvalue(form, fieldname):
    fallback = ""
    if form is not None:
        return form[fieldname].value() or fallback
    return fallback


@register.filter
def get_form_field(form, fieldname):
    fallback = None
    if form is not None:
        return form[fieldname] or fallback
    return fallback


@register.filter
def dictvalue(dict_, key, default=None):
    if dict_:
        return dict_.get(key, default)
    return default


@register.filter
def autoclose_time(message: Message):
    candidates = getattr(
        settings,
        "NOTIFICATION_TOAST_AUTOCLOSE_SECONDS",
        defaults.NOTIFICATION_TOAST_AUTOCLOSE_SECONDS,
    )
    tags = set(message.tags.split()) & set(candidates.keys())
    if not tags:
        return -1
    return min(candidates[tag] for tag in tags)


@register.filter
def update_interval_string(value: int | Literal["never"]):
    if value == "never":
        return "Never"
    return f"{value}s"


@register.filter
def is_valid_url(value: str) -> bool:
    """Returns True if the given string is a valid URL, False otherwise."""
    url_validator = URLValidator()
    try:
        url_validator(value)
        return True
    except ValidationError:
        return False
