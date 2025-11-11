# experiences/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Category, Destination, Provider, Experience,
    UserRecommendation, ExperienceReview, BookingTracking, Accommodation, TravelBlog, BlogComment, Restaurant,
    RestaurantRating, RestaurantComment
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin for experience categories"""
    list_display = ('name', 'icon_display', 'experience_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Display', {
            'fields': ('icon', 'color')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def icon_display(self, obj):
        return format_html(
            '<i class="{}" style="color: {}; font-size: 1.2em;"></i>',
            obj.icon,
            obj.color
        )
    icon_display.short_description = 'Icon'
    
    def experience_count(self, obj):
        count = obj.experiences.count()
        if count > 0:
            url = reverse('admin:experiences_experience_changelist') + f'?categories__id__exact={obj.id}'
            return format_html('<a href="{}">{} experiences</a>', url, count)
        return '0 experiences'
    experience_count.short_description = 'Experiences'

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    """Admin for destinations"""
    list_display = ('name', 'country', 'region', 'sustainability_score', 'hygge_factor', 'experience_count')
    list_filter = ('country', 'sustainability_score', 'hygge_factor', 'created_at')
    search_fields = ('name', 'country', 'region', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'country', 'region', 'description')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Travel Info', {
            'fields': ('climate', 'best_time_to_visit')
        }),
        ('Ratings', {
            'fields': ('sustainability_score', 'hygge_factor')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def experience_count(self, obj):
        count = obj.experiences.count()
        if count > 0:
            url = reverse('admin:experiences_experience_changelist') + f'?destination__id__exact={obj.id}'
            return format_html('<a href="{}">{} experiences</a>', url, count)
        return '0 experiences'
    experience_count.short_description = 'Experiences'

@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    """Admin for providers"""
    list_display = ('name', 'verified_status', 'website_link', 'experience_count', 'created_at')
    list_filter = ('verified', 'created_at')
    search_fields = ('name', 'description', 'website')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Contact Information', {
            'fields': ('website', 'contact_email', 'phone')
        }),
        ('Sustainability', {
            'fields': ('sustainability_certifications', 'verified')
        }),
        ('Media', {
            'fields': ('logo',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def verified_status(self, obj):
        if obj.verified:
            return format_html('<span style="color: green;">✓ Verified</span>')
        else:
            return format_html('<span style="color: orange;">⚠ Unverified</span>')
    verified_status.short_description = 'Status'
    
    def website_link(self, obj):
        if obj.website:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.website, obj.website[:50])
        return '-'
    website_link.short_description = 'Website'
    
    def experience_count(self, obj):
        count = obj.experiences.count()
        if count > 0:
            url = reverse('admin:experiences_experience_changelist') + f'?provider__id__exact={obj.id}'
            return format_html('<a href="{}">{} experiences</a>', url, count)
        return '0 experiences'
    experience_count.short_description = 'Experiences'

@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    """Admin for experiences"""
    list_display = (
        'title', 'destination', 'provider', 'experience_type', 
        'sustainability_badge', 'hygge_factor', 'price_display', 
        'is_featured', 'is_active', 'created_at'
    )
    list_filter = (
        'experience_type', 'budget_range', 'sustainability_score', 
        'hygge_factor', 'is_featured', 'is_active', 'carbon_neutral',
        'supports_local_community', 'created_at', 'destination__country'
    )
    search_fields = ('title', 'description', 'destination__name', 'provider__name')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('id', 'created_at', 'updated_at', 'recommendation_count', 'review_stats')
    filter_horizontal = ('categories',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'short_description', 'description')
        }),
        ('Relationships', {
            'fields': ('destination', 'provider', 'categories')
        }),
        ('Experience Details', {
            'fields': ('experience_type', 'budget_range', 'group_size', 'duration')
        }),
        ('Pricing', {
            'fields': ('price_from', 'price_to', 'currency')
        }),
        ('Sustainability & Hygge', {
            'fields': ('sustainability_score', 'hygge_factor', 'carbon_neutral', 'supports_local_community')
        }),
        ('Travel Style Matching', {
            'fields': ('travel_styles', 'accommodation_types', 'transport_types', 'sustainability_factors'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('main_image', 'gallery_images')
        }),
        ('Affiliate & Booking', {
            'fields': ('affiliate_link', 'booking_link', 'commission_rate')
        }),
        ('Features & Requirements', {
            'fields': ('included_features', 'requirements', 'what_to_bring'),
            'classes': ('collapse',)
        }),
        ('SEO & Meta', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Status & Admin', {
            'fields': ('is_featured', 'is_active', 'admin_notes')
        }),
        ('Metadata', {
            'fields': ('id', 'recommendation_count', 'review_stats', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def sustainability_badge(self, obj):
        badge = obj.get_sustainability_badge()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em;">{}</span>',
            badge['color'],
            badge['text']
        )
    sustainability_badge.short_description = 'Sustainability'
    
    def price_display(self, obj):
        return obj.get_price_display()
    price_display.short_description = 'Price'
    
    def recommendation_count(self, obj):
        count = obj.userrecommendation_set.count()
        if count > 0:
            url = reverse('admin:experiences_userrecommendation_changelist') + f'?experience__id__exact={obj.id}'
            return format_html('<a href="{}">{} recommendations</a>', url, count)
        return '0 recommendations'
    recommendation_count.short_description = 'Recommendations'
    
    def review_stats(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            avg_rating = sum(r.rating for r in reviews) / len(reviews)
            avg_sustainability = sum(r.sustainability_rating for r in reviews) / len(reviews)
            url = reverse('admin:experiences_experiencereview_changelist') + f'?experience__id__exact={obj.id}'
            return format_html(
                '<a href="{}">{} reviews</a><br>Rating: {:.1f}/5<br>Sustainability: {:.1f}/5',
                url, len(reviews), avg_rating, avg_sustainability
            )
        return 'No reviews'
    review_stats.short_description = 'Reviews'

@admin.register(UserRecommendation)
class UserRecommendationAdmin(admin.ModelAdmin):
    """Admin for user recommendations"""
    list_display = ('user', 'experience_title', 'match_score', 'viewed', 'clicked', 'bookmarked', 'created_at')
    list_filter = ('viewed', 'clicked', 'bookmarked', 'created_at', 'experience__destination__country')
    search_fields = ('user__username', 'experience__title', 'experience__destination__name')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Recommendation', {
            'fields': ('user', 'experience', 'match_score', 'reasons')
        }),
        ('Engagement', {
            'fields': ('viewed', 'clicked', 'bookmarked')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
    
    def experience_title(self, obj):
        return obj.experience.title
    experience_title.short_description = 'Experience'

@admin.register(ExperienceReview)
class ExperienceReviewAdmin(admin.ModelAdmin):
    """Admin for experience reviews"""
    list_display = (
        'user', 'experience_title', 'rating_display', 'sustainability_rating', 
        'hygge_rating', 'would_recommend', 'verified_booking', 'created_at'
    )
    list_filter = (
        'rating', 'sustainability_rating', 'hygge_rating', 'would_recommend', 
        'verified_booking', 'created_at', 'experience__destination__country'
    )
    search_fields = ('user__username', 'experience__title', 'title', 'content')
    readonly_fields = ('created_at', 'updated_at', 'helpful_votes')
    
    fieldsets = (
        ('Review Information', {
            'fields': ('user', 'experience', 'title', 'content')
        }),
        ('Ratings', {
            'fields': ('rating', 'sustainability_rating', 'hygge_rating', 'would_recommend')
        }),
        ('Verification', {
            'fields': ('verified_booking',)
        }),
        ('Engagement', {
            'fields': ('helpful_votes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def experience_title(self, obj):
        return obj.experience.title
    experience_title.short_description = 'Experience'
    
    def rating_display(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: #ffc107;">{}</span>', stars)
    rating_display.short_description = 'Rating'

@admin.register(BookingTracking)
class BookingTrackingAdmin(admin.ModelAdmin):
    """Admin for booking tracking"""
    list_display = (
        'experience_title', 'user_display', 'clicked_at', 'converted', 
        'conversion_date', 'commission_earned'
    )
    list_filter = ('converted', 'clicked_at', 'conversion_date', 'experience__destination__country')
    search_fields = ('user__username', 'experience__title', 'session_id')
    readonly_fields = ('clicked_at', 'ip_address', 'user_agent')
    
    fieldsets = (
        ('Tracking Information', {
            'fields': ('user', 'experience', 'session_id', 'clicked_at')
        }),
        ('Conversion', {
            'fields': ('converted', 'conversion_date', 'commission_earned')
        }),
        ('Technical', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def experience_title(self, obj):
        return obj.experience.title
    experience_title.short_description = 'Experience'
    
    def user_display(self, obj):
        if obj.user:
            return obj.user.username
        return f"Anonymous ({obj.session_id[:8]})"
    user_display.short_description = 'User'

@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    """Admin for accommodations"""
    list_display = (
        'name', 'destination', 'provider', 'accommodation_type',
        'sustainability_badge', 'hygge_factor', 'price_display',
        'is_featured', 'is_active', 'created_at'
    )
    list_filter = (
        'accommodation_type', 'budget_range', 'sustainability_score',
        'hygge_factor', 'is_featured', 'is_active', 'carbon_neutral',
        'eco_certified', 'supports_local_community', 'created_at',
        'destination__country'
    )
    search_fields = ('name', 'description', 'destination__name', 'provider__name', 'address')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('id', 'created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'short_description', 'description')
        }),
        ('Relationships', {
            'fields': ('destination', 'provider')
        }),
        ('Accommodation Details', {
            'fields': ('accommodation_type', 'budget_range', 'total_rooms', 'max_guests')
        }),
        ('Pricing', {
            'fields': ('price_per_night_from', 'price_per_night_to', 'currency')
        }),
        ('Sustainability & Hygge', {
            'fields': ('sustainability_score', 'hygge_factor', 'carbon_neutral', 'supports_local_community', 'eco_certified')
        }),
        ('Location', {
            'fields': ('address', 'latitude', 'longitude')
        }),
        ('Media', {
            'fields': ('main_image', 'gallery_images')
        }),
        ('Booking', {
            'fields': ('booking_link',)
        }),
        ('Amenities & Features', {
            'fields': ('amenities', 'room_types'),
            'classes': ('collapse',)
        }),
        ('Policies', {
            'fields': ('check_in_time', 'check_out_time', 'cancellation_policy'),
            'classes': ('collapse',)
        }),
        ('SEO & Meta', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Status & Admin', {
            'fields': ('is_featured', 'is_active', 'admin_notes')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def sustainability_badge(self, obj):
        badge = obj.get_sustainability_badge()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em;">{}</span>',
            badge['color'],
            badge['text']
        )
    sustainability_badge.short_description = 'Sustainability'

    def price_display(self, obj):
        return obj.get_price_display()
    price_display.short_description = 'Price'

@admin.register(TravelBlog)
class TravelBlogAdmin(admin.ModelAdmin):
    """Admin for travel blog posts"""
    list_display = (
        'title', 'author', 'destination', 'is_published', 'views_count',
        'likes_count', 'comment_count', 'published_at', 'created_at'
    )
    list_filter = ('is_published', 'is_featured', 'created_at', 'published_at', 'destination')
    search_fields = ('title', 'content', 'author__username', 'destination__name')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('id', 'views_count', 'likes_count', 'created_at', 'updated_at')
    filter_horizontal = ('liked_by',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'excerpt', 'content')
        }),
        ('Author & Relationships', {
            'fields': ('author', 'experience', 'accommodation', 'destination')
        }),
        ('Media', {
            'fields': ('featured_image', 'gallery_images')
        }),
        ('Tags & SEO', {
            'fields': ('tags', 'meta_title', 'meta_description')
        }),
        ('Publishing', {
            'fields': ('is_published', 'is_featured', 'published_at')
        }),
        ('Engagement', {
            'fields': ('views_count', 'likes_count', 'liked_by'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def comment_count(self, obj):
        count = obj.comments.count()
        if count > 0:
            return f"{count} comments"
        return "No comments"
    comment_count.short_description = 'Comments'

@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    """Admin for blog comments"""
    list_display = ('author', 'blog_title', 'content_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('author__username', 'blog_post__title', 'content')
    readonly_fields = ('created_at', 'updated_at')

    def blog_title(self, obj):
        return obj.blog_post.title
    blog_title.short_description = 'Blog Post'

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Comment'

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    """Admin for restaurants"""
    list_display = (
        'name', 'destination', 'restaurant_type', 'cuisine_type',
        'average_rating', 'rating_count', 'sustainability_badge', 'hygge_factor', 'price_display',
        'is_featured', 'is_active', 'created_at'
    )
    list_filter = (
        'restaurant_type', 'cuisine_type', 'budget_range', 'sustainability_score',
        'hygge_factor', 'is_featured', 'is_active', 'carbon_neutral',
        'supports_local_community', 'organic_ingredients', 'locally_sourced',
        'created_at', 'destination__country'
    )
    search_fields = ('name', 'description', 'destination__name', 'address', 'cuisine_type')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('id', 'average_rating', 'rating_count', 'created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'short_description', 'description')
        }),
        ('Location', {
            'fields': ('destination',)
        }),
        ('Restaurant Details', {
            'fields': ('restaurant_type', 'cuisine_type', 'budget_range')
        }),
        ('Contact & Website', {
            'fields': ('website', 'phone', 'email')
        }),
        ('Ratings', {
            'fields': ('average_rating', 'rating_count')
        }),
        ('Sustainability & Hygge', {
            'fields': ('sustainability_score', 'hygge_factor', 'carbon_neutral', 'supports_local_community', 'organic_ingredients', 'locally_sourced')
        }),
        ('Location Details', {
            'fields': ('address', 'latitude', 'longitude')
        }),
        ('Media', {
            'fields': ('main_image', 'gallery_images')
        }),
        ('Menu & Features', {
            'fields': ('signature_dishes', 'dietary_options', 'amenities'),
            'classes': ('collapse',)
        }),
        ('Hours', {
            'fields': ('opening_hours',)
        }),
        ('SEO & Meta', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Status & Admin', {
            'fields': ('is_featured', 'is_active', 'admin_notes')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def sustainability_badge(self, obj):
        badge = obj.get_sustainability_badge()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em;">{}</span>',
            badge['color'],
            badge['text']
        )
    sustainability_badge.short_description = 'Sustainability'

    def price_display(self, obj):
        return obj.get_price_display()
    price_display.short_description = 'Price'


@admin.register(RestaurantRating)
class RestaurantRatingAdmin(admin.ModelAdmin):
    """Admin for restaurant ratings"""
    list_display = ('user', 'restaurant', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'restaurant__name', 'review_text')
    readonly_fields = ('id', 'created_at', 'updated_at')

    fieldsets = (
        ('Rating Information', {
            'fields': ('restaurant', 'user', 'rating', 'review_text')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RestaurantComment)
class RestaurantCommentAdmin(admin.ModelAdmin):
    """Admin for restaurant comments"""
    list_display = ('user', 'restaurant', 'comment_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'restaurant__name', 'comment')
    readonly_fields = ('id', 'created_at', 'updated_at')

    fieldsets = (
        ('Comment Information', {
            'fields': ('restaurant', 'user', 'comment')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Comment'


# Customize admin site
admin.site.site_header = "HygGeo Experiences Administration"
admin.site.site_title = "HygGeo Experiences Admin"
admin.site.index_title = "Manage Sustainable Travel Experiences"