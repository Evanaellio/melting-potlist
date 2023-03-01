# Generated by Django 4.1 on 2022-08-24 17:35

from django.db import migrations


def migrate_is_group_mode(apps, schema_editor):
    DynamicPlaylist = apps.get_model('user_profile', 'DynamicPlaylist')

    for dynamic_playlist in DynamicPlaylist.objects.all():
        dynamic_playlist.is_group_mode = dynamic_playlist.groups.exists()
        dynamic_playlist.save()


class Migration(migrations.Migration):
    dependencies = [
        ('user_profile', '0008_dynamicplaylist_is_group_mode'),
    ]

    operations = [
        migrations.RunPython(migrate_is_group_mode, reverse_code=migrations.RunPython.noop),
    ]