from django.urls import path

from . import views

app_name = 'core'
urlpatterns = [
    path('', views.home, name='home'),
    path('groups', views.groups, name='groups'),
    path('groups/<int:guild_id>/playlist', views.group_playlist, name='group_playlist'),
]
