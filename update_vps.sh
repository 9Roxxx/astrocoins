#!/bin/bash

# Скрипт для обновления проекта Astrocoins на VPS
# Использование: ./update_vps.sh

set -e  # Остановить выполнение при ошибке

echo "🚀 Начинаем обновление Astrocoins..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверяем, что мы в правильной директории
if [ ! -f "manage.py" ]; then
    log_error "manage.py не найден! Убедитесь, что вы в корневой директории проекта Django."
    exit 1
fi

log_info "Директория проекта найдена ✓"

# Сохраняем изменения перед pull (если есть)
if ! git diff --quiet; then
    log_warning "Обнаружены локальные изменения. Сохраняем их..."
    git stash push -m "Auto-stash before update $(date)"
fi

# Получаем обновления из Git
log_info "Получаем обновления из Git..."
git fetch origin

# Проверяем, есть ли обновления
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    log_info "Код уже актуален. Обновления не требуются."
    exit 0
fi

log_info "Найдены обновления. Применяем..."
git pull origin main

# Активируем виртуальное окружение если есть
if [ -d "venv" ]; then
    log_info "Активируем виртуальное окружение..."
    source venv/bin/activate
elif [ -d "env" ]; then
    log_info "Активируем виртуальное окружение..."
    source env/bin/activate
else
    log_warning "Виртуальное окружение не найдено"
fi

# Устанавливаем/обновляем зависимости
log_info "Обновляем зависимости..."
pip install -r requirements.txt

# Выполняем миграции
log_info "Выполняем миграции базы данных..."
python manage.py migrate

# Собираем статические файлы
log_info "Собираем статические файлы..."
python manage.py collectstatic --noinput

# Перезапускаем сервис
log_info "Перезапускаем сервис astrocoins..."
sudo systemctl restart astrocoins

# Ждем немного и проверяем статус
sleep 3
if sudo systemctl is-active --quiet astrocoins; then
    log_info "✅ Сервис astrocoins успешно перезапущен"
else
    log_error "❌ Проблема с перезапуском сервиса astrocoins"
    log_info "Проверьте логи: sudo journalctl -u astrocoins -n 20"
    exit 1
fi

# Перезапускаем Nginx если есть
if systemctl is-active --quiet nginx; then
    log_info "Перезапускаем Nginx..."
    sudo systemctl reload nginx
    log_info "✅ Nginx перезагружен"
fi

log_info "🎉 Обновление завершено успешно!"
log_info "Проект обновлен с версии $(git rev-parse --short $LOCAL) до $(git rev-parse --short $REMOTE)"

echo ""
echo "📊 Статус сервисов:"
echo "Astrocoins: $(sudo systemctl is-active astrocoins)"
if systemctl is-active --quiet nginx; then
    echo "Nginx: $(sudo systemctl is-active nginx)"
fi

echo ""
log_info "Для просмотра логов используйте:"
echo "  sudo journalctl -u astrocoins -f"
echo "  sudo tail -f /var/log/nginx/error.log"