# Generated by Django 4.1.4 on 2023-10-14 19:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map', '0005_alter_viditelnost_mapa_globalne_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='viditelnost_mapa',
            name='uzivatelia',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]
