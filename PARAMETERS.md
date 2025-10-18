# MCP Server Parameters

Complete guide to using the Chrome MCP Server screenshot parameters.

---

## 📸 `take_screenshot` Tool

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | *required* | The URL to capture (e.g., "https://example.com") |
| `viewport_width` | integer | 1920 | Browser viewport width in pixels |
| `viewport_height` | integer | 1080 | Browser viewport height in pixels |
| `delay` | integer | 0 | Additional delay in milliseconds after page loads before taking screenshot |
| `full_page` | boolean | **true** | If true, captures entire scrollable page. If false, captures only viewport |
| `timeout` | integer | 30000 | Page load timeout in milliseconds |

---

## 🎯 Parameter Details

### `viewport_width` - Custom Width

Set the browser viewport width in pixels.

**Common sizes:**
- **Mobile (iPhone 14):** 390
- **Mobile (iPhone 14 Pro Max):** 430
- **Tablet (iPad):** 768
- **Desktop HD:** 1920
- **Desktop 4K:** 3840

**Examples:**
```python
# Mobile screenshot
take_screenshot("https://example.com", viewport_width=390, viewport_height=844)

# Desktop screenshot
take_screenshot("https://example.com", viewport_width=1920, viewport_height=1080)
```

---

### `delay` - Post-Load Delay

Wait time in milliseconds **after** the page fully loads before taking the screenshot.

**When to use:**
- ✅ Pages with animations or transitions
- ✅ Pages with lazy-loaded images
- ✅ Single-page applications (SPAs) that render content dynamically
- ✅ Pages with JavaScript that modifies content after load

**Recommended values:**
- **Static pages:** 0 ms (no delay needed)
- **Pages with animations:** 1000-2000 ms
- **Heavy dynamic content:** 3000-5000 ms
- **Very slow dynamic pages:** 5000+ ms

**Examples:**
```python
# No delay - page is static
take_screenshot("https://example.com", delay=0)

# Wait 2 seconds for animations to complete
take_screenshot("https://producthunt.com", delay=2000)

# Wait 5 seconds for lazy-loaded content
take_screenshot("https://heavy-spa-app.com", delay=5000)
```

---

## 📋 Page Load Strategy

The MCP server uses a **multi-stage wait strategy** to ensure pages are fully loaded:

### Stage 1: DOM Load (`wait_until='load'`)
- ✅ Waits for HTML document to be fully parsed
- ✅ All synchronous scripts have executed
- ⚠️ Images and stylesheets may still be loading

### Stage 2: Network Idle (`wait_for_load_state('networkidle')`)
- ✅ Waits for network to be idle (no ongoing requests for 500ms)
- ✅ All resources (images, CSS, JS) have loaded
- ⚠️ Has a 5-second timeout (continues even if not reached)

### Stage 3: Custom Delay (optional)
- ✅ Waits the specified `delay` milliseconds
- ✅ Useful for post-load animations and dynamic content
- ⚠️ Only used if `delay > 0`

**Total wait time:**
```
Total = Page Load Time + Network Idle (max 5s) + Custom Delay
```

---

## 🚀 Usage Examples

### Basic Screenshot (Full Page by Default)
```python
take_screenshot("https://example.com")
# Captures entire scrollable page by default
```

### Mobile Screenshot
```python
take_screenshot(
    url="https://example.com",
    viewport_width=375,
    viewport_height=812
)
```

### Desktop with Delay
```python
take_screenshot(
    url="https://producthunt.com",
    viewport_width=1920,
    viewport_height=1080,
    delay=2000  # Wait 2 seconds after load
)
```

### Viewport Only Screenshot
```python
take_screenshot(
    url="https://example.com",
    full_page=False  # Capture only visible viewport (not full page)
)
```

### Custom Everything
```python
take_screenshot(
    url="https://heavy-site.com",
    viewport_width=1280,
    viewport_height=720,
    delay=3000,
    full_page=True,  # Full page (default, but shown for clarity)
    timeout=60000    # 60 second timeout
)
```

---

## 🧪 Testing Parameters Locally

Run the test script to see different parameter combinations:

```bash
python test_parameters.py
```

This will create screenshots with:
- Default settings (1920x1080, no delay)
- Mobile viewport (375x812)
- Tablet viewport (768x1024)
- Desktop with 2-second delay

All screenshots are saved to `./screenshots/` folder.

---

## 💡 Tips & Best Practices

### Choosing Viewport Width

1. **For general screenshots:** Use 1920x1080 (desktop HD)
2. **For mobile testing:** Use actual device dimensions (e.g., 390x844)
3. **For responsive design testing:** Test multiple widths:
   - Mobile: 375-430px
   - Tablet: 768-1024px
   - Desktop: 1920-3840px

### Choosing Delay

1. **Start with 0ms** - Most static sites don't need delay
2. **Add 1000-2000ms** - If you see:
   - Loading spinners in screenshots
   - Missing images (lazy loading)
   - Incomplete animations
3. **Add 3000-5000ms** - If you see:
   - JavaScript-rendered content missing
   - Charts/graphs not fully rendered
   - Dynamic content still loading

### Full Page vs Viewport

- **Full page (`full_page=true`) - DEFAULT:**
  - ✅ Captures entire scrollable page
  - ✅ Perfect for documentation
  - ✅ Sees all content, including below the fold
  - ✅ **Now the default setting!**
  - ⚠️ Slightly slower for very long pages
  - ⚠️ Larger file size for long pages

- **Viewport only (`full_page=false`):**
  - ✅ Faster for very long pages
  - ✅ Smaller file size
  - ✅ Shows only "above the fold" content
  - ❌ Misses content below the fold
  - ❌ Less useful for documentation

---

## 🐛 Troubleshooting

### Screenshot shows loading spinner

**Problem:** Content not fully loaded  
**Solution:** Increase `delay` parameter

```python
take_screenshot("https://site.com", delay=3000)
```

### Screenshot missing images

**Problem:** Lazy-loaded images not loaded yet  
**Solution:** Increase `delay` parameter

```python
take_screenshot("https://site.com", delay=2000)
```

### Screenshot times out

**Problem:** Page takes too long to load  
**Solution:** Increase `timeout` parameter

```python
take_screenshot("https://slow-site.com", timeout=60000)
```

### Wrong viewport size

**Problem:** Incorrect width/height parameters  
**Solution:** Verify device dimensions

```python
# iPhone 14 Pro
take_screenshot("https://site.com", viewport_width=393, viewport_height=852)
```

---

## 📚 Additional Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [Common Device Viewports](https://viewportsizer.com/devices/)
- [FastMCP Documentation](https://gofastmcp.com/)

---

## 🎉 Summary

The Chrome MCP Server now supports:

✅ **Custom viewport dimensions** - Perfect for responsive testing  
✅ **Post-load delay** - Ensures dynamic content is fully loaded  
✅ **Multi-stage wait strategy** - Pages are fully loaded before screenshot  
✅ **Full flexibility** - Combine parameters as needed

Happy screenshotting! 📸
