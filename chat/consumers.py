import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth import get_user_model
from main.models import Chat

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]
        
        # Reject connection if user is not authenticated
        if self.user.is_anonymous:
            await self.close()
            return

        self.other_username = self.scope['url_route']['kwargs']['username']

        # Create a deterministic room name (alphabetical order)
        # This ensures UserA -> UserB and UserB -> UserA enter the same room
        usernames = sorted([self.user.username, self.other_username])
        self.room_group_name = f"chat_{usernames[0]}_{usernames[1]}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Fetch and send message history
        messages = await self.get_messages()
        for msg in messages:
            await self.send(text_data=json.dumps(msg))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        
        # 1. Handle Typing Status (No database hit)
        if data.get("type") == "typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_typing",
                    "username": self.user.username,
                    "is_typing": data.get("is_typing")
                }
            )
            return

        # 2. Handle Actual Messages
        message_body = data.get("message")
        if not message_body:
            return
        
        # Save message to DB and get formatted data back
        msg_data = await self.save_message(message_body)
        
        if msg_data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": msg_data
                }
            )

    async def chat_message(self, event):
        """Handler for 'chat_message' type events"""
        await self.send(text_data=json.dumps(event["message"]))

    async def user_typing(self, event):
        """Handler for 'user_typing' type events"""
        await self.send(text_data=json.dumps({
            "type": "typing_status",
            "username": event["username"],
            "is_typing": event["is_typing"]
        }))

    @database_sync_to_async
    def save_message(self, body):
        try:
            receiver = User.objects.get(username=self.other_username)
            chat_message = Chat.objects.create(
                sender=self.user,
                receiver=receiver,
                body=body
            )
            return {
                "id": chat_message.id,
                "sender": self.user.username,
                "body": chat_message.body,
                "timestamp": chat_message.timestamp.strftime('%H:%M'),
                "status": "sent",
            }
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def get_messages(self):
        try:
            receiver = User.objects.get(username=self.other_username)
        except User.DoesNotExist:
            return []

        # Mark incoming messages as read efficiently (single query)
        Chat.objects.filter(
            sender=receiver,
            receiver=self.user,
            is_read=False
        ).update(is_read=True, read_on=timezone.now())

        qs = Chat.objects.filter(
            sender__in=[self.user, receiver],
            receiver__in=[self.user, receiver]
        ).order_by("timestamp")[:50]

        return [{
            "id": msg.id,
            "sender": msg.sender.username if msg.sender else "Deleted User",
            "body": msg.body,
            "timestamp": msg.timestamp.strftime('%H:%M'),
            "status": "read" if msg.is_read else "sent"
        } for msg in qs]