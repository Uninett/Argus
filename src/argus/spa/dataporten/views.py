from django.conf import settings
from django.shortcuts import redirect

from rest_framework.authtoken.models import Token
from social_django import views as social_views


def login_wrapper(request, backend, *args, **kwargs):
    # Needs to be called to fetch the user's Feide data (available through `social_auth`)
    _response = social_views.complete(request, backend, *args, **kwargs)

    user = request.user
    data = user.social_auth.first().extra_data

    if not user.get_full_name():
        # Update the full name of the user
        user.first_name = " ".join(data["fullname"].split()[:-1])
        user.last_name = data["fullname"].split()[-1]

        user.save()

    token, _created = Token.objects.get_or_create(user=user)
    response = redirect(settings.FRONTEND_URL, permanent=True)
    response.set_cookie(settings.ARGUS_TOKEN_COOKIE_NAME, token.key, domain=settings.COOKIE_DOMAIN)
    return response
