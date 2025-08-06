#!/bin/bash

echo "========================================"
echo "Полная автоматическая установка Астрокоины"
echo "на Ubuntu 24.04"
echo "========================================"
echo

# Проверка на root права
if [ "$EUID" -ne 0 ]; then
    echo "Этот скрипт должен быть запущен с правами sudo"
    exit 1
fi

# Обновление системы
echo "1. Обновление системы..."
apt update && apt upgrade -y

# Установка необходимых пакетов
echo "2. Установка пакетов..."
apt install -y python3 python3-pip python3-venv python3-dev
apt install -y nginx postgresql postgresql-contrib
apt install -y git curl wget redis-server
apt install -y libjpeg-dev zlib1g-dev libpng-dev

# Создание пользователя
echo "3. Создание пользователя astrocoins..."
useradd -m -s /bin/bash astrocoins
usermod -aG sudo astrocoins

# Настройка PostgreSQL
echo "4. Настройка PostgreSQL..."
sudo -u postgres psql << EOF
CREATE USER astrocoins WITH PASSWORD 'astrocoins_password_2024';
CREATE DATABASE astrocoins OWNER astrocoins;
GRANT ALL PRIVILEGES ON DATABASE astrocoins TO astrocoins;
\q
EOF

# Настройка аутентификации PostgreSQL
sed -i "s/local   all             all                                     peer/local   all             all                                     md5/" /etc/postgresql/*/main/pg_hba.conf
systemctl restart postgresql

# Настройка Redis
echo "5. Настройка Redis..."
systemctl enable redis-server
systemctl start redis-server

# Создание директории проекта
echo "6. Создание директории проекта..."
mkdir -p /var/www/astrocoins
chown astrocoins:astrocoins /var/www/astrocoins

# Переключение на пользователя astrocoins
echo "7. Настройка проекта..."
sudo -u astrocoins bash << 'ASTROCOINS_USER'

cd /var/www/astrocoins

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Обновление pip
pip install --upgrade pip

# Установка зависимостей
pip install -r requirements.txt

# Применение миграций
python manage.py migrate

# Создание суперпользователя (автоматически)
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'algoritmika25mails@algoritmika25.store', 'admin123') if not User.objects.filter(username='admin').exists() else None" | python manage.py shell

# Загрузка начальных данных
python manage.py loaddata core/fixtures/initial_data.json
python manage.py setup_product_categories
python manage.py setup_award_reasons

# Сбор статических файлов
python manage.py collectstatic --noinput

# Создание сертификата
python create_cert.py

ASTROCOINS_USER

# Настройка systemd сервиса
echo "8. Настройка systemd сервиса..."
tee /etc/systemd/system/astrocoins.service > /dev/null <<EOF
[Unit]
Description=Astrocoins Django Application
After=network.target

[Service]
User=astrocoins
Group=astrocoins
WorkingDirectory=/var/www/astrocoins
Environment="PATH=/var/www/astrocoins/venv/bin"
ExecStart=/var/www/astrocoins/venv/bin/gunicorn --workers 3 --bind unix:/var/www/astrocoins/astrocoins.sock astrocoins.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Настройка Nginx
echo "9. Настройка Nginx..."
tee /etc/nginx/sites-available/astrocoins > /dev/null <<EOF
server {
    listen 80;
    server_name algoritmika25.store www.algoritmika25.store;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/astrocoins;
    }

    location /media/ {
        root /var/www/astrocoins;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/astrocoins/astrocoins.sock;
    }
}
EOF

# Активация сайта
ln -sf /etc/nginx/sites-available/astrocoins /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Настройка прав доступа
chown -R astrocoins:astrocoins /var/www/astrocoins
chmod -R 755 /var/www/astrocoins

# Создание лог директорий
mkdir -p /var/log/astrocoins
chown astrocoins:astrocoins /var/log/astrocoins

# Настройка firewall
echo "10. Настройка firewall..."
ufw allow 'Nginx Full'
ufw allow ssh

# Запуск сервисов
echo "11. Запуск сервисов..."
systemctl daemon-reload
systemctl enable astrocoins
systemctl start astrocoins
systemctl restart nginx

# Настройка SSL с Let's Encrypt
echo "12. Настройка SSL..."
apt install -y certbot python3-certbot-nginx
certbot --nginx -d algoritmika25.store -d www.algoritmika25.store --non-interactive --agree-tos --email algoritmika25mails@algoritmika25.store

echo "========================================"
echo "Установка завершена!"
echo "========================================"
echo
echo "Сайт доступен по адресу:"
echo "https://algoritmika25.store"
echo
echo "Админка: https://algoritmika25.store/admin"
echo "Логин: admin"
echo "Пароль: admin123"
echo
echo "Проверьте статус сервисов:"
echo "sudo systemctl status astrocoins"
echo "sudo systemctl status nginx"
echo
echo "Не забудьте изменить пароли в продакшене!" 