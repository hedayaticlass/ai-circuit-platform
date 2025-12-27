# راه‌اندازی Google Sign-In برای Circuit AI

## مقدمه
این پروژه از Google Sign-In برای ورود و ثبت نام کاربران استفاده می‌کند. این سیستم به کاربران اجازه می‌دهد تا با یک کلیک وارد شوند و حساب‌های گوگل ذخیره شده در مرورگر خود را انتخاب کنند.

## تنظیمات Google Cloud Console

### ۱. ایجاد پروژه
1. به [Google Cloud Console](https://console.cloud.google.com/) بروید
2. یک پروژه جدید ایجاد کنید یا پروژه موجود را انتخاب کنید

### ۲. فعال کردن Google+ API
1. از منوی سمت چپ، **APIs & Services** > **Library** را انتخاب کنید
2. **Google+ API** را جستجو و فعال کنید

### ۳. ایجاد OAuth 2.0 Client ID
1. از منوی سمت چپ، **APIs & Services** > **Credentials** را انتخاب کنید
2. روی **Create Credentials** > **OAuth 2.0 Client IDs** کلیک کنید
3. Application type را روی **Web application** تنظیم کنید
4. نام مناسب وارد کنید (مثل "Circuit AI")
5. Authorized JavaScript origins را اضافه کنید:
   - `http://localhost:8000`
   - `http://127.0.0.1:8000`
   - `http://localhost:8001`
   - `http://127.0.0.1:8001`
6. Authorized redirect URIs را اضافه کنید:
   - `http://localhost:8000/accounts/google/login/callback/`
   - `http://127.0.0.1:8000/accounts/google/login/callback/`
   - `http://localhost:8001/accounts/google/login/callback/`
   - `http://127.0.0.1:8001/accounts/google/login/callback/`

### ۴. دریافت Client ID و Client Secret
پس از ایجاد Client ID، مقادیر زیر را دریافت خواهید کرد:
- **Client ID**: یک رشته بلند شبیه به `123456789-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com`
- **Client Secret**: یک رشته دیگر

## تنظیمات پروژه Django

### ۱. متغیرهای محیطی
فایل `.env` در ریشه پروژه ایجاد کنید و مقادیر زیر را اضافه کنید:

```env
GOOGLE_CLIENT_ID=your-google-client-id-here
GOOGLE_CLIENT_SECRET=your-google-client-secret-here
```

### ۲. نصب وابستگی‌ها
```bash
pip install -r requirements.txt
```

### ۳. اجرای پروژه
```bash
cd as1
python manage_local.py runserver 8001
```

## نحوه عملکرد

### نمایش حساب‌های گوگل
1. وقتی کاربر روی دکمه "ثبت نام با گوگل" یا "ورود با گوگل" کلیک می‌کند
2. سیستم Google Sign-In SDK حساب‌های گوگل ذخیره شده در مرورگر را شناسایی می‌کند
3. لیست حساب‌ها به کاربر نمایش داده می‌شود
4. کاربر می‌تواند حساب مورد نظر خود را انتخاب کند

### پردازش ورود/ثبت نام
1. پس از انتخاب حساب، Google credential به سرور ارسال می‌شود
2. سرور credential را با Google API تأیید می‌کند
3. اگر کاربر وجود داشته باشد، وارد می‌شود
4. اگر کاربر وجود نداشته باشد و در حالت ثبت نام باشیم، کاربر جدید ایجاد می‌شود

## نکات مهم

### امنیت
- هرگز Client Secret را در کد قرار ندهید
- از HTTPS در محیط production استفاده کنید
- دامنه‌های مجاز را محدود کنید

### تنظیمات محیطی
- در محیط توسعه از localhost استفاده کنید
- در محیط production دامنه واقعی را تنظیم کنید
- OAuth consent screen را تنظیم کنید

### عیب‌یابی
اگر حساب‌های گوگل نمایش داده نشدند:
1. مطمئن شوید Client ID صحیح است
2. دامنه‌ها را در Google Console بررسی کنید
3. مطمئن شوید JavaScript console خطایی ندارد
4. Cookieهای مرورگر را پاک کنید

## پشتیبانی
اگر با مشکل مواجه شدید، موارد زیر را بررسی کنید:
- تنظیمات Google Cloud Console
- متغیرهای محیطی
- Console مرورگر برای خطاها
- تنظیمات Django
