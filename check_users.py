#!/usr/bin/env python
import os
import sys
import django

# Add the project root to the path
sys.path.append('/var/www/astrocoins')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'astrocoins.settings')
django.setup()

from core.models import User

print("Все пользователи в базе данных:")
users = User.objects.all()
for user in users:
    print(f"ID: {user.id}, Username: {user.username}, Role: {user.role}, Active: {user.is_active}")

print(f"\nВсего пользователей: {users.count()}")
print(f"Активных: {User.objects.filter(is_active=True).count()}")
print(f"Учителей: {User.objects.filter(role='teacher').count()}")
print(f"Админов городов: {User.objects.filter(role='city_admin').count()}")
print(f"Старых админов: {User.objects.filter(role='admin').count()}")

