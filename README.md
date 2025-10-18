# Chrome MCP Server 🌐📸

A production-ready Model Context Protocol (MCP) server that provides comprehensive automation capabilities including browser automation, AI vision, GitHub operations, and Coolify deployment management. Built with FastMCP and Playwright for maximum reliability and performance.

## Features ✨

### 🖼️ Screenshot & Vision
- **Screenshot Capture**: Take full-page or viewport screenshots with ImgBB cloud storage
- **AI Vision Analysis**: Ask questions about screenshots using OpenRouter LLMs
- **Configurable Parameters**: Custom delay, viewport sizes, and full-page capture
- **Page Information**: Extract page titles and metadata

### 🤖 Codegen AI Integration
- **Agent Management**: Create and manage AI agent runs
- **Real-time Communication**: Reply to and interact with running agents
- **Status Tracking**: List and monitor all agent runs
- **Cancellation Control**: Stop agent runs when needed

### 🐙 GitHub Operations
- **Repository Management**: Create new GitHub repositories programmatically
- **Repository Search**: Search and list accessible repositories
- **Full API Integration**: Comprehensive GitHub REST API support

### 🚀 Coolify Deployment Management
- **Application Management**: List, create, restart, and stop applications
- **Server Monitoring**: View server details and status
- **One-Click Deployment**: Create applications from GitHub repos instantly

### 🔧 System Features
- **Health Monitoring**: Built-in health check endpoint
- **Production-Ready**: Optimized for Docker deployment with proper resource management
- **FastMCP Integration**: HTTP transport for remote access
- **Cloud Storage**: Automatic ImgBB integration for screenshot hosting

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

### 📸 Screenshot & Vision Tools

#### `take_screenshot`
Capture a screenshot and optionally upload to ImgBB cloud storage.

**Parameters:**
- `url` (string, required): The URL to capture
- `full_page` (boolean, optional): Capture entire scrollable page (default: true)
- `viewport_width` (int, optional): Browser width in pixels (default: 1920)
- `viewport_height` (int, optional): Browser height in pixels (default: 1080)
- `timeout` (int, optional): Page load timeout in ms (default: 30000)
- `delay` (int, optional): Additional delay after page load in ms (default: 0)
- `upload_to_cloud` (boolean, optional): Upload to ImgBB (default: true)

**Returns:** Object with `success`, `message`, `public_url` (if uploaded), and optionally `screenshot_base64`

#### `ask_about_screenshot`
Take a screenshot and ask AI questions about it using vision models.

**Parameters:**
- `url` (string, required): The URL to capture
- `question` (string, required): Question to ask about the screenshot
- `model` (string, optional): OpenRouter model ID (default: "google/gemini-flash-1.5-8b")
- `full_page` (boolean, optional): Capture entire page (default: true)
- `viewport_width` (int, optional): Browser width in pixels (default: 1920)
- `viewport_height` (int, optional): Browser height in pixels (default: 1080)

**Returns:** AI's analysis response based on the screenshot

#### `get_page_title`
Get the title of a webpage.

**Parameters:**
- `url` (string, required): The URL to fetch
- `timeout` (int, optional): Page load timeout in ms (default: 30000)

**Returns:** Page title as string

#### `health_check`
Check server health and configuration status.

**Returns:** Health status including browser, ImgBB, OpenRouter, Codegen, GitHub, and Coolify configuration

---

### 🤖 Codegen AI Tools

#### `codegen_create_agent_run`
Create a new Codegen AI agent run.

**Parameters:**
- `prompt` (string, required): The instruction for the agent
- `repo_name` (string, optional): Repository name
- `org_id` (string, optional): Organization ID (uses env var if not provided)

**Returns:** Agent run details including `run_id` and `status`

#### `codegen_get_agent_run`
Get the status and details of an agent run.

**Parameters:**
- `run_id` (string, required): The agent run ID

**Returns:** Full agent run details including messages and status

#### `codegen_reply_to_agent_run`
Send a message to a running agent.

**Parameters:**
- `run_id` (string, required): The agent run ID
- `message` (string, required): Message to send to the agent

**Returns:** Updated agent run details

#### `codegen_list_agent_runs`
List all agent runs for the organization.

**Parameters:**
- `org_id` (string, optional): Organization ID (uses env var if not provided)
- `limit` (int, optional): Maximum number of runs to return (default: 10)

**Returns:** List of agent runs

#### `codegen_cancel_agent_run`
Cancel a running agent.

**Parameters:**
- `run_id` (string, required): The agent run ID to cancel

**Returns:** Cancellation confirmation

---

### 🐙 GitHub Tools

#### `github_create_repo`
Create a new GitHub repository.

**Parameters:**
- `name` (string, required): Repository name
- `description` (string, optional): Repository description
- `private` (boolean, optional): Make repository private (default: false)
- `auto_init` (boolean, optional): Initialize with README (default: true)

**Returns:** Repository details including clone URLs

#### `github_list_repos`
List accessible GitHub repositories.

**Parameters:**
- `affiliation` (string, optional): Filter by affiliation (default: "owner,collaborator,organization_member")
- `sort` (string, optional): Sort by: "created", "updated", "pushed", "full_name" (default: "updated")
- `per_page` (int, optional): Results per page (default: 30, max: 100)

**Returns:** List of repositories

#### `github_search_repo`
Search for repositories.

**Parameters:**
- `query` (string, required): Search query
- `sort` (string, optional): Sort by: "stars", "forks", "updated" (default: "updated")
- `per_page` (int, optional): Results per page (default: 30)

**Returns:** Search results with repositories

---

### 🚀 Coolify Tools

#### `coolify_list_applications`
List all Coolify applications.

**Returns:** List of all applications with their details

#### `coolify_list_servers`
List all Coolify servers.

**Returns:** List of all servers

#### `coolify_get_server_details`
Get detailed information about a specific server.

**Parameters:**
- `server_uuid` (string, required): Server UUID

**Returns:** Detailed server information

#### `coolify_create_application`
Create a new application in Coolify.

**Parameters:**
- `git_repository` (string, required): Git repository URL
- `name` (string, required): Application name
- `git_branch` (string, optional): Git branch (default: "main")
- `build_pack` (string, optional): Build pack type (default: "dockercompose")
- `docker_compose_location` (string, optional): Path to docker-compose file (default: "docker-compose.yml")
- `instant_deploy` (boolean, optional): Deploy immediately (default: true)

**Returns:** Application details including UUID

#### `coolify_restart_application`
Restart a Coolify application.

**Parameters:**
- `app_uuid` (string, required): Application UUID

**Returns:** Restart confirmation

#### `coolify_stop_application`
Stop a Coolify application.

**Parameters:**
- `app_uuid` (string, required): Application UUID

**Returns:** Stop confirmation

## Environment Variables 🔐

Configure the server using these environment variables:

### Required for Screenshot Upload
- `IMGBB_API_KEY`: ImgBB API key for screenshot cloud storage

### Required for AI Vision
- `OPENROUTER_API_KEY`: OpenRouter API key for AI vision analysis

### Required for Codegen Integration
- `CODEGEN_API_TOKEN`: Codegen API authentication token
- `CODEGEN_ORG_ID`: Your Codegen organization ID

### Required for GitHub Integration
- `GITHUB_API_TOKEN`: GitHub personal access token with repo permissions

### Required for Coolify Integration
- `COOLIFY_API_TOKEN`: Coolify API authentication token
- `COOLIFY_API_BASE_URL`: Coolify instance URL (e.g., "https://coolify.yourdomain.com/api/v1")
- `COOLIFY_PROJECT_UUID`: Default Coolify project UUID
- `COOLIFY_SERVER_UUID`: Default Coolify server UUID

**Note:** All integrations will show as "not configured" in health checks if their respective environment variables are not set. The server will still function for features that don't require those integrations.

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
├── server.py                  # FastMCP server with all integrations
├── .dockerignore             # Docker build exclusions
├── .gitignore                # Git exclusions
├── README.md                 # This file
├── DEPLOY.md                 # Coolify deployment guide
└── USAGE.md                  # Detailed usage examples
```

## Production Considerations 🎯

1. **Security**: Running as root is acceptable for trusted websites. For untrusted content, create a dedicated user.

2. **Monitoring**: Implement health checks and log aggregation for production monitoring.

3. **Rate Limiting**: Consider adding rate limiting for public-facing deployments.

4. **Caching**: Implement response caching for frequently requested screenshots.

5. **Scaling**: For high load, run multiple containers behind a load balancer.

## Integration Examples 💡

### Taking Screenshots with AI Analysis

```python
# Take a screenshot and ask questions about it
result = await ask_about_screenshot(
    url="https://producthunt.com",
    question="What are the top 3 products shown on this page?",
    model="google/gemini-flash-1.5-8b"
)
print(result['answer'])
```

### Creating GitHub Repos and Deploying to Coolify

```python
# Create a GitHub repository
repo = await github_create_repo(
    name="my-new-app",
    description="A cool new application",
    private=False
)

# Deploy it to Coolify
app = await coolify_create_application(
    git_repository=repo['clone_url'],
    name="my-new-app",
    instant_deploy=True
)
```

### Managing Codegen AI Agents

```python
# Create an agent to work on your code
run = await codegen_create_agent_run(
    prompt="Add input validation to the login form",
    repo_name="my-repo"
)

# Check its progress
status = await codegen_get_agent_run(run_id=run['run_id'])

# Send additional instructions
await codegen_reply_to_agent_run(
    run_id=run['run_id'],
    message="Also add error handling for network failures"
)
```

## License 📄

MIT License - feel free to use in your projects!

## Support 💬

Having issues? Please check the troubleshooting section or open an issue on GitHub.
