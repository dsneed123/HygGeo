#!/usr/bin/env python3
"""
Fix Google OAuth for production
Run this on your production server: python3 fix_production_oauth.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HygGeo.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

print("=" * 60)
print("FIXING GOOGLE OAUTH FOR PRODUCTION")
print("=" * 60)

# Get or create the production site
try:
    production_site = Site.objects.get(domain='hyggeo.com')
    print(f"\n✓ Found production site: {production_site.domain} (ID: {production_site.id})")
except Site.DoesNotExist:
    production_site = Site.objects.create(
        domain='hyggeo.com',
        name='HygGeo'
    )
    print(f"\n✓ Created production site: {production_site.domain} (ID: {production_site.id})")

# Check for Google OAuth app
try:
    google_app = SocialApp.objects.get(provider='google')
    print(f"\n✓ Found Google OAuth app: {google_app.name}")
    print(f"  Client ID: {google_app.client_id[:30]}...")
    print(f"  Currently linked to: {[s.domain for s in google_app.sites.all()]}")

    # Add production site if not already linked
    if production_site not in google_app.sites.all():
        google_app.sites.add(production_site)
        print(f"\n✓ Linked Google app to production site!")
    else:
        print(f"\n✓ Google app already linked to production site")

    print(f"  Now linked to: {[s.domain for s in google_app.sites.all()]}")

except SocialApp.DoesNotExist:
    print("\n⚠ ERROR: No Google OAuth app found in database!")
    print("\nYou need to create it:")
    print("1. Go to https://hyggeo.com/admin/")
    print("2. Go to 'Social applications'")
    print("3. Add a new application:")
    print("   - Provider: Google")
    print("   - Name: Google OAuth")
    print("   - Client ID: (your Google client ID)")
    print("   - Secret key: (your Google client secret)")
    print(f"   - Sites: Select '{production_site.domain}'")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ SUCCESS! Google OAuth is configured for production")
print("=" * 60)
print("\nExpected redirect URI in Google Console:")
print(f"  https://hyggeo.com/accounts/google/login/callback/")
print("\nRestart your production server for changes to take effect.")
