# Chrome MCP Server 🌐📸

A production-ready Model Context Protocol (MCP) server that provides Chrome/Chromium browser automation capabilities using Playwright. Perfect for taking screenshots, getting page titles, and browser automation tasks.

## Features ✨

- **Screenshot Capture**: Take full-page or viewport screenshots of any website
- **Configurable Parameters**: Custom delay, viewport sizes, and full-page capture
- **Page Information**: Extract page titles and metadata
- **Health Monitoring**: Built-in health check endpoint
- **Production-Ready**: Optimized for Docker deployment with proper resource management
- **FastMCP Integration**: HTTP transport for remote access
- **Coolify-Ready**: Deploy to Coolify with zero configuration

## 🚀 Deploy to Coolify (Zero Configuration!)

**Want to deploy to production instantly?**

👉 **[See DEPLOY.md for complete Coolify deployment guide](DEPLOY.md)**

**Quick version:**
1. Connect this GitHub repo to Coolify
2. Coolify detects `docker-compose.yml` automatically
3. Click "Deploy"
4. Done! Chrome/Chromium dependencies are handled automatically ✅

No configuration needed. No manual setup. Just works. 🎉

---

## 📋 Using the MCP Server

Once deployed, configure your MCP client:

### **Claude Desktop Configuration:**

Add this to your Claude Desktop config file:

**Config File Location:**
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

**Configuration:**
```json
{
  "mcpServers": {
    "chrome-screenshots": {
      "url": "https://YOUR-COOLIFY-DOMAIN/mcp",
      "transport": {
        "type": "http"
      }
    }
  }
}
```

**Important:**
- ✅ Endpoint is `/mcp` (Streamable-HTTP transport)
- ✅ Transport type is `"http"`
- ✅ Replace `YOUR-COOLIFY-DOMAIN` with your actual Coolify URL

**Then restart Claude Desktop and start taking screenshots!** 📸

👉 **[See USAGE.md for complete usage guide, examples, and troubleshooting](USAGE.md)**

---

## Quick Start 🚀

### Using Docker Compose (Recommended)

```bash
# Build and start the server
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the server
docker-compose down
```

The server will be available at `http://localhost:8000`

### Using Docker

```bash
# Build the image
docker build -t chrome-mcp .

# Run the container with critical flags
docker run -d \
  --name chrome-mcp \
  --ipc=host \
  --init \
  -p 8000:8000 \
  -m 2048m \
  chrome-mcp
```

**Critical Docker Flags:**
- `--ipc=host`: Prevents Chromium memory crashes (REQUIRED)
- `--init`: Prevents zombie processes (REQUIRED)
- `-m 2048m`: Minimum 2GB RAM for Playwright

## Available Tools 🛠️

### 1. take_screenshot

Capture a screenshot of any webpage.

**Parameters:**
- `url` (string, required): The URL to capture
- `full_page` (boolean, optional): Capture entire scrollable page (default: false)
- `viewport_width` (int, optional): Browser width in pixels (default: 1920)
- `viewport_height` (int, optional): Browser height in pixels (default: 1080)
- `timeout` (int, optional): Page load timeout in ms (default: 30000)

**Returns:** Base64-encoded PNG image as data URL

**Example:**
```json
{
  "name": "take_screenshot",
  "arguments": {
    "url": "https://www.producthunt.com",
    "full_page": false,
    "viewport_width": 1920,
    "viewport_height": 1080
  }
}
```

### 2. get_page_title

Get the title of a webpage.

**Parameters:**
- `url` (string, required): The URL to fetch
- `timeout` (int, optional): Page load timeout in ms (default: 30000)

**Returns:** Page title as string

### 3. health_check

Check if the server and browser are running properly.

**Parameters:** None

**Returns:** Health status object with connection info

## Testing 🧪

### Local Test (No Docker Required)

```bash
# Install dependencies
pip install playwright httpx
playwright install chromium

# Run test script
python test_screenshot.py
```

This will:
1. Test Playwright locally and save a screenshot to `screenshots/producthunt_test.png`
2. Test the MCP server (if running) and save to `screenshots/producthunt_mcp.png`

### Test with ProductHunt

The test script automatically captures screenshots of ProductHunt.com to verify everything works correctly.

## API Usage 📡

### Using curl

```bash
# Health check
curl -X POST http://localhost:8000/call-tool \
  -H "Content-Type: application/json" \
  -d '{"name": "health_check", "arguments": {}}'

# Take screenshot
curl -X POST http://localhost:8000/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "name": "take_screenshot",
    "arguments": {
      "url": "https://www.producthunt.com",
      "viewport_width": 1920,
      "viewport_height": 1080
    }
  }'
```

### Using Python (httpx)

```python
import httpx
import base64
from pathlib import Path

async def capture_screenshot():
    client = httpx.AsyncClient(timeout=60.0)
    
    response = await client.post(
        "http://localhost:8000/call-tool",
        json={
            "name": "take_screenshot",
            "arguments": {
                "url": "https://www.producthunt.com"
            }
        }
    )
    
    result = response.json()
    data_url = result["result"]
    
    # Extract and save base64 data
    base64_data = data_url.split(",")[1]
    screenshot_bytes = base64.b64decode(base64_data)
    Path("screenshot.png").write_bytes(screenshot_bytes)
    
    await client.aclose()
```

## Deployment 🚢

### Coolify Deployment

1. Create a new service in Coolify
2. Point to your Git repository
3. Coolify will automatically detect `docker-compose.yml`
4. Set any environment variables in Coolify UI
5. Deploy!

### Resource Requirements

- **Minimum RAM**: 2GB (for Playwright + Chromium)
- **Recommended RAM**: 4GB (for concurrent requests)
- **CPU**: 1+ cores recommended
- **Disk**: ~500MB for image + browsers

## Architecture 🏗️

```
┌─────────────────────────────────────┐
│   Docker Container                  │
│                                     │
│  ┌────────────────────────────┐   │
│  │  FastMCP HTTP Server       │   │
│  │  (Port 8000)               │   │
│  └────────┬───────────────────┘   │
│           │                         │
│  ┌────────▼───────────────────┐   │
│  │  Playwright Manager        │   │
│  │  (Browser Pool)            │   │
│  └────────┬───────────────────┘   │
│           │                         │
│  ┌────────▼───────────────────┐   │
│  │  Chromium Browser          │   │
│  │  (Headless)                │   │
│  └────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

### Key Design Decisions

1. **Official Playwright Image**: Uses `mcr.microsoft.com/playwright/python:v1.55.0-noble` with all system dependencies pre-installed

2. **IPC Host Mode**: Critical for preventing Chromium memory issues in Docker

3. **Shared Browser Instance**: One browser instance is reused across requests for efficiency

4. **Async Architecture**: Fully async implementation using `asyncio` and Playwright's async API

5. **Resource Limits**: Docker Compose enforces 2GB memory limit to prevent resource exhaustion

## Troubleshooting 🔧

### Browser Crashes or Memory Issues

**Problem:** Chromium crashes with "Out of memory" or shared memory errors

**Solution:** Ensure you're using `--ipc=host` flag (already in docker-compose.yml)

### Screenshots Not Working

**Problem:** Server runs but screenshots fail

**Solution:** 
1. Check if Chromium is installed: `docker exec chrome-mcp-server playwright install chromium`
2. Verify browser can launch: Check logs with `docker-compose logs`
3. Increase timeout for slow sites: Add `"timeout": 60000` to arguments

### Port Already in Use

**Problem:** Cannot bind to port 8000

**Solution:** Change port mapping in docker-compose.yml:
```yaml
ports:
  - "8080:8000"  # Use 8080 on host instead
```

### High Memory Usage

**Problem:** Container uses too much RAM

**Solution:** 
1. Increase memory limit in docker-compose.yml
2. Reduce concurrent operations
3. Monitor with: `docker stats chrome-mcp-server`

## Development 💻

### Local Development (Without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Run server
python server.py
```

### Project Structure

```
chrome-mcp/
├── Dockerfile                 # Production Docker image
├── docker-compose.yml         # Docker Compose configuration
├── requirements.txt           # Python dependencies
├── server.py                  # FastMCP server implementation
├── test_screenshot.py         # Test script
├── .dockerignore             # Docker build exclusions
├── .gitignore                # Git exclusions
└── README.md                 # This file
```

## Production Considerations 🎯

1. **Security**: Running as root is acceptable for trusted websites. For untrusted content, create a dedicated user.

2. **Monitoring**: Implement health checks and log aggregation for production monitoring.

3. **Rate Limiting**: Consider adding rate limiting for public-facing deployments.

4. **Caching**: Implement response caching for frequently requested screenshots.

5. **Scaling**: For high load, run multiple containers behind a load balancer.

## Based on Research 📚

This implementation follows production best practices identified from:
- Official Microsoft Playwright documentation
- Docker community best practices
- FastMCP deployment guides
- Real-world production deployments

**Key Sources:**
- Playwright Docker: https://playwright.dev/python/docs/docker
- FastMCP HTTP Deployment: https://gofastmcp.com/deployment/http
- Coolify Docker Compose: https://coolify.io/docs/builds/packs/docker-compose

## License 📄

MIT License - feel free to use in your projects!

## Support 💬

Having issues? Please check the troubleshooting section or open an issue on GitHub.
