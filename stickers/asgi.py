import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import stickers.routing  # Убедитесь, что этот импорт корректен и файл routing.py существует в приложении stickers

# Устанавливаем переменную окружения для настроек Django
# Замените 'your_project_name.settings' на 'stickers_project.settings'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stickers_project.settings')

# Получаем стандартное ASGI-приложение Django для HTTP-запросов
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,  # Используем полученное выше приложение для HTTP
    "websocket": AuthMiddlewareStack(
        URLRouter(
            stickers.routing.websocket_urlpatterns
        )
    ),
})