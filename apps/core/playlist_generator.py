import random
from itertools import islice
from typing import List

import requests
from django.conf import settings
from django.contrib.auth.models import User

from apps.user_profile.uri_converter import UriParser


def split_every(n, iterable):
    i = iter(iterable)
    piece = list(islice(i, n))
    while piece:
        yield piece
        piece = list(islice(i, n))


def make_playlists(videos):
    playlists = []

    for fifty_or_less_videos in split_every(50, videos):
        url = "http://www.youtube.com/watch_videos?video_ids=" + ",".join(fifty_or_less_videos)
        r = requests.get(url)
        playlists.append(r.url)

    return playlists


def generate_video_list(selected_users: List[User]):
    random.shuffle(selected_users)

    videos_lists = []

    for user in selected_users:
        videos = list(map(lambda user_track: UriParser(user_track.track_uri.uri).resource_id,
                          user.settings.get_enabled_tracks()))
        random.shuffle(videos)

        while len(videos) < settings.YOUTUBE_PLAYLIST_MIN_LENGTH:
            videos.append(settings.YOUTUBE_FILLER_VIDEO)

        videos_lists.append(videos)

    all_videos = []

    for nuplet in zip(*videos_lists):
        list_nuplet = list(nuplet)
        random.shuffle(list_nuplet)
        all_videos.extend(list_nuplet)

    return all_videos


delimiter = "&list="


def generate_youtube(selected_users: List[User]):
    all_videos = generate_video_list(selected_users)
    return map(lambda pl: pl[pl.find(delimiter) + len(delimiter):], make_playlists(all_videos))


def generate_pls(playlists):
    all_videos = generate_video_list(playlists)

    pls_list = ['[playlist]']

    pls_url_template = settings.PLS_URL_TEMPLATE.replace('[[', '{').replace(']]', '}')

    for i, video_id in enumerate(all_videos, 1):
        pls_list.append(f'File{i}={pls_url_template.format(video_id=video_id)}')

    pls_list.append(f'NumberOfEntries={len(all_videos)}')
    pls_list.append(f'Version=2')

    return '\n'.join(pls_list)
