
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('apps.core.urls')),
    path('discord/', include('apps.discord_login.urls')),
    path('admin/', admin.site.urls),
]
