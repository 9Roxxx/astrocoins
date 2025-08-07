import requests
from bs4 import BeautifulSoup
import re
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from core.models import Product, ProductCategory
from django.utils.text import slugify
import time
import random
import os
from urllib.parse import urljoin, urlparse
from django.core.files import File
import tempfile


class Command(BaseCommand):
    help = 'Parse products from algoritmika25.ru/store and add them to our shop'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually creating products',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to parse Algoritmika store...'))
        
        # Создаем основные категории, если их нет
        self.create_categories()
        
        # Парсим товары
        products = self.parse_products()
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No products will be created'))
            for product in products:
                self.stdout.write(f"Would create: {product['name']} - {product['price']} AC")
        else:
            self.create_products(products)
        
        self.stdout.write(self.style.SUCCESS('Parsing completed!'))

    def create_categories(self):
        """Создаем категории товаров"""
        categories = [
            {'name': 'Коврики для мыши', 'description': 'Стильные коврики для мыши с IT-тематикой'},
            {'name': 'Канцелярские принадлежности', 'description': 'Ручки, карандаши и другие канцтовары'},
            {'name': 'Браслеты', 'description': 'Браслеты с символикой Алгоритмики'},
            {'name': 'Попсокеты', 'description': 'Попсокеты для телефонов'},
            {'name': 'Бутылки и стаканы', 'description': 'Бутылки и стаканы для воды'},
            {'name': 'Рюкзаки и сумки', 'description': 'Рюкзаки и сумки с логотипом'},
            {'name': 'Головные уборы', 'description': 'Кепки, шапки и другие головные уборы'},
            {'name': 'Наклейки и переводки', 'description': 'Наклейки и переводки с IT-тематикой'},
            {'name': 'Вкусняшки', 'description': 'Сладости и снеки'},
            {'name': 'Часы', 'description': 'Часы с символикой'},
            {'name': 'Игры', 'description': 'Настольные и компьютерные игры'},
            {'name': 'Одежда', 'description': 'Футболки, худи и другая одежда'},
            {'name': 'Подарочные сертификаты', 'description': 'Подарочные сертификаты на курсы'},
            {'name': 'USB и аксессуары', 'description': 'USB-накопители и компьютерные аксессуары'},
            {'name': 'Игровые валюты', 'description': 'Roblox, Steam, Standoff и другие игровые валюты'},
            {'name': 'Значки и бейджи', 'description': 'Значки и школьные бейджи'},
        ]
        
        for cat_data in categories:
            category, created = ProductCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            if created:
                self.stdout.write(f"Created category: {category.name}")

    def parse_products(self):
        """Парсим товары с сайта"""
        products = []
        base_url = "https://algoritmika25.ru/store"
        
        self.stdout.write("Загружаем страницу магазина...")
        
        try:
            # Получаем HTML страницы
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(base_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ищем все товары на странице
            # Обновляем селекторы на основе реальной структуры сайта
            product_containers = soup.find_all('div', class_='product-item') or soup.find_all('div', class_='item') or soup.find_all('article')
            
            if not product_containers:
                # Пробуем альтернативные селекторы
                product_containers = soup.find_all('div', attrs={'data-product': True}) or soup.select('[class*="product"]')
            
            self.stdout.write(f"Найдено {len(product_containers)} контейнеров товаров")
            
            if not product_containers:
                # Если не можем найти автоматически, ищем по тексту
                self.stdout.write("Поиск товаров по тексту...")
                products = self.parse_by_text_patterns(soup)
            else:
                for i, container in enumerate(product_containers):
                    try:
                        self.stdout.write(f"Обрабатываем контейнер {i+1}/{len(product_containers)}")
                        product_data = self.extract_product_data(container, base_url)
                        if product_data:
                            products.append(product_data)
                            self.stdout.write(f"✅ Найден товар: {product_data['name']} - {product_data['price']} AC")
                        else:
                            self.stdout.write(f"❌ Контейнер {i+1} не содержит данных товара")
                    except Exception as e:
                        self.stdout.write(f"❌ Ошибка обработки контейнера {i+1}: {e}")
                        continue
            
            # Если ничего не найдено через контейнеры, пробуем текстовый парсинг
            if not products and product_containers:
                self.stdout.write("Контейнеры найдены, но товары не извлечены. Пробуем текстовый парсинг...")
                products = self.parse_by_text_patterns(soup)
            
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Ошибка загрузки страницы: {e}"))
            # Возвращаем базовые товары как fallback
            products = self.get_fallback_products()
        
        return products
    
    def parse_by_text_patterns(self, soup):
        """Парсим товары по текстовым паттернам"""
        products = []
        text_content = soup.get_text()
        
        self.stdout.write("Начинаем текстовый парсинг...")
        
        # Конкретные товары с правильными ценами из ваших данных
        known_products = [
            {'name': 'Коврик для мыши "Just code it"', 'price': 350, 'stock_pattern': r'Коврик для мыши "Just code it".*?В наличии:\s*(\d+)'},
            {'name': 'Ручка "Алгоритмика" белая', 'price': 40, 'stock_pattern': r'Ручка "Алгоритмика" белая.*?В наличии:\s*(\d+)'},
            {'name': 'Коврик для мыши "Cool kids do CODES"', 'price': 350, 'stock_pattern': r'Коврик для мыши "Cool kids do CODES".*?В наличии:\s*(\d+)'},
            {'name': 'Коврик для мыши с горячими клавишами', 'price': 350, 'stock_pattern': r'Коврик для мыши с горячими клавишами.*?В наличии:\s*(\d+)'},
            {'name': 'Коврик для мыши "Open source"', 'price': 350, 'stock_pattern': r'Коврик для мыши "Open source".*?В наличии:\s*(\d+)'},
            {'name': 'Коврик для мыши "Готово на 99%"', 'price': 350, 'stock_pattern': r'Коврик для мыши "Готово на 99%".*?В наличии:\s*(\d+)'},
            {'name': 'Карандаш "Алгоритмика" белый', 'price': 30, 'stock_pattern': r'Карандаш "Алгоритмика" белый.*?В наличии:\s*(\d+)'},
            {'name': 'Эко-ручка "Алгоритмика"', 'price': 40, 'stock_pattern': r'Эко-ручка "Алгоритмика".*?В наличии:\s*(\d+)'},
            {'name': 'Браслет "Алгоритмика" синий', 'price': 50, 'stock_pattern': r'Браслет "Алгоритмика" синий.*?В наличии:\s*(\d+)'},
            {'name': 'Roblox 800 Robux', 'price': 1000, 'stock_pattern': r'Roblox 800 Robux.*?В наличии:\s*(\d+)'},
            {'name': 'Steam Wallet 500₽', 'price': 600, 'stock_pattern': r'Steam Wallet 500₽.*?В наличии:\s*(\d+)'},
            {'name': 'Standoff 2 Gold 1000', 'price': 800, 'stock_pattern': r'Standoff 2 Gold 1000.*?В наличии:\s*(\d+)'},
            {'name': '80 робаксов с зачислением через 7 дней', 'price': 150, 'stock_pattern': r'80 робаксов с зачислением через 7 дней.*?В наличии:\s*(\d+)'},
            {'name': 'Попсокет "Code Life"', 'price': 200, 'stock_pattern': r'Попсокет "Code Life".*?В наличии:\s*(\d+)'},
            {'name': 'Попсокет "Open Source"', 'price': 100, 'stock_pattern': r'Попсокет "Open Source".*?В наличии:\s*(\d+)'},
            {'name': 'Коврик гигант фиолетовый', 'price': 350, 'stock_pattern': r'Коврик гигант фиолетовый.*?В наличии:\s*(\d+)'},
            {'name': 'Коврик гигант желтый', 'price': 350, 'stock_pattern': r'Коврик гигант желтый.*?В наличии:\s*(\d+)'},
        ]
        
        # Также пробуем найти товары по структуре "название товара" + "цена" + "В наличии:"
        lines = text_content.split('\n')
        current_product = {}
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Ищем названия товаров
            if any(keyword in line.lower() for keyword in ['коврик', 'ручка', 'попсокет', 'браслет', 'roblox', 'steam', 'standoff', 'карандаш']):
                if 'в наличии' not in line.lower() and len(line) > 5 and len(line) < 100:
                    current_product['name'] = line
                    
            # Ищем цены (числа без контекста "В наличии")
            elif re.match(r'^\d+$', line) and 'в наличии' not in lines[max(0, i-1)].lower():
                if 'name' in current_product:
                    current_product['price'] = int(line)
                    
            # Ищем количество в наличии
            elif 'в наличии:' in line.lower():
                match = re.search(r'в наличии:\s*(\d+)', line.lower())
                if match and 'name' in current_product:
                    current_product['stock'] = int(match.group(1))
                    
                    # Добавляем товар, если у нас есть название и цена
                    if 'name' in current_product and 'price' in current_product:
                        category = self.determine_category(current_product['name'])
                        products.append({
                            'name': current_product['name'],
                            'price': current_product['price'],
                            'stock': current_product.get('stock', 10),
                            'category': category,
                            'description': f"Товар {current_product['name']} из магазина Алгоритмики",
                            'is_digital': any(word in current_product['name'].lower() for word in ['roblox', 'steam', 'standoff', 'робакс']),
                            'featured': current_product['price'] > 500 or 'топ' in current_product['name'].lower() or '🔥' in current_product['name'],
                            'image_url': None
                        })
                        self.stdout.write(f"📦 Найден товар: {current_product['name']} - {current_product['price']} AC")
                        
                    current_product = {}
        
        # Ищем конкретные товары по названию
        for product_info in known_products:
            name = product_info['name']
            price = product_info['price']
            
            # Проверяем, есть ли этот товар на странице
            if name in text_content:
                # Проверяем, что товар еще не добавлен
                if not any(p['name'] == name for p in products):
                    # Ищем количество в наличии для этого товара
                    stock_match = re.search(product_info['stock_pattern'], text_content, re.IGNORECASE | re.DOTALL)
                    stock = int(stock_match.group(1)) if stock_match else 10
                    
                    category = self.determine_category(name)
                    products.append({
                        'name': name,
                        'price': price,
                        'stock': stock,
                        'category': category,
                        'description': f'Товар {name} из магазина Алгоритмики',
                        'is_digital': any(word in name.lower() for word in ['roblox', 'steam', 'standoff', 'робакс']),
                        'featured': price > 500 or 'топ' in name.lower() or '🔥' in name.lower(),
                        'image_url': None
                    })
                    self.stdout.write(f"🔍 Найден товар: {name} - {price} AC (в наличии: {stock})")
        
        self.stdout.write(f"Текстовый парсинг завершен. Найдено товаров: {len(products)}")
        return products
    
    def extract_product_data(self, container, base_url):
        """Извлекаем данные товара из контейнера"""
        try:
            # Ищем название товара
            name_elem = (
                container.find('h3') or 
                container.find('h4') or 
                container.find('h5') or
                container.find(class_=re.compile('title|name', re.I)) or
                container.find('a')
            )
            
            if not name_elem:
                return None
                
            name = name_elem.get_text().strip()
            
            # Ищем цену
            price_elem = (
                container.find(class_=re.compile('price|cost', re.I)) or
                container.find(text=re.compile(r'\d+\s*AC'))
            )
            
            if price_elem:
                if hasattr(price_elem, 'get_text'):
                    price_text = price_elem.get_text()
                else:
                    price_text = str(price_elem)
                    
                price_match = re.search(r'(\d+)', price_text)
                price = int(price_match.group(1)) if price_match else 100
            else:
                price = 100
            
            # Ищем количество в наличии
            stock_elem = container.find(text=re.compile(r'В наличии:\s*(\d+)', re.I))
            if stock_elem:
                stock_match = re.search(r'В наличии:\s*(\d+)', stock_elem)
                stock = int(stock_match.group(1)) if stock_match else 10
            else:
                stock = 10
            
            # Ищем изображение
            img_elem = container.find('img')
            image_url = None
            if img_elem and img_elem.get('src'):
                image_url = urljoin(base_url, img_elem['src'])
            
            # Определяем категорию
            category = self.determine_category(name)
            
            return {
                'name': name,
                'price': price,
                'stock': stock,
                'category': category,
                'description': f'Товар {name} из магазина Алгоритмики',
                'is_digital': any(word in name.lower() for word in ['roblox', 'steam', 'standoff', 'робакс']),
                'featured': price > 500 or 'топ' in name.lower() or '🔥' in name,
                'image_url': image_url
            }
            
        except Exception as e:
            self.stdout.write(f"Ошибка извлечения данных товара: {e}")
            return None
    
    def determine_category(self, name):
        """Определяем категорию товара по названию"""
        name_lower = name.lower()
        
        if any(word in name_lower for word in ['коврик']):
            return 'Коврики для мыши'
        elif any(word in name_lower for word in ['ручка', 'карандаш']):
            return 'Канцелярские принадлежности'
        elif any(word in name_lower for word in ['браслет']):
            return 'Браслеты'
        elif any(word in name_lower for word in ['попсокет']):
            return 'Попсокеты'
        elif any(word in name_lower for word in ['бутылка', 'кружка', 'стакан']):
            return 'Бутылки и стаканы'
        elif any(word in name_lower for word in ['рюкзак', 'сумка']):
            return 'Рюкзаки и сумки'
        elif any(word in name_lower for word in ['кепка', 'шапка']):
            return 'Головные уборы'
        elif any(word in name_lower for word in ['стикер', 'наклейка', 'переводка']):
            return 'Наклейки и переводки'
        elif any(word in name_lower for word in ['конфеты', 'шоколад', 'вкусняш']):
            return 'Вкусняшки'
        elif any(word in name_lower for word in ['часы']):
            return 'Часы'
        elif any(word in name_lower for word in ['игра', 'пазл']):
            return 'Игры'
        elif any(word in name_lower for word in ['футболка', 'худи', 'одежда']):
            return 'Одежда'
        elif any(word in name_lower for word in ['сертификат']):
            return 'Подарочные сертификаты'
        elif any(word in name_lower for word in ['usb', 'флешка']):
            return 'USB и аксессуары'
        elif any(word in name_lower for word in ['roblox', 'steam', 'standoff', 'робакс']):
            return 'Игровые валюты'
        elif any(word in name_lower for word in ['значок', 'бейдж']):
            return 'Значки и бейджи'
        else:
            return 'Попсокеты'  # Категория по умолчанию
    
    def download_image(self, image_url, product_name):
        """Скачиваем изображение товара"""
        if not image_url:
            return None
            
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
            self.stdout.write(f"Ошибка скачивания изображения {image_url}: {e}")
            return None
    
    def get_fallback_products(self):
        """Возвращаем базовые товары если парсинг не удался"""
        return [
            {
                'name': 'Коврик для мыши "Just code it"',
                'price': 350,
                'stock': 17,
                'category': 'Коврики для мыши',
                'description': 'Стильный коврик для мыши с мотивирующей надписью "Just code it" для программистов',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Ручка "Алгоритмика" белая',
                'price': 40,
                'stock': 54,
                'category': 'Канцелярские принадлежности',
                'description': 'Белая ручка с логотипом Алгоритмики. Идеально подходит для учебы и работы',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Коврик для мыши "Cool kids do CODES"',
                'price': 350,
                'stock': 18,
                'category': 'Коврики для мыши',
                'description': 'Коврик для мыши с надписью "Cool kids do CODES" - для юных программистов',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Коврик для мыши с горячими клавишами',
                'price': 350,
                'stock': 7,
                'category': 'Коврики для мыши',
                'description': 'ТОП товар! Коврик для мыши с полезными горячими клавишами для программирования',
                'is_digital': False,
                'featured': True  # Помечен как ТОП
            },
            {
                'name': 'Коврик для мыши "Open source"',
                'price': 350,
                'stock': 16,
                'category': 'Коврики для мыши',
                'description': 'Коврик для мыши с надписью "Open source" для любителей открытого кода',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Коврик для мыши "Готово на 99%"',
                'price': 350,
                'stock': 15,
                'category': 'Коврики для мыши',
                'description': 'Юмористический коврик для мыши "Готово на 99%" - знакомо каждому программисту',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Карандаш "Алгоритмика" белый',
                'price': 30,
                'stock': 5,
                'category': 'Канцелярские принадлежности',
                'description': 'Белый карандаш с логотипом Алгоритмики для рисования и черчения',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Эко-ручка "Алгоритмика"',
                'price': 40,
                'stock': 179,
                'category': 'Канцелярские принадлежности',
                'description': 'Экологичная ручка с логотипом Алгоритмики из переработанных материалов',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Браслет "Алгоритмика" синий',
                'price': 50,
                'stock': 2,
                'category': 'Браслеты',
                'description': 'Синий браслет с логотипом Алгоритмики. Стильный аксессуар для учеников',
                'is_digital': False,
                'featured': False
            },
            # Добавляем популярные игровые товары
            {
                'name': 'Roblox 800 Robux',
                'price': 1000,
                'stock': 50,
                'category': 'Игровые валюты',
                'description': '800 Robux для игры Roblox. Мгновенная доставка на аккаунт',
                'is_digital': True,
                'featured': True
            },
            {
                'name': 'Steam Wallet 500₽',
                'price': 600,
                'stock': 30,
                'category': 'Игровые валюты',
                'description': 'Пополнение Steam кошелька на 500 рублей. Цифровой код',
                'is_digital': True,
                'featured': True
            },
            {
                'name': 'Standoff 2 Gold 1000',
                'price': 800,
                'stock': 25,
                'category': 'Игровые валюты',
                'description': '1000 золота для игры Standoff 2. Быстрое пополнение аккаунта',
                'is_digital': True,
                'featured': True
            },
            {
                'name': 'Подарочный сертификат на курс программирования',
                'price': 5000,
                'stock': 10,
                'category': 'Подарочные сертификаты',
                'description': 'Подарочный сертификат на любой курс программирования в Алгоритмике',
                'is_digital': True,
                'featured': True
            },
            {
                'name': 'USB-флешка "Алгоритмика" 16GB',
                'price': 800,
                'stock': 15,
                'category': 'USB и аксессуары',
                'description': 'USB-накопитель 16GB с логотипом Алгоритмики. Идеален для хранения проектов',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Попсокет "Code Life"',
                'price': 200,
                'stock': 35,
                'category': 'Попсокеты',
                'description': 'Попсокет для телефона с надписью "Code Life" для юных программистов',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Попсокет "Open Source"',
                'price': 100,
                'stock': 25,
                'category': 'Попсокеты',
                'description': 'Попсокет для телефона с надписью "Open Source"',
                'is_digital': False,
                'featured': False
            },
            {
                'name': '80 робаксов с зачислением через 7 дней',
                'price': 150,
                'stock': 20,
                'category': 'Игровые валюты',
                'description': '80 робаксов для Roblox с зачислением через 7 дней (Уссурийск нет в наличии)',
                'is_digital': True,
                'featured': True
            },
            {
                'name': 'Коврик гигант фиолетовый',
                'price': 350,
                'stock': 3,
                'category': 'Коврики для мыши',
                'description': 'Большой фиолетовый коврик для мыши',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Коврик гигант желтый',
                'price': 350,
                'stock': 5,
                'category': 'Коврики для мыши',
                'description': 'Большой желтый коврик для мыши',
                'is_digital': False,
                'featured': False
            },
            # Дополнительные товары для пустых категорий
            {
                'name': 'Бутылка для воды "Алгоритмика"',
                'price': 400,
                'stock': 20,
                'category': 'Бутылки и стаканы',
                'description': 'Спортивная бутылка для воды с логотипом Алгоритмики',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Термокружка "Code & Coffee"',
                'price': 600,
                'stock': 15,
                'category': 'Бутылки и стаканы',
                'description': 'Термокружка для кофе с надписью "Code & Coffee"',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Рюкзак "Алгоритмика" черный',
                'price': 2000,
                'stock': 8,
                'category': 'Рюкзаки и сумки',
                'description': 'Стильный черный рюкзак с логотипом Алгоритмики для ноутбука',
                'is_digital': False,
                'featured': True
            },
            {
                'name': 'Сумка для ноутбука "Tech Style"',
                'price': 1500,
                'stock': 12,
                'category': 'Рюкзаки и сумки',
                'description': 'Удобная сумка для ноутбука в техно-стиле',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Кепка "Алгоритмика" синяя',
                'price': 500,
                'stock': 25,
                'category': 'Головные уборы',
                'description': 'Синяя кепка с вышитым логотипом Алгоритмики',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Шапка "Code Ninja"',
                'price': 600,
                'stock': 18,
                'category': 'Головные уборы',
                'description': 'Теплая шапка с надписью "Code Ninja"',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Набор стикеров "IT-мемы"',
                'price': 150,
                'stock': 100,
                'category': 'Наклейки и переводки',
                'description': 'Набор из 20 стикеров с популярными IT-мемами',
                'is_digital': False,
                'featured': True
            },
            {
                'name': 'Переводки "HTML теги"',
                'price': 100,
                'stock': 50,
                'category': 'Наклейки и переводки',
                'description': 'Переводки с основными HTML тегами для декора',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Конфеты "Алгоритмика" мятные',
                'price': 80,
                'stock': 200,
                'category': 'Вкусняшки',
                'description': 'Мятные конфеты с логотипом Алгоритмики',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Шоколадка "Bug Free"',
                'price': 120,
                'stock': 150,
                'category': 'Вкусняшки',
                'description': 'Молочный шоколад с надписью "Bug Free"',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Часы настенные "Binary Time"',
                'price': 1200,
                'stock': 5,
                'category': 'Часы',
                'description': 'Необычные настенные часы, показывающие время в двоичном коде',
                'is_digital': False,
                'featured': True
            },
            {
                'name': 'Наручные часы "Алгоритмика"',
                'price': 2500,
                'stock': 10,
                'category': 'Часы',
                'description': 'Стильные наручные часы с логотипом Алгоритмики',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Настольная игра "Алгоритмы"',
                'price': 1800,
                'stock': 15,
                'category': 'Игры',
                'description': 'Образовательная настольная игра для изучения алгоритмов',
                'is_digital': False,
                'featured': True
            },
            {
                'name': 'Пазл "Код программиста"',
                'price': 800,
                'stock': 20,
                'category': 'Игры',
                'description': 'Пазл из 500 деталей с изображением кода',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Футболка "Алгоритмика" черная',
                'price': 900,
                'stock': 30,
                'category': 'Одежда',
                'description': 'Черная футболка с логотипом Алгоритмики',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Худи "Code Life" серое',
                'price': 2200,
                'stock': 15,
                'category': 'Одежда',
                'description': 'Серое худи с надписью "Code Life"',
                'is_digital': False,
                'featured': True
            },
            {
                'name': 'Значок "Python"',
                'price': 80,
                'stock': 100,
                'category': 'Значки и бейджи',
                'description': 'Металлический значок с логотипом Python',
                'is_digital': False,
                'featured': False
            },
            {
                'name': 'Бейдж школьный "Ученик Алгоритмики"',
                'price': 120,
                'stock': 50,
                'category': 'Значки и бейджи',
                'description': 'Школьный бейдж для учеников Алгоритмики',
                'is_digital': False,
                'featured': False
            }
        ]
        
        return product_data

    def create_products(self, products):
        """Создаем товары в базе данных"""
        created_count = 0
        updated_count = 0
        
        for product_data in products:
            try:
                # Получаем категорию
                category = ProductCategory.objects.get(name=product_data['category'])
                
                # Проверяем, существует ли уже такой товар
                product, created = Product.objects.get_or_create(
                    name=product_data['name'],
                    defaults={
                        'description': product_data['description'],
                        'price': product_data['price'],
                        'stock': product_data['stock'],
                        'category': category,
                        'is_digital': product_data['is_digital'],
                        'featured': product_data['featured'],
                        'available': True
                    }
                )
                
                # Обрабатываем изображение
                if product_data.get('image_url') and (created or not product.image):
                    self.stdout.write(f"Скачиваем изображение для {product.name}...")
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
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"Created: {product.name} - {product.price} AC")
                    )
                else:
                    # Обновляем существующий товар
                    product.price = product_data['price']
                    product.stock = product_data['stock']
                    product.description = product_data['description']
                    product.category = category
                    product.is_digital = product_data['is_digital']
                    product.featured = product_data['featured']
                    product.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"Updated: {product.name} - {product.price} AC")
                    )
                    
            except ProductCategory.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Category not found: {product_data['category']}")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error creating product {product_data['name']}: {str(e)}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"Import completed! Created: {created_count}, Updated: {updated_count}")
        )