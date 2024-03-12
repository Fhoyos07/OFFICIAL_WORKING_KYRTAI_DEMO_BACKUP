# Generated by Django 5.0.2 on 2024-03-10 08:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0018_remove_document_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='is_scraped',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='case',
            name='scraped_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='document',
            name='download_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='document',
            name='is_downloaded',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='document',
            name='relative_path',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]