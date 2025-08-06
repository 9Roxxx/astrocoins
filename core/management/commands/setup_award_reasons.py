from django.core.management.base import BaseCommand
from core.models import AwardReason

class Command(BaseCommand):
    help = 'Creates default award reasons'

    def handle(self, *args, **options):
        reasons = [
            {
                'name': 'Подарок на день рождения',
                'coins': 100,
                'cooldown_days': 365,  # Раз в год
                'is_special': True
            },
            {
                'name': 'Стань помощником педагога на занятии',
                'coins': 10,
                'cooldown_days': 7,  # Раз в неделю
                'is_special': False
            },
            {
                'name': 'Выполняй задания учителя на уроке + соблюдай дисциплину',
                'coins': 10,
                'cooldown_days': 1,  # Каждый день
                'is_special': False
            },
            {
                'name': 'Дополнительный бонус от учителя',
                'coins': 10,
                'cooldown_days': 14,  # Не чаще раза в 2 недели
                'is_special': False
            },
            {
                'name': 'Выполняй задания дома (за весь модуль)',
                'coins': 30,
                'cooldown_days': 30,  # Примерно раз в месяц
                'is_special': False
            },
            {
                'name': 'Участвуй в интенсиве',
                'coins': 100,
                'cooldown_days': 0,  # Без ограничений
                'is_special': True
            },
            {
                'name': 'Переход на следующий год обучения',
                'coins': 100,
                'cooldown_days': 365,  # Раз в год
                'is_special': True
            },
            {
                'name': 'Спасибо за отзыв',
                'coins': 30,
                'cooldown_days': 30,  # Раз в месяц
                'is_special': False
            },
            {
                'name': 'Спасибо за друга',
                'coins': 100,
                'cooldown_days': 0,  # Без ограничений
                'is_special': True
            },
            {
                'name': 'Создание индивидуального проекта',
                'coins': 50,
                'cooldown_days': 0,  # Без ограничений
                'is_special': True
            },
            {
                'name': 'Подарок на Новый год',
                'coins': 100,
                'cooldown_days': 365,  # Раз в год
                'is_special': True
            },
            {
                'name': 'Отсутствие пропусков (4 занятия)',
                'coins': 20,
                'cooldown_days': 28,  # Примерно раз в месяц
                'is_special': False
            },
        ]

        for reason_data in reasons:
            AwardReason.objects.get_or_create(
                name=reason_data['name'],
                defaults={
                    'coins': reason_data['coins'],
                    'cooldown_days': reason_data['cooldown_days'],
                    'is_special': reason_data['is_special']
                }
            )

        self.stdout.write(self.style.SUCCESS('Successfully created award reasons'))