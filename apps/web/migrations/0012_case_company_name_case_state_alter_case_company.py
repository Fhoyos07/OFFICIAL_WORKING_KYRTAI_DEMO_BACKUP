# Generated by Django 5.0.2 on 2024-03-07 16:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0011_alter_companynamevariation_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='company_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='case',
            name='state',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='cases', to='web.state'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='case',
            name='company',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cases', to='web.company'),
        ),
    ]