# Generated by Django 5.0.7 on 2024-08-08 03:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_rename_connected_class_herd_connectedclass'),
    ]

    operations = [
        migrations.AlterField(
            model_name='animal',
            name='inbreeding',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='animal',
            name='pedigree',
            field=models.JSONField(default={'dam': None, 'id': None, 'sire': None}),
            preserve_default=False,
        ),
    ]
