from typing import Optional
from django.shortcuts import render

from django.views.decorators.http import require_http_methods
from django.http import HttpResponse

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


def _render_destination_list(request, create_form: Optional[DestinationFormCreate] = None) -> HttpResponse:
    """Function to render the destinations page.

    :param create_form: this is used to display the form for creating a new destination
    with errors while retaining the user input. If you want a blank form, pass None."""
    if create_form is None:
        create_form = DestinationFormCreate()
    context = {
        "create_form": create_form,
    }
    return render(request, "htmx/destination/destination_list.html", context=context)
