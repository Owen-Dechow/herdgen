# Generated by Django 5.0.7 on 2024-08-23 04:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0010_alter_assignmentstep_assignment_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='animal',
            name='net_merit',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='class',
            name='net_merit_visibility',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
    ]