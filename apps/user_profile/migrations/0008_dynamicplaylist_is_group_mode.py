# Generated by Django 4.1 on 2022-08-24 17:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user_profile", "0007_trackuri_unavailable"),
    ]

    operations = [
        migrations.AddField(
            model_name="dynamicplaylist",
            name="is_group_mode",
            field=models.BooleanField(default=True),
        ),
    ]
