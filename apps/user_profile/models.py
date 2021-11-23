from typing import List

import django
from annoying.fields import AutoOneToOneField
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from django.db.models.constraints import UniqueConstraint

from apps.discord_login.models import DiscordGuild


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
    listeners = models.ManyToManyField(User, through="UserTrackListenStats", related_name='listened_tracks')
    date_added = models.DateTimeField()

    class Meta:
        constraints = [
            UniqueConstraint(fields=['track_uri', 'user_playlist'], name='unique_track_uri_user_playlist'),
        ]


class UserTrackListenStats(models.Model):
    user_track = models.ForeignKey(UserTrack, on_delete=models.CASCADE, related_name='user_track_listen_stats')
    listener = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_track_listen_stats')
    date_last_listened = models.DateTimeField(default=timezone.now)
    listen_count = models.IntegerField(default=1)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['user_track', 'listener'], name='unique_user_track_listener'),
        ]


class UserSettings(models.Model):
    user = AutoOneToOneField(User, primary_key=True, on_delete=models.CASCADE, related_name='settings')

    def get_enabled_tracks(self) -> List[UserTrack]:
        enabled_playlists = self.user.playlists.filter(enabled=True)
        return list(UserTrack.objects.filter(user_playlist__in=enabled_playlists, track_uri__deleted=False))


class DynamicPlaylist(models.Model):
    date_generated = models.DateTimeField(default=timezone.now)
    tracks = models.ManyToManyField(UserTrack, related_name='dynamic_playlists', through="DynamicPlaylistTrack")
    groups = models.ManyToManyField(DiscordGuild, related_name='dynamic_playlists')
    users = models.ManyToManyField(User, related_name='dynamic_playlists', through="DynamicPlaylistUser")
    title = models.TextField(default="Unnamed dynamic playlist")


class DynamicPlaylistUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dynamic_playlist = models.ForeignKey(DynamicPlaylist, on_delete=models.CASCADE,
                                         related_name='dynamic_playlist_users')
    is_author = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    played_in_rotation = models.BooleanField(default=False)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['user', 'dynamic_playlist'], name='unique_user_dynamic_playlist'),
        ]


class DynamicPlaylistTrack(models.Model):
    track = models.ForeignKey(UserTrack, on_delete=models.CASCADE)
    dynamic_playlist = models.ForeignKey(DynamicPlaylist, on_delete=models.CASCADE,
                                         related_name='dynamic_playlist_tracks')
    played = models.DateTimeField(default=django.utils.timezone.now)
