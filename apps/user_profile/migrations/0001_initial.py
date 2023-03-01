# Generated by Django 3.0.1 on 2020-02-17 21:27

import annoying.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0011_update_proxy_permissions"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserSettings",
            fields=[
                (
                    "user",
                    annoying.fields.AutoOneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name="settings",
                        serialize=False,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("core_playlist_url", models.URLField(blank=True)),
            ],
        ),
    ]
