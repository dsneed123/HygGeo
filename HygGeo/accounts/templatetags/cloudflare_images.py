"""
Template filters for Cloudflare Image Transformations.

Usage:
    {% load cloudflare_images %}

    {{ image.url|cf_image:"format=webp,width=640,quality=30" }}
"""

from django import template
from urllib.parse import urlparse

register = template.Library()


@register.filter
def cf_image(image_url, transformations=''):
    """
    Convert an image URL to use Cloudflare's /cdn-cgi/image/ transformation API.

    Args:
        image_url: The original image URL (e.g., https://www.hyggeo.com/hyggeo-images/media/file.jpg)
        transformations: Comma-separated transformation options (e.g., "format=webp,width=640,quality=30")

    Returns:
        Cloudflare transformation URL (e.g., https://www.hyggeo.com/cdn-cgi/image/format=webp,width=640,quality=30/hyggeo-images/media/file.jpg)

    Example:
        {{ destination.image.url|cf_image:"format=webp,width=640,quality=30" }}
    """
    if not image_url:
        return ''

    # Parse the URL to get components
    parsed = urlparse(str(image_url))

    # Get the path without leading slash
    path = parsed.path.lstrip('/')

    # Construct Cloudflare transformation URL
    # Format: https://domain.com/cdn-cgi/image/options/path
    if transformations:
        cf_url = f"{parsed.scheme}://{parsed.netloc}/cdn-cgi/image/{transformations}/{path}"
    else:
        # No transformations, return original URL
        cf_url = str(image_url)

    return cf_url
