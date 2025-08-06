# Настройка Git для проекта Астрокоины

## Установка Git

### На Windows:
1. Скачайте Git с официального сайта: https://git-scm.com/download/win
2. Установите Git с настройками по умолчанию

### На Ubuntu/Linux:
```bash
sudo apt update
sudo apt install git
```

## Настройка Git

После установки Git выполните следующие команды в папке проекта:

```bash
# Инициализация репозитория
git init

# Настройка пользователя (замените на свои данные)
git config --global user.name "Ваше имя"
git config --global user.email "ваш-email@example.com"

# Добавление всех файлов
git add .

# Первый коммит
git commit -m "Initial commit: Астрокоины проект с новыми функциями"
```

## Подключение к GitHub

1. Создайте новый репозиторий на GitHub
2. Подключите локальный репозиторий к GitHub:

```bash
git remote add origin https://github.com/ваш-username/astrocoins.git
git branch -M main
git push -u origin main
```

## Ежедневная работа с Git

### Сохранение изменений:
```bash
git add .
git commit -m "Описание изменений"
git push
```

### Загрузка изменений с сервера:
```bash
git pull
```

### Просмотр статуса:
```bash
git status
```

### Просмотр истории:
```bash
git log --oneline
```

## Файл .gitignore

Файл `.gitignore` уже создан и настроен для Django проекта. Он исключает из версионирования:
- Виртуальные окружения (venv/)
- Базы данных (db.sqlite3)
- Статические файлы (staticfiles/)
- Переменные окружения (.env)
- Кэш Python (__pycache__/)
- IDE файлы
- SSL сертификаты

## Важные команды для деплоя

После внесения изменений на сервере:
```bash
# Остановить сервер
sudo systemctl stop astrocoins

# Обновить код
git pull

# Применить миграции (если есть)
python manage.py migrate

# Собрать статические файлы
python manage.py collectstatic --noinput

# Перезапустить сервер
sudo systemctl start astrocoins
sudo systemctl restart nginx
```