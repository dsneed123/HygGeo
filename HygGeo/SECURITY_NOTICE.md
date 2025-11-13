# ⚠️ URGENT: SECURITY NOTICE ⚠️

## Your Google OAuth Credentials Were Exposed!

You shared your Google OAuth credentials publicly. **You MUST rotate them immediately** to prevent unauthorized access to your application.

### What Was Exposed:
- **Client ID**: `[REDACTED - Your Google OAuth Client ID]`
- **Client Secret**: `[REDACTED - Your Google OAuth Client Secret]`

### Why This Is Dangerous:
Anyone with these credentials could:
- Impersonate your application
- Access user data through your OAuth integration
- Make API calls on behalf of your application
- Potentially compromise user accounts

---

## How to Rotate Your Credentials (Do This NOW!)

### Step 1: Delete the Old Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to **"APIs & Services" → "Credentials"**
4. Find your OLD OAuth 2.0 Client ID (the one you exposed)
5. Click the **trash icon** to delete it
6. Confirm deletion

### Step 2: Create New Credentials

1. Click **"Create Credentials" → "OAuth client ID"**
2. Select **"Web application"**
3. Name: `HygGeo Web Client (New)`

#### Authorized JavaScript origins:
**Local Development:**
- `http://localhost:8000`
- `http://127.0.0.1:8000`

**Production:**
- `https://hyggeo.com`
- `https://www.hyggeo.com`

#### Authorized redirect URIs:
**Local Development:**
- `http://localhost:8000/accounts/google/login/callback/`
- `http://127.0.0.1:8000/accounts/google/login/callback/`

**Production:**
- `https://hyggeo.com/accounts/google/login/callback/`
- `https://www.hyggeo.com/accounts/google/login/callback/`

4. Click **"Create"**
5. Copy your **NEW** Client ID and Client Secret

### Step 3: Update Your .env File

Replace the old credentials in your `.env` file:

```bash
# Old credentials (EXPOSED - DO NOT USE)
# GOOGLE_CLIENT_ID=[YOUR OLD CLIENT ID]
# GOOGLE_CLIENT_SECRET=[YOUR OLD CLIENT SECRET]

# New credentials (from Step 2)
GOOGLE_CLIENT_ID=your_new_client_id_here
GOOGLE_CLIENT_SECRET=your_new_client_secret_here
```

### Step 4: Update Production Environment Variables

If you've deployed to production (DigitalOcean):

1. Go to your **DigitalOcean App Platform** dashboard
2. Select your app
3. Go to **"Settings" → "App-Level Environment Variables"**
4. **Update** both variables with your new credentials:
   - `GOOGLE_CLIENT_ID` = your new client ID
   - `GOOGLE_CLIENT_SECRET` = your new client secret
5. Click **"Save"**
6. **Redeploy** your app

### Step 5: Test

1. Restart your local development server:
   ```bash
   python manage.py runserver
   ```

2. Go to `http://localhost:8000/accounts/login/`
3. Click **"Continue with Google"**
4. Verify it works with the new credentials

---

## Best Practices Going Forward

### ✅ DO:
- Store credentials in `.env` files (never in code)
- Add `.env` to `.gitignore` ✓ (already done)
- Use environment variables in production ✓ (already configured)
- Keep credentials private and secure
- Rotate credentials if ever exposed

### ❌ DON'T:
- Share credentials in chat, email, or messages
- Commit credentials to Git
- Post credentials in screenshots or videos
- Reuse the same credentials after exposure
- Store credentials in plain text files that get backed up to cloud storage

---

## What Happens If You Don't Rotate?

If someone malicious gets these credentials, they could:
1. Create fake OAuth flows that look like your app
2. Trick users into authorizing their malicious app
3. Access user profile data (name, email, etc.)
4. Make your app reach rate limits
5. Get your OAuth app banned by Google

---

## Current Status

✅ **Local Setup Complete:**
- `.env` file created with credentials
- `.env` added to `.gitignore`
- Site configured for localhost:8000
- Google OAuth ready to test

⚠️ **Action Required:**
- [ ] Delete old OAuth credentials in Google Console
- [ ] Create new OAuth credentials
- [ ] Update `.env` file with new credentials
- [ ] Update production environment variables (if deployed)
- [ ] Test with new credentials

---

## Need Help?

If you're unsure about any of these steps, refer to `GOOGLE_OAUTH_SETUP.md` for detailed instructions, or consult the [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2).

**Remember: Security is not optional. Rotate your credentials today!**
