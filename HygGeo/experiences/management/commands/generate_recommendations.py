# experiences/management/commands/generate_recommendations.py
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from experiences.recommendation_engine import RecommendationEngine, generate_recommendations_for_all_users

class Command(BaseCommand):
    help = 'Generate personalized recommendations for users based on their travel surveys'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Generate recommendations for a specific user ID',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Generate recommendations for a specific username',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Generate recommendations for all users with surveys',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Maximum number of recommendations per user (default: 20)',
        )

    def handle(self, *args, **options):
        engine = RecommendationEngine()

        if options['all']:
            self.stdout.write('Generating recommendations for all users...')
            total = generate_recommendations_for_all_users()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully generated {total} total recommendations')
            )

        elif options['user_id']:
            user_id = options['user_id']
            try:
                user = User.objects.get(id=user_id)
                recommendations = engine.generate_recommendations_for_user(
                    user_id, limit=options['limit']
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Generated {len(recommendations)} recommendations for user {user.username}'
                    )
                )
            except User.DoesNotExist:
                raise CommandError(f'User with ID {user_id} does not exist')

        elif options['username']:
            username = options['username']
            try:
                user = User.objects.get(username=username)
                recommendations = engine.generate_recommendations_for_user(
                    user.id, limit=options['limit']
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Generated {len(recommendations)} recommendations for {username}'
                    )
                )
            except User.DoesNotExist:
                raise CommandError(f'User with username {username} does not exist')

        else:
            self.stdout.write(
                self.style.ERROR(
                    'Please specify --all, --user-id, or --username'
                )
            )