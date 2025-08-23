from django.core.management.base import BaseCommand
from core.models import User

class Command(BaseCommand):
    help = 'Проверяет всех пользователей в системе'

    def handle(self, *args, **options):
        self.stdout.write("=== Все пользователи в базе данных ===")
        
        users = User.objects.all().order_by('id')
        for user in users:
            self.stdout.write(f"ID: {user.id}, Username: {user.username}, Role: {user.role}, Active: {user.is_active}")
        
        self.stdout.write(f"\n=== Статистика ===")
        self.stdout.write(f"Всего пользователей: {User.objects.count()}")
        self.stdout.write(f"Активных: {User.objects.filter(is_active=True).count()}")
        self.stdout.write(f"Учителей: {User.objects.filter(role='teacher').count()}")
        self.stdout.write(f"Админов городов: {User.objects.filter(role='city_admin').count()}")
        self.stdout.write(f"Старых админов: {User.objects.filter(role='admin').count()}")
        self.stdout.write(f"Учеников: {User.objects.filter(role='student').count()}")
        
        # Проверим, кого найдет форма
        from core.forms import GroupForm
        form = GroupForm()
        
        self.stdout.write(f"\n=== Что видит форма GroupForm ===")
        self.stdout.write("Преподаватели в форме:")
        for teacher in form.fields['teacher'].queryset:
            self.stdout.write(f"  - {teacher.username} (role: {teacher.role})")
            
        self.stdout.write("Кураторы в форме:")
        for curator in form.fields['curator'].queryset:
            self.stdout.write(f"  - {curator.username} (role: {curator.role})")

