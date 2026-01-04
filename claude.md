# Agent Dev MCP Server

A comprehensive Model Context Protocol (MCP) server providing browser automation, AI vision, GitHub operations, and Coolify deployment management.

## Project Overview

This is a production-ready MCP server built with FastMCP and Playwright that enables:
- **Screenshot & Vision**: Browser automation with AI-powered screenshot analysis
- **Codegen AI Integration**: Agent management and real-time communication
- **GitHub Operations**: Repository management and API integration
- **Coolify Deployment**: Application deployment and server management

## Tech Stack

- **Framework**: FastMCP (Model Context Protocol)
- **Browser Automation**: Playwright (Chromium)
- **Runtime**: Python 3.12+ (async/await)
- **Deployment**: Docker + Docker Compose
- **Cloud Storage**: ImgBB
- **AI Vision**: OpenRouter (Gemini, GPT-4V, Claude)

## Key Files

- `server.py` - Main FastMCP server with all tool implementations
- `Dockerfile` - Production Docker image using official Playwright base
- `docker-compose.yml` - Docker Compose with IPC host mode for Chromium
- `requirements.txt` - Python dependencies (fastmcp, playwright, httpx)

## Development Guidelines

### Environment Setup

Required environment variables:
- `IMGBB_API_KEY` - Screenshot cloud storage
- `OPENROUTER_API_KEY` - AI vision analysis
- `CODEGEN_API_TOKEN` - Codegen AI integration
- `CODEGEN_ORG_ID` - Organization ID
- `GITHUB_API_TOKEN` - GitHub API access
- `COOLIFY_API_TOKEN` - Coolify deployment
- `COOLIFY_API_BASE_URL` - Coolify instance URL
- `COOLIFY_PROJECT_UUID` - Default project
- `COOLIFY_SERVER_UUID` - Default server

### Critical Docker Configuration

The project requires specific Docker flags for Chromium stability:
- `--ipc=host` - Prevents Chromium shared memory crashes (REQUIRED)
- `--init` - Prevents zombie processes (REQUIRED)
- `-m 2048m` - Minimum 2GB RAM for Playwright

### Architecture Patterns

1. **Async-First**: All operations use async/await
2. **Shared Browser**: Single Playwright browser instance reused across requests
3. **Resource Management**: Proper cleanup with context managers
4. **Error Handling**: Comprehensive try/except with detailed error messages

### Adding New Tools

When adding MCP tools to `server.py`:

```python
@mcp.tool()
async def tool_name(param: str) -> dict:
    """
    Tool description for Claude.

    Args:
        param: Parameter description

    Returns:
        Result dictionary with success/data/error
    """
    try:
        # Implementation
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Testing Locally

```bash
# Without Docker
pip install -r requirements.txt
playwright install chromium
python server.py

# With Docker Compose
docker-compose up -d
docker-compose logs -f
```

### Deployment

Deploy to Coolify:
1. Connect GitHub repository
2. Coolify auto-detects `docker-compose.yml`
3. Set environment variables in Coolify UI
4. Click "Deploy"

MCP endpoint: `https://YOUR-DOMAIN/mcp`

## Common Tasks

### Taking Screenshots
- Use full_page=true for complete page capture
- Set viewport_width/height for responsive testing
- upload_to_cloud=true for ImgBB hosting

### GitHub Integration
- Create repos with `github_create_repo`
- List/search repos with proper pagination
- Use auto_init=true for README initialization

### Coolify Deployment
- List apps/servers to get UUIDs
- Use instant_deploy=true for immediate deployment
- Supports docker-compose and dockerfile buildpacks

## Resource Requirements

- **RAM**: 2GB minimum, 4GB recommended
- **CPU**: 1+ cores
- **Disk**: ~500MB for image + browsers
- **Network**: Stable connection for browser operations

## Best Practices

1. Always set appropriate timeouts for slow websites
2. Use environment variables for API keys (never hardcode)
3. Monitor Docker stats for resource usage
4. Implement health checks before production deployment
5. Use proper error handling in all MCP tools
6. Test with docker-compose before deploying

## Troubleshooting

- **Browser crashes**: Verify `--ipc=host` is set
- **Memory issues**: Increase Docker memory limit
- **Screenshots fail**: Check Playwright installation and network
- **Port conflicts**: Change port mapping in docker-compose.yml
