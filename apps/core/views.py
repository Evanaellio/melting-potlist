import datetime
import json
import urllib.parse
from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db.models import Q

from apps.discord_login.models import DiscordGuild, DiscordUser
from .playlist_generator import generate_youtube, generate_pls
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


def make_guild(guild: DiscordGuild):
    return {
        'name': guild.name,
        'id': guild.id,
        'image': guild.image,
        'default_image': guild.default_image,
        'is_ready': guild.is_ready,
        'users_ready_count': len(guild.users_ready)
    }


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
    user_guilds = list(map(make_guild, request.user.discord.guilds.all()))
    user_guilds.sort(key=lambda guild: guild['users_ready_count'], reverse=True)
    context = {
        'user_guilds': user_guilds,
    }

    return render(request, 'core/groups.html', context)


@login_required
def group_playlist(request, guild_id):
    guild = get_object_or_404(DiscordGuild, id=guild_id)
    users = list(map(make_multiselect_user, guild.users.all()))

    context = {
        'users_json': json.dumps(users),
        'title': guild.name,
        'guild_id': guild.id,
    }

    return render(request, 'core/group_playlist.html', context)


@login_required
def generate_playlist(request, guild_id):
    try:
        guild = request.user.discord.guilds.get(id=guild_id)
    except DiscordGuild.DoesNotExist:
        raise Http404()

    mode = request.POST['mode']
    sync = 'nosync' not in request.POST

    user_ids = set(map(int, request.POST['users'].split(',')))
    selected_users = list(map(lambda discord_user: discord_user.user, guild.users.filter(id__in=user_ids)))

    if sync:
        for user in selected_users:
            for enabled_playlist in user.playlists.filter(enabled=True):
                enabled_playlist.synchronize()

    if mode == 'youtube':
        generated_playlists = generate_youtube(selected_users)
        query = urllib.parse.urlencode({'playlists': ','.join(generated_playlists)})
        return redirect(f"{reverse('core:player')}?{query}")
    elif mode == 'pls':
        generated_pls = generate_pls(selected_users)
        response = HttpResponse(generated_pls, content_type="audio/x-scpls")
        response['Content-Disposition'] = 'inline; filename=playlist.pls'
        return response


def player(request):
    context = {
        'playlists': request.GET.get('playlists').split(','),
    }

    return render(request, 'core/player.html', context)


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


@login_required
def create_dynamic_playlist(request, guild_id):
    guild = get_object_or_404(DiscordGuild, id=guild_id)
    users = list(map(make_multiselect_user, guild.users.all()))

    context = {
        'json_context': json.dumps({
            'users': users,
            'guild_id': str(guild_id),
        }),
        'title': guild.name,
    }

    return render(request, 'core/create_dynamic_playlist.html', context)


@login_required
def play_dynamic_playlist(request, playlist_id):
    playlist = get_object_or_404(DynamicPlaylist, id=playlist_id)

    if playlist.users.get(dynamicplaylistuser__is_author=True) != request.user:
        raise PermissionDenied("Only the author of a playlist can play it (for now)")

    if playlist.groups.exists():
        users = list(map(lambda discord_user: make_multiselect_user(discord_user),
                         DiscordUser.objects.filter(guilds__in=playlist.groups.all())))
    else:
        users = list(map(lambda user: make_multiselect_user(user.discord), playlist.users.all()))

    active_users = list(
        map(lambda user: str(user.discord.id), playlist.users.filter(dynamicplaylistuser__is_active=True)))

    # Synchronize active users playlists before playing (except in solo mode)
    if playlist.groups.exists():
        for active_user in playlist.users.filter(dynamicplaylistuser__is_active=True):
            for enabled_playlist in active_user.playlists.filter(enabled=True):
                enabled_playlist.synchronize()

    for multiselect_user in users:
        multiselect_user["inInitialSelection"] = \
            multiselect_user["inInitialSelection"] and multiselect_user["id"] in active_users

    context = {
        'json_context': json.dumps({
            'users': users,
            'playlistId': playlist.id,
        }),
        'title': f"🎵 {playlist.title}",
    }

    return render(request, 'core/play_dynamic_playlist.html', context)
