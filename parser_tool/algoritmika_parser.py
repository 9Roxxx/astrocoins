#!/usr/bin/env python3
"""
Парсер для переноса данных с algoritmika25.ru в новую систему
"""

import os
import sys
import django
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, date
import time

# Добавляем путь к Django проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'astrocoins.settings')
django.setup()

# Импортируем модели Django
from core.models import User, Group, City, School, Course, Parent, Profile
from django.contrib.auth.hashers import make_password
from django.db import transaction


class AlgoritmikaParser:
    """Парсер для algoritmika25.ru"""
    
    def __init__(self, base_url="https://algoritmika25.ru"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # URLs для старого сайта
        self.login_url = f"{self.base_url}/login"  # Авторизация через /login
        self.groups_url = f"{self.base_url}/admin"  # После входа переходим в /admin для групп
        
        # Настройки для сопоставления
        self.city_mapping = {
            # Будем определять города по именам учителей или группам
            'default': 'Владивосток'  # Город по умолчанию
        }
        
        # Статистика парсинга
        self.stats = {
            'teachers': 0,
            'students': 0,
            'groups': 0,
            'parents': 0,
            'errors': []
        }
    
    def login(self, email, password):
        """Авторизация на старом сайте через email"""
        try:
            print(f"🔐 Авторизация для {email}...")
            
            # Получаем страницу входа
            login_page = self.session.get(self.login_url)
            soup = BeautifulSoup(login_page.content, 'html.parser')
            
            # Извлекаем CSRF токен (Laravel использует _token)
            csrf_token = soup.find('input', {'name': '_token'})
            if csrf_token:
                csrf_token = csrf_token.get('value')
                print(f"🔑 Найден _token: {csrf_token[:20]}...")
            else:
                print("⚠️ _token не найден")
            
            # Ищем форму входа и её поля
            form = soup.find('form')
            if form:
                print(f"📝 Найдена форма входа")
                # Выводим все поля формы для отладки
                inputs = form.find_all('input')
                print(f"🔍 Поля формы:")
                for inp in inputs:
                    name = inp.get('name', 'Без имени')
                    input_type = inp.get('type', 'text')
                    placeholder = inp.get('placeholder', '')
                    print(f"   - {name} (type: {input_type}) placeholder: '{placeholder}'")
            
            # Сохраняем HTML формы для анализа
            with open('debug_login_form.html', 'w', encoding='utf-8') as f:
                f.write(login_page.text)
            print("💾 HTML формы сохранен в debug_login_form.html")
            
            # Данные для входа (используем реальную структуру)
            login_data = {
                'login': email,  # Поле login принимает email
                'password': password,
            }
            
            # Добавляем Laravel CSRF токен
            if csrf_token:
                login_data['_token'] = csrf_token
            else:
                print("⚠️ Отправляем без CSRF токена")
            
            print(f"📤 Отправляем данные авторизации:")
            for key, value in login_data.items():
                if key == 'password':
                    print(f"   - {key}: {'*' * len(str(value))}")
                else:
                    print(f"   - {key}: {value}")
            
            # Выполняем вход
            response = self.session.post(self.login_url, data=login_data, allow_redirects=True)
            
            print(f"📥 Получен ответ: {response.status_code}")
            print(f"🔗 URL после входа: {response.url}")
            
            # Проверяем успешность входа
            if response.status_code == 200:
                # Проверяем содержимое страницы после входа
                if 'группы' in response.text.lower() or 'groups' in response.text.lower():
                    print(f"✅ Успешная авторизация для {email}")
                    return True
                elif 'error' in response.text.lower() or 'ошибка' in response.text.lower():
                    print(f"❌ Ошибка авторизации: неверные данные")
                    return False
                else:
                    print(f"⚠️ Возможна успешная авторизация, проверяем...")
                    return True
            else:
                print(f"❌ Ошибка HTTP: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка при авторизации: {str(e)}")
            self.stats['errors'].append(f"Login error: {str(e)}")
            return False
    
    def get_or_create_city(self, city_name):
        """Получить или создать город"""
        city, created = City.objects.get_or_create(
            name=city_name,
            defaults={'description': f'Город {city_name}'}
        )
        if created:
            print(f"✅ Создан город: {city_name}")
        return city
    
    def get_or_create_school(self, school_name, city):
        """Получить или создать школу"""
        school, created = School.objects.get_or_create(
            name=school_name,
            city=city,
            defaults={
                'director': 'Не указан',
                'address': f'{city.name}, точный адрес не указан',
                'phone': 'Не указан'
            }
        )
        if created:
            print(f"✅ Создана школа: {school_name} в городе {city.name}")
        return school
    
    def parse_groups(self, teacher_city_name="Владивосток"):
        """Парсинг групп преподавателя"""
        try:
            print("\n📚 Начинаем парсинг групп...")
            
            # Используем текущую сессию (уже авторизованы)
            # После входа на /admin уже должны быть группы
            groups_page = self.session.get(self.groups_url)
            
            print(f"📄 Получена страница групп: {groups_page.status_code}")
            
            # Сохраняем HTML для отладки
            with open('debug_groups_page.html', 'w', encoding='utf-8') as f:
                f.write(groups_page.text)
            print("💾 HTML сохранен в debug_groups_page.html")
            
            soup = BeautifulSoup(groups_page.content, 'html.parser')
            city = self.get_or_create_city(teacher_city_name)
            
            # Ищем группы на странице - пробуем разные селекторы
            group_elements = []
            
            # Попытка 1: ищем по классам связанным с группами
            possible_selectors = [
                'div.group-item',
                'div.group-card', 
                'div.group',
                '.group',
                'tr.group',
                'li.group',
                # Общие селекторы
                'div[class*="group"]',
                'div[class*="класс"]',
                'div[class*="lesson"]',
                'tr[class*="group"]'
            ]
            
            for selector in possible_selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"🎯 Найдены элементы по селектору: {selector} ({len(elements)} шт.)")
                    group_elements = elements
                    break
            
            if not group_elements:
                # Ищем таблицы или списки
                tables = soup.find_all('table')
                if tables:
                    print(f"📊 Найдено таблиц: {len(tables)}")
                    # Берем самую большую таблицу
                    biggest_table = max(tables, key=lambda t: len(t.find_all('tr')))
                    group_elements = biggest_table.find_all('tr')[1:]  # Пропускаем заголовок
                    print(f"📋 Используем таблицу с {len(group_elements)} строками")
                
                if not group_elements:
                    # Ищем любые списки
                    lists = soup.find_all(['ul', 'ol'])
                    for ul in lists:
                        items = ul.find_all('li')
                        if len(items) > 2:  # Если в списке больше 2 элементов
                            group_elements = items
                            print(f"📝 Используем список с {len(items)} элементами")
                            break
            
            if not group_elements:
                print("⚠️ Группы не найдены. Анализируем HTML...")
                # Выводим структуру страницы для анализа
                titles = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                print("📋 Заголовки на странице:")
                for title in titles[:10]:  # Первые 10 заголовков
                    print(f"   - {title.name}: {title.get_text(strip=True)}")
                
                # Ищем слова связанные с группами
                text = soup.get_text().lower()
                group_keywords = ['группа', 'класс', 'курс', 'урок', 'занятие']
                found_keywords = [kw for kw in group_keywords if kw in text]
                if found_keywords:
                    print(f"🔍 Найдены ключевые слова: {found_keywords}")
                
                return []
            
            groups_data = []
            for group_elem in group_elements:
                try:
                    # Извлекаем данные группы (адаптируйте под реальную структуру)
                    group_name = group_elem.find('h6')  # Адаптируйте селектор
                    if group_name:
                        group_name = group_name.text.strip()
                        
                        group_data = {
                            'name': group_name,
                            'city': city,
                            'students': []
                        }
                        
                        # Ищем учеников в группе
                        students = group_elem.find_all('span', class_='student-name')  # Адаптируйте
                        for student_elem in students:
                            student_name = student_elem.text.strip()
                            group_data['students'].append(student_name)
                        
                        groups_data.append(group_data)
                        print(f"📋 Найдена группа: {group_name} ({len(group_data['students'])} учеников)")
                        
                except Exception as e:
                    print(f"⚠️ Ошибка при парсинге группы: {str(e)}")
                    self.stats['errors'].append(f"Group parsing error: {str(e)}")
            
            return groups_data
            
        except Exception as e:
            print(f"❌ Ошибка при парсинге групп: {str(e)}")
            self.stats['errors'].append(f"Groups parsing error: {str(e)}")
            return []
    
    def parse_students(self, group_name=None):
        """Парсинг учеников"""
        try:
            print("\n👥 Начинаем парсинг учеников...")
            
            # Получаем страницу с учениками
            students_page = self.session.get(f"{self.base_url}/user-management/")  # Адаптируйте URL
            soup = BeautifulSoup(students_page.content, 'html.parser')
            
            # Ищем учеников (адаптируйте селекторы)
            student_elements = soup.find_all('div', class_='student-item')
            
            students_data = []
            for student_elem in student_elements:
                try:
                    # Извлекаем данные ученика
                    name_elem = student_elem.find('h6')
                    email_elem = student_elem.find('small')
                    
                    if name_elem:
                        full_name = name_elem.text.strip()
                        email = email_elem.text.strip() if email_elem else ""
                        
                        student_data = {
                            'full_name': full_name,
                            'email': email,
                            'group': group_name
                        }
                        
                        students_data.append(student_data)
                        print(f"👤 Найден ученик: {full_name}")
                        
                except Exception as e:
                    print(f"⚠️ Ошибка при парсинге ученика: {str(e)}")
            
            return students_data
            
        except Exception as e:
            print(f"❌ Ошибка при парсинге учеников: {str(e)}")
            self.stats['errors'].append(f"Students parsing error: {str(e)}")
            return []
    
    def create_users_in_database(self, teacher_username, teacher_city, groups_data):
        """Создание пользователей в новой базе данных"""
        try:
            print(f"\n💾 Создаем пользователей в базе данных...")
            
            city = self.get_or_create_city(teacher_city)
            
            with transaction.atomic():
                # Создаем или находим учителя
                teacher, created = User.objects.get_or_create(
                    username=teacher_username,
                    defaults={
                        'role': 'teacher',
                        'city': city,
                        'email': f'{teacher_username}@{teacher_city.lower()}.ru',
                        'password': make_password('временный_пароль_123')
                    }
                )
                
                if created:
                    print(f"✅ Создан учитель: {teacher_username}")
                    # Создаем профиль
                    Profile.objects.get_or_create(user=teacher, defaults={'astrocoins': 1000})
                    # Добавляем город в cities (ManyToMany)
                    teacher.cities.add(city)
                
                # Создаем школу по умолчанию
                school = self.get_or_create_school(f"Школа {teacher_city}", city)
                
                # Создаем курс по умолчанию
                course, _ = Course.objects.get_or_create(
                    name="Программирование",
                    defaults={'description': 'Базовый курс программирования'}
                )
                
                # Создаем группы и учеников
                for group_data in groups_data:
                    # Создаем группу
                    group, created = Group.objects.get_or_create(
                        name=group_data['name'],
                        defaults={
                            'teacher': teacher,
                            'school': school,
                            'course': course,
                            'is_active': True
                        }
                    )
                    
                    if created:
                        print(f"✅ Создана группа: {group_data['name']}")
                        self.stats['groups'] += 1
                    
                    # Создаем учеников
                    for student_name in group_data['students']:
                        # Генерируем username из имени
                        username = self.generate_username(student_name)
                        
                        student, created = User.objects.get_or_create(
                            username=username,
                            defaults={
                                'role': 'student',
                                'city': city,
                                'group': group,
                                'first_name': student_name.split()[1] if len(student_name.split()) > 1 else '',
                                'last_name': student_name.split()[0] if student_name.split() else student_name,
                                'email': f'{username}@student.{teacher_city.lower()}.ru',
                                'password': make_password('ученик123')
                            }
                        )
                        
                        if created:
                            print(f"✅ Создан ученик: {student_name} (username: {username})")
                            # Создаем профиль
                            Profile.objects.get_or_create(user=student, defaults={'astrocoins': 0})
                            self.stats['students'] += 1
                
                print(f"\n🎉 Импорт завершен!")
                print(f"📊 Статистика:")
                print(f"   - Групп: {self.stats['groups']}")
                print(f"   - Учеников: {self.stats['students']}")
                
        except Exception as e:
            print(f"❌ Ошибка при создании пользователей: {str(e)}")
            self.stats['errors'].append(f"Database creation error: {str(e)}")
    
    def generate_username(self, full_name):
        """Генерация username из полного имени"""
        # Транслитерация и очистка
        name_parts = full_name.lower().replace(' ', '_').replace('.', '')
        # Ограничиваем длину
        username = name_parts[:20] if len(name_parts) > 20 else name_parts
        
        # Проверяем уникальность
        counter = 1
        original_username = username
        while User.objects.filter(username=username).exists():
            username = f"{original_username}_{counter}"
            counter += 1
            
        return username
    
    def run_full_import(self, teacher_email, teacher_password, teacher_city):
        """Полный импорт данных"""
        print(f"🚀 Начинаем импорт данных для учителя {teacher_email} из города {teacher_city}")
        
        # Авторизация
        if not self.login(teacher_email, teacher_password):
            return False
        
        # Парсинг групп
        groups_data = self.parse_groups(teacher_city)
        
        if not groups_data:
            print("❌ Нет данных для импорта")
            return False
        
        # Создание в базе данных  
        # Извлекаем username из email для создания в БД
        teacher_username = teacher_email.split('@')[0]
        self.create_users_in_database(teacher_username, teacher_city, groups_data)
        
        # Выводим ошибки если есть
        if self.stats['errors']:
            print(f"\n⚠️ Обнаружены ошибки ({len(self.stats['errors'])}):")
            for error in self.stats['errors']:
                print(f"   - {error}")
        
        return True


if __name__ == "__main__":
    # Пример использования
    parser = AlgoritmikaParser()
    
    # Данные для импорта
    TEACHER_EMAIL = "depressed7kk1d@vk.com"
    TEACHER_PASSWORD = "123456"
    TEACHER_CITY = "Владивосток"
    
    # Запуск импорта
    success = parser.run_full_import(TEACHER_EMAIL, TEACHER_PASSWORD, TEACHER_CITY)
    
    if success:
        print("\n✅ Импорт завершен успешно!")
    else:
        print("\n❌ Импорт завершен с ошибками")
