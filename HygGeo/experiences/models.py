# experiences/models.py
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

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
    
    # Affiliate & Booking
    affiliate_link = models.URLField(help_text="Affiliate tracking link for bookings")
    booking_link = models.URLField(blank=True, help_text="Direct booking link (optional)")
    commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Commission percentage for affiliate sales"
    )
    
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
        else:
            return "Contact for pricing"
    
    def get_sustainability_badge(self):
        """Return sustainability badge level"""
        if self.sustainability_score >= 8:
            return {'level': 'excellent', 'color': '#28a745', 'text': 'Excellent'}
        elif self.sustainability_score >= 6:
            return {'level': 'good', 'color': '#ffc107', 'text': 'Good'}
        else:
            return {'level': 'fair', 'color': '#fd7e14', 'text': 'Fair'}

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
    
    def __str__(self):
        return self.name
