# stickers/admin.py
from django.contrib import admin
from .models import Sticker, Category, City, Like, Comment, Notification

admin.site.register(Sticker)
admin.site.register(Category)
admin.site.register(City)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Notification)