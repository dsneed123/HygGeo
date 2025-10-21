# Render-Blocking Resources - Cloudflare Rocket Loader Fix

## Problem
Lighthouse audit identified `/cloudflare-static/rocket-loader.min.js` as render-blocking resource:
- Blocks page rendering
- Delays LCP (Largest Contentful Paint)
- Adds unnecessary JavaScript processing

## Root Cause
Cloudflare Rocket Loader is automatically enabled in Cloudflare dashboard. It attempts to defer JavaScript loading but actually BLOCKS rendering in the process.

## Solution

### 1. Disable Rocket Loader in Cloudflare Dashboard
**This is the recommended fix:**

1. Log into Cloudflare dashboard: https://dash.cloudflare.com
2. Select domain: hyggeo.com
3. Navigate to: **Speed** > **Optimization**
4. Find: **Rocket Loader™**
5. Toggle: **OFF**
6. Save changes

**Why disable?**
- Modern browsers handle async/defer scripts efficiently
- Our templates already use optimal script loading strategies
- Rocket Loader adds overhead and blocks rendering
- We're already using `defer` and `async` attributes appropriately

### 2. Alternative: Exclude Critical Scripts (Not Recommended)
If you want to keep Rocket Loader but exclude specific scripts:

Add `data-cfasync="false"` attribute to scripts that should not be processed:

```html
<!-- Example: Critical Bootstrap script -->
<script src="..." defer data-cfasync="false"></script>
```

However, this is NOT recommended because:
- Rocket Loader still loads and executes
- Only prevents it from modifying specific scripts
- Still causes render-blocking

### 3. Verify After Disabling
After disabling Rocket Loader:

1. Clear Cloudflare cache:
   - **Caching** > **Configuration** > **Purge Everything**

2. Test with PageSpeed Insights:
   - https://pagespeed.web.dev/
   - Enter: https://hyggeo.com
   - Check that Rocket Loader is no longer listed in "Eliminate render-blocking resources"

## Expected Impact

**Before (with Rocket Loader):**
- Render-blocking JavaScript: Yes
- LCP impact: +200-500ms
- TBT impact: +50-100ms

**After (without Rocket Loader):**
- Render-blocking JavaScript: No
- LCP improvement: -200-500ms
- TBT improvement: -50-100ms
- Performance score: +5-10 points

## Alternative Cloudflare Optimizations to Keep

These Cloudflare features should REMAIN ENABLED:

### ✅ Keep Enabled:
- **Auto Minify** (HTML, CSS, JS)
- **Brotli** compression
- **HTTP/2** and **HTTP/3**
- **Early Hints**
- **Automatic Platform Optimization** (APO) for WordPress (if applicable)

### ❌ Disable:
- **Rocket Loader™** - Blocks rendering
- **Mirage** - Can cause layout shifts with images
- **Auto Minify JavaScript** - Can break code (we're already minifying)

## Status
- [x] Documentation created
- [ ] User needs to disable Rocket Loader in Cloudflare dashboard
- [ ] User needs to purge Cloudflare cache after disabling
- [ ] User needs to re-test with PageSpeed Insights to verify

## Notes
This is a Cloudflare account-level setting and cannot be fixed via code changes. User must access Cloudflare dashboard to disable.
