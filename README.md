# Enhanced Screenshot MCP Server

A powerful Python-based MCP (Model Context Protocol) server using FastMCP and Playwright that provides comprehensive web interaction capabilities for AI agents. Capture screenshots with granular control, extract page content, and perform browser interactions.

## 🚀 Features

### 📸 Screenshot Capture
- **Flexible Viewports**: Custom width/height or use mobile/desktop presets
- **High-DPI Support**: `device_scale_factor` for retina displays
- **Color Scheme Control**: Force light or dark mode rendering
- **Smart Waiting**: Wait for specific selectors before capture
- **Multiple Formats**: PNG (lossless) or JPEG (smaller files) with quality control
- **Full Page or Viewport**: Capture entire scrollable page or just visible area

### 📄 Content Extraction
- **Page Content**: Extract full HTML source or visible text
- **Element Targeting**: Extract specific elements by CSS selector
- **Format Options**: Get content as HTML or plain text

### 🖱️ Browser Interactions
- **Click Elements**: Interact with buttons, links, and UI elements
- **Type Text**: Fill forms and input fields
- **Scroll Pages**: Reveal content below the fold
- **Wait Actions**: Pause for animations or loading
- **Capture Results**: Optionally screenshot after interactions

### 🛡️ Production Ready
- **Docker Optimized**: Official Playwright image with all dependencies
- **Error Handling**: Comprehensive error messages and graceful degradation
- **Resource Management**: Proper browser lifecycle and cleanup
- **Type Safe**: Structured responses with clear contracts

## 📋 Available Tools

### 1. `capture_screenshot` - Advanced Screenshot Tool

The main screenshot tool with full customization.

**Parameters:**
```python
{
  "url": str,                    # Required: URL to capture
  "viewport_width": int,         # Default: 1920
  "viewport_height": int,        # Default: 1080
  "device_scale_factor": float,  # Default: 1.0 (use 2.0 for retina)
  "color_scheme": str,           # "light", "dark", or "no-preference" (default)
  "full_page": bool,             # Default: False
  "wait_for_selector": str,      # Optional: CSS selector to wait for
  "wait_timeout": int,           # Default: 30000 (ms)
  "output_format": str,          # "png" (default) or "jpeg"
  "jpeg_quality": int            # Default: 80 (0-100, for JPEG only)
}
```

**Examples:**
```json
// Desktop screenshot
{"url": "https://example.com"}

// Mobile with dark mode
{
  "url": "https://example.com",
  "viewport_width": 390,
  "viewport_height": 844,
  "color_scheme": "dark"
}

// High-DPI retina capture
{
  "url": "https://example.com",
  "device_scale_factor": 2.0
}

// Wait for content to load
{
  "url": "https://example.com",
  "wait_for_selector": ".main-content"
}

// JPEG for smaller file size
{
  "url": "https://example.com",
  "output_format": "jpeg",
  "jpeg_quality": 90
}
```

### 2. `screenshot_mobile` - Mobile Preset (390x844)

Convenience wrapper for mobile screenshots.

**Parameters:**
```python
{
  "url": str,         # Required
  "full_page": bool   # Default: True
}
```

### 3. `screenshot_desktop` - Desktop Preset (1920x1080)

Convenience wrapper for desktop screenshots.

**Parameters:**
```python
{
  "url": str,         # Required
  "full_page": bool   # Default: True
}
```

### 4. `get_page_content` - Extract Page Content

Extract HTML or text content from a web page.

**Parameters:**
```python
{
  "url": str,                  # Required
  "format": str,               # "html" or "text" (default: "text")
  "wait_for_selector": str,    # Optional
  "wait_timeout": int          # Default: 30000 (ms)
}
```

**Returns:**
```python
{
  "content": str,           # Extracted content
  "url": str,               # Final URL after redirects
  "title": str,             # Page title
  "format": str,            # Format used
  "content_length": int,    # Length in characters
  "error": str              # Optional error message
}
```

**Examples:**
```json
// Get page text
{"url": "https://example.com"}

// Get full HTML
{"url": "https://example.com", "format": "html"}

// Wait for dynamic content
{
  "url": "https://example.com",
  "wait_for_selector": "article"
}
```

### 5. `get_element_content` - Extract Specific Elements

Extract content from a specific element using CSS selectors.

**Parameters:**
```python
{
  "url": str,             # Required
  "selector": str,        # Required: CSS selector
  "format": str,          # "html" or "text" (default: "text")
  "wait_timeout": int     # Default: 30000 (ms)
}
```

**Returns:**
```python
{
  "content": str | None,       # Extracted content
  "selector_matched": bool,    # Whether selector found element
  "selector": str,             # Selector used
  "format": str,               # Format used
  "error": str                 # Optional error message
}
```

**Examples:**
```json
// Extract article text
{
  "url": "https://example.com/article",
  "selector": "article.main"
}

// Extract specific heading
{
  "url": "https://example.com",
  "selector": "h1",
  "format": "text"
}
```

### 6. `interact_and_capture` - Browser Interactions

Perform actions and optionally capture the result.

**Parameters:**
```python
{
  "url": str,                      # Required
  "actions": [                     # Required: List of actions
    {
      "type": "click",            # Action types: click, type, wait, scroll
      "selector": ".button"       # For click/type actions
    },
    {
      "type": "type",
      "selector": "#input",
      "value": "search term"      # For type actions
    },
    {
      "type": "wait",
      "duration": 1000            # Milliseconds for wait actions
    },
    {
      "type": "scroll",
      "amount": 500               # Pixels for scroll actions
    }
  ],
  "capture_screenshot": bool,     # Default: True
  "screenshot_format": str,       # "png" or "jpeg" (default: "png")
  "viewport_width": int,          # Default: 1920
  "viewport_height": int          # Default: 1080
}
```

**Returns:**
```python
{
  "success": bool,                # All actions completed successfully
  "screenshot": Image | None,     # Image if capture_screenshot=True
  "final_url": str,               # URL after all actions
  "actions_completed": int,       # Number of successful actions
  "errors": [str]                 # List of error messages
}
```

**Examples:**
```json
// Click button and capture
{
  "url": "https://example.com",
  "actions": [
    {"type": "click", "selector": ".menu-button"}
  ]
}

// Fill search form
{
  "url": "https://example.com/search",
  "actions": [
    {"type": "type", "selector": "#search-input", "value": "playwright"},
    {"type": "click", "selector": "#search-button"}
  ]
}

// Scroll to reveal content
{
  "url": "https://example.com",
  "actions": [
    {"type": "scroll", "amount": 1000},
    {"type": "wait", "duration": 500}
  ]
}
```

## 🔧 Local Development

### Prerequisites
- Python 3.11+
- pip

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
python -m playwright install chromium
```

3. Run the server:
```bash
python server.py
```

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

The docker-compose.yml includes recommended Playwright Docker configurations:

```bash
docker-compose up -d
```

The configuration includes:
- `init: true` - Prevents zombie processes
- `ipc: host` - Prevents Chromium out-of-memory crashes
- Automatic restart on failure

### Using Docker Directly

```bash
# Build
docker build -t screenshot-mcp-server .

# Run with recommended flags
docker run -d \
  --init \
  --ipc=host \
  -p 8000:8000 \
  screenshot-mcp-server
```

## ☁️ Coolify Deployment

This project is optimized for deployment on [Coolify](https://coolify.io).

### Quick Deploy

1. **Push to Git**: Ensure your repository is pushed to GitHub/GitLab
2. **Create Resource**: In Coolify, create a new "Docker Compose" resource
3. **Connect Repository**: Link your Git repository
4. **Deploy**: Coolify will automatically build and deploy

### Configuration

No additional environment variables are required for basic operation. The server runs on port 8000.

### Recommended Settings

- **Resource Type**: Docker Compose
- **Build Method**: Dockerfile
- **Port**: 8000
- **Health Check**: HTTP GET to `/` (if FastMCP supports it)

## 📊 Technical Details

### Architecture
- **Runtime**: Python 3.11
- **Framework**: FastMCP
- **Browser**: Playwright Chromium
- **Base Image**: `mcr.microsoft.com/playwright/python:v1.49.0-noble` (Ubuntu 24.04 LTS)

### Docker Configuration

Based on [official Playwright Docker documentation](https://playwright.dev/docs/docker):
- Uses Microsoft's official Playwright Python image
- Includes all system dependencies and browsers pre-installed
- Configured with `--no-sandbox` and `--disable-dev-shm-usage` for container compatibility
- `init: true` prevents zombie processes (PID 1 handling)
- `ipc: host` prevents Chromium memory issues

### Performance Characteristics

**Screenshot Capture:**
- Viewport only: ~2-5 seconds
- Full page: ~5-15 seconds (depends on page length)
- High-DPI (2x): ~1.5x slower than standard
- JPEG vs PNG: JPEG is ~30-50% smaller but lossy

**Content Extraction:**
- HTML extraction: ~1-3 seconds
- Text extraction: ~1-3 seconds
- Element extraction: ~1-4 seconds (includes selector wait time)

**Interactive Operations:**
- Per action: ~0.5-2 seconds
- Full workflow: Depends on action count and page responsiveness

### Resource Usage

- **Memory**: ~200-500 MB per browser instance
- **CPU**: Moderate during page rendering
- **Disk**: ~500 MB for Docker image

## 🎯 MCP Configuration

### For Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "screenshot": {
      "command": "python",
      "args": ["/path/to/chrome-mcp/server.py"]
    }
  }
}
```

### For Remote Deployment

```json
{
  "mcpServers": {
    "screenshot": {
      "url": "http://your-domain.com:8000",
      "transport": "sse"
    }
  }
}
```

## 💡 Usage Tips

### Screenshot Quality
- Use PNG for pixel-perfect captures (documentation, design review)
- Use JPEG for faster transmission and smaller storage (preview, thumbnails)
- Set `device_scale_factor: 2.0` for high-DPI displays and crisp text

### Color Scheme Testing
- Compare light/dark modes by taking two screenshots with different `color_scheme` values
- Useful for testing theme implementations

### Dynamic Content
- Always use `wait_for_selector` for single-page applications
- Increase `wait_timeout` for slow-loading pages
- Consider using `interact_and_capture` to trigger lazy-loaded content

### Error Handling
- All tools return structured responses with error fields
- Check `selector_matched` field when extracting elements
- Review `errors` array from `interact_and_capture` for partial failures

## 🔍 Troubleshooting

### Build Failures
- Ensure you're using the correct Playwright image version
- Check Docker has enough resources (memory, disk space)
- Review Coolify build logs for specific errors

### Chromium Launch Errors
- Uncomment `cap_add: SYS_ADMIN` in docker-compose.yml for development
- Ensure `ipc: host` is set (prevents shared memory issues)
- Check `/dev/shm` has sufficient space in container

### Timeout Issues
- Increase `wait_timeout` for slow networks or pages
- Check URL is accessible from container (network configuration)
- Verify CSS selectors are correct using browser DevTools

### Selector Not Found
- Test selectors in browser DevTools first
- Wait for dynamic content with `wait_for_selector`
- Check if content is in iframe (requires different handling)

## 📚 Examples

### Compare Light vs Dark Mode

```python
# Capture both modes
light = capture_screenshot(
    url="https://example.com",
    color_scheme="light"
)

dark = capture_screenshot(
    url="https://example.com",
    color_scheme="dark"
)
```

### Extract Article Text

```python
# Get article content
article = get_element_content(
    url="https://blog.example.com/post",
    selector="article.post-content",
    format="text"
)

print(article["content"])
```

### Automated Form Submission

```python
# Fill and submit form
result = interact_and_capture(
    url="https://example.com/contact",
    actions=[
        {"type": "type", "selector": "#name", "value": "John Doe"},
        {"type": "type", "selector": "#email", "value": "john@example.com"},
        {"type": "type", "selector": "#message", "value": "Hello!"},
        {"type": "click", "selector": "button[type='submit']"},
        {"type": "wait", "duration": 2000}
    ]
)

if result["success"]:
    print("Form submitted successfully!")
```

## 📖 API Reference

For complete API documentation, see the tool docstrings in `server.py`. Each tool includes:
- Detailed parameter descriptions
- Return value schemas
- Usage examples
- Error conditions

## 🤝 Contributing

Contributions are welcome! Please ensure:
- Code follows existing patterns
- New tools include comprehensive docstrings
- Docker configuration remains compatible with Playwright requirements

## 📄 License

MIT License - feel free to use this in your projects!

## 🆘 Support

For issues or questions:
- Open an issue in the repository
- Check [Playwright documentation](https://playwright.dev/docs/docker) for Docker-specific issues
- Review [FastMCP documentation](https://github.com/jlowin/fastmcp) for MCP-related questions

## 🔗 Related Resources

- [Playwright Docker Documentation](https://playwright.dev/docs/docker)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [Coolify Platform](https://coolify.io)

