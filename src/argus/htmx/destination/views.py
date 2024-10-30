from typing import Optional, Sequence
from django.shortcuts import render, get_object_or_404

from django.views.decorators.http import require_http_methods
from django.http import HttpResponse

from argus.notificationprofile.media import api_safely_get_medium_object
from argus.notificationprofile.media.base import NotificationMedium

from .forms import DestinationFormCreate


@require_http_methods(["GET", "POST"])
def destination_list(request):
    if request.method == "GET":
        return _render_destination_list(request)
    elif request.method == "POST":
        return destination_create(request)


def destination_create(request) -> HttpResponse:
    form = DestinationFormCreate(request.POST or None, request=request)
    if form.is_valid():
        form.save()
        return _render_destination_list(request)
    return _render_destination_list(request, create_form=form)


@require_http_methods(["POST"])
def destination_delete(request, pk: int) -> HttpResponse:
    destination = get_object_or_404(request.user.destinations.all(), pk=pk)

    try:
        medium = api_safely_get_medium_object(destination.media.slug)
        medium.raise_if_not_deletable(destination)
    except NotificationMedium.NotDeletableError:
        error_msg = "This destination cannot be deleted."
        return _render_destination_list(request, errors=[error_msg])
    else:
        destination.delete()
        return _render_destination_list(request)


def _render_destination_list(
    request,
    create_form: Optional[DestinationFormCreate] = None,
    errors: Optional[Sequence[str]] = None,
) -> HttpResponse:
    """Function to render the destinations page.

    :param create_form: this is used to display the form for creating a new destination
    with errors while retaining the user input. If you want a blank form, pass None.
    :param errors: a list of error messages to display on the page."""
    if create_form is None:
        create_form = DestinationFormCreate()
    if errors is None:
        errors = []
    context = {
        "create_form": create_form,
        errors: errors,
    }
    return render(request, "htmx/destination/destination_list.html", context=context)
