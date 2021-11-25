from django.urls import include, path
from apps.api import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'dynamicplaylists', views.DynamicPlaylistViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('dynamicplaylists/<int:playlist_id>/persist_and_next/', views.PersistAndNext.as_view()),
    path('dynamicplaylists/<int:playlist_id>/users/<int:user_id>', views.DynamicPlaylistUsers.as_view()),
    path('media/<str:media_uri>/', views.Media.as_view()),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
