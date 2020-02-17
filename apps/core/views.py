import json
from urllib.parse import urlparse, parse_qs

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from apps.discord_login.models import DiscordGuild, DiscordUser

from .playlist_generator import generate


def home(request):
    return render(request, 'core/home.html')


def make_guild(guild: DiscordGuild):
    return {
        'name': guild.name,
        'id': guild.id,
        'image': guild.image,
    }


def make_user(user: DiscordUser):
    return {
        'id': str(user.id),
        'name': user.username,
        'image': user.image,
    }


def get_playlist_id(user: DiscordUser):
    return parse_qs(urlparse(user.user.settings.core_playlist_url).query)['list'][0]

@login_required
def groups(request):
    context = {
        'guilds': map(make_guild, request.user.discord.guilds.all())
    }

    return render(request, 'core/groups.html', context)


@login_required
def group_playlist(request, guild_id):
    guild = get_object_or_404(DiscordGuild, id=guild_id)
    users = list(map(make_user, guild.users.all()))

    context = {
        'users_json': json.dumps(users),
        'title': f'{guild.name} - New Playlist',
        'guild_id': guild.id,
    }

    return render(request, 'core/group_playlist.html', context)


def generate_playlist(request, guild_id):
    user_ids = set(map(int, request.POST['users'].split(',')))
    discord_users = DiscordUser.objects.filter(id__in=user_ids).all()
    all_playlists_ids = list(map(get_playlist_id, discord_users))

    generated_playlists = generate(all_playlists_ids)

    return redirect(f'''{reverse('core:player')}?playlists={','.join(generated_playlists)}''')


def player(request):
    context = {
        'playlists': request.GET.get('playlists').split(','),
    }

    return render(request, 'core/player.html', context)
