# experiences/models.py
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
import uuid

# Lazy S3 storage import - defers initialization until first use
def get_s3_storage():
    from storages.backends.s3boto3 import S3Boto3Storage
    return S3Boto3Storage()

# Use a callable for storage to avoid early initialization
class LazyS3Storage:
    def __call__(self):
        from storages.backends.s3boto3 import S3Boto3Storage
        return S3Boto3Storage()

s3_storage = LazyS3Storage()()
class Category(models.Model):
    """Categories for travel experiences"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fas fa-map-marker-alt', help_text="FontAwesome icon class")
    color = models.CharField(max_length=7, default='#2d5a3d', help_text="Hex color code")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            # Generate slug from name, removing leading/trailing dashes
            self.slug = slugify(self.name).strip('-')
            # If slug is empty after stripping, use the name as-is
            if not self.slug:
                self.slug = slugify(self.name.replace(' ', '-'))
        # Clean up slug: remove leading/trailing dashes
        self.slug = self.slug.strip('-')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Destination(models.Model):
    """Travel destinations"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    country = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    climate = models.CharField(max_length=100, blank=True)
    best_time_to_visit = models.CharField(max_length=200, blank=True)
    sustainability_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=5,
        help_text="Sustainability rating from 1-10"
    )
    hygge_factor = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=5,
        help_text="How well this destination embodies hygge principles (1-10)"
    )
    image = models.ImageField(
        storage=s3_storage,
        upload_to='destinations/',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name}, {self.country}"
    
    def get_absolute_url(self):
        return reverse('experiences:destination_detail', kwargs={'slug': self.slug})


class Provider(models.Model):
    """Travel service providers (hotels, tour companies, etc.)"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    website = models.URLField()
    contact_email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    sustainability_certifications = models.TextField(blank=True, help_text="List any eco-certifications")
    verified = models.BooleanField(default=False, help_text="Verified as sustainable by HygGeo team")
    logo = models.ImageField(
        storage=s3_storage,
        upload_to='providers/',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Experience(models.Model):
    """Travel experiences with affiliate links"""
    
    EXPERIENCE_TYPES = [
        ('accommodation', 'Accommodation'),
        ('activity', 'Activity'),
        ('tour', 'Tour'),
        ('transport', 'Transportation'),
        ('food', 'Food & Dining'),
        ('wellness', 'Wellness & Spa'),
        ('cultural', 'Cultural Experience'),
        ('adventure', 'Adventure'),
        ('volunteering', 'Volunteer Tourism'),
    ]
    
    BUDGET_RANGES = [
        ('budget', 'Budget ($0-50/day)'),
        ('mid_range', 'Mid-range ($50-150/day)'),
        ('luxury', 'Luxury ($150+/day)'),
    ]
    
    GROUP_SIZES = [
        ('solo', 'Solo Friendly'),
        ('couple', 'Perfect for Couples'),
        ('small_group', 'Small Groups (3-5)'),
        ('large_group', 'Large Groups (6+)'),
        ('family', 'Family Friendly'),
    ]
    
    DURATION_TYPES = [
        ('half_day', 'Half Day'),
        ('full_day', 'Full Day'),
        ('weekend', 'Weekend (2-3 days)'),
        ('short_trip', 'Short Trip (4-7 days)'),
        ('long_trip', 'Extended Trip (1+ weeks)'),
    ]
    
    # Basic Info
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, help_text="Brief description for cards")
    booking_required = models.BooleanField(
        default=True, 
        help_text="Uncheck if no booking is required for this experience"
    )
    
    # Update existing booking field to be optional:
    affiliate_link = models.URLField(
        blank=True, 
        help_text="Booking/affiliate link (leave empty for experiences that don't require booking)"
    )
    
    # Relationships
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='experiences')
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='experiences')
    categories = models.ManyToManyField(Category, related_name='experiences')
    
    # Experience Details
    experience_type = models.ForeignKey(
    'ExperienceType',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='experiences'
)
    budget_range = models.CharField(max_length=20, choices=BUDGET_RANGES)
    group_size = models.CharField(max_length=20, choices=GROUP_SIZES)
    duration = models.CharField(max_length=20, choices=DURATION_TYPES)
    
    # Pricing
    price_from = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_to = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    
    # Sustainability & Hygge
    sustainability_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=5,
        help_text="Sustainability rating from 1-10"
    )
    hygge_factor = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=5,
        help_text="How well this experience embodies hygge principles (1-10)"
    )
    carbon_neutral = models.BooleanField(default=False)
    supports_local_community = models.BooleanField(default=False)
    
    # Travel Style Matching (matches TravelSurvey choices)
    travel_styles = models.JSONField(
        default=list,
        help_text="Travel styles this experience matches (adventure, cultural, etc.)"
    )
    accommodation_types = models.JSONField(
        default=list,
        help_text="Accommodation types (eco_hotels, hostels, etc.)"
    )
    transport_types = models.JSONField(
        default=list,
        help_text="Transportation types (walking, cycling, train, etc.)"
    )
    sustainability_factors = models.JSONField(
        default=list,
        help_text="Sustainability factors (carbon_offset, local_economy, etc.)"
    )
    
    # Media
    main_image = models.ImageField(
        storage=s3_storage,
        upload_to='experiences/',
        null=True,
        blank=True
    )
    gallery_images = models.JSONField(default=list, blank=True, help_text="List of image URLs")
    

    
    # Features & Amenities
    included_features = models.JSONField(default=list, help_text="What's included in the experience")
    requirements = models.TextField(blank=True, help_text="Requirements or restrictions")
    what_to_bring = models.TextField(blank=True, help_text="What participants should bring")
    
    # SEO & Meta
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    
    # Status & Admin
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    admin_notes = models.TextField(blank=True, help_text="Internal notes for admin")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.destination.name}"
    
    def get_absolute_url(self):
     return reverse('experiences:experience_detail', kwargs={'slug': self.slug})
    
    def get_price_display(self):
        """Return formatted price range"""
        if self.price_from and self.price_to:
            return f"${self.price_from} - ${self.price_to}"
        elif self.price_from:
            return f"From ${self.price_from}"
        elif self.budget_range:
            # Use budget range instead of "Contact for pricing"
            budget_display = dict(self.BUDGET_RANGES).get(self.budget_range, self.budget_range)
            return budget_display
        else:
            return "Price varies"
    
    def get_sustainability_badge(self):
        """Return sustainability badge level"""
        if self.sustainability_score >= 8:
            return {'level': 'excellent', 'color': '#000000', 'text': 'Excellent'}
        elif self.sustainability_score >= 6:
            return {'level': 'good', 'color': '#000000', 'text': 'Good'}
        else:
            return {'level': 'fair', 'color': '#000000', 'text': 'Fair'}

    def get_experience_type_display(self):
        """Return experience type name or default"""
        if self.experience_type:
            return self.experience_type.name
        return "General Experience"

    def get_group_size_display(self):
        """Return human-readable group size"""
        return dict(self.GROUP_SIZES).get(self.group_size, self.group_size)

    def get_duration_display(self):
        """Return human-readable duration"""
        return dict(self.DURATION_TYPES).get(self.duration, self.duration)

    def get_budget_range_display(self):
        """Return human-readable budget range"""
        return dict(self.BUDGET_RANGES).get(self.budget_range, self.budget_range)

    def get_seo_analysis(self):
        """Get comprehensive SEO analysis with caching for performance"""
        from django.core.cache import cache
        from .seo_analyzer import get_seo_analysis_for_experience

        # Create cache key based on content hash
        content_hash = hash(f"{self.title}{self.meta_title}{self.meta_description}{self.description}{self.short_description}{self.updated_at}")
        cache_key = f"seo_analysis_{self.id}_{content_hash}"

        # Try to get from cache first
        cached_analysis = cache.get(cache_key)
        if cached_analysis:
            return cached_analysis

        experience_data = {
            'title': self.title,
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'description': self.description,
            'short_description': self.short_description,
            'destination': str(self.destination),
            'experience_type': str(self.experience_type) if self.experience_type else '',
            'categories': [cat.name for cat in self.categories.all()],
            'sustainability_score': self.sustainability_score,
            'hygge_factor': self.hygge_factor
        }

        analysis = get_seo_analysis_for_experience(experience_data)

        # Cache for 1 hour
        cache.set(cache_key, analysis, 3600)
        return analysis

    def get_seo_grade(self):
        """Get SEO grade and color based on calculated score"""
        analysis = self.get_seo_analysis()
        return analysis['grade']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class UserRecommendation(models.Model):
    """Personalized recommendations for users based on their survey"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    experience = models.ForeignKey(Experience, on_delete=models.CASCADE)
    match_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Algorithm-generated match score (0-100)"
    )
    reasons = models.JSONField(
        default=list,
        help_text="List of reasons why this was recommended"
    )
    viewed = models.BooleanField(default=False)
    clicked = models.BooleanField(default=False)
    bookmarked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'experience']
        ordering = ['-match_score', '-created_at']
    
    def __str__(self):
        return f"{self.user.username} -> {self.experience.title} ({self.match_score}%)"

class ExperienceReview(models.Model):
    """User reviews for experiences"""
    experience = models.ForeignKey(Experience, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    sustainability_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="How sustainable was this experience?"
    )
    hygge_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="How well did this embody hygge principles?"
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    would_recommend = models.BooleanField(default=True)
    verified_booking = models.BooleanField(default=False, help_text="User booked through HygGeo")
    helpful_votes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['experience', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.experience.title} ({self.rating}/5)"

class BookingTracking(models.Model):
    """Track affiliate link clicks and conversions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    experience = models.ForeignKey(Experience, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=100, help_text="Anonymous session tracking")
    clicked_at = models.DateTimeField(auto_now_add=True)
    converted = models.BooleanField(default=False)
    conversion_date = models.DateTimeField(null=True, blank=True)
    commission_earned = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-clicked_at']
    
    def __str__(self):
        return f"Booking tracking for {self.experience.title}"
    
class ExperienceType(models.Model):
    """Dynamic experience types for travel experiences"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            # Generate slug from name, removing leading/trailing dashes
            self.slug = slugify(self.name).strip('-')
            # If slug is empty after stripping, use the name as-is
            if not self.slug:
                self.slug = slugify(self.name.replace(' ', '-'))
        # Clean up slug: remove leading/trailing dashes
        self.slug = self.slug.strip('-')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Accommodation(models.Model):
    """Accommodation options (hotels, hostels, eco-lodges, etc.)"""

    ACCOMMODATION_TYPES = [
        ('hotel', 'Hotel'),
        ('hostel', 'Hostel'),
        ('eco_lodge', 'Eco-Lodge'),
        ('guesthouse', 'Guesthouse'),
        ('boutique', 'Boutique Hotel'),
        ('resort', 'Resort'),
        ('airbnb', 'Airbnb/Vacation Rental'),
        ('camping', 'Camping/Glamping'),
        ('homestay', 'Homestay'),
        ('cabin', 'Cabin/Cottage'),
    ]

    BUDGET_RANGES = [
        ('budget', 'Budget ($0-50/night)'),
        ('mid_range', 'Mid-range ($50-150/night)'),
        ('luxury', 'Luxury ($150+/night)'),
    ]

    # Basic Info
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, help_text="Brief description for cards")

    # Relationships
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='accommodations')
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='accommodations')

    # Accommodation Details
    accommodation_type = models.CharField(max_length=20, choices=ACCOMMODATION_TYPES)
    budget_range = models.CharField(max_length=20, choices=BUDGET_RANGES)

    # Pricing
    price_per_night_from = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_night_to = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')

    # Booking
    booking_link = models.URLField(blank=True, help_text="Booking/affiliate link")

    # Sustainability & Hygge
    sustainability_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=5,
        help_text="Sustainability rating from 1-10"
    )
    hygge_factor = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=5,
        help_text="How well this accommodation embodies hygge principles (1-10)"
    )
    carbon_neutral = models.BooleanField(default=False)
    supports_local_community = models.BooleanField(default=False)
    eco_certified = models.BooleanField(default=False, help_text="Has environmental certification")

    # Location
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Media
    main_image = models.ImageField(
        storage=s3_storage,
        upload_to='accommodations/',
        null=True,
        blank=True
    )
    gallery_images = models.JSONField(default=list, blank=True, help_text="List of image URLs")

    # Amenities & Features
    amenities = models.JSONField(default=list, help_text="List of amenities (wifi, breakfast, parking, etc.)")
    room_types = models.JSONField(default=list, help_text="Types of rooms available")

    # Capacity
    total_rooms = models.IntegerField(null=True, blank=True, help_text="Total number of rooms")
    max_guests = models.IntegerField(null=True, blank=True, help_text="Maximum guests per room")

    # Policies
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    cancellation_policy = models.TextField(blank=True)

    # SEO & Meta
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    # Status & Admin
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    admin_notes = models.TextField(blank=True, help_text="Internal notes for admin")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.destination.name}"

    def get_absolute_url(self):
        return reverse('experiences:accommodation_detail', kwargs={'slug': self.slug})

    def get_price_display(self):
        """Return formatted price range"""
        if self.price_per_night_from and self.price_per_night_to:
            return f"${self.price_per_night_from} - ${self.price_per_night_to}/night"
        elif self.price_per_night_from:
            return f"From ${self.price_per_night_from}/night"
        elif self.budget_range:
            budget_display = dict(self.BUDGET_RANGES).get(self.budget_range, self.budget_range)
            return budget_display
        else:
            return "Price varies"

    def get_sustainability_badge(self):
        """Return sustainability badge level"""
        if self.sustainability_score >= 8:
            return {'level': 'excellent', 'color': '#000000', 'text': 'Excellent'}
        elif self.sustainability_score >= 6:
            return {'level': 'good', 'color': '#000000', 'text': 'Good'}
        else:
            return {'level': 'fair', 'color': '#000000', 'text': 'Fair'}

    def get_accommodation_type_display(self):
        """Return human-readable accommodation type"""
        return dict(self.ACCOMMODATION_TYPES).get(self.accommodation_type, self.accommodation_type)


class TravelBlog(models.Model):
    """User-generated travel blog posts"""

    # Basic Info
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField(help_text="Main blog content - supports markdown")
    excerpt = models.CharField(max_length=300, help_text="Short excerpt for cards and previews")

    # Author & Relationships
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='travel_blogs')
    experience = models.ForeignKey(
        Experience,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blog_posts',
        help_text="Link to a specific experience"
    )
    accommodation = models.ForeignKey(
        Accommodation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blog_posts',
        help_text="Link to a specific accommodation"
    )
    destination = models.ForeignKey(
        Destination,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blog_posts',
        help_text="Main destination featured in this post"
    )

    # Media
    featured_image = models.ImageField(
        storage=s3_storage,
        upload_to='blog/',
        null=True,
        blank=True,
        help_text="Main image for the blog post"
    )
    gallery_images = models.JSONField(
        default=list,
        blank=True,
        help_text="Additional images for the post"
    )

    # Tags & Categories
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags for this post (e.g., ['adventure', 'solo travel', 'budget'])"
    )

    # Engagement
    views_count = models.IntegerField(default=0)
    likes_count = models.IntegerField(default=0)
    liked_by = models.ManyToManyField(
        'auth.User',
        related_name='liked_blogs',
        blank=True
    )

    # SEO
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    # Publishing
    is_published = models.BooleanField(
        default=False,
        help_text="Publish this post to make it visible to others"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Feature this post on the blog homepage"
    )
    published_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['is_published', '-published_at']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('experiences:blog_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        # Auto-publish timestamp
        if self.is_published and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        elif not self.is_published:
            self.published_at = None
        super().save(*args, **kwargs)

    def get_reading_time(self):
        """Estimate reading time in minutes"""
        word_count = len(self.content.split())
        reading_time = word_count // 200  # Assume 200 words per minute
        return max(1, reading_time)  # Minimum 1 minute


class BlogComment(models.Model):
    """Comments on travel blog posts"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blog_post = models.ForeignKey(TravelBlog, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='blog_comments')
    content = models.TextField()

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.blog_post.title}"


class Restaurant(models.Model):
    """Local restaurants and dining experiences"""

    RESTAURANT_TYPES = [
        ('fine_dining', 'Fine Dining'),
        ('casual_dining', 'Casual Dining'),
        ('cafe', 'Cafe'),
        ('bistro', 'Bistro'),
        ('street_food', 'Street Food'),
        ('food_truck', 'Food Truck'),
        ('farm_to_table', 'Farm-to-Table'),
        ('vegetarian', 'Vegetarian/Vegan'),
        ('bakery', 'Bakery'),
        ('bar', 'Bar/Pub'),
    ]

    CUISINE_TYPES = [
        ('local', 'Local Cuisine'),
        ('italian', 'Italian'),
        ('french', 'French'),
        ('asian', 'Asian'),
        ('mediterranean', 'Mediterranean'),
        ('american', 'American'),
        ('mexican', 'Mexican'),
        ('fusion', 'Fusion'),
        ('international', 'International'),
        ('seafood', 'Seafood'),
    ]

    BUDGET_RANGES = [
        ('budget', 'Budget ($0-20/meal)'),
        ('mid_range', 'Mid-range ($20-50/meal)'),
        ('upscale', 'Upscale ($50-100/meal)'),
        ('luxury', 'Luxury ($100+/meal)'),
    ]

    # Basic Info
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, help_text="Brief description for cards")

    # Relationships
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='restaurants')

    # Restaurant Details
    restaurant_type = models.CharField(max_length=20, choices=RESTAURANT_TYPES)
    cuisine_type = models.CharField(max_length=20, choices=CUISINE_TYPES)
    budget_range = models.CharField(max_length=20, choices=BUDGET_RANGES)

    # Website & Contact
    website = models.URLField(blank=True, help_text="Restaurant website or booking link")
    phone = models.CharField(max_length=50, blank=True, help_text="Contact phone number")
    email = models.EmailField(blank=True, help_text="Contact email")

    # Sustainability & Hygge
    sustainability_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=5,
        help_text="Sustainability rating from 1-10"
    )
    hygge_factor = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=5,
        help_text="How well this restaurant embodies hygge principles (1-10)"
    )
    carbon_neutral = models.BooleanField(default=False)
    supports_local_community = models.BooleanField(default=False)
    organic_ingredients = models.BooleanField(default=False, help_text="Uses organic ingredients")
    locally_sourced = models.BooleanField(default=False, help_text="Locally sourced ingredients")

    # Location
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Media
    main_image = models.ImageField(
        storage=s3_storage,
        upload_to='restaurants/',
        null=True,
        blank=True
    )
    gallery_images = models.JSONField(default=list, blank=True, help_text="List of image URLs")

    # Menu & Features
    signature_dishes = models.JSONField(default=list, help_text="List of signature dishes")
    dietary_options = models.JSONField(default=list, help_text="Dietary options (vegan, gluten-free, etc.)")
    amenities = models.JSONField(default=list, help_text="Amenities (outdoor seating, wifi, etc.)")

    # Hours
    opening_hours = models.TextField(blank=True, help_text="Restaurant opening hours")

    # SEO & Meta
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    # Ratings (calculated from user ratings)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, help_text="Average user rating")
    rating_count = models.IntegerField(default=0, help_text="Number of ratings")

    # Status & Admin
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    admin_notes = models.TextField(blank=True, help_text="Internal notes for admin")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.destination.name}"

    def get_absolute_url(self):
        return reverse('experiences:restaurant_detail', kwargs={'slug': self.slug})

    def get_price_display(self):
        """Return formatted price range"""
        if self.budget_range:
            budget_display = dict(self.BUDGET_RANGES).get(self.budget_range, self.budget_range)
            return budget_display
        else:
            return "Price varies"

    def update_average_rating(self):
        """Recalculate average rating from all user ratings"""
        from django.db.models import Avg, Count

        # Use aggregation for efficiency
        result = self.ratings.aggregate(
            avg_rating=Avg('rating'),
            count=Count('id')
        )

        self.average_rating = result['avg_rating'] or 0
        self.rating_count = result['count'] or 0
        self.save(update_fields=['average_rating', 'rating_count'])

    def get_sustainability_badge(self):
        """Return sustainability badge level"""
        if self.sustainability_score >= 8:
            return {'level': 'excellent', 'color': '#000000', 'text': 'Excellent'}
        elif self.sustainability_score >= 6:
            return {'level': 'good', 'color': '#000000', 'text': 'Good'}
        else:
            return {'level': 'fair', 'color': '#000000', 'text': 'Fair'}

    def get_restaurant_type_display(self):
        """Return human-readable restaurant type"""
        return dict(self.RESTAURANT_TYPES).get(self.restaurant_type, self.restaurant_type)

    def get_cuisine_type_display(self):
        """Return human-readable cuisine type"""
        return dict(self.CUISINE_TYPES).get(self.cuisine_type, self.cuisine_type)


class RestaurantRating(models.Model):
    """User ratings for restaurants"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='restaurant_ratings')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1-5 stars"
    )
    review_text = models.TextField(blank=True, help_text="Optional review text")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['restaurant', 'user']  # One rating per user per restaurant

    def __str__(self):
        return f"{self.user.username} - {self.restaurant.name} ({self.rating}/5)"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update restaurant's average rating immediately after saving
        self.restaurant.update_average_rating()

    def delete(self, *args, **kwargs):
        restaurant = self.restaurant
        super().delete(*args, **kwargs)
        # Update restaurant's average rating immediately after deletion
        restaurant.update_average_rating()


class RestaurantComment(models.Model):
    """User comments on restaurants"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='restaurant_comments')
    comment = models.TextField()

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} on {self.restaurant.name}"
