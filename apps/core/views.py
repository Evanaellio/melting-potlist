import datetime
import json
import operator
from dataclasses import dataclass
from typing import List

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from apps.discord_login.models import DiscordGuild, DiscordUser
from ..user_profile.models import DynamicPlaylist


@dataclass
class Alert:
    message: str
    link: str = None
    css_class: str = "alert-primary"


def home(request):
    context = {}

    if request.user.is_authenticated:
        alerts = []
        if len(request.user.settings.get_enabled_tracks()) == 0:
            alerts.append(
                Alert(message="⚠ No tracks available for your profile, please review your playlists configuration",
                      link=reverse('user_profile:all_playlists'),
                      css_class='alert-warning'))

        for enabled_playlist in request.user.playlists.filter(enabled=True):
            deleted_or_unavailable_tracks_count = enabled_playlist.user_tracks.filter(
                Q(track_uri__deleted=True) | Q(track_uri__unavailable=True)).count()

            if deleted_or_unavailable_tracks_count:
                alerts.append(
                    Alert(
                        message=f'''⚠ {deleted_or_unavailable_tracks_count} tracks are unavailable or deleted from your playlist: "{enabled_playlist.title}"''',
                        link=reverse('user_profile:single_playlist', kwargs={'playlist_id': enabled_playlist.id}),
                        css_class='alert-danger'))

        context['alerts'] = alerts

    return render(request, 'core/home.html', context=context)


def about(request):
    context = {
        'version': f'v{settings.VERSION}'
    }

    return render(request, 'core/about.html', context=context)


def make_guild(guild: DiscordGuild, include_users: bool = False):
    guild_dict = {
        'name': guild.name,
        'id': str(guild.id),
        'image': guild.image,
        'default_image': guild.default_image,
        'is_ready': guild.is_ready,
        'users_ready_count': len(guild.users_ready)
    }

    if include_users:
        guild_dict["users"] = list(map(make_multiselect_user, guild.users.all()))

    return guild_dict


def make_user(discord_user: DiscordUser):
    return {
        'id': str(discord_user.id),
        'name': discord_user.username,
        'image': discord_user.image,
        'image_16': discord_user.image + '?size=16',
        'image_32': discord_user.image + '?size=32',
        'default_image': discord_user.default_image,
    }


def make_multiselect_user(discord_user: DiscordUser):
    is_user_ready = discord_user.is_ready

    multiselect_user = make_user(discord_user)
    multiselect_user['$isDisabled'] = not is_user_ready
    multiselect_user['inInitialSelection'] = is_user_ready

    return multiselect_user


def make_multiselect_guild(guild: DiscordGuild):
    return {
        'id': str(guild.id),
        'name': guild.name,
        'image': guild.image,
        'image_16': guild.image + '?size=16',
        'image_32': guild.image + '?size=32',
        'default_image': guild.default_image,
        '$isDisabled': not guild.is_ready,
    }


@login_required
def groups(request):
    user_query = Q(users__user=request.user)
    user_guilds = list(
        map(make_multiselect_guild,
            filter(lambda guild: guild.is_ready, DiscordGuild.objects.filter(user_query)))
    )
    other_guilds = list(
        map(make_multiselect_guild,
            filter(lambda guild: guild.is_ready, DiscordGuild.objects.filter(~user_query)))
    )
    get_name = operator.itemgetter('name')
    user_guilds.sort(key=get_name)
    other_guilds.sort(key=get_name)

    context = {
        'json_context': json.dumps({
            'user_guilds': user_guilds,
            'other_guilds': other_guilds,
            'create_playlist_url': reverse("core:create_dynamic_playlist")
        }),
    }

    return render(request, 'core/groups.html', context)


def subtitles(request):
    duration = datetime.timedelta(seconds=int(request.GET.get('duration')))

    ending_start_delta = duration - datetime.timedelta(seconds=15)
    ending_end_delta = duration - datetime.timedelta(seconds=5)
    ending_start = '{0:02d}:{1:02d}'.format(*divmod(ending_start_delta.seconds, 60))
    ending_end = '{0:02d}:{1:02d}'.format(*divmod(ending_end_delta.seconds, 60))

    context = {
        'ending_start': ending_start,
        'ending_end': ending_end,
        'title': request.GET.get('title'),
    }

    return render(request, 'core/subtitles.webvtt', context, content_type="text/vtt")


def get_guilds_without_duplicate_users(guilds: List[DiscordGuild]):
    # Remove users appearing in a guild from subsequent guilds
    already_appeared_users = set()
    guild_dicts = [make_guild(guild, include_users=True) for guild in guilds]
    for guild_dict in guild_dicts:
        user_ids_in_guild = set(map(lambda user: user["id"], guild_dict["users"]))
        guild_dict["users"] = list(filter(lambda user: user["id"] not in already_appeared_users, guild_dict["users"]))
        already_appeared_users.update(user_ids_in_guild)

    return guild_dicts


@login_required
def create_dynamic_playlist(request):
    selected_guilds = request.POST.get('selectedGuilds').split(',')
    guilds = [get_object_or_404(DiscordGuild, id=guild_id) for guild_id in selected_guilds]

    context = {
        'json_context': json.dumps({
            'guilds': get_guilds_without_duplicate_users(guilds),
        }),
        'title': "Create new playlist",
    }

    return render(request, 'core/create_dynamic_playlist.html', context)


# No authentication is required for watching playlists, it allows to have guests and is less cumbersome for users
def play_dynamic_playlist(request, playlist_id):
    playlist = get_object_or_404(DynamicPlaylist, id=playlist_id)

    guilds = get_guilds_without_duplicate_users(playlist.groups.all())

    active_users = list(
        map(lambda user: str(user.discord.id), playlist.users.filter(dynamicplaylistuser__is_active=True)))

    for guild in guilds:
        for multiselect_user in guild["users"]:
            multiselect_user["inInitialSelection"] = \
                multiselect_user["inInitialSelection"] and multiselect_user["id"] in active_users

    context = {
        'json_context': json.dumps({
            'guilds': guilds,
            'playlistId': playlist.id,
            'websocketProtocol': 'ws' if settings.DEBUG else 'wss',
        }),
        'title': f"🎵 {playlist.title}",
        'is_host': playlist.users.get(dynamicplaylistuser__is_author=True) == request.user
    }

    return render(request, 'core/play_dynamic_playlist.html', context)
