# Generated by Django 4.1.4 on 2024-01-27 10:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map', '0017_diskusia_skupiny_diskusny_prispevok_skupiny'),
    ]

    operations = [
        migrations.AddField(
            model_name='diskusia_skupiny',
            name='aktivna',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='diskusia_skupiny',
            name='uzivatelia',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]
