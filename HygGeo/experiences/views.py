# experiences/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from django.utils.html import escape
import re
from accounts.models import TravelSurvey
from experiences.forms import ExperienceForm, DestinationForm, ExperienceTypeForm, CategoryForm, AccommodationForm, TravelBlogForm, BlogCommentForm
from .forms import ProviderForm  # add this import at top
from django.utils.text import slugify
from collections import defaultdict
from .models import (
    Experience, Destination, Category, Provider,
    UserRecommendation, ExperienceReview, BookingTracking, ExperienceType, Accommodation, TravelBlog, BlogComment
)
from .recommendation_engine import RecommendationEngine
import random
from decimal import Decimal

# HTML Sanitization function
def sanitize_html(content):
    """
    Sanitize HTML content to only allow safe tags and attributes.
    Prevents XSS attacks while allowing basic formatting.
    """
    # Remove script tags and their content
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)

    # Remove on* event handlers (onclick, onload, etc.)
    content = re.sub(r'\son\w+\s*=\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\son\w+\s*=\s*[^\s>]*', '', content, flags=re.IGNORECASE)

    # Remove javascript: protocol from links
    content = re.sub(r'href\s*=\s*["\']javascript:[^"\']*["\']', 'href="#"', content, flags=re.IGNORECASE)

    # Remove style tags and their content
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)

    # Remove iframe, object, embed tags
    content = re.sub(r'<(iframe|object|embed)[^>]*>.*?</\1>', '', content, flags=re.DOTALL | re.IGNORECASE)

    # Remove any other potentially dangerous tags
    dangerous_tags = ['script', 'style', 'iframe', 'object', 'embed', 'form', 'input', 'button']
    for tag in dangerous_tags:
        content = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(f'<{tag}[^>]*/?>', '', content, flags=re.IGNORECASE)

    # Convert plain text newlines to <br> tags (preserve line breaks)
    # But don't convert newlines that are already inside HTML tags
    content = re.sub(r'\n(?![^<>]*>)', '<br>\n', content)

    return content

def generate_recommendations(user):
    """Generate personalized recommendations using the recommendation engine"""
    engine = RecommendationEngine()

    # Generate fresh recommendations
    recommendations = engine.generate_recommendations_for_user(user.id, limit=20)

    if not recommendations:
        # Fallback to featured experiences if no survey or recommendations
        return Experience.objects.filter(is_active=True, is_featured=True)[:12]

    # Return the experience objects from the recommendations
    return [rec.experience for rec in recommendations[:12]]

@login_required
def recommendations_view(request):
    """Display personalized recommendations for the user"""
    # Check if user has completed survey
    survey = TravelSurvey.objects.filter(user=request.user).first()
    if not survey:
        messages.info(request, 'Complete your travel survey to get personalized recommendations!')
        return redirect('survey')

    # Get or generate recommendations
    user_recommendations = UserRecommendation.objects.filter(
        user=request.user
    ).select_related('experience__destination', 'experience__provider', 'experience__experience_type').order_by('-match_score')

    # If no recommendations exist, generate them
    if not user_recommendations.exists():
        engine = RecommendationEngine()
        engine.generate_recommendations_for_user(request.user.id, limit=20)
        user_recommendations = UserRecommendation.objects.filter(
            user=request.user
        ).select_related('experience__destination', 'experience__provider', 'experience__experience_type').order_by('-match_score')

    # Get top recommendations for display
    top_recommendations = user_recommendations[:12]

    # Get recommended experience IDs for filtering featured experiences
    recommended_experience_ids = [rec.experience.id for rec in top_recommendations]

    # Get some featured experiences for variety
    featured_experiences = Experience.objects.filter(
        is_active=True,
        is_featured=True
    ).exclude(
        id__in=recommended_experience_ids
    )[:4]

    # Get popular destinations
    popular_destinations = Destination.objects.annotate(
        experience_count=Count('experiences')
    ).filter(experience_count__gt=0).order_by('-experience_count')[:6]

    context = {
        'survey': survey,
        'user_recommendations': top_recommendations,
        'featured_experiences': featured_experiences,
        'popular_destinations': popular_destinations,
    }

    return render(request, 'experiences/recommendations.html', context)

def experience_list_view(request):
    """Browse all experiences with filtering and load more functionality"""
    experiences = Experience.objects.filter(is_active=True).select_related(
        'destination', 'provider', 'experience_type'
    ).prefetch_related('categories')

    # Filtering
    category_slug = request.GET.get('category')
    destination_slug = request.GET.get('destination')
    experience_type_slug = request.GET.get('type')
    budget_range = request.GET.get('budget')
    sustainability_min = request.GET.get('sustainability_min')
    hygge_min = request.GET.get('hygge_min')
    group_size = request.GET.get('group_size')
    duration = request.GET.get('duration')
    carbon_neutral = request.GET.get('carbon_neutral')
    search_query = request.GET.get('search', '')

    # Apply filters
    if category_slug:
        experiences = experiences.filter(categories__slug=category_slug).distinct()

    if destination_slug:
        experiences = experiences.filter(destination__slug=destination_slug)

    if experience_type_slug:
        experiences = experiences.filter(experience_type__slug=experience_type_slug)

    if budget_range:
        experiences = experiences.filter(budget_range=budget_range)

    if group_size:
        experiences = experiences.filter(group_size=group_size)

    if duration:
        experiences = experiences.filter(duration=duration)

    if sustainability_min:
        try:
            sustainability_min = int(sustainability_min)
            experiences = experiences.filter(sustainability_score__gte=sustainability_min)
        except (ValueError, TypeError):
            pass

    if hygge_min:
        try:
            hygge_min = int(hygge_min)
            experiences = experiences.filter(hygge_factor__gte=hygge_min)
        except (ValueError, TypeError):
            pass

    if carbon_neutral == 'true':
        experiences = experiences.filter(carbon_neutral=True)

    if search_query:
        search_query = search_query.strip()
        if search_query:
            experiences = experiences.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(short_description__icontains=search_query) |
                Q(destination__name__icontains=search_query) |
                Q(destination__country__icontains=search_query) |
                Q(provider__name__icontains=search_query) |
                Q(categories__name__icontains=search_query)
            ).distinct()

    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_low':
        # Put null prices at the end
        experiences = experiences.order_by('price_from', 'title')
    elif sort_by == 'price_high':
        # Put null prices at the end
        experiences = experiences.order_by('-price_from', 'title')
    elif sort_by == 'sustainability':
        experiences = experiences.order_by('-sustainability_score', '-created_at')
    elif sort_by == 'hygge':
        experiences = experiences.order_by('-hygge_factor', '-created_at')
    elif sort_by == 'alphabetical':
        experiences = experiences.order_by('title')
    else:  # newest
        experiences = experiences.order_by('-created_at')

    # Load more functionality - initially load 12 experiences
    offset = int(request.GET.get('offset', 0))
    limit = 12

    # Get the experiences for this offset
    total_count = experiences.count()
    experiences_slice = experiences[offset:offset + limit]
    has_more = (offset + limit) < total_count

    # Check if this is an AJAX request for load more
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Get user bookmarks for template
        user_bookmarks = get_user_bookmarks(request.user)

        # Render just the experience cards HTML
        from django.template.loader import render_to_string
        html = render_to_string('experiences/experience_cards.html', {
            'experiences': experiences_slice,
            'user_bookmarks': user_bookmarks,
            'user': request.user,
        }, request=request)

        return JsonResponse({
            'html': html,
            'has_more': has_more,
            'next_offset': offset + limit,
            'total_count': total_count,
        })

    # Regular page load - create paginator for initial display
    # Use a fake paginator to work with existing template
    class FakePaginator:
        def __init__(self, count):
            self.count = count

    class FakePage:
        def __init__(self, object_list, paginator):
            self.object_list = object_list
            self.paginator = FakePaginator(paginator)

        def __iter__(self):
            return iter(self.object_list)

        def has_other_pages(self):
            return False  # We'll use load more instead

    page_obj = FakePage(experiences_slice, total_count)

    # Get filter options
    categories = Category.objects.all().order_by('name')
    destinations = Destination.objects.all().order_by('name')
    experience_types = ExperienceType.objects.all().order_by('name')

    # Get user bookmarks for template
    user_bookmarks = get_user_bookmarks(request.user)

    context = {
        'experiences': page_obj,
        'total_count': total_count,
        'has_more': has_more,
        'initial_offset': limit,
        'categories': categories,
        'destinations': destinations,
        'experience_types': experience_types,
        'budget_ranges': Experience.BUDGET_RANGES,
        'group_sizes': Experience.GROUP_SIZES,
        'duration_types': Experience.DURATION_TYPES,
        'user_bookmarks': user_bookmarks,
        'current_filters': {
            'category': category_slug or '',
            'destination': destination_slug or '',
            'type': experience_type_slug or '',
            'budget': budget_range or '',
            'group_size': group_size or '',
            'duration': duration or '',
            'sustainability_min': sustainability_min or '',
            'hygge_min': hygge_min or '',
            'carbon_neutral': carbon_neutral or '',
            'search': search_query or '',
            'sort': sort_by or 'newest',
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
    
    # Check if user has bookmarked this experience
    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = UserRecommendation.objects.filter(
            user=request.user,
            experience=experience,
            bookmarked=True
        ).exists()

    context = {
        'experience': experience,
        'reviews': reviews[:5],  # Show first 5 reviews
        'review_stats': review_stats,
        'similar_experiences': similar_experiences,
        'is_bookmarked': is_bookmarked,
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

    # Get accommodations for this destination
    accommodations = destination.accommodations.filter(is_active=True).order_by('-created_at')

    # Group accommodations by type
    accommodations_by_type = {}
    for accommodation in accommodations:
        acc_type = accommodation.get_accommodation_type_display()
        if acc_type not in accommodations_by_type:
            accommodations_by_type[acc_type] = []
        accommodations_by_type[acc_type].append(accommodation)

    context = {
        'destination': destination,
        'experiences': experiences,
        'experiences_by_type': experiences_by_type,
        'total_experiences': experiences.count(),
        'accommodations': accommodations,
        'accommodations_by_type': accommodations_by_type,
        'total_accommodations': accommodations.count(),
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
                'reasons': ['Manually bookmarked'],
                'bookmarked': True,
                'viewed': True  # Mark as viewed when bookmarked
            }
        )

        if not created:
            # Toggle bookmark status
            recommendation.bookmarked = not recommendation.bookmarked
            if recommendation.bookmarked:
                recommendation.viewed = True  # Mark as viewed when bookmarked

        recommendation.save()

        # Return comprehensive response
        return JsonResponse({
            'success': True,
            'bookmarked': recommendation.bookmarked,
            'message': 'Added to bookmarks' if recommendation.bookmarked else 'Removed from bookmarks'
        })

    except Experience.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Experience not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def get_user_bookmarks(user):
    """Helper function to get user's bookmarked experience IDs"""
    if user.is_authenticated:
        return set(UserRecommendation.objects.filter(
            user=user,
            bookmarked=True
        ).values_list('experience_id', flat=True))
    return set()

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
            destination = form.save()
            messages.success(request, f'Destination "{destination.name}" has been created successfully!')
            return redirect('experiences:destination_list')
    else:
        form = DestinationForm()
    return render(request, 'experiences/add_destination.html', {'form': form})

@user_passes_test(lambda u: u.is_staff)
def edit_destination(request, slug):
    destination = get_object_or_404(Destination, slug=slug)
    if request.method == "POST":
        form = DestinationForm(request.POST, request.FILES, instance=destination)
        if form.is_valid():
            destination = form.save()
            messages.success(request, f'Destination "{destination.name}" has been updated successfully!')
            return redirect('experiences:destination_detail', slug=destination.slug)
    else:
        form = DestinationForm(instance=destination)
    return render(request, 'experiences/edit_destination.html', {
        'form': form,
        'destination': destination
    })

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
    """Remove bookmark via AJAX - used on bookmarks page"""
    try:
        recommendation = UserRecommendation.objects.get(
            user=request.user,
            experience_id=experience_id,
            bookmarked=True
        )
        recommendation.bookmarked = False
        recommendation.save()
        return JsonResponse({
            'success': True,
            'message': 'Removed from bookmarks'
        })
    except UserRecommendation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Bookmark not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

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

@user_passes_test(lambda u: u.is_staff)
def delete_experience(request, slug):
    """Delete an experience"""
    experience = get_object_or_404(Experience, slug=slug)

    if request.method == "POST":
        experience_title = experience.title
        experience.delete()
        messages.success(request, f'✅ Experience "{experience_title}" has been deleted.')
        return redirect('experiences:experience_list')

    return render(request, 'experiences/delete_experience.html', {
        'experience': experience
    })

# Experience Type Management Views

@user_passes_test(lambda u: u.is_staff)
def experience_type_list_view(request):
    """View all experience types with edit/delete options"""
    experience_types = ExperienceType.objects.all().order_by('name')

    # Add count of experiences for each type
    for exp_type in experience_types:
        exp_type.experience_count = Experience.objects.filter(experience_type=exp_type).count()

    paginator = Paginator(experience_types, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'experience_types': page_obj,
        'total_count': experience_types.count(),
    }

    return render(request, 'experiences/experience_type_list.html', context)

@user_passes_test(lambda u: u.is_staff)
def edit_experience_type(request, slug):
    """Edit an existing experience type"""
    experience_type = get_object_or_404(ExperienceType, slug=slug)

    if request.method == 'POST':
        form = ExperienceTypeForm(request.POST, instance=experience_type)
        if form.is_valid():
            try:
                exp_type = form.save(commit=False)

                # Auto-generate slug if changed
                if not exp_type.slug or exp_type.slug != slug:
                    base_slug = slugify(exp_type.name)
                    new_slug = base_slug
                    counter = 1

                    while ExperienceType.objects.filter(slug=new_slug).exclude(id=exp_type.id).exists():
                        new_slug = f"{base_slug}-{counter}"
                        counter += 1

                    exp_type.slug = new_slug

                exp_type.save()
                messages.success(request, f'✅ Experience type "{exp_type.name}" updated successfully!')
                return redirect('experiences:experience_type_list')

            except Exception as e:
                messages.error(request, f'❌ Error updating experience type: {str(e)}')
        else:
            messages.error(request, '⚠️ Please correct the errors below.')
    else:
        form = ExperienceTypeForm(instance=experience_type)

    # Get count of experiences using this type
    experience_count = Experience.objects.filter(experience_type=experience_type).count()

    context = {
        'form': form,
        'experience_type': experience_type,
        'experience_count': experience_count,
        'page_title': f'Edit Experience Type - {experience_type.name}',
    }

    return render(request, 'experiences/edit_experience_type.html', context)

@user_passes_test(lambda u: u.is_staff)
def delete_experience_type(request, slug):
    """Delete an experience type"""
    experience_type = get_object_or_404(ExperienceType, slug=slug)

    # Check if any experiences are using this type
    experience_count = Experience.objects.filter(experience_type=experience_type).count()

    if request.method == 'POST':
        if experience_count > 0:
            messages.error(request, f'❌ Cannot delete "{experience_type.name}" because it is used by {experience_count} experience(s). Please reassign or delete those experiences first.')
        else:
            type_name = experience_type.name
            experience_type.delete()
            messages.success(request, f'✅ Experience type "{type_name}" deleted successfully!')

        return redirect('experiences:experience_type_list')

    context = {
        'experience_type': experience_type,
        'experience_count': experience_count,
        'can_delete': experience_count == 0,
    }

    return render(request, 'experiences/delete_experience_type.html', context)

# Category Management Views

@user_passes_test(lambda u: u.is_staff)
def category_list_view(request):
    """View all categories with edit/delete options"""
    categories = Category.objects.all().order_by('name')

    # Add count of experiences for each category
    for category in categories:
        category.experience_count = category.experiences.count()

    paginator = Paginator(categories, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'categories': page_obj,
        'total_count': categories.count(),
    }

    return render(request, 'experiences/category_list.html', context)

@user_passes_test(lambda u: u.is_staff)
def edit_category(request, slug):
    """Edit an existing category"""
    category = get_object_or_404(Category, slug=slug)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            try:
                cat = form.save(commit=False)

                # Auto-generate slug if changed
                if not cat.slug or cat.slug != slug:
                    base_slug = slugify(cat.name)
                    new_slug = base_slug
                    counter = 1

                    while Category.objects.filter(slug=new_slug).exclude(id=cat.id).exists():
                        new_slug = f"{base_slug}-{counter}"
                        counter += 1

                    cat.slug = new_slug

                cat.save()
                messages.success(request, f'✅ Category "{cat.name}" updated successfully!')
                return redirect('experiences:category_list')

            except Exception as e:
                messages.error(request, f'❌ Error updating category: {str(e)}')
        else:
            messages.error(request, '⚠️ Please correct the errors below.')
    else:
        form = CategoryForm(instance=category)

    # Get count of experiences using this category
    experience_count = category.experiences.count()

    context = {
        'form': form,
        'category': category,
        'experience_count': experience_count,
        'page_title': f'Edit Category - {category.name}',
    }

    return render(request, 'experiences/edit_category.html', context)

@user_passes_test(lambda u: u.is_staff)
def delete_category(request, slug):
    """Delete a category"""
    category = get_object_or_404(Category, slug=slug)

    # Check if any experiences are using this category
    experience_count = category.experiences.count()

    if request.method == 'POST':
        if experience_count > 0:
            messages.error(request, f'❌ Cannot delete "{category.name}" because it is used by {experience_count} experience(s). Please reassign or delete those experiences first.')
        else:
            category_name = category.name
            category.delete()
            messages.success(request, f'✅ Category "{category_name}" deleted successfully!')

        return redirect('experiences:category_list')

    context = {
        'category': category,
        'experience_count': experience_count,
        'can_delete': experience_count == 0,
    }

    return render(request, 'experiences/delete_category.html', context)

# Export Views
@user_passes_test(lambda u: u.is_staff)
def export_experience_types_csv(request):
    """Export experience types to CSV"""
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="experience_types_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Slug', 'Description', 'Experience Count', 'Created At'])

    experience_types = ExperienceType.objects.all().order_by('name')
    for exp_type in experience_types:
        experience_count = Experience.objects.filter(experience_type=exp_type).count()
        writer.writerow([
            exp_type.name,
            exp_type.slug,
            exp_type.description,
            experience_count,
            exp_type.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    return response

@user_passes_test(lambda u: u.is_staff)
def export_categories_csv(request):
    """Export categories to CSV"""
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="categories_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Slug', 'Description', 'Icon', 'Color', 'Experience Count', 'Created At'])

    categories = Category.objects.all().order_by('name')
    for category in categories:
        experience_count = category.experiences.count()
        writer.writerow([
            category.name,
            category.slug,
            category.description,
            category.icon,
            category.color,
            experience_count,
            category.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    return response

def sitemap_view(request):
    """Generate comprehensive XML sitemap for search engines with all experiences"""
    from django.http import HttpResponse
    from django.utils import timezone
    from xml.sax.saxutils import escape

    def xml_escape(text):
        """Escape special XML characters"""
        if not text:
            return ''
        return escape(str(text), {'"': '&quot;', "'": '&apos;'})

    def get_full_url(url_or_path):
        """Get full URL, handling both absolute URLs and relative paths"""
        if not url_or_path:
            return ''
        url_str = str(url_or_path)
        # If already an absolute URL, return as-is (with XML escaping)
        if url_str.startswith('http://') or url_str.startswith('https://'):
            return xml_escape(url_str)
        # Otherwise prepend base_url for relative paths
        return xml_escape(f'{base_url}{url_str}')

    # Get the current site domain dynamically
    current_site = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    base_url = f'{protocol}://{current_site}'

    # Get all active experiences, destinations, and published blogs
    experiences = Experience.objects.filter(is_active=True).select_related('destination').order_by('-updated_at')
    destinations = Destination.objects.all().order_by('-updated_at')
    categories = Category.objects.all().order_by('name')
    blogs = TravelBlog.objects.filter(is_published=True).select_related('author', 'destination').order_by('-published_at')
    accommodations = Accommodation.objects.filter(is_active=True).select_related('destination').order_by('-updated_at')

    # Build sitemap XML with better SEO attributes
    sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap_xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">')

    # Add homepage
    sitemap_xml.append('<url>')
    sitemap_xml.append(f'<loc>{base_url}/</loc>')
    sitemap_xml.append('<changefreq>daily</changefreq>')
    sitemap_xml.append('<priority>1.0</priority>')
    sitemap_xml.append(f'<lastmod>{timezone.now().strftime("%Y-%m-%d")}</lastmod>')
    sitemap_xml.append('</url>')

    # Add experience list page
    sitemap_xml.append('<url>')
    sitemap_xml.append(f'<loc>{base_url}/experiences/</loc>')
    sitemap_xml.append('<changefreq>daily</changefreq>')
    sitemap_xml.append('<priority>0.9</priority>')
    sitemap_xml.append(f'<lastmod>{timezone.now().strftime("%Y-%m-%d")}</lastmod>')
    sitemap_xml.append('</url>')

    # Add destination list page
    sitemap_xml.append('<url>')
    sitemap_xml.append(f'<loc>{base_url}/experiences/destinations/</loc>')
    sitemap_xml.append('<changefreq>weekly</changefreq>')
    sitemap_xml.append('<priority>0.8</priority>')
    sitemap_xml.append('</url>')

    # Add individual experiences with enhanced SEO
    for experience in experiences:
        sitemap_xml.append('<url>')
        sitemap_xml.append(f'<loc>{base_url}/experiences/experience/{experience.slug}/</loc>')
        sitemap_xml.append('<changefreq>weekly</changefreq>')
        # Higher priority for featured experiences
        priority = '0.95' if experience.is_featured else '0.9'
        sitemap_xml.append(f'<priority>{priority}</priority>')
        if experience.updated_at:
            sitemap_xml.append(f'<lastmod>{experience.updated_at.strftime("%Y-%m-%d")}</lastmod>')

        # Add image information for better SEO
        if experience.main_image:
            sitemap_xml.append('<image:image>')
            sitemap_xml.append(f'<image:loc>{get_full_url(experience.main_image.url)}</image:loc>')
            sitemap_xml.append(f'<image:title>{xml_escape(experience.title)}</image:title>')
            caption = experience.short_description[:160] if experience.short_description else experience.title
            sitemap_xml.append(f'<image:caption>{xml_escape(caption)}</image:caption>')
            sitemap_xml.append('</image:image>')

        sitemap_xml.append('</url>')

    # Add individual destinations
    for destination in destinations:
        sitemap_xml.append('<url>')
        sitemap_xml.append(f'<loc>{base_url}/experiences/destinations/{destination.slug}/</loc>')
        sitemap_xml.append('<changefreq>weekly</changefreq>')
        sitemap_xml.append('<priority>0.8</priority>')
        if destination.updated_at:
            sitemap_xml.append(f'<lastmod>{destination.updated_at.strftime("%Y-%m-%d")}</lastmod>')

        # Add destination image if available
        if destination.image:
            sitemap_xml.append('<image:image>')
            sitemap_xml.append(f'<image:loc>{get_full_url(destination.image.url)}</image:loc>')
            sitemap_xml.append(f'<image:title>{xml_escape(destination.name)}, {xml_escape(destination.country)}</image:title>')
            sitemap_xml.append(f'<image:caption>Sustainable travel destination: {xml_escape(destination.name)}</image:caption>')
            sitemap_xml.append('</image:image>')

        sitemap_xml.append('</url>')

    # Add category pages
    for category in categories:
        sitemap_xml.append('<url>')
        sitemap_xml.append(f'<loc>{base_url}/experiences/category/{category.slug}/</loc>')
        sitemap_xml.append('<changefreq>weekly</changefreq>')
        sitemap_xml.append('<priority>0.7</priority>')
        if hasattr(category, 'created_at') and category.created_at:
            sitemap_xml.append(f'<lastmod>{category.created_at.strftime("%Y-%m-%d")}</lastmod>')
        sitemap_xml.append('</url>')

    # Add accommodations list page
    sitemap_xml.append('<url>')
    sitemap_xml.append(f'<loc>{base_url}/experiences/accommodations/</loc>')
    sitemap_xml.append('<changefreq>daily</changefreq>')
    sitemap_xml.append('<priority>0.9</priority>')
    sitemap_xml.append(f'<lastmod>{timezone.now().strftime("%Y-%m-%d")}</lastmod>')
    sitemap_xml.append('</url>')

    # Add individual accommodations
    for accommodation in accommodations:
        sitemap_xml.append('<url>')
        sitemap_xml.append(f'<loc>{base_url}/experiences/accommodation/{accommodation.slug}/</loc>')
        sitemap_xml.append('<changefreq>weekly</changefreq>')
        priority = '0.95' if accommodation.is_featured else '0.9'
        sitemap_xml.append(f'<priority>{priority}</priority>')
        if accommodation.updated_at:
            sitemap_xml.append(f'<lastmod>{accommodation.updated_at.strftime("%Y-%m-%d")}</lastmod>')

        # Add accommodation image if available
        if accommodation.main_image:
            sitemap_xml.append('<image:image>')
            sitemap_xml.append(f'<image:loc>{get_full_url(accommodation.main_image.url)}</image:loc>')
            sitemap_xml.append(f'<image:title>{xml_escape(accommodation.name)}</image:title>')
            acc_caption = accommodation.short_description[:160] if accommodation.short_description else accommodation.name
            sitemap_xml.append(f'<image:caption>{xml_escape(acc_caption)}</image:caption>')
            sitemap_xml.append('</image:image>')

        sitemap_xml.append('</url>')

    # Add blog feed page
    sitemap_xml.append('<url>')
    sitemap_xml.append(f'<loc>{base_url}/experiences/blogs/</loc>')
    sitemap_xml.append('<changefreq>daily</changefreq>')
    sitemap_xml.append('<priority>0.9</priority>')
    sitemap_xml.append(f'<lastmod>{timezone.now().strftime("%Y-%m-%d")}</lastmod>')
    sitemap_xml.append('</url>')

    # Add individual blog posts - HIGH PRIORITY FOR SEO
    for blog in blogs:
        sitemap_xml.append('<url>')
        sitemap_xml.append(f'<loc>{base_url}/experiences/blog/{blog.slug}/</loc>')
        sitemap_xml.append('<changefreq>monthly</changefreq>')
        # Blog posts get high priority for SEO value
        priority = '0.95' if blog.is_featured else '0.85'
        sitemap_xml.append(f'<priority>{priority}</priority>')
        if blog.published_at:
            sitemap_xml.append(f'<lastmod>{blog.published_at.strftime("%Y-%m-%d")}</lastmod>')
        elif blog.updated_at:
            sitemap_xml.append(f'<lastmod>{blog.updated_at.strftime("%Y-%m-%d")}</lastmod>')

        # Add blog featured image if available
        if blog.featured_image:
            sitemap_xml.append('<image:image>')
            sitemap_xml.append(f'<image:loc>{get_full_url(blog.featured_image.url)}</image:loc>')
            sitemap_xml.append(f'<image:title>{xml_escape(blog.title)}</image:title>')
            blog_caption = blog.excerpt[:160] if blog.excerpt else blog.title
            sitemap_xml.append(f'<image:caption>{xml_escape(blog_caption)}</image:caption>')
            sitemap_xml.append('</image:image>')

        sitemap_xml.append('</url>')

    sitemap_xml.append('</urlset>')

    return HttpResponse('\n'.join(sitemap_xml), content_type='application/xml')


@csrf_exempt
@require_POST
def analyze_seo_ajax(request):
    """
    AJAX endpoint for real-time SEO analysis
    Returns comprehensive SEO score and recommendations
    """
    try:
        data = json.loads(request.body)

        # Extract form data
        experience_data = {
            'title': data.get('title', ''),
            'meta_title': data.get('meta_title', ''),
            'meta_description': data.get('meta_description', ''),
            'description': data.get('description', ''),
            'short_description': data.get('short_description', ''),
            'destination': data.get('destination', ''),
            'experience_type': data.get('experience_type', '')
        }

        # Import and use the SEO analyzer
        from .seo_analyzer import get_seo_analysis_for_experience
        analysis = get_seo_analysis_for_experience(experience_data)

        return JsonResponse({
            'success': True,
            'analysis': analysis
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Analysis failed: {str(e)}'
        })

# ============= ACCOMMODATIONS VIEWS =============

def accommodation_list_view(request):
    """Browse all accommodations with filtering"""
    accommodations = Accommodation.objects.filter(is_active=True).select_related(
        'destination', 'provider'
    )

    # Filtering
    destination_slug = request.GET.get('destination')
    accommodation_type = request.GET.get('type')
    budget_range = request.GET.get('budget')
    search_query = request.GET.get('search')

    if destination_slug:
        accommodations = accommodations.filter(destination__slug=destination_slug)
    if accommodation_type:
        accommodations = accommodations.filter(accommodation_type=accommodation_type)
    if budget_range:
        accommodations = accommodations.filter(budget_range=budget_range)
    if search_query:
        accommodations = accommodations.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(destination__name__icontains=search_query)
        )

    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_low':
        accommodations = accommodations.order_by('price_per_night_from')
    elif sort_by == 'price_high':
        accommodations = accommodations.order_by('-price_per_night_from')
    elif sort_by == 'sustainability':
        accommodations = accommodations.order_by('-sustainability_score')
    elif sort_by == 'hygge':
        accommodations = accommodations.order_by('-hygge_factor')
    else:
        accommodations = accommodations.order_by('-created_at')

    # Pagination
    paginator = Paginator(accommodations, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'accommodations': page_obj,
        'destinations': Destination.objects.all(),
        'accommodation_types': Accommodation.ACCOMMODATION_TYPES,
        'budget_ranges': Accommodation.BUDGET_RANGES,
        'active_filters': {
            'destination': destination_slug or '',
            'type': accommodation_type or '',
            'budget': budget_range or '',
            'search': search_query or '',
            'sort': sort_by or 'newest',
        }
    }

    return render(request, 'experiences/accommodation_list.html', context)

def accommodation_detail_view(request, slug):
    """Detailed view of an accommodation"""
    accommodation = get_object_or_404(
        Accommodation.objects.select_related('destination', 'provider'),
        slug=slug,
        is_active=True
    )

    # Get similar accommodations
    similar_accommodations = Accommodation.objects.filter(
        is_active=True,
        destination=accommodation.destination
    ).exclude(id=accommodation.id)[:4]

    context = {
        'accommodation': accommodation,
        'similar_accommodations': similar_accommodations,
    }

    return render(request, 'experiences/accommodation_detail.html', context)

@user_passes_test(lambda u: u.is_staff)
def add_accommodation(request):
    """Add a new accommodation"""
    if request.method == "POST":
        form = AccommodationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                accommodation = form.save(commit=False)

                # Auto-generate slug if not provided
                if not accommodation.slug:
                    base_slug = slugify(accommodation.name)
                    slug = base_slug
                    counter = 1

                    # Ensure slug is unique
                    while Accommodation.objects.filter(slug=slug).exists():
                        slug = f"{base_slug}-{counter}"
                        counter += 1

                    accommodation.slug = slug

                # Handle amenities JSON
                amenities_str = request.POST.get('amenities', '[]')
                try:
                    accommodation.amenities = json.loads(amenities_str)
                except json.JSONDecodeError:
                    # If not valid JSON, convert comma-separated to list
                    accommodation.amenities = [a.strip() for a in amenities_str.split(',') if a.strip()]

                accommodation.save()

                messages.success(request, f'✅ Accommodation "{accommodation.name}" created successfully!')
                return redirect('experiences:accommodation_list')

            except Exception as e:
                messages.error(request, f'❌ Error creating accommodation: {str(e)}')
                print(f"Error details: {e}")
        else:
            messages.error(request, '⚠️ Please correct the errors below.')
            print(f"Form errors: {form.errors}")
    else:
        form = AccommodationForm()

    # Fetch data for dropdowns
    destinations = Destination.objects.all()
    providers = Provider.objects.all()

    return render(request, 'experiences/add_accommodation.html', {
        'form': form,
        'page_title': 'Add New Accommodation',
        'destinations': destinations,
        'providers': providers,
    })

@user_passes_test(lambda u: u.is_staff)
def edit_accommodation(request, slug):
    """Edit an existing accommodation"""
    accommodation = get_object_or_404(Accommodation, slug=slug)

    if request.method == "POST":
        form = AccommodationForm(request.POST, request.FILES, instance=accommodation)
        if form.is_valid():
            try:
                accommodation = form.save(commit=False)

                # Handle amenities JSON
                amenities_str = request.POST.get('amenities', '[]')
                try:
                    accommodation.amenities = json.loads(amenities_str)
                except json.JSONDecodeError:
                    # If not valid JSON, convert comma-separated to list
                    accommodation.amenities = [a.strip() for a in amenities_str.split(',') if a.strip()]

                accommodation.save()

                messages.success(request, f'✅ Accommodation "{accommodation.name}" updated successfully!')
                return redirect('experiences:accommodation_detail', slug=accommodation.slug)

            except Exception as e:
                messages.error(request, f'❌ Error updating accommodation: {str(e)}')
                print(f"Error details: {e}")
        else:
            messages.error(request, '⚠️ Please correct the errors below.')
            print(f"Form errors: {form.errors}")
    else:
        # Pre-populate amenities as JSON string for the form
        initial_data = {
            'amenities': json.dumps(accommodation.amenities) if accommodation.amenities else '[]'
        }
        form = AccommodationForm(instance=accommodation, initial=initial_data)

    destinations = Destination.objects.all()
    providers = Provider.objects.all()

    return render(request, 'experiences/edit_accommodation.html', {
        'form': form,
        'accommodation': accommodation,
        'page_title': f'Edit {accommodation.name}',
        'destinations': destinations,
        'providers': providers,
    })

@user_passes_test(lambda u: u.is_staff)
def delete_accommodation(request, slug):
    """Delete an accommodation"""
    accommodation = get_object_or_404(Accommodation, slug=slug)

    if request.method == "POST":
        accommodation_name = accommodation.name
        accommodation.delete()
        messages.success(request, f'✅ Accommodation "{accommodation_name}" has been deleted.')
        return redirect('experiences:accommodation_list')

    return render(request, 'experiences/delete_accommodation.html', {
        'accommodation': accommodation
    })

# ============= TRAVEL BLOG VIEWS =============

def blog_feed(request):
    """Public feed of all published travel blogs"""
    blogs = TravelBlog.objects.filter(is_published=True).select_related(
        'author', 'destination', 'experience', 'accommodation'
    ).order_by('-published_at')

    # Filtering
    tag = request.GET.get('tag')
    destination_slug = request.GET.get('destination')
    author_username = request.GET.get('author')

    if destination_slug:
        blogs = blogs.filter(destination__slug=destination_slug)
    if author_username:
        blogs = blogs.filter(author__username=author_username)

    # Tag filtering - handle SQLite compatibility
    if tag:
        # Filter in Python to support SQLite (which doesn't support JSONField contains)
        tag_lower = tag.lower()
        filtered_blogs = []
        for blog in blogs:
            if blog.tags and any(tag_lower == t.lower() for t in blog.tags):
                filtered_blogs.append(blog.id)
        blogs = blogs.filter(id__in=filtered_blogs)

    # Pagination
    paginator = Paginator(blogs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'blogs': page_obj,
        'destinations': Destination.objects.all(),
    }

    return render(request, 'experiences/blog_feed.html', context)

def blog_detail(request, slug):
    """Detailed view of a blog post with comments"""
    blog = get_object_or_404(
        TravelBlog.objects.select_related('author', 'destination', 'experience', 'accommodation'),
        slug=slug,
        is_published=True
    )

    # Increment view count
    blog.views_count += 1
    blog.save(update_fields=['views_count'])

    # Get comments
    comments = blog.comments.select_related('author').all()

    # Check if user liked this blog
    user_liked = False
    if request.user.is_authenticated:
        user_liked = blog.liked_by.filter(id=request.user.id).exists()

    # Handle comment submission
    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = BlogCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.blog_post = blog
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment added successfully!')
            return redirect('experiences:blog_detail', slug=slug)
    else:
        comment_form = BlogCommentForm()

    # Get related blogs
    related_blogs = TravelBlog.objects.filter(
        is_published=True
    ).exclude(id=blog.id)

    if blog.destination:
        related_blogs = related_blogs.filter(destination=blog.destination)[:3]
    else:
        related_blogs = related_blogs[:3]

    context = {
        'blog': blog,
        'comments': comments,
        'comment_form': comment_form,
        'user_liked': user_liked,
        'related_blogs': related_blogs,
    }

    return render(request, 'experiences/blog_detail.html', context)

@login_required
def my_blogs(request):
    """View user's own blogs (published and drafts)"""
    blogs = request.user.travel_blogs.all().order_by('-created_at')

    context = {
        'blogs': blogs,
    }

    return render(request, 'experiences/my_blogs.html', context)

@login_required
def create_blog(request):
    """Create a new travel blog post"""
    if request.method == 'POST':
        form = TravelBlogForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                blog = form.save(commit=False)
                blog.author = request.user

                # Sanitize HTML content
                blog.content = sanitize_html(blog.content)

                # Auto-generate slug
                if not blog.slug:
                    base_slug = slugify(blog.title)
                    slug = base_slug
                    counter = 1

                    while TravelBlog.objects.filter(slug=slug).exists():
                        slug = f"{base_slug}-{counter}"
                        counter += 1

                    blog.slug = slug

                blog.save()

                if blog.is_published:
                    messages.success(request, f'✅ Blog post "{blog.title}" published successfully!')
                else:
                    messages.success(request, f'✅ Blog post "{blog.title}" saved as draft!')

                return redirect('experiences:blog_detail', slug=blog.slug) if blog.is_published else redirect('experiences:my_blogs')

            except Exception as e:
                messages.error(request, f'❌ Error creating blog post: {str(e)}')
        else:
            messages.error(request, '⚠️ Please correct the errors below.')
    else:
        form = TravelBlogForm()

    destinations = Destination.objects.all()
    experiences = Experience.objects.filter(is_active=True)
    accommodations = Accommodation.objects.filter(is_active=True)

    return render(request, 'experiences/create_blog.html', {
        'form': form,
        'destinations': destinations,
        'experiences': experiences,
        'accommodations': accommodations,
    })

@login_required
def edit_blog(request, slug):
    """Edit an existing blog post"""
    blog = get_object_or_404(TravelBlog, slug=slug, author=request.user)

    if request.method == 'POST':
        form = TravelBlogForm(request.POST, request.FILES, instance=blog)
        if form.is_valid():
            try:
                blog = form.save(commit=False)

                # Sanitize HTML content
                blog.content = sanitize_html(blog.content)

                blog.save()

                messages.success(request, f'✅ Blog post "{blog.title}" updated successfully!')
                return redirect('experiences:blog_detail', slug=blog.slug) if blog.is_published else redirect('experiences:my_blogs')

            except Exception as e:
                messages.error(request, f'❌ Error updating blog post: {str(e)}')
        else:
            messages.error(request, '⚠️ Please correct the errors below.')
    else:
        form = TravelBlogForm(instance=blog)

    destinations = Destination.objects.all()
    experiences = Experience.objects.filter(is_active=True)
    accommodations = Accommodation.objects.filter(is_active=True)

    return render(request, 'experiences/edit_blog.html', {
        'form': form,
        'blog': blog,
        'destinations': destinations,
        'experiences': experiences,
        'accommodations': accommodations,
    })

@login_required
def delete_blog(request, slug):
    """Delete a blog post"""
    blog = get_object_or_404(TravelBlog, slug=slug, author=request.user)

    if request.method == 'POST':
        blog_title = blog.title
        blog.delete()
        messages.success(request, f'✅ Blog post "{blog_title}" has been deleted.')
        return redirect('experiences:my_blogs')

    return render(request, 'experiences/delete_blog.html', {
        'blog': blog
    })

def blogger_terms(request):
    """Display blogger terms and conditions"""
    from datetime import datetime
    return render(request, 'experiences/blogger_terms.html', {
        'current_date': datetime.now().strftime('%B %Y')
    })

@login_required
@require_POST
def like_blog(request, slug):
    """Toggle like on a blog post"""
    blog = get_object_or_404(TravelBlog, slug=slug, is_published=True)

    if request.user in blog.liked_by.all():
        blog.liked_by.remove(request.user)
        blog.likes_count = max(0, blog.likes_count - 1)
        liked = False
    else:
        blog.liked_by.add(request.user)
        blog.likes_count += 1
        liked = True

    blog.save(update_fields=['likes_count'])

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'likes_count': blog.likes_count})

    return redirect('experiences:blog_detail', slug=slug)
