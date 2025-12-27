# ai-circuit-platform
AI-powered circuit analyzer !

## راه‌اندازی پروژه

### پیش‌نیازها
- Python 3.8+
- pip
- virtualenv (اختیاری اما توصیه می‌شود)

### نصب وابستگی‌ها
```bash
pip install -r requirements.txt
```

### اجرای پروژه به صورت محلی

1. **برای محیط توسعه محلی:**
```bash
cd as1
python manage_local.py runserver
```

2. **برای محیط سرور:**
```bash
cd as1
python manage.py runserver
```

### تنظیمات محیطی

برای اجرای محلی، تنظیمات به صورت خودکار شناسایی می‌شوند. اگر نیاز به تنظیم متغیرهای محیطی دارید:

1. فایل `env.example.txt` را کپی کنید:
```bash
cp env.example.txt .env
```

2. متغیرهای مورد نیاز را در فایل `.env` تنظیم کنید.

### تنظیم Google OAuth

برای فعال کردن ورود با گوگل:

1. به [Google Cloud Console](https://console.cloud.google.com/) بروید
2. یک پروژه جدید ایجاد کنید یا پروژه موجود را انتخاب کنید
3. APIs & Services > Credentials بروید
4. روی "Create Credentials" > "OAuth 2.0 Client IDs" کلیک کنید
5. Application type را روی "Web application" تنظیم کنید
6. Authorized redirect URIs را اضافه کنید:
   - برای محیط محلی: `http://localhost:8000/accounts/google/login/callback/`
   - برای محیط سرور: `https://yourdomain.com/accounts/google/login/callback/`
7. Client ID و Client Secret را دریافت کنید
8. این مقادیر را به عنوان متغیرهای محیطی تنظیم کنید:
   ```bash
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_client_secret
   ```

### ساختار پروژه
- `as1/` - پروژه اصلی Django
- `as1/home/` - اپلیکیشن اصلی
- `r/` - ابزارهای تحلیل مدار
- `static/` - فایل‌های استاتیک
- `templates/` - قالب‌ها