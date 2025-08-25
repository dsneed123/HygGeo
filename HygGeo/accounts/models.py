# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
class UserProfile(models.Model):
    """Extended user profile for HygGeo users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    # Travel preferences
    sustainability_priority = models.IntegerField(
        choices=[(1, 'Low'), (2, 'Medium'), (3, 'High'), (4, 'Very High'), (5, 'Essential')],
        default=3,
        help_text="How important is sustainability in your travel decisions?"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

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
    destination = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    trip_status = models.CharField(max_length=20, choices=TRIP_STATUS_CHOICES, default='planning')
    
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
    trip_image = models.ImageField(upload_to='trip_images/', blank=True, null=True)
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