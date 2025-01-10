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
    try:
        medium = api_safely_get_medium_object(destination.media.slug)
        medium.raise_if_not_deletable(destination)
    except NotificationMedium.NotDeletableError:
        form = DestinationFormUpdate(instance=destination)
        context = {
            "update_error_msg": "This destination cannot be deleted.",
            "form": form,
        }
        return render(request, "htmx/destination/_update_and_delete_form.html", context=context)
    else:
        destination.delete()
        return HttpResponse()


@require_http_methods(["POST"])
def update_htmx(request, pk: int) -> HttpResponse:
    destination = DestinationConfig.objects.get(pk=pk)
    form = DestinationFormUpdate(request.POST or None, instance=destination, request=request)
    if form.is_valid():
        form.save()
    context = {"form": form, "update_error_msg": None}
    return render(request, "htmx/destination/_update_and_delete_form.html", context=context)


def _render_destination_list(
    request,
    create_form: Optional[DestinationFormCreate] = None,
    template: str = "htmx/destination/destination_list.html",
) -> HttpResponse:
    """Function to render the destinations page.

    :param create_form: this is used to display the form for creating a new destination
    with errors while retaining the user input. If you want a blank form, pass None."""

    if create_form is None:
        create_form = DestinationFormCreate()
    update_forms = _get_update_forms(request.user)
    grouped_forms = _group_update_forms_by_media(update_forms)
    context = {
        "create_form": create_form,
        "grouped_forms": grouped_forms,
    }
    return render(request, template, context=context)


def _get_update_forms(user) -> list[DestinationFormUpdate]:
    # Sort by oldest first
    destinations = user.destinations.all().order_by("pk")
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
