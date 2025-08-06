#!/bin/bash

echo "========================================"
echo "Настройка продакшена Астрокоины"
echo "========================================"
echo

# Установка Gunicorn
echo "Установка Gunicorn..."
cd /var/www/astrocoins
source venv/bin/activate
pip install gunicorn

# Создание systemd сервиса
echo "Создание systemd сервиса..."
sudo tee /etc/systemd/system/astrocoins.service > /dev/null <<EOF
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
echo "Настройка Nginx..."
sudo tee /etc/nginx/sites-available/astrocoins > /dev/null <<EOF
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
echo "Активация Nginx сайта..."
sudo ln -sf /etc/nginx/sites-available/astrocoins /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Настройка прав доступа
echo "Настройка прав доступа..."
sudo chown -R astrocoins:astrocoins /var/www/astrocoins
sudo chmod -R 755 /var/www/astrocoins

# Создание лог директорий
sudo mkdir -p /var/log/astrocoins
sudo chown astrocoins:astrocoins /var/log/astrocoins

# Настройка firewall
echo "Настройка firewall..."
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh

# Запуск сервисов
echo "Запуск сервисов..."
sudo systemctl daemon-reload
sudo systemctl enable astrocoins
sudo systemctl start astrocoins
sudo systemctl restart nginx

# Настройка SSL с Let's Encrypt
echo "Настройка SSL с Let's Encrypt..."
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d algoritmika25.store -d www.algoritmika25.store --non-interactive --agree-tos --email algoritmika25mails@algoritmika25.store

echo "========================================"
echo "Настройка продакшена завершена!"
echo "========================================"
echo
echo "Проверьте статус сервисов:"
echo "sudo systemctl status astrocoins"
echo "sudo systemctl status nginx"
echo
echo "Сайт доступен по адресу:"
echo "https://algoritmika25.store" 