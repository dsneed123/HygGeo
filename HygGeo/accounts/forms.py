# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, TravelSurvey

class CustomUserCreationForm(UserCreationForm):
    """Extended user creation form with additional fields"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    """Form for editing user profile"""
    class Meta:
        model = UserProfile
        fields = ['bio', 'location', 'birth_date', 'avatar', 'sustainability_priority']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
            'sustainability_priority': forms.Select(attrs={'class': 'form-control'}),
        }

class TravelSurveyForm(forms.ModelForm):
    """Comprehensive travel survey form"""
    
    # Multi-select fields
    travel_styles = forms.MultipleChoiceField(
        choices=TravelSurvey.TRAVEL_STYLE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text="Select all that apply to your travel interests"
    )
    
    accommodation_preferences = forms.MultipleChoiceField(
        choices=TravelSurvey.ACCOMMODATION_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text="Choose your preferred sustainable accommodation types"
    )
    
    transport_preferences = forms.MultipleChoiceField(
        choices=TravelSurvey.TRANSPORT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text="Select your preferred eco-friendly transportation methods"
    )
    
    SUSTAINABILITY_FACTOR_CHOICES = [
        ('carbon_offset', 'Carbon Offset Programs'),
        ('local_economy', 'Supporting Local Economy'),
        ('waste_reduction', 'Waste Reduction'),
        ('wildlife_protection', 'Wildlife Protection'),
        ('cultural_preservation', 'Cultural Preservation'),
        ('water_conservation', 'Water Conservation'),
        ('renewable_energy', 'Renewable Energy Use'),
        ('fair_trade', 'Fair Trade Practices'),
        ('plastic_free', 'Plastic-Free Options'),
        ('organic_food', 'Organic/Local Food'),
    ]
    
    sustainability_factors = forms.MultipleChoiceField(
        choices=SUSTAINABILITY_FACTOR_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text="Which sustainability factors are most important to you?"
    )
    
    class Meta:
        model = TravelSurvey
        fields = [
            'travel_styles', 'accommodation_preferences', 'transport_preferences',
            'budget_range', 'travel_frequency', 'sustainability_factors',
            'group_size_preference', 'trip_duration_preference',
            'dream_destination', 'sustainability_goals'
        ]
        widgets = {
            'budget_range': forms.RadioSelect,
            'travel_frequency': forms.RadioSelect,
            'group_size_preference': forms.RadioSelect,
            'trip_duration_preference': forms.RadioSelect,
            'dream_destination': forms.TextInput(attrs={
                'placeholder': 'e.g., Costa Rica, Iceland, New Zealand...',
                'class': 'form-control'
            }),
            'sustainability_goals': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Share your personal sustainability goals and values when traveling...',
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if field_name not in ['travel_styles', 'accommodation_preferences', 
                                'transport_preferences', 'sustainability_factors']:
                if not isinstance(field.widget, forms.RadioSelect):
                    field.widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Convert multi-select fields to lists for JSON storage
        instance.travel_styles = self.cleaned_data['travel_styles']
        instance.accommodation_preferences = self.cleaned_data['accommodation_preferences']
        instance.transport_preferences = self.cleaned_data['transport_preferences']
        instance.sustainability_factors = self.cleaned_data['sustainability_factors']
        
        if commit:
            instance.save()
        return instance

class UserUpdateForm(forms.ModelForm):
    """Form for updating basic user information"""
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']