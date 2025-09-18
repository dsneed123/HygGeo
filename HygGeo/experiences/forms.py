# experiences/forms.py
from django import forms
from .models import Experience, Provider, Destination, Category, ExperienceType
class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = [
            'title', 'short_description', 'description', 'main_image',
            'destination', 'provider', 'experience_type', 'categories',
            'budget_range', 'group_size', 'duration', 'sustainability_score',
            'hygge_factor', 'meta_title', 'meta_description', 'is_featured',
            'is_active', 'booking_required', 'affiliate_link',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter experience title',
                'required': True
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief description for cards (max 300 characters)',
                'maxlength': 300
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Detailed description of the experience...'
            }),
            'main_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'destination': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'provider': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'experience_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'categories': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '4'
            }),
            'budget_range': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'group_size': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'duration': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'sustainability_score': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }, choices=[
                (i, f"{i} - {'Very Poor' if i == 1 else 'Poor' if i == 2 else 'Below Average' if i == 3 else 'Fair' if i == 4 else 'Average' if i == 5 else 'Good' if i == 6 else 'Very Good' if i == 7 else 'Excellent' if i == 8 else 'Outstanding' if i == 9 else 'Perfect'}")
                for i in range(1, 11)
            ]),
            'hygge_factor': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }, choices=[
                (i, f"{i} - {'Very Low' if i == 1 else 'Low' if i == 2 else 'Below Average' if i == 3 else 'Fair' if i == 4 else 'Average' if i == 5 else 'Good' if i == 6 else 'Very Good' if i == 7 else 'Excellent' if i == 8 else 'Outstanding' if i == 9 else 'Perfect'}")
                for i in range(1, 11)
            ]),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'booking_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'affiliate_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/book-this-experience'
            }),
            'meta_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SEO title (leave blank to use main title)',
                'maxlength': 60
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief SEO description for search results (120-160 characters)',
                'maxlength': 160
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial values
        self.fields['is_active'].initial = True
        self.fields['is_featured'].initial = False
        self.fields['sustainability_score'].initial = 5
        self.fields['hygge_factor'].initial = 5
        
        # Add comprehensive help text and labels with definitions
        self.fields['title'].help_text = 'The main headline that will appear on experience cards and detail pages. Make it compelling and descriptive.'
        self.fields['short_description'].help_text = 'A brief, engaging summary (max 300 characters) shown on cards and search results. Focus on key highlights.'
        self.fields['description'].help_text = 'Detailed description of what participants can expect, including activities, highlights, and unique features.'
        self.fields['main_image'].help_text = 'Upload a high-quality, representative image (JPG, PNG, WebP). This will be the primary visual for your experience.'
        self.fields['sustainability_score'].help_text = 'Rate the environmental impact and sustainability practices (1=Poor, 5=Average, 10=Excellent). Consider carbon footprint, waste reduction, local sourcing.'
        self.fields['hygge_factor'].help_text = 'Rate the coziness, comfort, and mindful enjoyment factor (1=Rushed/Stressful, 5=Moderate, 10=Very Cozy/Relaxing).'

        # Improve field labels with detailed definitions
        self.fields['experience_type'].label = 'Experience Type'
        self.fields['experience_type'].help_text = 'The primary category that best describes this experience. Examples: Adventure (hiking, climbing), Cultural (museums, festivals), Culinary (food tours, cooking classes), Wellness (spa, meditation), Nature (wildlife, gardens).'

        self.fields['categories'].label = 'Experience Categories'
        self.fields['categories'].help_text = 'Select all applicable tags that help users filter experiences. Examples: Outdoor (nature activities), Family-Friendly (suitable for children), Budget-Friendly (affordable options), Luxury (premium experiences), Solo-Friendly (good for individual travelers).'

        self.fields['destination'].label = 'Destination Location'
        self.fields['destination'].help_text = 'The city, region, or specific location where this experience takes place. This helps users find experiences in their desired travel area.'

        self.fields['provider'].label = 'Experience Provider'
        self.fields['provider'].help_text = 'The company, organization, or individual who offers this experience. This could be a tour operator, local guide, business, or venue.'

        self.fields['budget_range'].label = 'Price Range'
        self.fields['budget_range'].help_text = 'The typical cost category for this experience. Budget ($): Under $50, Mid-range ($$): $50-150, Premium ($$$): $150-500, Luxury ($$$$): $500+. Choose the range that best fits the average price.'

        self.fields['group_size'].label = 'Group Size Capacity'
        self.fields['group_size'].help_text = 'Maximum number of participants that can join this experience. Consider: Solo (1 person), Small Group (2-8), Medium Group (9-20), Large Group (21+), or Private (exclusive booking).'

        self.fields['duration'].label = 'Experience Duration'
        self.fields['duration'].help_text = 'How long the experience lasts from start to finish. Examples: Quick (under 2 hours), Half-day (2-5 hours), Full-day (6-8 hours), Multi-day (overnight or longer).'

        self.fields['booking_required'].label = 'Advance Booking Required'
        self.fields['booking_required'].help_text = 'Check this if participants must book in advance. Leave unchecked for walk-in or spontaneous experiences.'

        self.fields['affiliate_link'].label = 'Booking/Website Link'
        self.fields['affiliate_link'].help_text = 'Direct link where users can book or learn more about this experience. Can be the provider\'s website, booking platform, or contact information.'

        self.fields['is_featured'].label = 'Featured Experience'
        self.fields['is_featured'].help_text = 'Mark as featured to highlight this experience on the homepage and in special promotions. Only select for exceptional experiences.'

        self.fields['is_active'].label = 'Currently Available'
        self.fields['is_active'].help_text = 'Uncheck to temporarily hide this experience (e.g., seasonal availability, maintenance). Users won\'t see inactive experiences in search results.'

        self.fields['meta_title'].label = 'SEO Title'
        self.fields['meta_title'].help_text = 'Custom title for search engines (max 60 chars). Leave blank to use main title. Include your focus keyword near the beginning.'

        self.fields['meta_description'].label = 'SEO Meta Description'
        self.fields['meta_description'].help_text = 'Description that appears in search results (120-160 chars). Include focus keyword and compelling call-to-action.'
        
        # Make sure we have data for dropdowns
        if not self.fields['destination'].queryset.exists():
            self.fields['destination'].widget.attrs['data-no-options'] = 'No destinations available'
        if not self.fields['provider'].queryset.exists():
            self.fields['provider'].widget.attrs['data-no-options'] = 'No providers available'
        if not self.fields['experience_type'].queryset.exists():
            self.fields['experience_type'].widget.attrs['data-no-options'] = 'No experience types available'
        if not self.fields['categories'].queryset.exists():
            self.fields['categories'].widget.attrs['data-no-options'] = 'No categories available'

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 5:
            raise forms.ValidationError('Title must be at least 5 characters long.')
        return title

    def clean_short_description(self):
        short_desc = self.cleaned_data.get('short_description')
        if len(short_desc) < 10:
            raise forms.ValidationError('Short description must be at least 10 characters long.')
        return short_desc
class DestinationForm(forms.ModelForm):
    class Meta:
        model = Destination
        fields = [
            'name', 'slug', 'country', 'region', 'description',
            'sustainability_score', 'hygge_factor', 'image',
            'best_time_to_visit', 'climate'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Copenhagen, Tulum, Scottish Highlands',
                'required': True
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'auto-generated-from-name',
                'help_text': 'Leave blank to auto-generate from name'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Denmark, Mexico, Scotland',
                'required': True
            }),
            'region': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Scandinavia, Yucatan Peninsula, United Kingdom'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe what makes this destination special, its character, and what travelers can expect...'
            }),
            'sustainability_score': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[
                (i, f"{i} - {'Very Poor' if i == 1 else 'Poor' if i == 2 else 'Below Average' if i == 3 else 'Fair' if i == 4 else 'Average' if i == 5 else 'Good' if i == 6 else 'Very Good' if i == 7 else 'Excellent' if i == 8 else 'Outstanding' if i == 9 else 'Perfect'}")
                for i in range(1, 11)
            ]),
            'hygge_factor': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[
                (i, f"{i} - {'Very Low' if i == 1 else 'Low' if i == 2 else 'Below Average' if i == 3 else 'Fair' if i == 4 else 'Average' if i == 5 else 'Good' if i == 6 else 'Very Good' if i == 7 else 'Excellent' if i == 8 else 'Outstanding' if i == 9 else 'Perfect'}")
                for i in range(1, 11)
            ]),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'best_time_to_visit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., May-September for warm weather, December-February for winter sports'
            }),
            'climate': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Temperate oceanic, Mediterranean, Tropical'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set initial values
        self.fields['sustainability_score'].initial = 5
        self.fields['hygge_factor'].initial = 5

        # Add comprehensive help text
        self.fields['name'].help_text = 'The primary name of this destination as travelers would know it'
        self.fields['slug'].help_text = 'URL-friendly version of the name (auto-generated if left blank)'
        self.fields['country'].help_text = 'The country where this destination is located'
        self.fields['region'].help_text = 'Broader geographic region (optional, e.g., Scandinavia, Mediterranean)'
        self.fields['description'].help_text = 'Compelling description that captures the essence and appeal of this destination'
        self.fields['sustainability_score'].help_text = 'Rate environmental consciousness and sustainable tourism practices (1-10)'
        self.fields['hygge_factor'].help_text = 'Rate how cozy, comfortable, and mindfully enjoyable this destination is (1-10)'
        self.fields['image'].help_text = 'Upload a beautiful, representative image that showcases this destination'
        self.fields['best_time_to_visit'].help_text = 'Best months or seasons to visit this destination'
        self.fields['climate'].help_text = 'General climate type (e.g., temperate, tropical, mediterranean)'

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 2:
            raise forms.ValidationError('Destination name must be at least 2 characters long.')
        return name

    def clean_country(self):
        country = self.cleaned_data.get('country')
        if len(country) < 2:
            raise forms.ValidationError('Country name must be at least 2 characters long.')
        return country
from django import forms
from .models import Provider

class ProviderForm(forms.ModelForm):
    class Meta:
        model = Provider
        fields = [
            'name', 'slug', 'description', 'website',
            'contact_email', 'phone', 'sustainability_certifications',
            'verified', 'logo'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter provider name',
                'required': True
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'auto-generated-slug',
                'help_text': 'Leave blank to auto-generate from name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe what this provider offers...'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@provider.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (555) 123-4567'
            }),
            'sustainability_certifications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'List any eco-certifications or sustainability credentials...'
            }),
            'verified': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'style': 'display: none;'  # Hidden for custom upload area
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make name field required
        self.fields['name'].required = True
        # Make slug optional - we'll auto-generate if empty
        self.fields['slug'].required = False
        
        # Add help text
        self.fields['website'].help_text = 'Full URL including https://'
        self.fields['verified'].help_text = 'Check if verified as sustainable by HygGeo team'
        self.fields['logo'].help_text = 'Upload a logo or representative image'

    def clean_website(self):
        website = self.cleaned_data.get('website')
        if website and not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        return website

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        # If slug is empty, we'll generate it in the view from the name
        return slug
from .models import ExperienceType

class ExperienceTypeForm(forms.ModelForm):
    class Meta:
        model = ExperienceType
        fields = ['name', 'slug', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Adventure, Cultural, Culinary, Wellness',
                'required': True
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'auto-generated-slug',
                'help_text': 'Leave blank to auto-generate from name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe what makes this type of experience unique...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].help_text = 'The main type or theme of experience (e.g., Adventure, Cultural, Culinary)'
        self.fields['description'].help_text = 'Brief description of what experiences of this type typically involve'

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'icon', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Outdoor, Family-Friendly, Budget-Friendly, Luxury',
                'required': True
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'auto-generated-slug',
                'help_text': 'Leave blank to auto-generate from name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe what experiences in this category offer...'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'fas fa-hiking (for Outdoor), fas fa-child (for Family-Friendly)',
                'help_text': 'FontAwesome icon class - browse icons at fontawesome.com'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'help_text': 'Choose a color that represents this category'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].help_text = 'Category name (e.g., Outdoor, Family-Friendly, Budget-Friendly, Luxury)'
        self.fields['description'].help_text = 'Brief description of what experiences in this category typically offer'
        self.fields['icon'].help_text = 'FontAwesome icon class - browse available icons at fontawesome.com/icons'
        self.fields['color'].help_text = 'Choose a color that best represents this category'

