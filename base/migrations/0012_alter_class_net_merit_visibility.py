# Generated by Django 5.0.7 on 2024-11-13 00:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0011_animal_net_merit_class_net_merit_visibility'),
    ]

    operations = [
        migrations.AlterField(
            model_name='class',
            name='net_merit_visibility',
            field=models.BooleanField(default=True),
        ),
    ]
