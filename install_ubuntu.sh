#!/bin/bash

echo "========================================"
echo "Установка Астрокоины на Ubuntu 24.04"
echo "========================================"
echo

# Обновление системы
echo "Обновление системы..."
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
echo "Установка необходимых пакетов..."
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y nginx
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y git curl wget

# Установка дополнительных зависимостей для Pillow
sudo apt install -y libjpeg-dev zlib1g-dev libpng-dev

# Создание пользователя для приложения
echo "Создание пользователя astrocoins..."
sudo useradd -m -s /bin/bash astrocoins
sudo usermod -aG sudo astrocoins

# Создание директории для проекта
sudo mkdir -p /var/www/astrocoins
sudo chown astrocoins:astrocoins /var/www/astrocoins

echo "========================================"
echo "Установка системных пакетов завершена!"
echo "========================================"
echo
echo "Следующие шаги:"
echo "1. Переключитесь на пользователя astrocoins: sudo su - astrocoins"
echo "2. Скопируйте файлы проекта в /var/www/astrocoins/"
echo "3. Запустите setup_project.sh" 