from django.urls import path

from . import views

app_name = 'user_profile'
urlpatterns = [
    path('settings/', views.settings, name='settings'),
]
