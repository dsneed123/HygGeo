# experiences/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from accounts.models import TravelSurvey
from experiences.forms import ExperienceForm, DestinationForm, ExperienceTypeForm, CategoryForm
from .forms import ProviderForm  # add this import at top
from django.utils.text import slugify 
from collections import defaultdict
from .models import (
    Experience, Destination, Category, Provider, 
    UserRecommendation, ExperienceReview, BookingTracking, ExperienceType
)
import random
from decimal import Decimal

def generate_recommendations(user):
    """Generate personalized recommendations based on user survey"""
    # Get user's latest survey
    survey = TravelSurvey.objects.filter(user=user).first()
    if not survey:
        return Experience.objects.filter(is_active=True, is_featured=True)[:6]
    
    # Start with all active experiences
    experiences = Experience.objects.filter(is_active=True)
    scored_experiences = []
    
    for experience in experiences:
        score = 0
        reasons = []
        
        # Travel style matching (30% weight)
        if hasattr(survey, 'travel_styles') and survey.travel_styles:
            style_matches = set(survey.travel_styles) & set(experience.travel_styles)
            if style_matches:
                score += 30
                reasons.append(f"Matches your interest in {', '.join(style_matches)}")
        
        # Budget matching (20% weight)
        if survey.budget_range == experience.budget_range:
            score += 20
            reasons.append("Fits your budget range")
        
        # Group size matching (15% weight)
        if survey.group_size_preference == experience.group_size:
            score += 15
            reasons.append("Perfect for your group size")
        
        # Sustainability factors (25% weight)
        if hasattr(survey, 'sustainability_factors') and survey.sustainability_factors:
            sustainability_matches = set(survey.sustainability_factors) & set(experience.sustainability_factors)
            if sustainability_matches:
                score += 25
                reasons.append(f"Matches your sustainability priorities: {', '.join(sustainability_matches)}")
        
        # Accommodation preferences (10% weight)
        if hasattr(survey, 'accommodation_preferences') and survey.accommodation_preferences:
            accommodation_matches = set(survey.accommodation_preferences) & set(experience.accommodation_types)
            if accommodation_matches:
                score += 10
                reasons.append("Matches your accommodation preferences")
        
        # Bonus points for high sustainability and hygge scores
        if experience.sustainability_score >= 8:
            score += 5
            reasons.append("Highly sustainable option")
        
        if experience.hygge_factor >= 8:
            score += 5
            reasons.append("Embodies hygge principles")
        
        if score > 0:
            scored_experiences.append({
                'experience': experience,
                'score': score,
                'reasons': reasons
            })
    
    # Sort by score and return top experiences
    scored_experiences.sort(key=lambda x: x['score'], reverse=True)
    
    # Save recommendations to database
    for item in scored_experiences[:20]:  # Save top 20
        recommendation, created = UserRecommendation.objects.get_or_create(
            user=user,
            experience=item['experience'],
            defaults={
                'match_score': Decimal(str(item['score'])),
                'reasons': item['reasons']
            }
        )
    
    return [item['experience'] for item in scored_experiences[:12]]

@login_required
def recommendations_view(request):
    """Display personalized recommendations for the user"""
    # Check if user has completed survey
    survey = TravelSurvey.objects.filter(user=request.user).first()
    if not survey:
        messages.info(request, 'Complete your travel survey to get personalized recommendations!')
        return redirect('survey')
    
    # Generate recommendations
    recommended_experiences = generate_recommendations(request.user)
    
    # Get some featured experiences for variety
    featured_experiences = Experience.objects.filter(
        is_active=True, 
        is_featured=True
    ).exclude(
        id__in=[exp.id for exp in recommended_experiences]
    )[:4]
    
    # Get popular destinations
    popular_destinations = Destination.objects.annotate(
        experience_count=Count('experiences')
    ).filter(experience_count__gt=0).order_by('-experience_count')[:6]
    
    context = {
        'survey': survey,
        'recommended_experiences': recommended_experiences,
        'featured_experiences': featured_experiences,
        'popular_destinations': popular_destinations,
    }
    
    return render(request, 'experiences/recommendations.html', context)

def experience_list_view(request):
    """Browse all experiences with filtering"""
    experiences = Experience.objects.filter(is_active=True).select_related(
        'destination', 'provider'
    ).prefetch_related('categories')
    
    # Filtering
    category_slug = request.GET.get('category')
    destination_slug = request.GET.get('destination')
    experience_type = request.GET.get('type')
    budget_range = request.GET.get('budget')
    sustainability_min = request.GET.get('sustainability_min')
    search_query = request.GET.get('search')
    
    if category_slug:
        experiences = experiences.filter(categories__slug=category_slug)
    
    if destination_slug:
        experiences = experiences.filter(destination__slug=destination_slug)
    
    if experience_type:
        experiences = experiences.filter(experience_type=experience_type)
    
    if budget_range:
        experiences = experiences.filter(budget_range=budget_range)
    
    if sustainability_min:
        experiences = experiences.filter(sustainability_score__gte=sustainability_min)
    
    if search_query:
        experiences = experiences.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(destination__name__icontains=search_query) |
            Q(destination__country__icontains=search_query)
        )
    
    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_low':
        experiences = experiences.order_by('price_from')
    elif sort_by == 'price_high':
        experiences = experiences.order_by('-price_from')
    elif sort_by == 'sustainability':
        experiences = experiences.order_by('-sustainability_score')
    elif sort_by == 'hygge':
        experiences = experiences.order_by('-hygge_factor')
    else:  # newest
        experiences = experiences.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(experiences, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    categories = Category.objects.all()
    destinations = Destination.objects.annotate(
        experience_count=Count('experiences')
    ).filter(experience_count__gt=0)
    
    context = {
        'experiences': page_obj,
        'categories': categories,
        'destinations': destinations,
        'experience_types': Experience.EXPERIENCE_TYPES,
        'budget_ranges': Experience.BUDGET_RANGES,
        'current_filters': {
            'category': category_slug,
            'destination': destination_slug,
            'type': experience_type,
            'budget': budget_range,
            'sustainability_min': sustainability_min,
            'search': search_query,
            'sort': sort_by,
        }
    }
    
    return render(request, 'experiences/experience_list.html', context)

def experience_detail_view(request, slug):
    """Detailed view of an experience"""
    experience = get_object_or_404(
        Experience.objects.select_related('destination', 'provider').prefetch_related('categories'),
        slug=slug,
        is_active=True
    )
    
    # Get reviews
    reviews = experience.reviews.all().order_by('-created_at')
    
    # Calculate review statistics
    review_stats = {
        'count': reviews.count(),
        'avg_rating': 0,
        'avg_sustainability': 0,
        'avg_hygge': 0,
    }
    
    if reviews:
        review_stats['avg_rating'] = reviews.aggregate(Avg('rating'))['rating__avg']
        review_stats['avg_sustainability'] = reviews.aggregate(Avg('sustainability_rating'))['sustainability_rating__avg']
        review_stats['avg_hygge'] = reviews.aggregate(Avg('hygge_rating'))['hygge_rating__avg']
    
    # Get similar experiences
    similar_experiences = Experience.objects.filter(
        is_active=True,
        destination=experience.destination
    ).exclude(id=experience.id)[:4]
    
    if similar_experiences.count() < 4:
        # Fill with experiences from same categories
        additional = Experience.objects.filter(
            is_active=True,
            categories__in=experience.categories.all()
        ).exclude(id=experience.id).exclude(
            id__in=[exp.id for exp in similar_experiences]
        ).distinct()[:4-similar_experiences.count()]
        
        similar_experiences = list(similar_experiences) + list(additional)
    
    # Track view if user is logged in
    if request.user.is_authenticated:
        try:
            recommendation = UserRecommendation.objects.get(
                user=request.user,
                experience=experience
            )
            recommendation.viewed = True
            recommendation.save()
        except UserRecommendation.DoesNotExist:
            pass
    
    context = {
        'experience': experience,
        'reviews': reviews[:5],  # Show first 5 reviews
        'review_stats': review_stats,
        'similar_experiences': similar_experiences,
    }
    
    return render(request, 'experiences/experience_detail.html', context)

def destination_list_view(request):
    destinations = Destination.objects.all().order_by('name')

    # Group by country
    destinations_by_country = {}
    for destination in destinations:
        if destination.country not in destinations_by_country:
            destinations_by_country[destination.country] = []
        destinations_by_country[destination.country].append(destination)

    context = {
        'destinations_by_country': destinations_by_country,
    }
    
    return render(request, 'experiences/destination_list.html', context)


def destination_detail_view(request, slug):

    destination = get_object_or_404(Destination, slug=slug)
    # Fetch active experiences for the destination
    experiences = Experience.objects.filter(destination=destination, is_active=True)
    # Group experiences by experience_type.name
    experiences_by_type = defaultdict(list)
    for experience in experiences:
        exp_type_name = experience.experience_type.name if experience.experience_type else "Unspecified"
        experiences_by_type[exp_type_name].append(experience)
    # Convert to regular dict
    experiences_by_type = dict(experiences_by_type)
    # Calculate total experiences
    total_experiences = len(experiences)
    context = {
        'destination': destination,
        'experiences_by_type': experiences_by_type,
        'total_experiences': total_experiences,
    }
    return render(request, 'experiences/destination_detail.html', context)
    
def destination_detail_view(request, slug):
    """Detailed view of a destination"""
    destination = get_object_or_404(Destination, slug=slug)
    
    experiences = destination.experiences.filter(is_active=True).order_by('-created_at')
    
    # Group experiences by type
    experiences_by_type = {}
    for experience in experiences:
        exp_type = experience.experience_type.name if experience.experience_type else "Unspecified"
        if exp_type not in experiences_by_type:
            experiences_by_type[exp_type] = []
        experiences_by_type[exp_type].append(experience)
    
    context = {
        'destination': destination,
        'experiences': experiences,
        'experiences_by_type': experiences_by_type,
        'total_experiences': experiences.count(),
    }
    
    return render(request, 'experiences/destination_detail.html', context)

def category_detail_view(request, slug):
    """Experiences by category"""
    category = get_object_or_404(Category, slug=slug)
    
    experiences = category.experiences.filter(is_active=True).select_related(
        'destination', 'provider'
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(experiences, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'experiences': page_obj,
    }
    
    return render(request, 'experiences/category_detail.html', context)

@require_POST
def track_affiliate_click(request, experience_id):
    """Track affiliate link clicks"""
    try:
        experience = Experience.objects.get(id=experience_id, is_active=True)
        
        # Create tracking record
        tracking = BookingTracking.objects.create(
            user=request.user if request.user.is_authenticated else None,
            experience=experience,
            session_id=request.session.session_key or 'anonymous',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Mark recommendation as clicked if exists
        if request.user.is_authenticated:
            try:
                recommendation = UserRecommendation.objects.get(
                    user=request.user,
                    experience=experience
                )
                recommendation.clicked = True
                recommendation.save()
            except UserRecommendation.DoesNotExist:
                pass
        
        return JsonResponse({
            'success': True,
            'redirect_url': experience.affiliate_link
        })
        
    except Experience.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Experience not found'})

@login_required
@require_POST
def bookmark_experience(request, experience_id):
    """Bookmark/unbookmark an experience"""
    try:
        experience = Experience.objects.get(id=experience_id, is_active=True)
        
        recommendation, created = UserRecommendation.objects.get_or_create(
            user=request.user,
            experience=experience,
            defaults={
                'match_score': Decimal('0'),
                'reasons': ['Manually bookmarked']
            }
        )
        
        recommendation.bookmarked = not recommendation.bookmarked
        recommendation.save()
        
        return JsonResponse({
            'success': True,
            'bookmarked': recommendation.bookmarked
        })
        
    except Experience.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Experience not found'})

@login_required
def my_bookmarks_view(request):
    """View user's bookmarked experiences"""
    bookmarks = UserRecommendation.objects.filter(
        user=request.user,
        bookmarked=True
    ).select_related('experience__destination', 'experience__provider')
    
    context = {
        'bookmarks': bookmarks,
    }
    
    return render(request, 'experiences/my_bookmarks.html', context)

@user_passes_test(lambda u: u.is_staff)  # staff/admin only
def add_experience(request):
    if request.method == "POST":
        form = ExperienceForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                experience = form.save(commit=False)
                
                # Auto-generate slug if not provided
                if not experience.slug:
                    base_slug = slugify(experience.title)
                    slug = base_slug
                    counter = 1
                    
                    # Ensure slug is unique
                    while Experience.objects.filter(slug=slug).exists():
                        slug = f"{base_slug}-{counter}"
                        counter += 1
                    
                    experience.slug = slug
                
                # Set default affiliate link if not provided
                if not experience.affiliate_link:
                    experience.affiliate_link = "https://placeholder-affiliate-link.com"
                
                experience.save()
                
                # Save many-to-many relationships (e.g., categories)
                form.save_m2m()
                
                messages.success(request, f'✅ Experience "{experience.title}" created successfully!')
                return redirect('experiences:experience_list')
                
            except Exception as e:
                messages.error(request, f'❌ Error creating experience: {str(e)}')
                print(f"Error details: {e}")  # For debugging
        else:
            messages.error(request, '⚠️ Please correct the errors below.')
            print(f"Form errors: {form.errors}")  # For debugging
    else:
        form = ExperienceForm()
    
    # Fetch data for dropdowns
    destinations = Destination.objects.all()
    providers = Provider.objects.all()
    experience_types = ExperienceType.objects.all()
    categories = Category.objects.all()
    
    return render(request, 'experiences/add_experience.html', {
        'form': form,
        'page_title': 'Add New Experience',
        'destinations': destinations,
        'providers': providers,
        'experience_types': experience_types,
        'categories': categories,
    })

@user_passes_test(lambda u: u.is_staff)  # restrict to staff/admin
def add_destination(request):
    if request.method == "POST":
        form = DestinationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('experiences:destination_list' )  # change to your destination listing view name if different
    else:
        form = DestinationForm()
    return render(request, 'experiences/add_destination.html', {'form': form})

@user_passes_test(lambda u: u.is_staff)  # staff/admin only
def add_provider(request):
    if request.method == "POST":
        form = ProviderForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('experiences:experience_list')  # or provider list if you have one
    else:
        form = ProviderForm()
    return render(request, 'experiences/add_provider.html', {'form': form})
@user_passes_test(lambda u: u.is_staff)
def add_experience_type(request):
    if request.method == "POST":
        form = ExperienceTypeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('experiences:add_experience')  # or to a list view if you want
    else:
        form = ExperienceTypeForm()
    return render(request, 'experiences/add_experience_type.html', {'form': form})

@user_passes_test(lambda u: u.is_staff)
def add_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('experiences:add_experience')  # or a category list view if you have one
    else:
        form = CategoryForm()
    return render(request, 'experiences/add_category.html', {'form': form})
@login_required
@require_POST
def remove_bookmark_view(request, experience_id):
    try:
        recommendation = UserRecommendation.objects.get(
            user=request.user,
            experience_id=experience_id,
            bookmarked=True
        )
        recommendation.bookmarked = False
        recommendation.save()
        return JsonResponse({'success': True})
    except UserRecommendation.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bookmark not found'})

@require_POST
def track_booking_view(request, experience_id):
    experience = get_object_or_404(Experience, id=experience_id)
    
    # Create booking tracking record
    BookingTracking.objects.create(
        user=request.user if request.user.is_authenticated else None,
        experience=experience,
        session_id=request.session.session_key or 'anonymous',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return JsonResponse({'success': True})
@login_required
def my_bookmarks_view(request):
    bookmarked_experiences = UserRecommendation.objects.filter(
        user=request.user,
        bookmarked=True
    ).select_related('experience', 'experience__destination', 'experience__provider')
    
    # Optional pagination
    paginator = Paginator(bookmarked_experiences, 12)  # 12 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'bookmarked_experiences': page_obj,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': page_obj,
    }
    return render(request, 'experiences/my_bookmarks.html', context)
def about_view(request):
    return render(request, 'experiences/about.html')

@user_passes_test(lambda u: u.is_staff)  # staff/admin only
def edit_experience(request, slug):
    experience = get_object_or_404(Experience, slug=slug)

    if request.method == "POST":
        form = ExperienceForm(request.POST, request.FILES, instance=experience)
        if form.is_valid():
            try:
                experience = form.save(commit=False)

                # Auto-generate slug if changed and not provided
                if not experience.slug or experience.slug != slug:
                    base_slug = slugify(experience.title)
                    new_slug = base_slug
                    counter = 1

                    # Ensure slug is unique (excluding current experience)
                    while Experience.objects.filter(slug=new_slug).exclude(id=experience.id).exists():
                        new_slug = f"{base_slug}-{counter}"
                        counter += 1

                    experience.slug = new_slug

                experience.save()

                # Save many-to-many relationships (e.g., categories)
                form.save_m2m()

                messages.success(request, f'✅ Experience "{experience.title}" updated successfully!')
                return redirect('experiences:experience_detail', slug=experience.slug)

            except Exception as e:
                messages.error(request, f'❌ Error updating experience: {str(e)}')
                print(f"Error details: {e}")  # For debugging
        else:
            messages.error(request, '⚠️ Please correct the errors below.')
            print(f"Form errors: {form.errors}")  # For debugging
    else:
        form = ExperienceForm(instance=experience)

    # Fetch data for dropdowns
    destinations = Destination.objects.all()
    providers = Provider.objects.all()
    experience_types = ExperienceType.objects.all()
    categories = Category.objects.all()

    return render(request, 'experiences/edit_experience.html', {
        'form': form,
        'experience': experience,
        'page_title': f'Edit Experience - {experience.title}',
        'destinations': destinations,
        'providers': providers,
        'experience_types': experience_types,
        'categories': categories,
    })


