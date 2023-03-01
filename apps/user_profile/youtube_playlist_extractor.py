import re
from datetime import timedelta

import yt_dlp
from django.utils import timezone

from apps.user_profile.models import Track, TrackUri, UserPlaylist, UserTrack

from .uri_converter import UriParser

YTDL_OPTS = {
    "ignoreerrors": True,
    "quiet": True,
}


def make_track_uri(video):
    track_uri, track_uri_created = TrackUri.objects.get_or_create(
        uri=f'youtube:video:{video["id"]}',
    )

    # Videos that are private or deleted appear without a channel
    track_uri.deleted = not video["channel"]

    # Retry to fetch unavailable track info to check if it's still unavailable
    if track_uri.unavailable:
        with yt_dlp.YoutubeDL(YTDL_OPTS) as ytdl:
            track_uri.unavailable = not track_uri.deleted and not ytdl.extract_info(
                UriParser(track_uri.uri).url, download=False, process=False
            )

    if not track_uri.deleted and not track_uri.track:
        artist_without_topic = re.sub(" - [Tt]opic$", "", video["channel"])

        track_uri.track = Track.objects.create(
            title=video["title"],
            artist=artist_without_topic,
            duration=timedelta(seconds=int(video["duration"])),
        )

    track_uri.save()

    return track_uri


def extract_tracks(user_playlist: UserPlaylist) -> UserPlaylist:
    playlist_url = UriParser(user_playlist.uri).url

    with yt_dlp.YoutubeDL(YTDL_OPTS) as ytdl:
        playlist_infos = ytdl.extract_info(playlist_url, download=False, process=False)

    if not playlist_infos:
        user_playlist.title = "⚠️ Invalid or private playlist"
        user_playlist.enabled = False
        user_playlist.save()
        return user_playlist

    all_track_uris = []

    for video in playlist_infos["entries"]:
        track_uri = make_track_uri(video)
        user_track, user_track_created = UserTrack.objects.get_or_create(
            track_uri=track_uri,
            user_playlist=user_playlist,
            defaults={"date_added": timezone.now()},
        )
        all_track_uris.append(track_uri)

    # Delete records that are missing from the current version of the playlist
    UserTrack.objects.filter(user_playlist=user_playlist).exclude(track_uri__in=all_track_uris).delete()

    user_playlist.title = playlist_infos["title"]

    return user_playlist
