"""
Management command for creating email templates
Usage: python manage.py create_email_template --name "Welcome Email" --category welcome
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import EmailTemplate


class Command(BaseCommand):
    help = 'Create email templates'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, help='Template name')
        parser.add_argument('--category', type=str,
                          choices=['welcome', 'experiences', 'community', 'sustainability', 'newsletter', 'announcement', 'other'],
                          help='Template category')
        parser.add_argument('--subject', type=str, default='Welcome to HygGeo!', help='Email subject')
        parser.add_argument('--sample', action='store_true', help='Create sample templates')

    def handle(self, *args, **options):
        if options['sample']:
            self.create_sample_templates()
        else:
            if not options['name'] or not options['category']:
                self.stdout.write(self.style.ERROR('--name and --category are required when not using --sample'))
                return
            self.create_single_template(options)

    def create_single_template(self, options):
        template = EmailTemplate.objects.create(
            name=options['name'],
            category=options['category'],
            subject=options['subject'],
            html_content=self.get_default_html(),
            text_content=self.get_default_text(),
            available_merge_fields=['first_name', 'last_name', 'username', 'email', 'member_since']
        )

        self.stdout.write(
            self.style.SUCCESS(f'Created template: {template.name} (ID: {template.id})')
        )

    def create_sample_templates(self):
        """Create comprehensive sample templates"""
        templates = [
            {
                'name': 'Welcome New Members',
                'category': 'welcome',
                'subject': 'Welcome to HygGeo, {{first_name}}! 🌍',
                'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Welcome to HygGeo</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #4A7C59, #6B8E5A); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #4A7C59; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 30px; color: #666; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to HygGeo, {{first_name}}!</h1>
            <p>Your journey to sustainable travel starts here</p>
        </div>
        <div class="content">
            <h2>Hi {{first_name}},</h2>
            <p>We're thrilled to have you join our community of mindful travelers! HygGeo is all about combining the Danish concept of hygge with sustainable travel practices.</p>

            <h3>🌱 What you can do with HygGeo:</h3>
            <ul>
                <li>Discover eco-friendly experiences and destinations</li>
                <li>Connect with like-minded sustainable travelers</li>
                <li>Plan trips that align with your environmental values</li>
                <li>Share your own sustainable travel discoveries</li>
            </ul>

            <p>Your sustainability level: <strong>{{sustainability_level}}</strong></p>
            <p>Member since: <strong>{{member_since}}</strong></p>

            <a href="https://hyggeo.com/experiences/" class="button">Explore Experiences</a>

            <p>Ready to start your sustainable adventure? We recommend completing your travel preferences survey to get personalized recommendations!</p>

            <p>Happy travels!<br>The HygGeo Team 🌍</p>
        </div>
        <div class="footer">
            <p>This email was sent to {{email}}. If you no longer wish to receive these emails, you can unsubscribe at any time.</p>
        </div>
    </div>
</body>
</html>
                ''',
                'text_content': '''
Welcome to HygGeo, {{first_name}}!

Hi {{first_name}},

We're thrilled to have you join our community of mindful travelers! HygGeo is all about combining the Danish concept of hygge with sustainable travel practices.

What you can do with HygGeo:
• Discover eco-friendly experiences and destinations
• Connect with like-minded sustainable travelers
• Plan trips that align with your environmental values
• Share your own sustainable travel discoveries

Your sustainability level: {{sustainability_level}}
Member since: {{member_since}}

Visit https://hyggeo.com/experiences/ to explore experiences.

Ready to start your sustainable adventure? We recommend completing your travel preferences survey to get personalized recommendations!

Happy travels!
The HygGeo Team 🌍

This email was sent to {{email}}. If you no longer wish to receive these emails, you can unsubscribe at any time.
                '''
            },
            {
                'name': 'New Experiences Weekly',
                'category': 'experiences',
                'subject': 'New sustainable experiences this week! 🌿',
                'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>New Experiences</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #6B8E5A; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .experience { background: white; padding: 20px; margin: 15px 0; border-left: 4px solid #4A7C59; border-radius: 5px; }
        .button { display: inline-block; background: #4A7C59; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>New Experiences This Week!</h1>
            <p>Fresh sustainable adventures for {{first_name}}</p>
        </div>
        <div class="content">
            <h2>Hello {{first_name}},</h2>
            <p>We've added some amazing new sustainable experiences that match your {{sustainability_level}} travel style!</p>

            <div class="experience">
                <h3>🌲 Forest Bathing Retreat</h3>
                <p>Reconnect with nature in our mindful forest immersion experience. Perfect for slow travel enthusiasts.</p>
                <a href="https://hyggeo.com/experiences/" class="button">Learn More</a>
            </div>

            <div class="experience">
                <h3>🚲 Eco-Cycling Tours</h3>
                <p>Explore local communities by bike while supporting sustainable transportation initiatives.</p>
                <a href="https://hyggeo.com/experiences/" class="button">Learn More</a>
            </div>

            <p>You've been a member since {{member_since}} and have created {{trips_count}} sustainable trips so far!</p>

            <p>Keep exploring mindfully!<br>The HygGeo Team</p>
        </div>
    </div>
</body>
</html>
                ''',
                'text_content': '''
New Experiences This Week!

Hello {{first_name}},

We've added some amazing new sustainable experiences that match your {{sustainability_level}} travel style!

🌲 Forest Bathing Retreat
Reconnect with nature in our mindful forest immersion experience. Perfect for slow travel enthusiasts.

🚲 Eco-Cycling Tours
Explore local communities by bike while supporting sustainable transportation initiatives.

You've been a member since {{member_since}} and have created {{trips_count}} sustainable trips so far!

Visit https://hyggeo.com/experiences/ to explore all experiences.

Keep exploring mindfully!
The HygGeo Team
                '''
            },
            {
                'name': 'Community Update Monthly',
                'category': 'community',
                'subject': 'Your HygGeo community update for this month 📬',
                'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Community Update</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #4A7C59; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .stat { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; text-align: center; }
        .stat-number { font-size: 24px; font-weight: bold; color: #4A7C59; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Community Update</h1>
            <p>What's happening in the HygGeo community</p>
        </div>
        <div class="content">
            <h2>Hi {{first_name}},</h2>
            <p>Here's what's been happening in our sustainable travel community this month:</p>

            <div class="stat">
                <div class="stat-number">127</div>
                <div>New sustainable experiences added</div>
            </div>

            <div class="stat">
                <div class="stat-number">89</div>
                <div>Eco-friendly trips planned</div>
            </div>

            <div class="stat">
                <div class="stat-number">{{trips_count}}</div>
                <div>Your sustainable trips created</div>
            </div>

            <h3>🌟 Your Impact</h3>
            <p>As a {{sustainability_level}} traveler, you're part of a movement that's making travel more mindful and sustainable. Keep up the great work!</p>

            <p>Thanks for being part of our community since {{member_since}}!</p>

            <p>Sustainable regards,<br>The HygGeo Team</p>
        </div>
    </div>
</body>
</html>
                ''',
                'text_content': '''
Community Update

Hi {{first_name}},

Here's what's been happening in our sustainable travel community this month:

📊 Community Stats:
• 127 new sustainable experiences added
• 89 eco-friendly trips planned
• {{trips_count}} sustainable trips you've created

🌟 Your Impact
As a {{sustainability_level}} traveler, you're part of a movement that's making travel more mindful and sustainable. Keep up the great work!

Thanks for being part of our community since {{member_since}}!

Sustainable regards,
The HygGeo Team
                '''
            }
        ]

        created_count = 0
        for template_data in templates:
            template, created = EmailTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults={
                    'category': template_data['category'],
                    'subject': template_data['subject'],
                    'html_content': template_data['html_content'],
                    'text_content': template_data['text_content'],
                    'available_merge_fields': ['first_name', 'last_name', 'username', 'email', 'sustainability_level', 'member_since', 'trips_count']
                }
            )

            if created:
                created_count += 1
                self.stdout.write(f'Created: {template.name}')
            else:
                self.stdout.write(f'Already exists: {template.name}')

        self.stdout.write(
            self.style.SUCCESS(f'\\nCreated {created_count} new email templates!')
        )

    def get_default_html(self):
        return '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>HygGeo Email</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #4A7C59; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Hello {{first_name}}!</h1>
        </div>
        <div class="content">
            <p>This is a sample email template. Customize this content for your campaign.</p>
            <p>Available merge fields: {{first_name}}, {{last_name}}, {{username}}, {{email}}, {{member_since}}</p>
        </div>
    </div>
</body>
</html>
        '''

    def get_default_text(self):
        return '''
Hello {{first_name}}!

This is a sample email template. Customize this content for your campaign.

Available merge fields: {{first_name}}, {{last_name}}, {{username}}, {{email}}, {{member_since}}

Best regards,
The HygGeo Team
        '''