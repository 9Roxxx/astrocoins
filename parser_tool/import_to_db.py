#!/usr/bin/env python3
"""
Скрипт для импорта данных из JSON в Django БД
"""

import os
import sys
import django
import json
from datetime import datetime

# Добавляем путь к Django проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'astrocoins.settings')
django.setup()

# Импортируем модели Django
from core.models import User, Group, City, School, Course, Parent, Profile
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()

class DatabaseImporter:
    """Импортер данных в Django БД"""
    
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self.data = None
        self.teacher_user = None  # AlexanderX
        self.curator_user = None  # adminVld
        self.default_city = None
        self.default_school = None
        
        # Статистика
        self.stats = {
            'groups_created': 0,
            'courses_created': 0,
            'students_created': 0,
            'students_updated': 0,
            'errors': []
        }
    
    def load_json_data(self):
        """Загружает данные из JSON файла"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            print(f"📄 Загружен JSON файл: {self.json_file_path}")
            print(f"📊 Студентов: {len(self.data.get('students', []))}")
            print(f"📊 Групп: {len(self.data.get('groups', []))}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка загрузки JSON: {e}")
            return False
    
    def setup_basic_data(self):
        """Настраивает базовые данные: город, школу, пользователей"""
        try:
            # Находим/создаем город
            self.default_city, created = City.objects.get_or_create(
                name="Владивосток",
                defaults={'description': 'Город Владивосток'}
            )
            if created:
                print(f"🏙️ Создан город: {self.default_city.name}")
            else:
                print(f"🏙️ Найден город: {self.default_city.name}")
            
            # Находим/создаем школу
            self.default_school, created = School.objects.get_or_create(
                name="Алгоритмика Владивосток",
                city=self.default_city,
                defaults={
                    'address': 'Владивосток',
                    'description': 'Школа программирования Алгоритмика'
                }
            )
            if created:
                print(f"🏫 Создана школа: {self.default_school.name}")
            else:
                print(f"🏫 Найдена школа: {self.default_school.name}")
            
            # Находим преподавателя AlexanderX
            try:
                self.teacher_user = User.objects.get(username='AlexanderX')
                print(f"👨‍🏫 Найден преподаватель: {self.teacher_user.username}")
            except User.DoesNotExist:
                print(f"❌ Преподаватель AlexanderX не найден в БД")
                return False
            
            # Находим куратора adminVld
            try:
                self.curator_user = User.objects.get(username='adminVld')
                print(f"👨‍💼 Найден куратор: {self.curator_user.username}")
            except User.DoesNotExist:
                print(f"❌ Куратор adminVld не найден в БД")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка настройки базовых данных: {e}")
            self.stats['errors'].append(f"Setup error: {e}")
            return False
    
    def create_courses_and_groups(self):
        """Создает курсы и группы из JSON данных"""
        try:
            print(f"\n📚 Создание курсов и групп...")
            
            unique_groups = self.data.get('groups', [])
            
            for group_name in unique_groups:
                try:
                    # Создаем курс для каждой уникальной группы
                    course, created = Course.objects.get_or_create(
                        name=group_name,
                        defaults={
                            'description': f'Курс {group_name}',
                            'duration_weeks': 36,  # Учебный год
                            'price': 5000,  # Примерная цена
                            'max_students': 12
                        }
                    )
                    
                    if created:
                        print(f"📖 Создан курс: {course.name}")
                        self.stats['courses_created'] += 1
                    else:
                        print(f"📖 Найден курс: {course.name}")
                    
                    # Создаем группу для курса
                    group, created = Group.objects.get_or_create(
                        name=group_name,
                        course=course,
                        defaults={
                            'school': self.default_school,
                            'teacher': self.teacher_user,
                            'curator': self.curator_user,
                            'start_date': datetime.now().date(),
                            'max_students': 12,
                            'is_active': True
                        }
                    )
                    
                    if created:
                        print(f"👥 Создана группа: {group.name}")
                        self.stats['groups_created'] += 1
                    else:
                        print(f"👥 Найдена группа: {group.name}")
                        # Обновляем преподавателя и куратора если нужно
                        if group.teacher != self.teacher_user:
                            group.teacher = self.teacher_user
                        if group.curator != self.curator_user:
                            group.curator = self.curator_user
                        group.save()
                
                except Exception as e:
                    error_msg = f"Ошибка создания группы {group_name}: {e}"
                    print(f"❌ {error_msg}")
                    self.stats['errors'].append(error_msg)
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка создания курсов и групп: {e}")
            self.stats['errors'].append(f"Courses/Groups error: {e}")
            return False
    
    def create_students(self):
        """Создает студентов из JSON данных"""
        try:
            print(f"\n👨‍🎓 Создание студентов...")
            
            students_data = self.data.get('students', [])
            
            for student_data in students_data:
                try:
                    first_name = student_data.get('first_name', '').strip()
                    last_name = student_data.get('last_name', '').strip()
                    login = student_data.get('login', '').strip()
                    password = student_data.get('password', '123456')
                    balance = student_data.get('balance', 0)
                    group_name = student_data.get('group_name', '').strip()
                    
                    if not first_name or not last_name or not login:
                        print(f"⚠️ Пропускаем студента с неполными данными: {student_data}")
                        continue
                    
                    # Находим группу для студента
                    try:
                        group = Group.objects.get(name=group_name)
                    except Group.DoesNotExist:
                        print(f"❌ Группа {group_name} не найдена для студента {first_name} {last_name}")
                        continue
                    
                    # Создаем/обновляем пользователя-студента
                    user, created = User.objects.get_or_create(
                        username=login,
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name,
                            'email': f"{login}@algoritmika.local",
                            'password': make_password(password),
                            'is_active': True,
                            'user_type': 'student'
                        }
                    )
                    
                    if created:
                        print(f"👤 Создан пользователь: {user.username}")
                        self.stats['students_created'] += 1
                    else:
                        # Обновляем данные если пользователь уже существует
                        user.first_name = first_name
                        user.last_name = last_name
                        user.user_type = 'student'
                        user.save()
                        print(f"👤 Обновлен пользователь: {user.username}")
                        self.stats['students_updated'] += 1
                    
                    # Создаем/обновляем профиль студента
                    profile, created = Profile.objects.get_or_create(
                        user=user,
                        defaults={
                            'balance': balance,
                            'city': self.default_city,
                            'school': self.default_school
                        }
                    )
                    
                    if not created:
                        # Обновляем баланс
                        profile.balance = balance
                        profile.city = self.default_city
                        profile.school = self.default_school
                        profile.save()
                    
                    # Добавляем студента в группу
                    if user not in group.students.all():
                        group.students.add(user)
                        print(f"  ✅ Добавлен в группу: {group.name}")
                
                except Exception as e:
                    error_msg = f"Ошибка создания студента {student_data}: {e}"
                    print(f"❌ {error_msg}")
                    self.stats['errors'].append(error_msg)
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка создания студентов: {e}")
            self.stats['errors'].append(f"Students error: {e}")
            return False
    
    def print_statistics(self):
        """Выводит статистику импорта"""
        print(f"\n📊 Статистика импорта:")
        print(f"   📖 Курсов создано: {self.stats['courses_created']}")
        print(f"   👥 Групп создано: {self.stats['groups_created']}")
        print(f"   👨‍🎓 Студентов создано: {self.stats['students_created']}")
        print(f"   👤 Студентов обновлено: {self.stats['students_updated']}")
        
        if self.stats['errors']:
            print(f"\n❌ Ошибки ({len(self.stats['errors'])}):")
            for error in self.stats['errors'][:5]:  # Показываем первые 5 ошибок
                print(f"   - {error}")
            if len(self.stats['errors']) > 5:
                print(f"   ... и еще {len(self.stats['errors']) - 5} ошибок")
        else:
            print(f"\n✅ Импорт завершен без ошибок!")
    
    def run_import(self):
        """Запускает полный импорт данных"""
        print(f"🚀 Начинаем импорт данных в Django БД...")
        print(f"=" * 50)
        
        # Загружаем JSON
        if not self.load_json_data():
            return False
        
        # Настраиваем базовые данные
        if not self.setup_basic_data():
            return False
        
        # Используем транзакцию для атомарности
        try:
            with transaction.atomic():
                # Создаем курсы и группы
                if not self.create_courses_and_groups():
                    raise Exception("Ошибка создания курсов и групп")
                
                # Создаем студентов
                if not self.create_students():
                    raise Exception("Ошибка создания студентов")
                
                print(f"\n✅ Импорт завершен успешно!")
                self.print_statistics()
                return True
                
        except Exception as e:
            print(f"❌ Ошибка импорта (транзакция отменена): {e}")
            self.stats['errors'].append(f"Transaction error: {e}")
            self.print_statistics()
            return False


def main():
    """Главная функция"""
    import glob
    
    # Ищем последний JSON файл
    json_files = glob.glob("algoritmika_data_*.json")
    if not json_files:
        print("❌ JSON файлы не найдены. Сначала запустите парсер.")
        return
    
    # Берем самый свежий файл
    latest_file = max(json_files, key=os.path.getctime)
    print(f"📄 Используем файл: {latest_file}")
    
    # Подтверждение
    confirm = input(f"\n❓ Импортировать данные из {latest_file} в базу данных? (y/N): ")
    if confirm.lower() not in ['y', 'yes', 'да']:
        print("❌ Импорт отменен")
        return
    
    # Запускаем импорт
    importer = DatabaseImporter(latest_file)
    success = importer.run_import()
    
    if success:
        print(f"\n🎉 Импорт завершен успешно!")
        print(f"\n📋 Следующие шаги:")
        print(f"1. Проверьте созданные группы в админке")
        print(f"2. Проверьте студентов и их баланс")
        print(f"3. При необходимости скорректируйте данные")
    else:
        print(f"\n❌ Импорт завершен с ошибками")


if __name__ == "__main__":
    main()
