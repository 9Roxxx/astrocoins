@echo off
echo Запуск Django сервера с поддержкой HTTPS...
echo.
echo Если сертификат не существует, создаем его...
if not exist cert.pem (
    python create_cert.py
)
echo.
echo Запуск сервера на https://127.0.0.1:8000/
python manage.py runserver_plus --cert-file cert.pem --key-file key.pem 127.0.0.1:8000
pause 