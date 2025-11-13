# Google OAuth Setup Guide for HygGeo

Your Django application is already configured for Google OAuth! You just need to set up Google OAuth credentials.

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: `HygGeo` (or your preferred name)
4. Click "Create"

## Step 2: Enable Google+ API

1. In the Google Cloud Console, select your project
2. Go to "APIs & Services" → "Library"
3. Search for "Google+ API"
4. Click on it and press "Enable"
5. Also search for "Google People API" and enable it

## Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Select "External" (unless you have a Google Workspace)
3. Click "Create"

### Fill in the App Information:
- **App name**: HygGeo
- **User support email**: Your email
- **App logo**: Upload your logo (optional)
- **Application home page**: `https://hyggeo.com` (or your domain)
- **Authorized domains**:
  - Add `hyggeo.com` (your production domain)
  - For local testing, you don't need to add `localhost`
- **Developer contact email**: Your email

4. Click "Save and Continue"

### Scopes Section:
1. Click "Add or Remove Scopes"
2. Select these scopes:
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`
   - `openid`
3. Click "Update" → "Save and Continue"

### Test Users (for development):
1. Add your email and any test users
2. Click "Save and Continue"

## Step 4: Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Select "Web application"
4. Enter name: `HygGeo Web Client`

### Configure Authorized JavaScript origins:
For **Development**:
- `http://localhost:8000`
- `http://127.0.0.1:8000`

For **Production**:
- `https://hyggeo.com`
- `https://www.hyggeo.com`

### Configure Authorized redirect URIs:
For **Development**:
- `http://localhost:8000/accounts/google/login/callback/`
- `http://127.0.0.1:8000/accounts/google/login/callback/`

For **Production**:
- `https://hyggeo.com/accounts/google/login/callback/`
- `https://www.hyggeo.com/accounts/google/login/callback/`

5. Click "Create"

## Step 5: Copy Your Credentials

After creating, you'll see:
- **Client ID** (looks like: `123456789-abcdefghijk.apps.googleusercontent.com`)
- **Client Secret** (looks like: `GOCSPX-xxxxxxxxxxxxx`)

**IMPORTANT**: Keep these secret!

## Step 6: Add Credentials to Your Environment

### For Local Development:

Create a `.env` file in your project root (if you don't have one):

```bash
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

### For Production (DigitalOcean):

1. Go to your DigitalOcean App Platform dashboard
2. Select your app
3. Go to "Settings" → "App-Level Environment Variables"
4. Add two new variables:
   - `GOOGLE_CLIENT_ID` = your_client_id
   - `GOOGLE_CLIENT_SECRET` = your_client_secret
5. Click "Save"
6. Redeploy your app

## Step 7: Update Django Site Settings

1. Run your Django shell:
```bash
python manage.py shell
```

2. Update the Site object:
```python
from django.contrib.sites.models import Site

# Get or create the site
site = Site.objects.get(id=3)  # Your SITE_ID from settings.py

# Update for production
site.domain = 'hyggeo.com'
site.name = 'HygGeo'
site.save()

# Verify
print(f"Site ID: {site.id}, Domain: {site.domain}, Name: {site.name}")
```

If you need to check your SITE_ID, run:
```python
from django.conf import settings
print(settings.SITE_ID)
```

## Step 8: Test Google Login

### For Local Development:

1. Start your Django server:
```bash
python manage.py runserver
```

2. Go to: `http://localhost:8000/accounts/login/`
3. Click "Continue with Google"
4. Sign in with your Google account
5. You should be redirected to your home page

### For Production:

1. Go to: `https://hyggeo.com/accounts/login/`
2. Click "Continue with Google"
3. Sign in with your Google account
4. You should be redirected to your home page

## Troubleshooting

### Error: "redirect_uri_mismatch"
- Check that your redirect URI exactly matches what's in Google Console
- Make sure to include the trailing slash: `/accounts/google/login/callback/`
- Verify the domain matches (http vs https, www vs non-www)

### Error: "invalid_client"
- Check your `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correct
- Make sure there are no extra spaces or quotes
- Verify the credentials are from the same OAuth client

### Google Sign-in button doesn't appear
- Check that `django-allauth` is installed: `pip list | grep django-allauth`
- Verify `SITE_ID = 3` in settings.py matches your database
- Check that social account templates are loading: `{% load socialaccount %}`

### Error: "Site matching query does not exist"
- Your SITE_ID in settings.py doesn't match the database
- Run the Django shell commands in Step 7 to create/update the site

### Users get logged in but profile data is missing
- Check that `SOCIALACCOUNT_PROVIDERS` in settings.py includes the scopes:
  ```python
  'SCOPE': ['profile', 'email']
  ```

## Security Best Practices

1. **Never commit credentials to Git**
   - Add `.env` to your `.gitignore`
   - Use environment variables in production

2. **Use HTTPS in production**
   - Google OAuth requires HTTPS for production
   - Only use HTTP for local development

3. **Restrict authorized domains**
   - Only add domains you control
   - Remove localhost URLs before going to production

4. **Regularly rotate secrets**
   - Change your client secret periodically
   - Revoke old credentials in Google Console

## What's Already Configured

Your Django app already has:
- ✅ `django-allauth` installed
- ✅ Google provider configured
- ✅ Authentication backends set up
- ✅ URL routes configured (`/accounts/google/login/callback/`)
- ✅ Google login buttons on login and signup pages
- ✅ Settings configured to read from environment variables

You just need to:
1. Create Google OAuth credentials (Steps 1-5)
2. Add them to your environment (Step 6)
3. Update Site settings (Step 7)
4. Test! (Step 8)

## Additional Features

### Auto-create UserProfile
When users sign up with Google, django-allauth will automatically:
- Create a User account
- Use their Google email
- Use their Google name (first_name, last_name)
- Set `email_verified=True` (since Google verified it)

You may want to add a signal to auto-create UserProfile:

```python
# In accounts/signals.py (create if it doesn't exist)
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added
from .models import UserProfile

@receiver(social_account_added)
def create_profile_for_social_user(sender, request, sociallogin, **kwargs):
    """Create UserProfile when user signs up with social account"""
    user = sociallogin.user

    if not hasattr(user, 'userprofile'):
        UserProfile.objects.create(
            user=user,
            email_consent=True  # Assuming they want updates
        )
```

Then in `accounts/__init__.py`:
```python
default_app_config = 'accounts.apps.AccountsConfig'
```

And in `accounts/apps.py`:
```python
from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        import accounts.signals
```

## Need Help?

- [django-allauth Documentation](https://django-allauth.readthedocs.io/)
- [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)
- Check Django logs for detailed error messages
