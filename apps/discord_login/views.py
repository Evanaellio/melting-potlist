import django.contrib.auth
from django.conf import settings
from django.shortcuts import redirect
from .oauth import make_session


def login(request):
    oauth = make_session(request)
    authorization_url, state = oauth.authorization_url('https://discordapp.com/api/oauth2/authorize')
    return redirect(authorization_url)


def callback(request):
    code = request.GET.get('code')
    user = django.contrib.auth.authenticate(request, oauth_code=code)
    django.contrib.auth.login(request, user)
    return redirect(settings.LOGIN_REDIRECT_URL)


def logout(request):
    django.contrib.auth.logout(request)
    return redirect(settings.LOGOUT_REDIRECT_URL)
