import os
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _

def validate_file_type(upload):
    # Список разрешенных расширений файлов
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    # Список разрешенных MIME-типов
    ALLOWED_MIME_TYPES = [
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp'
    ]
    
    # Проверка расширения файла
    ext = os.path.splitext(upload.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            _('Неподдерживаемый тип файла. Разрешены только: %(types)s'),
            params={'types': ', '.join(ALLOWED_EXTENSIONS)}
        )
    
    # Проверка MIME-типа
    content_type = upload.content_type.lower()
    if content_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            _('Неподдерживаемый тип файла. Разрешены только изображения.')
        )

def validate_file_size(upload):
    # Максимальный размер файла - 5MB
    MAX_UPLOAD_SIZE = 5 * 1024 * 1024
    
    if upload.size > MAX_UPLOAD_SIZE:
        raise ValidationError(
            _('Файл слишком большой. Максимальный размер: %(max_size)s'),
            params={'max_size': filesizeformat(MAX_UPLOAD_SIZE)}
        )