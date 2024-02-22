# Generated by Django 5.0.2 on 2024-02-22 17:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=5, unique=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('website', models.URLField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Case',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('court', models.CharField(max_length=255)),
                ('case_id', models.CharField(max_length=255, unique=True)),
                ('case_type', models.CharField(max_length=100)),
                ('url', models.URLField(blank=True)),
                ('case_number', models.CharField(max_length=100)),
                ('caption', models.TextField()),
                ('received_date', models.DateField()),
                ('file_date', models.DateField()),
                ('return_date', models.DateField(blank=True, null=True)),
                ('additional_data', models.JSONField(blank=True, default=dict)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cases', to='web.company')),
                ('state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cases', to='web.state')),
            ],
        ),
    ]
