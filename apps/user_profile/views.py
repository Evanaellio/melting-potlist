from datetime import datetime
import json
from typing import List
from urllib.parse import urlparse, parse_qs

from django.contrib.auth.decorators import login_required
from django.contrib.humanize.templatetags.humanize import naturaltime, naturalday
from django.core.exceptions import ValidationError
from django.forms import DurationField
from django.http.response import Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.duration import _get_duration_components

from .models import UserPlaylist, UserTrack
from .uri_converter import UriParser


def duration_to_str(duration: DurationField):
    days, hours, minutes, seconds, microseconds = _get_duration_components(duration)

    return '{:02d}:{:02d}'.format(minutes, seconds)


def make_playlist(user_playlist: UserPlaylist):
    valid_tracks = user_playlist.user_tracks.filter(track_uri__deleted=False)
    last_3_tracks: List[UserTrack] = list(valid_tracks.order_by('-date_added')[:3])

    return {
        'id': user_playlist.id,
        'title': user_playlist.title,
        'enabled': user_playlist.enabled,
        'url': UriParser(user_playlist.uri).url,
        'last_synchronized': naturaltime(user_playlist.last_synchronized),
        'last_track_added': naturaltime(last_3_tracks[0].date_added) if last_3_tracks else None,
        'recent_tracks': map(make_track, last_3_tracks)
    }


def make_track(user_track: UserTrack):
    track_uri = user_track.track_uri
    track_id = track_uri.uri.split(':')[2]
    uri_parser = UriParser(track_uri.uri)

    return {
        "title": track_uri.track.title if track_uri.track else "[DELETED]",
        "artist": track_uri.track.artist if track_uri.track else "[DELETED]",
        "id": track_id,
        "url": uri_parser.url,
        "thumbnail": uri_parser.thumbnail,
        "duration": duration_to_str(track_uri.track.duration) if track_uri.track else "0:00",
        "date_added_natural": naturalday(user_track.date_added),
        "date_added": datetime.timestamp(user_track.date_added),
        "deleted": track_uri.deleted,
        "unavailable": track_uri.unavailable,
    }


@login_required
def all_playlists(request):
    if request.POST:

        playlist_url = request.POST['playlistUrl']
        parsed_url = urlparse(playlist_url)
        parsed_query = parse_qs(parsed_url.query)

        uri = None

        if 'youtube.com' in parsed_url.netloc and 'list' in parsed_query:
            uri = f'youtube:playlist:{parsed_query["list"][0]}'

        if uri:
            user_playlist, user_playlist_created = UserPlaylist.objects.get_or_create(uri=uri, user=request.user)
        else:
            raise ValidationError(f"No playlist extractor available for URL: {playlist_url}")

        user_playlist.synchronize()

        return redirect(reverse('user_profile:single_playlist', kwargs={'playlist_id': user_playlist.id}))

    context = {
        'playlists': map(make_playlist, request.user.playlists.order_by("title"))
    }

    return render(request, 'user_profile/playlists.html', context=context)


@login_required
def delete_playlist(request, playlist_id):
    if request.POST:
        UserPlaylist.objects.get(user=request.user, id=playlist_id).delete()

    return redirect(reverse('user_profile:all_playlists'))


@login_required
def single_playlist(request, playlist_id):
    try:
        playlist = request.user.playlists.get(id=playlist_id)
    except UserPlaylist.DoesNotExist:
        raise Http404()

    valid_tracks = playlist.user_tracks.filter(track_uri__deleted=False)
    deleted_tracks = playlist.user_tracks.filter(track_uri__deleted=True)
    unavailable_tracks = playlist.user_tracks.filter(track_uri__unavailable=True)

    tracks = list(map(make_track, playlist.user_tracks.all()))

    context = {
        'playlist_id': playlist_id,
        'url': UriParser(playlist.uri).url,
        'videos': tracks,
        'title': playlist.title,
        'tracks_json': json.dumps(tracks),
        'track_count': valid_tracks.count(),
        'deleted_track_count': deleted_tracks.count(),
        'unavailable_track_count': unavailable_tracks.count(),
    }

    return render(request, 'user_profile/single_playlist.html', context=context)


@login_required
def synchronize_playlist(request, playlist_id):
    try:
        playlist = request.user.playlists.get(id=playlist_id)
    except UserPlaylist.DoesNotExist:
        raise Http404()

    playlist.synchronize()

    return redirect(reverse('user_profile:all_playlists'))


def toggle_playlist(request, playlist_id):
    try:
        playlist = request.user.playlists.get(id=playlist_id)
    except UserPlaylist.DoesNotExist:
        raise Http404()

    playlist.enabled = not playlist.enabled
    playlist.save()

    return redirect(reverse('user_profile:all_playlists'))
