# Image Optimization Guide for HygGeo

## Critical Issue: Image Sizes

Your PageSpeed Insights report shows that images are **30MB+ in size** and **not properly sized**. This is causing:
- **88-second LCP (Largest Contentful Paint)** - should be under 2.5s
- Poor mobile performance (score: 42/100)
- Excessive data usage for users

## Immediate Actions Required

### 1. Optimize Existing Images in DigitalOcean Spaces

Your images need to be:
- **Compressed**: Reduce file sizes by 70-90%
- **Resized**: Generate multiple sizes for responsive images
- **Converted**: Use modern formats (WebP, AVIF) with JPEG fallbacks

#### Current Issues:
```
Seattle image: 7,834 KB → should be ~200 KB (97% reduction)
Portland image: 3,544 KB → should be ~150 KB (96% reduction)
Experience images: 1,200-4,700 KB → should be ~50-200 KB each
```

### 2. Image Processing Strategy

#### Option A: Batch Process Existing Images (Recommended First Step)

Use a tool like **ImageMagick** or **sharp** (Node.js) to batch process all images:

```bash
# Install ImageMagick
# Windows: Download from https://imagemagick.org/
# macOS: brew install imagemagick
# Linux: sudo apt-get install imagemagick

# Example commands for hero images (run from image directory):
magick convert input.jpg -resize 1920x1080^ -gravity center -extent 1920x1080 -quality 75 -strip output.jpg
magick convert input.jpg -resize 1200x675^ -gravity center -extent 1200x675 -quality 75 -strip output-medium.jpg
magick convert input.jpg -resize 800x450^ -gravity center -extent 800x450 -quality 75 -strip output-small.jpg

# Convert to WebP (even better compression):
magick convert output.jpg -quality 75 output.webp
```

#### Option B: Use Python/Django to Process (Long-term Solution)

Install Pillow if not already installed:
```bash
pip install Pillow
```

Create a Django management command to process images:

```python
# experiences/management/commands/optimize_images.py
from django.core.management.base import BaseCommand
from PIL import Image
import io
from experiences.models import Destination, Experience
from django.core.files.uploadedfile import InMemoryUploadedFile

class Command(BaseCommand):
    help = 'Optimize all images in the system'

    def handle(self, *args, **kwargs):
        self.optimize_destinations()
        self.optimize_experiences()

    def optimize_image(self, image_field, sizes):
        """
        Optimize an image and create multiple sizes
        sizes: dict like {'large': (1920, 1080), 'medium': (1200, 675), 'small': (800, 450)}
        """
        if not image_field:
            return

        try:
            img = Image.open(image_field)

            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background

            # For each size, create optimized version
            for size_name, (width, height) in sizes.items():
                # Resize image maintaining aspect ratio
                img_copy = img.copy()
                img_copy.thumbnail((width, height), Image.Resampling.LANCZOS)

                # Save to BytesIO
                output = io.BytesIO()
                img_copy.save(output, format='JPEG', quality=75, optimize=True)
                output.seek(0)

                self.stdout.write(f"Optimized {image_field.name} to {size_name}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing {image_field.name}: {str(e)}'))

    def optimize_destinations(self):
        destinations = Destination.objects.exclude(image='')
        for dest in destinations:
            self.stdout.write(f'Processing destination: {dest.name}')
            self.optimize_image(dest.image, {
                'large': (1920, 1080),
                'medium': (1200, 675),
                'small': (800, 450)
            })

    def optimize_experiences(self):
        experiences = Experience.objects.exclude(main_image='')
        for exp in experiences:
            self.stdout.write(f'Processing experience: {exp.title}')
            self.optimize_image(exp.main_image, {
                'medium': (800, 450),
                'small': (400, 225)
            })
```

Run with:
```bash
python manage.py optimize_images
```

#### Option C: Use DigitalOcean Spaces CDN Features

DigitalOcean Spaces supports image transformations via URL parameters (if enabled). Check if your Space has this feature enabled.

### 3. Implement Responsive Images in Templates

Already done! The templates now include:
- `width` and `height` attributes to prevent layout shift
- `fetchpriority="high"` on the first hero image
- `loading="lazy"` on below-the-fold images

Next step: Add `srcset` for responsive images once you have multiple sizes:

```html
<img
    src="{{ destination.image.url }}"
    srcset="{{ destination.image_small.url }} 800w,
            {{ destination.image_medium.url }} 1200w,
            {{ destination.image_large.url }} 1920w"
    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 80vw, 1920px"
    alt="{{ destination.name }}"
    width="1920"
    height="1080"
    fetchpriority="high">
```

### 4. Set Up Proper Caching Headers

In your DigitalOcean Spaces bucket settings, set:
- **Cache-Control**: `public, max-age=31536000, immutable` (1 year)
- **Content-Type**: Ensure correct MIME types

### 5. Consider Using django-storages with Optimizations

Update your `settings.py`:

```python
# Add to settings.py
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=31536000',
}

# Install django-storages if not already
# pip install django-storages boto3
```

## Performance Targets

After optimization, you should achieve:

| Metric | Current | Target | Priority |
|--------|---------|--------|----------|
| LCP | 88s | <2.5s | CRITICAL |
| Image Sizes | 30MB | <500KB total | CRITICAL |
| Performance Score | 42 | >90 | HIGH |
| CLS | 0.596 | <0.1 | MEDIUM |

## What We've Already Fixed

✅ Removed lazy loading from LCP hero image
✅ Added `width` and `height` to prevent layout shift
✅ Added `fetchpriority="high"` to first hero image
✅ Optimized Google Tag Manager loading
✅ Added preconnect to DigitalOcean Spaces
✅ Fixed accessibility issues (button labels)
✅ Improved color contrast

## Next Steps (Priority Order)

1. **URGENT**: Optimize all images in DigitalOcean Spaces (use Option A or B above)
2. Implement srcset for responsive images
3. Enable CDN/compression on DigitalOcean Spaces
4. Consider using a service like Cloudinary or ImageKit for automatic optimization
5. Set up automated image optimization pipeline for new uploads

## Testing Your Changes

After optimizing images:

1. Test locally first
2. Deploy to production
3. Run PageSpeed Insights again: https://pagespeed.web.dev/
4. Target metrics:
   - Performance: >90
   - LCP: <2.5s
   - Total page size: <2MB

## Tools & Resources

- ImageMagick: https://imagemagick.org/
- Sharp (Node.js): https://sharp.pixelplumbing.com/
- Pillow (Python): https://python-pillow.org/
- WebP Converter: https://developers.google.com/speed/webp
- PageSpeed Insights: https://pagespeed.web.dev/
