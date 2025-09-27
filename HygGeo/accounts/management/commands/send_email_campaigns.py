"""
Management command for sending scheduled email campaigns
Usage: python manage.py send_email_campaigns
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from accounts.models import EmailCampaign, EmailLog
from accounts.admin import process_email_campaign


class Command(BaseCommand):
    help = 'Send scheduled email campaigns'

    def add_arguments(self, parser):
        parser.add_argument(
            '--campaign-id',
            type=int,
            help='Send specific campaign by ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force send campaigns even if not scheduled',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Starting email campaign processor...'))

        # Get campaigns to send
        if options['campaign_id']:
            campaigns = EmailCampaign.objects.filter(id=options['campaign_id'])
            if not campaigns.exists():
                self.stdout.write(self.style.ERROR(f'Campaign with ID {options["campaign_id"]} not found'))
                return
        elif options['force']:
            campaigns = EmailCampaign.objects.filter(status='draft')
        else:
            # Get scheduled campaigns
            now = timezone.now()
            campaigns = EmailCampaign.objects.filter(
                status='draft',
                scheduled_send__lte=now
            )

        if not campaigns.exists():
            self.stdout.write(self.style.WARNING('No campaigns to send'))
            return

        for campaign in campaigns:
            self.stdout.write(f'\n📧 Processing campaign: {campaign.name}')
            self.stdout.write(f'   Template: {campaign.template.name}')
            self.stdout.write(f'   Mode: {campaign.get_mode_display()}')
            self.stdout.write(f'   Recipients: {campaign.get_recipient_count()}')

            if options['dry_run']:
                self.stdout.write(self.style.WARNING('   [DRY RUN] Would send campaign'))
                continue

            try:
                # Update status
                campaign.status = 'sending'
                campaign.save()

                # Send emails
                sent_count = process_email_campaign(campaign)

                # Update final status
                campaign.status = 'completed'
                campaign.sent_at = timezone.now()
                campaign.save()

                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ Successfully sent to {sent_count} recipients')
                )

                # Show failure count if any
                if campaign.emails_failed > 0:
                    self.stdout.write(
                        self.style.WARNING(f'   ⚠️  {campaign.emails_failed} emails failed')
                    )

            except Exception as e:
                campaign.status = 'failed'
                campaign.save()

                self.stdout.write(
                    self.style.ERROR(f'   ❌ Campaign failed: {str(e)}')
                )

        self.stdout.write(self.style.SUCCESS('\n🎉 Email campaign processing complete!'))