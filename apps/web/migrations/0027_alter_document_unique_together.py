# Generated by Django 5.0.3 on 2024-03-17 20:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0026_case_found_date'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='document',
            unique_together={('case', 'document_id')},
        ),
    ]