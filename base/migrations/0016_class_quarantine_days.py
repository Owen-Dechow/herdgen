# Generated by Django 5.0.7 on 2025-01-04 23:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0015_remove_class_starter_herd'),
    ]

    operations = [
        migrations.AddField(
            model_name='class',
            name='quarantine_days',
            field=models.IntegerField(default=0),
        ),
    ]