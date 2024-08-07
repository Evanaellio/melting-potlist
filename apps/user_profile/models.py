import datetime
import random
from typing import List, Optional

import django
from annoying.fields import AutoOneToOneField
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.utils import timezone

from apps.discord_login.models import DiscordGuild

VERY_LOW_WEIGHT = 0.0000001


class Track(models.Model):
    title = models.TextField()
    artist = models.TextField(blank=True)
    album = models.TextField(blank=True)
    duration = models.DurationField()


class TrackUri(models.Model):
    uri = models.TextField(primary_key=True)
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name="uris", null=True)
    deleted = models.BooleanField(default=False)
    unavailable = models.BooleanField(default=False)


class UserPlaylist(models.Model):
    uri = models.TextField()
    title = models.TextField(default="Unknown playlist")
    enabled = models.BooleanField(default=True)
    last_synchronized = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="playlists")
    tracks = models.ManyToManyField(TrackUri, through="UserTrack", related_name="user_playlists")

    class Meta:
        constraints = [
            UniqueConstraint(fields=["user", "uri"], name="unique_user_uri"),
        ]

    def synchronize(self):
        if self.uri.startswith("youtube:"):
            # Lazy import to avoid circular dependency issues
            import apps.user_profile.youtube_playlist_extractor as youtube_extractor

            youtube_extractor.extract_tracks(self)

            self.last_synchronized = timezone.now()
            self.save()
        else:
            raise ValidationError(f"No playlist extractor available for URI: {self.uri}")


class UserTrack(models.Model):
    track_uri = models.ForeignKey(TrackUri, on_delete=models.CASCADE, related_name="user_tracks")
    user_playlist = models.ForeignKey(UserPlaylist, on_delete=models.CASCADE, related_name="user_tracks")
    date_added = models.DateTimeField()

    class Meta:
        constraints = [
            UniqueConstraint(fields=["track_uri", "user_playlist"], name="unique_track_uri_user_playlist"),
        ]


class TrackListenStats(models.Model):
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name="track_listen_stats")
    listener = models.ForeignKey(User, on_delete=models.CASCADE, related_name="track_listen_stats")
    date_last_listened = models.DateTimeField(default=timezone.now)
    listen_count = models.IntegerField(default=1)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["track", "listener"], name="unique_track_listener"),
        ]


class UserSettings(models.Model):
    user = AutoOneToOneField(User, primary_key=True, on_delete=models.CASCADE, related_name="settings")

    def get_enabled_tracks(self) -> List[UserTrack]:
        enabled_playlists = self.user.playlists.filter(enabled=True)
        return list(
            UserTrack.objects.filter(
                user_playlist__in=enabled_playlists, track_uri__deleted=False, track_uri__unavailable=False
            )
        )


def compute_weight_from_track_stats(
    track_statistics: List[TrackListenStats], active_users_count, has_user_warmed_up
) -> float:
    now = django.utils.timezone.now()
    weight = 1.0

    # Increase weight for each user that never listened to the track, but only after one warmup song from this user
    if has_user_warmed_up:
        for i in range(active_users_count - len(track_statistics)):
            weight += 6

    listened_recently_count = 0

    for stat in track_statistics:
        delta = now - stat.date_last_listened
        total_hours = delta.days * 24 + (delta.seconds / 3600)

        if delta.days >= 1:
            weight += (min(delta.days, 60) / 60) * 3
        elif total_hours <= 8:
            listened_recently_count += 1

    return weight if not listened_recently_count else VERY_LOW_WEIGHT


class DynamicPlaylist(models.Model):
    date_generated = models.DateTimeField(default=timezone.now)
    tracks = models.ManyToManyField(Track, related_name="dynamic_playlists", through="DynamicPlaylistTrack")
    groups = models.ManyToManyField(DiscordGuild, related_name="dynamic_playlists")
    users = models.ManyToManyField(User, related_name="dynamic_playlists", through="DynamicPlaylistUser")
    title = models.TextField(default="Unnamed dynamic playlist")
    is_group_mode = models.BooleanField(default=True)

    def persist_track_and_user(self, track_id, user_id):
        active_users = list(self.dynamic_playlist_users.filter(is_active=True))

        persisted_track = Track.objects.get(id=track_id)
        persisted_user = User.objects.get(id=user_id)

        # Update (or create) listening stats for active users (only in group mode)
        if self.is_group_mode:
            for listening_user in active_users:
                listen_stats, listen_stats_created = TrackListenStats.objects.get_or_create(
                    listener=listening_user.user, track=persisted_track
                )

                if not listen_stats_created:
                    listen_stats.listen_count += 1
                    listen_stats.date_last_listened = django.utils.timezone.now()
                    listen_stats.save()

            # Save track to dynamic playlist's list of tracks (only in group mode)
            DynamicPlaylistTrack.objects.create(dynamic_playlist=self, track=persisted_track, user=persisted_user)

        # Mark the user that provided the persisted track as played in current rotation
        persisted_playlist_user: DynamicPlaylistUser = self.dynamic_playlist_users.get(user=persisted_user)
        persisted_playlist_user.played_in_rotation = True
        persisted_playlist_user.save()

    def find_next_track(self) -> Optional[UserTrack]:
        playlist_author = self.dynamic_playlist_users.get(is_author=True)
        active_users = list(self.dynamic_playlist_users.filter(is_active=True))
        users_still_in_rotation = list(filter(lambda active_user: not active_user.played_in_rotation, active_users))

        if not active_users:
            return None

        # Start a new rotation if all users have finished the current rotation
        if not users_still_in_rotation:
            # Don't reset rotation when user is alone
            if len(active_users) > 1:
                for user in active_users:
                    user.played_in_rotation = False
                    user.save()
            users_still_in_rotation = active_users

        chosen_user = random.choice(users_still_in_rotation)

        # Synchronize each chosen user's playlist that have last been synchronized more than an hour ago
        if self.is_group_mode:
            for enabled_playlist in chosen_user.user.playlists.filter(enabled=True):
                if timezone.now() - enabled_playlist.last_synchronized > datetime.timedelta(hours=1):
                    enabled_playlist.synchronize()

        all_user_tracks: List[UserTrack] = chosen_user.user.settings.get_enabled_tracks()
        all_tracks = list(map(lambda user_track: user_track.track_uri.track, all_user_tracks))

        has_user_warmed_up = self.dynamic_playlist_tracks.filter(user=chosen_user.user).exists()

        if self.is_group_mode:
            users_listening = list(map(lambda dyn_playlist_user: dyn_playlist_user.user, active_users))
        else:
            users_listening = []  # Tracking is disabled in solo mode for now

        statistics = list(TrackListenStats.objects.filter(track__in=all_tracks, listener__in=users_listening))

        weights = []
        for track in all_tracks:
            filtered_stats = list(filter(lambda stat: stat.track == track, statistics))
            weights.append(compute_weight_from_track_stats(filtered_stats, len(users_listening), has_user_warmed_up))

        return random.choices(all_user_tracks, k=1, weights=weights)[0]


class DynamicPlaylistUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dynamic_playlist = models.ForeignKey(
        DynamicPlaylist, on_delete=models.CASCADE, related_name="dynamic_playlist_users"
    )
    is_author = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    played_in_rotation = models.BooleanField(default=False)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["user", "dynamic_playlist"], name="unique_user_dynamic_playlist"),
        ]


class DynamicPlaylistTrack(models.Model):
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, null=True)
    dynamic_playlist = models.ForeignKey(
        DynamicPlaylist, on_delete=models.CASCADE, related_name="dynamic_playlist_tracks"
    )
    played = models.DateTimeField(default=django.utils.timezone.now)
