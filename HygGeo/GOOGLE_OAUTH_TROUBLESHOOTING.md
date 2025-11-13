# Google OAuth Troubleshooting Guide

## Error: "Access blocked: This app's request is invalid"

This error means Google rejected the OAuth request. Here's how to fix it:

---

## ✅ Checklist for Localhost Testing

### 1. Check Your Redirect URI in Google Console

**Where:** [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials)

**What to check:**
- [ ] Click on your OAuth 2.0 Client ID
- [ ] Scroll to "Authorized redirect URIs"
- [ ] Verify you have **EXACTLY** this (with trailing slash):
  ```
  http://localhost:8000/accounts/google/login/callback/
  ```

**Common mistakes:**
- ❌ `http://localhost:8000/accounts/google/login/callback` (no trailing slash)
- ❌ `https://localhost:8000/accounts/google/login/callback/` (https instead of http)
- ❌ `http://127.0.0.1:8000/accounts/google/login/callback/` (IP instead of localhost)

**Fix:** Click "Save" after adding the correct URI

---

### 2. Check JavaScript Origins

**Where:** Same OAuth client settings page

**What to check:**
- [ ] Scroll to "Authorized JavaScript origins"
- [ ] Add: `http://localhost:8000`
- [ ] Click "Save"

---

### 3. Check OAuth Consent Screen

**Where:** [OAuth Consent Screen](https://console.cloud.google.com/apis/credentials/consent)

**What to check:**
- [ ] **Publishing status** = "Testing" (NOT "In production")
- [ ] Your email is added as a **Test user**
- [ ] App name is set
- [ ] Support email is set

**How to add test users:**
1. Scroll to "Test users"
2. Click "Add Users"
3. Enter your Google email address
4. Click "Save"

---

### 4. Check APIs are Enabled

**Where:** [API Library](https://console.cloud.google.com/apis/library)

**What to check:**
- [ ] **Google+ API** is enabled
- [ ] **Google People API** is enabled

**How to enable:**
1. Search for "Google+ API"
2. Click on it
3. Click "Enable"
4. Repeat for "Google People API"

---

### 5. Check Django Site Configuration

Run this command in your terminal:

```bash
python manage.py shell
```

Then run:

```python
from django.contrib.sites.models import Site
from django.conf import settings

site = Site.objects.get(id=settings.SITE_ID)
print(f"Current site: {site.domain}")
print(f"Expected redirect URI: http://{site.domain}/accounts/google/login/callback/")
```

**Expected output:**
```
Current site: localhost:8000
Expected redirect URI: http://localhost:8000/accounts/google/login/callback/
```

**If it shows something different:**
```python
# Update the site
site.domain = 'localhost:8000'
site.name = 'HygGeo Local'
site.save()
print("✓ Site updated!")
```

---

### 6. Check Environment Variables

Make sure your `.env` file exists and has the correct credentials:

```bash
cat .env
```

**Expected output:**
```
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxx
```

**If missing or wrong:**
1. Check you created the `.env` file in the correct location (same folder as manage.py)
2. Verify the credentials match your Google Console

---

### 7. Test the Full OAuth Flow

**Step-by-step test:**

1. **Start Django server:**
   ```bash
   python manage.py runserver
   ```

2. **Open in INCOGNITO/PRIVATE mode:**
   ```
   http://localhost:8000/accounts/login/
   ```

3. **Click "Continue with Google"**

4. **Watch the URL bar:**
   - First: redirects to `accounts.google.com`
   - Then: should redirect back to `http://localhost:8000/accounts/google/login/callback/...`
   - Finally: redirects to your home page

5. **If it fails at the Google page:**
   - Error = "Access blocked" → Google Console settings wrong
   - Error = "redirect_uri_mismatch" → Redirect URI doesn't match
   - Error = "invalid_client" → Wrong Client ID/Secret

---

## Common Errors and Solutions

### Error: "redirect_uri_mismatch"

**Problem:** The redirect URI in the request doesn't match Google Console

**Solution:**
1. Go to Google Console → Credentials
2. Click your OAuth client
3. Add EXACTLY: `http://localhost:8000/accounts/google/login/callback/`
4. Save and wait 2-3 minutes

---

### Error: "invalid_client"

**Problem:** Wrong Client ID or Client Secret

**Solution:**
1. Check your `.env` file has the correct credentials
2. Verify they match Google Console
3. Make sure there are no extra spaces or quotes
4. Restart your Django server after changing `.env`

---

### Error: "Access blocked: This app's request is invalid"

**Problem:** Usually OAuth consent screen or redirect URI issue

**Solutions:**
1. **Add yourself as test user** (if app is in Testing mode)
2. **Check redirect URI** exactly matches (with trailing slash)
3. **Enable required APIs** (Google+, People API)
4. **Wait 2-3 minutes** after making changes in Google Console
5. **Clear browser cache** or use Incognito mode

---

### Error: "User not authorized to perform this action"

**Problem:** App is in Testing mode and you're not a test user

**Solution:**
1. Go to OAuth Consent Screen
2. Add your email to "Test users"
3. Save and try again

---

## Still Not Working?

### Debug Mode:

1. **Check Django logs** in the terminal where `runserver` is running
2. **Check browser console** (F12 → Console tab)
3. **Try a different browser** or Incognito mode
4. **Restart everything:**
   ```bash
   # Kill Django server (Ctrl+C)
   # Restart it
   python manage.py runserver
   ```

### Alternative: Use 127.0.0.1 Instead

If localhost doesn't work, try using 127.0.0.1:

**In Google Console:**
1. Add redirect URI: `http://127.0.0.1:8000/accounts/google/login/callback/`
2. Add origin: `http://127.0.0.1:8000`

**Update Django site:**
```python
from django.contrib.sites.models import Site
site = Site.objects.get(id=3)
site.domain = '127.0.0.1:8000'
site.save()
```

**Test at:** `http://127.0.0.1:8000/accounts/login/`

---

## Production Deployment

For production (`hyggeo.com`):

1. **Different OAuth Client** (recommended) or add to existing:
   ```
   https://hyggeo.com/accounts/google/login/callback/
   https://www.hyggeo.com/accounts/google/login/callback/
   ```

2. **Different Site in Django:**
   - SITE_ID = 1 for production
   - Domain = 'hyggeo.com'

3. **Environment variables in DigitalOcean:**
   - Add GOOGLE_CLIENT_ID
   - Add GOOGLE_CLIENT_SECRET

4. **OAuth Consent Screen:**
   - Can keep in "Testing" mode
   - Or publish it (requires verification for large user base)

---

## Quick Reference

| Setting | Local Development | Production |
|---------|------------------|------------|
| **Redirect URI** | `http://localhost:8000/accounts/google/login/callback/` | `https://hyggeo.com/accounts/google/login/callback/` |
| **JavaScript Origin** | `http://localhost:8000` | `https://hyggeo.com` |
| **Site Domain** | `localhost:8000` | `hyggeo.com` |
| **SITE_ID** | 3 | 1 |
| **Protocol** | HTTP | HTTPS |
| **OAuth Status** | Testing (with test users) | Testing or Production |

---

## Need More Help?

- [django-allauth Documentation](https://django-allauth.readthedocs.io/en/latest/providers.html#google)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Common OAuth Errors](https://developers.google.com/identity/protocols/oauth2/web-server#handlingresponse)
