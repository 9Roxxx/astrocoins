from django.core.management.base import BaseCommand
from django.db import connection
from core.models import User, City
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Безопасная настройка администраторов городов с проверкой структуры БД'
    
    def check_database_structure(self):
        """Проверяет структуру базы данных и выводит информацию"""
        with connection.cursor() as cursor:
            self.stdout.write("🔍 Анализируем структуру базы данных...")
            
            # Получаем список всех таблиц
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            
            self.stdout.write(f"📋 Найдено таблиц: {len(tables)}")
            
            # Проверяем структуру основных таблиц
            important_tables = ['core_user', 'core_coinaward', 'core_purchase', 'core_group', 'core_group_students']
            
            for table in important_tables:
                if table in tables:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    self.stdout.write(f"  ✅ {table}: {[col[1] for col in columns]}")
                else:
                    self.stdout.write(f"  ❌ {table}: НЕ НАЙДЕНА")
            
            return tables
    
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
    
    def safe_delete_users(self, admin_usernames):
        """Безопасно удаляет пользователей с учетом структуры БД"""
        with connection.cursor() as cursor:
            # Отключаем проверку внешних ключей
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            # Подсчитываем сколько пользователей будет удалено
            placeholders = ','.join(['?' for _ in admin_usernames])
            cursor.execute(f"""
                SELECT COUNT(*) FROM core_user 
                WHERE username NOT IN ({placeholders})
                AND NOT (is_superuser = 1 AND username LIKE 'admin%')
            """, admin_usernames)
            
            count_to_delete = cursor.fetchone()[0]
            
            if count_to_delete > 0:
                self.stdout.write("  🧹 Очищаем связанные данные...")
                
                # Получаем список всех таблиц
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Проверяем какие таблицы существуют и очищаем их
                
                # CoinAward - проверяем разные варианты названий полей
                if 'core_coinaward' in tables:
                    cursor.execute("PRAGMA table_info(core_coinaward)")
                    coinaward_columns = [col[1] for col in cursor.fetchall()]
                    
                    user_field = None
                    if 'user_id' in coinaward_columns:
                        user_field = 'user_id'
                    elif 'student_id' in coinaward_columns:
                        user_field = 'student_id'
                    
                    if user_field:
                        cursor.execute(f"""
                            DELETE FROM core_coinaward 
                            WHERE {user_field} IN (
                                SELECT id FROM core_user 
                                WHERE username NOT IN ({placeholders})
                                AND NOT (is_superuser = 1 AND username LIKE 'admin%')
                            )
                        """, admin_usernames)
                        self.stdout.write(f"    🏆 Очищены CoinAward записи (поле: {user_field})")
                
                # Purchase
                if 'core_purchase' in tables:
                    cursor.execute("PRAGMA table_info(core_purchase)")
                    purchase_columns = [col[1] for col in cursor.fetchall()]
                    
                    if 'student_id' in purchase_columns:
                        cursor.execute(f"""
                            DELETE FROM core_purchase 
                            WHERE student_id IN (
                                SELECT id FROM core_user 
                                WHERE username NOT IN ({placeholders})
                                AND NOT (is_superuser = 1 AND username LIKE 'admin%')
                            )
                        """, admin_usernames)
                        self.stdout.write("    🛒 Очищены Purchase записи")
                
                # Group - обнуляем teacher_id
                if 'core_group' in tables:
                    cursor.execute("PRAGMA table_info(core_group)")
                    group_columns = [col[1] for col in cursor.fetchall()]
                    
                    if 'teacher_id' in group_columns:
                        cursor.execute(f"""
                            UPDATE core_group 
                            SET teacher_id = NULL 
                            WHERE teacher_id IN (
                                SELECT id FROM core_user 
                                WHERE username NOT IN ({placeholders})
                                AND NOT (is_superuser = 1 AND username LIKE 'admin%')
                            )
                        """, admin_usernames)
                        self.stdout.write("    👨‍🏫 Обнулены teacher_id в группах")
                
                # Group students many-to-many
                if 'core_group_students' in tables:
                    cursor.execute("PRAGMA table_info(core_group_students)")
                    group_students_columns = [col[1] for col in cursor.fetchall()]
                    
                    user_field = None
                    if 'user_id' in group_students_columns:
                        user_field = 'user_id'
                    elif 'student_id' in group_students_columns:
                        user_field = 'student_id'
                    
                    if user_field:
                        cursor.execute(f"""
                            DELETE FROM core_group_students 
                            WHERE {user_field} IN (
                                SELECT id FROM core_user 
                                WHERE username NOT IN ({placeholders})
                                AND NOT (is_superuser = 1 AND username LIKE 'admin%')
                            )
                        """, admin_usernames)
                        self.stdout.write(f"    👥 Очищены связи в группах (поле: {user_field})")
                
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
    
    def handle(self, *args, **options):
        """Безопасная настройка администраторов городов"""
        
        self.stdout.write(self.style.WARNING("🔧 Начинаем безопасную настройку..."))
        
        # 1. Анализируем структуру БД
        tables = self.check_database_structure()
        
        # 2. Добавляем колонку city_id если её нет
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
        
        # 3. Создаем города если их нет
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
        
        # 4. Безопасно удаляем существующих пользователей
        self.stdout.write(self.style.WARNING("🗑️  Удаляем существующих пользователей..."))
        admin_usernames = [admin['username'] for admin in city_admins]
        self.safe_delete_users(admin_usernames)
        
        # 5. Создаем администраторов городов
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
        
        # 6. Показываем итоговую статистику
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
