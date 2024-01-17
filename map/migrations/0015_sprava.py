# Generated by Django 4.1.4 on 2024-01-17 14:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('map', '0014_alter_profile_icon'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sprava',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sprava', models.TextField(blank=True, default='')),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('videne', models.BooleanField(default=False)),
                ('odosielatel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='odosielatel_sprava', to=settings.AUTH_USER_MODEL)),
                ('prijimatel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prijimatel_sprava', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]