from django.urls import path

from . import views

app_name = 'user_profile'
urlpatterns = [
    path('playlists/', views.all_playlists, name='all_playlists'),
    path('playlists/<int:playlist_id>/', views.single_playlist, name='single_playlist'),
    path('playlists/<int:playlist_id>/delete', views.delete_playlist, name='delete_playlist'),
    path('playlists/<int:playlist_id>/synchronize', views.synchronize_playlist, name='synchronize_playlist'),
    path('playlists/<int:playlist_id>/toggle', views.toggle_playlist, name='toggle_playlist'),
]
