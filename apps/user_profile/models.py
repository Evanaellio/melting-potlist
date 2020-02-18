from annoying.fields import AutoOneToOneField
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from urllib.parse import urlparse, parse_qs


class UserSettings(models.Model):
    user = AutoOneToOneField(User, primary_key=True, on_delete=models.CASCADE, related_name='settings')
    core_playlist_url = models.URLField(blank=True)

    def clean(self):
        # Only allow Youtube playlist URL for core playlist
        parsed_url = urlparse(self.core_playlist_url)
        parsed_query = parse_qs(parsed_url.query)

        if 'youtube.com' not in parsed_url.netloc or 'list' not in parsed_query:
            raise ValidationError({'core_playlist_url': 'Enter a valid Youtube playlist URL'})
