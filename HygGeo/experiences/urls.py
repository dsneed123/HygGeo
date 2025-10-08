# experiences/urls.py
from django.urls import path
from . import views

app_name = 'experiences'

urlpatterns = [
    # Recommendations and Bookmarks
    path('recommendations/', views.recommendations_view, name='recommendations'),
    path('bookmarks/', views.my_bookmarks_view, name='my_bookmarks'),
    path('bookmark/remove/<uuid:experience_id>/', views.remove_bookmark_view, name='remove_bookmark'),
    
    # Experiences
    path('', views.experience_list_view, name='experience_list'),
    path('add/', views.add_experience, name='add_experience'),
    path('experience/<slug:slug>/', views.experience_detail_view, name='experience_detail'),
    path('experience/<slug:slug>/edit/', views.edit_experience, name='edit_experience'),
    path('experience/<slug:slug>/delete/', views.delete_experience, name='delete_experience'),
    
    # Destinations - SPECIFIC PATHS FIRST, THEN GENERAL ONES
    path('destinations/', views.destination_list_view, name='destination_list'),
    path('destinations/add/', views.add_destination, name='add_destination'),
    path('destinations/<slug:slug>/edit/', views.edit_destination, name='edit_destination'),
    path('destinations/<slug:slug>/', views.destination_detail_view, name='destination_detail'),
    
    # Providers, Experience Types, Categories - specific before general
    path('providers/add/', views.add_provider, name='add_provider'),
    path('experience-types/', views.experience_type_list_view, name='experience_type_list'),
    path('experience-types/add/', views.add_experience_type, name='add_experience_type'),
    path('experience-types/<slug:slug>/edit/', views.edit_experience_type, name='edit_experience_type'),
    path('experience-types/<slug:slug>/delete/', views.delete_experience_type, name='delete_experience_type'),
    path('categories/', views.category_list_view, name='category_list'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/<slug:slug>/edit/', views.edit_category, name='edit_category'),
    path('categories/<slug:slug>/delete/', views.delete_category, name='delete_category'),

    # Export URLs
    path('experience-types/export/', views.export_experience_types_csv, name='export_experience_types'),
    path('categories/export/', views.export_categories_csv, name='export_categories'),

    # Categories
    path('category/<slug:slug>/', views.category_detail_view, name='category_detail'),

    # Accommodations
    path('accommodations/', views.accommodation_list_view, name='accommodation_list'),
    path('accommodations/add/', views.add_accommodation, name='add_accommodation'),
    path('accommodations/<slug:slug>/', views.accommodation_detail_view, name='accommodation_detail'),
    path('accommodations/<slug:slug>/edit/', views.edit_accommodation, name='edit_accommodation'),
    path('accommodations/<slug:slug>/delete/', views.delete_accommodation, name='delete_accommodation'),

    # Travel Blogs
    path('blogs/', views.blog_feed, name='blog_feed'),
    path('blogs/my-blogs/', views.my_blogs, name='my_blogs'),
    path('blogs/create/', views.create_blog, name='create_blog'),
    path('blogs/terms/', views.blogger_terms, name='blogger_terms'),
    path('blogs/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('blogs/<slug:slug>/edit/', views.edit_blog, name='edit_blog'),
    path('blogs/<slug:slug>/delete/', views.delete_blog, name='delete_blog'),
    path('blogs/<slug:slug>/like/', views.like_blog, name='like_blog'),

    # AJAX endpoints
    path('api/track-click/<uuid:experience_id>/', views.track_affiliate_click, name='track_affiliate_click'),
    path('api/bookmark/<uuid:experience_id>/', views.bookmark_experience, name='bookmark_experience'),
    path('api/analyze-seo/', views.analyze_seo_ajax, name='analyze_seo_ajax'),
    path('track-booking/<uuid:experience_id>/', views.track_booking_view, name='track_booking'),
    path('about/', views.about_view, name='about'),
]