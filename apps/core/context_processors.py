from django.http import HttpRequest
from .views import make_user


def user(request: HttpRequest):
    context = {}

    if request.user.is_authenticated:
        context['user'] = make_user(request.user.discord)

    return context
