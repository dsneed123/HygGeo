"""
Django management command to migrate image URLs from DigitalOcean Spaces to Cloudflare R2.

This command updates all image field URLs in the database to point to the new R2 bucket.
It does NOT upload files - assumes files are already uploaded to R2 in the same structure.

Usage:
    python manage.py migrate_to_r2 --dry-run  # Preview changes
    python manage.py migrate_to_r2            # Apply changes
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from experiences.models import Destination, Provider, Experience, Accommodation, TravelBlog
from accounts.models import UserProfile, Trip

User = get_user_model()


class Command(BaseCommand):
    help = 'Migrate image URLs from DigitalOcean Spaces to Cloudflare R2'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without applying them',
        )
        parser.add_argument(
            '--old-domain',
            type=str,
            default='hygoe-images.sfo3.cdn.digitaloceanspaces.com',
            help='Old DigitalOcean Spaces domain (default: hygoe-images.sfo3.cdn.digitaloceanspaces.com)',
        )
        parser.add_argument(
            '--new-domain',
            type=str,
            default='pub-cfe28881db15475f88c173572f38ab10.r2.dev',
            help='New Cloudflare R2 public domain (default: pub-cfe28881db15475f88c173572f38ab10.r2.dev)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        old_domain = options['old_domain']
        new_domain = options['new_domain']

        self.stdout.write(self.style.WARNING(f'\n{"="*70}'))
        self.stdout.write(self.style.WARNING('MIGRATING IMAGE URLS FROM DIGITALOCEAN SPACES TO CLOUDFLARE R2'))
        self.stdout.write(self.style.WARNING(f'{"="*70}\n'))

        if dry_run:
            self.stdout.write(self.style.SUCCESS('DRY RUN MODE - No changes will be saved\n'))
        else:
            self.stdout.write(self.style.ERROR('LIVE MODE - Changes will be saved to database\n'))

        self.stdout.write(f'Old domain: {old_domain}')
        self.stdout.write(f'New domain: {new_domain}\n')

        # Track statistics
        stats = {
            'destinations': 0,
            'providers': 0,
            'experiences': 0,
            'accommodations': 0,
            'blogs': 0,
            'profiles': 0,
            'trips': 0,
        }

        # Migrate Destinations
        self.stdout.write(self.style.HTTP_INFO('\n[1/7] Processing Destinations...'))
        for destination in Destination.objects.exclude(image=''):
            if old_domain in str(destination.image):
                old_url = str(destination.image)
                new_url = old_url.replace(old_domain, new_domain)

                self.stdout.write(f'  Destination "{destination.name}":')
                self.stdout.write(f'    Old: {old_url}')
                self.stdout.write(f'    New: {new_url}')

                if not dry_run:
                    destination.image.name = new_url.split('/')[-2] + '/' + new_url.split('/')[-1]
                    destination.save(update_fields=['image'])

                stats['destinations'] += 1

        # Migrate Providers
        self.stdout.write(self.style.HTTP_INFO('\n[2/7] Processing Providers...'))
        for provider in Provider.objects.exclude(logo=''):
            if old_domain in str(provider.logo):
                old_url = str(provider.logo)
                new_url = old_url.replace(old_domain, new_domain)

                self.stdout.write(f'  Provider "{provider.name}":')
                self.stdout.write(f'    Old: {old_url}')
                self.stdout.write(f'    New: {new_url}')

                if not dry_run:
                    provider.logo.name = new_url.split('/')[-2] + '/' + new_url.split('/')[-1]
                    provider.save(update_fields=['logo'])

                stats['providers'] += 1

        # Migrate Experiences
        self.stdout.write(self.style.HTTP_INFO('\n[3/7] Processing Experiences...'))
        for experience in Experience.objects.exclude(main_image=''):
            if old_domain in str(experience.main_image):
                old_url = str(experience.main_image)
                new_url = old_url.replace(old_domain, new_domain)

                self.stdout.write(f'  Experience "{experience.title}":')
                self.stdout.write(f'    Old: {old_url}')
                self.stdout.write(f'    New: {new_url}')

                if not dry_run:
                    experience.main_image.name = new_url.split('/')[-2] + '/' + new_url.split('/')[-1]
                    experience.save(update_fields=['main_image'])

                stats['experiences'] += 1

        # Migrate Accommodations
        self.stdout.write(self.style.HTTP_INFO('\n[4/7] Processing Accommodations...'))
        for accommodation in Accommodation.objects.exclude(main_image=''):
            if old_domain in str(accommodation.main_image):
                old_url = str(accommodation.main_image)
                new_url = old_url.replace(old_domain, new_domain)

                self.stdout.write(f'  Accommodation "{accommodation.name}":')
                self.stdout.write(f'    Old: {old_url}')
                self.stdout.write(f'    New: {new_url}')

                if not dry_run:
                    accommodation.main_image.name = new_url.split('/')[-2] + '/' + new_url.split('/')[-1]
                    accommodation.save(update_fields=['main_image'])

                stats['accommodations'] += 1

        # Migrate Travel Blogs
        self.stdout.write(self.style.HTTP_INFO('\n[5/7] Processing Travel Blogs...'))
        for blog in TravelBlog.objects.exclude(featured_image=''):
            if old_domain in str(blog.featured_image):
                old_url = str(blog.featured_image)
                new_url = old_url.replace(old_domain, new_domain)

                self.stdout.write(f'  Blog "{blog.title}":')
                self.stdout.write(f'    Old: {old_url}')
                self.stdout.write(f'    New: {new_url}')

                if not dry_run:
                    blog.featured_image.name = new_url.split('/')[-2] + '/' + new_url.split('/')[-1]
                    blog.save(update_fields=['featured_image'])

                stats['blogs'] += 1

        # Migrate User Profiles
        self.stdout.write(self.style.HTTP_INFO('\n[6/7] Processing User Profiles...'))
        for profile in UserProfile.objects.exclude(avatar=''):
            if old_domain in str(profile.avatar):
                old_url = str(profile.avatar)
                new_url = old_url.replace(old_domain, new_domain)

                self.stdout.write(f'  Profile "{profile.user.username}":')
                self.stdout.write(f'    Old: {old_url}')
                self.stdout.write(f'    New: {new_url}')

                if not dry_run:
                    profile.avatar.name = new_url.split('/')[-2] + '/' + new_url.split('/')[-1]
                    profile.save(update_fields=['avatar'])

                stats['profiles'] += 1

        # Migrate Trips
        self.stdout.write(self.style.HTTP_INFO('\n[7/7] Processing Trips...'))
        for trip in Trip.objects.exclude(trip_image=''):
            if old_domain in str(trip.trip_image):
                old_url = str(trip.trip_image)
                new_url = old_url.replace(old_domain, new_domain)

                self.stdout.write(f'  Trip "{trip.title}":')
                self.stdout.write(f'    Old: {old_url}')
                self.stdout.write(f'    New: {new_url}')

                if not dry_run:
                    trip.trip_image.name = new_url.split('/')[-2] + '/' + new_url.split('/')[-1]
                    trip.save(update_fields=['trip_image'])

                stats['trips'] += 1

        # Print summary
        self.stdout.write(self.style.WARNING(f'\n{"="*70}'))
        self.stdout.write(self.style.WARNING('MIGRATION SUMMARY'))
        self.stdout.write(self.style.WARNING(f'{"="*70}\n'))

        total = sum(stats.values())
        for model_name, count in stats.items():
            if count > 0:
                self.stdout.write(f'  {model_name.capitalize()}: {count} updated')

        self.stdout.write(f'\n  TOTAL: {total} images migrated')

        if dry_run:
            self.stdout.write(self.style.SUCCESS('\nDRY RUN COMPLETE - No changes were saved'))
            self.stdout.write(self.style.WARNING('Run without --dry-run to apply changes'))
        else:
            self.stdout.write(self.style.SUCCESS('\nMIGRATION COMPLETE - All URLs updated in database'))

        self.stdout.write(self.style.WARNING(f'\n{"="*70}\n'))
