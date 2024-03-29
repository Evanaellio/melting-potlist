import json
import logging
from urllib.parse import quote

import yt_dlp
from django.contrib.auth.models import User
from django.core.exceptions import BadRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import parsers, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.serializers import DynamicPlaylistSerializer
from apps.user_profile.models import DynamicPlaylist, DynamicPlaylistUser, UserTrack
from apps.user_profile.uri_converter import UriParser

YTDL_OPTS = {
    "ignoreerrors": True,
    "quiet": True,
}

logger = logging.getLogger(__name__)


def is_valid_video_format(song_format):
    if not song_format.get("fps", None):
        return False

    try:
        return song_format["fragments"][0]["path"].startswith("range")
    except (KeyError, IndexError):
        return True


def fetch_media(media_url):
    with yt_dlp.YoutubeDL(YTDL_OPTS) as ydl:
        media = ydl.extract_info(media_url, download=False, process=False)

    if not media:
        return None

    duration = int(media["duration"])
    title = media["title"]
    artist = media["channel"]

    song_formats = list(media["formats"])

    audio_formats = list(filter(lambda fmt: fmt.get("audio_channels", None) and not fmt.get("fps", None), song_formats))

    # Get best audio format (largest filesize)
    audio = max(audio_formats, key=lambda fmt: fmt["filesize"])

    video_formats = list(filter(is_valid_video_format, song_formats))

    # Get video closest to 1080p
    video = min(video_formats, key=lambda fmt: abs(fmt["width"] - 1080))

    return {
        "audio": audio["url"] if "manifest_url" not in audio else audio["fragment_base_url"],
        "video": video["url"] if "manifest_url" not in video else video["fragment_base_url"],
        "title": title,
        "artist": artist,
        "duration": duration,
        "url": media_url,
        "subtitles_url": f"{reverse('core:subtitles')}?title={quote(title)}&duration={duration}",
    }


class DynamicPlaylistUsers(APIView):
    parser_classes = (parsers.JSONParser,)

    def patch(self, request, playlist_id, user_id, format=None):
        dynamic_playlist = get_object_or_404(DynamicPlaylist, id=playlist_id)

        # Check rights to modify playlist
        playlist_author = DynamicPlaylistUser.objects.get(dynamic_playlist=dynamic_playlist, is_author=True).user
        if playlist_author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        user_to_update, user_created = DynamicPlaylistUser.objects.get_or_create(
            dynamic_playlist=dynamic_playlist,
            user=User.objects.get(discord__id=user_id),
        )

        user_to_update.is_active = request.data["is_active"]
        user_to_update.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class PersistAndNext(APIView):
    def post(self, request, playlist_id, format=None):
        dynamic_playlist = get_object_or_404(DynamicPlaylist, id=playlist_id)

        # Check rights to modify playlist
        playlist_author = DynamicPlaylistUser.objects.get(dynamic_playlist=dynamic_playlist, is_author=True).user
        if playlist_author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if "trackId" in request.data and "userId" in request.data:
            dynamic_playlist.persist_track_and_user(request.data["trackId"], request.data["userId"])

        for i in range(5):
            next_user_track: UserTrack = dynamic_playlist.find_next_track()
            if not next_user_track:
                raise BadRequest("No active user in playlist")
            uri_parser = UriParser(next_user_track.track_uri.uri)
            if response_content := fetch_media(uri_parser.url):
                response_content["track_id"] = next_user_track.track_uri.track.id
                response_content["user_id"] = next_user_track.user_playlist.user.id
                response_content["thumbnail"] = uri_parser.thumbnail(high_quality=True)
                return Response(response_content)
            else:
                next_user_track.track_uri.unavailable = True
                next_user_track.track_uri.save()
                logger.warning(
                    "Tagged TrackUri '%s' as unavailable because it couldn't be fetched",
                    next_user_track.track_uri.uri,
                )

        raise Exception("Couldn't fetch any valid user track after 5 tries")


class Media(APIView):
    def get(self, request, media_uri, format=None):
        media_url = UriParser(media_uri).url
        response_content = fetch_media(media_url)

        if response_content:
            return Response(response_content)

        raise Exception("Couldn't fetch specified media")


class DynamicPlaylistViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows dynamic playlists to be created or viewed
    """

    queryset = DynamicPlaylist.objects.all()
    serializer_class = DynamicPlaylistSerializer
    permission_classes = [permissions.IsAuthenticated]
