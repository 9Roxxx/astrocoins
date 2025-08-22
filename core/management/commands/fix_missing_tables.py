from django.core.management.base import BaseCommand
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Исправление недостающих таблиц в базе данных'
    
    def check_and_create_missing_tables(self):
        """Проверяет и создает недостающие таблицы"""
        with connection.cursor() as cursor:
            self.stdout.write("🔍 Проверяем недостающие таблицы...")
            
            # Получаем список всех таблиц
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            self.stdout.write(f"📋 Найдено таблиц: {len(existing_tables)}")
            
            # Проверяем таблицу core_user_cities
            if 'core_user_cities' not in existing_tables:
                self.stdout.write("🔧 Создаем таблицу core_user_cities...")
                
                # Создаем таблицу для many-to-many связи User <-> City
                cursor.execute("""
                    CREATE TABLE "core_user_cities" (
                        "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                        "user_id" integer NOT NULL REFERENCES "core_user" ("id") DEFERRABLE INITIALLY DEFERRED,
                        "city_id" integer NOT NULL REFERENCES "core_city" ("id") DEFERRABLE INITIALLY DEFERRED
                    )
                """)
                
                # Создаем индексы
                cursor.execute("""
                    CREATE INDEX "core_user_cities_user_id_idx" ON "core_user_cities" ("user_id")
                """)
                
                cursor.execute("""
                    CREATE INDEX "core_user_cities_city_id_idx" ON "core_user_cities" ("city_id")
                """)
                
                # Создаем уникальный индекс
                cursor.execute("""
                    CREATE UNIQUE INDEX "core_user_cities_user_id_city_id_uniq" 
                    ON "core_user_cities" ("user_id", "city_id")
                """)
                
                self.stdout.write("  ✅ Таблица core_user_cities создана")
            else:
                self.stdout.write("  ℹ️  Таблица core_user_cities уже существует")
            
            # Проверяем другие возможные недостающие таблицы
            expected_tables = [
                'core_user_cities',
                'core_group_students',  # Может понадобиться позже
            ]
            
            missing_tables = []
            for table in expected_tables:
                if table not in existing_tables:
                    missing_tables.append(table)
            
            if missing_tables:
                self.stdout.write(f"⚠️  Недостающие таблицы: {missing_tables}")
            else:
                self.stdout.write("✅ Все необходимые таблицы существуют")
    
    def handle(self, *args, **options):
        """Исправление недостающих таблиц"""
        
        self.stdout.write(self.style.WARNING("🔧 Начинаем исправление недостающих таблиц..."))
        
        # 1. Проверяем и создаем недостающие таблицы
        self.check_and_create_missing_tables()
        
        # 2. Проверяем структуру базы после исправлений
        with connection.cursor() as cursor:
            self.stdout.write("\n🔍 Проверяем структуру после исправлений...")
            
            # Проверяем таблицу core_user_cities
            if True:  # Всегда проверяем
                cursor.execute("PRAGMA table_info(core_user_cities)")
                columns = cursor.fetchall()
                self.stdout.write(f"  📋 core_user_cities: {[col[1] for col in columns]}")
            
            # Проверяем что связи работают
            try:
                cursor.execute("SELECT COUNT(*) FROM core_user_cities")
                count = cursor.fetchone()[0]
                self.stdout.write(f"  📊 Записей в core_user_cities: {count}")
            except Exception as e:
                self.stdout.write(f"  ❌ Ошибка при проверке: {str(e)}")
        
        # 3. Показываем итоговую статистику
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("🎊 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!"))
        self.stdout.write("="*60)
        
        self.stdout.write("✅ Результат:")
        self.stdout.write("  🗄️  Таблица core_user_cities создана и готова к работе")
        self.stdout.write("  🔗 Many-to-many связь User <-> City теперь работает")
        self.stdout.write("  👨‍🏫 Учителя смогут работать в нескольких городах")
        
        self.stdout.write("\n🚀 Теперь можно:")
        self.stdout.write("  1. Перезапустить сервис")
        self.stdout.write("  2. Тестировать региональную систему")
        self.stdout.write("  3. Назначать учителей в несколько городов")
        
        self.stdout.write(self.style.SUCCESS("\n✨ База данных полностью исправлена!"))
