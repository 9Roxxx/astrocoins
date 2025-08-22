from django.core.management.base import BaseCommand
from core.models import User, City
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Настройка администраторов городов'
    
    def handle(self, *args, **options):
        """Создание администраторов городов и удаление остальных пользователей"""
        
        # Данные для создания администраторов
        city_admins = [
            {'username': 'adminVld', 'city_name': 'Владивосток'},
            {'username': 'adminBlag', 'city_name': 'Благовещенск'},
            {'username': 'adminSpassk', 'city_name': 'Спасск-Дальний'},
            {'username': 'adminUssur', 'city_name': 'Уссурийск'},
            {'username': 'adminNakhodka', 'city_name': 'Находка'},
            {'username': 'adminSvobodniy', 'city_name': 'Свободный'},
        ]
        
        self.stdout.write(self.style.WARNING("🏗️  Начинаем настройку региональных администраторов..."))
        
        # 1. Создаем города если их нет
        self.stdout.write("📍 Создаем города...")
        for admin_data in city_admins:
            city, created = City.objects.get_or_create(
                name=admin_data['city_name'],
                defaults={'description': f'Город {admin_data["city_name"]}'}
            )
            if created:
                self.stdout.write(f"  ✅ Создан город: {city.name}")
            else:
                self.stdout.write(f"  📍 Город уже существует: {city.name}")
        
        # 2. Удаляем всех существующих пользователей (кроме superuser'ов с именем не admin*)
        self.stdout.write(self.style.WARNING("🗑️  Удаляем существующих пользователей..."))
        
        # Найдем пользователей для удаления
        users_to_delete = User.objects.exclude(
            username__in=[admin['username'] for admin in city_admins]
        ).exclude(
            is_superuser=True,
            username__startswith='admin'
        )
        
        deleted_count = users_to_delete.count()
        if deleted_count > 0:
            users_to_delete.delete()
            self.stdout.write(f"  🗑️  Удалено пользователей: {deleted_count}")
        else:
            self.stdout.write("  ℹ️  Нет пользователей для удаления")
        
        # 3. Создаем администраторов городов
        self.stdout.write("👥 Создаем администраторов городов...")
        
        for admin_data in city_admins:
            username = admin_data['username']
            city_name = admin_data['city_name']
            
            try:
                city = City.objects.get(name=city_name)
                
                # Проверяем существует ли администратор
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': f'{username}@algoritmika25.store',
                        'role': 'admin',
                        'is_superuser': True,
                        'is_staff': True,
                        'city': city,
                        'first_name': f'Администратор',
                        'last_name': city_name,
                    }
                )
                
                if created:
                    # Устанавливаем пароль
                    user.set_password('admin123456')
                    user.save()
                    self.stdout.write(f"  ✅ Создан администратор: {username} (город: {city_name})")
                else:
                    # Обновляем существующего
                    user.role = 'admin'
                    user.is_superuser = True
                    user.is_staff = True
                    user.city = city
                    user.first_name = 'Администратор'
                    user.last_name = city_name
                    user.set_password('admin123456')
                    user.save()
                    self.stdout.write(f"  🔄 Обновлен администратор: {username} (город: {city_name})")
                
            except City.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Город {city_name} не найден для {username}")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Ошибка при создании {username}: {str(e)}")
                )
        
        # 4. Показываем итоговую статистику
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("🎊 НАСТРОЙКА ЗАВЕРШЕНА!"))
        self.stdout.write("="*60)
        
        self.stdout.write("📊 Статистика:")
        self.stdout.write(f"  🏙️  Всего городов: {City.objects.count()}")
        self.stdout.write(f"  👥 Всего администраторов: {User.objects.filter(role='admin').count()}")
        self.stdout.write(f"  📚 Всего пользователей: {User.objects.count()}")
        
        self.stdout.write("\n🔐 Данные для входа:")
        for admin_data in city_admins:
            username = admin_data['username']
            city_name = admin_data['city_name']
            self.stdout.write(f"  👤 {username} / admin123456 (город: {city_name})")
        
        self.stdout.write("\n🚀 Теперь можно:")
        self.stdout.write("  1. Войти как любой из администраторов")
        self.stdout.write("  2. Создавать учеников и учителей в своих городах")
        self.stdout.write("  3. Добавлять товары доступные в конкретных городах")
        
        self.stdout.write(self.style.SUCCESS("\n✨ Региональная система готова к работе!"))
