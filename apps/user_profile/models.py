import datetime
import random
from collections import defaultdict
from typing import List, Optional

import django
import pytz
from annoying.fields import AutoOneToOneField
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.utils import timezone

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
    unavailable = models.BooleanField(default=False)


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
        return list(UserTrack.objects.filter(user_playlist__in=enabled_playlists,
                                             track_uri__deleted=False,
                                             track_uri__unavailable=False))


def compute_weight_from_track_stats(track_statistics: List[UserTrackListenStats], active_users_count,
                                    has_user_warmed_up) -> float:
    # Merge all stats to aggregate a single listen count and date for each tuple (user, track_uri)
    merged_stats = defaultdict(
        lambda: {"date_last_listened": datetime.datetime.min.replace(tzinfo=pytz.UTC), "listen_count": 0})
    for track_stat in track_statistics:
        key = (track_stat.user_track.user_playlist.user.id, track_stat.user_track.track_uri.uri)
        merged_stats[key]["listen_count"] += track_stat.listen_count
        merged_stats[key]["date_last_listened"] = max(merged_stats[key]["date_last_listened"],
                                                      track_stat.date_last_listened)

    now = django.utils.timezone.now()
    weight = 1.0

    # Increase weight for each user that never listened to the track, but only after one warmup song from this user
    if has_user_warmed_up:
        for i in range(active_users_count - len(track_statistics)):
            weight += 5

    for merged_stat in merged_stats.values():
        delta = now - merged_stat["date_last_listened"]
        total_hours = delta.days * 24 + (delta.seconds / 3600)

        if delta.days >= 1:
            weight += (min(delta.days, 30) / 30) * 3
        elif total_hours <= 8:
            weight *= 0.5

    return weight


class DynamicPlaylist(models.Model):
    date_generated = models.DateTimeField(default=timezone.now)
    tracks = models.ManyToManyField(UserTrack, related_name='dynamic_playlists', through="DynamicPlaylistTrack")
    groups = models.ManyToManyField(DiscordGuild, related_name='dynamic_playlists')
    users = models.ManyToManyField(User, related_name='dynamic_playlists', through="DynamicPlaylistUser")
    title = models.TextField(default="Unnamed dynamic playlist")

    def persist_track(self, track_id_to_persist):
        is_group_mode = self.groups.exists()
        playlist_author = self.dynamic_playlist_users.get(is_author=True)
        active_users = list(self.dynamic_playlist_users.filter(is_active=True))

        persisted_track = UserTrack.objects.get(id=track_id_to_persist)

        # Update (or create) listening stats for active users (in group mode) or playlist author (in solo mode)
        for listening_user in (active_users if is_group_mode else [playlist_author]):
            listen_stats, listen_stats_created = UserTrackListenStats.objects.get_or_create(
                listener=listening_user.user,
                user_track=persisted_track
            )

            if not listen_stats_created:
                listen_stats.listen_count += 1
                listen_stats.date_last_listened = django.utils.timezone.now()
                listen_stats.save()

        # Save track to dynamic playlist's list of tracks
        DynamicPlaylistTrack.objects.create(
            dynamic_playlist=self,
            track=persisted_track
        )

        # Mark the user that provided the persisted track as played in current rotation
        persisted_track_user: DynamicPlaylistUser = self.dynamic_playlist_users.get(
            user=persisted_track.user_playlist.user)
        persisted_track_user.played_in_rotation = True
        persisted_track_user.save()

    def find_next_track(self) -> Optional[UserTrack]:
        is_group_mode = self.groups.exists()
        playlist_author = self.dynamic_playlist_users.get(is_author=True)
        active_users = list(self.dynamic_playlist_users.filter(is_active=True))
        users_still_in_rotation = list(filter(lambda user: not user.played_in_rotation, active_users))

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
        all_tracks: List[UserTrack] = chosen_user.user.settings.get_enabled_tracks()
        all_track_uris = list(map(lambda track: track.track_uri.uri, all_tracks))

        has_user_warmed_up = self.tracks.filter(user_playlist__user=chosen_user.user).exists()

        if is_group_mode:
            users_listening = list(map(lambda dyn_playlist_user: dyn_playlist_user.user, active_users))
        else:
            users_listening = [playlist_author.user]

        statistics = list(UserTrackListenStats.objects.filter(user_track__track_uri__uri__in=all_track_uris,
                                                              listener__in=users_listening))

        weights = []
        for user_track_uri in all_track_uris:
            filtered_stats = list(filter(lambda stat: stat.user_track.track_uri.uri == user_track_uri, statistics))
            weights.append(compute_weight_from_track_stats(filtered_stats, len(users_listening), has_user_warmed_up))

        return random.choices(all_tracks, k=1, weights=weights)[0]


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
