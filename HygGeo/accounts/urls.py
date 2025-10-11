
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication URLs
    path('admin/analytics/', views.analytics_dashboard, name='analytics'),

    # Email export URLs
    path('admin/export/emails-csv/', views.export_all_emails_csv, name='export_all_emails_csv'),
    path('admin/export/emails-txt/', views.export_all_emails_text, name='export_all_emails_text'),
    path('admin/export/active-emails-csv/', views.export_active_emails_csv, name='export_active_emails_csv'),
    path('admin/export/active-emails-txt/', views.export_active_emails_text, name='export_active_emails_text'),
    path('admin/export/mail-merge-premium/', views.export_mail_merge_premium, name='export_mail_merge_premium'),

    # Email management URLs
    path('admin/email/', views.email_management, name='email_management'),
    path('admin/email/create-template/', views.create_email_template, name='create_email_template'),
    path('admin/email/send/<int:template_id>/', views.send_template_email, name='send_template_email'),

    # Subscription management URLs
    path('unsubscribe/<str:token>/', views.unsubscribe_view, name='unsubscribe'),
    path('resubscribe/<str:token>/', views.resubscribe_view, name='resubscribe'),

    # JSON export URLs
    path('admin/export/experience-types-json/', views.export_experience_types_json, name='export_experience_types_json'),
    path('admin/export/categories-json/', views.export_categories_json, name='export_categories_json'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Password reset URLs
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt'
         ),
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
    path('users/<str:username>/trips/', views.user_trips_view, name='user_trips'),  # NEW LINE
    
    # Trip URLs
    path('create/', views.create_trip, name='create_trip'),
    path('<int:pk>/', views.trip_detail_view, name='trip_detail'),
    path('', views.trip_list_view, name='trip_list'),
    path('my-trips/', views.my_trips_view, name='my_trips'),
    path('trips/create/', views.create_trip, name='create_trip'),
    path('trips/', views.trip_list_view, name='trip_list'),
    path('trips/<int:pk>/', views.trip_detail_view, name='trip_detail'),
    path('trips/<int:pk>/edit/', views.edit_trip_view, name='edit_trip'),
    path('trips/<int:pk>/delete/', views.delete_trip_view, name='delete_trip'),

    # Message URLs
    path('messages/', views.message_list_view, name='message_list'),
    path('messages/send/', views.send_message_view, name='send_message'),
    path('messages/conversation/<int:conversation_id>/', views.conversation_view, name='conversation'),
    path('messages/<int:message_id>/delete/', views.delete_message_view, name='delete_message'),
    path("messages/send/<str:username>/", views.send_message_view, name="send_message"),
    path('debug-spaces/', views.debug_spaces, name='debug_spaces'),
    path('test-upload/', views.test_upload, name='test_upload'),
    path('debug-storage/', views.debug_storage, name='debug_storage'),

    # Legal pages
    path('privacy/', views.privacy_policy_view, name='privacy_policy'),
    path('faq/', views.faq_view, name='faq'),
]
