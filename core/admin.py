from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe
from .models import User, Profile, Transaction, Product, Purchase, ProductCategory, Group, Parent, City, School, Course

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'email', 'get_students_count', 'created_at')
    search_fields = ('full_name', 'phone', 'email', 'work_place')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at', 'get_students_list')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('full_name', 'phone', 'email')
        }),
        ('Дополнительная информация', {
            'fields': ('address', 'work_place', 'notes')
        }),
        ('Дети', {
            'fields': ('get_students_list',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_students_count(self, obj):
        count = obj.students_count
        if count > 0:
            return f"{count} детей"
        return "Нет детей"
    get_students_count.short_description = 'Количество детей'

    def get_students_list(self, obj):
        students = obj.students.all()
        if students:
            student_links = []
            for student in students:
                url = f'/admin/core/user/{student.id}/change/'
                student_links.append(f'<a href="{url}" target="_blank">{student.get_full_name() or student.username}</a>')
            return mark_safe('<br>'.join(student_links))
        return 'Нет привязанных детей'
    get_students_list.short_description = 'Дети'

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'get_parent_info', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'role', 'groups')
    
    fieldsets = (
        ('Основная информация', {'fields': ('username', 'password')}),
        ('Персональные данные', {'fields': ('first_name', 'last_name', 'email')}),
        ('Роль и группа', {'fields': ('role', 'group')}),
        ('Информация ученика', {'fields': ('birth_date', 'parent')}),
        ('Устаревшие поля родителя', {
            'fields': ('parent_full_name', 'parent_phone'),
            'classes': ('collapse',),
            'description': 'Эти поля сохранены для совместимости. Используйте поле "Родитель" выше.'
        }),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    
    def get_parent_info(self, obj):
        if obj.parent:
            return f"{obj.parent.full_name}"
        elif obj.parent_full_name:
            return f"{obj.parent_full_name} (старые данные)"
        return "Не указан"
    get_parent_info.short_description = 'Родитель'

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


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_schools_count', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'get_schools_list')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name',)
        }),
        ('Школы в городе', {
            'fields': ('get_schools_list',)
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_schools_count(self, obj):
        count = obj.schools_count
        return f"{count} школ" if count > 0 else "Нет школ"
    get_schools_count.short_description = 'Количество школ'

    def get_schools_list(self, obj):
        schools = obj.schools.all()
        if schools:
            school_links = []
            for school in schools:
                url = f'/admin/core/school/{school.id}/change/'
                school_links.append(f'<a href="{url}" target="_blank">{school.name}</a>')
            return mark_safe('<br>'.join(school_links))
        return 'Нет школ в городе'
    get_schools_list.short_description = 'Школы'


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'director', 'phone', 'get_courses_count', 'get_groups_count', 'created_at')
    search_fields = ('name', 'director', 'representative', 'address', 'phone', 'email')
    list_filter = ('city', 'created_at')
    readonly_fields = ('created_at', 'get_courses_list', 'get_groups_list')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('city', 'name', 'director', 'representative')
        }),
        ('Контактные данные', {
            'fields': ('address', 'phone', 'email', 'website')
        }),
        ('Курсы', {
            'fields': ('get_courses_list',)
        }),
        ('Группы', {
            'fields': ('get_groups_list',)
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_courses_count(self, obj):
        count = obj.courses_count
        return f"{count} курсов" if count > 0 else "Нет курсов"
    get_courses_count.short_description = 'Курсы'

    def get_groups_count(self, obj):
        count = obj.groups_count
        return f"{count} групп" if count > 0 else "Нет групп"
    get_groups_count.short_description = 'Группы'

    def get_courses_list(self, obj):
        courses = obj.courses.all()
        if courses:
            course_links = []
            for course in courses:
                url = f'/admin/core/course/{course.id}/change/'
                status = "🟢" if course.is_active else "🔴"
                course_links.append(f'<a href="{url}" target="_blank">{status} {course.name}</a>')
            return mark_safe('<br>'.join(course_links))
        return 'Нет курсов в школе'
    get_courses_list.short_description = 'Курсы'

    def get_groups_list(self, obj):
        groups = obj.groups.all()
        if groups:
            group_links = []
            for group in groups:
                url = f'/admin/core/group/{group.id}/change/'
                status = "🟢" if group.is_active else "🔴"
                group_links.append(f'<a href="{url}" target="_blank">{status} {group.name}</a>')
            return mark_safe('<br>'.join(group_links))
        return 'Нет групп в школе'
    get_groups_list.short_description = 'Группы'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'duration_hours', 'get_groups_count', 'get_active_status', 'created_at')
    search_fields = ('name', 'description', 'school__name', 'school__city__name')
    list_filter = ('is_active', 'school__city', 'school', 'created_at')
    readonly_fields = ('created_at', 'get_groups_list')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('school', 'name', 'description')
        }),
        ('Параметры курса', {
            'fields': ('duration_hours', 'is_active')
        }),
        ('Группы по курсу', {
            'fields': ('get_groups_list',)
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_active_status(self, obj):
        return "🟢 Активный" if obj.is_active else "🔴 Неактивный"
    get_active_status.short_description = 'Статус'

    def get_groups_count(self, obj):
        count = obj.groups_count
        return f"{count} групп" if count > 0 else "Нет групп"
    get_groups_count.short_description = 'Группы'

    def get_groups_list(self, obj):
        groups = obj.groups.all()
        if groups:
            group_links = []
            for group in groups:
                url = f'/admin/core/group/{group.id}/change/'
                status = "🟢" if group.is_active else "🔴"
                teacher = group.teacher.get_full_name() or group.teacher.username
                group_links.append(f'<a href="{url}" target="_blank">{status} {group.name}</a> (преп: {teacher})')
            return mark_safe('<br>'.join(group_links))
        return 'Нет групп по этому курсу'
    get_groups_list.short_description = 'Группы'