from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

class Command(BaseCommand):
    help = 'Mark all accounts app migrations as unapplied'

    def handle(self, *args, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM django_migrations WHERE app = %s", ['accounts'])
        self.stdout.write(self.style.SUCCESS('Marked accounts migrations as unapplied'))