"""
Management command to fix broken slugs across all models
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from experiences.models import Category, ExperienceType


class Command(BaseCommand):
    help = 'Fix all slugs that have leading or trailing dashes'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting comprehensive slug fix...'))

        total_fixed = 0
        total_errors = 0

        # Fix Categories
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.WARNING('Fixing Category slugs...'))
        fixed, errors = self.fix_model_slugs(Category)
        total_fixed += fixed
        total_errors += errors

        # Fix Experience Types
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.WARNING('Fixing ExperienceType slugs...'))
        fixed, errors = self.fix_model_slugs(ExperienceType)
        total_fixed += fixed
        total_errors += errors

        # Summary
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS(f'TOTAL Fixed: {total_fixed} slugs'))
        if total_errors > 0:
            self.stdout.write(self.style.WARNING(f'TOTAL Errors: {total_errors} slugs'))
        self.stdout.write(self.style.SUCCESS('Comprehensive slug fix complete!'))

    def fix_model_slugs(self, model):
        """Fix slugs for a given model"""
        fixed_count = 0
        error_count = 0

        objects = model.objects.all()

        for obj in objects:
            old_slug = obj.slug

            # Check if slug has leading or trailing dashes or is otherwise malformed
            if old_slug.startswith('-') or old_slug.endswith('-') or '--' in old_slug:
                # Generate new slug from name
                new_slug = slugify(obj.name).strip('-')

                # Replace multiple dashes with single dash
                while '--' in new_slug:
                    new_slug = new_slug.replace('--', '-')

                # If slug is empty, skip
                if not new_slug:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  Cannot generate slug for {model.__name__}: {obj.name} (id: {obj.id})'
                        )
                    )
                    error_count += 1
                    continue

                # Check if new slug already exists
                if model.objects.filter(slug=new_slug).exclude(id=obj.id).exists():
                    # Append object id to make it unique
                    new_slug = f'{new_slug}-{obj.id}'

                # Update the slug
                obj.slug = new_slug
                try:
                    obj.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  Fixed: "{old_slug}" -> "{new_slug}" ({model.__name__}: {obj.name})'
                        )
                    )
                    fixed_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  Error fixing {obj.name}: {str(e)}'
                        )
                    )
                    error_count += 1

        if fixed_count == 0 and error_count == 0:
            self.stdout.write(self.style.SUCCESS(f'  All {model.__name__} slugs are clean!'))

        return fixed_count, error_count
