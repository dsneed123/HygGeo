"""
Middleware to handle broken category/experience-type URLs and redirect to correct ones
"""
from django.http import HttpResponsePermanentRedirect
from django.urls import resolve
from experiences.models import Category, ExperienceType


class BrokenSlugRedirectMiddleware:
    """
    Middleware to catch 404 errors from broken slugs (with leading dashes)
    and attempt to redirect to the correct URL
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only handle 404 responses for category or experience-type URLs
        if response.status_code == 404:
            path = request.path

            # Check if this is a category URL with a broken slug
            if '/category/' in path:
                redirect_url = self.try_fix_category_url(path)
                if redirect_url:
                    return HttpResponsePermanentRedirect(redirect_url)

            # Check if this is an experience-type URL with a broken slug (if applicable)
            # Add similar logic for other models if needed

        return response

    def try_fix_category_url(self, path):
        """
        Try to fix a broken category URL by finding a category with matching name
        """
        # Extract the broken slug from the path
        parts = path.split('/category/')
        if len(parts) != 2:
            return None

        broken_slug = parts[1].rstrip('/')

        # Remove leading dashes and clean up the slug
        cleaned_slug = broken_slug.lstrip('-').strip()

        if not cleaned_slug:
            return None

        # Try to find a category with this cleaned slug
        try:
            category = Category.objects.get(slug=cleaned_slug)
            # Return the correct URL
            return f'/experiences/category/{category.slug}/'
        except Category.DoesNotExist:
            # Try to find by name similarity
            # Remove dashes and compare names
            search_name = cleaned_slug.replace('-', ' ').title()

            try:
                category = Category.objects.get(name__iexact=search_name)
                return f'/experiences/category/{category.slug}/'
            except (Category.DoesNotExist, Category.MultipleObjectsReturned):
                pass

        return None
