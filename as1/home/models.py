from django.db import models
from django.contrib.auth.models import User
import time

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # می‌توانید فیلدهای اضافی برای پروفایل کاربر اینجا اضافه کنید

    def __str__(self):
        return self.user.username

class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    session_id = models.CharField(max_length=255, unique=True, db_index=True)
    display_name = models.CharField(max_length=255, default='چت جدید')
    last_message_time = models.FloatField(default=time.time) # زمان آخرین پیام (timestamp)

    def __str__(self):
        return f"{self.user.username} - {self.display_name}"

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20) # 'user' or 'assistant'
    content_text = models.TextField(null=True, blank=True)
    content_json = models.JSONField(null=True, blank=True) # برای ذخیره خروجی‌های پیچیده‌تر دستیار

    def __str__(self):
        return f"{self.session.display_name} - {self.role}: {self.content_text[:50]}"
