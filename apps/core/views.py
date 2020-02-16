import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from ..discord_login.models import DiscordGuild, DiscordUser


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


@login_required(login_url='discord/login')
def groups(request):
    context = {
        'guilds': map(make_guild, request.user.discord.guilds.all())
    }

    return render(request, 'core/groups.html', context)


@login_required(login_url='discord/login')
def group_playlist(request, guild_id):
    guild = get_object_or_404(DiscordGuild, id=guild_id)
    users = list(map(make_user, guild.users.all()))

    context = {
        'users_json': json.dumps(users),
        'title': f'{guild.name} - New Playlist',
    }

    return render(request, 'core/group_playlist.html', context)
