#!/bin/bash

# Скрипт полной установки Астрокоинов с GitHub
# Версия 2.0 с новыми функциями

echo "🚀 Установка Астрокоинов v2.0 с GitHub..."

# Обновление системы
echo "📦 Обновление системы..."
sudo apt update && sudo apt upgrade -y

# Установка Git
echo "🔧 Установка Git..."
sudo apt install git -y

# Создание директории
echo "📁 Создание директории проекта..."
sudo mkdir -p /var/www
cd /var/www

# Клонирование проекта
echo "📥 Клонирование проекта с GitHub..."
sudo git clone https://github.com/9Roxxx/astrocoins.git

# Настройка прав
echo "🔐 Настройка прав доступа..."
sudo chown -R $USER:$USER /var/www/astrocoins
cd astrocoins

# Запуск автоматической установки
echo "⚙️ Запуск автоматической установки..."
chmod +x install_all.sh
sudo ./install_all.sh

echo ""
echo "✅ Установка завершена!"
echo ""
echo "🌐 Ваш сайт будет доступен по адресу вашего домена"
echo "🔧 Админка: https://ваш-домен/admin"
echo "👤 Логин: admin"
echo ""
echo "🎮 Новые функции v2.0:"
echo "  • Динамические игровые фоны (Standoff 2, Dota 2, CS 2, Steam, Roblox)"
echo "  • Управление категориями товаров для администраторов"
echo "  • Убрана пасхалка с изменением цвета астрокоинов"
echo ""
echo "📚 Для обновлений используйте: git pull"