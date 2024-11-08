from django.http import HttpResponse
from django.template import Template, RequestContext
from django.urls import path


def placeholder(request):
    template = Template(
        """{% extends "htmx/base.html" %}
        {% block main %}
        <h1>NOTIFICATION PROFILES PLACEHOLDER</h1>
        {% endblock main %}
        """
    )
    context = RequestContext(request)
    return HttpResponse(template.render(context))


app_name = "htmx"
urlpatterns = [
    path("", placeholder, name="notificationprofile-placeholder"),
]
