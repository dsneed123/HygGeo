#!/usr/bin/env python3
"""
Quick script to check OAuth configuration
Run: python check_oauth_config.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HygGeo.settings')
django.setup()

from django.contrib.sites.models import Site
from django.conf import settings
from allauth.socialaccount.models import SocialApp

print("=" * 60)
print("DJANGO OAUTH CONFIGURATION CHECK")
print("=" * 60)

# Check Site configuration
print(f"\n✓ SITE_ID: {settings.SITE_ID}")
site = Site.objects.get(id=settings.SITE_ID)
print(f"✓ Site Domain: {site.domain}")

# Expected redirect URI
redirect_uri = f"http://{site.domain}/accounts/google/login/callback/"
print(f"\n✓ Expected Redirect URI:")
print(f"  {redirect_uri}")

# Check if Google social app is configured
print(f"\n--- Checking Google Social App ---")
try:
    google_apps = SocialApp.objects.filter(provider='google')
    if google_apps.exists():
        for app in google_apps:
            print(f"✓ Google App Found: {app.name}")
            print(f"  Client ID: {app.client_id[:20]}..." if app.client_id else "  Client ID: NOT SET")
            print(f"  Client Secret: {'SET' if app.secret else 'NOT SET'}")
            print(f"  Sites: {', '.join([str(s.domain) for s in app.sites.all()])}")
    else:
        print("⚠ WARNING: No Google SocialApp configured in Django admin!")
        print("\nYou need to:")
        print("1. Go to http://localhost:8000/admin/")
        print("2. Go to 'Social applications'")
        print("3. Add a new application:")
        print("   - Provider: Google")
        print("   - Name: Google OAuth")
        print("   - Client ID: (from Google Console)")
        print("   - Secret key: (from Google Console)")
        print("   - Sites: Select 'localhost:8000'")
except Exception as e:
    print(f"⚠ Error checking SocialApp: {e}")

# Check environment variables
print(f"\n--- Checking Environment Variables ---")
client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')

if client_id:
    print(f"✓ GOOGLE_CLIENT_ID: {client_id[:20]}...")
else:
    print("⚠ GOOGLE_CLIENT_ID: NOT SET in environment")

if client_secret:
    print(f"✓ GOOGLE_CLIENT_SECRET: SET")
else:
    print("⚠ GOOGLE_CLIENT_SECRET: NOT SET in environment")

# Check settings
print(f"\n--- Checking Settings ---")
print(f"✓ LOGIN_REDIRECT_URL: {settings.LOGIN_REDIRECT_URL}")
print(f"✓ SOCIALACCOUNT_AUTO_SIGNUP: {settings.SOCIALACCOUNT_AUTO_SIGNUP}")

print("\n" + "=" * 60)
print("WHAT TO PUT IN GOOGLE CLOUD CONSOLE")
print("=" * 60)
print(f"\nAuthorized redirect URIs (add this EXACTLY):")
print(f"  {redirect_uri}")
print(f"\nAuthorized JavaScript origins:")
print(f"  http://{site.domain}")

print("\n" + "=" * 60)
print("CHECKLIST")
print("=" * 60)
print("[ ] Redirect URI in Google Console matches exactly (with trailing slash)")
print("[ ] JavaScript origin in Google Console is set")
print("[ ] Google SocialApp configured in Django admin")
print("[ ] Client ID and Secret set in .env file")
print("[ ] Saved changes in Google Console")
print("[ ] Waited 2-3 minutes after saving")
print("[ ] Tested in Incognito/Private mode")
print("\n")
