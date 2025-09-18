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

    # Pagination
    paginator = Paginator(experiences, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get filter options
    categories = Category.objects.all().order_by('name')
    destinations = Destination.objects.annotate(
        experience_count=Count('experiences', filter=Q(experiences__is_active=True))
    ).filter(experience_count__gt=0).order_by('name')
    experience_types = ExperienceType.objects.all().order_by('name')

    # Get user bookmarks for template
    user_bookmarks = get_user_bookmarks(request.user)

    context = {
        'experiences': page_obj,
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

def sitemap_view(request):
    """Generate XML sitemap for search engines"""
    from django.http import HttpResponse
    from django.utils import timezone

    # Get all active experiences and destinations
    experiences = Experience.objects.filter(is_active=True).select_related('destination')
    destinations = Destination.objects.all()
    categories = Category.objects.all()

    # Build sitemap XML
    sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap_xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    # Add homepage
    sitemap_xml.append('<url>')
    sitemap_xml.append('<loc>https://yourdomain.com/</loc>')
    sitemap_xml.append('<changefreq>daily</changefreq>')
    sitemap_xml.append('<priority>1.0</priority>')
    sitemap_xml.append('</url>')

    # Add experience list
    sitemap_xml.append('<url>')
    sitemap_xml.append('<loc>https://yourdomain.com/experiences/</loc>')
    sitemap_xml.append('<changefreq>daily</changefreq>')
    sitemap_xml.append('<priority>0.8</priority>')
    sitemap_xml.append('</url>')

    # Add destination list
    sitemap_xml.append('<url>')
    sitemap_xml.append('<loc>https://yourdomain.com/experiences/destinations/</loc>')
    sitemap_xml.append('<changefreq>weekly</changefreq>')
    sitemap_xml.append('<priority>0.8</priority>')
    sitemap_xml.append('</url>')

    # Add individual experiences
    for experience in experiences:
        sitemap_xml.append('<url>')
        sitemap_xml.append(f'<loc>https://yourdomain.com/experiences/experience/{experience.slug}/</loc>')
        sitemap_xml.append('<changefreq>weekly</changefreq>')
        sitemap_xml.append('<priority>0.9</priority>')
        if experience.updated_at:
            sitemap_xml.append(f'<lastmod>{experience.updated_at.strftime("%Y-%m-%d")}</lastmod>')
        sitemap_xml.append('</url>')

    # Add individual destinations
    for destination in destinations:
        sitemap_xml.append('<url>')
        sitemap_xml.append(f'<loc>https://yourdomain.com/experiences/destinations/{destination.slug}/</loc>')
        sitemap_xml.append('<changefreq>weekly</changefreq>')
        sitemap_xml.append('<priority>0.7</priority>')
        if destination.updated_at:
            sitemap_xml.append(f'<lastmod>{destination.updated_at.strftime("%Y-%m-%d")}</lastmod>')
        sitemap_xml.append('</url>')

    # Add categories
    for category in categories:
        sitemap_xml.append('<url>')
        sitemap_xml.append(f'<loc>https://yourdomain.com/experiences/category/{category.slug}/</loc>')
        sitemap_xml.append('<changefreq>weekly</changefreq>')
        sitemap_xml.append('<priority>0.6</priority>')
        sitemap_xml.append('</url>')

    sitemap_xml.append('</urlset>')

    return HttpResponse('\n'.join(sitemap_xml), content_type='application/xml')

