#!/bin/bash

echo "========================================"
echo "Настройка проекта Астрокоины"
echo "========================================"
echo

# Переход в директорию проекта
cd /var/www/astrocoins

# Создание виртуального окружения
echo "Создание виртуального окружения..."
python3 -m venv venv

# Активация виртуального окружения
echo "Активация виртуального окружения..."
source venv/bin/activate

# Обновление pip
echo "Обновление pip..."
pip install --upgrade pip

# Установка зависимостей
echo "Установка зависимостей..."
pip install -r requirements.txt

# Применение миграций
echo "Применение миграций..."
python manage.py migrate

# Создание суперпользователя (интерактивно)
echo "Создание суперпользователя..."
python manage.py createsuperuser

# Загрузка начальных данных
echo "Загрузка начальных данных..."
python manage.py loaddata core/fixtures/initial_data.json
python manage.py setup_product_categories
python manage.py setup_award_reasons

# Сбор статических файлов
echo "Сбор статических файлов..."
python manage.py collectstatic --noinput

# Создание сертификата для разработки
echo "Создание сертификата..."
python create_cert.py

# Настройка прав доступа
echo "Настройка прав доступа..."
sudo chown -R astrocoins:astrocoins /var/www/astrocoins
chmod +x *.sh

echo "========================================"
echo "Настройка проекта завершена!"
echo "========================================"
echo
echo "Для запуска сервера разработки:"
echo "source venv/bin/activate"
echo "python manage.py runserver_plus --cert-file cert.pem --key-file key.pem 0.0.0.0:8000"
echo
echo "Для настройки продакшена запустите:"
echo "sudo ./setup_production.sh" 