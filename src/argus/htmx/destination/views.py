from __future__ import annotations

from collections import namedtuple
import logging
from typing import Optional, TYPE_CHECKING, Tuple

from django.http import QueryDict
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_http_methods

from argus.notificationprofile.models import DestinationConfig, Media
from argus.notificationprofile.media import get_medium_object
from argus.notificationprofile.media.base import NotificationMedium, LabelForm

if TYPE_CHECKING:
    from django.forms import Form


LOG = logging.getLogger(__name__)
Forms = namedtuple("Forms", ["label_form", "settings_form"])


# not a view
def get_forms(request, media: str, instance: Optional[DestinationConfig] = None) -> Forms:
    """Get and bind the two forms necessary to change a destination

    - media is for selecting the right plugin
    - label_form is for all the common fields of a destination
    - settings_form is fetched from the destination plugin found via "media"
    - instance holds the pre-existing values if updating
    """
    prefix = "destinationform"
    medium = get_medium_object(media)

    if instance and instance.pk:
        prefix += f"-{instance.pk}-{media}"
        label_name = medium.get_label(instance)
        label_initial = {"label": label_name}
    else:
        prefix += f"-{media}"
        label_initial = {}

    data = None
    for key in request.POST:
        if key.startswith(prefix):
            data = request.POST
            break
    label_form = LabelForm(data=data, user=request.user, initial=label_initial, instance=instance, prefix=prefix)
    settings_form = medium.validate_settings(data, request.user, instance=instance, prefix=prefix)

    if data:
        label_form.is_valid()
    return Forms(label_form, settings_form)


# not a view
def save_forms(user, media: str, label_form: LabelForm, settings_form: Form) -> Tuple[DestinationConfig, bool]:
    """Save the contents of the two forms necessary to change a destination

    The two forms should first have been instantiated via ``get_forms``.

    - media is for linking up the right plugin on create
    - label_form is for all the common fields of a destination
    - settings_form is fetched from the destination plugin found via "media"

    if the forms are valid, return the (updated) DestinationConfig and a bool
    of whether the object was changed or not. If the forms were not valid,
    return (None, false)
    """
    changed = False
    obj = label_form.instance
    if obj.pk:
        # ensure that media type cannot be changed when updating a destination
        media = obj.media_id
    if label_form.has_changed() or settings_form.has_changed():
        changed = True
    else:
        return obj, changed
    if not (label_form.is_valid() and settings_form.is_valid()):
        obj = obj or None
        return obj, changed
    obj = label_form.save(commit=False)
    obj.user = user
    obj.media_id = media
    obj.settings = settings_form.cleaned_data
    obj.save()
    return obj, changed


@require_http_methods(["GET"])
def destination_list(request):
    return _render_destination_list(request)


@require_http_methods(["POST"])
def create_destination(request, media: str) -> HttpResponse:
    medium = get_medium_object(media)
    label_form, settings_form = get_forms(request, media)
    template = "htmx/destination/_content.html"
    context = {
        "label_form": label_form,
        "settings_form": settings_form,
        "media": media,
    }
    obj, changed = save_forms(request.user, media, label_form, settings_form)
    if changed:
        if obj:
            label = medium.get_label(obj)
            message = f'Created new {medium.MEDIA_NAME} destination "{label}"'
            messages.success(request, message)
            LOG.info(message)
        request.POST = QueryDict("")
        return _render_destination_list(request, context=context, template=template)
    error_msg = f"Could not create new {medium.MEDIA_NAME} destination"
    messages.warning(request, error_msg)
    LOG.warn(error_msg)
    return _render_destination_list(request, context=context, template=template)


@require_http_methods(["POST"])
def delete_destination(request, pk: int) -> HttpResponse:
    destination = get_object_or_404(request.user.destinations.all(), pk=pk)
    media = destination.media
    error_msg = None
    medium = get_medium_object(media.slug)
    destination_label = medium.get_label(destination)
    try:
        medium.raise_if_not_deletable(destination)
    except NotificationMedium.NotDeletableError as e:
        # template?
        error_msg = ", ".join(e.args)
        message = f'Failed to delete {medium.MEDIA_NAME} destination "{destination}": {error_msg}'
        messages.warning(request, message)
        LOG.warn(message)
    else:
        destination.delete()
        message = f'Deleted {medium.MEDIA_NAME} destination "{destination_label}"'
        messages.success(request, message)
        LOG.info(message)

    return redirect("htmx:destination-list")


@require_http_methods(["POST"])
def update_destination(request, pk: int, media: str) -> HttpResponse:
    medium = get_medium_object(media)
    template = "htmx/destination/_form_list.html"
    destination = get_object_or_404(request.user.destinations.all(), pk=pk)
    label = medium.get_label(destination)
    forms = get_forms(request, media, instance=destination)
    obj, changed = save_forms(request.user, media, *forms)
    if changed:
        if obj:
            label = medium.get_label(obj)
            message = f'Updated {medium.MEDIA_NAME} destination "{label}"'
            messages.success(request, message)
            LOG.info(message)
        request.POST = QueryDict("")
        return _render_destination_list(request, template=template)
    else:
        return _render_destination_list(request, template=template)
    error_msg = f'Could not update {medium.MEDIA_NAME} destination "{label}"'
    messages.warning(request, error_msg)
    LOG.warn(request, error_msg)
    all_forms = get_all_forms_grouped_by_media(request)
    update_forms = get_all_update_forms_for_media(request, media)
    for index, forms in enumerate(update_forms):
        if forms.label_form.instance.pk == pk:
            update_forms[index] = forms
            break
    all_forms[media] = update_forms
    context = {
        "forms": all_forms,
        "label_form": forms.label_form,
        "settings_form": forms.settings_form,
        "media": media,
    }
    return _render_destination_list(request, context=context, template=template)


def _render_destination_list(
    request,
    context: Optional[dict] = None,
    template: str = "htmx/destination/destination_list.html",
) -> HttpResponse:
    """Function to render the destinations page"""

    if not context:
        context = {}
    if "forms" not in context:
        context["forms"] = get_all_forms_grouped_by_media(request)
    context["page_title"] = "Destinations"
    return render(request, template, context=context)


def get_all_update_forms_for_media(request, media: str) -> list[Forms]:
    """Get a list of update forms for the user's destinations.
    :param media: Only return destinations for this media.
    """
    destinations = request.user.destinations.filter(media_id=media).order_by("pk")

    return [get_forms(request, media, instance=destination) for destination in destinations]


def get_all_forms_grouped_by_media(request):
    forms = {}
    for media in Media.objects.all():
        create_form = get_forms(request, media.slug)
        update_forms = get_all_update_forms_for_media(request, media.slug)
        forms[media] = {
            "create_form": create_form,
            "update_forms": update_forms,
        }
    return forms
