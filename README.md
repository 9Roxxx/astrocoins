# Астрокоины - Файлы для деплоя на Ubuntu 24.04

Это папка содержит все необходимые файлы для развертывания проекта Астрокоины на Ubuntu 24.04.

## ✅ Тестирование готово!

Проект успешно протестирован и работает на порту 8001:
- **HTTPS**: https://127.0.0.1:8001/
- **Админка**: https://127.0.0.1:8001/admin
- **Логин админа**: `admin`

## 🆕 Новые функции (v2.0)

### Для администраторов:
- **Управление категориями товаров**: Создание, редактирование и удаление категорий прямо в интерфейсе магазина
- **Настройка иконок**: Поддержка Font Awesome иконок для категорий
- **Популярные категории**: Отметка категорий как "🔥 TOP"

### Для всех пользователей:
- **Динамические игровые фоны**: Случайные фоны из популярных игр при каждом входе
  - Standoff 2, Dota 2, CS 2, Steam, Roblox
- **Улучшенный дизайн**: Более читаемые карточки с полупрозрачным фоном
- **Убрана пасхалка**: Удален функционал изменения цвета астрокоинов при кликах

## 🚀 Быстрая установка на Ubuntu 24.04

### ⚡ Полная автоматическая установка (рекомендуется)
```bash
# Скопируйте файлы в /var/www/astrocoins/
sudo mkdir -p /var/www/astrocoins
sudo chown $USER:$USER /var/www/astrocoins
# ... скопируйте все файлы из папки deploy

# Запустите полную установку
chmod +x install_all.sh
sudo ./install_all.sh
```

### 🔧 Пошаговая установка

#### 1. Подготовка сервера
```bash
chmod +x install_ubuntu.sh
sudo ./install_ubuntu.sh
```

#### 2. Настройка базы данных
```bash
chmod +x setup_database.sh
sudo ./setup_database.sh
```

#### 3. Настройка проекта
```bash
sudo su - astrocoins
cd /var/www/astrocoins
chmod +x setup_project.sh
./setup_project.sh
```

#### 4. Настройка продакшена
```bash
sudo chmod +x setup_production.sh
sudo ./setup_production.sh
```

## Структура проекта

```
deploy/
├── astrocoins/          # Основные настройки Django
├── core/               # Основное приложение
├── static/             # Статические файлы (CSS, JS, изображения)
├── templates/          # Шаблоны
├── manage.py           # Управление Django
├── requirements.txt    # Зависимости Python
├── passenger_wsgi.py   # WSGI для Passenger
├── .htaccess          # Настройки Apache
├── create_cert.py     # Скрипт создания сертификата
├── start_https_server.bat # Скрипт запуска HTTPS сервера (Windows)
├── start_deploy_server.bat # Автоматический запуск из папки деплоя (Windows)
├── install_ubuntu.sh  # Установка на Ubuntu 24.04
├── setup_database.sh  # Настройка PostgreSQL и Redis
├── setup_project.sh   # Настройка проекта
├── setup_production.sh # Настройка продакшена
├── astrocoins/settings_production.py # Настройки для продакшена
├── env_example.txt    # Пример переменных окружения
├── env_production.txt # Переменные окружения для продакшена
└── README.md          # Этот файл
```

## 📋 Подробные инструкции по развертыванию

### Для Ubuntu 24.04 (рекомендуется)

#### 1. Подготовка сервера
```bash
# Клонируйте или скопируйте файлы в /var/www/astrocoins/
sudo mkdir -p /var/www/astrocoins
sudo chown $USER:$USER /var/www/astrocoins

# Запустите установку
chmod +x install_ubuntu.sh
sudo ./install_ubuntu.sh
```

#### 2. Настройка базы данных
```bash
chmod +x setup_database.sh
sudo ./setup_database.sh
```

#### 3. Настройка проекта
```bash
sudo su - astrocoins
cd /var/www/astrocoins
chmod +x setup_project.sh
./setup_project.sh
```

#### 4. Настройка продакшена
```bash
sudo chmod +x setup_production.sh
sudo ./setup_production.sh
```

### Для Windows (разработка)

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка базы данных

```bash
python manage.py migrate
```

### 4. Создание суперпользователя

```bash
python manage.py createsuperuser
```

### 5. Загрузка начальных данных

```bash
python manage.py loaddata core/fixtures/initial_data.json
python manage.py setup_product_categories
python manage.py setup_award_reasons
```

### 6. Сбор статических файлов

```bash
python manage.py collectstatic --noinput
```

### 7. Запуск сервера

#### Автоматический запуск (рекомендуется):
```bash
start_deploy_server.bat
```

#### Ручной запуск (HTTPS):
```bash
python create_cert.py
python manage.py runserver_plus --cert-file cert.pem --key-file key.pem 127.0.0.1:8001
```

#### Для продакшена:
Настройте WSGI сервер (Gunicorn, uWSGI) с файлом `passenger_wsgi.py`

## Настройки для продакшена

1. Измените `DEBUG = False` в `astrocoins/settings.py`
2. Настройте `ALLOWED_HOSTS` для вашего домена
3. Настройте `SECRET_KEY` через переменную окружения
4. Настройте базу данных PostgreSQL или MySQL
5. Настройте email сервер

## 📧 Настройки почты

Проект настроен для работы с почтовым ящиком:
- **Email**: algoritmika25mails@algoritmika25.store
- **Пароль**: 3164579881245$Ss
- **SMTP сервер**: smtp.beget.com
- **Порт**: 465 (SSL)

## 🌐 Домен

Проект настроен для домена: `algoritmika25.store`

## 📞 Контакты

При возникновении проблем обращайтесь к разработчику.

## 🔧 Разработка и Git

### Настройка Git (для разработки):
1. Установите Git: см. файл `SETUP_GIT.md`
2. Инициализируйте репозиторий:
```bash
git init
git add .
git commit -m "Initial commit"
```

### Подключение к GitHub:
1. Создайте репозиторий на GitHub
2. Подключите локальный репозиторий:
```bash
git remote add origin https://github.com/username/astrocoins.git
git push -u origin main
```

### Синхронизация изменений:
```bash
# Загрузка изменений
git pull

# Сохранение изменений
git add .
git commit -m "Описание изменений"
git push
```

## 📋 Файлы проекта

- `SETUP_GIT.md` - Инструкции по настройке Git
- `CHANGELOG.md` - История изменений проекта
- `.gitignore` - Настройки Git для исключения файлов 