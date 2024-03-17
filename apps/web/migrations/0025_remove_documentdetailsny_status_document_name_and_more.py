# Generated by Django 5.0.3 on 2024-03-17 20:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0024_remove_casedetailsct_file_date_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='documentdetailsny',
            name='status_document_name',
        ),
        migrations.RemoveField(
            model_name='documentdetailsny',
            name='status_document_url',
        ),
        migrations.AddField(
            model_name='casedetailsny',
            name='status_document_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='casedetailsny',
            name='status_document_url',
            field=models.URLField(blank=True, max_length=255, null=True),
        ),
    ]
