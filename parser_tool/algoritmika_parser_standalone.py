#!/usr/bin/env python3
"""
Standalone парсер для algoritmika25.ru (без подключения к Django БД)
Только извлекает и выводит данные в JSON формате
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, date
import time
import re


class AlgoritmikaParserStandalone:
    """Standalone парсер для algoritmika25.ru"""
    
    def __init__(self, base_url="https://algoritmika25.ru"):
        self.base_url = base_url
        
        # Создаем сессию для сохранения cookies
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
        
        # Данные для экспорта (упрощенная структура)
        self.parsed_data = {
            'students': [],  # имя, фамилия, логин, пароль, баланс, группа
            'groups': [],    # названия групп
            'summary': {
                'total_students': 0,
                'total_groups': 0,
                'export_date': None
            }
        }

    def login(self, email, password):
        """Авторизация на сайте"""
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
            if response.status_code == 200 and '/admin' in response.url:
                print(f"✅ Успешная авторизация для {email}")
                return True
            else:
                print(f"❌ Ошибка HTTP: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка авторизации: {e}")
            return False

    def parse_groups(self, city_filter=None):
        """Парсинг групп со старого сайта"""
        try:
            print(f"📚 Начинаем парсинг групп...")
            
            # Получаем страницу с группами
            response = self.session.get(self.groups_url)
            print(f"📄 Получена страница групп: {response.status_code}")
            
            # Сохраняем HTML для анализа
            with open('debug_groups_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("💾 HTML сохранен в debug_groups_page.html")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ищем структуру с группами
            groups_found = []
            students_found = []
            courses_found = set()
            
            # Вариант 1: Ищем таблицы
            tables = soup.find_all('table')
            print(f"🔍 Найдено таблиц: {len(tables)}")
            
            for i, table in enumerate(tables):
                print(f"📊 Анализ таблицы {i+1}:")
                rows = table.find_all('tr')
                print(f"   - Строк: {len(rows)}")
                
                if len(rows) > 1:  # Есть данные кроме заголовка
                    headers = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])]
                    print(f"   - Заголовки: {headers}")
                    
                    # Проверяем содержимое первых нескольких строк
                    for j, row in enumerate(rows[1:6]):  # Первые 5 строк данных
                        cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                        if any(cells):  # Если строка не пустая
                            print(f"   - Строка {j+1}: {cells}")
                    
                    # Если это таблица со студентами (есть ID, ФИО, Группы)
                    if len(headers) >= 3 and any(h in ['ID', 'ФИО', 'Группы'] for h in headers):
                        print(f"✅ Найдена таблица студентов!")
                        
                        # Извлекаем всех студентов
                        for j, row in enumerate(rows[1:]):  # Пропускаем заголовок
                            cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                            
                            if len(cells) >= 3 and cells[0] and cells[1]:  # ID и ФИО не пустые
                                student_id = cells[0]
                                full_name = cells[1]
                                group_name = cells[2] if len(cells) > 2 else ""
                                
                                # Разбираем ФИО
                                name_parts = full_name.strip().split()
                                if len(name_parts) >= 2:
                                    first_name = name_parts[1]  # Имя
                                    last_name = name_parts[0]   # Фамилия
                                    middle_name = name_parts[2] if len(name_parts) > 2 else ""
                                else:
                                    first_name = full_name
                                    last_name = ""
                                    middle_name = ""
                                
                                # Генерируем логин и пароль (если они не извлекаются напрямую)
                                # Логин: имя.фамилия (латиницей)
                                login = self.transliterate_name(first_name, last_name)
                                password = "123456"  # Временный пароль, позже можно улучшить
                                
                                # Извлекаем баланс из данных астрокоинов (если есть)
                                balance = self.extract_balance_from_coins_data(cells)
                                
                                student_data = {
                                    'id': student_id,
                                    'first_name': first_name,
                                    'last_name': last_name,
                                    'login': login,
                                    'password': password,
                                    'balance': balance,
                                    'group_name': group_name,
                                    'full_name': full_name  # Оставляем для отладки
                                }
                                
                                students_found.append(student_data)
                                
                                # Добавляем группу в список курсов
                                if group_name:
                                    courses_found.add(group_name)
                        
                        print(f"📚 Извлечено студентов: {len(students_found)}")
                        print(f"📚 Найдено уникальных групп: {len(courses_found)}")
                        
                        # Показываем примеры
                        print(f"👨‍🎓 Примеры студентов:")
                        for student in students_found[:3]:
                            print(f"   - {student['full_name']} → {student['group_name']}")
                        
                        print(f"📖 Примеры групп:")
                        for course in list(courses_found)[:5]:
                            print(f"   - {course}")
                        
                        # Сохраняем данные
                        self.parsed_data['students'] = students_found
                        self.parsed_data['groups'] = list(courses_found)
                        self.parsed_data['summary'] = {
                            'total_students': len(students_found),
                            'total_groups': len(courses_found),
                            'export_date': datetime.now().isoformat()
                        }
                        groups_found = list(courses_found)
            
            # Вариант 2: Ищем карточки или блоки
            cards = soup.find_all(['div'], class_=re.compile(r'card|group|class|item', re.I))
            print(f"🔍 Найдено карточек/блоков: {len(cards)}")
            
            for i, card in enumerate(cards[:5]):  # Первые 5 для анализа
                text = card.get_text(strip=True)[:100]  # Первые 100 символов
                if text:
                    print(f"   - Карточка {i+1}: {text}...")
            
            # Вариант 3: Ищем списки
            lists = soup.find_all(['ul', 'ol'])
            print(f"🔍 Найдено списков: {len(lists)}")
            
            for i, ul in enumerate(lists[:3]):  # Первые 3 для анализа
                items = ul.find_all('li')
                if len(items) > 2:  # Только содержательные списки
                    print(f"   - Список {i+1}: {len(items)} элементов")
                    for j, li in enumerate(items[:3]):  # Первые 3 элемента
                        text = li.get_text(strip=True)[:50]
                        if text:
                            print(f"     * {text}...")
            
            # Вариант 4: Поиск по ключевым словам
            text_content = soup.get_text()
            keywords = ['группа', 'класс', 'ученик', 'студент', 'курс', 'преподаватель']
            
            print(f"🔍 Поиск ключевых слов в тексте:")
            for keyword in keywords:
                count = text_content.lower().count(keyword.lower())
                if count > 0:
                    print(f"   - '{keyword}': {count} упоминаний")
            
            # Сохраняем результат
            self.parsed_data['groups'] = groups_found
            
            if groups_found:
                print(f"✅ Найдено групп: {len(groups_found)}")
                return groups_found
            else:
                print("❌ Группы не найдены")
                return []
                
        except Exception as e:
            print(f"❌ Ошибка при парсинге групп: {e}")
            return []

    def export_to_json(self, filename=None):
        """Экспорт данных в JSON"""
        if filename is None:
            filename = f"algoritmika_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.parsed_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"💾 Данные экспортированы в {filename}")
            return filename
        except Exception as e:
            print(f"❌ Ошибка экспорта: {e}")
            return None

    def transliterate_name(self, first_name, last_name):
        """Транслитерация имени для создания логина"""
        translit_map = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
        }
        
        def transliterate_word(word):
            result = ""
            for char in word.lower():
                result += translit_map.get(char, char)
            return result
        
        first_translit = transliterate_word(first_name)
        last_translit = transliterate_word(last_name)
        
        # Создаем логин: имя.фамилия
        login = f"{first_translit}.{last_translit}".lower()
        
        # Убираем недопустимые символы
        login = re.sub(r'[^a-z0-9.]', '', login)
        
        return login[:50]  # Ограничиваем длину
    
    def extract_balance_from_coins_data(self, cells):
        """Извлекает текущий баланс астрокоинов из данных ячейки"""
        try:
            # В 4-й и 5-й колонках могут быть данные об астрокоинах
            coins_data = ""
            if len(cells) > 3:
                coins_data += cells[3] + " "
            if len(cells) > 4:
                coins_data += cells[4]
            
            # Ищем числа с "коинов" или "астрокоинов"
            # Пока возвращаем 0, позже можно улучшить парсинг
            balance = 0
            
            # Простой поиск чисел перед словом "коинов"
            import re
            matches = re.findall(r'(\d+)\s*коинов', coins_data)
            if matches:
                # Берем последнее найденное значение как текущий баланс
                balance = int(matches[-1])
            
            return balance
            
        except Exception as e:
            print(f"⚠️ Ошибка при извлечении баланса: {e}")
            return 0

    def get_debug_info(self):
        """Получить отладочную информацию"""
        return {
            'base_url': self.base_url,
            'login_url': self.login_url,
            'groups_url': self.groups_url,
            'session_cookies': dict(self.session.cookies),
            'parsed_counts': {
                'students': len(self.parsed_data['students']),
                'groups': len(self.parsed_data['groups']),
            },
            'summary': self.parsed_data['summary']
        }


def main():
    """Главная функция для тестирования"""
    parser = AlgoritmikaParserStandalone()
    
    print("🔄 Standalone парсер algoritmika25.ru")
    print("=" * 40)
    
    # Тест авторизации
    email = input("Введите email учителя: ").strip()
    password = input("Введите пароль: ").strip()
    
    if parser.login(email, password):
        print("\n✅ Авторизация успешна!")
        
        # Тест парсинга групп
        city = input("Введите город (или Enter для всех): ").strip()
        city_filter = city if city else None
        
        groups = parser.parse_groups(city_filter)
        
        # Экспорт данных
        if groups or True:  # Экспортируем в любом случае для анализа
            filename = parser.export_to_json()
            print(f"\n📄 Результаты сохранены в {filename}")
        
        # Отладочная информация
        debug_info = parser.get_debug_info()
        print(f"\n🔍 Отладочная информация:")
        print(json.dumps(debug_info, ensure_ascii=False, indent=2))
        
    else:
        print("\n❌ Авторизация не удалась")


if __name__ == "__main__":
    main()
