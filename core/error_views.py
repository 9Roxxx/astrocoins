"""
Кастомные обработчики ошибок для красивых страниц ошибок
"""
from django.shortcuts import render


def custom_404_view(request, exception):
    """Кастомная страница 404 - Страница не найдена"""
    return render(request, '404.html', {}, status=404)


def custom_500_view(request):
    """Кастомная страница 500 - Внутренняя ошибка сервера"""
    return render(request, '500.html', {}, status=500)


def custom_403_view(request, exception):
    """Кастомная страница 403 - Доступ запрещён"""
    return render(request, '403.html', {}, status=403)


def custom_400_view(request, exception):
    """Кастомная страница 400 - Неверный запрос"""
    return render(request, '403.html', {}, status=400)  # Используем 403 template для 400