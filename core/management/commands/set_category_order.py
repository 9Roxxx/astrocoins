from django.core.management.base import BaseCommand
from core.models import ProductCategory


class Command(BaseCommand):
    help = 'Set the display order for product categories'

    def handle(self, *args, **options):
        # Определяем желаемый порядок категорий
        category_order = [
            "Коврики для мыши",
            "Браслеты", 
            "Канцелярские принадлежности",
            "Попсокеты",
            "Бутылки и стаканы",
            "Рюкзаки и сумки",
            "Головные уборы",
            "Наклейки и переводки",
            "ИЗ с педагогом",
            "Вкусняшки",
            "Часы",
            "Игры",
            "Одежда",
            "Подарочные сертификаты",
            "USB и аксессуары",
            "Значки и бейджи",
        ]

        self.stdout.write("🔄 Устанавливаем порядок категорий...")
        
        updated_count = 0
        not_found_count = 0
        
        for index, category_name in enumerate(category_order, start=1):
            try:
                category = ProductCategory.objects.get(name=category_name)
                category.order = index * 10  # Умножаем на 10, чтобы оставить место для вставок
                category.save()
                
                self.stdout.write(f"✅ {index:2d}. {category_name} (order={category.order})")
                updated_count += 1
                
            except ProductCategory.DoesNotExist:
                self.stdout.write(f"❌ {index:2d}. {category_name} - категория не найдена")
                not_found_count += 1

        # Устанавливаем порядок для остальных категорий (если есть)
        remaining_categories = ProductCategory.objects.exclude(
            name__in=category_order
        ).order_by('name')
        
        if remaining_categories.exists():
            self.stdout.write("\n📦 Остальные категории:")
            next_order = (len(category_order) + 1) * 10
            
            for category in remaining_categories:
                category.order = next_order
                category.save()
                self.stdout.write(f"✅ {next_order//10:2d}. {category.name} (order={category.order})")
                next_order += 10
                updated_count += 1

        # Статистика
        self.stdout.write("\n" + "="*60)
        self.stdout.write("📊 РЕЗУЛЬТАТ УСТАНОВКИ ПОРЯДКА")
        self.stdout.write("="*60)
        self.stdout.write(f"✅ Обновлено категорий: {updated_count}")
        self.stdout.write(f"❌ Не найдено категорий: {not_found_count}")
        self.stdout.write(f"📦 Всего категорий в системе: {ProductCategory.objects.count()}")
        
        if not_found_count > 0:
            self.stdout.write(f"\n💡 Создайте отсутствующие категории или проверьте названия")
            
        self.stdout.write("="*60)
        self.stdout.write("🎉 Порядок категорий установлен!")