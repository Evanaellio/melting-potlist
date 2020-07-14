import random
from itertools import islice

import requests
from collections import Counter

from googleapiclient.discovery import build

from django.conf import settings


def fetch_all_youtube_videos(playlist_id):
    """
    Fetches a playlist of videos from youtube
    We splice the results together in no particular order

    Parameters:
        parm1 - (string) playlistId
    Returns:
        playListItem Dict
    """
    youtube = build(serviceName="youtube", version="v3", developerKey=settings.YOUTUBE_DEVELOPER_KEY)

    res = youtube.playlistItems().list(
        part="snippet",
        playlistId=playlist_id,
        maxResults="50"
    ).execute()

    next_page_token = res.get('nextPageToken')
    while 'nextPageToken' in res:
        nextPage = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults="50",
            pageToken=next_page_token
        ).execute()
        res['items'] = res['items'] + nextPage['items']

        if 'nextPageToken' not in nextPage:
            res.pop('nextPageToken', None)
        else:
            next_page_token = nextPage['nextPageToken']

    return res


def fetch_video_ids(playlist_id):
    items = fetch_all_youtube_videos(playlist_id)["items"]
    return list(map(lambda item: item["snippet"]["resourceId"]["videoId"], items))


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
        print(url)
        r = requests.get(url)
        playlists.append(r.url)

    return playlists


def generate_video_list(chosen_playlists, listened_count):
    random.shuffle(chosen_playlists)

    videos_lists = []

    for playlist_id in chosen_playlists:
        videos = fetch_video_ids(playlist_id)[:10]
        random.shuffle(videos)
        videos.sort(key=lambda v: listened_count[v])

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


def generate_youtube(playlists):
    count = Counter()

    all_videos = generate_video_list(playlists, count)
    return map(lambda pl: pl[pl.find(delimiter) + len(delimiter):], make_playlists(all_videos))


def generate_pls(playlists):
    count = Counter()

    all_videos = generate_video_list(playlists, count)

    pls_list = ['[playlist]']

    pls_url_template = settings.PLS_URL_TEMPLATE.replace('[[', '{').replace(']]', '}')

    for i, video_id in enumerate(all_videos, 1):
        pls_list.append(f'File{i}={pls_url_template.format(video_id=video_id)}')

    pls_list.append(f'NumberOfEntries={len(all_videos)}')
    pls_list.append(f'Version=2')

    return '\n'.join(pls_list)
