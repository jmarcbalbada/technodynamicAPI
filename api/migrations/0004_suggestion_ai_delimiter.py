# Generated by Django 5.0.6 on 2024-12-05 16:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_suggestion_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='suggestion',
            name='ai_delimiter',
            field=models.TextField(blank=True, null=True),
        ),
    ]
