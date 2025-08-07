from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from core.models import Product, ProductCategory
import requests
import os
import json
from urllib.parse import urlparse
import tempfile
from django.core.files import File
import re


class Command(BaseCommand):
    help = 'Add multiple products from JSON data'

    def add_arguments(self, parser):
        parser.add_argument('--json-file', type=str, help='Path to JSON file with products')
        parser.add_argument('--json-data', type=str, help='JSON string with products data')

    def handle(self, *args, **options):
        if options.get('json_file'):
            # Читаем из файла
            try:
                with open(options['json_file'], 'r', encoding='utf-8') as f:
                    products_data = json.load(f)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка чтения файла: {e}"))
                return
        elif options.get('json_data'):
            # Читаем из строки
            try:
                products_data = json.loads(options['json_data'])
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка парсинга JSON: {e}"))
                return
        else:
            self.stdout.write(self.style.ERROR("Укажите --json-file или --json-data"))
            return

        if not isinstance(products_data, list):
            self.stdout.write(self.style.ERROR("JSON должен содержать массив товаров"))
            return

        created_count = 0
        updated_count = 0
        error_count = 0

        for i, product_data in enumerate(products_data):
            try:
                self.stdout.write(f"\n📦 Обрабатываем товар {i+1}/{len(products_data)}")
                
                # Проверяем обязательные поля
                if not all(key in product_data for key in ['name', 'price', 'category']):
                    self.stdout.write(self.style.ERROR(f"❌ Товар {i+1}: отсутствуют обязательные поля (name, price, category)"))
                    error_count += 1
                    continue

                # Создаем или получаем категорию
                category, cat_created = ProductCategory.objects.get_or_create(
                    name=product_data['category'],
                    defaults={'description': f'Категория {product_data["category"]}'}
                )
                
                if cat_created:
                    self.stdout.write(f"✅ Создана категория: {category.name}")

                # Проверяем, существует ли уже такой товар
                existing_product = Product.objects.filter(name=product_data['name']).first()
                
                if existing_product:
                    # Обновляем существующий товар
                    existing_product.price = product_data['price']
                    existing_product.stock = product_data.get('stock', 10)
                    existing_product.description = product_data.get('description', f"Товар {product_data['name']} из магазина Алгоритмики")
                    existing_product.category = category
                    existing_product.is_digital = product_data.get('is_digital', False)
                    existing_product.featured = product_data.get('featured', False)
                    existing_product.save()
                    
                    product = existing_product
                    updated_count += 1
                    self.stdout.write(f"🔄 Обновлен: {product.name} - {product.price} AC")
                else:
                    # Создаем новый товар
                    product = Product.objects.create(
                        name=product_data['name'],
                        price=product_data['price'],
                        stock=product_data.get('stock', 10),
                        description=product_data.get('description', f"Товар {product_data['name']} из магазина Алгоритмики"),
                        category=category,
                        is_digital=product_data.get('is_digital', False),
                        featured=product_data.get('featured', False),
                        available=True
                    )
                    created_count += 1
                    self.stdout.write(f"✅ Создан: {product.name} - {product.price} AC")

                # Обрабатываем изображение, если указан URL
                if product_data.get('image_url'):
                    self.stdout.write(f"🖼️ Скачиваем изображение для {product.name}...")
                    image_result = self.download_image(product_data['image_url'], product.name)
                    
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

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Ошибка обработки товара {i+1}: {e}"))
                error_count += 1

        # Итоговая статистика
        self.stdout.write("\n" + "="*60)
        self.stdout.write(f"🎉 ИМПОРТ ЗАВЕРШЕН")
        self.stdout.write("="*60)
        self.stdout.write(f"✅ Создано товаров: {created_count}")
        self.stdout.write(f"🔄 Обновлено товаров: {updated_count}")
        self.stdout.write(f"❌ Ошибок: {error_count}")
        self.stdout.write(f"📦 Всего обработано: {len(products_data)}")
        self.stdout.write("="*60)

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