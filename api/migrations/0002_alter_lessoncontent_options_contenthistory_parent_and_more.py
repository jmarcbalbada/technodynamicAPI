# Generated by Django 5.0.6 on 2024-10-18 06:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='lessoncontent',
            options={'ordering': ['id']},
        ),
        migrations.AddField(
            model_name='contenthistory',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='api.contenthistory'),
        ),
        migrations.AlterField(
            model_name='contenthistory',
            name='lessonId',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lesson_id', to='api.lesson'),
        ),
        migrations.AlterField(
            model_name='contenthistory',
            name='version',
            field=models.CharField(default='1', max_length=10),
        ),
    ]