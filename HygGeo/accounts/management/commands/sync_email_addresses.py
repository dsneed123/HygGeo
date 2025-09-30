from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from allauth.account.models import EmailAddress


class Command(BaseCommand):
    help = 'Sync User emails to allauth EmailAddress model'

    def handle(self, *args, **options):
        users = User.objects.exclude(email='')
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for user in users:
            email_lower = user.email.lower()

            # Check if email already exists for another user
            existing = EmailAddress.objects.filter(email=email_lower).first()

            if existing and existing.user != user:
                self.stdout.write(self.style.WARNING(
                    f'Skipped {user.username}: email {email_lower} already exists for user {existing.user.username}'
                ))
                skipped_count += 1
                continue

            # Get or create EmailAddress for this user
            ea, created = EmailAddress.objects.get_or_create(
                user=user,
                email=email_lower,
                defaults={
                    'verified': True,
                    'primary': True
                }
            )

            if created:
                created_count += 1
                self.stdout.write(f'Created EmailAddress for {user.username}: {user.email}')
            else:
                # Update if not verified or not primary
                if not ea.verified or not ea.primary:
                    ea.verified = True
                    ea.primary = True
                    ea.save()
                    updated_count += 1
                    self.stdout.write(f'Updated EmailAddress for {user.username}: {user.email}')

        self.stdout.write(self.style.SUCCESS(
            f'\nSync complete: {created_count} created, {updated_count} updated, {skipped_count} skipped'
        ))