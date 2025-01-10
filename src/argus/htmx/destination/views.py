from typing import Optional, Sequence
from django.shortcuts import render, get_object_or_404

from django.views.decorators.http import require_http_methods
from django.http import HttpResponse

from argus.notificationprofile.models import DestinationConfig, Media
from argus.notificationprofile.media import api_safely_get_medium_object
from argus.notificationprofile.media.base import NotificationMedium

from .forms import DestinationFormCreate, DestinationFormUpdate


@require_http_methods(["GET"])
def destination_list(request):
    return _render_destination_list(request)


@require_http_methods(["POST"])
def create_htmx(request) -> HttpResponse:
    form = DestinationFormCreate(request.POST or None, request=request)
    template = "htmx/destination/_content.html"
    if form.is_valid():
        form.save()
        return _render_destination_list(request, template=template)
    return _render_destination_list(request, create_form=form, template=template)


@require_http_methods(["POST"])
def delete_htmx(request, pk: int) -> HttpResponse:
    destination = get_object_or_404(request.user.destinations.all(), pk=pk)
    media = destination.media
    error_msg = None
    try:
        medium = api_safely_get_medium_object(destination.media.slug)
        medium.raise_if_not_deletable(destination)
    except NotificationMedium.NotDeletableError:
        error_msg = "That destination cannot be deleted."
    else:
        destination.delete()

    forms = _get_update_forms(request.user, media=media)

    context = {
        "error_msg": error_msg,
        "forms": forms,
        "media": media,
    }
    return render(request, "htmx/destination/_collapse_with_forms.html", context=context)


@require_http_methods(["POST"])
def update_htmx(request, pk: int) -> HttpResponse:
    destination = DestinationConfig.objects.get(pk=pk)
    form = DestinationFormUpdate(request.POST or None, instance=destination, request=request)
    template = "htmx/destination/_form_list.html"
    if form.is_valid():
        form.save()
        return _render_destination_list(request, template=template)

    update_forms = _get_update_forms(request.user)
    for index, update_form in enumerate(update_forms):
        if update_form.instance.pk == pk:
            update_forms[index] = form
            break
    return _render_destination_list(request, update_forms=update_forms, template=template)


def _render_destination_list(
    request,
    create_form: Optional[DestinationFormCreate] = None,
    update_forms: Optional[Sequence[DestinationFormUpdate]] = None,
    errors: Optional[Sequence[str]] = None,
    template: str = "htmx/destination/destination_list.html",
) -> HttpResponse:
    """Function to render the destinations page.

    :param create_form: this is used to display the form for creating a new destination
    with errors while retaining the user input. If you want a blank form, pass None.
    :param update_forms: list of update forms to display. Useful for rendering forms
    with error messages while retaining the user input.
    If this is None, the update forms will be generated from the user's destinations.
    :param errors: a list of error messages to display on the page. Will not be tied to
    any form fields."""

    if create_form is None:
        create_form = DestinationFormCreate()
    if update_forms is None:
        update_forms = _get_update_forms(request.user)
    if errors is None:
        errors = []
    grouped_forms = _group_update_forms_by_media(update_forms)
    context = {
        "create_form": create_form,
        "grouped_forms": grouped_forms,
        "errors": errors,
        "page_title": "Destinations",
    }
    return render(request, template, context=context)


def _get_update_forms(user, media: Media = None) -> list[DestinationFormUpdate]:
    """Get a list of update forms for the user's destinations.
    :param media: if provided, only return destinations for this media.
    """
    if media:
        destinations = user.destinations.filter(media=media)
    else:
        destinations = user.destinations.all()
    # Sort by oldest first
    destinations = destinations.order_by("pk")
    return [DestinationFormUpdate(instance=destination) for destination in destinations]


def _group_update_forms_by_media(
    destination_forms: Sequence[DestinationFormUpdate],
) -> dict[Media, list[DestinationFormUpdate]]:
    grouped_destinations = {}

    # Adding a media to the dict even if there are no destinations for it
    # is useful so that the template can render a section for that media
    for media in Media.objects.all():
        grouped_destinations[media] = []

    for form in destination_forms:
        grouped_destinations[form.instance.media].append(form)

    return grouped_destinations
