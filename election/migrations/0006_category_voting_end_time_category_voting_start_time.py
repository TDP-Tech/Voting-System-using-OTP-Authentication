# Generated by Django 5.0.2 on 2024-07-19 16:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('election', '0005_remove_category_voting_end_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='voting_end_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='category',
            name='voting_start_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
