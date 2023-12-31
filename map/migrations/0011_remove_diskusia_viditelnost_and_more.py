# Generated by Django 4.1.4 on 2023-12-28 12:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('map', '0010_diskusia_diskusny_prispevok'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='diskusia',
            name='viditelnost',
        ),
        migrations.AlterField(
            model_name='diskusny_prispevok',
            name='diskusia',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='map.diskusia'),
        ),
        migrations.AlterField(
            model_name='diskusny_prispevok',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
