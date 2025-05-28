from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.shortcuts import redirect

def redirect_to_profile(request):
    return redirect('profile')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('set_language/', include('django.conf.urls.i18n'), name='set_language'),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('accounts/profile/', redirect_to_profile),  # Добавляем маршрут
]

urlpatterns += i18n_patterns(
    path('', include('stickers.urls')),
)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)