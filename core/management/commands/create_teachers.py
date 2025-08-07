from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Создает тестовых преподавателей для системы'

    def handle(self, *args, **options):
        teachers_data = [
            {
                'username': 'teacher1',
                'first_name': 'Анна',
                'last_name': 'Иванова',
                'email': 'teacher1@example.com',
                'role': 'teacher'
            },
            {
                'username': 'teacher2', 
                'first_name': 'Петр',
                'last_name': 'Смирнов',
                'email': 'teacher2@example.com',
                'role': 'teacher'
            },
            {
                'username': 'teacher3',
                'first_name': 'Елена',
                'last_name': 'Козлова', 
                'email': 'teacher3@example.com',
                'role': 'teacher'
            }
        ]
        
        created_count = 0
        
        with transaction.atomic():
            for teacher_data in teachers_data:
                user, created = User.objects.get_or_create(
                    username=teacher_data['username'],
                    defaults={
                        'first_name': teacher_data['first_name'],
                        'last_name': teacher_data['last_name'],
                        'email': teacher_data['email'],
                        'role': teacher_data['role'],
                        'is_active': True
                    }
                )
                
                if created:
                    # Устанавливаем простой пароль для тестирования
                    user.set_password('teacher123')
                    user.save()
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Создан преподаватель: {user.get_full_name()} ({user.username})'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Преподаватель уже существует: {user.get_full_name()} ({user.username})'
                        )
                    )
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Создано {created_count} новых преподавателей'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    'Пароль для всех преподавателей: teacher123'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Все преподаватели уже существуют в системе'
                )
            )