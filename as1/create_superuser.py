import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'as1.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Superuser details
username = 'admin'
email = 'admin@example.com'
password = 'adminpassword'  # Change this to a strong password in production!

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Superuser '{username}' created successfully.")
else:
    print(f"Superuser '{username}' already exists.")