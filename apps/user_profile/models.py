from datetime import datetime
from typing import List

from annoying.fields import AutoOneToOneField
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from django.db.models.constraints import UniqueConstraint


class Track(models.Model):
    title = models.TextField()
    artist = models.TextField(blank=True)
    album = models.TextField(blank=True)
    duration = models.DurationField()


class TrackUri(models.Model):
    uri = models.TextField(primary_key=True)
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='uris', null=True)
    deleted = models.BooleanField(default=False)


class UserPlaylist(models.Model):
    uri = models.TextField()
    title = models.TextField(default="Unknown playlist")
    enabled = models.BooleanField(default=True)
    last_synchronized = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    tracks = models.ManyToManyField(TrackUri, through='UserTrack', related_name='user_playlists')

    class Meta:
        constraints = [
            UniqueConstraint(fields=['user', 'uri'], name='unique_user_uri'),
        ]

    def synchronize(self):
        if self.uri.startswith('youtube:'):

            # Lazy import to avoid circular dependency issues
            import apps.user_profile.youtube_playlist_extractor as youtube_extractor
            youtube_extractor.extract_tracks(self)

            self.last_synchronized = timezone.now()
            self.save()
        else:
            raise ValidationError(f"No playlist extractor available for URI: {self.uri}")


class UserTrack(models.Model):
    track_uri = models.ForeignKey(TrackUri, on_delete=models.CASCADE, related_name='user_tracks')
    user_playlist = models.ForeignKey(UserPlaylist, on_delete=models.CASCADE, related_name='user_tracks')
    date_added = models.DateTimeField()

    class Meta:
        constraints = [
            UniqueConstraint(fields=['track_uri', 'user_playlist'], name='unique_track_uri_user_playlist'),
        ]


class UserSettings(models.Model):
    user = AutoOneToOneField(User, primary_key=True, on_delete=models.CASCADE, related_name='settings')

    def get_enabled_tracks(self) -> List[UserTrack]:
        enabled_playlists = self.user.playlists.filter(enabled=True)
        return list(UserTrack.objects.filter(user_playlist__in=enabled_playlists, track_uri__deleted=False))
