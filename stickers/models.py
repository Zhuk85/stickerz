from django.db import models
from django.contrib.auth.models import User
from transliterate import translit
import re

class City(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    image = models.ImageField(upload_to='city_images/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = re.sub(r'[^a-zA-Z0-9-]', '-', translit(self.name, 'ru', reversed=True)).lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)

    def __str__(self):
        return self.name  # Исправляем: возвращаем name

class Sticker(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='sticker_images/', blank=True, null=True)
    video = models.FileField(upload_to='sticker_videos/', blank=True, null=True)
    video_thumbnail = models.ImageField(upload_to='sticker_thumbnails/', blank=True, null=True)
    navigation_link = models.URLField(blank=True, null=True)
    proportion = models.CharField(max_length=10, default='1:1')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'city', 'category', 'description')  # Добавляем уникальность

    def __str__(self):
        return self.description

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sticker = models.ForeignKey(Sticker, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'sticker')

    def __str__(self):
        return f"{self.user.username} likes {self.sticker.description}"

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sticker = models.ForeignKey(Sticker, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.text}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    message = models.TextField()
    sticker = models.ForeignKey(Sticker, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.message} для {self.user.username}"

class Chat(models.Model):
    participants = models.ManyToManyField(User, related_name='chats')

    def get_other_participant(self, current_user):
        return self.participants.exclude(id=current_user.id).first()

    def get_last_message(self):
        return self.messages.order_by('-created_at').first()

    def __str__(self):
        return f"Chat {self.id} between {', '.join([user.username for user in self.participants.all()])}"

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username}: {self.content}"