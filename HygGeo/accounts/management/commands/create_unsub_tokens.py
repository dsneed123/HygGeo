from django.core.management.base import BaseCommand
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Generate unsubscribe tokens for all user profiles that don\'t have one'

    def handle(self, *args, **options):
        # Get all profiles without tokens
        profiles_without_tokens = UserProfile.objects.filter(unsubscribe_token__isnull=True)
        count_without = profiles_without_tokens.count()

        # Also process all profiles to ensure tokens exist
        all_profiles = UserProfile.objects.all()
        total_count = all_profiles.count()

        generated_count = 0

        for profile in all_profiles:
            if not profile.unsubscribe_token:
                profile.save()  # This will auto-generate the token
                generated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated {generated_count} unsubscribe tokens out of {total_count} total profiles'
            )
        )

        if generated_count == 0:
            self.stdout.write(
                self.style.WARNING('All profiles already have unsubscribe tokens!')
            )