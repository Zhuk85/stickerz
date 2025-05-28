import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import Chat, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat_group_name = f'chat_{self.chat_id}'

        # Проверяем, что пользователь имеет доступ к чату
        chat = await Chat.objects.aget(id=self.chat_id)
        if self.scope['user'] not in await chat.participants.all():
            await self.close()

        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.chat_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        content = text_data_json['content']
        sender = self.scope['user']

        # Сохраняем сообщение в базе
        chat = await Chat.objects.aget(id=self.chat_id)
        message = await Message.objects.acreate(
            chat=chat,
            sender=sender,
            content=content,
        )

        # Отправляем сообщение всем в группе
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'chat_message',
                'content': content,
                'sender': sender.username,
                'created_at': message.created_at.strftime('%H:%M, %d %b %Y'),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'content': event['content'],
            'sender': event['sender'],
            'created_at': event['created_at'],
        }))