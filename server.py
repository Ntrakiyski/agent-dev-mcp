"""
Chrome MCP Server with Playwright
Production-ready screenshot service using FastMCP with ImgBB cloud storage
"""

import asyncio
import base64
import logging
import os
from typing import Optional
from pathlib import Path

from fastmcp import FastMCP
from playwright.async_api import async_playwright, Browser, Page, Playwright
import aiohttp
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("chrome-screenshot-server")

# ImgBB API Configuration - read from environment variable
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "")

# OpenRouter API Configuration - read from environment variable
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Global playwright and browser instances (shared across requests for efficiency)
playwright_instance: Optional[Playwright] = None
browser: Optional[Browser] = None


async def get_browser() -> Browser:
    """Get or create browser instance"""
    global playwright_instance, browser
    
    if playwright_instance is None:
        logger.info("Starting Playwright...")
        playwright_instance = await async_playwright().start()
    
    if browser is None or not browser.is_connected():
        logger.info("Launching Chromium browser...")
        browser = await playwright_instance.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',  # Required for running as root in Docker
                '--disable-dev-shm-usage',  # Overcome limited resource problems
                '--disable-blink-features=AutomationControlled',  # Avoid detection
            ]
        )
        logger.info("Browser launched successfully")
    return browser


async def upload_to_imgbb(screenshot_b64: str) -> str:
    """
    Upload base64 image to ImgBB and return public URL
    
    Args:
        screenshot_b64: Base64 encoded image string (without data:image prefix)
        
    Returns:
        Public URL of uploaded image (e.g., https://i.ibb.co/xxxxx/image.png)
    """
    logger.info("Uploading screenshot to ImgBB...")
    
    if not IMGBB_API_KEY:
        raise ValueError("IMGBB_API_KEY environment variable is not set")
    
    url = f"https://api.imgbb.com/1/upload?key={IMGBB_API_KEY}"
    
    data = aiohttp.FormData()
    data.add_field('image', screenshot_b64)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                result = await response.json()
                
                if result.get('success'):
                    public_url = result['data']['url']
                    display_url = result['data']['display_url']
                    logger.info(f"Image uploaded successfully: {display_url}")
                    return display_url
                else:
                    error_msg = result.get('error', {}).get('message', 'Unknown error')
                    raise Exception(f"ImgBB upload failed: {error_msg}")
                    
    except Exception as e:
        error_msg = f"Failed to upload to ImgBB: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


@mcp.tool()
async def take_screenshot(
    url: str,
    full_page: bool = True,
    viewport_width: int = 1920,
    viewport_height: int = 1080,
    timeout: int = 30000,
    delay: int = 0,
    upload_to_cloud: bool = True
) -> dict:
    """
    Take a screenshot of a web page and upload to ImgBB cloud storage.
    
    Args:
        url: The URL to capture (e.g., "https://producthunt.com")
        full_page: If True, captures entire scrollable page (default: True)
        viewport_width: Browser viewport width in pixels (default: 1920)
        viewport_height: Browser viewport height in pixels (default: 1080)
        timeout: Page load timeout in milliseconds (default: 30000)
        delay: Additional delay in ms after page loads (default: 0)
        upload_to_cloud: If True, uploads to ImgBB. If False, returns base64 (default: True)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'public_url': str (if upload_to_cloud=True),
            'screenshot_base64': str (always included)
        }
    
    Examples:
        - take_screenshot("https://producthunt.com")
        - take_screenshot("https://example.com", upload_to_cloud=False)
        - take_screenshot("https://example.com", delay=2000)
    """
    page_type = "full page" if full_page else "viewport only"
    logger.info(f"Taking screenshot of {url} ({page_type}, viewport: {viewport_width}x{viewport_height})")
    
    try:
        # Get browser instance
        browser = await get_browser()
        
        # Create a new page
        page = await browser.new_page(
            viewport={'width': viewport_width, 'height': viewport_height}
        )
        
        try:
            # Navigate to URL
            logger.info(f"Navigating to {url}...")
            await page.goto(url, timeout=timeout, wait_until='load')
            logger.info("Page loaded")
            
            # Wait for network idle
            try:
                await page.wait_for_load_state('networkidle', timeout=5000)
                logger.info("Network idle")
            except Exception as e:
                logger.warning(f"Network idle timeout: {e}")
            
            # Additional delay if specified
            if delay > 0:
                logger.info(f"Waiting {delay}ms...")
                await asyncio.sleep(delay / 1000)
            
            # Take screenshot
            logger.info("Capturing screenshot...")
            screenshot_bytes = await page.screenshot(
                full_page=full_page,
                type='png'
            )
            
            # Encode to base64
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            logger.info(f"Screenshot captured ({len(screenshot_bytes)} bytes)")
            
            # Return base64 if cloud upload disabled
            if not upload_to_cloud:
                return {
                    'success': True,
                    'message': 'Screenshot captured successfully',
                    'screenshot_base64': f"data:image/png;base64,{screenshot_b64}"
                }
            
            # Upload to ImgBB
            public_url = await upload_to_imgbb(screenshot_b64)
            
            return {
                'success': True,
                'message': 'Screenshot uploaded successfully',
                'public_url': public_url
            }
            
        finally:
            await page.close()
            logger.info("Page closed")
            
    except Exception as e:
        error_msg = f"Failed to capture screenshot: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }


@mcp.tool()
async def get_page_title(url: str, timeout: int = 30000) -> str:
    """
    Get the title of a web page.
    
    Args:
        url: The URL to fetch (e.g., "https://producthunt.com")
        timeout: Page load timeout in milliseconds (default: 30000)
    
    Returns:
        The page title as a string
    """
    logger.info(f"Getting title for {url}")
    
    try:
        browser = await get_browser()
        page = await browser.new_page()
        
        try:
            await page.goto(url, timeout=timeout, wait_until='domcontentloaded')
            title = await page.title()
            logger.info(f"Page title: {title}")
            return title
        finally:
            await page.close()
            
    except Exception as e:
        error_msg = f"Failed to get page title: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


@mcp.tool()
async def health_check() -> dict:
    """Check server health and configuration"""
    try:
        browser = await get_browser()
        is_connected = browser.is_connected()
        imgbb_configured = bool(IMGBB_API_KEY)
        openrouter_configured = bool(OPENROUTER_API_KEY)
        
        all_healthy = is_connected and imgbb_configured and openrouter_configured
        
        warnings = []
        if not imgbb_configured:
            warnings.append("ImgBB API key not configured")
        if not openrouter_configured:
            warnings.append("OpenRouter API key not configured")
        if not is_connected:
            warnings.append("Browser not connected")
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "browser_connected": is_connected,
            "imgbb_configured": imgbb_configured,
            "openrouter_configured": openrouter_configured,
            "message": "Server is fully operational" if all_healthy else f"Warnings: {', '.join(warnings)}"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "browser_connected": False,
            "imgbb_configured": False,
            "openrouter_configured": False,
            "message": f"Error: {str(e)}"
        }


@mcp.tool()
async def ask_about_screenshot(
    prompt: str,
    image_url: str,
    model: str = "qwen/qwen-2.5-vl-72b-instruct",
    api_key: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None
) -> dict:
    """
    Analyze a screenshot using OpenRouter's vision-capable LLM models.
    
    This tool sends an image URL and a text prompt to OpenRouter's API and returns
    the model's analysis. Perfect for extracting information from screenshots,
    describing UI elements, reading text from images, or any vision-based tasks.
    
    Args:
        prompt: Your question or instruction about the image (e.g., "What's in this image?", "Describe the UI layout")
        image_url: Public URL of the image to analyze (e.g., from ImgBB, or any accessible image URL)
        model: OpenRouter model ID (default: "qwen/qwen-2.5-vl-72b-instruct")
               Other vision models: "google/gemini-2.0-flash-001", "anthropic/claude-3.5-sonnet", etc.
        api_key: OpenRouter API key (optional, uses OPENROUTER_API_KEY env var if not provided)
        max_tokens: Maximum tokens in response (optional, uses model default)
        temperature: Sampling temperature 0.0-1.0 (optional, uses model default)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'response': str (the model's answer),
            'model': str (model used),
            'usage': dict (token usage info)
        }
    
    Examples:
        - ask_about_screenshot("What's in this image?", "https://i.ibb.co/xxxxx/screenshot.png")
        - ask_about_screenshot("Describe the layout", "https://example.com/image.png", model="google/gemini-2.0-flash-001")
        - ask_about_screenshot("What text is visible?", "https://i.ibb.co/xxxxx/ui.png", temperature=0.2)
    """
    logger.info(f"Analyzing image with model: {model}")
    logger.info(f"Image URL: {image_url}")
    logger.info(f"Prompt: {prompt[:100]}...")
    
    # Get API key from parameter or environment variable
    api_key_to_use = api_key or OPENROUTER_API_KEY
    
    if not api_key_to_use:
        error_msg = "OpenRouter API key not provided. Set OPENROUTER_API_KEY env var or pass api_key parameter."
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }
    
    try:
        # Prepare OpenRouter API request
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key_to_use}",
            "Content-Type": "application/json"
        }
        
        # Build messages with vision content
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]
            }
        ]
        
        # Build payload with optional parameters
        payload = {
            "model": model,
            "messages": messages
        }
        
        # Add optional parameters if provided
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if temperature is not None:
            payload["temperature"] = temperature
        
        logger.info(f"Sending request to OpenRouter API...")
        
        # Make synchronous request (OpenRouter uses standard requests, not async)
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Received response from OpenRouter")
        
        # Extract the response text
        if 'choices' in result and len(result['choices']) > 0:
            response_text = result['choices'][0]['message']['content']
            usage_info = result.get('usage', {})
            
            return {
                'success': True,
                'message': 'Image analyzed successfully',
                'response': response_text,
                'model': model,
                'usage': usage_info
            }
        else:
            error_msg = "Unexpected response format from OpenRouter API"
            logger.error(f"{error_msg}: {result}")
            return {
                'success': False,
                'message': error_msg,
                'raw_response': result
            }
            
    except requests.exceptions.RequestException as e:
        error_msg = f"OpenRouter API request failed: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }
    except Exception as e:
        error_msg = f"Failed to analyze image: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }


# =============================================================================
# CODEGEN AGENT TOOLS
# =============================================================================

# Codegen API Configuration - read from environment variables
CODEGEN_ORG_ID = os.getenv("CODEGEN_ORG_ID", "")
CODEGEN_API_TOKEN = os.getenv("CODEGEN_API_TOKEN", "")
CODEGEN_BASE_URL = os.getenv("CODEGEN_BASE_URL", "https://codegen-sh-rest-api.modal.run")


@mcp.tool()
async def codegen_create_agent_run(
    prompt: str,
    org_id: Optional[str] = None,
    api_token: Optional[str] = None
) -> dict:
    """
    Create a new Codegen agent run with a given prompt.
    
    Args:
        prompt: The instruction for the Codegen agent to execute (required)
        org_id: Organization ID (optional, defaults to CODEGEN_ORG_ID env var)
        api_token: API token (optional, defaults to CODEGEN_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'agent_run_id': str,
            'status': str,
            'web_url': str,
            'result': Any (if available)
        }
    
    Examples:
        - codegen_create_agent_run("Review PR #123")
        - codegen_create_agent_run("Fix the bug in auth.py", org_id="123", api_token="token")
    """
    logger.info(f"Creating Codegen agent run with prompt: {prompt[:50]}...")
    
    # Use provided values or fall back to environment variables
    org = org_id or CODEGEN_ORG_ID
    token = api_token or CODEGEN_API_TOKEN
    
    if not org or not token:
        return {
            'success': False,
            'message': 'CODEGEN_ORG_ID and CODEGEN_API_TOKEN environment variables must be set'
        }
    
    try:
        # Prepare API request
        url = f"{CODEGEN_BASE_URL}/v1/organizations/{org}/agent/run"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {"prompt": prompt}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                result = await response.json()
                
                if response.status == 200 or response.status == 201:
                    logger.info(f"Agent run created successfully: {result.get('id')}")
                    return {
                        'success': True,
                        'message': 'Agent run created successfully',
                        'agent_run_id': str(result.get('id')),
                        'status': result.get('status', 'pending'),
                        'web_url': result.get('web_url', ''),
                        'result': result.get('result')
                    }
                else:
                    error_msg = result.get('detail', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to create agent run: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }


@mcp.tool()
async def codegen_get_agent_run(
    agent_run_id: str,
    org_id: Optional[str] = None,
    api_token: Optional[str] = None
) -> dict:
    """
    Get the status and details of a specific Codegen agent run.
    
    Args:
        agent_run_id: ID of the agent run to retrieve (required)
        org_id: Organization ID (optional, defaults to CODEGEN_ORG_ID env var)
        api_token: API token (optional, defaults to CODEGEN_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'agent_run_id': str,
            'status': str (pending, running, completed, failed, etc.),
            'web_url': str,
            'result': Any (if available)
        }
    
    Examples:
        - codegen_get_agent_run("123456")
        - codegen_get_agent_run("123456", org_id="123", api_token="token")
    """
    logger.info(f"Getting Codegen agent run: {agent_run_id}")
    
    # Use provided values or fall back to environment variables
    org = org_id or CODEGEN_ORG_ID
    token = api_token or CODEGEN_API_TOKEN
    
    if not org or not token:
        return {
            'success': False,
            'message': 'CODEGEN_ORG_ID and CODEGEN_API_TOKEN environment variables must be set'
        }
    
    try:
        # Prepare API request
        url = f"{CODEGEN_BASE_URL}/v1/organizations/{org}/agent/run/{agent_run_id}"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                result = await response.json()
                
                if response.status == 200:
                    logger.info(f"Agent run retrieved: {agent_run_id} - Status: {result.get('status')}")
                    return {
                        'success': True,
                        'message': 'Agent run retrieved successfully',
                        'agent_run_id': str(result.get('id')),
                        'status': result.get('status', 'unknown'),
                        'web_url': result.get('web_url', ''),
                        'result': result.get('result')
                    }
                else:
                    error_msg = result.get('detail', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to get agent run: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }


@mcp.tool()
async def codegen_reply_to_agent_run(
    agent_run_id: int,
    prompt: str,
    images: Optional[list[str]] = None,
    org_id: Optional[str] = None,
    api_token: Optional[str] = None
) -> dict:
    """
    Resume a paused Codegen agent run with additional instructions or feedback.
    
    Args:
        agent_run_id: ID of the agent run to resume (required, must be an integer)
        prompt: Your prompt/message to the agent (required)
        images: Optional list of base64 encoded data URIs representing images to be processed
        org_id: Organization ID (optional, defaults to CODEGEN_ORG_ID env var)
        api_token: API token (optional, defaults to CODEGEN_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'agent_run_id': int,
            'status': str,
            'result': dict (full agent run response)
        }
    
    Examples:
        - codegen_reply_to_agent_run(123456, "Please also add unit tests")
        - codegen_reply_to_agent_run(123456, "Looks good, ship it!", org_id="123")
        - codegen_reply_to_agent_run(123456, "Check this screenshot", images=["data:image/png;base64,..."])
    """
    logger.info(f"Resuming Codegen agent run: {agent_run_id}")
    
    # Use provided values or fall back to environment variables
    org = org_id or CODEGEN_ORG_ID
    token = api_token or CODEGEN_API_TOKEN
    
    if not org or not token:
        return {
            'success': False,
            'message': 'CODEGEN_ORG_ID and CODEGEN_API_TOKEN environment variables must be set'
        }
    
    try:
        # Prepare API request
        url = f"{CODEGEN_BASE_URL}/v1/organizations/{org}/agent/run/resume"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Build payload according to API spec
        payload = {
            "agent_run_id": agent_run_id,
            "prompt": prompt
        }
        
        # Add images if provided
        if images:
            payload["images"] = images
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                result = await response.json()
                
                if response.status == 200 or response.status == 201:
                    logger.info(f"Successfully resumed agent run: {agent_run_id}")
                    return {
                        'success': True,
                        'message': 'Agent run resumed successfully',
                        'agent_run_id': agent_run_id,
                        'status': result.get('status', 'processing'),
                        'result': result
                    }
                else:
                    error_msg = result.get('detail', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to reply to agent run: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }


@mcp.tool()
async def codegen_list_agent_runs(
    limit: int = 10,
    skip: int = 0,
    user_id: Optional[int] = None,
    source_type: Optional[str] = None,
    org_id: Optional[str] = None,
    api_token: Optional[str] = None
) -> dict:
    """
    List Codegen agent runs for an organization with optional filtering.
    
    Args:
        limit: Maximum number of runs to return (default: 10, range: 1-100)
        skip: Number of runs to skip for pagination (default: 0, must be >= 0)
        user_id: Filter by user ID who initiated the agent runs (optional)
        source_type: Filter by source type (optional, e.g., 'LOCAL', 'SLACK', 'GITHUB', 'API', 'LINEAR')
        org_id: Organization ID (optional, defaults to CODEGEN_ORG_ID env var)
        api_token: API token (optional, defaults to CODEGEN_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'runs': list[dict],
            'total': int,
            'page': int,
            'size': int,
            'pages': int
        }
    
    Examples:
        - codegen_list_agent_runs()
        - codegen_list_agent_runs(limit=20, skip=10)
        - codegen_list_agent_runs(user_id=123, source_type="SLACK")
    """
    logger.info(f"Listing Codegen agent runs (limit: {limit}, skip: {skip})")
    
    # Use provided values or fall back to environment variables
    org = org_id or CODEGEN_ORG_ID
    token = api_token or CODEGEN_API_TOKEN
    
    if not org or not token:
        return {
            'success': False,
            'message': 'CODEGEN_ORG_ID and CODEGEN_API_TOKEN environment variables must be set'
        }
    
    try:
        # Prepare API request - FIXED: Changed from /agents/runs to /agent/runs
        url = f"{CODEGEN_BASE_URL}/v1/organizations/{org}/agent/runs"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        params = {
            "limit": limit,
            "skip": skip
        }
        
        # Add optional filter parameters
        if user_id is not None:
            params["user_id"] = user_id
        if source_type:
            params["source_type"] = source_type
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                result = await response.json()
                
                if response.status == 200:
                    runs = result.get('items', [])
                    logger.info(f"Retrieved {len(runs)} agent runs")
                    return {
                        'success': True,
                        'message': f'Retrieved {len(runs)} agent runs',
                        'runs': runs,
                        'total': result.get('total', len(runs)),
                        'page': result.get('page', 0),
                        'size': result.get('size', len(runs)),
                        'pages': result.get('pages', 1)
                    }
                else:
                    error_msg = result.get('detail', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to list agent runs: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'runs': [],
            'total': 0
        }


@mcp.tool()
async def codegen_cancel_agent_run(
    agent_run_id: str,
    org_id: Optional[str] = None,
    api_token: Optional[str] = None
) -> dict:
    """
    Cancel a running Codegen agent run.
    
    Args:
        agent_run_id: ID of the agent run to cancel (required)
        org_id: Organization ID (optional, defaults to CODEGEN_ORG_ID env var)
        api_token: API token (optional, defaults to CODEGEN_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'agent_run_id': str,
            'status': str
        }
    
    Examples:
        - codegen_cancel_agent_run("123456")
    """
    logger.info(f"Cancelling Codegen agent run: {agent_run_id}")
    
    # Use provided values or fall back to environment variables
    org = org_id or CODEGEN_ORG_ID
    token = api_token or CODEGEN_API_TOKEN
    
    if not org or not token:
        return {
            'success': False,
            'message': 'CODEGEN_ORG_ID and CODEGEN_API_TOKEN environment variables must be set'
        }
    
    try:
        # Prepare API request
        url = f"{CODEGEN_BASE_URL}/v1/organizations/{org}/agent-run/{agent_run_id}/cancel"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                result = await response.json()
                
                if response.status == 200:
                    logger.info(f"Agent run cancelled successfully: {agent_run_id}")
                    return {
                        'success': True,
                        'message': 'Agent run cancelled successfully',
                        'agent_run_id': agent_run_id,
                        'status': result.get('status', 'cancelled')
                    }
                else:
                    error_msg = result.get('detail', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to cancel agent run: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }


# =============================================================================
# GITHUB API TOOLS
# =============================================================================

# GitHub API Configuration - read from environment variables
GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN", "")
GITHUB_API_BASE_URL = "https://api.github.com"


@mcp.tool()
async def github_create_repo(
    name: str,
    description: Optional[str] = None,
    private: bool = True,
    api_token: Optional[str] = None
) -> dict:
    """
    Create a new GitHub repository.
    
    Args:
        name: Repository name (required)
        description: Repository description (optional)
        private: Whether repo should be private (default: True)
        api_token: GitHub API token (optional, defaults to GITHUB_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'repo_name': str,
            'repo_url': str,
            'clone_url': str,
            'ssh_url': str
        }
    
    Examples:
        - github_create_repo("my-new-repo", "A cool project")
        - github_create_repo("test-repo", private=False)
    """
    logger.info(f"Creating GitHub repository: {name}")
    
    token = api_token or GITHUB_API_TOKEN
    if not token:
        return {
            'success': False,
            'message': 'GITHUB_API_TOKEN environment variable must be set'
        }
    
    try:
        url = f"{GITHUB_API_BASE_URL}/user/repos"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json"
        }
        payload = {
            "name": name,
            "private": private
        }
        if description:
            payload["description"] = description
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                result = await response.json()
                
                if response.status == 201:
                    logger.info(f"Repository created successfully: {result.get('full_name')}")
                    return {
                        'success': True,
                        'message': 'Repository created successfully',
                        'repo_name': result.get('full_name'),
                        'repo_url': result.get('html_url'),
                        'clone_url': result.get('clone_url'),
                        'ssh_url': result.get('ssh_url')
                    }
                else:
                    error_msg = result.get('message', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to create repository: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }



@mcp.tool()
async def github_fork_repo(
    owner: str,
    repo: str,
    organization: Optional[str] = None,
    name: Optional[str] = None,
    default_branch_only: bool = False,
    api_token: Optional[str] = None
) -> dict:
    """
    Fork a GitHub repository to your account or organization.
    
    Creates a private fork that maintains connection to the upstream repository.
    
    Args:
        owner: Repository owner username (e.g., "Ntrakiyski")
        repo: Repository name to fork (e.g., "chrome-mcp")
        organization: Optional organization name if forking into an organization
        name: Custom name for the fork (useful when forking within same org)
        default_branch_only: If true, fork only the default branch (default: False)
        api_token: GitHub API token (optional, defaults to GITHUB_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'fork': {
                'name': str,
                'full_name': str,
                'owner': str,
                'url': str,
                'clone_url': str,
                'ssh_url': str,
                'private': bool,
                'fork': bool,
                'parent_repo': str,
                'default_branch': str
            },
            'note': str
        }
    
    Examples:
        - github_fork_repo("Ntrakiyski", "chrome-mcp")
        - github_fork_repo("Ntrakiyski", "chrome-mcp", organization="my-org")
        - github_fork_repo("Ntrakiyski", "chrome-mcp", name="my-fork", default_branch_only=True)
    """
    logger.info(f"Forking GitHub repository: {owner}/{repo}")
    
    token = api_token or GITHUB_API_TOKEN
    if not token:
        return {
            'success': False,
            'message': 'GITHUB_API_TOKEN environment variable must be set'
        }
    
    try:
        url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/forks"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json"
        }
        
        # Build payload with optional parameters
        payload = {}
        if organization:
            payload["organization"] = organization
        if name:
            payload["name"] = name
        if default_branch_only:
            payload["default_branch_only"] = default_branch_only
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                result = await response.json()
                
                if response.status == 202:
                    logger.info(f"Repository forked successfully: {result.get('full_name')}")
                    return {
                        'success': True,
                        'message': 'Repository forked successfully',
                        'fork': {
                            'name': result.get('name'),
                            'full_name': result.get('full_name'),
                            'owner': result.get('owner', {}).get('login'),
                            'url': result.get('html_url'),
                            'clone_url': result.get('clone_url'),
                            'ssh_url': result.get('ssh_url'),
                            'private': result.get('private', True),
                            'fork': result.get('fork', True),
                            'parent_repo': f"{owner}/{repo}",
                            'default_branch': result.get('default_branch')
                        },
                        'note': 'Fork is being created asynchronously. It may take a few moments for git objects to be accessible.'
                    }
                else:
                    error_msg = result.get('message', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to fork repository: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }


@mcp.tool()
async def github_list_repos(
    per_page: int = 100,
    page: int = 1,
    api_token: Optional[str] = None
) -> dict:
    """
    List all GitHub repositories for the authenticated user.
    
    Args:
        per_page: Number of repos per page (default: 100, max: 100)
        page: Page number (default: 1)
        api_token: GitHub API token (optional, defaults to GITHUB_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'repos': list[dict],
            'total': int
        }
    
    Examples:
        - github_list_repos()
        - github_list_repos(per_page=50, page=2)
    """
    logger.info(f"Listing GitHub repositories (page: {page}, per_page: {per_page})")
    
    token = api_token or GITHUB_API_TOKEN
    if not token:
        return {
            'success': False,
            'message': 'GITHUB_API_TOKEN environment variable must be set'
        }
    
    try:
        url = f"{GITHUB_API_BASE_URL}/users/Ntrakiyski/repos"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        params = {
            "per_page": per_page,
            "page": page
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                result = await response.json()
                
                if response.status == 200:
                    repos = [{'name': r.get('name'), 'full_name': r.get('full_name'), 
                             'url': r.get('html_url'), 'private': r.get('private')} 
                            for r in result]
                    logger.info(f"Retrieved {len(repos)} repositories")
                    return {
                        'success': True,
                        'message': f'Retrieved {len(repos)} repositories',
                        'repos': repos,
                        'total': len(repos)
                    }
                else:
                    error_msg = result.get('message', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to list repositories: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'repos': [],
            'total': 0
        }


# @mcp.tool()
# async def github_search_repo(
#     query: str,
#     username: Optional[str] = None,
#     api_token: Optional[str] = None
# ) -> dict:
#     """
#     Search for a specific GitHub repository.
    
#     Args:
#         query: Search query (required)
#         username: Filter by username (optional) always use username Ntrakiyski
#         api_token: GitHub API token (optional, defaults to GITHUB_API_TOKEN env var)
    
#     Returns:
#         dict: {
#             'success': bool,
#             'message': str,
#             'repos': list[dict],
#             'total_count': int
#         }
    
#     Examples:
#         - github_search_repo("forest")
#         - github_search_repo("react", username="facebook")
#     """
#     logger.info(f"Searching GitHub repositories: {query}")
    
#     token = api_token or GITHUB_API_TOKEN
#     if not token:
#         return {
#             'success': False,
#             'message': 'GITHUB_API_TOKEN environment variable must be set'
#         }
    
#     try:
#         # Build search query
#         search_query = f"{query} in:name"
#         if username:
#             search_query += f" user:{username}"
        
#         url = f"{GITHUB_API_BASE_URL}/search/repositories"
#         headers = {
#             "Authorization": f"token {token}",
#             "Accept": "application/vnd.github+json",
#             "X-GitHub-Api-Version": "2022-11-28"
#         }
#         params = {"q": search_query}
        
#         async with aiohttp.ClientSession() as session:
#             async with session.get(url, headers=headers, params=params) as response:
#                 result = await response.json()
                
#                 if response.status == 200:
#                     repos = [{'name': r.get('name'), 'full_name': r.get('full_name'),
#                              'url': r.get('html_url'), 'description': r.get('description')}
#                             for r in result.get('items', [])]
#                     logger.info(f"Found {result.get('total_count', 0)} repositories")
#                     return {
#                         'success': True,
#                         'message': f"Found {result.get('total_count', 0)} repositories",
#                         'repos': repos,
#                         'total_count': result.get('total_count', 0)
#                     }
#                 else:
#                     error_msg = result.get('message', f'API request failed with status {response.status}')
#                     raise Exception(error_msg)
                    
#     except Exception as e:
#         error_msg = f"Failed to search repositories: {str(e)}"
#         logger.error(error_msg)
#         return {
#             'success': False,
#             'message': error_msg,
#             'repos': [],
#             'total_count': 0
#         }

# =============================================================================
# GITHUB PULL REQUEST TOOLS
# =============================================================================

@mcp.tool()
async def github_list_pull_requests(
    owner: str,
    repo: str,
    state: str = "open",
    per_page: int = 30,
    page: int = 1,
    api_token: Optional[str] = None
) -> dict:
    """
    List pull requests in a GitHub repository.
    
    Args:
        owner: Repository owner username (e.g., "Ntrakiyski")
        repo: Repository name (e.g., "chrome-mcp")
        state: PR state filter - "open", "closed", or "all" (default: "open")
        per_page: Number of PRs per page (default: 30, max: 100)
        page: Page number (default: 1)
        api_token: GitHub API token (optional, defaults to GITHUB_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'pull_requests': list[dict],
            'count': int
        }
    
    Examples:
        - github_list_pull_requests("Ntrakiyski", "chrome-mcp")
        - github_list_pull_requests("Ntrakiyski", "chrome-mcp", state="all")
    """
    logger.info(f"Listing pull requests for {owner}/{repo} (state: {state})")
    
    token = api_token or GITHUB_API_TOKEN
    if not token:
        return {
            'success': False,
            'message': 'GITHUB_API_TOKEN environment variable must be set'
        }
    
    try:
        url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/pulls"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        params = {
            "state": state,
            "per_page": per_page,
            "page": page
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    prs = [{
                        'number': pr.get('number'),
                        'title': pr.get('title'),
                        'state': pr.get('state'),
                        'user': pr.get('user', {}).get('login'),
                        'created_at': pr.get('created_at'),
                        'updated_at': pr.get('updated_at'),
                        'html_url': pr.get('html_url'),
                        'head': pr.get('head', {}).get('ref'),
                        'base': pr.get('base', {}).get('ref'),
                        'mergeable': pr.get('mergeable'),
                        'draft': pr.get('draft')
                    } for pr in result]
                    
                    logger.info(f"Retrieved {len(prs)} pull requests")
                    return {
                        'success': True,
                        'message': f'Retrieved {len(prs)} pull requests',
                        'pull_requests': prs,
                        'count': len(prs)
                    }
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('message', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to list pull requests: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'pull_requests': [],
            'count': 0
        }


@mcp.tool()
async def github_get_pull_request(
    owner: str,
    repo: str,
    pull_number: int,
    api_token: Optional[str] = None
) -> dict:
    """
    Get detailed information about a specific pull request.
    
    Args:
        owner: Repository owner username (e.g., "Ntrakiyski")
        repo: Repository name (e.g., "chrome-mcp")
        pull_number: Pull request number (e.g., 42)
        api_token: GitHub API token (optional, defaults to GITHUB_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'pull_request': dict with full PR details
        }
    
    Examples:
        - github_get_pull_request("Ntrakiyski", "chrome-mcp", 1)
    """
    logger.info(f"Getting PR #{pull_number} for {owner}/{repo}")
    
    token = api_token or GITHUB_API_TOKEN
    if not token:
        return {
            'success': False,
            'message': 'GITHUB_API_TOKEN environment variable must be set'
        }
    
    try:
        url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/pulls/{pull_number}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    pr = await response.json()
                    logger.info(f"Retrieved PR #{pull_number}: {pr.get('title')}")
                    
                    return {
                        'success': True,
                        'message': f"Retrieved PR #{pull_number}",
                        'pull_request': {
                            'number': pr.get('number'),
                            'title': pr.get('title'),
                            'body': pr.get('body'),
                            'state': pr.get('state'),
                            'user': pr.get('user', {}).get('login'),
                            'created_at': pr.get('created_at'),
                            'updated_at': pr.get('updated_at'),
                            'closed_at': pr.get('closed_at'),
                            'merged_at': pr.get('merged_at'),
                            'html_url': pr.get('html_url'),
                            'head': pr.get('head', {}).get('ref'),
                            'base': pr.get('base', {}).get('ref'),
                            'mergeable': pr.get('mergeable'),
                            'mergeable_state': pr.get('mergeable_state'),
                            'merged': pr.get('merged'),
                            'draft': pr.get('draft'),
                            'commits': pr.get('commits'),
                            'additions': pr.get('additions'),
                            'deletions': pr.get('deletions'),
                            'changed_files': pr.get('changed_files')
                        }
                    }
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('message', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to get pull request: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }


@mcp.tool()
async def github_merge_pull_request(
    owner: str,
    repo: str,
    pull_number: int,
    commit_title: Optional[str] = None,
    commit_message: Optional[str] = None,
    merge_method: str = "merge",
    api_token: Optional[str] = None
) -> dict:
    """
    Merge a pull request.
    
    Args:
        owner: Repository owner username (e.g., "Ntrakiyski")
        repo: Repository name (e.g., "chrome-mcp")
        pull_number: Pull request number to merge
        commit_title: Title for the merge commit (optional, auto-generated if not provided)
        commit_message: Extra detail for merge commit message (optional)
        merge_method: Merge method - "merge", "squash", or "rebase" (default: "merge")
        api_token: GitHub API token (optional, defaults to GITHUB_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'sha': str (commit SHA if successful),
            'merged': bool
        }
    
    Examples:
        - github_merge_pull_request("Ntrakiyski", "chrome-mcp", 1)
        - github_merge_pull_request("Ntrakiyski", "chrome-mcp", 1, merge_method="squash")
    """
    logger.info(f"Merging PR #{pull_number} for {owner}/{repo} (method: {merge_method})")
    
    token = api_token or GITHUB_API_TOKEN
    if not token:
        return {
            'success': False,
            'message': 'GITHUB_API_TOKEN environment variable must be set'
        }
    
    # Validate merge method
    if merge_method not in ["merge", "squash", "rebase"]:
        return {
            'success': False,
            'message': f'Invalid merge_method: {merge_method}. Must be "merge", "squash", or "rebase"'
        }
    
    try:
        url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/pulls/{pull_number}/merge"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        payload = {
            "merge_method": merge_method
        }
        if commit_title:
            payload["commit_title"] = commit_title
        if commit_message:
            payload["commit_message"] = commit_message
        
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, json=payload) as response:
                result = await response.json()
                
                if response.status == 200:
                    logger.info(f"PR #{pull_number} merged successfully")
                    return {
                        'success': True,
                        'message': result.get('message', 'Pull request merged successfully'),
                        'sha': result.get('sha'),
                        'merged': result.get('merged', True)
                    }
                elif response.status == 405:
                    return {
                        'success': False,
                        'message': 'Pull request cannot be merged (method not allowed). Check if PR is mergeable and branch protection rules.'
                    }
                elif response.status == 409:
                    return {
                        'success': False,
                        'message': 'Merge conflict detected. Pull request head branch must be updated.'
                    }
                else:
                    error_msg = result.get('message', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to merge pull request: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'merged': False
        }


@mcp.tool()
async def github_list_pull_request_files(
    owner: str,
    repo: str,
    pull_number: int,
    per_page: int = 30,
    page: int = 1,
    api_token: Optional[str] = None
) -> dict:
    """
    List files changed in a pull request.
    
    Args:
        owner: Repository owner username (e.g., "Ntrakiyski")
        repo: Repository name (e.g., "chrome-mcp")
        pull_number: Pull request number
        per_page: Number of files per page (default: 30, max: 100)
        page: Page number (default: 1)
        api_token: GitHub API token (optional, defaults to GITHUB_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'files': list[dict],
            'count': int
        }
    
    Examples:
        - github_list_pull_request_files("Ntrakiyski", "chrome-mcp", 1)
    """
    logger.info(f"Listing files for PR #{pull_number} in {owner}/{repo}")
    
    token = api_token or GITHUB_API_TOKEN
    if not token:
        return {
            'success': False,
            'message': 'GITHUB_API_TOKEN environment variable must be set'
        }
    
    try:
        url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/pulls/{pull_number}/files"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        params = {
            "per_page": per_page,
            "page": page
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    files = [{
                        'filename': f.get('filename'),
                        'status': f.get('status'),
                        'additions': f.get('additions'),
                        'deletions': f.get('deletions'),
                        'changes': f.get('changes'),
                        'blob_url': f.get('blob_url'),
                        'raw_url': f.get('raw_url'),
                        'patch': f.get('patch', '')[:500]  # Truncate patch to 500 chars
                    } for f in result]
                    
                    logger.info(f"Retrieved {len(files)} files for PR #{pull_number}")
                    return {
                        'success': True,
                        'message': f'Retrieved {len(files)} files',
                        'files': files,
                        'count': len(files)
                    }
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('message', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to list PR files: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'files': [],
            'count': 0
        }


@mcp.tool()
async def github_check_pull_request_merged(
    owner: str,
    repo: str,
    pull_number: int,
    api_token: Optional[str] = None
) -> dict:
    """
    Check if a pull request has been merged.
    
    Args:
        owner: Repository owner username (e.g., "Ntrakiyski")
        repo: Repository name (e.g., "chrome-mcp")
        pull_number: Pull request number
        api_token: GitHub API token (optional, defaults to GITHUB_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'merged': bool
        }
    
    Examples:
        - github_check_pull_request_merged("Ntrakiyski", "chrome-mcp", 1)
    """
    logger.info(f"Checking if PR #{pull_number} is merged in {owner}/{repo}")
    
    token = api_token or GITHUB_API_TOKEN
    if not token:
        return {
            'success': False,
            'message': 'GITHUB_API_TOKEN environment variable must be set'
        }
    
    try:
        url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/pulls/{pull_number}/merge"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 204:
                    logger.info(f"PR #{pull_number} is merged")
                    return {
                        'success': True,
                        'message': f'PR #{pull_number} has been merged',
                        'merged': True
                    }
                elif response.status == 404:
                    logger.info(f"PR #{pull_number} is NOT merged")
                    return {
                        'success': True,
                        'message': f'PR #{pull_number} has NOT been merged',
                        'merged': False
                    }
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('message', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to check merge status: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'merged': False
        }


@mcp.tool()
async def github_update_pull_request(
    owner: str,
    repo: str,
    pull_number: int,
    title: Optional[str] = None,
    body: Optional[str] = None,
    state: Optional[str] = None,
    base: Optional[str] = None,
    api_token: Optional[str] = None
) -> dict:
    """
    Update a pull request (title, body, state, or base branch).
    
    Args:
        owner: Repository owner username (e.g., "Ntrakiyski")
        repo: Repository name (e.g., "chrome-mcp")
        pull_number: Pull request number to update
        title: New PR title (optional)
        body: New PR body/description (optional)
        state: New PR state - "open" or "closed" (optional)
        base: New base branch name (optional)
        api_token: GitHub API token (optional, defaults to GITHUB_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'pull_request': dict with updated PR details
        }
    
    Examples:
        - github_update_pull_request("Ntrakiyski", "chrome-mcp", 1, title="New Title")
        - github_update_pull_request("Ntrakiyski", "chrome-mcp", 1, state="closed")
    """
    logger.info(f"Updating PR #{pull_number} for {owner}/{repo}")
    
    token = api_token or GITHUB_API_TOKEN
    if not token:
        return {
            'success': False,
            'message': 'GITHUB_API_TOKEN environment variable must be set'
        }
    
    # Build payload with only provided fields
    payload = {}
    if title is not None:
        payload["title"] = title
    if body is not None:
        payload["body"] = body
    if state is not None:
        if state not in ["open", "closed"]:
            return {
                'success': False,
                'message': f'Invalid state: {state}. Must be "open" or "closed"'
            }
        payload["state"] = state
    if base is not None:
        payload["base"] = base
    
    if not payload:
        return {
            'success': False,
            'message': 'No update parameters provided (title, body, state, or base)'
        }
    
    try:
        url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/pulls/{pull_number}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    pr = await response.json()
                    logger.info(f"PR #{pull_number} updated successfully")
                    return {
                        'success': True,
                        'message': f"PR #{pull_number} updated successfully",
                        'pull_request': {
                            'number': pr.get('number'),
                            'title': pr.get('title'),
                            'state': pr.get('state'),
                            'html_url': pr.get('html_url')
                        }
                    }
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('message', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to update pull request: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }

@mcp.tool()
async def github_set_pr_ready_for_review(
    owner: str,
    repo: str,
    pull_number: int,
    api_token: Optional[str] = None
) -> dict:
    """
    Mark a draft pull request as ready for review.
    
    Converts a draft PR to a regular PR that can be reviewed and merged.
    
    Args:
        owner: Repository owner username (e.g., "Ntrakiyski")
        repo: Repository name (e.g., "chrome-mcp")
        pull_number: Pull request number to mark as ready
        api_token: GitHub API token (optional, defaults to GITHUB_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'pull_request': {
                'number': int,
                'title': str,
                'state': str,
                'draft': bool,
                'html_url': str
            }
        }
    
    Examples:
        - github_set_pr_ready_for_review("Ntrakiyski", "chrome-mcp", 4)
        - github_set_pr_ready_for_review("owner", "repo", 15)
    """
    logger.info(f"Marking PR #{pull_number} as ready for review in {owner}/{repo}")
    
    token = api_token or GITHUB_API_TOKEN
    if not token:
        return {
            'success': False,
            'message': 'GITHUB_API_TOKEN environment variable must be set'
        }
    
    try:
        url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/pulls/{pull_number}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json"
        }
        
        payload = {"draft": False}
        
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    pr = await response.json()
                    logger.info(f"PR #{pull_number} marked as ready for review")
                    return {
                        'success': True,
                        'message': f"Pull request #{pull_number} marked as ready for review.",
                        'pull_request': {
                            'number': pr.get('number'),
                            'title': pr.get('title'),
                            'state': pr.get('state'),
                            'draft': pr.get('draft', False),
                            'html_url': pr.get('html_url')
                        }
                    }
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('message', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to update pull request: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }


# =============================================================================
# GITHUB FILE MANAGEMENT TOOLS
# =============================================================================


@mcp.tool()
async def github_get_repo_tree(
    owner: str,
    repo: str,
    branch: str = "main",
    recursive: bool = True,
    api_token: Optional[str] = None
) -> dict:
    """
    Get the complete file/folder structure of a GitHub repository.

    This tool retrieves the entire repository tree structure in one API call,
    providing complete context of the repository without needing to fetch each file individually.

    Args:
        owner: GitHub username or organization name (required)
        repo: Repository name (required)
        branch: Branch name to get tree from (default: "main")
        recursive: Whether to get the full recursive tree (default: True)
        api_token: GitHub API token (optional, defaults to GITHUB_API_TOKEN env var)

    Returns:
        dict with success status, repository info, tree structure, and statistics
    """
    logger.info(f"Getting repository tree for {owner}/{repo} on branch {branch}")

    token = api_token or GITHUB_API_TOKEN
    if not token:
        return {
            'success': False,
            'message': 'GITHUB_API_TOKEN environment variable must be set'
        }

    try:
        # Step 1: Get the branch to find the tree SHA
        branch_url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/branches/{branch}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(branch_url, headers=headers) as response:
                if response.status != 200:
                    error_data = await response.json()
                    error_msg = error_data.get('message', f'Failed to get branch info (status {response.status})')
                    raise Exception(error_msg)

                branch_data = await response.json()
                tree_sha = branch_data["commit"]["commit"]["tree"]["sha"]

            # Step 2: Get the tree (recursive if requested)
            tree_url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/git/trees/{tree_sha}"
            if recursive:
                tree_url += "?recursive=1"

            async with session.get(tree_url, headers=headers) as response:
                if response.status != 200:
                    error_data = await response.json()
                    error_msg = error_data.get('message', f'Failed to get tree (status {response.status})')
                    raise Exception(error_msg)

                tree_data = await response.json()

        # Process the tree data
        files = [item for item in tree_data["tree"] if item["type"] == "blob"]
        dirs = [item for item in tree_data["tree"] if item["type"] == "tree"]
        total_size = sum(item.get("size", 0) for item in files)

        logger.info(f"Retrieved tree with {len(files)} files and {len(dirs)} directories")

        return {
            'success': True,
            'message': f'Retrieved repository tree with {len(files)} files',
            'repository': {
                'owner': owner,
                'repo': repo,
                'branch': branch,
                'sha': tree_sha
            },
            'tree': tree_data["tree"],
            'file_count': len(files),
            'directory_count': len(dirs),
            'total_size_bytes': total_size,
            'truncated': tree_data.get("truncated", False)
        }

    except Exception as e:
        error_msg = f"Failed to get repository tree: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }



# =============================================================================
\
@mcp.tool()
async def github_get_file_content(
    owner: str,
    repo: str,
    path: str,
    branch: str = "main",
    api_token: Optional[str] = None
) -> dict:
    """
    Get the content of a file from a GitHub repository.

    Retrieves file content, metadata, and SHA (needed for updates/deletes).
    Content is returned as decoded text.

    Args:
        owner: GitHub username or organization name (required)
        repo: Repository name (required)
        path: File path within the repository (required)
        branch: Branch name (default: "main")
        api_token: GitHub API token (optional, defaults to GITHUB_API_TOKEN env var)

    Returns:
        dict with file information including content and SHA
    """
    logger.info(f"Getting file content for {owner}/{repo}/{path} on branch {branch}")

    token = api_token or GITHUB_API_TOKEN
    if not token:
        return {
            'success': False,
            'message': 'GITHUB_API_TOKEN environment variable must be set'
        }

    try:
        url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/contents/{path}?ref={branch}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    error_data = await response.json()
                    error_msg = error_data.get('message', f'Failed to get file (status {response.status})')
                    raise Exception(error_msg)

                file_data = await response.json()

        # Decode base64 content
        content_b64 = file_data.get("content", "")
        if content_b64:
            try:
                content = base64.b64decode(content_b64).decode("utf-8")
            except UnicodeDecodeError:
                # If it's not UTF-8 text, return base64 and note it
                content = f"[BINARY FILE - {len(content_b64)} bytes base64 encoded]"
        else:
            content = ""

        logger.info(f"Retrieved file {path} ({len(content)} characters)")

        return {
            'success': True,
            'message': f'Successfully retrieved file {path}',
            'file': {
                'name': file_data.get('name') ,
                'path': file_data.get('path') ,
                'sha': file_data.get('sha') ,  # IMPORTANT: Save this!
                'size': file_data.get('size', 0),
                'encoding': file_data.get('encoding', 'base64') ,
                'content': content
            }
        }

    except Exception as e:
        error_msg = f"Failed to get file content: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }


\
@mcp.tool()
async def github_update_file(
    owner: str,
    repo: str,
    path: str,
    content: str,
    message: str,
    sha: str,
    branch: str = "main",
    api_token: Optional[str] = None
) -> dict:
    """
    Update an existing file in a GitHub repository.

    IMPORTANT: You MUST provide the current file SHA (obtained from github_get_file_content).
    If the SHA doesn't match the current file, the update will fail with a 409 Conflict error.

    Args:
        owner: GitHub username or organization name (required)
        repo: Repository name (required)
        path: File path within the repository (required)
        content: New file content as string (required)
        message: Commit message (required)
        sha: Current file SHA (required - get from github_get_file_content)
        branch: Branch name (default: "main")
        api_token: GitHub API token (optional, defaults to GITHUB_API_TOKEN env var)

    Returns:
        dict with commit and file information
    """
    logger.info(f"Updating file {owner}/{repo}/{path} on branch {branch}")

    token = api_token or GITHUB_API_TOKEN
    if not token:
        return {
            'success': False,
            'message': 'GITHUB_API_TOKEN environment variable must be set'
        }

    try:
        # Encode content to base64
        content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/contents/{path}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json"
        }
        payload = {
            "message": message,
            "content": content_b64,
            "sha": sha,  # IMPORTANT: Current file SHA
            "branch": branch
        }

        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, json=payload) as response:
                if response.status == 200 or response.status == 201:
                    result = await response.json()
                    logger.info(f"File {path} updated successfully")
                    return {
                        'success': True,
                        'message': f'File {path} updated successfully',
                        'commit': result.get('commit') ,
                        'file': {
                            'name': result['content'].get('name') ,
                            'path': result['content'].get('path') ,
                            'sha': result['content'].get('sha') ,  # New SHA
                            'size': result['content'].get('size', 0)
                        }
                    }
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('message', f'API request failed with status {response.status}')
                    raise Exception(error_msg)

    except Exception as e:
        error_msg = f"Failed to update file: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }


\
@mcp.tool()
async def github_create_file(
    owner: str,
    repo: str,
    path: str,
    content: str,
    message: str,
    branch: str = "main",
    api_token: Optional[str] = None
) -> dict:
    """
    Create a new file in a GitHub repository.

    Note: If a file already exists at the given path, this will fail.
    Use github_update_file to modify existing files.

    Args:
        owner: GitHub username or organization name (required)
        repo: Repository name (required)
        path: File path within the repository (required)
        content: File content as string (required)
        message: Commit message (required)
        branch: Branch name (default: "main")
        api_token: GitHub API token (optional, defaults to GITHUB_API_TOKEN env var)

    Returns:
        dict with commit and file information
    """
    logger.info(f"Creating file {owner}/{repo}/{path} on branch {branch}")

    token = api_token or GITHUB_API_TOKEN
    if not token:
        return {
            'success': False,
            'message': 'GITHUB_API_TOKEN environment variable must be set'
        }

    try:
        # Encode content to base64
        content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/contents/{path}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json"
        }
        payload = {
            "message": message,
            "content": content_b64,
            "branch": branch
            # NOTE: No 'sha' field for new files
        }

        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, json=payload) as response:
                if response.status == 201:
                    result = await response.json()
                    logger.info(f"File {path} created successfully")
                    return {
                        'success': True,
                        'message': f'File {path} created successfully',
                        'commit': result.get('commit') ,
                        'file': {
                            'name': result['content'].get('name') ,
                            'path': result['content'].get('path') ,
                            'sha': result['content'].get('sha') ,
                            'size': result['content'].get('size', 0)
                        }
                    }
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('message', f'API request failed with status {response.status}')
                    raise Exception(error_msg)

    except Exception as e:
        error_msg = f"Failed to create file: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }


# COOLIFY API TOOLS
# =============================================================================

# Coolify API Configuration - read from environment variables
COOLIFY_API_TOKEN = os.getenv("COOLIFY_API_TOKEN", "")
COOLIFY_API_BASE_URL = os.getenv("COOLIFY_API_BASE_URL", "https://worfklow.org/api/v1")
COOLIFY_PROJECT_UUID = "j0ck0c4kckgw0gosksosogog"  # Hardcoded as requested
COOLIFY_SERVER_UUID = "qk48swgog4kok0og8848wwg8"  # Hardcoded as requested


@mcp.tool()
async def coolify_list_applications(
    api_token: Optional[str] = None
) -> dict:
    """
    List all Coolify applications.
    
    Args:
        api_token: Coolify API token (optional, defaults to COOLIFY_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'applications': list[dict],
            'total': int
        }
    
    Examples:
        - coolify_list_applications()
    """
    logger.info("Listing Coolify applications")
    
    token = api_token or COOLIFY_API_TOKEN
    if not token:
        return {
            'success': False,
            'message': 'COOLIFY_API_TOKEN environment variable must be set'
        }
    
    try:
        url = f"{COOLIFY_API_BASE_URL}/applications"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                result = await response.json()
                
                if response.status == 200:
                    apps = result if isinstance(result, list) else result.get('applications', [])
                    logger.info(f"Retrieved {len(apps)} applications")
                    return {
                        'success': True,
                        'message': f'Retrieved {len(apps)} applications',
                        'applications': apps,
                        'total': len(apps)
                    }
                else:
                    error_msg = result.get('message', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to list applications: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'applications': [],
            'total': 0
        }


@mcp.tool()
async def coolify_list_servers(
    api_token: Optional[str] = None
) -> dict:
    """
    List all Coolify servers.
    
    Args:
        api_token: Coolify API token (optional, defaults to COOLIFY_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'servers': list[dict],
            'total': int
        }
    
    Examples:
        - coolify_list_servers()
    """
    logger.info("Listing Coolify servers")
    
    token = api_token or COOLIFY_API_TOKEN
    if not token:
        return {
            'success': False,
            'message': 'COOLIFY_API_TOKEN environment variable must be set'
        }
    
    try:
        url = f"{COOLIFY_API_BASE_URL}/servers"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                result = await response.json()
                
                if response.status == 200:
                    servers = result if isinstance(result, list) else result.get('servers', [])
                    logger.info(f"Retrieved {len(servers)} servers")
                    return {
                        'success': True,
                        'message': f'Retrieved {len(servers)} servers',
                        'servers': servers,
                        'total': len(servers)
                    }
                else:
                    error_msg = result.get('message', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to list servers: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'servers': [],
            'total': 0
        }


@mcp.tool()
async def coolify_get_server_details(
    server_uuid: Optional[str] = None,
    api_token: Optional[str] = None
) -> dict:
    """
    Get details of a specific Coolify server.
    
    Args:
        server_uuid: Server UUID (optional, defaults to hardcoded COOLIFY_SERVER_UUID)
        api_token: Coolify API token (optional, defaults to COOLIFY_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'server': dict
        }
    
    Examples:
        - coolify_get_server_details()
        - coolify_get_server_details(server_uuid="custom-uuid")
    """
    server_id = server_uuid or COOLIFY_SERVER_UUID
    logger.info(f"Getting Coolify server details: {server_id}")
    
    token = api_token or COOLIFY_API_TOKEN
    if not token:
        return {
            'success': False,
            'message': 'COOLIFY_API_TOKEN environment variable must be set'
        }
    
    try:
        url = f"{COOLIFY_API_BASE_URL}/servers/{server_id}"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                result = await response.json()
                
                if response.status == 200:
                    logger.info(f"Server details retrieved: {server_id}")
                    return {
                        'success': True,
                        'message': 'Server details retrieved successfully',
                        'server': result
                    }
                else:
                    error_msg = result.get('message', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to get server details: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }


@mcp.tool()
async def coolify_create_application(
    git_repository: str,
    name: str,
    git_branch: str = "main",
    build_pack: str = "dockercompose",
    docker_compose_location: str = "docker-compose.yml",
    instant_deploy: bool = True,
    environment_name: str = "production",
    project_uuid: Optional[str] = None,
    server_uuid: Optional[str] = None,
    api_token: Optional[str] = None
) -> dict:
    """
    Create a new public application in Coolify.
    
    Args:
        git_repository: Git repository URL (required, e.g., "https://github.com/user/repo.git")
        name: Application name (required)
        git_branch: Git branch to deploy (default: "main")
        build_pack: Build pack type (default: "dockercompose")
        docker_compose_location: Path to docker-compose file (default: "docker-compose.yml")
        instant_deploy: Whether to deploy immediately (default: True)
        environment_name: Environment name (default: "production")
        project_uuid: Project UUID (optional, defaults to hardcoded value)
        server_uuid: Server UUID (optional, defaults to hardcoded value)
        api_token: Coolify API token (optional, defaults to COOLIFY_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'application_uuid': str,
            'application': dict
        }
    
    Examples:
        - coolify_create_application("https://github.com/user/repo.git", "my-app")
        - coolify_create_application("https://github.com/user/repo.git", "test-app", git_branch="develop")
    """
    logger.info(f"Creating Coolify application: {name}")
    
    token = api_token or COOLIFY_API_TOKEN
    project_id = project_uuid or COOLIFY_PROJECT_UUID
    server_id = server_uuid or COOLIFY_SERVER_UUID
    
    if not token:
        return {
            'success': False,
            'message': 'COOLIFY_API_TOKEN environment variable must be set'
        }
    
    try:
        url = f"{COOLIFY_API_BASE_URL}/applications/public"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "project_uuid": project_id,
            "server_uuid": server_id,
            "environment_name": environment_name,
            "git_repository": git_repository,
            "git_branch": git_branch,
            "name": name,
            "build_pack": build_pack,
            "docker_compose_location": docker_compose_location,
            "instant_deploy": instant_deploy
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                result = await response.json()
                
                if response.status == 200 or response.status == 201:
                    logger.info(f"Application created successfully: {name}")
                    return {
                        'success': True,
                        'message': 'Application created successfully',
                        'application_uuid': result.get('uuid', result.get('id')),
                        'application': result
                    }
                else:
                    error_msg = result.get('message', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to create application: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }


@mcp.tool()
async def coolify_create_private_github_app_application(
    github_app_uuid: str,
    git_repository: str,
    name: str,
    git_branch: str = "main",
    build_pack: str = "dockercompose",
    docker_compose_location: str = "docker-compose.yml",
    instant_deploy: bool = True,
    environment_name: str = "production",
    project_uuid: Optional[str] = None,
    server_uuid: Optional[str] = None,
    domains: Optional[str] = None,
    api_token: Optional[str] = None
) -> dict:
    """
    Create and deploy a new application in Coolify from a private GitHub repository using GitHub App integration.
    Specifically designed for docker-compose deployments with compose files in the root directory.

    Args:
        github_app_uuid: UUID of the GitHub App configured in Coolify Sources (required)
        git_repository: Repository identifier (required, e.g., "Ntrakiyski/chrome-mcp")
        name: Application name in Coolify (required)
        git_branch: Git branch to deploy (default: "main")
        build_pack: Build pack type (default: "dockercompose")
        docker_compose_location: Path to docker-compose file (default: "docker-compose.yml")
        instant_deploy: Whether to deploy immediately after creation (default: True)
        environment_name: Environment name (default: "production")
        project_uuid: Coolify project UUID (optional, defaults to hardcoded value)
        server_uuid: Coolify server UUID (optional, defaults to hardcoded value)
        domains: Comma-separated domains (optional, e.g., "app.example.com,www.app.example.com")
        api_token: Coolify API token (optional, defaults to COOLIFY_API_TOKEN env var)

    Returns:
        dict: {
            'success': bool,
            'message': str,
            'application_uuid': str,
            'application': dict
        }

    Examples:
        - coolify_create_private_github_app_application("github-app-uuid", "Ntrakiyski/chrome-mcp", "my-private-app")
        - coolify_create_private_github_app_application("github-app-uuid", "Ntrakiyski/chrome-mcp", "test-app", git_branch="develop", domains="test.example.com")
    """
    logger.info(f"Creating Coolify private GitHub App application: {name} from {git_repository}")

    token = api_token or COOLIFY_API_TOKEN
    project_id = project_uuid or COOLIFY_PROJECT_UUID
    server_id = server_uuid or COOLIFY_SERVER_UUID

    if not token:
        return {
            'success': False,
            'message': 'COOLIFY_API_TOKEN environment variable must be set'
        }

    try:
        url = f"{COOLIFY_API_BASE_URL}/applications/private-github-app"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "project_uuid": project_id,
            "server_uuid": server_id,
            "environment_name": environment_name,
            "github_app_uuid": github_app_uuid,
            "git_repository": git_repository,
            "git_branch": git_branch,
            "name": name,
            "build_pack": build_pack,
            "docker_compose_location": docker_compose_location,
            "instant_deploy": instant_deploy
        }

        # Add domains if provided
        if domains:
            payload["domains"] = domains

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                result = await response.json()

                if response.status == 200 or response.status == 201:
                    app_uuid = result.get('uuid', result.get('id'))
                    logger.info(f"Private application created successfully: {name} (UUID: {app_uuid})")
                    return {
                        'success': True,
                        'message': 'Private application created successfully',
                        'application_uuid': app_uuid,
                        'application': {
                            'uuid': app_uuid,
                            'name': name,
                            'git_repository': git_repository,
                            'git_branch': git_branch,
                            'build_pack': build_pack,
                            'status': result.get('status', 'created'),
                            'domains': domains,
                            'fqdn': result.get('fqdn', ''),
                            'environment_name': environment_name
                        }
                    }
                else:
                    error_msg = result.get('message', f'API request failed with status {response.status}')
                    raise Exception(error_msg)

    except Exception as e:
        error_msg = f"Failed to create private application: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }


@mcp.tool()
async def coolify_restart_application(
    app_uuid: str,
    api_token: Optional[str] = None
) -> dict:
    """
    Restart a Coolify application.
    
    Args:
        app_uuid: Application UUID (required)
        api_token: Coolify API token (optional, defaults to COOLIFY_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str
        }
    
    Examples:
        - coolify_restart_application("app-uuid-here")
    """
    logger.info(f"Restarting Coolify application: {app_uuid}")
    
    token = api_token or COOLIFY_API_TOKEN
    if not token:
        return {
            'success': False,
            'message': 'COOLIFY_API_TOKEN environment variable must be set'
        }
    
    try:
        url = f"{COOLIFY_API_BASE_URL}/applications/{app_uuid}/restart"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                result = await response.json() if response.content_length else {}
                
                if response.status == 200 or response.status == 204:
                    logger.info(f"Application restarted successfully: {app_uuid}")
                    return {
                        'success': True,
                        'message': 'Application restarted successfully'
                    }
                else:
                    error_msg = result.get('message', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to restart application: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }


@mcp.tool()
async def coolify_stop_application(
    app_uuid: str,
    api_token: Optional[str] = None
) -> dict:
    """
    Stop a Coolify application.
    
    Args:
        app_uuid: Application UUID (required)
        api_token: Coolify API token (optional, defaults to COOLIFY_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str
        }
    
    Examples:
        - coolify_stop_application("app-uuid-here")
    """
    logger.info(f"Stopping Coolify application: {app_uuid}")
    
    token = api_token or COOLIFY_API_TOKEN
    if not token:
        return {
            'success': False,
            'message': 'COOLIFY_API_TOKEN environment variable must be set'
        }
    
    try:
        url = f"{COOLIFY_API_BASE_URL}/applications/{app_uuid}/stop"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                result = await response.json() if response.content_length else {}
                
                if response.status == 200 or response.status == 204:
                    logger.info(f"Application stopped successfully: {app_uuid}")
                    return {
                        'success': True,
                        'message': 'Application stopped successfully'
                    }
                else:
                    error_msg = result.get('message', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to stop application: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }


@mcp.tool()
async def get_coolify_domain_and_envs(
    app_uuid: str,
    api_token: Optional[str] = None
) -> dict:
    """
    Get domain and all environment variables for a Coolify application.
    
    This tool retrieves both the application's domain/FQDN and all environment 
    variables in a single call, making it convenient to get complete deployment 
    configuration information.
    
    Args:
        app_uuid: Application UUID (required)
        api_token: Coolify API token (optional, defaults to COOLIFY_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'application_uuid': str,
            'domain': str,
            'fqdn': str,
            'environment_variables': list[dict] with fields:
                - id: int
                - uuid: str
                - key: str
                - value: str (masked sensitive values)
                - real_value: str (actual value)
                - is_literal: bool
                - is_multiline: bool
                - is_preview: bool
                - is_runtime: bool
                - is_buildtime: bool
                - is_shared: bool
                - is_shown_once: bool
                - version: str
                - created_at: str
                - updated_at: str
        }
    
    Examples:
        - get_coolify_domain_and_envs("app-uuid-here")
        - get_coolify_domain_and_envs("app-uuid-here", api_token="custom-token")
    """
    logger.info(f"Getting domain and environment variables for Coolify application: {app_uuid}")
    
    token = api_token or COOLIFY_API_TOKEN
    if not token:
        return {
            'success': False,
            'message': 'COOLIFY_API_TOKEN environment variable must be set'
        }
    
    try:
        # Get environment variables
        envs_url = f"{COOLIFY_API_BASE_URL}/applications/{app_uuid}/envs"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        async with aiohttp.ClientSession() as session:
            # Get environment variables
            async with session.get(envs_url, headers=headers) as envs_response:
                if envs_response.status != 200:
                    error_msg = f'Failed to get environment variables (status {envs_response.status})'
                    raise Exception(error_msg)
                
                envs_result = await envs_response.json()
                logger.info(f"Retrieved {len(envs_result)} environment variables")
            
            # Get application details for domain/FQDN
            app_url = f"{COOLIFY_API_BASE_URL}/applications/{app_uuid}"
            async with session.get(app_url, headers=headers) as app_response:
                if app_response.status != 200:
                    error_msg = f'Failed to get application details (status {app_response.status})'
                    raise Exception(error_msg)
                
                app_result = await app_response.json()
                domain = app_result.get('fqdn', app_result.get('domain', ''))
                logger.info(f"Application domain: {domain}")
        
        return {
            'success': True,
            'message': 'Successfully retrieved domain and environment variables',
            'application_uuid': app_uuid,
            'domain': domain,
            'fqdn': domain,
            'environment_variables': envs_result
        }
                    
    except Exception as e:
        error_msg = f"Failed to get domain and environment variables: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }


if __name__ == "__main__":
    logger.info("Starting Chrome MCP Server with Full Integration on 0.0.0.0:8000...")
    logger.info("Available tools:")
    logger.info("  - Screenshot: take_screenshot, get_page_title, ask_about_screenshot, health_check")
    logger.info("  - Codegen: codegen_create_agent_run, codegen_get_agent_run, codegen_reply_to_agent_run,")
    logger.info("             codegen_list_agent_runs, codegen_cancel_agent_run")
    logger.info("  - GitHub: github_create_repo, github_fork_repo, github_list_repos, github_search_repo, github_get_repo_tree,")
    logger.info("            github_list_pull_requests, github_get_pull_request, github_merge_pull_request,")
    logger.info("            github_list_pull_request_files, github_check_pull_request_merged, github_update_pull_request,")
    logger.info("            github_set_pr_ready_for_review, github_get_file_content, github_update_file, github_create_file")
    logger.info("  - Coolify: coolify_list_applications, coolify_list_servers, coolify_get_server_details,")
    logger.info("             coolify_create_application, coolify_create_private_github_app_application,")
    logger.info("             coolify_restart_application, coolify_stop_application,")
    logger.info("             get_coolify_domain_and_envs")
    logger.info(f"ImgBB configured: {bool(IMGBB_API_KEY)}")
    logger.info(f"OpenRouter configured: {bool(OPENROUTER_API_KEY)}")
    logger.info(f"Codegen configured: {bool(CODEGEN_ORG_ID and CODEGEN_API_TOKEN)}")
    logger.info(f"GitHub configured: {bool(GITHUB_API_TOKEN)}")
    logger.info(f"Coolify configured: {bool(COOLIFY_API_TOKEN)}")
    
    mcp.run(transport="http", host="0.0.0.0", port=8000)
@mcp.tool()
async def coolify_create_private_github_app_application(
    github_app_uuid: str,
    git_repository: str,
    name: str,
    git_branch: str = "main",
    build_pack: str = "dockercompose",
    docker_compose_location: str = "docker-compose.yml",
    instant_deploy: bool = True,
    environment_name: str = "production",
    project_uuid: Optional[str] = None,
    server_uuid: Optional[str] = None,
    domains: Optional[str] = None,
    api_token: Optional[str] = None
) -> dict:
    """
    Create and deploy a new application in Coolify from a private GitHub repository using GitHub App integration.
    Specifically designed for docker-compose deployments with compose files in the root directory.

    Args:
        github_app_uuid: UUID of the GitHub App configured in Coolify Sources (required)
        git_repository: Repository identifier (required, e.g., "Ntrakiyski/chrome-mcp")
        name: Application name in Coolify (required)
        git_branch: Git branch to deploy (default: "main")
        build_pack: Build pack type (default: "dockercompose")
        docker_compose_location: Path to docker-compose file (default: "docker-compose.yml")
        instant_deploy: Whether to deploy immediately after creation (default: True)
        environment_name: Environment name (default: "production")
        project_uuid: Coolify project UUID (optional, defaults to hardcoded value)
        server_uuid: Coolify server UUID (optional, defaults to hardcoded value)
        domains: Comma-separated domains (optional, e.g., "app.example.com,www.app.example.com")
        api_token: Coolify API token (optional, defaults to COOLIFY_API_TOKEN env var)

    Returns:
        dict: {
            'success': bool,
            'message': str,
            'application_uuid': str,
            'application': dict
        }

    Examples:
        - coolify_create_private_github_app_application("github-app-uuid", "Ntrakiyski/chrome-mcp", "my-private-app")
        - coolify_create_private_github_app_application("github-app-uuid", "Ntrakiyski/chrome-mcp", "test-app", git_branch="develop", domains="test.example.com")
    """
    logger.info(f"Creating Coolify private GitHub App application: {name} from {git_repository}")

    token = api_token or COOLIFY_API_TOKEN
    project_id = project_uuid or COOLIFY_PROJECT_UUID
    server_id = server_uuid or COOLIFY_SERVER_UUID

    if not token:
        return {
            'success': False,
            'message': 'COOLIFY_API_TOKEN environment variable must be set'
        }

    try:
        url = f"{COOLIFY_API_BASE_URL}/applications/private-github-app"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "project_uuid": project_id,
            "server_uuid": server_id,
            "environment_name": environment_name,
            "github_app_uuid": github_app_uuid,
            "git_repository": git_repository,
            "git_branch": git_branch,
            "name": name,
            "build_pack": build_pack,
            "docker_compose_location": docker_compose_location,
            "instant_deploy": instant_deploy
        }

        # Add domains if provided
        if domains:
            payload["domains"] = domains

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                result = await response.json()

                if response.status == 200 or response.status == 201:
                    app_uuid = result.get('uuid', result.get('id'))
                    logger.info(f"Private application created successfully: {name} (UUID: {app_uuid})")
                    return {
                        'success': True,
                        'message': 'Private application created successfully',
                        'application_uuid': app_uuid,
                        'application': {
                            'uuid': app_uuid,
                            'name': name,
                            'git_repository': git_repository,
                            'git_branch': git_branch,
                            'build_pack': build_pack,
                            'status': result.get('status', 'created'),
                            'domains': domains,
                            'fqdn': result.get('fqdn', ''),
                            'environment_name': environment_name
                        }
                    }
                else:
                    error_msg = result.get('message', f'API request failed with status {response.status}')
                    raise Exception(error_msg)

    except Exception as e:
        error_msg = f"Failed to create private application: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }

