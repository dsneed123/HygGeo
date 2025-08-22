# experiences/forms.py
from django import forms
from .models import Experience, Provider, Destination, Category
from .models import Category
class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = [
            'title', 'short_description', 'description', 'main_image',
            'destination', 'provider', 'experience_type', 'categories',
            'budget_range', 'group_size', 'duration', 'is_featured', 'is_active'
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
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial values
        self.fields['is_active'].initial = True
        self.fields['is_featured'].initial = False
        
        # Add help text
        self.fields['title'].help_text = 'This will be the main headline for your experience'
        self.fields['short_description'].help_text = 'Brief description shown on cards and previews'
        self.fields['categories'].help_text = 'Hold Ctrl/Cmd to select multiple categories'
        self.fields['main_image'].help_text = 'Upload a high-quality image representing this experience'
        
        # Make sure we have data for dropdowns
        if not self.fields['destination'].queryset.exists():
            self.fields['destination'].widget.attrs['data-no-options'] = 'No destinations available'
            
        if not self.fields['provider'].queryset.exists():
            self.fields['provider'].widget.attrs['data-no-options'] = 'No providers available'

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
        fields = '__all__'
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

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'icon', 'color']

