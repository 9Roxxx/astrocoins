@echo off
echo ========================================
echo Запуск Астрокоины из папки деплоя
echo ========================================
echo.

REM Активируем виртуальное окружение
if not exist venv (
    echo Создание виртуального окружения...
    python -m venv venv
)

echo Активация виртуального окружения...
call venv\Scripts\activate.bat

REM Устанавливаем зависимости
echo Установка зависимостей...
pip install -r requirements.txt

REM Применяем миграции
echo Применение миграций...
python manage.py migrate

REM Создаем сертификат если его нет
if not exist cert.pem (
    echo Создание сертификата...
    python create_cert.py
)

REM Собираем статические файлы
echo Сбор статических файлов...
python manage.py collectstatic --noinput

echo.
echo ========================================
echo Сервер запускается на https://127.0.0.1:8001/
echo ========================================
echo.

REM Запускаем сервер
python manage.py runserver_plus --cert-file cert.pem --key-file key.pem 127.0.0.1:8001

pause 