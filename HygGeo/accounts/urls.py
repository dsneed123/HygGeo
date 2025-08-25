# accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication URLs
    path('signup/', views.signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Password reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
         name='password_reset_complete'),
    
    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/delete/', views.delete_account_view, name='delete_account'),
    
    # Survey URLs
    path('survey/', views.survey_view, name='survey'),
    path('survey/success/', views.survey_success_view, name='survey_success'),
    
    # Community features
    path('users/', views.user_list_view, name='user_list'),
    path('users/<str:username>/', views.public_profile_view, name='public_profile'),
    path('create/', views.create_trip, name='create_trip'),
    path('<int:pk>/', views.trip_detail_view, name='trip_detail'),
    path('', views.trip_list_view, name='trip_list'),
    path('my-trips/', views.my_trips_view, name='my_trips'),

        # Community features
    path('trips/create/', views.create_trip, name='create_trip'),
    path('trips/', views.trip_list_view, name='trip_list'),
    path('trips/<int:pk>/', views.trip_detail_view, name='trip_detail'),
    path('trips/<int:pk>/edit/', views.edit_trip_view, name='edit_trip'),
    path('trips/<int:pk>/delete/', views.delete_trip_view, name='delete_trip'),

    path('messages/', views.message_list_view, name='message_list'),

    # For starting a new message (no preselected user)
    path('messages/send/', views.send_message_view, name='send_message'),

    # For messaging a specific user (from trip card, profile, etc.)
   

    path('messages/conversation/<int:conversation_id>/', views.conversation_view, name='conversation'),
    path('messages/<int:message_id>/delete/', views.delete_message_view, name='delete_message'),
    # accounts/urls.py
     path("messages/send/<str:username>/", views.send_message_view, name="send_message"),

]