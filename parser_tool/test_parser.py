#!/usr/bin/env python3
"""
Тестовый скрипт для парсера algoritmika25.ru
"""

try:
    from algoritmika_parser_standalone import AlgoritmikaParserStandalone as AlgoritmikaParser
    print("🔧 Используем standalone версию парсера (без Django)")
except ImportError:
    from algoritmika_parser import AlgoritmikaParser
    print("🔧 Используем полную версию парсера (с Django)")

def test_login():
    """Тест авторизации"""
    print("🔐 Тестируем авторизацию...")
    
    # Данные по умолчанию
    default_email = "depressed7kk1d@vk.com"
    default_password = "123456"
    
    email = input(f"Введите email учителя ({default_email}): ").strip()
    if not email:
        email = default_email
        
    password = input(f"Введите пароль ({default_password}): ").strip()
    if not password:
        password = default_password
    
    parser = AlgoritmikaParser()
    success = parser.login(email, password)
    
    if success:
        print("✅ Авторизация успешна!")
        return parser, email, password
    else:
        print("❌ Ошибка авторизации")
        return None, None, None

def test_groups_parsing(parser, city="Владивосток"):
    """Тест парсинга групп"""
    print(f"\n📚 Тестируем парсинг групп для города {city}...")
    
    groups = parser.parse_groups(city)
    
    if groups:
        print(f"✅ Найдено {len(groups)} групп:")
        if isinstance(groups, list) and groups:
            for i, group in enumerate(groups[:10], 1):  # Показываем первые 10
                if isinstance(group, str):
                    print(f"   {i}. {group}")
                elif isinstance(group, dict):
                    print(f"   {i}. {group.get('name', 'Без названия')} - {len(group.get('students', []))} учеников")
                    if group.get('students'):
                        print(f"      Первые ученики: {', '.join(group['students'][:3])}{'...' if len(group['students']) > 3 else ''}")
        else:
            print(f"   Данные: {groups}")
        return groups
    else:
        print("❌ Группы не найдены")
        return []

def test_export_data(parser):
    """Экспорт данных в JSON"""
    print("💾 Экспорт данных в JSON...")
    
    filename = parser.export_to_json()
    if filename:
        print(f"✅ Данные экспортированы в {filename}")
        
        # Показываем статистику
        debug_info = parser.get_debug_info()
        print(f"\n📊 Статистика:")
        print(f"   - Студентов: {debug_info['parsed_counts']['students']}")
        print(f"   - Групп: {debug_info['parsed_counts']['groups']}")
        
        # Показываем примеры студентов с новой структурой
        students = parser.parsed_data['students']
        if students:
            print(f"\n👨‍🎓 Примеры студентов:")
            for i, student in enumerate(students[:3]):
                print(f"   {i+1}. {student['first_name']} {student['last_name']}")
                print(f"      Логин: {student['login']}")
                print(f"      Баланс: {student['balance']} коинов")
                print(f"      Группа: {student['group_name']}")
        
        groups = parser.parsed_data['groups']
        if groups:
            print(f"\n📖 Найденные группы:")
            for i, group in enumerate(groups[:5]):
                print(f"   {i+1}. {group}")
        
        return filename
    else:
        print("❌ Ошибка экспорта")
        return None

def test_full_import():
    """Полный тест импорта"""
    print("🚀 Полный тест импорта данных")
    print("=" * 50)
    
    # Тест авторизации
    parser, username, password = test_login()
    if not parser:
        return
    
    # Выбор города
    city = input("\nВведите название города (по умолчанию: Владивосток): ").strip()
    if not city:
        city = "Владивосток"
    
    # Тест парсинга
    groups = test_groups_parsing(parser, city)
    if not groups:
        print("❌ Нет данных для импорта")
        return
    
    # Подтверждение импорта
    print(f"\n📋 Готовы к импорту:")
    print(f"   - Учитель: {username}")
    print(f"   - Город: {city}")
    print(f"   - Групп: {len(groups)}")
    total_students = sum(len(group['students']) for group in groups)
    print(f"   - Учеников: {total_students}")
    
    confirm = input("\n❓ Продолжить импорт в базу данных? (y/N): ")
    if confirm.lower() not in ['y', 'yes', 'да']:
        print("❌ Импорт отменен")
        return
    
    # Запуск полного импорта
    print("\n💾 Запускаем импорт в базу данных...")
    success = parser.run_full_import(username, password, city)
    
    if success:
        print("\n🎉 Импорт завершен успешно!")
        print("\n📋 Следующие шаги:")
        print("1. Зайдите в админку сайта")
        print("2. Проверьте созданных пользователей")
        print("3. Смените пароли учителям")
        print("4. Сообщите ученикам их логины и пароли")
    else:
        print("\n❌ Импорт завершен с ошибками")

def debug_html():
    """Отладка HTML структуры сайта"""
    print("🔍 Отладка HTML структуры...")
    
    parser, _, _ = test_login()
    if not parser:
        return
    
    # Получаем страницу групп
    try:
        response = parser.session.get(f"{parser.base_url}/groups/")
        
        # Сохраняем HTML для анализа
        with open("debug_groups_page.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        
        print("✅ HTML страницы сохранен в debug_groups_page.html")
        print("📝 Откройте файл и найдите нужные CSS селекторы")
        print("🔧 Затем обновите селекторы в algoritmika_parser.py")
        
    except Exception as e:
        print(f"❌ Ошибка при получении HTML: {str(e)}")

def main():
    """Главное меню"""
    print("🔄 Парсер algoritmika25.ru")
    print("=" * 30)
    print("1. Тест авторизации")
    print("2. Тест парсинга групп") 
    print("3. Полный импорт данных")
    print("4. Отладка HTML структуры")
    print("0. Выход")
    
    while True:
        try:
            choice = input("\nВыберите действие (0-4): ")
            
            if choice == "0":
                print("👋 До свидания!")
                break
            elif choice == "1":
                test_login()
            elif choice == "2":
                parser, _, _ = test_login()
                if parser:
                    city = input("Введите город (Владивосток): ") or "Владивосток"
                    test_groups_parsing(parser, city)
            elif choice == "3":
                # Полный импорт с экспортом в JSON
                parser, username, password = test_login()
                if parser:
                    city = input("Введите город (Владивосток): ") or "Владивосток"
                    
                    print(f"\n📚 Парсинг групп для города {city}...")
                    groups = parser.parse_groups(city)
                    
                    print(f"\n💾 Экспорт данных...")
                    filename = test_export_data(parser)
                    
                    if filename:
                        print(f"\n✅ Импорт завершен! Данные сохранены в {filename}")
                    else:
                        print(f"\n❌ Ошибка при экспорте данных")
            elif choice == "4":
                debug_html()
            else:
                print("❌ Неверный выбор")
                
        except KeyboardInterrupt:
            print("\n👋 До свидания!")
            break
        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")

if __name__ == "__main__":
    main()
