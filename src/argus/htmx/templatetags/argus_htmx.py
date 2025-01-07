from django import template
from django.contrib.messages.storage.base import Message
from django.conf import settings
from .. import defaults

register = template.Library()


@register.filter
def tagvalues(incident, key) -> list:
    """Return values of tags with key KEY for incident INCIDENT

    There can be multiple tags with the same key
    """
    tags = incident.deprecated_tags
    return [str(tag.value) for tag in tags if tag.key == key]


@register.filter
def is_acked_by(incident, group: str) -> bool:
    return incident.is_acked_by(group)


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
    if level not in mapping:
        return mapping["5"]
    return mapping[level]


@register.filter
def fieldvalue(form, fieldname):
    return form[fieldname].value() or ""


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
