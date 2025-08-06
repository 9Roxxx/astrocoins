from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe
from .models import User, Profile, Transaction, Product, Purchase, ProductCategory, Group

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'groups')
    fieldsets = (
        ('Основная информация', {'fields': ('username', 'password')}),
        ('Персональные данные', {'fields': ('first_name', 'last_name', 'email')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'astrocoins', 'created_at')
    search_fields = ('user__username', 'user__email')
    list_filter = ('created_at',)
    fieldsets = (
        ('Пользователь', {'fields': ('user',)}),
        ('Баланс', {'fields': ('astrocoins',)}),
        ('Информация', {'fields': ('created_at',)}),
    )

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'amount', 'get_transaction_type_display', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('sender__username', 'receiver__username', 'description')
    
    def get_transaction_type_display(self, obj):
        types = {
            'TRANSFER': 'Перевод',
            'PURCHASE': 'Покупка',
            'EARN': 'Начисление',
            'SPEND': 'Списание'
        }
        return types.get(obj.transaction_type, obj.transaction_type)
    get_transaction_type_display.short_description = 'Тип транзакции'

    fieldsets = (
        ('Участники', {
            'fields': ('sender', 'receiver')
        }),
        ('Детали транзакции', {
            'fields': ('amount', 'transaction_type', 'description')
        }),
        ('Информация', {
            'fields': ('created_at',)
        }),
    )

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_icon_display', 'get_featured_display', 'order', 'get_products_count')
    list_filter = ('is_featured',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')

    def get_featured_display(self, obj):
        return "🔥 Горячая" if obj.is_featured else "Обычная"
    get_featured_display.short_description = 'Тип категории'

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Настройки отображения', {
            'fields': ('icon', 'order', 'is_featured')
        }),
    )

    def get_icon_display(self, obj):
        if obj.icon:
            return mark_safe(f'<i class="fas {obj.icon}"></i> {obj.icon}')
        return '-'
    get_icon_display.short_description = 'Иконка'

    def get_products_count(self, obj):
        return obj.products.count()
    get_products_count.short_description = 'Товаров'

    class Media:
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',)
        }

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'get_availability_display', 'get_featured_display', 'get_type_display', 'get_image')
    list_filter = ('category', 'available', 'featured', 'is_digital', 'created_at')
    search_fields = ('name', 'description', 'category__name')
    readonly_fields = ('get_image',)
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'description', 'category', 'price')
        }),
        ('Изображение', {
            'fields': ('image', 'get_image')
        }),
        ('Настройки', {
            'fields': ('available', 'stock', 'is_digital', 'featured')
        }),
    )

    def get_availability_display(self, obj):
        return "✅ В наличии" if obj.available else "❌ Нет в наличии"
    get_availability_display.short_description = 'Доступность'

    def get_featured_display(self, obj):
        return "⭐ Популярный" if obj.featured else "Обычный"
    get_featured_display.short_description = 'Статус'

    def get_type_display(self, obj):
        return "💻 Цифровой" if obj.is_digital else "📦 Физический"
    get_type_display.short_description = 'Тип товара'

    def get_image(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" height="100" style="object-fit: cover; border-radius: 8px;" />')
        return 'Нет изображения'
    get_image.short_description = 'Изображение'

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'total_price', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'product__name')
    fieldsets = (
        ('Покупатель и товар', {
            'fields': ('user', 'product')
        }),
        ('Детали покупки', {
            'fields': ('quantity', 'total_price')
        }),
        ('Информация', {
            'fields': ('created_at',)
        }),
    )