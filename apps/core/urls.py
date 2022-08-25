from django.urls import path

from . import views

app_name = 'core'
urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('subtitles/', views.subtitles, name='subtitles'),
    path('player/', views.player, name='player'),
    path('groups/', views.groups, name='groups'),
    path('groups/<int:guild_id>/playlist/', views.group_playlist, name='group_playlist'),
    path('groups/<int:guild_id>/playlist/create', views.create_dynamic_playlist, name='create_dynamic_playlist'),
    path('playlists/<int:playlist_id>/', views.play_dynamic_playlist, name='play_dynamic_playlist'),
]
