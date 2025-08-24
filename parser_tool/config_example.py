"""
Пример конфигурации для парсера algoritmika25.ru
Скопируйте этот файл как config.py и заполните своими данными
"""

# Настройки учителей для импорта
TEACHERS_CONFIG = {
    "владивосток": {
        "username": "ваш_логин_владивосток",
        "password": "ваш_пароль_владивосток", 
        "city": "Владивосток",
        "email": "teacher_vlad@algoritmika.ru"
    },
    "благовещенск": {
        "username": "ваш_логин_благовещенск",
        "password": "ваш_пароль_благовещенск",
        "city": "Благовещенск", 
        "email": "teacher_blag@algoritmika.ru"
    },
    "уссурийск": {
        "username": "ваш_логин_уссурийск",
        "password": "ваш_пароль_уссурийск",
        "city": "Уссурийск",
        "email": "teacher_uss@algoritmika.ru"
    }
}

# Сопоставление названий групп с городами (если нужно)
GROUP_CITY_MAPPING = {
    "Владивосток": ["Python ВЛД", "Scratch ВЛД", "Unity ВЛД"],
    "Благовещенск": ["Python БЛГ", "Scratch БЛГ"], 
    "Уссурийск": ["Python УСС", "Minecraft УСС"]
}

# HTML селекторы для парсинга (адаптируйте под реальный сайт)
HTML_SELECTORS = {
    "groups": {
        "container": ".groups-container",
        "group_item": ".group-card",
        "group_name": ".group-name", 
        "students_list": ".students-list",
        "student_item": ".student-name"
    },
    "students": {
        "container": ".students-container",
        "student_item": ".student-card",
        "student_name": ".student-name",
        "student_email": ".student-email",
        "student_group": ".student-group"
    },
    "profile": {
        "full_name": ".profile-name",
        "email": ".profile-email",
        "phone": ".profile-phone"
    }
}

# Настройки генерации данных
GENERATION_SETTINGS = {
    "default_teacher_coins": 1000,
    "default_student_coins": 0,
    "default_student_password": "ученик123",
    "default_teacher_password": "учитель123",
    "username_max_length": 20,
    "email_domain": "algoritmika.local"
}

# URLs старого сайта
OLD_SITE_URLS = {
    "base": "https://algoritmika25.ru",
    "login": "/accounts/login/",
    "groups": "/groups/", 
    "students": "/user-management/",
    "profile": "/profile/"
}

# Создаваемые школы по умолчанию
DEFAULT_SCHOOLS = {
    "Владивосток": {
        "name": "Алгоритмика Владивосток",
        "director": "Не указан",
        "address": "г. Владивосток",
        "phone": "+7 (423) XXX-XX-XX"
    },
    "Благовещенск": {
        "name": "Алгоритмика Благовещенск", 
        "director": "Не указан",
        "address": "г. Благовещенск",
        "phone": "+7 (416) XXX-XX-XX"
    },
    "Уссурийск": {
        "name": "Алгоритмика Уссурийск",
        "director": "Не указан", 
        "address": "г. Уссурийск",
        "phone": "+7 (424) XXX-XX-XX"
    }
}

# Курсы по умолчанию
DEFAULT_COURSES = [
    {
        "name": "Программирование на Python",
        "description": "Изучение основ программирования на языке Python"
    },
    {
        "name": "Программирование в Scratch",
        "description": "Визуальное программирование для начинающих"
    },
    {
        "name": "Разработка игр в Unity",
        "description": "Создание 2D и 3D игр на движке Unity"
    },
    {
        "name": "Веб-разработка",
        "description": "Создание сайтов на HTML, CSS и JavaScript"
    }
]


