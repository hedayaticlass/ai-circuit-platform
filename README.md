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

### ساختار پروژه
- `as1/` - پروژه اصلی Django
- `as1/home/` - اپلیکیشن اصلی
- `r/` - ابزارهای تحلیل مدار
- `static/` - فایل‌های استاتیک
- `templates/` - قالب‌ها