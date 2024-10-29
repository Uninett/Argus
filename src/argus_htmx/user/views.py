from django.shortcuts import render


def user_settings(request):
    """Renders the main settings page for a user"""
    context = {"page_title": "User settings"}
    return render(request, "htmx/user/settings.html", context=context)
