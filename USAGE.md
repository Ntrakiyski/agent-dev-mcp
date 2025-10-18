# 📸 Using Chrome MCP Server

Your Chrome MCP server is running with **Streamable-HTTP** transport on the `/mcp` endpoint.

---

## 🔌 Quick Start: Claude Desktop Configuration

### **Step 1: Find Your Server URL**

Your MCP server is deployed on Coolify. Find your URL in:
- Coolify Dashboard → Your Service → **Domains** section
- Example: `https://ms804wwgsswsocs844wko84k.159.69.35.245.sslip.io`

### **Step 2: Configure Claude Desktop**

Add this to your Claude Desktop config:

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

**Replace `YOUR-COOLIFY-DOMAIN` with your actual Coolify URL!**

**Example:**
```json
{
  "mcpServers": {
    "chrome-screenshots": {
      "url": "https://ms804wwgsswsocs844wko84k.159.69.35.245.sslip.io/mcp",
      "transport": {
        "type": "http"
      }
    }
  }
}
```

### **Step 3: Restart Claude Desktop**

Close and reopen Claude Desktop completely for the changes to take effect.

### **Step 4: Test It!**

Ask Claude:
```
Take a screenshot of https://producthunt.com
```

Claude will use your MCP server to capture a full-page screenshot! 📸

---

## 🎯 Understanding the Endpoint

Your server uses **Streamable-HTTP** (FastMCP 2.0):

- **Endpoint:** `/mcp` (NOT `/sse`)
- **Transport:** `http` (NOT `sse`)
- **Method:** POST requests with JSON-RPC 2.0
- **Protocol:** Streamable-HTTP (optimized for large responses like screenshots)

---

## 🧪 Testing the Server

### **Test with cURL:**

```bash
# Replace with your actual Coolify domain
SERVER_URL="https://YOUR-COOLIFY-DOMAIN"

# Test 1: List available tools
curl -X POST "$SERVER_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'

# Test 2: Take a screenshot
curl -X POST "$SERVER_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "take_screenshot",
      "arguments": {
        "url": "https://producthunt.com",
        "full_page": true
      }
    }
  }'
```

### **Test with MCP Inspector:**

```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Connect to your server (replace with your URL)
npx @modelcontextprotocol/inspector https://YOUR-COOLIFY-DOMAIN/mcp
```

This opens a web interface where you can:
- ✅ See all available tools
- ✅ Test parameters interactively
- ✅ View responses in real-time

---

## 📸 Using the Screenshot Tool

### **Available Tools:**

#### **1. `take_screenshot`** - Capture webpage screenshots

**Parameters:**
| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `url` | string | - | ✅ Yes | URL to screenshot |
| `full_page` | boolean | `true` | ❌ No | Capture entire scrollable page |
| `viewport_width` | number | `1920` | ❌ No | Browser viewport width in pixels |
| `viewport_height` | number | `1080` | ❌ No | Browser viewport height in pixels |
| `delay` | number | `0` | ❌ No | Wait time in milliseconds after page load |
| `timeout` | number | `30000` | ❌ No | Page load timeout in milliseconds |

**Returns:**
- Base64-encoded PNG image
- Format: `data:image/png;base64,iVBORw0KGgo...`

**Examples:**

```json
// Basic full-page screenshot
{
  "url": "https://producthunt.com"
}

// Mobile screenshot (iPhone 12 Pro)
{
  "url": "https://example.com",
  "viewport_width": 390,
  "viewport_height": 844
}

// Tablet screenshot (iPad)
{
  "url": "https://example.com",
  "viewport_width": 768,
  "viewport_height": 1024
}

// Viewport-only screenshot (no scrolling)
{
  "url": "https://example.com",
  "full_page": false
}

// Screenshot with delay for animations
{
  "url": "https://animated-site.com",
  "delay": 3000
}

// Screenshot with custom timeout
{
  "url": "https://slow-loading-site.com",
  "timeout": 60000
}
```

#### **2. `get_page_title`** - Extract page title

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | ✅ Yes | URL to get title from |

**Returns:**
- Page title as string

**Example:**
```json
{
  "url": "https://producthunt.com"
}
// Returns: "Product Hunt – The best new products in tech."
```

#### **3. `health_check`** - Server health status

**Parameters:** None

**Returns:**
- Server status and info

**Example:**
```json
{}
// Returns: {"status": "ok", "chromium": "installed", ...}
```

---

## 💻 Custom Client Examples

### **Python Client:**

```python
import httpx
import asyncio

async def use_mcp_server():
    server_url = "https://YOUR-COOLIFY-DOMAIN/mcp"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Initialize connection
        init_response = await client.post(
            server_url,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "my-client",
                        "version": "1.0.0"
                    }
                }
            }
        )
        print("✅ Connected:", init_response.json())
        
        # List available tools
        tools_response = await client.post(
            server_url,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            }
        )
        print("📋 Available tools:", tools_response.json())
        
        # Take a screenshot
        screenshot_response = await client.post(
            server_url,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "take_screenshot",
                    "arguments": {
                        "url": "https://producthunt.com",
                        "full_page": True,
                        "viewport_width": 1920,
                        "viewport_height": 1080
                    }
                }
            }
        )
        
        result = screenshot_response.json()
        if "result" in result:
            print("✅ Screenshot captured!")
            # The base64 image is in result['result']['content'][0]['text']
            base64_image = result['result']['content'][0]['text']
            print(f"📸 Image size: {len(base64_image)} bytes")
        else:
            print("❌ Error:", result.get("error"))

# Run the client
asyncio.run(use_mcp_server())
```

### **JavaScript/TypeScript Client:**

```javascript
const fetch = require('node-fetch');

async function useMCPServer() {
  const serverUrl = "https://YOUR-COOLIFY-DOMAIN/mcp";
  
  // Initialize
  const initResponse = await fetch(serverUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method: "initialize",
      params: {
        protocolVersion: "2024-11-05",
        capabilities: {},
        clientInfo: {
          name: "my-client",
          version: "1.0.0"
        }
      }
    })
  });
  console.log("✅ Connected:", await initResponse.json());
  
  // List tools
  const toolsResponse = await fetch(serverUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 2,
      method: "tools/list"
    })
  });
  console.log("📋 Available tools:", await toolsResponse.json());
  
  // Take screenshot
  const screenshotResponse = await fetch(serverUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 3,
      method: "tools/call",
      params: {
        name: "take_screenshot",
        arguments: {
          url: "https://producthunt.com",
          full_page: true,
          viewport_width: 1920,
          viewport_height: 1080
        }
      }
    })
  });
  
  const result = await screenshotResponse.json();
  if (result.result) {
    console.log("✅ Screenshot captured!");
    const base64Image = result.result.content[0].text;
    console.log(`📸 Image size: ${base64Image.length} bytes`);
  } else {
    console.log("❌ Error:", result.error);
  }
}

useMCPServer();
```

---

## 📱 Common Viewport Sizes

Use these for different device screenshots:

### **Mobile Devices:**
```json
// iPhone 12/13/14 Pro
{"viewport_width": 390, "viewport_height": 844}

// iPhone 12/13/14 Pro Max
{"viewport_width": 428, "viewport_height": 926}

// Samsung Galaxy S21
{"viewport_width": 360, "viewport_height": 800}

// Google Pixel 5
{"viewport_width": 393, "viewport_height": 851}
```

### **Tablets:**
```json
// iPad (portrait)
{"viewport_width": 768, "viewport_height": 1024}

// iPad Pro 12.9" (portrait)
{"viewport_width": 1024, "viewport_height": 1366}

// iPad (landscape)
{"viewport_width": 1024, "viewport_height": 768}
```

### **Desktop:**
```json
// Standard HD
{"viewport_width": 1920, "viewport_height": 1080}

// MacBook Pro 13"
{"viewport_width": 1440, "viewport_height": 900}

// MacBook Pro 16"
{"viewport_width": 1728, "viewport_height": 1117}

// 4K Display
{"viewport_width": 3840, "viewport_height": 2160}
```

---

## 🔐 Security Best Practices

Your MCP server is **publicly accessible**. Anyone with the URL can use it.

### **Option 1: Coolify Basic Auth (Recommended)**

1. In Coolify, go to your service
2. Enable **"Basic Authentication"**
3. Set username and password
4. Update your client config:

```json
{
  "mcpServers": {
    "chrome-screenshots": {
      "url": "https://YOUR-USERNAME:YOUR-PASSWORD@YOUR-COOLIFY-DOMAIN/mcp",
      "transport": {
        "type": "http"
      }
    }
  }
}
```

**Note:** Replace `YOUR-USERNAME`, `YOUR-PASSWORD`, and `YOUR-COOLIFY-DOMAIN` with actual values.

### **Option 2: Limit Usage**

Monitor your server logs and restrict access by:
- Setting up rate limiting in Coolify
- Using Cloudflare Access for email-based auth
- Implementing custom API key authentication

---

## 🐛 Troubleshooting

### **Issue: "Connection refused" or timeout**

**Check:**
1. Is the container running in Coolify?
2. Is the URL correct? (Should end with `/mcp`)
3. Are you using HTTPS? (Coolify provides it automatically)

**Solution:**
```bash
# Test if server is responding
curl -X POST https://YOUR-COOLIFY-DOMAIN/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### **Issue: Screenshot is blank or incomplete**

**Cause:** Page hasn't fully loaded or animations are still running

**Solution:** Add a delay:
```json
{
  "url": "https://site.com",
  "delay": 3000
}
```

### **Issue: Screenshot timeout**

**Cause:** Page is very slow to load

**Solution:** Increase timeout:
```json
{
  "url": "https://slow-site.com",
  "timeout": 60000
}
```

### **Issue: "406 Not Acceptable" or "400 Bad Request"**

**Cause:** Wrong HTTP method or missing headers

**Solution:**
- Use POST (not GET)
- Include `Content-Type: application/json` header
- Send valid JSON-RPC 2.0 format

### **Issue: Claude Desktop not connecting**

**Check:**
1. Config file is valid JSON (use a JSON validator)
2. URL ends with `/mcp` (not `/sse`)
3. Transport type is `"http"` (not `"sse"`)
4. Claude Desktop was restarted after config change

---

## 📊 Monitoring

### **Check Server Logs in Coolify:**

1. Go to your service in Coolify
2. Click **"Logs"**
3. Look for:
   ```
   ✅ FastMCP server running on port 8000
   ✅ Taking screenshot of https://...
   ✅ Screenshot captured successfully
   ```

### **Server Metrics:**

Watch for:
- **Memory usage:** Should be ~500MB-1GB during screenshots
- **CPU usage:** Spikes during screenshot capture (normal)
- **Response time:** Usually 2-5 seconds per screenshot

---

## 🎉 Quick Reference

**✅ Correct Configuration:**
```json
{
  "mcpServers": {
    "chrome-screenshots": {
      "url": "https://YOUR-COOLIFY-DOMAIN/mcp",
      "transport": {"type": "http"}
    }
  }
}
```

**✅ Correct Endpoint:** `POST https://YOUR-COOLIFY-DOMAIN/mcp`

**✅ Transport Type:** Streamable-HTTP (FastMCP 2.0)

**❌ Wrong:** `/sse` endpoint, `"sse"` transport, GET requests

---

## 📚 Additional Resources

- **PARAMETERS.md** - Complete parameter reference
- **DEPLOY.md** - Coolify deployment guide
- **README.md** - Project overview
- **FastMCP Docs** - https://gofastmcp.com
- **MCP Protocol** - https://modelcontextprotocol.io

---

## 🚀 Ready to Use!

Your MCP server is:
- ✅ Deployed on Coolify
- ✅ Running with Chromium
- ✅ Using Streamable-HTTP transport
- ✅ Available at `/mcp` endpoint
- ✅ Ready for Claude Desktop and custom clients

**Just add the config and start taking screenshots!** 📸
