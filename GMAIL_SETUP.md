# Gmail Configuration for HygGeo Password Reset

## Quick Setup Guide

### Option 1: Direct Settings (Quick Test)
Add this to your `settings.py` after line 194:

```python
# Gmail Configuration for Testing
if not DEBUG:  # Only for production/testing
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = 'your-email@gmail.com'
    EMAIL_HOST_PASSWORD = 'your-app-password'  # NOT your regular password!
    DEFAULT_FROM_EMAIL = 'HygGeo <your-email@gmail.com>'
```

### Option 2: Environment Variables (Recommended)
Create a `.env` file in your project root:

```env
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password
DEFAULT_FROM_EMAIL=HygGeo <your-email@gmail.com>
```

## Gmail App Password Setup

### Step 1: Enable 2-Factor Authentication
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Turn on 2-Step Verification (required for app passwords)

### Step 2: Generate App Password
1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select "Mail" and "Other (custom name)"
3. Enter "Django HygGeo"
4. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

### Step 3: Use App Password
- **Use**: The 16-character app password
- **Don't use**: Your regular Gmail password

## Testing

### Test Console Email (Current Setup)
```bash
# Visit: http://127.0.0.1:8000/accounts/login/
# Click "Forgot password?"
# Enter any email
# Check console output for email content
```

### Test Real Gmail Sending
```python
# In Django shell:
from django.core.mail import send_mail
send_mail(
    'Test Email',
    'This is a test message.',
    'your-email@gmail.com',
    ['recipient@example.com'],
    fail_silently=False,
)
```

## Current Status
✅ Forgot password fully functional on dev server
✅ Beautiful templates created
✅ URLs configured
✅ Security implemented
✅ Ready for Gmail integration

## Quick Toggle for Testing
To test with real emails, temporarily change line 185 in settings.py:
```python
# Change this:
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# To this:
if False:  # Temporarily disable console backend
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Then add Gmail settings and restart the server!