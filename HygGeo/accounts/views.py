# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .forms import CustomUserCreationForm, UserProfileForm, TravelSurveyForm, UserUpdateForm
from .models import UserProfile, TravelSurvey
import random

from django.contrib.auth.decorators import user_passes_test

from django.db.models import Count
from experiences.models import Experience, Destination, Provider, Category, ExperienceType


def index(request):
    """Homepage with hygge concept, sustainability facts, and survey CTA"""
    
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
    
    # Check if user has completed a survey
    has_survey = False
    if request.user.is_authenticated:
        has_survey = TravelSurvey.objects.filter(user=request.user).exists()
    
    context = {
        'sustainability_facts': featured_facts,
        'has_survey': has_survey,
    }
    
    return render(request, 'index.html', context)

def signup_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
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
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
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

def user_list_view(request):
    """Public user list (optional - for community features)"""
    search_query = request.GET.get('search', '')
    users = User.objects.filter(is_active=True).select_related('userprofile')
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(userprofile__location__icontains=search_query)
        )
    
    # Paginate users
    paginator = Paginator(users, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'users': page_obj,
        'search_query': search_query,
    }
    
    return render(request, 'accounts/user_list.html', context)

def public_profile_view(request, username):
    """View another user's public profile"""
    user = get_object_or_404(User, username=username, is_active=True)
    profile = get_object_or_404(UserProfile, user=user)
    
    # Get latest survey for travel interests (if user allows public viewing)
    latest_survey = TravelSurvey.objects.filter(user=user).first()
    
    context = {
        'profile_user': user,
        'profile': profile,
        'latest_survey': latest_survey,
        'is_own_profile': request.user == user,
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
    }
    
    # Get recent activity (last 6 experiences)
    recent_experiences = Experience.objects.select_related('destination').order_by('-created_at')[:6]
    
    # Get recent destinations
    recent_destinations = Destination.objects.order_by('-created_at')[:5]
    
    # Get active/featured counts
    featured_experiences = Experience.objects.filter(is_featured=True).count()
    active_experiences = Experience.objects.filter(is_active=True).count()
    
    context = {
        'stats': stats,
        'recent_experiences': recent_experiences,
        'recent_destinations': recent_destinations,
        'featured_count': featured_experiences,
        'active_count': active_experiences,
    }
    
    # Updated template path to match your file location
    return render(request, 'admin-dashboard.html', context)