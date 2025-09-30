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
from django.contrib import messages
from django.utils import timezone
from django.template import Template, Context
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import re
from .models import UserProfile, TravelSurvey, EmailTemplate, EmailCampaign, EmailLog
from .email_utils import get_merge_fields

def export_emails_csv(modeladmin, request, queryset):
    """Export user emails as CSV file"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="user_emails.csv"'

    writer = csv.writer(response)
    writer.writerow(['Email', 'Username', 'First Name', 'Last Name', 'Date Joined', 'Is Active', 'Unsubscribe Token', 'Unsubscribe URL'])

    for user in queryset:
        try:
            profile = user.userprofile
            unsub_token = profile.unsubscribe_token or ''
            unsub_url = f"{settings.SITE_URL}{profile.get_unsubscribe_url()}" if unsub_token else ''
        except:
            unsub_token = ''
            unsub_url = ''

        writer.writerow([
            user.email,
            user.username,
            user.first_name,
            user.last_name,
            user.date_joined.strftime('%Y-%m-%d'),
            'Yes' if user.is_active else 'No',
            unsub_token,
            unsub_url
        ])

    return response

export_emails_csv.short_description = "Export selected user emails as CSV"

def export_all_emails_csv(modeladmin, request, queryset):
    """Export ALL user emails as CSV file (ignores selection)"""
    all_users = User.objects.all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="all_user_emails.csv"'

    writer = csv.writer(response)
    writer.writerow(['Email', 'Username', 'First Name', 'Last Name', 'Date Joined', 'Is Active', 'Unsubscribe Token', 'Unsubscribe URL'])

    for user in all_users:
        try:
            profile = user.userprofile
            unsub_token = profile.unsubscribe_token or ''
            unsub_url = f"{settings.SITE_URL}{profile.get_unsubscribe_url()}" if unsub_token else ''
        except:
            unsub_token = ''
            unsub_url = ''

        writer.writerow([
            user.email,
            user.username,
            user.first_name,
            user.last_name,
            user.date_joined.strftime('%Y-%m-%d'),
            'Yes' if user.is_active else 'No',
            unsub_token,
            unsub_url
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
    list_display = ('user', 'location', 'sustainability_priority', 'email_consent', 'created_at')
    list_filter = ('sustainability_priority', 'email_consent', 'created_at')
    search_fields = ('user__username', 'user__email', 'location')
    readonly_fields = ('created_at', 'updated_at', 'unsubscribe_token')

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
        ('Email Preferences', {
            'fields': ('email_consent', 'unsubscribe_token')
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


# =============================================================================
# EMAIL CAMPAIGN ADMIN
# =============================================================================

def send_test_email(modeladmin, request, queryset):
    """Send test emails to admin users only"""
    sent_count = 0
    error_count = 0

    for campaign in queryset:
        if campaign.status != 'draft':
            messages.error(request, f'Campaign "{campaign.name}" is not in draft status')
            continue

        # Force test mode for this action
        campaign.mode = 'test'
        campaign.save()

        # Send to admin users only
        admin_users = User.objects.filter(is_staff=True, is_active=True).exclude(email='')

        for user in admin_users:
            try:
                success = send_campaign_email(campaign, user)
                if success:
                    sent_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                messages.error(request, f'Error sending to {user.email}: {str(e)}')

    if sent_count > 0:
        messages.success(request, f'Successfully sent {sent_count} test emails')
    if error_count > 0:
        messages.error(request, f'{error_count} emails failed to send')

send_test_email.short_description = "Send test emails (admin users only)"

def send_campaign_now(modeladmin, request, queryset):
    """Send campaign emails immediately"""
    for campaign in queryset:
        if campaign.status != 'draft':
            messages.error(request, f'Campaign "{campaign.name}" is not in draft status')
            continue

        if campaign.mode == 'test':
            messages.warning(request, f'Campaign "{campaign.name}" is in test mode - only admin users will receive emails')

        # Start sending process
        campaign.status = 'sending'
        campaign.save()

        try:
            sent_count = process_email_campaign(campaign)
            campaign.status = 'completed'
            campaign.sent_at = timezone.now()
            campaign.save()

            messages.success(request, f'Campaign "{campaign.name}" sent to {sent_count} recipients')
        except Exception as e:
            campaign.status = 'failed'
            campaign.save()
            messages.error(request, f'Campaign "{campaign.name}" failed: {str(e)}')

send_campaign_now.short_description = "Send campaign emails now"

def get_merge_fields():
    """Get available merge fields for email templates"""
    return [
        'first_name', 'last_name', 'username', 'email',
        'experiences_count', 'trips_count', 'surveys_count',
        'sustainability_level', 'member_since', 'last_login_date',
        'unsubscribe_url'
    ]

def process_merge_fields(text, user):
    """Process merge fields in email content"""
    if not text or not user:
        return text

    # Get user data
    try:
        profile = user.userprofile
        sustainability_levels = {
            1: 'Eco-Aware', 2: 'Eco-Friendly', 3: 'Eco-Focused',
            4: 'Eco-Champion', 5: 'Eco-Warrior'
        }
        sustainability_level = sustainability_levels.get(profile.sustainability_priority, 'Eco-Focused')
        unsubscribe_url = f"{settings.SITE_URL}{profile.get_unsubscribe_url()}"
    except:
        sustainability_level = 'Eco-Focused'
        unsubscribe_url = f"{settings.SITE_URL}/accounts/unsubscribe/"

    # Create context data
    context_data = {
        'first_name': user.first_name or user.username,
        'last_name': user.last_name or '',
        'username': user.username,
        'email': user.email,
        'experiences_count': getattr(user, 'created_trips', []).count() if hasattr(user, 'created_trips') else 0,
        'trips_count': getattr(user, 'created_trips', []).count() if hasattr(user, 'created_trips') else 0,
        'surveys_count': getattr(user, 'travel_surveys', []).count() if hasattr(user, 'travel_surveys') else 0,
        'sustainability_level': sustainability_level,
        'member_since': user.date_joined.strftime('%B %Y'),
        'last_login_date': user.last_login.strftime('%B %d, %Y') if user.last_login else 'Recently',
        'unsubscribe_url': unsubscribe_url
    }

    # Process template
    try:
        template = Template(text)
        context = Context(context_data)
        return template.render(context)
    except Exception as e:
        # If template processing fails, do simple replacement
        for key, value in context_data.items():
            text = text.replace(f'{{{{{key}}}}}', str(value))
        return text

def send_campaign_email(campaign, user):
    """Send individual campaign email to user"""
    template = campaign.template

    # Process merge fields
    subject = process_merge_fields(template.subject, user)
    html_content = process_merge_fields(template.html_content, user)
    text_content = process_merge_fields(template.text_content, user) if template.text_content else ''

    try:
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content or 'Please view this email in HTML format.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )

        if html_content:
            email.attach_alternative(html_content, "text/html")

        # Send email
        email.send()

        # Log success
        EmailLog.objects.update_or_create(
            campaign=campaign,
            recipient=user,
            defaults={
                'status': 'sent',
                'subject_sent': subject,
                'sent_at': timezone.now()
            }
        )

        return True

    except Exception as e:
        # Log failure
        EmailLog.objects.update_or_create(
            campaign=campaign,
            recipient=user,
            defaults={
                'status': 'failed',
                'subject_sent': subject,
                'error_message': str(e)
            }
        )

        return False

def process_email_campaign(campaign):
    """Process and send all emails for a campaign"""
    sent_count = 0
    failed_count = 0

    # Get recipients based on campaign settings
    if campaign.mode == 'test':
        # Test mode: send to staff users regardless of consent (for testing)
        recipients = User.objects.filter(is_staff=True, is_active=True).exclude(email='')
    else:
        # Production mode: respect email consent
        base_filter = {
            'is_active': True,
            'userprofile__email_consent': True  # Only users who consented to emails
        }

        if campaign.recipient_type == 'all_users':
            recipients = User.objects.filter(**base_filter).exclude(email='')
        elif campaign.recipient_type == 'active_users':
            cutoff = timezone.now() - timezone.timedelta(days=30)
            recipients = User.objects.filter(last_login__gte=cutoff, **base_filter).exclude(email='')
        elif campaign.recipient_type == 'survey_completed':
            recipients = User.objects.filter(travel_surveys__isnull=False, **base_filter).distinct().exclude(email='')
        elif campaign.recipient_type == 'trip_creators':
            recipients = User.objects.filter(created_trips__isnull=False, **base_filter).distinct().exclude(email='')
        elif campaign.recipient_type == 'admin_only':
            recipients = User.objects.filter(is_staff=True, is_active=True).exclude(email='')
        elif campaign.recipient_type == 'custom':
            recipients = campaign.custom_recipients.filter(**base_filter).exclude(email='')
        else:
            recipients = User.objects.none()

    # Update campaign stats
    campaign.total_recipients = recipients.count()
    campaign.save()

    # Send emails
    for user in recipients:
        if send_campaign_email(campaign, user):
            sent_count += 1
        else:
            failed_count += 1

    # Update final stats
    campaign.emails_sent = sent_count
    campaign.emails_failed = failed_count
    campaign.save()

    return sent_count

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'created_by', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'subject')
    readonly_fields = ('created_at', 'updated_at', 'available_merge_fields')

    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'category', 'is_active')
        }),
        ('Email Content', {
            'fields': ('subject', 'html_content', 'text_content'),
            'description': 'Use {{field_name}} for merge fields. Available: {{first_name}}, {{last_name}}, {{username}}, {{experiences_count}}, {{sustainability_level}}, {{member_since}}, {{unsubscribe_url}}'
        }),
        ('Metadata', {
            'fields': ('available_merge_fields', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user

        # Auto-populate available merge fields
        obj.available_merge_fields = get_merge_fields()

        super().save_model(request, obj, form, change)

@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'template', 'mode', 'recipient_type', 'status', 'get_recipient_count', 'emails_sent', 'created_at')
    list_filter = ('mode', 'recipient_type', 'status', 'created_at')
    search_fields = ('name', 'template__name')
    readonly_fields = ('total_recipients', 'emails_sent', 'emails_failed', 'sent_at', 'created_at')
    actions = [send_test_email, send_campaign_now]

    fieldsets = (
        ('Campaign Information', {
            'fields': ('name', 'template')
        }),
        ('Recipients', {
            'fields': ('recipient_type', 'custom_recipients'),
            'description': 'Select who should receive this campaign'
        }),
        ('Settings', {
            'fields': ('mode', 'scheduled_send'),
            'description': 'Test mode sends only to admin users. Production mode sends to selected recipients.'
        }),
        ('Status & Statistics', {
            'fields': ('status', 'total_recipients', 'emails_sent', 'emails_failed', 'sent_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    filter_horizontal = ('custom_recipients',)

    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_recipient_count(self, obj):
        count = obj.get_recipient_count()
        if obj.mode == 'test':
            return f"{count} (test mode)"
        return count
    get_recipient_count.short_description = 'Recipients'

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'recipient', 'status', 'subject_sent', 'sent_at')
    list_filter = ('status', 'sent_at', 'campaign')
    search_fields = ('recipient__email', 'recipient__username', 'campaign__name', 'subject_sent')
    readonly_fields = ('campaign', 'recipient', 'status', 'subject_sent', 'error_message', 'sent_at', 'created_at')

    def has_add_permission(self, request):
        return False  # Don't allow manual creation

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete logs