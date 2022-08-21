import uuid

import re
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AbstractUser

from apps.user_profile.models import DynamicPlaylist
from unidecode import unidecode


def cleanup_group_name(group_name):
    return re.sub('[^a-zA-Z0-9_.-]', '_', unidecode(group_name))


class DynamicPlaylistConsumer(AsyncJsonWebsocketConsumer):
    playlist_id: int
    group_playlist: str
    group_playlist_host: str
    group_playlist_user: str
    is_host: bool
    username: str
    current_user: AbstractUser

    @database_sync_to_async
    def is_host(self):
        playlist = DynamicPlaylist.objects.get(id=self.playlist_id)
        return playlist.dynamic_playlist_users.get(is_author=True).user == self.current_user

    async def connect(self):
        self.current_user = self.scope["user"]
        self.username = self.current_user.username or "Anonymous#" + uuid.uuid4().hex
        self.playlist_id = self.scope['url_route']['kwargs']['playlist_id']
        self.group_playlist = f'playlist_{self.playlist_id}'
        self.group_playlist_host = f'playlist_{self.playlist_id}_host'
        self.group_playlist_user = cleanup_group_name(f'playlist_{self.playlist_id}_{self.username}')
        self.is_host = await self.is_host()

        # Groups in parent variable self.groups will be leaved on user disconnect
        self.groups = [self.group_playlist, self.group_playlist_user]
        if self.is_host:
            self.groups.append(self.group_playlist_host)

        for group in self.groups:
            await self.channel_layer.group_add(group, self.channel_name)

        await self.accept()

        connect_message = {
            'type': 'websocket_action',
            'data': {
                'action': 'connect',
                'username': self.username,
                'is_host': self.is_host,
            }
        }

        await self.channel_layer.group_send(self.group_playlist, connect_message)

    async def disconnect(self, close_code):
        disconnect_message = {
            'type': 'websocket_action',
            'data': {
                'action': 'disconnect',
                'username': self.username,
                'is_host': self.is_host,
            }
        }

        await self.channel_layer.group_send(self.group_playlist, disconnect_message)

    # Receive message from WebSocket
    async def receive_json(self, content, **kwargs):
        message = {
            'type': 'websocket_action',
            'data': content
        }

        if content['action'] == "update_status":
            if not self.is_host:  # Only host can update status
                return
            elif 'to' in content:  # Update is destined to specific user that made a status query
                await self.channel_layer.group_send(content['to'], message)
            else:  # Update is destined to all users
                await self.channel_layer.group_send(self.group_playlist, message)
        elif content['action'] == "query_status":  # Add username to query status metadata and only send it to the host
            content['from'] = self.group_playlist_user
            await self.channel_layer.group_send(self.group_playlist_host, message)

    async def websocket_action(self, event):
        await self.send_json(event['data'])
