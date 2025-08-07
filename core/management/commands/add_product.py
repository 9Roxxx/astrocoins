from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from core.models import Product, ProductCategory
import requests
import os
from urllib.parse import urlparse
import tempfile
from django.core.files import File


class Command(BaseCommand):
    help = 'Add a single product to the store'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, required=True, help='Product name')
        parser.add_argument('--price', type=int, required=True, help='Product price in AC')
        parser.add_argument('--category', type=str, required=True, help='Product category')
        parser.add_argument('--stock', type=int, default=10, help='Stock quantity')
        parser.add_argument('--description', type=str, default='', help='Product description')
        parser.add_argument('--image-url', type=str, help='URL to product image')
        parser.add_argument('--digital', action='store_true', help='Is this a digital product?')
        parser.add_argument('--featured', action='store_true', help='Is this a featured product?')

    def handle(self, *args, **options):
        # Создаем или получаем категорию
        category, created = ProductCategory.objects.get_or_create(
            name=options['category'],
            defaults={'description': f'Категория {options["category"]}'}
        )
        
        if created:
            self.stdout.write(f"✅ Создана категория: {category.name}")
        else:
            self.stdout.write(f"📁 Категория найдена: {category.name}")

        # Проверяем, существует ли уже такой товар
        existing_product = Product.objects.filter(name=options['name']).first()
        
        if existing_product:
            # Обновляем существующий товар
            existing_product.price = options['price']
            existing_product.stock = options['stock']
            existing_product.description = options['description'] or f"Товар {options['name']} из магазина Алгоритмики"
            existing_product.category = category
            existing_product.is_digital = options['digital']
            existing_product.featured = options['featured']
            existing_product.save()
            
            product = existing_product
            self.stdout.write(f"🔄 Обновлен товар: {product.name}")
        else:
            # Создаем новый товар
            product = Product.objects.create(
                name=options['name'],
                price=options['price'],
                stock=options['stock'],
                description=options['description'] or f"Товар {options['name']} из магазина Алгоритмики",
                category=category,
                is_digital=options['digital'],
                featured=options['featured'],
                available=True
            )
            self.stdout.write(f"✅ Создан товар: {product.name}")

        # Обрабатываем изображение, если указан URL
        if options.get('image_url'):
            self.stdout.write(f"🖼️ Скачиваем изображение...")
            image_result = self.download_image(options['image_url'], product.name)
            
            if image_result:
                temp_file_path, filename = image_result
                try:
                    with open(temp_file_path, 'rb') as f:
                        product.image.save(filename, File(f), save=True)
                    self.stdout.write(f"✅ Изображение сохранено: {filename}")
                    
                    # Удаляем временный файл
                    os.unlink(temp_file_path)
                except Exception as e:
                    self.stdout.write(f"❌ Ошибка сохранения изображения: {e}")
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)

        # Выводим информацию о товаре
        self.stdout.write("\n" + "="*50)
        self.stdout.write(f"📦 ТОВАР ДОБАВЛЕН")
        self.stdout.write("="*50)
        self.stdout.write(f"Название: {product.name}")
        self.stdout.write(f"Цена: {product.price} AC")
        self.stdout.write(f"Категория: {product.category.name}")
        self.stdout.write(f"В наличии: {product.stock} шт.")
        self.stdout.write(f"Тип: {'Цифровой' if product.is_digital else 'Физический'}")
        self.stdout.write(f"Популярный: {'Да' if product.featured else 'Нет'}")
        if product.image:
            self.stdout.write(f"Изображение: {product.image.url}")
        self.stdout.write("="*50)

    def download_image(self, image_url, product_name):
        """Скачиваем изображение товара"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(image_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Получаем расширение файла
            parsed_url = urlparse(image_url)
            file_extension = os.path.splitext(parsed_url.path)[1] or '.jpg'
            
            # Создаем имя файла
            import re
            safe_name = re.sub(r'[^\w\s-]', '', product_name).strip()
            safe_name = re.sub(r'[-\s]+', '-', safe_name)
            filename = f"{safe_name}{file_extension}"
            
            # Сохраняем во временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                tmp_file.write(response.content)
                tmp_file.flush()
                
                return tmp_file.name, filename
                
        except Exception as e:
            self.stdout.write(f"❌ Ошибка скачивания изображения {image_url}: {e}")
            return None