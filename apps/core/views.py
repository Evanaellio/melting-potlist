import json
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from apps.discord_login.models import DiscordGuild, DiscordUser

from .playlist_generator import generate_youtube, generate_pls


@dataclass
class Alert:
    """Class for keeping track of an item in inventory."""
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
            deleted_tracks_count = enabled_playlist.user_tracks.filter(track_uri__deleted=True).count()

            if deleted_tracks_count:
                alerts.append(
                    Alert(
                        message=f'''⚠ {deleted_tracks_count} tracks are deleted from your playlist: "{enabled_playlist.title}"''',
                        link=reverse('user_profile:single_playlist', kwargs={'playlist_id': enabled_playlist.id}),
                        css_class='alert-danger'))

        context['alerts'] = alerts

    return render(request, 'core/home.html', context=context)


def make_guild(guild: DiscordGuild):
    return {
        'name': guild.name,
        'id': guild.id,
        'image': guild.image,
    }


def make_user(discord_user: DiscordUser):
    return {
        'id': str(discord_user.id),
        'name': discord_user.username,
        'image': discord_user.image,
        '$isDisabled': len(discord_user.user.settings.get_enabled_tracks()) == 0,
    }


@login_required
def groups(request):
    ready_guilds = sorted(filter(lambda guild: guild.users.count() >= 2, request.user.discord.guilds.all()),
                          key=lambda guild: guild.users.count(), reverse=True)
    not_ready_guilds = filter(lambda guild: guild.users.count() < 2, request.user.discord.guilds.all())

    context = {
        'ready_guilds': list(map(make_guild, ready_guilds)),
        'not_ready_guilds': list(map(make_guild, not_ready_guilds)),
    }

    return render(request, 'core/groups.html', context)


@login_required
def group_playlist(request, guild_id):
    guild = get_object_or_404(DiscordGuild, id=guild_id)
    users = list(map(make_user, guild.users.all()))

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
    user_ids = set(map(int, request.POST['users'].split(',')))
    selected_users = list(map(lambda discord_user: discord_user.user, guild.users.filter(id__in=user_ids)))

    for user in selected_users:
        for enabled_playlist in user.playlists.filter(enabled=True):
            enabled_playlist.synchronize()

    if mode == 'youtube':
        generated_playlists = generate_youtube(selected_users)
        return redirect(f'''{reverse('core:player')}?playlists={','.join(generated_playlists)}''')
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
