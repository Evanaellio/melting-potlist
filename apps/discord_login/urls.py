from django.urls import path

from . import views

app_name = "discord_login"
urlpatterns = [
    path("login/", views.login, name="login"),
    path("login/callback", views.callback, name="callback"),
    path("logout/", views.logout, name="logout"),
    path("fake_login/<int:user_id>/", views.fake_login, name="logout"),
]
