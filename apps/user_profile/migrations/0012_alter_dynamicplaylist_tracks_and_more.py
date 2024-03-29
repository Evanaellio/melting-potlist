# Generated by Django 4.0 on 2022-09-02 19:43

from django.db import migrations, models
import django.db.models.deletion


def delete_all_rows_from_dynamic_playlist_tracks(apps, schema_editor):
    DynamicPlaylistTrack = apps.get_model("user_profile", "DynamicPlaylistTrack")
    DynamicPlaylistTrack.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("user_profile", "0011_migrate_track_listen_stats"),
    ]

    operations = [
        # Delete all rows first to avoid foreign key conflicts, the existing data is partially invalid anyway
        migrations.RunPython(delete_all_rows_from_dynamic_playlist_tracks, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="dynamicplaylist",
            name="tracks",
            field=models.ManyToManyField(
                related_name="dynamic_playlists", through="user_profile.DynamicPlaylistTrack", to="user_profile.Track"
            ),
        ),
        migrations.AlterField(
            model_name="dynamicplaylisttrack",
            name="track",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="user_profile.track"),
        ),
    ]
