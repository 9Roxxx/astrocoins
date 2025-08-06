# 🚀 Установка Астрокоинов v2.0 на VPS

## Быстрая установка (5 минут):

### 1. Переустановите VPS на Ubuntu 24.04

### 2. Подключитесь по SSH и выполните:

```bash
# Скачиваем скрипт установки
wget https://raw.githubusercontent.com/9Roxxx/astrocoins/main/install_from_github.sh

# Делаем исполняемым
chmod +x install_from_github.sh

# Запускаем установку
./install_from_github.sh
```

## Альтернативный способ (ручная установка):

```bash
# 1. Обновление системы
sudo apt update && sudo apt upgrade -y

# 2. Установка Git
sudo apt install git -y

# 3. Клонирование проекта
cd /var/www
sudo git clone https://github.com/9Roxxx/astrocoins.git
sudo chown -R $USER:$USER astrocoins
cd astrocoins

# 4. Автоматическая установка
chmod +x install_all.sh
sudo ./install_all.sh
```

## 🎯 Что получите:

✅ **Чистая установка** Ubuntu 24.04
✅ **Актуальный код** прямо с GitHub
✅ **Все новые функции v2.0**:
  - Динамические игровые фоны
  - Управление категориями для админов
  - Убранная пасхалка с астрокоинами
✅ **HTTPS сертификаты**
✅ **Настроенный Nginx + Gunicorn**
✅ **PostgreSQL база данных**

## 🔄 Обновления в будущем:

```bash
cd /var/www/astrocoins
git pull
sudo systemctl restart astrocoins
sudo systemctl restart nginx
```

## 🌐 После установки:

- **Сайт**: https://algoritmika25.store
- **Админка**: https://algoritmika25.store/admin
- **Логин**: admin (создайте пароль через `python manage.py changepassword admin`)

## 🎮 Новые функции для тестирования:

1. **Обновляйте главную страницу** - фоны будут меняться
2. **Войдите как админ в магазин** - увидите кнопки управления категориями
3. **Создайте тестовую категорию** - проверьте новый функционал
4. **Кликайте по астрокоинам** - пасхалка больше не работает