from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import logout


from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone

from .forms import (
    CustomUserCreationForm, 
    UserProfileForm, 
    TravelSurveyForm, 
    UserUpdateForm, 
    TripForm, 
    MessageForm, 
    ReplyForm
)
from .models import UserProfile, TravelSurvey, Trip, Message
from experiences.models import Experience, Destination, Provider, Category, ExperienceType
import random

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
from django.db.models import Q
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

@login_required
def create_trip(request):
    """Create a new trip"""
    if request.method == 'POST':
        form = TripForm(request.POST, request.FILES)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.creator = request.user
            trip.save()
            messages.success(request, 'Your trip has been created successfully!')
            return redirect('trip_detail', pk=trip.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TripForm()
    
    return render(request, 'accounts/create_trip.html', {'form': form})

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
    
    return JsonResponse({
        'DEBUG': settings.DEBUG,
        'INSTALLED_APPS_has_storages': 'storages' in settings.INSTALLED_APPS,
        'AWS_ACCESS_KEY_ID': getattr(settings, 'AWS_ACCESS_KEY_ID', 'NOT_SET')[:8] + '...' if getattr(settings, 'AWS_ACCESS_KEY_ID', None) else 'NOT_SET',
        'AWS_STORAGE_BUCKET_NAME': getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'NOT_SET'),
        'AWS_S3_ENDPOINT_URL': getattr(settings, 'AWS_S3_ENDPOINT_URL', 'NOT_SET'),
        'DEFAULT_FILE_STORAGE': getattr(settings, 'DEFAULT_FILE_STORAGE', 'NOT_SET'),
        'MEDIA_URL': settings.MEDIA_URL,
        'env_SPACES_ACCESS_KEY': 'EXISTS' if os.environ.get('SPACES_ACCESS_KEY') else 'MISSING',
        'env_SPACES_BUCKET_NAME': os.environ.get('SPACES_BUCKET_NAME', 'MISSING'),
    })