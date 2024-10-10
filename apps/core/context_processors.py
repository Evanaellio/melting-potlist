from django.http import HttpRequest
from django.conf import settings
from .views import make_user


def discord_user(request: HttpRequest):
    context = {}

    if request.user.is_authenticated:
        context["discord_user"] = make_user(request.user.discord)

    return context
