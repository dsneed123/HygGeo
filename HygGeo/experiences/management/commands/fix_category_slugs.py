"""
Management command to fix broken category slugs
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from experiences.models import Category


class Command(BaseCommand):
    help = 'Fix category slugs that have leading or trailing dashes'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting category slug fix...'))

        fixed_count = 0
        error_count = 0

        categories = Category.objects.all()

        for category in categories:
            old_slug = category.slug

            # Check if slug has leading or trailing dashes
            if old_slug.startswith('-') or old_slug.endswith('-'):
                # Generate new slug from name
                new_slug = slugify(category.name).strip('-')

                # If slug is empty, skip
                if not new_slug:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Cannot generate slug for category: {category.name} (id: {category.id})'
                        )
                    )
                    error_count += 1
                    continue

                # Check if new slug already exists
                if Category.objects.filter(slug=new_slug).exclude(id=category.id).exists():
                    # Append category id to make it unique
                    new_slug = f'{new_slug}-{category.id}'

                # Update the slug
                category.slug = new_slug
                try:
                    category.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Fixed: "{old_slug}" → "{new_slug}" (Category: {category.name})'
                        )
                    )
                    fixed_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error fixing {category.name}: {str(e)}'
                        )
                    )
                    error_count += 1

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'Fixed: {fixed_count} categories'))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'Errors: {error_count} categories'))
        self.stdout.write(self.style.SUCCESS('Category slug fix complete!'))
