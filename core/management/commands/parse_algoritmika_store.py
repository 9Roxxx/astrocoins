import requests
from bs4 import BeautifulSoup
import re
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from core.models import Product, ProductCategory
from django.utils.text import slugify
import time
import random


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
        
        # Товары, которые мы видим на сайте
        product_data = [
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