from django.contrib.auth.models import User
from django.db import models


def discord_image(type, identifier, name):
    if identifier:
        ext = 'gif' if name.startswith('a_') else 'png'
        return f"https://cdn.discordapp.com/{type}/{identifier}/{name}.{ext}"
    return None


def discord_default_image(identifier):
    return f'https://cdn.discordapp.com/embed/avatars/{int(identifier) % 5}.png'


class DiscordGuild(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.TextField()
    icon = models.TextField(blank=True)

    @property
    def image(self):
        return discord_image('icons', self.id, self.icon) or self.default_image

    @property
    def default_image(self):
        return discord_default_image(self.id)

    @property
    def is_ready(self):
        if self.users.count() < 2:
            return False

        ready_count = 0
        for user in self.users.all():
            if user.is_ready:
                ready_count += 1
                if ready_count >= 2:
                    return True

        return False

    @property
    def users_ready(self):
        return [user for user in self.users.all() if user.is_ready]

    def __str__(self):
        return f'{self.name} ({self.id})'


class DiscordUser(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='discord')
    guilds = models.ManyToManyField(DiscordGuild, related_name='users')
    avatar = models.TextField(blank=True)
    username = models.TextField()
    discriminator = models.TextField()
    locale = models.TextField()

    @property
    def image(self):
        return discord_image('avatars', self.id, self.avatar) or self.default_image

    @property
    def default_image(self):
        return discord_default_image(self.discriminator)

    @property
    def is_ready(self):
        return len(self.user.settings.get_enabled_tracks()) > 0
