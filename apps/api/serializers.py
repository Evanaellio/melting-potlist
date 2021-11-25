from django.contrib.auth.models import User
from rest_framework import serializers

from apps.discord_login.models import DiscordGuild
from apps.user_profile.models import DynamicPlaylist, UserTrack, DynamicPlaylistUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']
        read_only_fields = ['id', 'username']


class DynamicPlaylistUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = DynamicPlaylistUser
        fields = ['id', 'user', 'is_author', 'is_active']
        read_only_fields = ['id', 'user', 'is_author', 'is_active']


class DynamicPlaylistSerializer(serializers.ModelSerializer):
    groups = serializers.PrimaryKeyRelatedField(many=True, queryset=DiscordGuild.objects.all())
    users = serializers.ListField(child=serializers.IntegerField(), write_only=True)
    title = serializers.CharField(required=False)

    class Meta:
        model = DynamicPlaylist
        fields = ['id', 'date_generated', 'groups', 'users', 'title']
        read_only_fields = ['id', 'date_generated']

    def to_representation(self, dynamic_playlist):
        ret = super().to_representation(dynamic_playlist)
        ret['users'] = map(lambda user: user.discord.id, dynamic_playlist.users.all())
        return ret

    def create(self, validated_data):
        authenticated_user = self.context['request'].user
        users = validated_data.pop('users')
        groups = validated_data.pop('groups')
        dynamic_playlist = DynamicPlaylist.objects.create(**validated_data)
        dynamic_playlist.groups.set(groups)

        for user in map(lambda user_id: User.objects.get(discord__id=user_id), users):
            DynamicPlaylistUser.objects.create(
                dynamic_playlist=dynamic_playlist,
                user=user,
                is_author=(user == authenticated_user),
            )

        # If playlist author (authenticated user) was not created yet (not in initial selection), add him as inactive
        author, author_created = DynamicPlaylistUser.objects.get_or_create(
            dynamic_playlist=dynamic_playlist,
            user=authenticated_user,
            is_author=True,
        )

        if author_created:
            author.is_active = False
            author.save()

        return dynamic_playlist
