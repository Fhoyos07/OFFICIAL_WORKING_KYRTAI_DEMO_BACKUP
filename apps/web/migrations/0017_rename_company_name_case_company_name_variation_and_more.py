# Generated by Django 5.0.2 on 2024-03-09 12:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0016_document_documentdetailsct_documentdetailsny'),
    ]

    operations = [
        migrations.RenameField(
            model_name='case',
            old_name='company_name',
            new_name='company_name_variation',
        ),
        migrations.AlterUniqueTogether(
            name='case',
            unique_together={('state', 'case_id')},
        ),
    ]
