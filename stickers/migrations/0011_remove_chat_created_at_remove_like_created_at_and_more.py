# Generated by Django 5.2.1 on 2025-05-27 09:47

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stickers', '0010_chat_message'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='chat',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='like',
            name='created_at',
        ),
        migrations.AddField(
            model_name='sticker',
            name='video_thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to='sticker_thumbnails/'),
        ),
        migrations.AlterField(
            model_name='category',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='category_images/'),
        ),
        migrations.AlterField(
            model_name='city',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='city_images/'),
        ),
        migrations.AlterField(
            model_name='city',
            name='slug',
            field=models.SlugField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='message',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='notification',
            name='message',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='notification',
            name='sender',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sent_notifications', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='notification',
            name='sticker',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stickers.sticker'),
        ),
        migrations.AlterField(
            model_name='sticker',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='sticker_images/'),
        ),
        migrations.AlterField(
            model_name='sticker',
            name='navigation_link',
            field=models.URLField(blank=True, null=True),
        ),
    ]
