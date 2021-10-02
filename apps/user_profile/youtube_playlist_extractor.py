import re
from datetime import timedelta

from django.utils import timezone

from apps.user_profile.models import UserPlaylist, Track, TrackUri, UserTrack
from .uri_converter import UriParser

import yt_dlp

YTDL_OPTS = {
    'ignoreerrors': True,
    'quiet': True,
}


def make_track_uri(video):
    track_uri, track_uri_created = TrackUri.objects.get_or_create(
        uri=f'youtube:video:{video["id"]}',
    )

    # Videos that are private or deleted appear without an uploader
    track_uri.deleted = not video["uploader"]

    if not track_uri.deleted and not track_uri.track:
        artist_without_topic = re.sub(' - [Tt]opic$', '', video['uploader'])

        track_uri.track = Track.objects.create(
            title=video['title'],
            artist=artist_without_topic,
            duration=timedelta(seconds=int(video['duration'])),
        )

    track_uri.save()

    return track_uri


def extract_tracks(user_playlist: UserPlaylist) -> UserPlaylist:
    playlist_url = UriParser(user_playlist.uri).url

    with yt_dlp.YoutubeDL(YTDL_OPTS) as ytdl:
        playlist_infos = ytdl.extract_info(playlist_url, download=False, process=False)

    all_track_uris = []

    for video in playlist_infos['entries']:
        track_uri = make_track_uri(video)
        user_track, user_track_created = UserTrack.objects.get_or_create(
            track_uri=track_uri,
            user_playlist=user_playlist,
            defaults={'date_added': timezone.now()},
        )
        all_track_uris.append(track_uri)

    # Delete records that are missing from the current version of the playlist
    UserTrack.objects.filter(user_playlist=user_playlist).exclude(track_uri__in=all_track_uris).delete()

    user_playlist.title = playlist_infos['title']

    return user_playlist
