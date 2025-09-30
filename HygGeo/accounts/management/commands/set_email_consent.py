from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile
import secrets


class Command(BaseCommand):
    help = 'Set email consent for all existing users and generate unsubscribe tokens'

    def add_arguments(self, parser):
        parser.add_argument(
            '--consent',
            type=str,
            choices=['true', 'false'],
            default='true',
            help='Set email consent to true or false (default: true)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update all users even if they already have consent set'
        )

    def handle(self, *args, **options):
        consent_value = options['consent'].lower() == 'true'
        force_update = options['force']

        self.stdout.write(
            self.style.SUCCESS(
                f'Setting email consent to {consent_value} for existing users...'
            )
        )

        # Get all users
        users = User.objects.all()
        updated_count = 0
        created_count = 0

        for user in users:
            # Get or create user profile
            profile, created = UserProfile.objects.get_or_create(user=user)

            if created:
                created_count += 1
                # Set defaults for new profile
                profile.email_consent = consent_value
                if not profile.unsubscribe_token:
                    profile.unsubscribe_token = secrets.token_urlsafe(32)
                profile.save()

                self.stdout.write(
                    f'Created profile for {user.username} with email_consent={consent_value}'
                )
            else:
                # Update existing profile if needed
                needs_update = False

                if force_update or profile.email_consent != consent_value:
                    profile.email_consent = consent_value
                    needs_update = True

                if not profile.unsubscribe_token:
                    profile.unsubscribe_token = secrets.token_urlsafe(32)
                    needs_update = True

                if needs_update:
                    profile.save()
                    updated_count += 1

                    if force_update:
                        self.stdout.write(
                            f'Updated {user.username}: email_consent={consent_value}'
                        )
                    elif not profile.unsubscribe_token:
                        self.stdout.write(
                            f'Added unsubscribe token for {user.username}'
                        )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary:\n'
                f'- Created {created_count} new profiles\n'
                f'- Updated {updated_count} existing profiles\n'
                f'- Total users processed: {users.count()}\n'
                f'- Email consent set to: {consent_value}'
            )
        )

        # Show stats
        consented_users = UserProfile.objects.filter(email_consent=True).count()
        total_profiles = UserProfile.objects.count()

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCurrent stats:\n'
                f'- Users with email consent: {consented_users}\n'
                f'- Total user profiles: {total_profiles}\n'
                f'- Consent rate: {(consented_users/total_profiles*100):.1f}%'
            )
        )