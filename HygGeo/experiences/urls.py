# experiences/urls.py
from django.urls import path
from . import views

app_name = 'experiences'

urlpatterns = [
    # Recommendations
    path('recommendations/', views.recommendations_view, name='recommendations'),
    path('bookmarks/', views.my_bookmarks_view, name='my_bookmarks'),
    
    # Experiences
    path('', views.experience_list_view, name='experience_list'),
    path('add/', views.add_experience, name='add_experience'),  # Moved before detail view
    path('experience/<slug:slug>/', views.experience_detail_view, name='experience_detail'),
    
    # Destinations - SPECIFIC PATHS FIRST, THEN GENERAL ONES
    path('destinations/', views.destination_list_view, name='destination_list'),
    path('destinations/add/', views.add_destination, name='add_destination'),  # MOVED BEFORE <slug:slug>
    path('destinations/<slug:slug>/', views.destination_detail_view, name='destination_detail'),  # MOVED AFTER add/
    
    # Providers, Experience Types, Categories - specific before general
    path('providers/add/', views.add_provider, name='add_provider'),
    path('experience-types/add/', views.add_experience_type, name='add_experience_type'),
    path('categories/add/', views.add_category, name='add_category'),
    
    # Categories
    path('category/<slug:slug>/', views.category_detail_view, name='category_detail'),
    
    # AJAX endpoints
    path('api/track-click/<uuid:experience_id>/', views.track_affiliate_click, name='track_affiliate_click'),
    path('api/bookmark/<uuid:experience_id>/', views.bookmark_experience, name='bookmark_experience'),
]