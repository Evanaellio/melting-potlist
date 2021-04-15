import re
from datetime import timedelta

from django.utils import timezone

from apps.user_profile.models import UserPlaylist, Track, TrackUri, UserTrack
from .uri_converter import UriParser

import youtube_dl

YTDL_OPTS = {
    'ignoreerrors': True,
    'quiet': True,
}


def make_track_uri(video):
    track_uri, track_uri_created = TrackUri.objects.get_or_create(
        uri=f'youtube:video:{video["id"]}',
    )

    if not track_uri.track:
        artist_without_topic = re.sub(' - [Tt]opic$', '', video['uploader'])

        track_uri.track = Track.objects.create(
            title=video['title'],
            artist=artist_without_topic,
            duration=timedelta(seconds=int(video['duration'])),
        )

    # Reset deleted flag in case video was flagged as deleted because it was private but is now public again
    track_uri.deleted = False
    track_uri.save()

    return track_uri


def extract_tracks(user_playlist: UserPlaylist) -> UserPlaylist:
    playlist_url = UriParser(user_playlist.uri).url

    with youtube_dl.YoutubeDL(YTDL_OPTS) as ytdl:
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

    # Manage records that are missing from the current version of the playlist
    for missing_track in UserTrack.objects.filter(user_playlist=user_playlist).exclude(track_uri__in=all_track_uris):
        with youtube_dl.YoutubeDL(YTDL_OPTS) as ytdl:
            video_info = ytdl.extract_info(UriParser(missing_track.track_uri.uri).url, download=False, process=False)

        if not video_info:  # If the video was removed from Youtube
            missing_track.track_uri.deleted = True  # Flag as deleted but keep it in the user's playlist
            missing_track.track_uri.save()
        else:
            missing_track.delete()  # Delete from the user's playlist

    user_playlist.title = playlist_infos['title']

    return user_playlist
