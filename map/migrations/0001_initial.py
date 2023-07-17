# Generated by Django 4.1.4 on 2023-04-23 11:02

import django.contrib.gis.db.models.fields
import django.contrib.postgres.fields
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Objekty',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('meno', models.TextField(blank=True, null=True)),
                ('color', models.TextField(blank=True, null=True)),
                ('fillcolor', models.TextField(blank=True, null=True)),
                ('html', models.TextField(blank=True, null=True)),
                ('diskusia', models.BigIntegerField(blank=True, null=True)),
                ('geometry', django.contrib.gis.db.models.fields.GeometryField(srid=4326)),
                ('nastavenia', models.JSONField(blank=True, null=True)),
            ],
            options={
                'db_table': 'objekty',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Podskupiny',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('meno', models.TextField(blank=True, null=True)),
                ('viditelnost', django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), blank=True, size=None)),
                ('spravca', models.TextField(blank=True, null=True)),
                ('nastavenia', models.JSONField(blank=True, null=True)),
            ],
            options={
                'db_table': 'podskupiny',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Skupiny',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('meno', models.TextField(blank=True, null=True)),
                ('spravca', models.TextField(blank=True, null=True)),
                ('viditelnost', django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), blank=True, size=None)),
                ('nastavenia', models.JSONField(blank=True, null=True)),
            ],
            options={
                'db_table': 'skupiny',
                'managed': False,
            },
        ),
    ]
