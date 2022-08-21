from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/dynamicplaylists/(?P<playlist_id>\w+)/$', consumers.DynamicPlaylistConsumer.as_asgi()),
]
