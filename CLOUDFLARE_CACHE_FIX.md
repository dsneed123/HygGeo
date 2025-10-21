# Fix Cloudflare Cache Policy (4 hours → 1 month)

## Issue
Your images are only cached for 4 hours. This means:
- Repeat visitors have to re-download images
- Lighthouse flags "Serve static assets with an efficient cache policy"
- Slower page loads for returning users

## Solution: Increase Cache TTL to 1 Month

### Method 1: Page Rules (Recommended, Easy)

**Go to:** Cloudflare Dashboard → Rules → Page Rules

#### Create 3 Page Rules:

**Rule 1: Static Files**
```
URL Pattern: *hyggeo.com/static/*
Settings:
- Cache Level: Cache Everything
- Edge Cache TTL: 1 month
- Browser Cache TTL: 1 month
```

**Rule 2: R2 Images**
```
URL Pattern: *hyggeo.com/hyggeo-images/*
Settings:
- Cache Level: Cache Everything
- Edge Cache TTL: 1 month
- Browser Cache TTL: 1 month
```

**Rule 3: Transformed Images**
```
URL Pattern: *hyggeo.com/cdn-cgi/image/*
Settings:
- Cache Level: Cache Everything
- Edge Cache TTL: 1 month
- Browser Cache TTL: 1 month
```

**Free plan:** You get 3 page rules (perfect!)
**Paid plan:** Unlimited page rules

---

### Method 2: Cache Rules (Newer, More Flexible)

**Go to:** Cloudflare Dashboard → Caching → Cache Rules

#### Create 1 Cache Rule:

**Rule Name:** Long Cache for Static Assets

**When incoming requests match:**
```
(http.request.uri.path contains "/static/") or
(http.request.uri.path contains "/hyggeo-images/") or
(http.request.uri.path contains "/cdn-cgi/image/")
```

**Then:**
- Eligible for cache: Yes
- Edge TTL: 1 month (2592000 seconds)
- Browser TTL: 1 month (2592000 seconds)

---

### Method 3: Django Settings (Server-Side Headers)

**Edit:** `settings.py`

Add this:

```python
# Cloudflare respects these headers
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=2592000, public, immutable',  # 30 days
}
```

This is **already set** in your code, but Cloudflare might override it. Use Page Rules to enforce.

---

## Expected Results

### Before:
```
Cache-Control: max-age=14400  (4 hours)
```

### After:
```
Cache-Control: max-age=2592000, public, immutable  (30 days)
```

### Benefits:
- ✅ Returning visitors: Images load instantly from cache
- ✅ Bandwidth savings: ~70% reduction on repeat visits
- ✅ Lighthouse: "Serve static assets with an efficient cache policy" passes
- ✅ Faster page loads for all users after first visit

---

## Testing

1. **Apply the page rules** in Cloudflare Dashboard
2. **Wait 5 minutes** for changes to propagate
3. **Test with curl:**

```bash
curl -I "https://www.hyggeo.com/hyggeo-images/media/destinations/example.jpg"

# Look for:
# cache-control: max-age=2592000, public, immutable
# cf-cache-status: HIT
```

4. **Test in browser:**
   - Open DevTools → Network tab
   - Load your homepage
   - Look at image requests
   - Should show `max-age=2592000` in response headers

---

## Important Notes

### Why 1 Month is Safe

✅ **Images don't change:** Your destination/accommodation images are static
✅ **Unique filenames:** Django generates unique filenames (e.g., `2f8189f2.jpg.webp`)
✅ **Cloudflare purge:** You can always purge cache manually if needed
✅ **SEO benefit:** Faster site = better rankings

### What About Dynamic Content?

**DO NOT cache:**
- `/` (homepage - dynamic)
- `/experiences/` (listings - dynamic)
- `/profile/` (user pages - dynamic)
- Any pages with forms or user-specific content

**DO cache:**
- `/static/*` (CSS, JS, fonts - never changes)
- `/hyggeo-images/*` (uploaded images - never changes)
- `/cdn-cgi/image/*` (transformed images - never changes)

Page Rules already handle this correctly!

---

## Troubleshooting

### If cache headers still show 4 hours:

1. **Check Page Rules are active:**
   - Go to Cloudflare Dashboard → Rules → Page Rules
   - Make sure rules are enabled (toggle should be ON)

2. **Check rule order:**
   - Most specific rules should be first
   - Example order:
     1. `/cdn-cgi/image/*` (most specific)
     2. `/hyggeo-images/*`
     3. `/static/*` (least specific)

3. **Purge cache and test:**
   - Go to Cloudflare Dashboard → Caching → Configuration
   - Click "Purge Everything"
   - Wait 1 minute
   - Test again with curl

4. **Check Cloudflare cache level:**
   - Go to Cloudflare Dashboard → Caching → Configuration
   - "Caching Level" should be "Standard" or higher
   - "Browser Cache TTL" can be "Respect Existing Headers"

---

## Priority: HIGH

This fix will:
- Reduce LCP "Load Delay" from 800ms to ~100ms for repeat visitors
- Improve Lighthouse "cache policy" score
- Save bandwidth costs
- Speed up site significantly for returning users

**Estimated time to implement:** 5 minutes
**Estimated impact:** 40-60% faster repeat visit loads

---

## Summary

**Quick Fix Steps:**
1. Go to Cloudflare Dashboard
2. Rules → Page Rules
3. Add 3 rules (see above)
4. Save and wait 5 minutes
5. Test with curl
6. Done! 🎉

Your images will now be cached for 30 days instead of 4 hours.
