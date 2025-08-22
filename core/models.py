from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils import timezone
from django.utils.text import slugify
from .validators import validate_file_type, validate_file_size
import uuid
import re

class CaseInsensitiveUserManager(UserManager):
    """Менеджер пользователей с поддержкой регистронезависимого поиска"""
    
    def get_by_natural_key(self, username):
        """Поиск пользователя без учета регистра"""
        return self.get(username__iexact=username)
    
    def authenticate_user(self, username, password):
        """Аутентификация пользователя без учета регистра"""
        try:
            user = self.get(username__iexact=username)
            if user.check_password(password):
                return user
        except self.model.DoesNotExist:
            pass
        return None

def create_cyrillic_slug(text):
    """Создает slug с поддержкой кириллицы"""
    # Словарь для транслитерации кириллицы
    cyrillic_to_latin = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'YO',
        'Ж': 'ZH', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'TS', 'Ч': 'CH', 'Ш': 'SH', 'Щ': 'SCH',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'YU', 'Я': 'YA'
    }
    
    # Транслитерируем кириллицу
    transliterated = ''
    for char in text:
        if char in cyrillic_to_latin:
            transliterated += cyrillic_to_latin[char]
        else:
            transliterated += char
    
    # Применяем стандартный slugify к транслитерированному тексту
    slug = slugify(transliterated)
    
    # Если slug пустой, генерируем уникальный
    if not slug:
        slug = f"category-{uuid.uuid4().hex[:8]}"
    
    return slug

class Parent(models.Model):
    """
    Модель родителя с полной информацией
    """
    full_name = models.CharField(max_length=255, verbose_name='ФИО родителя')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    address = models.TextField(blank=True, verbose_name='Адрес')
    work_place = models.CharField(max_length=255, blank=True, verbose_name='Место работы')
    notes = models.TextField(blank=True, verbose_name='Дополнительные заметки')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Родитель'
        verbose_name_plural = 'Родители'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name

    @property
    def students_count(self):
        """Количество детей у этого родителя"""
        return self.students.count()

class User(AbstractUser):
    """
    Пользовательская модель пользователя с дополнительными полями
    """
    ROLE_CHOICES = [
        ('student', 'Ученик'),
        ('teacher', 'Преподаватель'),
        ('city_admin', 'Администратор города'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    
    # Добавляем кастомный менеджер для регистронезависимого поиска
    objects = CaseInsensitiveUserManager()
    group = models.ForeignKey('Group', on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    
    # Поля для региональной системы
    city = models.ForeignKey('City', on_delete=models.SET_NULL, null=True, blank=True, 
                            verbose_name='Город', help_text='Основной город (для администраторов и учеников)')
    cities = models.ManyToManyField('City', blank=True, related_name='teachers', 
                                   verbose_name='Города', help_text='Города где работает учитель')
    
    # Дополнительные поля для учеников
    birth_date = models.DateField(null=True, blank=True, verbose_name='Дата рождения')
    parent_full_name = models.CharField(max_length=255, blank=True, verbose_name='ФИО родителя (устаревшее)')
    parent_phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон родителя (устаревшее)')
    
    # Новая связь с моделью Parent
    parent = models.ForeignKey('Parent', on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='students', verbose_name='Родитель')

    def is_teacher(self):
        return self.role == 'teacher' or self.role == 'city_admin'
    
    def is_student(self):
        return self.role == 'student'
    
    def get_cities(self):
        """Получить все города пользователя"""
        if self.role == 'teacher':
            return self.cities.all()
        elif self.role in ['student', 'city_admin'] and self.city:
            return [self.city]
        return []
    
    def can_access_city(self, city):
        """Проверить может ли пользователь работать с данным городом"""
        if self.is_superuser:
            return True
        if self.role == 'teacher':
            return city in self.cities.all()
        elif self.role in ['student', 'city_admin']:
            return self.city == city
        return False
    
    def get_parent_info(self):
        """Получить информацию о родителе (новая модель или старые поля)"""
        if self.parent:
            return {
                'full_name': self.parent.full_name,
                'phone': self.parent.phone,
                'email': self.parent.email,
                'address': self.parent.address,
                'work_place': self.parent.work_place,
                'notes': self.parent.notes,
            }
        elif self.parent_full_name or self.parent_phone:
            return {
                'full_name': self.parent_full_name,
                'phone': self.parent_phone,
                'email': '',
                'address': '',
                'work_place': '',
                'notes': '',
            }
        return None

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    astrocoins = models.IntegerField(default=0)  # Изменено на целые числа
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username}'s profile"

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('EARN', 'Earned'),
        ('SPEND', 'Spent'),
        ('TRANSFER', 'Transfer'),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_transactions')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_transactions')
    amount = models.IntegerField()  # Изменено на целые числа
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.transaction_type}: {self.amount} AstroCoins"

class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False)  # Для "горячих" категорий (🔥)
    icon = models.CharField(max_length=50, blank=True)  # Для иконок Font Awesome
    order = models.PositiveIntegerField(default=0)  # Для сортировки
    
    # Региональная система - каждая категория принадлежит одному городу
    city = models.ForeignKey('City', on_delete=models.CASCADE, related_name='categories',
                            verbose_name='Город', help_text='Город в котором создана эта категория',
                            null=True, blank=True)  # Временно nullable для миграции
    
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Категория товаров'
        verbose_name_plural = 'Категории товаров'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            # Используем нашу функцию с поддержкой кириллицы
            base_slug = create_cyrillic_slug(self.name)
            slug = base_slug
            
            # Проверяем уникальность slug
            counter = 1
            while ProductCategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        super().save(*args, **kwargs)

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, max_length=255)  # Увеличено для длинных названий
    description = models.TextField()
    price = models.IntegerField()  # Изменено на целые числа
    image = models.ImageField(
        upload_to='products/',
        null=True,
        blank=True,
        validators=[validate_file_type, validate_file_size]
    )
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, related_name='products')
    available = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=1)  # Количество в наличии
    is_digital = models.BooleanField(default=False)  # Цифровой товар (например, Roblox, Steam)
    featured = models.BooleanField(default=False)  # Популярный товар
    
    # Региональная система - товар принадлежит одному городу
    city = models.ForeignKey('City', on_delete=models.CASCADE, related_name='products',
                            verbose_name='Город', help_text='Город в котором создан этот товар',
                            null=True, blank=True)  # Временно nullable для миграции
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-featured', '-created_at']
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.price < 0:
            raise ValidationError('Цена не может быть отрицательной')
        if self.price > 10000:
            raise ValidationError('Цена слишком высокая (максимум 10000 AC)')
        if self.stock < 0:
            raise ValidationError('Количество не может быть отрицательным')
        if len(self.name.strip()) == 0:
            raise ValidationError('Название товара не может быть пустым')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_availability_display(self):
        return "В наличии" if self.available else "Нет в наличии"

    def get_type_display(self):
        return "Цифровой товар" if self.is_digital else "Физический товар"

    def get_featured_display(self):
        return "Популярный" if self.featured else "Обычный"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = create_cyrillic_slug(self.name)
            self.slug = base_slug
            
            # Проверяем уникальность slug и добавляем номер если нужно
            counter = 1
            while Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
                
        super().save(*args, **kwargs)

    @property
    def is_in_stock(self):
        return self.stock > 0

class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    delivered = models.BooleanField(default=False, verbose_name='Товар выдан')
    delivered_date = models.DateTimeField(null=True, blank=True, verbose_name='Дата выдачи')
    notes = models.TextField(blank=True, verbose_name='Примечания к выдаче')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"
    
    def mark_as_delivered(self):
        """Отметить товар как выданный"""
        self.delivered = True
        self.delivered_date = timezone.now()
        self.save()

class City(models.Model):
    """
    Модель города
    """
    name = models.CharField(max_length=100, verbose_name='Название города')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def schools_count(self):
        """Количество школ в городе"""
        return self.schools.count()


class School(models.Model):
    """
    Модель школы/учреждения
    """
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='schools', verbose_name='Город')
    name = models.CharField(max_length=255, verbose_name='Название учреждения')
    director = models.CharField(max_length=255, verbose_name='Директор')
    representative = models.CharField(max_length=255, verbose_name='Представитель')
    address = models.TextField(verbose_name='Адрес')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    website = models.URLField(blank=True, verbose_name='Сайт')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Школа'
        verbose_name_plural = 'Школы'
        ordering = ['city__name', 'name']

    def __str__(self):
        return f"{self.name} ({self.city.name})"

    @property
    def courses_count(self):
        """Количество курсов в школе"""
        return self.courses.count()

    @property
    def groups_count(self):
        """Количество групп в школе"""
        return self.groups.count()


class Course(models.Model):
    """
    Модель курса
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='courses', verbose_name='Школа')
    name = models.CharField(max_length=255, verbose_name='Название курса')
    description = models.TextField(blank=True, verbose_name='Описание курса')
    duration_hours = models.PositiveIntegerField(default=0, verbose_name='Продолжительность (часы)')
    is_active = models.BooleanField(default=True, verbose_name='Активный курс')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ['school__name', 'name']

    def __str__(self):
        return f"{self.name} - {self.school.name}"

    @property
    def groups_count(self):
        """Количество групп по этому курсу"""
        return self.groups.count()


class Group(models.Model):
    """
    Обновленная модель группы с расширенными полями
    """
    name = models.CharField(max_length=100, verbose_name='Название группы')
    description = models.TextField(blank=True, verbose_name='Описание')
    
    # Связи (временно nullable для миграции)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups', verbose_name='Курс', null=True, blank=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='groups', verbose_name='Школа', null=True, blank=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teaching_groups', 
                               limit_choices_to={'role__in': ['teacher', 'city_admin']}, verbose_name='Преподаватель')
    curator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                               related_name='curated_groups', limit_choices_to={'role': 'city_admin'}, 
                               verbose_name='Куратор')
    
    # Расписание и место
    first_lesson_date = models.DateField(null=True, blank=True, verbose_name='Дата первого урока')
    classroom = models.CharField(max_length=50, blank=True, verbose_name='Кабинет')
    lesson_time = models.TimeField(null=True, blank=True, verbose_name='Время занятий')
    
    # Статус
    is_active = models.BooleanField(default=True, verbose_name='Активная группа')
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['-is_active', '-created_at']

    def __str__(self):
        return f"{self.name} - {self.course.name} ({self.school.name})"

    @property
    def students_count(self):
        """Количество учеников в группе"""
        return self.students.count()

    def clean(self):
        """Валидация модели"""
        from django.core.exceptions import ValidationError
        
        # Проверяем, что курс принадлежит выбранной школе
        if self.course and self.school and self.course.school != self.school:
            raise ValidationError({
                'course': 'Выбранный курс не принадлежит указанной школе.'
            })

class AwardReason(models.Model):
    name = models.CharField(max_length=200)
    coins = models.PositiveIntegerField()
    cooldown_days = models.PositiveIntegerField(default=0)  # 0 означает без ограничений
    is_special = models.BooleanField(default=False)  # Для особых наград (например, переход на следующий год)

    def __str__(self):
        return f"{self.name} ({self.coins} AC)"

class CoinAward(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_awards')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_awards')
    reason = models.ForeignKey(AwardReason, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()
    created_at = models.DateTimeField(default=timezone.now)
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student.username} получил {self.amount} AC от {self.teacher.username}"

    def save(self, *args, **kwargs):
        if not self.pk:  # Только при создании
            # Создаем транзакцию
            Transaction.objects.create(
                sender=self.teacher,
                receiver=self.student,
                amount=self.amount,
                transaction_type='EARN',
                description=f"{self.reason.name}\n{self.comment if self.comment else ''}"
            )
            
            # Обновляем баланс студента
            profile = self.student.profile
            profile.astrocoins += self.amount
            profile.save()
            
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Создаем отрицательную транзакцию при удалении награды
        Transaction.objects.create(
            sender=self.teacher,
            receiver=self.student,
            amount=-self.amount,
            transaction_type='EARN',
            description=f"Отмена: {self.reason.name}\n{self.comment if self.comment else ''}"
        )
        
        # Обновляем баланс студента
        profile = self.student.profile
        profile.astrocoins -= self.amount
        profile.save()
        
        super().delete(*args, **kwargs)