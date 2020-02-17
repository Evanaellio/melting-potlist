from annoying.fields import AutoOneToOneField
from django.contrib.auth.models import User
from django.db import models


class UserSettings(models.Model):
    user = AutoOneToOneField(User, primary_key=True, on_delete=models.CASCADE, related_name='settings')
    core_playlist_url = models.URLField(blank=True)
