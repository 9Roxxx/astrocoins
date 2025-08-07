# 🚀 Инструкция по развертыванию в продакшене

## 📋 Чек-лист готовности

- ✅ PostgreSQL настроен и работает
- ✅ Nginx/Apache настроен для HTTPS
- ✅ Переменные окружения настроены
- ✅ SSL-сертификат установлен
- ✅ Firewall настроен

## 🔧 1. Настройка переменных окружения

Создайте файл `.env` на VPS:

```bash
sudo nano /var/www/astrocoins/.env
```

Скопируйте содержимое из `env_production_template.txt` и обязательно измените:

- `SECRET_KEY` - используйте сгенерированный ключ
- `DB_PASSWORD` - пароль от PostgreSQL
- `EMAIL_PASSWORD` - пароль от почты

## 🔐 2. Установка прав доступа

```bash
# Права на файл с переменными
sudo chmod 600 /var/www/astrocoins/.env
sudo chown astrocoins:astrocoins /var/www/astrocoins/.env

# Создание директории для логов
sudo mkdir -p /var/log/astrocoins
sudo chown astrocoins:astrocoins /var/log/astrocoins
```

## 🗄️ 3. Настройка базы данных

```bash
# Подключение к PostgreSQL
sudo -u postgres psql

# Создание базы и пользователя
CREATE DATABASE astrocoins;
CREATE USER astrocoins WITH PASSWORD 'ваш_пароль';
GRANT ALL PRIVILEGES ON DATABASE astrocoins TO astrocoins;
ALTER ROLE astrocoins SET client_encoding TO 'utf8';
ALTER ROLE astrocoins SET default_transaction_isolation TO 'read committed';
ALTER ROLE astrocoins SET timezone TO 'Europe/Moscow';

# Подключение к базе и выдача прав на схему
\c astrocoins
GRANT ALL ON SCHEMA public TO astrocoins;
\q
```

## 🔄 4. Развертывание приложения

```bash
# Переход в директорию проекта
cd /var/www/astrocoins

# Загрузка переменных окружения
export $(cat .env | xargs)

# Применение миграций
python manage.py migrate

# Загрузка данных (если есть дамп)
python manage.py loaddata datadump.json

# Сбор статических файлов
python manage.py collectstatic --noinput

# Создание суперпользователя
python manage.py createsuperuser

# Загрузка начальных данных
python manage.py setup_product_categories
python manage.py setup_award_reasons
```

## 🌐 5. Настройка веб-сервера

### Nginx (рекомендуется)

```nginx
server {
    listen 80;
    server_name algoritmika25.store www.algoritmika25.store;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name algoritmika25.store www.algoritmika25.store;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    location /static/ {
        alias /var/www/astrocoins/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/astrocoins/media/;
        expires 30d;
    }
}
```

## 🔄 6. Настройка Gunicorn

Создайте файл `/etc/systemd/system/astrocoins.service`:

```ini
[Unit]
Description=Astrocoins Django App
After=network.target

[Service]
User=astrocoins
Group=astrocoins
WorkingDirectory=/var/www/astrocoins
EnvironmentFile=/var/www/astrocoins/.env
ExecStart=/var/www/astrocoins/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 astrocoins.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

Запуск сервиса:

```bash
sudo systemctl daemon-reload
sudo systemctl enable astrocoins
sudo systemctl start astrocoins
sudo systemctl status astrocoins
```

## ✅ 7. Проверка работы

1. **Откройте сайт**: https://algoritmika25.store
2. **Проверьте админку**: https://algoritmika25.store/admin
3. **Проверьте статику**: стили должны загружаться
4. **Проверьте функции**: регистрация, вход, покупки

## 🔍 8. Мониторинг

```bash
# Просмотр логов Django
tail -f /var/log/astrocoins/django.log

# Просмотр логов Gunicorn
sudo journalctl -u astrocoins -f

# Просмотр логов Nginx
sudo tail -f /var/log/nginx/error.log
```

## 🆘 9. Устранение проблем

### Проблема: Стили не загружаются
```bash
python manage.py collectstatic --noinput
sudo systemctl restart astrocoins
```

### Проблема: Ошибки базы данных
```bash
# Проверка подключения
python manage.py dbshell
```

### Проблема: 502 Bad Gateway
```bash
# Проверка статуса Gunicorn
sudo systemctl status astrocoins
sudo systemctl restart astrocoins
```

## 🔄 10. Обновление проекта

```bash
# Обновление кода
git pull origin main

# Применение миграций
python manage.py migrate

# Сбор статики
python manage.py collectstatic --noinput

# Перезапуск сервиса
sudo systemctl restart astrocoins
```

---

**🎉 Проект готов к работе в продакшене!**
