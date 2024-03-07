# Generated by Django 5.0.2 on 2024-03-07 14:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0007_rename_companyinputname_company_delete_case'),
    ]

    operations = [
        migrations.CreateModel(
            name='Case',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('case_id', models.CharField(blank=True, max_length=255, null=True)),
                ('case_number', models.CharField(blank=True, max_length=255, null=True)),
                ('case_type', models.CharField(blank=True, max_length=255, null=True)),
                ('court', models.CharField(blank=True, max_length=255, null=True)),
                ('url', models.URLField(blank=True, null=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='web.company')),
            ],
        ),
    ]
