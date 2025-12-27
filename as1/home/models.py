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
    session_id = models.CharField(max_length=255, db_index=True)
    display_name = models.CharField(max_length=255, default='چت جدید')
    last_message_time = models.FloatField(default=time.time) # زمان آخرین پیام (timestamp)

    class Meta:
        unique_together = ('user', 'session_id')

    def __str__(self):
        return f"{self.user.username} - {self.display_name}"

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20) # 'user' or 'assistant'
    content_text = models.TextField(null=True, blank=True)
    content_json = models.JSONField(null=True, blank=True) # برای ذخیره خروجی‌های پیچیده‌تر دستیار

    def __str__(self):
        content_preview = self.content_text[:50] if self.content_text else "No content"
        return f"{self.session.display_name} - {self.role}: {content_preview}"

class Review(models.Model):
    # فیلدهای اصلی
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)]) # 1 تا 5 ستاره
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False) # مدیریت نظرات

    # فیلدهای کاربر ثبت‌شده
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)

    # فیلدهای مهمان (کاربران بدون حساب)
    guest_name = models.CharField(max_length=100, blank=True, null=True)
    guest_email = models.EmailField(blank=True, null=True)

    # فیلد پیام چت هیستوری (فقط برای کاربران ثبت‌شده)
    chat_history_message_id = models.IntegerField(blank=True, null=True)  # ID پیام انتخاب شده از چت هیستوری

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'نظر کاربر'
        verbose_name_plural = 'نظرات کاربران'

    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.rating} ستاره"
        else:
            return f"{self.guest_name or 'مهمان'} - {self.rating} ستاره"

    @property
    def stars_display(self):
        """نمایش ستاره‌های پر و خالی"""
        filled = '★' * self.rating
        empty = '☆' * (5 - self.rating)
        return filled + empty

    @property
    def author_name(self):
        """نام نویسنده نظر"""
        return self.user.username if self.user else (self.guest_name or 'مهمان')

    @property
    def can_upload_image(self):
        """آیا این نظر می‌تواند تصویر داشته باشد"""
        return self.user is not None

    @property
    def chat_session_name(self):
        """نام چت مرتبط با این نظر (اگر وجود داشته باشد)"""
        if self.chat_history_message_id:
            try:
                message = ChatMessage.objects.get(id=self.chat_history_message_id)
                return message.session.display_name if message.session else None
            except ChatMessage.DoesNotExist:
                return None
        return None