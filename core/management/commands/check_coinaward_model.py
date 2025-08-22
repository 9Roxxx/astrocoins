from django.core.management.base import BaseCommand
from core.models import CoinAward
from django.db import connection

class Command(BaseCommand):
    help = 'Проверяет структуру модели CoinAward'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Проверка модели CoinAward...")
        
        # Проверяем поля модели
        fields = CoinAward._meta.get_fields()
        self.stdout.write(f"📋 Поля модели CoinAward:")
        for field in fields:
            self.stdout.write(f"   - {field.name}: {type(field).__name__}")
        
        # Проверяем структуру таблицы в базе данных
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'core_coinaward' ORDER BY ordinal_position;")
                db_fields = cursor.fetchall()
                
                self.stdout.write(f"\n📊 Поля в базе данных:")
                for field_name, field_type in db_fields:
                    self.stdout.write(f"   - {field_name}: {field_type}")
                
                # Проверяем есть ли поле student или user
                field_names = [field[0] for field in db_fields]
                if 'student_id' in field_names:
                    self.stdout.write(self.style.SUCCESS("✅ Поле 'student_id' найдено в базе данных"))
                elif 'user_id' in field_names:
                    self.stdout.write(self.style.WARNING("⚠️  Найдено поле 'user_id' вместо 'student_id'"))
                    self.stdout.write("   Нужна миграция для переименования поля!")
                else:
                    self.stdout.write(self.style.ERROR("❌ Не найдено ни 'student_id', ни 'user_id'"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка при проверке базы данных: {e}"))
        
        # Проверяем можем ли создать объект
        try:
            self.stdout.write("\n🧪 Попытка создания тестового объекта...")
            from core.models import User, AwardReason
            
            admin = User.objects.filter(is_superuser=True).first()
            student = User.objects.filter(role='student').first()
            reason = AwardReason.objects.first()
            
            if all([admin, student, reason]):
                # Пробуем создать объект
                test_award = CoinAward(
                    student=student,
                    teacher=admin,
                    reason=reason,
                    amount=reason.coins,
                    comment="Тест модели"
                )
                # Не сохраняем, только проверяем что объект создается
                self.stdout.write(self.style.SUCCESS("✅ Тестовый объект CoinAward создан успешно"))
                
            else:
                self.stdout.write(self.style.WARNING("⚠️  Недостаточно данных для тестирования"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка создания объекта: {e}"))
