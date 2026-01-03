from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.urls import reverse

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        در اینجا می‌توانیم منطق ورود اجتماعی را تغییر دهیم
        """
        # اگر کاربر قبلاً وجود دارد، مستقیم وارد شود
        if sociallogin.is_existing:
            return redirect('/')

        # برای کاربران جدید، اجازه ثبت نام خودکار بده
        return super().pre_social_login(request, sociallogin)

    def get_login_redirect_url(self, request):
        """
        پس از ورود موفق، به صفحه اصلی برود
        """
        return '/'

    def is_auto_signup_allowed(self, request, sociallogin):
        """
        اجازه می‌دهد که ثبت نام خودکار انجام شود
        """
        return True

    def get_connect_redirect_url(self, request, socialaccount):
        """
        پس از اتصال حساب، به صفحه اصلی برود
        """
        return '/'

    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """
        مدیریت خطاهای احراز هویت
        """
        return super().authentication_error(request, provider_id, error, exception, extra_context)