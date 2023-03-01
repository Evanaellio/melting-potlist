from django.urls import reverse
from django.conf import settings
from requests_oauthlib import OAuth2Session


def make_session(request):
    return OAuth2Session(
        client_id=settings.DISCORD_CLIENT_ID,
        redirect_uri=request.build_absolute_uri(reverse("discord_login:callback")),
        scope=["identify", "guilds"],
    )
