#!/bin/bash

echo "========================================"
echo "Настройка базы данных PostgreSQL"
echo "========================================"
echo

# Настройка PostgreSQL
echo "Настройка PostgreSQL..."

# Создание пользователя и базы данных
sudo -u postgres psql << EOF
CREATE USER astrocoins WITH PASSWORD 'astrocoins_password_2024';
CREATE DATABASE astrocoins OWNER astrocoins;
GRANT ALL PRIVILEGES ON DATABASE astrocoins TO astrocoins;
\q
EOF

# Настройка аутентификации
echo "Настройка аутентификации PostgreSQL..."
sudo sed -i "s/local   all             all                                     peer/local   all             all                                     md5/" /etc/postgresql/*/main/pg_hba.conf

# Перезапуск PostgreSQL
echo "Перезапуск PostgreSQL..."
sudo systemctl restart postgresql

# Установка Redis
echo "Установка Redis..."
sudo apt install -y redis-server

# Настройка Redis
echo "Настройка Redis..."
sudo systemctl enable redis-server
sudo systemctl start redis-server

echo "========================================"
echo "Настройка базы данных завершена!"
echo "========================================"
echo
echo "Данные для подключения:"
echo "База данных: astrocoins"
echo "Пользователь: astrocoins"
echo "Пароль: astrocoins_password_2024"
echo "Хост: localhost"
echo "Порт: 5432"
echo
echo "Не забудьте изменить пароль в продакшене!" 