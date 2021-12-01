
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('apps.core.urls')),
    path('discord/', include('apps.discord_login.urls')),
    path('profile/', include('apps.user_profile.urls')),
    path('api/', include('apps.api.urls')),
    path('admin/', admin.site.urls),
]
