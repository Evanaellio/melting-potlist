from django.contrib.auth.models import User
from django.db import models


class DiscordGuild(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.TextField()
    icon = models.TextField(blank=True)

    @property
    def image(self):
        if self.icon:
            icon_ext = 'gif' if self.icon.startswith('a_') else 'png'
            image = f"https://cdn.discordapp.com/icons/{self.id}/{self.icon}.{icon_ext}"
        else:
            image = 'https://cdn.discordapp.com/embed/avatars/0.png'
        return image


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
        if self.avatar:
            icon_ext = 'gif' if self.avatar.startswith('a_') else 'png'
            image = f'https://cdn.discordapp.com/avatars/{self.id}/{self.avatar}.{icon_ext}'
        else:
            image = f'https://cdn.discordapp.com/embed/avatars/{self.discriminator % 5}.png'
        return image
