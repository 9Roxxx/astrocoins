from django.core.management.base import BaseCommand
from core.models import ProductCategory
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Creates default product categories'

    def handle(self, *args, **options):
        categories = [
            {
                'name': 'Коврики для мыши',
                'icon': 'fa-computer-mouse',
                'order': 1
            },
            {
                'name': 'Браслеты',
                'icon': 'fa-ring',
                'order': 2
            },
            {
                'name': 'Канцелярские принадлежности',
                'icon': 'fa-pencil',
                'order': 3
            },
            {
                'name': 'Попсокеты',
                'icon': 'fa-mobile-screen',
                'order': 4
            },
            {
                'name': 'Бутылки/стаканы для воды',
                'icon': 'fa-bottle-water',
                'order': 5
            },
            {
                'name': 'Рюкзаки и сумки',
                'icon': 'fa-bag-shopping',
                'order': 6
            },
            {
                'name': 'Головные уборы',
                'icon': 'fa-hat-cowboy',
                'order': 7
            },
            {
                'name': 'Переводки и наклейки',
                'icon': 'fa-note-sticky',
                'order': 8
            },
            {
                'name': 'ИЗ с педагогом',
                'icon': 'fa-palette',
                'order': 9
            },
            {
                'name': 'Вкусняшки',
                'icon': 'fa-cookie-bite',
                'order': 10
            },
            {
                'name': 'Часы',
                'icon': 'fa-clock',
                'order': 11
            },
            {
                'name': 'Игры',
                'icon': 'fa-gamepad',
                'order': 12
            },
            {
                'name': 'Одежда',
                'icon': 'fa-shirt',
                'order': 13
            },
            {
                'name': 'Подарочные сертификаты',
                'icon': 'fa-gift',
                'order': 14
            },
            {
                'name': 'USB-накопитель (флешка)',
                'icon': 'fa-usb',
                'order': 15
            },
            {
                'name': 'Ремувки',
                'icon': 'fa-eraser',
                'order': 16
            },
            {
                'name': 'Картхолдер',
                'icon': 'fa-credit-card',
                'order': 17
            },
            {
                'name': 'Roblox ТОП',
                'icon': 'fa-robot',
                'order': 18,
                'is_featured': True
            },
            {
                'name': 'Gold Standoff',
                'icon': 'fa-gun',
                'order': 19,
                'is_featured': True
            },
            {
                'name': 'Steam DOTA TOP',
                'icon': 'fa-gamepad',
                'order': 20,
                'is_featured': True
            },
            {
                'name': 'Значки',
                'icon': 'fa-circle-check',
                'order': 21
            },
            {
                'name': 'Зарядный аккумулятор',
                'icon': 'fa-battery-full',
                'order': 22
            },
            {
                'name': 'Бэйджи школьные',
                'icon': 'fa-id-card',
                'order': 23
            },
        ]

        for category_data in categories:
            name = category_data['name']
            ProductCategory.objects.get_or_create(
                slug=slugify(name),
                defaults={
                    'name': name,
                    'icon': category_data['icon'],
                    'order': category_data['order'],
                    'is_featured': category_data.get('is_featured', False)
                }
            )

        self.stdout.write(self.style.SUCCESS('Successfully created product categories'))