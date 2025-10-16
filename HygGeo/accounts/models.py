# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from storages.backends.s3boto3 import S3Boto3Storage

s3_storage = S3Boto3Storage()
class UserProfile(models.Model):
    """Extended user profile for HygGeo users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    avatar = models.ImageField(
        storage=s3_storage,
        upload_to='avatars/',
        null=True,
        blank=True
    )

    # Travel preferences
    sustainability_priority = models.IntegerField(
        choices=[(1, 'Low'), (2, 'Medium'), (3, 'High'), (4, 'Very High'), (5, 'Essential')],
        default=3,
        help_text="How important is sustainability in your travel decisions?"
    )

    # Email preferences
    email_consent = models.BooleanField(
        default=True,
        help_text="I consent to receive emails about sustainable travel opportunities, community updates, and newsletters from HygGeo"
    )
    unsubscribe_token = models.CharField(max_length=64, blank=True, null=True, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

    def save(self, *args, **kwargs):
        if not self.unsubscribe_token:
            import secrets
            self.unsubscribe_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def get_unsubscribe_url(self):
        from django.urls import reverse
        return reverse('unsubscribe', kwargs={'token': self.unsubscribe_token})

class TravelSurvey(models.Model):
    """Survey responses for travel interests and preferences"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='travel_surveys')
    
    # Travel style preferences
    TRAVEL_STYLE_CHOICES = [
        ('adventure', 'Adventure & Outdoor Activities'),
        ('cultural', 'Cultural Experiences'),
        ('relaxation', 'Relaxation & Wellness'),
        ('urban', 'Urban Exploration'),
        ('nature', 'Nature & Wildlife'),
        ('food', 'Culinary Experiences'),
        ('historical', 'Historical Sites'),
        ('volunteering', 'Volunteer Tourism'),
    ]
    
    travel_styles = models.JSONField(
        default=list,
        help_text="Selected travel styles (stored as list)"
    )
    
    # Accommodation preferences
    ACCOMMODATION_CHOICES = [
        ('eco_hotels', 'Eco-friendly Hotels'),
        ('hostels', 'Sustainable Hostels'),
        ('airbnb', 'Local Airbnb/Home-stays'),
        ('camping', 'Camping & Glamping'),
        ('ecolodges', 'Eco-lodges'),
        ('farm_stays', 'Farm Stays'),
    ]
    
    accommodation_preferences = models.JSONField(
        default=list,
        help_text="Preferred accommodation types"
    )
    
    # Transportation preferences
    TRANSPORT_CHOICES = [
        ('walking', 'Walking'),
        ('cycling', 'Cycling'),
        ('public_transport', 'Public Transportation'),
        ('electric_vehicles', 'Electric Vehicles'),
        ('train', 'Train Travel'),
        ('car_sharing', 'Car Sharing Services'),
        ('sailing', 'Sailing/Ferry'),
    ]
    
    transport_preferences = models.JSONField(
        default=list,
        help_text="Preferred transportation methods"
    )
    
    # Budget range
    BUDGET_CHOICES = [
        ('budget', 'Budget ($0-50/day)'),
        ('mid_range', 'Mid-range ($50-150/day)'),
        ('luxury', 'Luxury ($150+/day)'),
        ('varies', 'Varies by trip'),
    ]
    
    budget_range = models.CharField(
        max_length=20,
        choices=BUDGET_CHOICES,
        default='varies'
    )
    
    # Travel frequency
    FREQUENCY_CHOICES = [
        ('rarely', 'Rarely (once a year or less)'),
        ('occasionally', 'Occasionally (2-3 times a year)'),
        ('regularly', 'Regularly (4-6 times a year)'),
        ('frequently', 'Frequently (monthly or more)'),
    ]
    
    travel_frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='occasionally'
    )
    
    # Sustainability priorities
    sustainability_factors = models.JSONField(
        default=list,
        help_text="Important sustainability factors"
    )
    
    # Additional preferences
    group_size_preference = models.CharField(
        max_length=20,
        choices=[
            ('solo', 'Solo Travel'),
            ('couple', 'Couple'),
            ('small_group', 'Small Group (3-5 people)'),
            ('large_group', 'Large Group (6+ people)'),
            ('family', 'Family with Children'),
        ],
        default='solo'
    )
    
    trip_duration_preference = models.CharField(
        max_length=20,
        choices=[
            ('weekend', 'Weekend (1-3 days)'),
            ('short', 'Short Trip (4-7 days)'),
            ('medium', 'Medium Trip (1-2 weeks)'),
            ('long', 'Long Trip (3+ weeks)'),
            ('varies', 'Varies'),
        ],
        default='short'
    )
    
    # Free text fields
    dream_destination = models.CharField(max_length=200, blank=True)
    sustainability_goals = models.TextField(
        max_length=1000, 
        blank=True,
        help_text="What are your personal sustainability goals when traveling?"
    )
    
    # Metadata
    completed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-completed_at']
    
    def __str__(self):
        return f"Survey by {self.user.username} - {self.completed_at.strftime('%Y-%m-%d')}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)


class Trip(models.Model):
    TRIP_STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('seeking_buddies', 'Seeking Travel Buddies'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
    ]
    
    BUDGET_RANGE_CHOICES = [
        ('budget', 'Budget ($0-1,000)'),
        ('moderate', 'Moderate ($1,000-3,000)'),
        ('comfortable', 'Comfortable ($3,000-5,000)'),
        ('luxury', 'Luxury ($5,000+)'),
    ]
    
    GROUP_SIZE_CHOICES = [
        ('solo', 'Solo Adventure'),
        ('small', 'Small Group (2-4 people)'),
        ('medium', 'Medium Group (5-8 people)'),
        ('large', 'Large Group (9+ people)'),
    ]
    
    DURATION_CHOICES = [
        ('short', 'Short Trip (1-7 days)'),
        ('medium', 'Medium Trip (1-2 weeks)'),
        ('long', 'Long Trip (2-4 weeks)'),
        ('extended', 'Extended Journey (1+ months)'),
    ]
    
    TRAVEL_FREQUENCY_CHOICES = [
        ('slow', 'Slow & Mindful Travel'),
        ('moderate', 'Balanced Exploration'),
        ('frequent', 'Active Adventure'),
        ('intensive', 'Intensive Experience'),
    ]
    
    VISIBILITY_CHOICES = [
        ('public', 'Public - All HygGeo users'),
        ('community', 'Community - Members only'),
        ('private', 'Private - Only me'),
    ]
    
    SEEKING_BUDDIES_CHOICES = [
        ('yes', 'Yes, seeking travel buddies'),
        ('maybe', 'Open to meeting fellow travelers'),
        ('no', 'Planning solo/with existing group'),
    ]
    
    # Basic Information
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_trips')
    trip_name = models.CharField(max_length=200)
    destination = models.ForeignKey('experiences.Destination', on_delete=models.CASCADE, related_name='trips')
    description = models.TextField(blank=True, null=True)
    trip_status = models.CharField(max_length=20, choices=TRIP_STATUS_CHOICES, default='planning')
    experiences = models.ManyToManyField('experiences.Experience', blank=True, related_name='trips')

    
    # Dates
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    trip_duration_preference = models.CharField(max_length=20, choices=DURATION_CHOICES, default='short')
    
    # Group & Budget
    group_size_preference = models.CharField(max_length=20, choices=GROUP_SIZE_CHOICES, default='solo')
    budget_range = models.CharField(max_length=20, choices=BUDGET_RANGE_CHOICES, default='moderate')
    travel_frequency = models.CharField(max_length=20, choices=TRAVEL_FREQUENCY_CHOICES, default='moderate')
    seeking_buddies = models.CharField(max_length=10, choices=SEEKING_BUDDIES_CHOICES, default='yes')
    
    # Travel Interests (stored as JSON array - compatible with your travel buddy system)
    travel_styles = models.JSONField(default=list, blank=True)
    
    # Sustainability
    sustainability_priority = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=3)
    sustainability_factors = models.JSONField(default=list, blank=True)
    
    # Media & Privacy
    trip_image = models.ImageField(
        storage=s3_storage,
        upload_to='trip_images/',
        blank=True,
        null=True
    )
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    allow_messages = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.trip_name} - {self.destination}"
    
    def get_absolute_url(self):
        return reverse('trip_detail', kwargs={'pk': self.pk})
    
    @property
    def duration_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return None
    
    @property
    def eco_level_display(self):
        levels = {
            1: 'Eco-Aware',
            2: 'Eco-Friendly', 
            3: 'Eco-Focused',
            4: 'Eco-Champion',
            5: 'Eco-Warrior'
        }
        return levels.get(self.sustainability_priority, 'Eco-Focused')
    
    # Add this to your accounts/models.py

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, null=True, blank=True, related_name='messages')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    parent_message = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username}: {self.subject[:50]}"
    
    @property
    def conversation_id(self):
        """Generate a consistent conversation ID for grouping messages"""
        if self.parent_message:
            return self.parent_message.conversation_id
        return self.id


class EmailTemplate(models.Model):
    """Email templates for mass email campaigns"""
    name = models.CharField(max_length=200, help_text="Template name for admin reference")
    subject = models.CharField(max_length=300, help_text="Email subject line. Use {{}} for merge fields like {{first_name}}")
    html_content = models.TextField(help_text="HTML email content. Use {{}} for merge fields like {{first_name}}, {{experiences_count}}")
    text_content = models.TextField(blank=True, help_text="Plain text version (optional, will be auto-generated if empty)")

    # Template categorization
    CATEGORY_CHOICES = [
        ('welcome', 'Welcome/Onboarding'),
        ('experiences', 'New Experiences'),
        ('community', 'Community Updates'),
        ('sustainability', 'Sustainability Tips'),
        ('newsletter', 'Newsletter'),
        ('announcement', 'Announcements'),
        ('other', 'Other'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')

    # Merge fields available
    available_merge_fields = models.JSONField(
        default=list,
        help_text="Available merge fields for this template (auto-populated)"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.get_category_display()}: {self.name}"


class EmailCampaign(models.Model):
    """Mass email campaigns"""
    name = models.CharField(max_length=200, help_text="Campaign name for tracking")
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE)

    # Recipients
    RECIPIENT_CHOICES = [
        ('all_users', 'All Users'),
        ('active_users', 'Active Users (logged in last 30 days)'),
        ('survey_completed', 'Users who completed surveys'),
        ('trip_creators', 'Users who created trips'),
        ('admin_only', 'Admin Users Only (for testing)'),
        ('custom', 'Custom Selection'),
    ]
    recipient_type = models.CharField(max_length=20, choices=RECIPIENT_CHOICES, default='all_users')
    custom_recipients = models.ManyToManyField(User, blank=True, related_name='custom_campaigns', help_text="Used when recipient_type is 'custom'")

    # Campaign settings
    MODE_CHOICES = [
        ('test', 'Test Mode (Admin users only)'),
        ('production', 'Production Mode (Send to selected recipients)'),
    ]
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='test')

    # Scheduling
    scheduled_send = models.DateTimeField(null=True, blank=True, help_text="Leave empty to send immediately")

    # Status tracking
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')

    # Statistics
    total_recipients = models.IntegerField(default=0)
    emails_sent = models.IntegerField(default=0)
    emails_failed = models.IntegerField(default=0)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_campaigns')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def get_recipient_count(self):
        """Calculate how many recipients this campaign will reach"""
        if self.mode == 'test':
            return User.objects.filter(is_staff=True).count()

        if self.recipient_type == 'all_users':
            return User.objects.filter(is_active=True).count()
        elif self.recipient_type == 'active_users':
            from django.utils import timezone
            cutoff = timezone.now() - timezone.timedelta(days=30)
            return User.objects.filter(is_active=True, last_login__gte=cutoff).count()
        elif self.recipient_type == 'survey_completed':
            return User.objects.filter(travel_surveys__isnull=False).distinct().count()
        elif self.recipient_type == 'trip_creators':
            return User.objects.filter(created_trips__isnull=False).distinct().count()
        elif self.recipient_type == 'admin_only':
            return User.objects.filter(is_staff=True).count()
        elif self.recipient_type == 'custom':
            return self.custom_recipients.count()

        return 0


class EmailLog(models.Model):
    """Log individual email sends for tracking and debugging"""
    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, related_name='email_logs')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    subject_sent = models.CharField(max_length=300, help_text="Subject after merge field processing")
    error_message = models.TextField(blank=True, help_text="Error details if send failed")

    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['campaign', 'recipient']

    def __str__(self):
        return f"{self.campaign.name} -> {self.recipient.email} ({self.status})"


class PageView(models.Model):
    """Track page views with referrer source attribution"""
    # User information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='page_views')
    session_id = models.CharField(max_length=100, help_text="Anonymous session tracking")

    # Page information
    page_url = models.CharField(max_length=500, help_text="Full URL of the page viewed")
    page_path = models.CharField(max_length=500, help_text="Path component of URL")
    page_title = models.CharField(max_length=300, blank=True)

    # Referrer tracking (where they came from)
    referrer_url = models.CharField(max_length=500, blank=True, null=True, help_text="Full referrer URL")
    referrer_source = models.CharField(max_length=100, blank=True, null=True, help_text="Parsed source (e.g., Facebook, Google, Direct)")
    utm_source = models.CharField(max_length=100, blank=True, null=True, help_text="UTM source parameter")
    utm_medium = models.CharField(max_length=100, blank=True, null=True, help_text="UTM medium parameter")
    utm_campaign = models.CharField(max_length=100, blank=True, null=True, help_text="UTM campaign parameter")
    utm_term = models.CharField(max_length=100, blank=True, null=True)
    utm_content = models.CharField(max_length=100, blank=True, null=True)

    # Device/Browser information
    user_agent = models.CharField(max_length=500, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_type = models.CharField(max_length=20, blank=True, choices=[
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
        ('unknown', 'Unknown')
    ], default='unknown')

    # Timestamps
    viewed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['viewed_at']),
            models.Index(fields=['page_path']),
            models.Index(fields=['referrer_source']),
            models.Index(fields=['utm_source']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{user_str} viewed {self.page_path} from {self.referrer_source or 'Direct'}"


class ClickEvent(models.Model):
    """Track clicks on specific elements (links, buttons, etc.)"""
    # User information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='click_events')
    session_id = models.CharField(max_length=100, help_text="Anonymous session tracking")

    # Click information
    element_type = models.CharField(max_length=50, help_text="Type of element clicked (link, button, etc.)")
    element_text = models.CharField(max_length=500, blank=True, help_text="Text content of clicked element")
    element_id = models.CharField(max_length=200, blank=True, help_text="HTML ID of clicked element")
    element_class = models.CharField(max_length=200, blank=True, help_text="HTML class of clicked element")

    # Destination
    target_url = models.CharField(max_length=500, help_text="URL the link points to")
    is_external = models.BooleanField(default=False, help_text="Is this an external link?")

    # Source page
    source_page = models.CharField(max_length=500, help_text="Page where the click occurred")
    source_path = models.CharField(max_length=500, help_text="Path of source page")

    # Referrer attribution (inherited from page view)
    referrer_source = models.CharField(max_length=100, blank=True, null=True, help_text="Original traffic source")
    utm_source = models.CharField(max_length=100, blank=True, null=True)
    utm_campaign = models.CharField(max_length=100, blank=True, null=True)

    # Click context
    clicked_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-clicked_at']
        indexes = [
            models.Index(fields=['clicked_at']),
            models.Index(fields=['target_url']),
            models.Index(fields=['source_path']),
            models.Index(fields=['referrer_source']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{user_str} clicked {self.element_text[:50]} on {self.source_path}"