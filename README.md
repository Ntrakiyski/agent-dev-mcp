# Screenshot MCP Server

A Python-based MCP (Model Context Protocol) server using FastMCP and Playwright that captures screenshots at mobile (370px) and desktop (1200px) viewport widths. Returns image binary data in MCP-compatible format for AI agents.

## Features

- 📱 **Mobile Screenshots**: Capture at 370px viewport width
- 🖥️ **Desktop Screenshots**: Capture at 1200px viewport width
- 🎯 **Full Page or Viewport**: Option to capture entire page or just visible area
- 🤖 **MCP Compatible**: Returns images in format consumable by AI agents
- 🐳 **Docker Ready**: Optimized for deployment with Docker and Coolify

## Tools Available

### `screenshot_mobile`
Captures a screenshot at mobile viewport width (370px).

**Parameters:**
- `url` (string): The URL to capture
- `full_page` (boolean, optional): Whether to capture the full page or just the viewport (default: `True`)

### `screenshot_desktop`
Captures a screenshot at desktop viewport width (1200px).

**Parameters:**
- `url` (string): The URL to capture
- `full_page` (boolean, optional): Whether to capture the full page or just the viewport (default: `True`)

## Local Development

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

The server will start on the default MCP port.

## Docker Deployment

### Using Docker Compose

1. Build and run:
```bash
docker-compose up -d
```

2. The server will be available on port 8000.

### Using Docker directly

1. Build the image:
```bash
docker build -t screenshot-mcp-server .
```

2. Run the container:
```bash
docker run -d -p 8000:8000 screenshot-mcp-server
```

## Coolify Deployment

This project is optimized for deployment on [Coolify](https://coolify.io).

### Deployment Steps:

1. **Push to Git**: Push this repository to your Git provider (GitHub, GitLab, etc.)

2. **Create a New Resource in Coolify**:
   - Select "Docker Compose" as the resource type
   - Connect your Git repository
   - Select the branch you want to deploy

3. **Configure Environment**:
   - No additional environment variables are required for basic operation
   - The server will automatically start on port 8000

4. **Deploy**:
   - Coolify will automatically build and deploy your application
   - The Traefik reverse proxy will handle routing and SSL

5. **Access Your Server**:
   - Your MCP server will be accessible via the domain Coolify assigns
   - Use this URL to connect AI agents to your screenshot service

### Coolify Configuration

The `docker-compose.yml` file is pre-configured for Coolify:
- Automatic restarts on failure
- Unbuffered Python output for real-time logs
- Port 8000 exposed for the MCP server

## Technical Details

### Architecture
- **Runtime**: Python 3.11
- **Framework**: FastMCP
- **Browser**: Playwright (Chromium)
- **Container**: Docker with slim-buster base image

### Dependencies
The Dockerfile includes all necessary system dependencies for running Playwright's Chromium browser in a headless environment:
- NSS libraries for security
- GTK libraries for rendering
- Audio libraries for media support
- Compositor libraries for complex layouts

### Image Optimization
- Multi-layer Docker build for efficient caching
- System dependencies installed first
- Python dependencies cached separately
- Playwright browsers pre-installed in the image

## Usage Example

Once deployed, AI agents can call the MCP tools:

```python
# Mobile screenshot
result = screenshot_mobile(
    url="https://example.com",
    full_page=True
)

# Desktop screenshot
result = screenshot_desktop(
    url="https://example.com",
    full_page=False  # Only capture viewport
)
```

The server returns an `Image` object with base64-encoded PNG data that AI agents can process and display.

## License

MIT License - feel free to use this in your projects!

## Support

For issues or questions, please open an issue in the repository.

