from django.contrib import admin
from .models import Review, ChatSession, ChatMessage, UserProfile


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'author_name', 'rating', 'is_approved', 'created_at', 'has_chat_image')
    list_filter = ('is_approved', 'rating', 'created_at')
    search_fields = ('user__username', 'guest_name', 'guest_email', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('rating', 'comment', 'is_approved')
        }),
        ('کاربر ثبت‌شده', {
            'fields': ('user', 'chat_history_message_id'),
            'classes': ('collapse',)
        }),
        ('کاربر مهمان', {
            'fields': ('guest_name', 'guest_email'),
            'classes': ('collapse',)
        }),
        ('زمان‌بندی', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_chat_image(self, obj):
        """نمایش اینکه آیا این نظر تصویر چت دارد یا نه"""
        return obj.chat_history_message_id is not None
    has_chat_image.short_description = 'تصویر چت'
    has_chat_image.boolean = True


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'display_name', 'session_id', 'last_message_time')
    list_filter = ('user', 'last_message_time')
    search_fields = ('user__username', 'display_name', 'session_id')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'role', 'content_preview')
    list_filter = ('role', 'session__user')
    search_fields = ('session__display_name', 'content_text')

    def content_preview(self, obj):
        if obj.content_text:
            return obj.content_text[:50] + '...' if len(obj.content_text) > 50 else obj.content_text
        elif obj.content_json:
            return 'JSON Content'
        return 'Empty'
    content_preview.short_description = 'محتوای پیام'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'user_email')
    search_fields = ('user__username', 'user__email')

    def user_email(self, obj):
        return obj.user.email if obj.user else '-'
    user_email.short_description = 'ایمیل کاربر'

