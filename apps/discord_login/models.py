from django.contrib.auth.models import User
from django.db import models


class DiscordGuild(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.TextField()
    icon = models.TextField(blank=True)


class DiscordUser(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='discord')
    guilds = models.ManyToManyField(DiscordGuild, related_name='users')
    avatar = models.TextField(blank=True)
    username = models.TextField()
    discriminator = models.TextField()
    locale = models.TextField()
