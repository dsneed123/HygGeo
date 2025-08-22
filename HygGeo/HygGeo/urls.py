# HygGeo/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import index, admin_dashboard

urlpatterns = [
    # Admin Dashboard - BEFORE Django admin to avoid conflicts
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    
    # Django admin
    path('admin/', admin.site.urls),
    
    # Homepage
    path('', index, name='index'),
    
    # Include app URLs (let each app handle its own URLs)
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # Built-in auth views
    path('experiences/', include('experiences.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)