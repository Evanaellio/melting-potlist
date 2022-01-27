import json

import channels.exceptions
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.contrib.auth.models import AbstractUser, AnonymousUser

from apps.user_profile.models import DynamicPlaylist

'''
Implementation :

Lorsqu'un utilisateur se connecte, il envoie un message what's up ? Et le host lui répond en lui donnant les infos à synchroniser (playing / paused, elapsedTime).
Contrôle du son géré par chaque personne en individuel (sauf en mode contrôle de téléphone/PC à distance, mais c'est un autre sujet).

Attention : ne pas autoriser les non hosts à contrôler des choses ou a seek, à vérifier côté serveur
Todo : authent avec les sessions DJango (done ?)

Afficher côté host et côté listeners la liste des utilisateurs connectés à la playlist (ou bien les synchroniser en temps réel avec qui accède ou pas)
Côté listeners, seulement ça et pas le multiselect des gens

SI c'est en mode 'just discovering songs by myself', alors message d'erreur si on essaye de rejoindre ?? Ou juste alerte ?

Idée de génie : maintenant ça va être encore plus simple de gérer une liste des titres likés

Add sync button to force resync of audio to host

TODO : Bouton pour share l'URL et la coller dans le presse papier

'''


class DynamicPlaylistConsumer(WebsocketConsumer):
    playlist_id: int
    playlist_group_listeners_name: str
    playlist_group_host_name: str
    current_group: str
    is_host: bool
    current_user: AbstractUser
    playlist: DynamicPlaylist

    def connect(self):
        self.current_user = self.scope["user"]

        if self.current_user.is_anonymous:
            raise channels.exceptions.DenyConnection()

        self.playlist_id = self.scope['url_route']['kwargs']['playlist_id']
        self.playlist = DynamicPlaylist.objects.get(id=self.playlist_id)
        self.playlist_group_listeners_name = f'playlist_{self.playlist_id}_listeners'
        self.playlist_group_host_name = f'playlist_{self.playlist_id}_host'
        self.is_host = self.playlist.dynamic_playlist_users.get(is_author=True).user == self.current_user
        self.current_group = self.playlist_group_host_name if self.is_host else self.playlist_group_listeners_name

        async_to_sync(self.channel_layer.group_add)(self.current_group, self.channel_name)

        self.accept()

    def disconnect(self, close_code):
        # Leave current group
        async_to_sync(self.channel_layer.group_discard)(self.current_group, self.channel_name)

    # Receive message from WebSocket
    def receive(self, text_data):
        json_data = json.loads(text_data)
        other_group = self.playlist_group_listeners_name if self.is_host else self.playlist_group_host_name

        json_data['are_you_host'] = self.is_host
        json_data['current_group'] = self.current_group
        json_data['other_group'] = other_group

        message = {
            'type': 'websocket_action',
            'data': json_data
        }

        # Send message to other group
        async_to_sync(self.channel_layer.group_send)(other_group, message)

    def websocket_action(self, event):
        self.send_data(event['data'])

    def send_data(self, data):
        # Send data to WebSocket
        self.send(text_data=json.dumps(data))
