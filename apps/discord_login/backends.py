from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.backends import BaseBackend

from apps.discord_login.models import DiscordUser, DiscordGuild
from apps.discord_login.oauth import make_session


class DiscordBackend(BaseBackend):
    def authenticate(self, request, oauth_code=None):
        oauth = make_session(request)

        oauth.fetch_token(
            token_url='https://discordapp.com/api/oauth2/token',
            code=oauth_code,
            client_secret=settings.DISCORD_CLIENT_SECRET
        )

        json_user = oauth.get('https://discordapp.com/api/users/@me').json()
        json_guilds = oauth.get('https://discordapp.com/api/users/@me/guilds').json()

        user = self.create_or_update_user(json_user=json_user)

        for json_guild in json_guilds:
            guild = self.create_or_update_guild(json_guild=json_guild)
            user.discord.guilds.add(guild)

        return user

    def create_or_update_user(self, json_user) -> User:

        discord_id = json_user["id"]

        try:
            user = DiscordUser.objects.get(id=discord_id).user
        except DiscordUser.DoesNotExist:
            user = User()
            user.discord = DiscordUser(id=discord_id)

        user.discord.avatar = json_user['avatar'] or ''
        user.discord.locale = json_user['locale']
        user.discord.username = json_user['username']
        user.discord.discriminator = json_user['discriminator']
        user.username = f'{user.discord.username}#{user.discord.discriminator}'

        user.save()
        user.discord.save()

        return user

    def create_or_update_guild(self, json_guild) -> DiscordGuild:

        guild_id = json_guild["id"]

        try:
            guild = DiscordGuild.objects.get(id=guild_id)
        except DiscordGuild.DoesNotExist:
            guild = DiscordGuild(id=guild_id)

        guild.name = json_guild["name"]
        guild.icon = json_guild["icon"] or ''
        guild.save()

        return guild

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
