# 🚀 Обновление AstroCoins v2.1 на VPS

## Что нового в версии 2.1:
- **Система родителей** с полной информацией
- **Иерархическая школьная система** (Города → Школы → Курсы → Группы)
- **Расширенные поля групп** (курс, школа, дата, время, кабинет, куратор)

## 📋 Команды для обновления на VPS:

### 1. Подключиться к VPS по SSH
```bash
ssh root@your-server-ip
```

### 2. Перейти в папку проекта
```bash
cd /var/www/astrocoins
```

### 3. Остановить сервер
```bash
sudo systemctl stop astrocoins
sudo systemctl stop nginx
```

### 4. Создать резервную копию БД (рекомендуется)
```bash
sudo -u postgres pg_dump astrocoins_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 5. Обновить код с GitHub
```bash
git pull origin main
```

### 6. Активировать виртуальное окружение
```bash
source venv/bin/activate
```

### 7. Установить новые зависимости (если есть)
```bash
pip install -r requirements.txt
```

### 8. Применить миграции БД
```bash
python manage.py migrate
```

### 9. Собрать статические файлы
```bash
python manage.py collectstatic --noinput
```

### 10. Перезапустить сервер
```bash
sudo systemctl start astrocoins
sudo systemctl start nginx
```

### 11. Проверить статус
```bash
sudo systemctl status astrocoins
sudo systemctl status nginx
```

## 🎯 Что проверить после обновления:

### В админке Django (https://ваш-домен/admin/):
1. **Города** - должна появиться новая модель City
2. **Школы** - должна появиться новая модель School  
3. **Курсы** - должна появиться новая модель Course
4. **Родители** - должна появиться новая модель Parent
5. **Группы** - должны появиться новые поля (курс, школа, дата первого урока, куратор, кабинет, время)

### В интерфейсе (https://ваш-домен/):
1. **Навигация** - должно появиться выпадающее меню "Школьная система"
2. **Управление городами** - `/city-management/`
3. **Управление школами** - `/school-management/`
4. **Управление родителями** - `/parent-management/`
5. **Создание групп** - обновленная форма в `/groups/`
6. **Профиль ученика** - должна отображаться информация о родителе

## 🔧 Создание тестовых данных:

После обновления можно создать тестовые данные:

```bash
python manage.py shell -c "
from core.models import City, School, Course

# Создаем города
moscow = City.objects.create(name='Москва')
spb = City.objects.create(name='Санкт-Петербург')

# Создаем школы
school1 = School.objects.create(
    city=moscow,
    name='ГБОУ Школа № 1234',
    director='Иванов Иван Иванович',
    representative='Петрова Анна Сергеевна',
    address='г. Москва, ул. Пушкина, д. 10',
    phone='+7 (495) 123-45-67',
    email='school1234@edu.mos.ru'
)

# Создаем курсы
Course.objects.create(
    school=school1,
    name='Программирование на Python',
    description='Изучение основ программирования',
    duration_hours=72,
    is_active=True
)

print('Тестовые данные созданы!')
"
```

## 🆘 В случае проблем:

### Откат к предыдущей версии:
```bash
git log --oneline -5  # посмотреть последние коммиты
git reset --hard COMMIT_HASH  # откатиться к нужному коммиту
python manage.py migrate
sudo systemctl restart astrocoins
```

### Восстановление БД из резервной копии:
```bash
sudo -u postgres psql -d astrocoins_db -f backup_YYYYMMDD_HHMMSS.sql
```

## 📞 Поддержка:
При возникновении проблем обращайтесь к разработчику.

---
**AstroCoins v2.1** - Готово к продакшену! 🚀