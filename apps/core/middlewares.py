from datetime import datetime
from django.utils import timezone

LAST_COOKIE_REFRESH = 'last_cookie_refresh'


class ExtendUserSession(object):
    """
    Extend authenticated user's sessions when they reach half of the SESSION_COOKIE_AGE
    """

    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def refresh_session_cookie(request):
        request.session.set_expiry(request.session.get_session_cookie_age())
        request.session[LAST_COOKIE_REFRESH] = timezone.now().isoformat()

    def __call__(self, request):
        response = self.get_response(request)

        # Only extend the session for authenticated users
        if request.user.is_authenticated:
            session_cookie_age = request.session.get_session_cookie_age()
            if LAST_COOKIE_REFRESH not in request.session:
                self.refresh_session_cookie(request)
            elif (timezone.now() - datetime.fromisoformat(request.session[LAST_COOKIE_REFRESH])).total_seconds() \
                    > session_cookie_age / 2:
                self.refresh_session_cookie(request)

        return response
