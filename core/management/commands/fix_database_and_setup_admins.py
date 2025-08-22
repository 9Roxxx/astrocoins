from django.core.management.base import BaseCommand
from django.db import connection
from core.models import User, City
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Исправление базы данных и настройка администраторов городов'
    
    def add_city_column_if_not_exists(self):
        """Добавляет колонку city_id в таблицу core_user если её нет"""
        with connection.cursor() as cursor:
            # Проверяем существование колонки
            cursor.execute("PRAGMA table_info(core_user)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'city_id' not in columns:
                self.stdout.write("🔧 Добавляем колонку city_id в таблицу core_user...")
                cursor.execute("ALTER TABLE core_user ADD COLUMN city_id INTEGER NULL")
                cursor.execute("CREATE INDEX IF NOT EXISTS core_user_city_id_idx ON core_user(city_id)")
                self.stdout.write("  ✅ Колонка city_id добавлена")
            else:
                self.stdout.write("  ℹ️  Колонка city_id уже существует")
    
    def handle(self, *args, **options):
        """Исправление базы данных и создание администраторов городов"""
        
        self.stdout.write(self.style.WARNING("🔧 Начинаем исправление базы данных..."))
        
        # 1. Добавляем колонку city_id если её нет
        self.add_city_column_if_not_exists()
        
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
        
        # 2. Создаем города если их нет
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
        
        # 3. Удаляем всех существующих пользователей (кроме новых админов)
        self.stdout.write(self.style.WARNING("🗑️  Удаляем существующих пользователей..."))
        
        # Теперь используем raw SQL для безопасного удаления
        with connection.cursor() as cursor:
            # Отключаем проверку внешних ключей
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            # Получаем список пользователей которых НЕ нужно удалять
            admin_usernames = [admin['username'] for admin in city_admins]
            placeholders = ','.join(['?' for _ in admin_usernames])
            
            # Подсчитываем сколько пользователей будет удалено
            cursor.execute(f"""
                SELECT COUNT(*) FROM core_user 
                WHERE username NOT IN ({placeholders})
                AND NOT (is_superuser = 1 AND username LIKE 'admin%')
            """, admin_usernames)
            
            count_to_delete = cursor.fetchone()[0]
            
            if count_to_delete > 0:
                # Удаляем связанные записи сначала
                self.stdout.write("  🧹 Очищаем связанные данные...")
                
                # Удаляем CoinAward записи для пользователей
                cursor.execute(f"""
                    DELETE FROM core_coinaward 
                    WHERE user_id IN (
                        SELECT id FROM core_user 
                        WHERE username NOT IN ({placeholders})
                        AND NOT (is_superuser = 1 AND username LIKE 'admin%')
                    )
                """, admin_usernames)
                
                # Удаляем Purchase записи
                cursor.execute(f"""
                    DELETE FROM core_purchase 
                    WHERE student_id IN (
                        SELECT id FROM core_user 
                        WHERE username NOT IN ({placeholders})
                        AND NOT (is_superuser = 1 AND username LIKE 'admin%')
                    )
                """, admin_usernames)
                
                # Обнуляем teacher_id в группах
                cursor.execute(f"""
                    UPDATE core_group 
                    SET teacher_id = NULL 
                    WHERE teacher_id IN (
                        SELECT id FROM core_user 
                        WHERE username NOT IN ({placeholders})
                        AND NOT (is_superuser = 1 AND username LIKE 'admin%')
                    )
                """, admin_usernames)
                
                # Удаляем связи many-to-many в группах
                cursor.execute(f"""
                    DELETE FROM core_group_students 
                    WHERE user_id IN (
                        SELECT id FROM core_user 
                        WHERE username NOT IN ({placeholders})
                        AND NOT (is_superuser = 1 AND username LIKE 'admin%')
                    )
                """, admin_usernames)
                
                # Теперь удаляем пользователей
                cursor.execute(f"""
                    DELETE FROM core_user 
                    WHERE username NOT IN ({placeholders})
                    AND NOT (is_superuser = 1 AND username LIKE 'admin%')
                """, admin_usernames)
                
                self.stdout.write(f"  🗑️  Удалено пользователей: {count_to_delete}")
            else:
                self.stdout.write("  ℹ️  Нет пользователей для удаления")
            
            # Включаем обратно проверку внешних ключей
            cursor.execute("PRAGMA foreign_keys = ON")
        
        # 4. Создаем администраторов городов
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
        
        # 5. Показываем итоговую статистику
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
