from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.text import slugify
from .validators import validate_file_type, validate_file_size
import uuid
import re

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

class User(AbstractUser):
    """
    Пользовательская модель пользователя с дополнительными полями
    """
    ROLE_CHOICES = [
        ('student', 'Ученик'),
        ('teacher', 'Преподаватель'),
        ('admin', 'Администратор'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    group = models.ForeignKey('Group', on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    
    # Дополнительные поля для учеников
    birth_date = models.DateField(null=True, blank=True, verbose_name='Дата рождения')
    parent_full_name = models.CharField(max_length=255, blank=True, verbose_name='ФИО родителя')
    parent_phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон родителя')

    def is_teacher(self):
        return self.role == 'teacher' or self.role == 'admin'
    
    def is_student(self):
        return self.role == 'student'

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    astrocoins = models.DecimalField(max_digits=10, decimal_places=2, default=0)
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
    amount = models.DecimalField(max_digits=10, decimal_places=2)
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
    slug = models.SlugField(unique=True, blank=True)  # blank=True позволит создать slug автоматически
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
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
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-featured', '-created_at']

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
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def is_in_stock(self):
        return self.stock > 0

class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

class Group(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teaching_groups')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']

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