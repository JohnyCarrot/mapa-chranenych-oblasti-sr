# Generated by Django 4.1.4 on 2023-12-30 13:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map', '0012_profile_icon_profile_reg_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='facebook_url',
            field=models.TextField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='profile',
            name='instagram_url',
            field=models.TextField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='profile',
            name='linked_in_url',
            field=models.TextField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='profile',
            name='website_url',
            field=models.TextField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='profile',
            name='youtube_url',
            field=models.TextField(blank=True, default='', max_length=500),
        ),
    ]