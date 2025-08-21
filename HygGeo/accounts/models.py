# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

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