# HygGeo/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.generic import RedirectView
from accounts.views import index, admin_dashboard, analytics_dashboard, global_search_view, search_autocomplete
from experiences.views import sitemap_view

urlpatterns = [
    # Admin Dashboard - BEFORE Django admin to avoid conflicts
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin/analytics/', analytics_dashboard, name='analytics_dashboard'),

    # Django admin
    path('admin/', admin.site.urls),

    # Homepage
    path('', index, name='index'),

    # Global search
    path('search/', global_search_view, name='global_search'),
    path('search/autocomplete/', search_autocomplete, name='search_autocomplete'),
    
    # Include app URLs (let each app handle its own URLs)
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # Built-in auth views
    path('accounts/', include('allauth.urls')),  # Allauth OAuth URLs
    path('experiences/', include('experiences.urls')),
    path('task-management/', include('task_management.urls')),

    # Top-level subscription management is handled in accounts.urls

    # SEO URLs
    path('sitemap.xml', sitemap_view, name='sitemap'),
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
    path('site.webmanifest', RedirectView.as_view(url='/static/site.webmanifest', permanent=True)),
    path('browserconfig.xml', RedirectView.as_view(url='/static/browserconfig.xml', permanent=True)),
    path('robots.txt', RedirectView.as_view(url='/static/robots.txt', permanent=True)),
]

# Serve media files during development
# FIXED: Serve media files in production AND development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve static files during development only (WhiteNoise handles this in production)  
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)