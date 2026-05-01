from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('fichas.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='login.html')),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/')),
]

if settings.DEBUG:
    from pathlib import Path
    BASE_DIR = Path(__file__).resolve().parent.parent
    urlpatterns += static(settings.STATIC_URL, document_root=BASE_DIR / 'static')
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)