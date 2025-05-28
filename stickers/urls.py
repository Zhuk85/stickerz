from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('city/<slug:city_slug>/', views.city_stickers, name='city_stickers'),
    path('city/<slug:city_slug>/category/<int:category_id>/', views.category_stickers, name='category_stickers'),
    path('sticker/<int:sticker_id>/', views.sticker_detail, name='sticker_detail'),
    path('profile/', views.profile, name='profile'),
    path('top/', views.top_stickers, name='top_stickers'),
    path('sticker/<int:sticker_id>/comment/', views.add_comment, name='add_comment'),
    path('sticker/<int:sticker_id>/like/', views.toggle_like, name='toggle_like'),
    path('create/', views.create_sticker, name='create_sticker'),
    path('edit/<int:sticker_id>/', views.edit_sticker, name='edit_sticker'),
    path('delete/<int:sticker_id>/', views.delete_sticker, name='delete_sticker'),
    path('search/', views.search, name='search'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.user_login, name='login'),
    path('chats/', views.chat_list, name='chat_list'),
    path('chat/<int:user_id>/', views.start_chat, name='start_chat'),
    path('chat/<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('chat/<int:chat_id>/send/', views.send_message, name='send_message'),
]