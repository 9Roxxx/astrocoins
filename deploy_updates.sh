#!/bin/bash

# Скрипт развертывания обновлений Астрокоинов на сервере
# Автор: AI Assistant
# Дата: Январь 2025

echo "🚀 Начинаем развертывание обновлений Астрокоинов..."

# Переходим в директорию проекта
cd /var/www/astrocoins

# Останавливаем сервис (если используется systemd)
echo "⏸️  Останавливаем сервис..."
sudo systemctl stop astrocoins

# Создаем резервную копию
echo "💾 Создаем резервную копию..."
sudo cp -r /var/www/astrocoins /var/www/astrocoins_backup_$(date +%Y%m%d_%H%M%S)

# Обновляем код из git
echo "📦 Получаем обновления из Git..."
sudo -u astrocoins git fetch origin
sudo -u astrocoins git reset --hard origin/main

# Активируем виртуальное окружение
echo "🐍 Активируем виртуальное окружение..."
source venv/bin/activate

# Устанавливаем зависимости (если есть новые)
echo "📚 Проверяем зависимости..."
pip install -r requirements.txt

# Применяем миграции базы данных
echo "🗄️  Применяем миграции базы данных..."
python manage.py migrate

# Собираем статические файлы
echo "🎨 Собираем статические файлы..."
python manage.py collectstatic --noinput

# Перезапускаем сервис
echo "🔄 Перезапускаем сервис..."
sudo systemctl start astrocoins
sudo systemctl enable astrocoins

# Проверяем статус
echo "✅ Проверяем статус сервиса..."
sudo systemctl status astrocoins

echo "🎉 Развертывание завершено!"
echo ""
echo "📋 Список изменений:"
echo "✅ Ручной ввод даты рождения (день/месяц/год)"
echo "✅ Обновленная база знаний с правилами начисления AC"
echo "✅ Фильтры покупок по группам"
echo "✅ Система отслеживания выдачи товаров"
echo "✅ Фильтр учеников по дням рождения"
echo "✅ Индивидуальное начисление AC в группах"
echo "✅ Удаление групп для администраторов"
echo ""
echo "🌐 Проверьте сайт: https://algoritmika25.store"
echo "🔧 Админка: https://algoritmika25.store/admin"
