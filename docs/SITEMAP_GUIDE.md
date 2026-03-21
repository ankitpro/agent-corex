# Sitemap Guide for Agent-Corex

## Overview

A sitemap is an XML file that lists all pages on your website. It helps search engines discover, crawl, and index your pages more efficiently.

---

## 📍 Our Sitemap

**Location**: `https://ankitpro.github.io/agent-corex/sitemap.xml`

The sitemap is automatically generated and updated whenever the site is built by Jekyll.

---

## 🔧 How It Works

### Jekyll Sitemap Plugin
- **Plugin**: `jekyll-sitemap`
- **Configuration**: Already enabled in `/docs/_config.yml`
- **Generation**: Automatic on each Jekyll build
- **Scope**: Includes all pages except excluded files

### Sitemap Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://ankitpro.github.io/agent-corex/</loc>
    <lastmod>2026-03-21T00:00:00Z</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://ankitpro.github.io/agent-corex/quickstart/</loc>
    <lastmod>2026-03-21T00:00:00Z</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <!-- More pages... -->
</urlset>
```

### Fields Explained

| Field | Meaning | Example |
|-------|---------|---------|
| `<loc>` | Full URL of the page | `https://ankitpro.github.io/agent-corex/` |
| `<lastmod>` | Last modification date | `2026-03-21T00:00:00Z` |
| `<changefreq>` | How often page updates | `weekly`, `monthly`, `yearly` |
| `<priority>` | Importance relative to other pages | `0.0 - 1.0` (1.0 = highest) |

---

## 📝 Pages Included in Sitemap

The sitemap automatically includes:

```
✅ https://ankitpro.github.io/agent-corex/
✅ https://ankitpro.github.io/agent-corex/quickstart/
✅ https://ankitpro.github.io/agent-corex/installation/
✅ https://ankitpro.github.io/agent-corex/api/
✅ https://ankitpro.github.io/agent-corex/deployment/
```

**Excluded Files** (in _config.yml):
```
❌ .github/
❌ .gitignore
❌ .vscode/
❌ Gemfile
❌ Gemfile.lock
❌ node_modules/
❌ vendor/
❌ .env
❌ .venv
❌ README.md
❌ CHANGELOG.md
```

---

## 🔗 Robots.txt Connection

The `robots.txt` file points search engines to the sitemap:

```
# In /docs/robots.txt
Sitemap: https://ankitpro.github.io/agent-corex/sitemap.xml
```

This tells crawlers: "Here's a complete list of all pages to index."

---

## 📊 Sitemap Best Practices

### 1. **Keep It Updated**
- ✅ Jekyll automatically regenerates on each build
- ✅ New pages are added automatically
- ✅ Last modification dates are updated

### 2. **Proper Change Frequency**
- `always` - For pages that change every visit
- `hourly` - For frequently updated pages
- `daily` - For blogs, news
- `weekly` - For documentation (our case)
- `monthly` - For infrequently updated pages
- `yearly` - For archival content
- `never` - For outdated content

### 3. **Priority Levels**
```
Home page: 1.0 (most important)
Main docs: 0.8
Sub-docs: 0.6
Archives: 0.3
Deprecated: 0.1
```

### 4. **Size Limits**
- Max 50,000 URLs per sitemap file
- Max 50MB per sitemap file
- ✅ Our site: 5 pages (well under limit)

### 5. **Multiple Sitemaps**
For large sites (1000+ pages), use sitemap index:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://ankitpro.github.io/agent-corex/sitemap-1.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://ankitpro.github.io/agent-corex/sitemap-2.xml</loc>
  </sitemap>
</sitemapindex>
```
Status: ✅ Not needed yet (only 5 pages)

---

## 🚀 Submitting to Search Engines

### Google Search Console
1. Go to: https://search.google.com/search-console
2. Select your property: `https://ankitpro.github.io/agent-corex/`
3. Left sidebar → **Sitemaps**
4. Click **Add a new sitemap**
5. Enter: `agent-corex/sitemap.xml`
6. Click **Submit**

**Status**: Should show "Success" within 24 hours

### Bing Webmaster Tools
1. Go to: https://www.bing.com/webmasters
2. Add site: `https://ankitpro.github.io/agent-corex/`
3. Click **Submit sitemap**
4. Paste: `https://ankitpro.github.io/agent-corex/sitemap.xml`

---

## 📈 Monitoring

### Google Search Console
Track these metrics:

| Metric | What It Means | Goal |
|--------|---------------|------|
| **Discovered** | Pages found by Google | Equal to total pages |
| **Indexed** | Pages added to search index | 100% of sitemap |
| **Coverage** | Errors and warnings | 0 errors |
| **Valid items** | Properly formatted pages | All pages valid |

### What to Look For

✅ **Good Signs**:
- All pages indexed within 1-7 days
- No crawl errors
- Proper mobile usability

❌ **Problems to Fix**:
- Noindex meta tags blocking indexing
- Robots.txt disallowing pages
- Server returning 404/500 errors
- Duplicate content issues

---

## 🔄 Sitemap Update Cycle

### Automatic Updates

```
Git push to main
    ↓
GitHub Actions triggers Jekyll build
    ↓
Jekyll regenerates sitemap.xml
    ↓
New pages automatically included
    ↓
lastmod dates updated
    ↓
Google discovers changes (within 24h)
```

**No manual action needed!**

---

## 🧪 Testing Your Sitemap

### 1. **Direct Access**
Visit: `https://ankitpro.github.io/agent-corex/sitemap.xml`

Should return valid XML with all pages.

### 2. **Validation**
Use: https://www.xml-sitemaps.com/validate-xml-sitemap.html

Checks for XML syntax errors.

### 3. **Google Search Console**
Check **Coverage** report for:
- Total discovered URLs
- Indexed vs excluded
- Errors and warnings

---

## 📋 Sitemap Maintenance Checklist

### When Adding New Pages
- [ ] Create new `.md` file in `/docs/`
- [ ] Add proper YAML frontmatter
- [ ] Commit and push to GitHub
- [ ] Sitemap auto-regenerates (no action needed)
- [ ] Check Google Search Console after 24h

### When Updating Pages
- [ ] Modify existing page content
- [ ] Commit and push to GitHub
- [ ] Last modification date auto-updates
- [ ] Changes indexed within 1 week

### When Removing Pages
- [ ] Delete or rename the file
- [ ] Commit and push to GitHub
- [ ] Remove from sitemap automatically
- [ ] Add 404 redirect (optional, for old links)

### Monthly Review
- [ ] Check Google Search Console for indexing status
- [ ] Verify no crawl errors
- [ ] Check mobile usability issues
- [ ] Review Core Web Vitals

---

## 🔍 Advanced: Custom Sitemap Configuration

To customize sitemap behavior, edit `/docs/_config.yml`:

### Change Priority for Specific Pages

```yaml
# In _config.yml (future enhancement)
sitemap:
  priority_map:
    /: 1.0
    /quickstart/: 0.8
    /api/: 0.7
    /deployment/: 0.6
```

### Exclude Specific Pages

```yaml
# In _config.yml
exclude:
  - drafts/
  - private/
```

**Current Status**: Using defaults (works perfectly for our site)

---

## 📚 Resources

### Official Documentation
- Google Sitemaps: https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview
- Jekyll Sitemap Plugin: https://github.com/jekyll/jekyll-sitemap
- Sitemap Protocol: https://www.sitemaps.org

### Tools
- Sitemap Generator: https://www.xml-sitemaps.com
- Validator: https://www.xml-sitemaps.com/validate-xml-sitemap.html
- Google Search Console: https://search.google.com/search-console

### Best Practices
- Moz Guide: https://moz.com/learn/seo/sitemap
- Screaming Frog: https://www.screamingfrog.co.uk/seo-spider/

---

## 🎯 Current Status

| Item | Status | Details |
|------|--------|---------|
| Sitemap Generated | ✅ Yes | Located at `/agent-corex/sitemap.xml` |
| Auto-Updates | ✅ Yes | Regenerates on each Jekyll build |
| Robots.txt Points to Sitemap | ✅ Yes | Configured in `/docs/robots.txt` |
| Submitted to Google | ✅ Yes | In Google Search Console |
| Pages Indexed | ⏳ In Progress | 1-7 days after submission |
| Sitemap Valid | ✅ Yes | Passes XML validation |

---

## 📞 Troubleshooting

### Issue: Sitemap not appearing
**Solution**: Rebuild Jekyll
```bash
cd docs
jekyll build
```

### Issue: Pages not indexed
**Solution**: Check Google Search Console
1. Go to Coverage report
2. Look for errors or warnings
3. Submit sitemap again

### Issue: Old pages still showing in search
**Solution**: Use Google Search Console's URL removal tool
1. Go to **Removals**
2. Click **New request**
3. Enter URL to remove
4. Select duration (temporary or permanent)

---

**Last Updated**: March 21, 2026
**Sitemap URL**: https://ankitpro.github.io/agent-corex/sitemap.xml
**Status**: ✅ Active and auto-updating
