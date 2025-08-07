from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Назначаем кастомные обработчики для ошибок.
# Django будет использовать их автоматически, когда DEBUG = False.
handler403 = 'core.views.custom_permission_denied_view'
handler404 = 'core.views.custom_page_not_found_view'
handler500 = 'core.views.custom_server_error_view'
