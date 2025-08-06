import os
import sys
import shutil
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core import management

class Command(BaseCommand):
    help = 'Creates a backup of the database and media files'

    def handle(self, *args, **options):
        # Создаем директорию для бэкапов если её нет
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Текущая дата для имени файла
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Бэкап базы данных
        db_backup_path = os.path.join(backup_dir, f'db_backup_{timestamp}.json')
        try:
            management.call_command('dumpdata', output=db_backup_path, indent=4)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully backed up database to {db_backup_path}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error backing up database: {str(e)}')
            )
            return

        # Бэкап медиафайлов
        media_backup_path = os.path.join(backup_dir, f'media_backup_{timestamp}')
        try:
            if os.path.exists(settings.MEDIA_ROOT):
                shutil.copytree(settings.MEDIA_ROOT, media_backup_path)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully backed up media files to {media_backup_path}')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error backing up media files: {str(e)}')
            )

        # Очистка старых бэкапов (оставляем только последние 5)
        try:
            # Получаем список всех файлов бэкапов
            db_backups = sorted([f for f in os.listdir(backup_dir) if f.startswith('db_backup_')])
            media_backups = sorted([f for f in os.listdir(backup_dir) if f.startswith('media_backup_')])

            # Удаляем старые бэкапы БД
            while len(db_backups) > 5:
                os.remove(os.path.join(backup_dir, db_backups.pop(0)))

            # Удаляем старые бэкапы медиафайлов
            while len(media_backups) > 5:
                shutil.rmtree(os.path.join(backup_dir, media_backups.pop(0)))

            self.stdout.write(
                self.style.SUCCESS('Old backups cleaned up successfully')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error cleaning up old backups: {str(e)}')
            )