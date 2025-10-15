from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import logout
from django.http import HttpResponse

from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
import csv

from .forms import (
    CustomUserCreationForm, 
    UserProfileForm, 
    TravelSurveyForm, 
    UserUpdateForm, 
    TripForm, 
    MessageForm, 
    ReplyForm
)
from .models import UserProfile, TravelSurvey, Trip, Message, EmailTemplate, EmailCampaign
from experiences.models import Experience, Destination, Provider, Category, ExperienceType, Accommodation
from .email_utils import get_merge_fields
import random

def index(request):
    """Homepage with hygge concept, sustainability facts, and survey CTA"""
    from django.core.cache import cache

    # Sustainability facts to display randomly
    sustainability_facts = [
        {
            'fact': 'Tourism accounts for 8% of global carbon emissions',
            'action': 'Choose eco-friendly transportation and accommodations'
        },
        {
            'fact': 'A single flight from NYC to London produces 1.2 tons of CO2 per passenger',
            'action': 'Consider train travel for shorter distances or carbon offset programs'
        },
        {
            'fact': 'Hotels can reduce water usage by 20-30% with simple conservation measures',
            'action': 'Stay at certified eco-hotels and reuse towels and linens'
        },
        {
            'fact': '70% of travel waste comes from single-use plastics',
            'action': 'Pack reusable water bottles, bags, and containers'
        },
        {
            'fact': 'Local spending has 3x more economic impact than chain businesses',
            'action': 'Support local restaurants, guides, and family-owned accommodations'
        },
        {
            'fact': 'Over-tourism threatens 96 UNESCO World Heritage sites',
            'action': 'Travel during off-peak seasons and explore lesser-known destinations'
        }
    ]

    # Select 3 random facts for display
    featured_facts = random.sample(sustainability_facts, 3)

    # Try to get cached featured destinations (cache for 15 minutes)
    featured_destinations = cache.get('index_featured_destinations')
    if featured_destinations is None:
        # Optimized query: Only fetch needed fields and use efficient ordering
        featured_destinations = Destination.objects.filter(
            experiences__isnull=False
        ).distinct().only(
            'id', 'name', 'country', 'description', 'image',
            'sustainability_score', 'hygge_factor', 'created_at'
        ).prefetch_related(
            'experiences'
        ).order_by('-created_at')[:6]

        # Convert to list to cache the queryset
        featured_destinations = list(featured_destinations)

        # If no destinations with experiences, get any 6 destinations
        if not featured_destinations:
            featured_destinations = list(
                Destination.objects.only(
                    'id', 'name', 'country', 'description', 'image',
                    'sustainability_score', 'hygge_factor', 'created_at'
                ).order_by('-created_at')[:6]
            )

        # Cache for 15 minutes
        cache.set('index_featured_destinations', featured_destinations, 60 * 15)

    # Try to get cached featured experiences (cache for 10 minutes)
    # Changed cache key to invalidate old cache with fallback logic
    featured_experiences = cache.get('index_featured_experiences_v2')
    if featured_experiences is None:
        # Optimized query: ONLY show featured experiences, no fallback
        featured_experiences = Experience.objects.filter(
            is_featured=True,
            is_active=True
        ).select_related(
            'destination', 'experience_type', 'provider'
        ).only(
            'id', 'title', 'description', 'main_image', 'price_from', 'slug',
            'destination__id', 'destination__name',
            'experience_type__id', 'experience_type__name',
            'provider__id', 'provider__name'
        ).order_by('?')[:8]

        # Convert to list to cache
        featured_experiences = list(featured_experiences)

        # Cache for 10 minutes
        cache.set('index_featured_experiences_v2', featured_experiences, 60 * 10)

    # Try to get cached featured accommodations (cache for 10 minutes)
    featured_accommodations = cache.get('index_featured_accommodations')
    if featured_accommodations is None:
        # Optimized query for featured accommodations - ONLY show featured ones
        # Note: Removed .only() to ensure ImageField loads properly
        featured_accommodations = Accommodation.objects.filter(
            is_featured=True,
            is_active=True
        ).select_related(
            'destination', 'provider'
        ).order_by('?')[:8]

        # Convert to list to cache
        featured_accommodations = list(featured_accommodations)

        # Cache for 10 minutes
        cache.set('index_featured_accommodations', featured_accommodations, 60 * 10)

    # Check if user has completed a survey (only for authenticated users)
    has_survey = False
    if request.user.is_authenticated:
        # Cache per-user survey status for 5 minutes
        cache_key = f'user_has_survey_{request.user.id}'
        has_survey = cache.get(cache_key)
        if has_survey is None:
            has_survey = TravelSurvey.objects.filter(user=request.user).exists()
            cache.set(cache_key, has_survey, 60 * 5)

    context = {
        'sustainability_facts': featured_facts,
        'has_survey': has_survey,
        'featured_destinations': featured_destinations,
        'featured_experiences': featured_experiences,
        'featured_accommodations': featured_accommodations,
    }

    return render(request, 'index.html', context)

def signup_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')

            # Success message with profile picture status
            if form.cleaned_data.get('avatar'):
                messages.success(request, f'Account created for {username} with profile picture! Please take our travel survey to get personalized recommendations.')
            else:
                messages.success(request, f'Account created for {username}! Please take our travel survey to get personalized recommendations.')

            # Log the user in after registration
            user = authenticate(username=username, password=form.cleaned_data.get('password1'))
            if user:
                login(request, user)
                return redirect('survey')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/signup.html', {'form': form})

@login_required
def profile_view(request):
    """View user profile and survey history"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    surveys = TravelSurvey.objects.filter(user=request.user).order_by('-completed_at')
    
    # Paginate surveys
    paginator = Paginator(surveys, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'profile': user_profile,
        'surveys': page_obj,
        'survey_count': surveys.count(),
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile_view(request):
    """Edit user profile and basic information"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        
        # Handle password change
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        password_valid = True
        
        # If any password field is filled, validate password change
        if current_password or new_password1 or new_password2:
            if not current_password:
                messages.error(request, 'Current password is required when changing password.')
                password_valid = False
            elif not authenticate(username=request.user.username, password=current_password):
                messages.error(request, 'Current password is incorrect.')
                password_valid = False
            elif not new_password1 or not new_password2:
                messages.error(request, 'Please fill in both new password fields.')
                password_valid = False
            elif new_password1 != new_password2:
                messages.error(request, 'New passwords do not match.')
                password_valid = False
            elif len(new_password1) < 8:
                messages.error(request, 'New password must be at least 8 characters long.')
                password_valid = False
        
        if user_form.is_valid() and profile_form.is_valid() and password_valid:
            user_form.save()
            profile_form.save()
            
            # Change password if provided
            if current_password and new_password1 and password_valid:
                request.user.set_password(new_password1)
                request.user.save()
                update_session_auth_hash(request, request.user)  # Keep user logged in
                messages.success(request, 'Your profile and password have been updated successfully!')
            else:
                messages.success(request, 'Your profile has been updated successfully!')
                
            return redirect('profile')
        else:
            if not password_valid:
                messages.error(request, 'Please correct the password errors and try again.')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'accounts/edit_profile.html', context)

@login_required
def survey_view(request):
    """Travel survey form"""
    # Check if user has already completed a survey recently (within 30 days)
    existing_survey = TravelSurvey.objects.filter(user=request.user).first()
    
    if request.method == 'POST':
        form = TravelSurveyForm(request.POST, instance=existing_survey)
        if form.is_valid():
            survey = form.save(commit=False)
            survey.user = request.user
            survey.save()
            messages.success(request, 'Thank you for completing the survey! We\'ll use this information to provide you with personalized sustainable travel recommendations.')
            return redirect('survey_success')
    else:
        form = TravelSurveyForm(instance=existing_survey)
    
    context = {
        'form': form,
        'is_update': existing_survey is not None,
    }
    
    return render(request, 'survey/survey.html', context)

@login_required
def survey_success_view(request):
    """Survey completion success page"""
    latest_survey = TravelSurvey.objects.filter(user=request.user).first()
    
    context = {
        'survey': latest_survey,
    }
    
    return render(request, 'survey/survey_success.html', context)

@login_required
def delete_account_view(request):
    """Delete user account with confirmation"""
    if request.method == 'POST':
        if 'confirm_delete' in request.POST:
            user = request.user
            user.delete()
            messages.success(request, 'Your account has been successfully deleted.')
            return redirect('index')
    
    return render(request, 'accounts/delete_account.html')

# In your views.py
from django.db.models import Q, Count, F
from django.db import models
from .models import User, TravelSurvey

# Replace your existing user_list_view with this updated version:

def user_list_view(request):
    users = User.objects.select_related('userprofile').prefetch_related('travel_surveys')

    # Filter by destination (search in dream_destination)
    destination_query = request.GET.get('destination', '')
    if destination_query:
        users = users.filter(
            travel_surveys__dream_destination__icontains=destination_query
        )

    # Filter by travel style
    travel_style = request.GET.get('travel_style', '')
    if travel_style:
        users = users.filter(
            travel_surveys__travel_styles__contains=[travel_style]
        )

    # Filter by age range
    age_range = request.GET.get('age_range', '')
    gender_pref = request.GET.get('gender_pref', '')
    travel_month = request.GET.get('travel_month', '')

    # Sort by newest members (default and only option)
    users = users.order_by('-date_joined')
    
    # Get recent trips from all users (including current user)
    recent_trips = Trip.objects.filter(
        visibility__in=['public', 'community']
    ).select_related(
        'creator__userprofile'
    ).order_by('-created_at')[:12]  # Get 12 most recent trips
    
    # Pagination for users
    paginator = Paginator(users, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'users': page_obj,
        'recent_trips': recent_trips,
        'destination_query': destination_query,
        'travel_style': travel_style,
        'age_range': age_range,
        'gender_pref': gender_pref,
        'travel_month': travel_month,
    }
    return render(request, 'accounts/user_list.html', context)


def public_profile_view(request, username):
    profile_user = User.objects.get(username=username)
    
    today = timezone.now().date()
    
    public_trips = Trip.objects.filter(
        creator=profile_user,
        visibility='public',
        start_date__gte=today
    ).order_by('start_date')
    
    past_trips = Trip.objects.filter(
        creator=profile_user,
        start_date__lt=today
    ).order_by('-start_date')
    
    context = {
        'profile_user': profile_user,
        'public_trips': public_trips,
        'past_trips': past_trips,
    }
    
    return render(request, 'accounts/public_profile.html', context)


# In your accounts/views.py - Replace your existing admin_dashboard function with this:

@user_passes_test(lambda u: u.is_staff, login_url='/accounts/login/')
def admin_dashboard(request):
    """
    Admin dashboard view - only accessible to staff users
    """
    # Gather statistics
    stats = {
        'experiences_count': Experience.objects.count(),
        'destinations_count': Destination.objects.count(),
        'providers_count': Provider.objects.count(),
        'users_count': User.objects.count(),
        'categories_count': Category.objects.count(),
        'experience_types_count': ExperienceType.objects.count(),
        'accommodations_count': Accommodation.objects.count(),
    }

    # Email statistics
    email_stats = {
        'total_users': User.objects.count(),
        'users_with_email': User.objects.exclude(email='').count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'active_users_with_email': User.objects.filter(is_active=True).exclude(email='').count(),
    }
    email_stats['users_without_email'] = email_stats['total_users'] - email_stats['users_with_email']

    # Get recent activity (last 6 experiences)
    recent_experiences = Experience.objects.select_related('destination').order_by('-created_at')[:6]

    # Get recent destinations
    recent_destinations = Destination.objects.order_by('-created_at')[:5]

    # Get active/featured counts
    featured_experiences = Experience.objects.filter(is_featured=True).count()
    active_experiences = Experience.objects.filter(is_active=True).count()
    featured_accommodations = Accommodation.objects.filter(is_featured=True).count()

    # Update stats dict with featured counts
    stats['featured_experiences_count'] = featured_experiences
    stats['featured_accommodations_count'] = featured_accommodations

    # Get all experiences and accommodations for featured management
    # Fetch all to allow proper filtering in the UI
    all_experiences = Experience.objects.select_related('destination').order_by('-created_at')
    all_accommodations = Accommodation.objects.select_related('destination').order_by('-created_at')

    # Get all destinations for blog generator
    all_destinations = Destination.objects.all().order_by('name')

    context = {
        'stats': stats,
        'email_stats': email_stats,
        'recent_experiences': recent_experiences,
        'recent_destinations': recent_destinations,
        'featured_count': featured_experiences,
        'active_count': active_experiences,
        'all_experiences': all_experiences,
        'all_accommodations': all_accommodations,
        'all_destinations': all_destinations,
    }

    # Updated template path to match your file location
    return render(request, 'admin-dashboard.html', context)

@user_passes_test(lambda u: u.is_staff, login_url='/accounts/login/')
def export_all_emails_csv(request):
    """Export all user emails as CSV file with mail merge fields"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="user_emails_mail_merge.csv"'

    writer = csv.writer(response)
    # Mail merge friendly headers
    writer.writerow([
        'Email', 'FirstName', 'LastName', 'FullName', 'Username',
        'DateJoined', 'IsActive', 'Location', 'TravelInterests', 'SustainabilityPriority'
    ])

    # Get all users with related profile data
    users = User.objects.select_related('userprofile').prefetch_related('travel_surveys').all()

    for user in users:
        # Get user profile if it exists
        profile = getattr(user, 'userprofile', None)

        # Get latest travel survey if it exists
        latest_survey = user.travel_surveys.first() if user.travel_surveys.exists() else None

        # Prepare names for mail merge
        first_name = user.first_name or user.username.split('@')[0] if '@' in user.username else user.username
        last_name = user.last_name or ''
        full_name = f"{first_name} {last_name}".strip() or user.username

        # Get travel interests from survey
        travel_interests = ''
        if latest_survey and latest_survey.travel_styles:
            travel_interests = ', '.join(latest_survey.travel_styles)

        # Get sustainability priority
        sustainability_priority = ''
        if profile and profile.sustainability_priority:
            priorities = {1: 'Low', 2: 'Medium', 3: 'High', 4: 'Very High', 5: 'Essential'}
            sustainability_priority = priorities.get(profile.sustainability_priority, 'Medium')

        writer.writerow([
            user.email,
            first_name,
            last_name,
            full_name,
            user.username,
            user.date_joined.strftime('%Y-%m-%d'),
            'Yes' if user.is_active else 'No',
            profile.location if profile else '',
            travel_interests,
            sustainability_priority
        ])

    return response

@user_passes_test(lambda u: u.is_staff, login_url='/accounts/login/')
def export_all_emails_text(request):
    """Export all user emails as plain text file"""
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="all_user_emails.txt"'

    emails = [user.email for user in User.objects.all() if user.email]
    response.write(', '.join(emails))

    return response

@user_passes_test(lambda u: u.is_staff, login_url='/accounts/login/')
def export_active_emails_csv(request):
    """Export active user emails as CSV file with mail merge fields"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="active_users_mail_merge.csv"'

    writer = csv.writer(response)
    # Mail merge friendly headers
    writer.writerow([
        'Email', 'FirstName', 'LastName', 'FullName', 'Username',
        'DateJoined', 'Location', 'TravelInterests', 'SustainabilityPriority', 'BudgetRange'
    ])

    # Get active users with related profile data
    users = User.objects.filter(is_active=True).select_related('userprofile').prefetch_related('travel_surveys')

    for user in users:
        # Get user profile if it exists
        profile = getattr(user, 'userprofile', None)

        # Get latest travel survey if it exists
        latest_survey = user.travel_surveys.first() if user.travel_surveys.exists() else None

        # Prepare names for mail merge
        first_name = user.first_name or user.username.split('@')[0] if '@' in user.username else user.username
        last_name = user.last_name or ''
        full_name = f"{first_name} {last_name}".strip() or user.username

        # Get travel interests from survey
        travel_interests = ''
        if latest_survey and latest_survey.travel_styles:
            travel_interests = ', '.join(latest_survey.travel_styles)

        # Get sustainability priority
        sustainability_priority = ''
        if profile and profile.sustainability_priority:
            priorities = {1: 'Low', 2: 'Medium', 3: 'High', 4: 'Very High', 5: 'Essential'}
            sustainability_priority = priorities.get(profile.sustainability_priority, 'Medium')

        # Get budget range
        budget_range = ''
        if latest_survey and latest_survey.budget_range:
            budget_ranges = {
                'budget': 'Budget ($0-50/day)',
                'mid_range': 'Mid-range ($50-150/day)',
                'luxury': 'Luxury ($150+/day)',
                'varies': 'Varies by trip'
            }
            budget_range = budget_ranges.get(latest_survey.budget_range, latest_survey.budget_range)

        writer.writerow([
            user.email,
            first_name,
            last_name,
            full_name,
            user.username,
            user.date_joined.strftime('%Y-%m-%d'),
            profile.location if profile else '',
            travel_interests,
            sustainability_priority,
            budget_range
        ])

    return response

@user_passes_test(lambda u: u.is_staff, login_url='/accounts/login/')
def export_active_emails_text(request):
    """Export active user emails as plain text file"""
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="active_user_emails.txt"'

    emails = [user.email for user in User.objects.filter(is_active=True) if user.email]
    response.write(', '.join(emails))

    return response

@user_passes_test(lambda u: u.is_staff, login_url='/accounts/login/')
def export_mail_merge_premium(request):
    """Export users with comprehensive mail merge data including recommendations"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="mail_merge_premium_data.csv"'

    writer = csv.writer(response)
    # Comprehensive mail merge headers
    writer.writerow([
        'Email', 'FirstName', 'LastName', 'FullName', 'Username',
        'DateJoined', 'Location', 'TravelInterests', 'SustainabilityPriority', 'BudgetRange',
        'GroupSizePreference', 'TripDurationPreference', 'DreamDestination', 'HasCompletedSurvey',
        'TopRecommendation', 'RecommendationCount', 'PersonalizedGreeting'
    ])

    # Get active users with all related data
    users = User.objects.filter(is_active=True).select_related('userprofile').prefetch_related(
        'travel_surveys', 'recommendations__experience__destination'
    )

    for user in users:
        # Get user profile if it exists
        profile = getattr(user, 'userprofile', None)

        # Get latest travel survey if it exists
        latest_survey = user.travel_surveys.first() if user.travel_surveys.exists() else None

        # Prepare names for mail merge
        first_name = user.first_name or user.username.split('@')[0] if '@' in user.username else user.username
        last_name = user.last_name or ''
        full_name = f"{first_name} {last_name}".strip() or user.username

        # Get travel interests from survey
        travel_interests = ''
        if latest_survey and latest_survey.travel_styles:
            travel_interests = ', '.join(latest_survey.travel_styles)

        # Get sustainability priority
        sustainability_priority = ''
        if profile and profile.sustainability_priority:
            priorities = {1: 'Low', 2: 'Medium', 3: 'High', 4: 'Very High', 5: 'Essential'}
            sustainability_priority = priorities.get(profile.sustainability_priority, 'Medium')

        # Get budget range
        budget_range = ''
        if latest_survey and latest_survey.budget_range:
            budget_ranges = {
                'budget': 'Budget ($0-50/day)',
                'mid_range': 'Mid-range ($50-150/day)',
                'luxury': 'Luxury ($150+/day)',
                'varies': 'Varies by trip'
            }
            budget_range = budget_ranges.get(latest_survey.budget_range, latest_survey.budget_range)

        # Get group size and duration preferences
        group_size_pref = ''
        trip_duration_pref = ''
        dream_destination = ''
        if latest_survey:
            group_size_pref = latest_survey.get_group_size_preference_display() if hasattr(latest_survey, 'get_group_size_preference_display') else latest_survey.group_size_preference
            trip_duration_pref = latest_survey.get_trip_duration_preference_display() if hasattr(latest_survey, 'get_trip_duration_preference_display') else latest_survey.trip_duration_preference
            dream_destination = latest_survey.dream_destination

        # Get recommendation data
        recommendations = user.recommendations.all()
        recommendation_count = recommendations.count()
        top_recommendation = ''
        if recommendations.exists():
            top_rec = recommendations.first()
            top_recommendation = f"{top_rec.experience.title} in {top_rec.experience.destination.name}"

        # Create personalized greeting
        personalized_greeting = f"Hi {first_name}!"
        if travel_interests:
            personalized_greeting += f" We know you love {travel_interests.lower()}."
        if dream_destination:
            personalized_greeting += f" Your dream destination of {dream_destination} awaits!"

        writer.writerow([
            user.email,
            first_name,
            last_name,
            full_name,
            user.username,
            user.date_joined.strftime('%Y-%m-%d'),
            profile.location if profile else '',
            travel_interests,
            sustainability_priority,
            budget_range,
            group_size_pref,
            trip_duration_pref,
            dream_destination,
            'Yes' if latest_survey else 'No',
            top_recommendation,
            recommendation_count,
            personalized_greeting
        ])

    return response

@user_passes_test(lambda u: u.is_staff, login_url='/accounts/login/')
def analytics_dashboard(request):
    """
    Analytics Dashboard - Real Data Only
    """
    from django.db.models import Count, Avg, Q, F, Sum
    from django.utils import timezone
    from datetime import datetime, timedelta
    from experiences.models import UserRecommendation, BookingTracking, ExperienceReview
    import json

    now = timezone.now()

    # Get time period from request (default to 30 days)
    period = request.GET.get('period', '30d')

    # Define all time periods
    time_periods = {
        '7d': timedelta(days=7),
        '30d': timedelta(days=30),
        '90d': timedelta(days=90),
        '6m': timedelta(days=180),
        '1y': timedelta(days=365),
        'all': None  # All time
    }

    selected_period = time_periods.get(period, time_periods['30d'])

    # Date ranges for different time periods
    last_30_days = now - timedelta(days=30)
    last_7_days = now - timedelta(days=7)
    last_24_hours = now - timedelta(hours=24)
    last_90_days = now - timedelta(days=90)
    last_6_months = now - timedelta(days=180)
    last_year = now - timedelta(days=365)

    # Dynamic date range based on selected period
    if selected_period:
        start_date = now - selected_period
    else:
        start_date = None  # All time

    # User Analytics
    total_users = User.objects.count()

    # Users for selected period
    if start_date:
        new_users_period = User.objects.filter(date_joined__gte=start_date).count()
        active_users_period = User.objects.filter(last_login__gte=start_date).count()
    else:
        new_users_period = total_users
        active_users_period = User.objects.filter(last_login__isnull=False).count()

    # Fixed time periods for comparison
    new_users_30_days = User.objects.filter(date_joined__gte=last_30_days).count()
    new_users_7_days = User.objects.filter(date_joined__gte=last_7_days).count()
    new_users_90_days = User.objects.filter(date_joined__gte=last_90_days).count()
    new_users_6_months = User.objects.filter(date_joined__gte=last_6_months).count()
    new_users_year = User.objects.filter(date_joined__gte=last_year).count()

    # Booking Analytics
    total_bookings = BookingTracking.objects.count()
    bookings_7_days = BookingTracking.objects.filter(clicked_at__gte=last_7_days).count()
    bookings_30_days = BookingTracking.objects.filter(clicked_at__gte=last_30_days).count()
    bookings_90_days = BookingTracking.objects.filter(clicked_at__gte=last_90_days).count()
    bookings_6_months = BookingTracking.objects.filter(clicked_at__gte=last_6_months).count()
    bookings_year = BookingTracking.objects.filter(clicked_at__gte=last_year).count()

    # Bookings for selected period
    if start_date:
        bookings_period = BookingTracking.objects.filter(clicked_at__gte=start_date).count()
    else:
        bookings_period = total_bookings

    # Active users based on login activity
    active_users_7_days = User.objects.filter(last_login__gte=last_7_days).count()
    active_users_24_hours = User.objects.filter(last_login__gte=last_24_hours).count()
    active_users_30_days = User.objects.filter(last_login__gte=last_30_days).count()
    active_users_90_days = User.objects.filter(last_login__gte=last_90_days).count()

    # Dynamic chart data based on selected period
    if period == '7d':
        chart_days = 7
        date_format = '%m/%d'
    elif period == '90d':
        chart_days = 90
        date_format = '%m/%d'
    elif period == '6m':
        chart_days = 180
        date_format = '%m/%d'
    elif period == '1y':
        chart_days = 365
        date_format = '%m/%y'
    elif period == 'all':
        # Get the earliest user registration date
        earliest_user = User.objects.order_by('date_joined').first()
        if earliest_user:
            chart_days = (now - earliest_user.date_joined).days
        else:
            chart_days = 30
        date_format = '%m/%y'
    else:  # 30d default
        chart_days = 30
        date_format = '%m/%d'

    # User registrations data for selected period
    user_registration_data = []
    step = max(1, chart_days // 50)  # Limit to 50 data points max

    for i in range(0, chart_days, step):
        date = now - timedelta(days=chart_days-1-i)
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=step)
        count = User.objects.filter(
            date_joined__gte=start_of_day,
            date_joined__lt=end_of_day
        ).count()
        user_registration_data.append({
            'date': start_of_day.strftime(date_format),
            'count': count
        })

    # Active users by hour (last 24 hours)
    hourly_activity_data = []
    for i in range(24):
        hour_start = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=23-i)
        hour_end = hour_start + timedelta(hours=1)
        count = User.objects.filter(
            last_login__gte=hour_start,
            last_login__lt=hour_end
        ).count()
        hourly_activity_data.append({
            'hour': hour_start.strftime('%H:00'),
            'count': count
        })

    # Content Analytics
    total_experiences = Experience.objects.count()
    active_experiences = Experience.objects.filter(is_active=True).count()
    featured_experiences = Experience.objects.filter(is_featured=True).count()

    # Recommendations and user engagement
    total_recommendations = UserRecommendation.objects.count()
    viewed_recommendations = UserRecommendation.objects.filter(viewed=True).count()
    clicked_recommendations = UserRecommendation.objects.filter(clicked=True).count()
    bookmarked_experiences = UserRecommendation.objects.filter(bookmarked=True).count()

    # Top performing experiences (by bookings)
    top_experiences = Experience.objects.annotate(
        booking_count=Count('bookingtracking')
    ).filter(booking_count__gt=0).order_by('-booking_count')[:10]

    # Top destinations by experience count
    top_destinations = Destination.objects.annotate(
        experience_count=Count('experiences')
    ).filter(experience_count__gt=0).order_by('-experience_count')[:10]

    # Category popularity
    category_stats = Category.objects.annotate(
        experience_count=Count('experiences'),
        booking_count=Count('experiences__bookingtracking')
    ).order_by('-booking_count')[:8]

    # User travel preferences analysis
    travel_surveys = TravelSurvey.objects.count()
    survey_completion_rate = (travel_surveys / total_users * 100) if total_users > 0 else 0

    # Sustainability scores analysis
    avg_sustainability_score = Experience.objects.aggregate(
        avg_score=Avg('sustainability_score')
    )['avg_score'] or 0

    avg_hygge_factor = Experience.objects.aggregate(
        avg_score=Avg('hygge_factor')
    )['avg_score'] or 0

    # Engagement rates
    recommendation_view_rate = (viewed_recommendations / total_recommendations * 100) if total_recommendations > 0 else 0
    recommendation_click_rate = (clicked_recommendations / viewed_recommendations * 100) if viewed_recommendations > 0 else 0
    booking_conversion_rate = (bookings_30_days / total_users * 100) if total_users > 0 else 0

    # Recent activity metrics
    experiences_created_7_days = Experience.objects.filter(created_at__gte=last_7_days).count()
    destinations_created_7_days = Destination.objects.filter(created_at__gte=last_7_days).count()

    # Booking trends (last 7 days)
    booking_trend_data = []
    for i in range(7):
        date = now - timedelta(days=6-i)
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        count = BookingTracking.objects.filter(
            clicked_at__gte=start_of_day,
            clicked_at__lt=end_of_day
        ).count()
        booking_trend_data.append({
            'date': start_of_day.strftime('%m/%d'),
            'count': count
        })

    context = {
        'current_period': period,
        'available_periods': [
            ('7d', '7 Days'),
            ('30d', '30 Days'),
            ('90d', '3 Months'),
            ('6m', '6 Months'),
            ('1y', '1 Year'),
            ('all', 'All Time')
        ],
        'analytics': {
            # User metrics
            'total_users': total_users,
            'new_users_period': new_users_period,
            'active_users_period': active_users_period,
            'new_users_7_days': new_users_7_days,
            'new_users_30_days': new_users_30_days,
            'new_users_90_days': new_users_90_days,
            'new_users_6_months': new_users_6_months,
            'new_users_year': new_users_year,
            'active_users_7_days': active_users_7_days,
            'active_users_24_hours': active_users_24_hours,
            'active_users_30_days': active_users_30_days,
            'active_users_90_days': active_users_90_days,
            'user_growth_rate': (new_users_period / total_users * 100) if total_users > 0 else 0,

            # Content metrics
            'total_experiences': total_experiences,
            'active_experiences': active_experiences,
            'featured_experiences': featured_experiences,
            'experiences_created_7_days': experiences_created_7_days,
            'destinations_created_7_days': destinations_created_7_days,

            # Booking metrics
            'total_bookings': total_bookings,
            'bookings_period': bookings_period,
            'bookings_7_days': bookings_7_days,
            'bookings_30_days': bookings_30_days,
            'bookings_90_days': bookings_90_days,
            'bookings_6_months': bookings_6_months,
            'bookings_year': bookings_year,

            # Recommendation metrics
            'total_recommendations': total_recommendations,
            'viewed_recommendations': viewed_recommendations,
            'clicked_recommendations': clicked_recommendations,
            'bookmarked_experiences': bookmarked_experiences,
            'travel_surveys': travel_surveys,

            # Rates and conversions
            'survey_completion_rate': round(survey_completion_rate, 1),
            'recommendation_view_rate': round(recommendation_view_rate, 1),
            'recommendation_click_rate': round(recommendation_click_rate, 1),
            'booking_conversion_rate': round(booking_conversion_rate, 1),
            'avg_sustainability_score': round(avg_sustainability_score, 1),
            'avg_hygge_factor': round(avg_hygge_factor, 1),
        },
        'top_experiences': top_experiences,
        'top_destinations': top_destinations,
        'category_stats': category_stats,
        'chart_data': {
            'user_registrations': json.dumps(user_registration_data),
            'hourly_activity': json.dumps(hourly_activity_data),
            'booking_trends': json.dumps(booking_trend_data),
        }
    }

    return render(request, 'analytics.html', context)


@login_required
def create_trip(request):
    """Create a new trip"""
    if request.method == 'POST':
        form = TripForm(request.POST, request.FILES)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.creator = request.user
            trip.save()
            # Save many-to-many relationships
            form.save_m2m()
            messages.success(request, 'Your trip has been created successfully!')
            return redirect('trip_detail', pk=trip.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TripForm()
    
    return render(request, 'accounts/create_trip.html', {
        'form': form,
        'destinations': Destination.objects.all(),
        'experiences': Experience.objects.filter(is_active=True)
    })

@login_required
def trip_detail_view(request, pk):
    """View trip details"""
    trip = get_object_or_404(Trip, pk=pk)
    
    # Check visibility permissions
    if trip.visibility == 'private' and trip.creator != request.user:
        messages.error(request, 'This trip is private.')
        return redirect('trip_list')
    
    context = {
        'trip': trip,
        'can_edit': trip.creator == request.user,
        'can_message': trip.allow_messages and trip.creator != request.user,
    }
    
    return render(request, 'accounts/trip_detail.html', context)

def trip_list_view(request):
    """List all public trips with filtering"""
    trips = Trip.objects.filter(visibility__in=['public', 'community']).select_related('creator__userprofile')
    
    # Filter by destination
    destination_query = request.GET.get('destination')
    if destination_query:
        trips = trips.filter(destination__icontains=destination_query)
    
    # Filter by budget range
    budget_filter = request.GET.get('budget_range')
    if budget_filter:
        trips = trips.filter(budget_range=budget_filter)
    
    # Filter by travel style
    travel_style = request.GET.get('travel_style')
    if travel_style:
        trips = trips.filter(travel_styles__contains=[travel_style])
    
    # Filter by seeking buddies
    seeking_buddies = request.GET.get('seeking_buddies')
    if seeking_buddies:
        trips = trips.filter(seeking_buddies=seeking_buddies)
    
    # Pagination
    paginator = Paginator(trips, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'trips': page_obj,
        'destination_query': destination_query,
        'budget_filter': budget_filter,
        'travel_style': travel_style,
        'seeking_buddies': seeking_buddies,
    }
    
    return render(request, 'accounts/trip_list.html', context)

@login_required
def my_trips_view(request):
    """View user's own trips"""
    trips = Trip.objects.filter(creator=request.user).order_by('-created_at')
    
    paginator = Paginator(trips, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'accounts/my_trips.html', {'trips': page_obj})

@login_required
def edit_trip_view(request, pk):
    """Edit an existing trip"""
    trip = get_object_or_404(Trip, pk=pk, creator=request.user)
    
    if request.method == 'POST':
        form = TripForm(request.POST, request.FILES, instance=trip)
        if form.is_valid():
            # Handle image removal if requested
            if 'remove_image' in request.POST and request.POST.get('remove_image') == 'on':
                if trip.trip_image:
                    trip.trip_image.delete()
                    trip.trip_image = None
            
            trip = form.save()
            messages.success(request, 'Your trip has been updated successfully!')
            return redirect('trip_detail', pk=trip.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TripForm(instance=trip)
    
    context = {
        'form': form,
        'trip': trip,
        'experiences': Experience.objects.filter(is_active=True),
    }

    return render(request, 'accounts/edit_trip.html', context)

@login_required
def delete_trip_view(request, pk):
    """Delete a trip"""
    trip = get_object_or_404(Trip, pk=pk, creator=request.user)
    
    if request.method == 'POST':
        trip_name = trip.trip_name
        trip.delete()
        messages.success(request, f'Trip "{trip_name}" has been deleted successfully!')
        return redirect('my_trips')
    
    return redirect('trip_detail', pk=pk)


# Add these to your accounts/views.py

@login_required
def send_message_view(request, username=None, trip_id=None):
    """Send a message to another user, optionally about a specific trip"""
    recipient = None
    trip = None
    
    if username:
        recipient = get_object_or_404(User, username=username)
    if trip_id:
        trip = get_object_or_404(Trip, pk=trip_id)
        if not recipient:
            recipient = trip.creator
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = recipient
            message.trip = trip
            message.save()
            
            messages.success(request, f'Message sent to {recipient.first_name or recipient.username}!')
            return redirect('message_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        initial_data = {}
        if trip:
            initial_data['subject'] = f'Interest in your trip: {trip.trip_name}'
        form = MessageForm(initial=initial_data)
    
    context = {
        'form': form,
        'recipient': recipient,
        'trip': trip,
    }
    
    return render(request, 'accounts/send_message.html', context)

@login_required
def message_list_view(request):
    """List all conversations for the current user"""
    # Get all messages where user is sender or recipient
    user_messages = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).select_related('sender', 'recipient', 'trip')
    
    # Group messages by conversation
    conversations = {}
    for message in user_messages:
        conv_id = message.conversation_id
        if conv_id not in conversations:
            conversations[conv_id] = {
                'latest_message': message,
                'participants': set(),
                'unread_count': 0,
                'trip': message.trip,
            }
        
        # Update latest message if this one is newer
        if message.created_at > conversations[conv_id]['latest_message'].created_at:
            conversations[conv_id]['latest_message'] = message
        
        # Add participants
        conversations[conv_id]['participants'].add(message.sender)
        conversations[conv_id]['participants'].add(message.recipient)
        
        # Count unread messages for current user
        if message.recipient == request.user and not message.is_read:
            conversations[conv_id]['unread_count'] += 1
    
    # Convert to list and sort by latest message
    conversation_list = list(conversations.values())
    conversation_list.sort(key=lambda x: x['latest_message'].created_at, reverse=True)
    
    # Pagination
    paginator = Paginator(conversation_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'conversations': page_obj,
        'total_unread': sum(conv['unread_count'] for conv in conversation_list),
    }
    
    return render(request, 'accounts/message_list.html', context)

@login_required
def conversation_view(request, conversation_id):
    """View a specific conversation thread"""
    # Get the root message
    root_message = get_object_or_404(Message, pk=conversation_id)
    
    # Check if user is part of this conversation
    if request.user not in [root_message.sender, root_message.recipient]:
        messages.error(request, 'You do not have access to this conversation.')
        return redirect('message_list')
    
    # Get all messages in this conversation
    conversation_messages = Message.objects.filter(
    Q(id=conversation_id) | Q(parent_message_id=conversation_id)
        ).select_related('sender', 'recipient', 'trip').order_by('created_at')

        # Mark messages as read for current user
    Message.objects.filter(
        Q(id=conversation_id) | Q(parent_message_id=conversation_id),
        recipient=request.user,
        is_read=False
    ).update(is_read=True)
    
    # Get the other participant
    other_user = root_message.recipient if root_message.sender == request.user else root_message.sender
    
    # Handle reply form
    if request.method == 'POST':
        form = ReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.sender = request.user
            reply.recipient = other_user
            reply.subject = f"Re: {root_message.subject}"
            reply.trip = root_message.trip
            reply.parent_message = root_message
            reply.save()
            
            messages.success(request, 'Reply sent!')
            return redirect('conversation', conversation_id=conversation_id)
    else:
        form = ReplyForm()
    
    context = {
        'conversation_messages': conversation_messages,
        'other_user': other_user,
        'trip': root_message.trip,
        'form': form,
        'conversation_id': conversation_id,
    }
    
    return render(request, 'accounts/conversation.html', context)

@login_required
def delete_message_view(request, message_id):
    """Delete a message"""
    message = get_object_or_404(Message, pk=message_id, sender=request.user)
    
    if request.method == 'POST':
        conversation_id = message.conversation_id
        message.delete()
        messages.success(request, 'Message deleted successfully!')
        return redirect('conversation', conversation_id=conversation_id)
    
    return redirect('message_list')

@login_required
def logout_view(request):
    """Log the user out and redirect to homepage"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('index')

def user_trips_view(request, username):
    """Display all public trips for a specific user"""
    user = get_object_or_404(User, username=username)
    
    # Base queryset for the user's trips
    trips = Trip.objects.filter(creator=user)
    
    # Filter by visibility based on the viewer
    if request.user == user:
        # User viewing their own trips - show all trips
        pass
    elif request.user.is_authenticated:
        # Logged-in user viewing someone else's trips - show public and community trips
        trips = trips.filter(visibility__in=['public', 'community'])
    else:
        # Anonymous user - only show public trips
        trips = trips.filter(visibility='public')
    
    # Filter by trip status (optional - you might want to show all or filter out completed trips)
    status_filter = request.GET.get('status')
    if status_filter:
        trips = trips.filter(trip_status=status_filter)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        trips = trips.filter(
            Q(trip_name__icontains=search_query) |
            Q(destination__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Ordering
    order_by = request.GET.get('order_by', '-created_at')
    if order_by in ['created_at', '-created_at', 'start_date', '-start_date', 'trip_name', '-trip_name']:
        trips = trips.order_by(order_by)
    
    # Pagination
    paginator = Paginator(trips, 12)  # Show 12 trips per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get trip status choices for filtering
    status_choices = Trip.TRIP_STATUS_CHOICES
    
    context = {
        'profile_user': user,
        'trips': page_obj,
        'total_trips': trips.count(),
        'status_choices': status_choices,
        'current_status': status_filter,
        'search_query': search_query,
        'current_order': order_by,
    }
    
    return render(request, 'accounts/user_trips.html', context)

def debug_spaces(request):
    from django.conf import settings
    from django.http import JsonResponse
    import os
    import boto3
    
    debug_info = {
        'DEBUG': settings.DEBUG,
        'INSTALLED_APPS_has_storages': 'storages' in settings.INSTALLED_APPS,
        'AWS_ACCESS_KEY_ID': getattr(settings, 'AWS_ACCESS_KEY_ID', 'NOT_SET')[:8] + '...' if getattr(settings, 'AWS_ACCESS_KEY_ID', None) else 'NOT_SET',
        'AWS_STORAGE_BUCKET_NAME': getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'NOT_SET'),
        'AWS_S3_ENDPOINT_URL': getattr(settings, 'AWS_S3_ENDPOINT_URL', 'NOT_SET'),
        'DEFAULT_FILE_STORAGE': getattr(settings, 'DEFAULT_FILE_STORAGE', 'NOT_SET'),
        'MEDIA_URL': settings.MEDIA_URL,
        'env_SPACES_ACCESS_KEY': 'EXISTS' if os.environ.get('SPACES_ACCESS_KEY') else 'MISSING',
        'env_SPACES_BUCKET_NAME': os.environ.get('SPACES_BUCKET_NAME', 'MISSING'),
    }
    
    # Test connection to Spaces
    try:
        client = boto3.client(
            's3',
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        # Try to list bucket contents
        response = client.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        debug_info['connection_test'] = 'SUCCESS'
        debug_info['objects_in_bucket'] = response.get('KeyCount', 0)
        
    except Exception as e:
        debug_info['connection_test'] = f'FAILED: {str(e)}'
    
    return JsonResponse(debug_info)

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def test_upload(request):
    from django.http import JsonResponse
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage
    
    try:
        # Create a test file
        test_content = ContentFile(b"This is a test file from Django")
        test_filename = "test-upload.txt"
        
        # Try to save it using the default storage
        saved_name = default_storage.save(f"test/{test_filename}", test_content)
        
        # Get the URL
        file_url = default_storage.url(saved_name)
        
        return JsonResponse({
            'status': 'success',
            'saved_name': saved_name,
            'file_url': file_url,
            'storage_class': str(type(default_storage)),
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'error_type': str(type(e)),
            'storage_class': str(type(default_storage)),
        })
    
def debug_storage(request):
    from django.conf import settings
    from django.core.files.storage import default_storage
    from django.http import JsonResponse
    import os
    
    return JsonResponse({
        'DEBUG': settings.DEBUG,
        'DEFAULT_FILE_STORAGE_in_settings': getattr(settings, 'DEFAULT_FILE_STORAGE', 'NOT_SET'),
        'actual_storage_class': str(type(default_storage)),
        'all_installed_apps': settings.INSTALLED_APPS,
        'storages_in_installed_apps': 'storages' in settings.INSTALLED_APPS,
        'AWS_settings_exist': {
            'AWS_ACCESS_KEY_ID': bool(getattr(settings, 'AWS_ACCESS_KEY_ID', None)),
            'AWS_SECRET_ACCESS_KEY': bool(getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)),
            'AWS_STORAGE_BUCKET_NAME': bool(getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)),
        },
        'if_not_debug_condition': not settings.DEBUG,  # This should be True in production
    })

def privacy_policy_view(request):
    """Display the privacy policy"""
    from django.utils import timezone
    return render(request, 'accounts/privacy_policy.html', {
        'current_date': timezone.now()
    })

# Email Management Views
from .models import EmailTemplate, EmailCampaign, EmailLog
from django.template import Template, Context
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import re

@user_passes_test(lambda u: u.is_staff)
def email_management(request):
    """Email management dashboard"""
    templates = EmailTemplate.objects.filter(is_active=True)
    recent_campaigns = EmailCampaign.objects.all()[:5]

    # Email stats
    total_templates = EmailTemplate.objects.count()
    active_campaigns = EmailCampaign.objects.filter(status__in=['draft', 'scheduled', 'sending']).count()
    completed_campaigns = EmailCampaign.objects.filter(status='completed').count()

    context = {
        'templates': templates,
        'recent_campaigns': recent_campaigns,
        'stats': {
            'total_templates': total_templates,
            'active_campaigns': active_campaigns,
            'completed_campaigns': completed_campaigns,
        }
    }
    return render(request, 'accounts/email_management.html', context)

@user_passes_test(lambda u: u.is_staff)
def create_email_template(request):
    """Create a new email template"""
    if request.method == 'POST':
        name = request.POST.get('name')
        subject = request.POST.get('subject')
        html_content = request.POST.get('html_content')
        text_content = request.POST.get('text_content')
        category = request.POST.get('category')

        template = EmailTemplate.objects.create(
            name=name,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            category=category,
            created_by=request.user,
            available_merge_fields=get_merge_fields()
        )

        messages.success(request, f'Email template "{name}" created successfully!')
        return redirect('email_management')

    return render(request, 'accounts/create_email_template.html', {
        'categories': EmailTemplate.CATEGORY_CHOICES,
        'merge_fields': get_merge_fields()
    })

@user_passes_test(lambda u: u.is_staff)
def send_template_email(request, template_id):
    """Send email using a template"""
    template = get_object_or_404(EmailTemplate, id=template_id)

    if request.method == 'POST':
        # Create campaign
        campaign_name = request.POST.get('campaign_name')
        recipient_type = request.POST.get('recipient_type')
        mode = request.POST.get('mode', 'test')

        campaign = EmailCampaign.objects.create(
            name=campaign_name,
            template=template,
            recipient_type=recipient_type,
            mode=mode,
            created_by=request.user,
        )

        # Process and send immediately
        try:
            # Import inside function to avoid circular import
            from .admin import process_email_campaign

            campaign.status = 'sending'
            campaign.save()

            sent_count = process_email_campaign(campaign)

            campaign.status = 'completed'
            campaign.sent_at = timezone.now()
            campaign.save()

            messages.success(request, f'Email sent to {sent_count} recipients!')

        except Exception as e:
            campaign.status = 'failed'
            campaign.save()
            messages.error(request, f'Failed to send email: {str(e)}')

        return redirect('email_management')

    # Calculate recipient counts
    recipient_counts = {}
    for choice, label in EmailCampaign.RECIPIENT_CHOICES:
        if choice == 'all_users':
            count = User.objects.filter(is_active=True).count()
        elif choice == 'active_users':
            cutoff = timezone.now() - timezone.timedelta(days=30)
            count = User.objects.filter(is_active=True, last_login__gte=cutoff).count()
        elif choice == 'survey_completed':
            count = User.objects.filter(travel_surveys__isnull=False).distinct().count()
        elif choice == 'trip_creators':
            count = User.objects.filter(created_trips__isnull=False).distinct().count()
        elif choice == 'admin_only':
            count = User.objects.filter(is_staff=True).count()
        else:
            count = 0
        recipient_counts[choice] = count

    return render(request, 'accounts/send_template_email.html', {
        'template': template,
        'recipient_choices': EmailCampaign.RECIPIENT_CHOICES,
        'recipient_counts': recipient_counts,
        'merge_fields': get_merge_fields()
    })

def unsubscribe_view(request, token):
    """Handle email unsubscribe requests"""
    try:
        profile = UserProfile.objects.get(unsubscribe_token=token)
        user = profile.user

        if request.method == 'POST':
            profile.email_consent = False
            profile.save()
            messages.success(request, f'You have been successfully unsubscribed from HygGeo email communications.')
            return render(request, 'accounts/unsubscribe_success.html', {'user': user})

        # Show confirmation page
        return render(request, 'accounts/unsubscribe_confirm.html', {
            'user': user,
            'token': token
        })

    except UserProfile.DoesNotExist:
        messages.error(request, 'Invalid unsubscribe link. Please contact support if you continue to receive unwanted emails.')
        return render(request, 'accounts/unsubscribe_error.html')

def resubscribe_view(request, token):
    """Handle email resubscribe requests"""
    try:
        profile = UserProfile.objects.get(unsubscribe_token=token)
        user = profile.user

        if request.method == 'POST':
            profile.email_consent = True
            profile.save()
            messages.success(request, f'You have been successfully resubscribed to HygGeo email communications.')
            return render(request, 'accounts/resubscribe_success.html', {'user': user})

        # Show confirmation page
        return render(request, 'accounts/resubscribe_confirm.html', {
            'user': user,
            'token': token
        })

    except UserProfile.DoesNotExist:
        messages.error(request, 'Invalid resubscribe link. Please contact support if you need assistance.')
        return render(request, 'accounts/resubscribe_error.html')

@user_passes_test(lambda u: u.is_staff)
def export_experience_types_json(request):
    """Export all experience types as JSON"""
    from experiences.models import ExperienceType
    from django.http import JsonResponse

    experience_types = list(ExperienceType.objects.values(
        'id', 'name', 'description', 'icon_class', 'color_code', 'is_active'
    ))

    response = JsonResponse({
        'experience_types': experience_types,
        'count': len(experience_types),
        'exported_at': timezone.now().isoformat()
    })
    response['Content-Disposition'] = 'attachment; filename="experience_types.json"'
    return response

@user_passes_test(lambda u: u.is_staff)
def export_categories_json(request):
    """Export all categories as JSON"""
    from experiences.models import Category
    from django.http import JsonResponse

    categories = list(Category.objects.values(
        'id', 'name', 'description', 'icon_class', 'color_code', 'is_active'
    ))

    response = JsonResponse({
        'categories': categories,
        'count': len(categories),
        'exported_at': timezone.now().isoformat()
    })
    response['Content-Disposition'] = 'attachment; filename="categories.json"'
    return response

def faq_view(request):
    """Display the FAQs page"""
    return render(request, 'accounts/faq.html')

@user_passes_test(lambda u: u.is_staff, login_url='/accounts/login/')
def toggle_featured_status(request):
    """Toggle featured status for experiences or accommodations via AJAX"""
    from django.http import JsonResponse
    from django.core.cache import cache

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    content_type = request.POST.get('content_type')  # 'experience' or 'accommodation'
    content_id = request.POST.get('content_id')

    try:
        if content_type == 'experience':
            item = Experience.objects.get(id=content_id)
            item.is_featured = not item.is_featured
            item.save()
            # Clear cache (both old and new keys)
            cache.delete('index_featured_experiences')
            cache.delete('index_featured_experiences_v2')
        elif content_type == 'accommodation':
            item = Accommodation.objects.get(id=content_id)
            item.is_featured = not item.is_featured
            item.save()
            # Clear cache
            cache.delete('index_featured_accommodations')
        else:
            return JsonResponse({'success': False, 'error': 'Invalid content type'}, status=400)

        return JsonResponse({
            'success': True,
            'is_featured': item.is_featured,
            'message': f'{"Featured" if item.is_featured else "Unfeatured"} successfully'
        })
    except (Experience.DoesNotExist, Accommodation.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Item not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@user_passes_test(lambda u: u.is_staff, login_url='/accounts/login/')
def get_items_for_destination(request):
    """AJAX endpoint to get items for a destination"""
    from django.http import JsonResponse

    destination_id = request.GET.get('destination')
    item_type = request.GET.get('type')

    if not destination_id:
        return JsonResponse({'error': 'Destination required'}, status=400)

    try:
        items = []

        if item_type == 'experiences':
            # Don't filter by is_active for staff users - show all experiences
            queryset = Experience.objects.filter(
                destination_id=destination_id
            ).select_related('provider', 'experience_type').order_by('-sustainability_score', '-created_at')

            for exp in queryset:
                short_desc = exp.short_description or exp.title
                description = short_desc[:100] + '...' if len(short_desc) > 100 else short_desc
                # Include experience type in the description if available
                exp_type = f" ({exp.experience_type.name})" if exp.experience_type else ""
                items.append({
                    'id': str(exp.id),
                    'name': exp.title + exp_type,
                    'description': description,
                    'sustainability': exp.sustainability_score or 0,
                    'hygge': exp.hygge_factor or 0,
                    'is_active': exp.is_active,
                })

        elif item_type == 'accommodations':
            # Don't filter by is_active for staff users - show all accommodations
            queryset = Accommodation.objects.filter(
                destination_id=destination_id
            ).select_related('provider').order_by('-sustainability_score', '-created_at')

            for acc in queryset:
                short_desc = acc.short_description or acc.name
                description = short_desc[:100] + '...' if len(short_desc) > 100 else short_desc
                # Use the model's built-in method
                acc_type = f" ({acc.get_accommodation_type_display()})" if acc.accommodation_type else ""
                items.append({
                    'id': str(acc.id),
                    'name': acc.name + acc_type,
                    'description': description,
                    'sustainability': acc.sustainability_score or 0,
                    'hygge': acc.hygge_factor or 0,
                    'is_active': acc.is_active,
                })

        elif item_type == 'mixed':
            # Get both experiences and accommodations - don't filter by is_active
            exp_queryset = Experience.objects.filter(
                destination_id=destination_id
            ).select_related('provider', 'experience_type').order_by('-sustainability_score', '-created_at')[:30]

            acc_queryset = Accommodation.objects.filter(
                destination_id=destination_id
            ).select_related('provider').order_by('-sustainability_score', '-created_at')[:30]

            for exp in exp_queryset:
                short_desc = exp.short_description or exp.title
                description = short_desc[:100] + '...' if len(short_desc) > 100 else short_desc
                exp_type = f" ({exp.experience_type.name})" if exp.experience_type else ""
                items.append({
                    'id': f'exp_{exp.id}',
                    'name': exp.title + exp_type,
                    'description': description,
                    'sustainability': exp.sustainability_score or 0,
                    'hygge': exp.hygge_factor or 0,
                    'is_active': exp.is_active,
                    'type': 'experience',
                })

            for acc in acc_queryset:
                short_desc = acc.short_description or acc.name
                description = short_desc[:100] + '...' if len(short_desc) > 100 else short_desc
                # Use the model's built-in method (matching line 1707)
                acc_type = f" ({acc.get_accommodation_type_display()})" if acc.accommodation_type else ""
                items.append({
                    'id': f'acc_{acc.id}',
                    'name': acc.name + acc_type,
                    'description': description,
                    'sustainability': acc.sustainability_score or 0,
                    'hygge': acc.hygge_factor or 0,
                    'is_active': acc.is_active,
                    'type': 'accommodation',
                })

        return JsonResponse({'items': items})

    except Exception as e:
        # Add detailed logging for debugging
        import traceback
        error_details = {
            'error': str(e),
            'error_type': type(e).__name__,
            'traceback': traceback.format_exc(),
            'destination_id': destination_id,
            'item_type': item_type,
        }
        print(f"ERROR in get_items_for_destination: {error_details}")  # Log to console
        return JsonResponse({'error': str(e)}, status=500)

@user_passes_test(lambda u: u.is_staff, login_url='/accounts/login/')
def generate_top_10_blog(request):
    """Generate a Top 10 blog post with experiences/accommodations"""
    from experiences.models import TravelBlog
    from django.utils.text import slugify
    from datetime import datetime

    if request.method != 'POST':
        messages.error(request, 'Invalid request method')
        return redirect('admin_dashboard')

    try:
        # Get form data
        blog_type = request.POST.get('blog_type')
        destination_id = request.POST.get('destination')
        selection_method = request.POST.get('selection_method', 'auto')
        publish = request.POST.get('publish') == 'true'

        # Auto-selection parameters
        filter_by = request.POST.get('filter_by', 'sustainability')
        item_count = int(request.POST.get('item_count', 10))

        # Manual selection parameters
        selected_items = request.POST.getlist('selected_items')

        # Title handling
        title_template = request.POST.get('title_template', '')
        custom_title = request.POST.get('custom_title', '').strip()

        # Intro handling
        include_intro = request.POST.get('include_intro', 'auto')
        custom_intro = request.POST.get('custom_intro', '').strip() if include_intro == 'custom' else ''

        # Get destination
        destination = Destination.objects.get(id=destination_id)

        # Build query based on blog type and selection method
        items = []

        # Handle manual selection
        if selection_method == 'manual' and selected_items:
            if blog_type == 'experiences':
                items = list(Experience.objects.filter(
                    id__in=selected_items,
                    is_active=True
                ).select_related('destination', 'provider', 'experience_type'))
                content_type_label = "Experiences"
            elif blog_type == 'accommodations':
                items = list(Accommodation.objects.filter(
                    id__in=selected_items,
                    is_active=True
                ).select_related('destination', 'provider'))
                content_type_label = "Accommodations"
            elif blog_type == 'mixed':
                # Handle mixed selection (exp_123 or acc_456 format)
                exp_ids = [item.replace('exp_', '') for item in selected_items if item.startswith('exp_')]
                acc_ids = [item.replace('acc_', '') for item in selected_items if item.startswith('acc_')]

                experiences = Experience.objects.filter(
                    id__in=exp_ids,
                    is_active=True
                ).select_related('destination', 'provider', 'experience_type')

                accommodations = Accommodation.objects.filter(
                    id__in=acc_ids,
                    is_active=True
                ).select_related('destination', 'provider')

                items = []
                for exp in experiences:
                    exp.item_type = 'experience'
                    items.append(exp)
                for acc in accommodations:
                    acc.item_type = 'accommodation'
                    items.append(acc)

                content_type_label = "Things to Do"

        # Handle auto-selection
        elif selection_method == 'auto' or not selected_items:
            if blog_type == 'experiences':
                queryset = Experience.objects.filter(
                    destination=destination,
                    is_active=True
                ).select_related('destination', 'provider', 'experience_type')

                # Apply filters
                if filter_by == 'sustainability':
                    queryset = queryset.order_by('-sustainability_score', '-hygge_factor')
                elif filter_by == 'hygge':
                    queryset = queryset.order_by('-hygge_factor', '-sustainability_score')
                elif filter_by == 'featured':
                    queryset = queryset.filter(is_featured=True).order_by('-created_at')
                elif filter_by == 'recent':
                    queryset = queryset.order_by('-created_at')
                elif filter_by == 'random':
                    queryset = queryset.order_by('?')

                items = list(queryset[:item_count])
                content_type_label = "Experiences"

            elif blog_type == 'accommodations':
                queryset = Accommodation.objects.filter(
                    destination=destination,
                    is_active=True
                ).select_related('destination', 'provider')

                # Apply filters
                if filter_by == 'sustainability':
                    queryset = queryset.order_by('-sustainability_score', '-hygge_factor')
                elif filter_by == 'hygge':
                    queryset = queryset.order_by('-hygge_factor', '-sustainability_score')
                elif filter_by == 'featured':
                    queryset = queryset.filter(is_featured=True).order_by('-created_at')
                elif filter_by == 'recent':
                    queryset = queryset.order_by('-created_at')
                elif filter_by == 'random':
                    queryset = queryset.order_by('?')

                items = list(queryset[:item_count])
                content_type_label = "Accommodations"

            elif blog_type == 'mixed':
                # Get half experiences and half accommodations
                exp_count = item_count // 2
                acc_count = item_count - exp_count

                exp_queryset = Experience.objects.filter(
                    destination=destination,
                    is_active=True
                ).select_related('destination', 'provider', 'experience_type')

                acc_queryset = Accommodation.objects.filter(
                    destination=destination,
                    is_active=True
                ).select_related('destination', 'provider')

                # Apply filters to both
                if filter_by == 'sustainability':
                    exp_queryset = exp_queryset.order_by('-sustainability_score')
                    acc_queryset = acc_queryset.order_by('-sustainability_score')
                elif filter_by == 'hygge':
                    exp_queryset = exp_queryset.order_by('-hygge_factor')
                    acc_queryset = acc_queryset.order_by('-hygge_factor')
                elif filter_by == 'featured':
                    exp_queryset = exp_queryset.filter(is_featured=True).order_by('-created_at')
                    acc_queryset = acc_queryset.filter(is_featured=True).order_by('-created_at')
                elif filter_by == 'recent':
                    exp_queryset = exp_queryset.order_by('-created_at')
                    acc_queryset = acc_queryset.order_by('-created_at')
                elif filter_by == 'random':
                    exp_queryset = exp_queryset.order_by('?')
                    acc_queryset = acc_queryset.order_by('?')

                experiences = list(exp_queryset[:exp_count])
                accommodations = list(acc_queryset[:acc_count])

                # Combine and mark type
                items = []
                for exp in experiences:
                    exp.item_type = 'experience'
                    items.append(exp)
                for acc in accommodations:
                    acc.item_type = 'accommodation'
                    items.append(acc)

                # Shuffle if random
                if filter_by == 'random':
                    import random
                    random.shuffle(items)

                content_type_label = "Things to Do"

        # Check if we have enough items
        if not items:
            messages.error(request, f'No items found for {destination.name}. Please choose a different destination.')
            return redirect('admin_dashboard')

        # Generate title
        if custom_title:
            title = custom_title
        else:
            filter_labels = {
                'sustainability': 'Most Sustainable',
                'hygge': 'Most Hygge',
                'featured': 'Best',
                'recent': 'Newest',
                'random': 'Top'
            }
            filter_label = filter_labels.get(filter_by, 'Top')
            title = f"{filter_label} {len(items)} {content_type_label} in {destination.name}"

        # Generate slug
        slug = slugify(title)
        # Ensure uniqueness
        original_slug = slug
        counter = 1
        while TravelBlog.objects.filter(slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1

        # Generate intro
        if custom_intro:
            intro = custom_intro
        else:
            intro = f"Discover the {filter_labels.get(filter_by, 'top').lower()} {content_type_label.lower()} in {destination.name}, {destination.country}. From sustainable eco-tourism to hygge-inspired experiences, these carefully selected options embody everything we love about mindful, authentic travel."

        # Generate excerpt
        excerpt = f"Explore our curated list of the {filter_labels.get(filter_by, 'best').lower()} {content_type_label.lower()} in {destination.name}. Perfect for eco-conscious travelers seeking authentic experiences."

        # Generate HTML content
        content_html = f"<p>{intro}</p>\n\n"

        for index, item in enumerate(items, 1):
            # Determine item details based on type
            if blog_type == 'mixed':
                if item.item_type == 'experience':
                    item_title = item.title
                    item_description = item.description
                    item_url = request.build_absolute_uri(item.get_absolute_url())
                    booking_link = item.affiliate_link if item.booking_required else item_url
                    sustainability = item.sustainability_score
                    hygge = item.hygge_factor
                    provider = item.provider.name if item.provider else 'Local Provider'
                else:  # accommodation
                    item_title = item.name
                    item_description = item.description
                    item_url = request.build_absolute_uri(item.get_absolute_url())
                    booking_link = item.booking_link if item.booking_link else item_url
                    sustainability = item.sustainability_score
                    hygge = item.hygge_factor
                    provider = item.provider.name if item.provider else 'Local Provider'
            elif blog_type == 'experiences':
                item_title = item.title
                item_description = item.description
                item_url = request.build_absolute_uri(item.get_absolute_url())
                booking_link = item.affiliate_link if item.booking_required else item_url
                sustainability = item.sustainability_score
                hygge = item.hygge_factor
                provider = item.provider.name if item.provider else 'Local Provider'
            else:  # accommodations
                item_title = item.name
                item_description = item.description
                item_url = request.build_absolute_uri(item.get_absolute_url())
                booking_link = item.booking_link if item.booking_link else item_url
                sustainability = item.sustainability_score
                hygge = item.hygge_factor
                provider = item.provider.name if item.provider else 'Local Provider'

            # Add item to content
            content_html += f"<h2>{index}. {item_title}</h2>\n"
            content_html += f"<p>{item_description}</p>\n"
            content_html += f"<p><strong>Provider:</strong> {provider}</p>\n"
            content_html += f"<p><strong>Sustainability Score:</strong> {sustainability}/10 | <strong>Hygge Factor:</strong> {hygge}/10</p>\n"
            content_html += f"<p><a href=\"{booking_link}\" target=\"_blank\" rel=\"noopener noreferrer\"><strong>Book Now →</strong></a> | "
            content_html += f"<a href=\"{item_url}\">View Details</a></p>\n\n"

        # Add conclusion
        content_html += f"<h2>Plan Your Trip to {destination.name}</h2>\n"
        content_html += f"<p>Ready to explore {destination.name}? These {content_type_label.lower()} represent the best of sustainable, hygge-inspired travel. Each option has been carefully selected for its commitment to environmental responsibility and authentic local experiences.</p>\n"
        content_html += f"<p>Remember to travel mindfully, support local businesses, and leave only footprints behind. Safe travels!</p>\n"

        # Determine featured image - use destination image or random experience/accommodation image
        featured_image = None
        if destination.image:
            featured_image = destination.image
        elif items:
            # Try to find an item with an image
            items_with_images = [item for item in items if hasattr(item, 'main_image') and item.main_image]
            if items_with_images:
                # Pick a random item with an image
                random_item = random.choice(items_with_images)
                featured_image = random_item.main_image

        # Generate SEO-optimized meta title (max 60 characters)
        meta_title = title
        if len(meta_title) > 60:
            # Truncate if too long, keeping the most important parts
            meta_title = f"{filter_labels.get(filter_by, 'Top')} {len(items)} {content_type_label} in {destination.name}"
            if len(meta_title) > 60:
                # Further truncate if still too long
                meta_title = f"{len(items)} Best {content_type_label} in {destination.name}"[:60]

        # Generate SEO-optimized meta description (max 160 characters)
        current_year = datetime.now().year
        meta_description = f"Discover the {filter_labels.get(filter_by, 'best').lower()} {content_type_label.lower()} in {destination.name} for {current_year}. Sustainable, hygge-inspired travel options for eco-conscious travelers."
        if len(meta_description) > 160:
            meta_description = f"Explore {len(items)} {content_type_label.lower()} in {destination.name}. Sustainable travel options for eco-conscious travelers seeking authentic experiences."[:160]

        # Create blog post
        blog = TravelBlog.objects.create(
            title=title,
            slug=slug,
            content=content_html,
            excerpt=excerpt,
            author=request.user,
            destination=destination,
            featured_image=featured_image,
            is_published=publish,
            meta_title=meta_title,
            meta_description=meta_description,
            tags=['top 10', destination.name.lower(), content_type_label.lower(), 'sustainable travel', 'hygge']
        )

        if publish:
            blog.published_at = timezone.now()
            blog.save()

        messages.success(request, f'Blog post "{title}" {"published" if publish else "created as draft"} successfully!')
        return redirect('experiences:edit_blog', slug=blog.slug)

    except Destination.DoesNotExist:
        messages.error(request, 'Selected destination not found.')
        return redirect('admin_dashboard')
    except Exception as e:
        messages.error(request, f'Error generating blog: {str(e)}')
        return redirect('admin_dashboard')