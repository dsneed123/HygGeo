# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.db.models import Count, Q
import csv
from .models import UserProfile, TravelSurvey

def export_emails_csv(modeladmin, request, queryset):
    """Export user emails as CSV file"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="user_emails.csv"'

    writer = csv.writer(response)
    writer.writerow(['Email', 'Username', 'First Name', 'Last Name', 'Date Joined', 'Is Active'])

    for user in queryset:
        writer.writerow([
            user.email,
            user.username,
            user.first_name,
            user.last_name,
            user.date_joined.strftime('%Y-%m-%d'),
            'Yes' if user.is_active else 'No'
        ])

    return response

export_emails_csv.short_description = "Export selected user emails as CSV"

def export_all_emails_csv(modeladmin, request, queryset):
    """Export ALL user emails as CSV file (ignores selection)"""
    all_users = User.objects.all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="all_user_emails.csv"'

    writer = csv.writer(response)
    writer.writerow(['Email', 'Username', 'First Name', 'Last Name', 'Date Joined', 'Is Active'])

    for user in all_users:
        writer.writerow([
            user.email,
            user.username,
            user.first_name,
            user.last_name,
            user.date_joined.strftime('%Y-%m-%d'),
            'Yes' if user.is_active else 'No'
        ])

    return response

export_all_emails_csv.short_description = "Export ALL user emails as CSV"

def export_emails_text(modeladmin, request, queryset):
    """Export user emails as plain text file (comma-separated)"""
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="user_emails.txt"'

    emails = [user.email for user in queryset if user.email]
    response.write(', '.join(emails))

    return response

export_emails_text.short_description = "Export selected emails as text file"

def export_all_emails_text(modeladmin, request, queryset):
    """Export ALL user emails as plain text file (ignores selection)"""
    all_users = User.objects.all()
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="all_user_emails.txt"'

    emails = [user.email for user in all_users if user.email]
    response.write(', '.join(emails))

    return response

export_all_emails_text.short_description = "Export ALL emails as text file"

class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class UserAdmin(BaseUserAdmin):
    """Extended User admin with profile inline"""
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined', 'email_status')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    actions = [export_emails_csv, export_all_emails_csv, export_emails_text, export_all_emails_text]

    def email_status(self, obj):
        """Display email status with color coding"""
        if obj.email:
            return format_html('<span style="color: green;">✓ {}</span>', obj.email)
        else:
            return format_html('<span style="color: red;">✗ No email</span>')

    email_status.short_description = 'Email Status'

    def get_urls(self):
        """Add custom admin URLs"""
        urls = super().get_urls()
        custom_urls = [
            path('email-export/', self.admin_site.admin_view(self.email_export_view), name='email_export'),
        ]
        return custom_urls + urls

    def email_export_view(self, request):
        """Custom view for email export with statistics"""
        total_users = User.objects.count()
        users_with_email = User.objects.exclude(email='').count()
        users_without_email = total_users - users_with_email
        active_users_with_email = User.objects.filter(is_active=True).exclude(email='').count()

        context = {
            'title': 'Email Export Dashboard',
            'opts': self.model._meta,
            'has_permission': True,
            'total_users': total_users,
            'users_with_email': users_with_email,
            'users_without_email': users_without_email,
            'active_users_with_email': active_users_with_email,
        }

        return render(request, 'admin/email_export.html', context)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile model"""
    list_display = ('user', 'location', 'sustainability_priority', 'created_at')
    list_filter = ('sustainability_priority', 'created_at')
    search_fields = ('user__username', 'user__email', 'location')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Profile Details', {
            'fields': ('bio', 'location', 'birth_date', 'avatar')
        }),
        ('Travel Preferences', {
            'fields': ('sustainability_priority',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(TravelSurvey)
class TravelSurveyAdmin(admin.ModelAdmin):
    """Admin for TravelSurvey model"""
    list_display = ('user', 'budget_range', 'travel_frequency', 'group_size_preference', 'completed_at')
    list_filter = ('budget_range', 'travel_frequency', 'group_size_preference', 'trip_duration_preference', 'completed_at')
    search_fields = ('user__username', 'user__email', 'dream_destination')
    readonly_fields = ('completed_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Travel Preferences', {
            'fields': (
                'travel_styles', 
                'accommodation_preferences', 
                'transport_preferences',
                'sustainability_factors'
            )
        }),
        ('Trip Details', {
            'fields': (
                'budget_range',
                'travel_frequency', 
                'group_size_preference',
                'trip_duration_preference'
            )
        }),
        ('Personal Goals', {
            'fields': ('dream_destination', 'sustainability_goals')
        }),
        ('Metadata', {
            'fields': ('completed_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')

# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Customize admin site headers
admin.site.site_header = "HygGeo Administration"
admin.site.site_title = "HygGeo Admin"
admin.site.index_title = "Welcome to HygGeo Administration"