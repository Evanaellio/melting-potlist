from django.forms import ModelForm

from .models import UserSettings


class UserSettingsForm(ModelForm):
    class Meta:
        model = UserSettings
        fields = ['core_playlist_url']
        labels = {
            'core_playlist_url': 'Youtube playlist URL'
        }
