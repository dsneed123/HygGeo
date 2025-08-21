# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, TravelSurvey

class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class UserAdmin(BaseUserAdmin):
    """Extended User admin with profile inline"""
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')

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