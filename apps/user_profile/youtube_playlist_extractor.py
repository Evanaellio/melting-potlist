import json
import re
from datetime import timedelta

from django.utils import timezone

import requests

from apps.user_profile.models import UserPlaylist, Track, TrackUri, UserTrack
from .uri_converter import UriParser


def make_track_uri(video_renderer):
    track_uri, track_uri_created = TrackUri.objects.get_or_create(
        uri=f'youtube:video:{video_renderer["videoId"]}',
    )

    if 'no_thumbnail.jpg' in video_renderer['thumbnail']['thumbnails'][0]['url']:
        track_uri.deleted = True
    else:
        if not track_uri.track:
            artist_without_topic = re.sub(' - topic$', '', video_renderer['shortBylineText']['runs'][0]['text'])

            track_uri.track = Track.objects.create(
                title=video_renderer['title']['runs'][0]['text'],
                artist=artist_without_topic,
                duration=timedelta(seconds=int(video_renderer['lengthSeconds'])),
            )

    track_uri.save()

    return track_uri


def extract_tracks(user_playlist: UserPlaylist) -> UserPlaylist:
    playlist_url = UriParser(user_playlist.uri).url

    headers = {
        'x-youtube-client-name': "1",
        'x-youtube-client-version': "2.20200609.04.01"
    }

    response = requests.get(playlist_url, headers=headers)
    match = re.search(r'\s*window\["ytInitialData"\] = (.*);', response.text)

    parsed = json.loads(match.group(1))

    videolist_renderer = parsed["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0]["tabRenderer"]["content"] \
        ["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"][0]["playlistVideoListRenderer"]

    video_renderers = []

    video_renderers.extend(map(lambda item: item["playlistVideoRenderer"], videolist_renderer["contents"]))

    while "continuations" in videolist_renderer:
        continuation = videolist_renderer["continuations"][0]["nextContinuationData"]["continuation"]

        continue_response = requests.get(f"https://www.youtube.com/browse_ajax?continuation={continuation}",
                                         headers=headers).json()

        videolist_renderer = continue_response[1]["response"]["continuationContents"]["playlistVideoListContinuation"]

        video_renderers.extend(map(lambda item: item["playlistVideoRenderer"], videolist_renderer["contents"]))

    all_track_uris = []

    for renderer in video_renderers:
        track_uri = make_track_uri(renderer)
        user_track, user_track_created = UserTrack.objects.get_or_create(
            track_uri=track_uri,
            user_playlist=user_playlist,
            defaults={'date_added': timezone.now()},
        )
        all_track_uris.append(track_uri)

    # Delete records that previously belonged to the playlist but have since been removed
    UserTrack.objects.filter(user_playlist=user_playlist).exclude(track_uri__in=all_track_uris).delete()

    user_playlist.title = parsed['metadata']['playlistMetadataRenderer']['title']

    return user_playlist
