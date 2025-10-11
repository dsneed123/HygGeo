# 🔐 Secure Email Setup Guide

## ✅ Your settings.py is already configured correctly!

Your Django settings are already set up to use environment variables securely.

## Step 1: Create .env file

Create a file called `.env` in your project root:

```env
# Gmail Configuration
EMAIL_HOST_USER=youremail@gmail.com
EMAIL_HOST_PASSWORD=abcd-efgh-ijkl-mnop
DEFAULT_FROM_EMAIL=HygGeo <youremail@gmail.com>

# Optional: To test real emails in development
# DEBUG=False
```

## Step 2: Get Gmail App Password

1. **Enable 2-Factor Authentication**:
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Turn on 2-Step Verification

2. **Generate App Password**:
   - Go to [App Passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" and "Other (custom name)"
   - Enter "Django HygGeo"
   - Copy the 16-character password (format: `abcd efgh ijkl mnop`)

3. **Use App Password in .env**:
   ```env
   EMAIL_HOST_PASSWORD=abcdefghijklmnop  # Remove spaces
   ```

## Step 3: Test Email Sending

### Option A: Test in Development
```env
# In .env file
DEBUG=False  # This switches to real email sending
```

### Option B: Keep Development Mode
```env
# In .env file
DEBUG=True   # Emails go to console (current setup)
```

## Security Best Practices ✅

- ✅ Passwords in `.env` file (not in code)
- ✅ `.env` should be in `.gitignore` (don't commit passwords)
- ✅ Use App Passwords (not regular Gmail password)
- ✅ Environment variables already configured

## Quick Test

1. Create `.env` with your Gmail credentials
2. Restart Django server
3. Go to: `http://127.0.0.1:8000/accounts/login/`
4. Click "Forgot password?"
5. Enter your email address
6. Check your Gmail inbox! 📧

## Current Status
✅ Code is secure and production-ready
✅ Just need to add your Gmail credentials to `.env`
✅ No code changes needed!

## Example .env File
```env
EMAIL_HOST_USER=john@gmail.com
EMAIL_HOST_PASSWORD=abcdefghijklmnop
DEFAULT_FROM_EMAIL=HygGeo <john@gmail.com>
DEBUG=False
```

That's it! Your app is already configured securely. 🎉