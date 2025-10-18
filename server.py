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
                'public_url': public_url,
                'screenshot_base64': f"data:image/png;base64,{screenshot_b64}"
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
    agent_run_id: str,
    message: str,
    org_id: Optional[str] = None,
    api_token: Optional[str] = None
) -> dict:
    """
    Reply to an existing Codegen agent run with additional instructions or feedback.
    
    Args:
        agent_run_id: ID of the agent run to reply to (required)
        message: Your reply message to the agent (required)
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
        - codegen_reply_to_agent_run("123456", "Please also add unit tests")
        - codegen_reply_to_agent_run("123456", "Looks good, ship it!", org_id="123")
    """
    logger.info(f"Replying to Codegen agent run: {agent_run_id}")
    
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
        payload = {"message": message}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                result = await response.json()
                
                if response.status == 200 or response.status == 201:
                    logger.info(f"Reply sent successfully to agent run: {agent_run_id}")
                    return {
                        'success': True,
                        'message': 'Reply sent successfully',
                        'agent_run_id': agent_run_id,
                        'status': result.get('status', 'processing')
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
    offset: int = 0,
    status: Optional[str] = None,
    org_id: Optional[str] = None,
    api_token: Optional[str] = None
) -> dict:
    """
    List all Codegen agent runs for an organization.
    
    Args:
        limit: Maximum number of runs to return (default: 10)
        offset: Number of runs to skip (default: 0)
        status: Filter by status (optional: 'pending', 'running', 'completed', 'failed')
        org_id: Organization ID (optional, defaults to CODEGEN_ORG_ID env var)
        api_token: API token (optional, defaults to CODEGEN_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'runs': list[dict],
            'total': int
        }
    
    Examples:
        - codegen_list_agent_runs()
        - codegen_list_agent_runs(limit=20, status="completed")
    """
    logger.info(f"Listing Codegen agent runs (limit: {limit}, offset: {offset})")
    
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
        url = f"{CODEGEN_BASE_URL}/v1/organizations/{org}/agents/runs"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        params = {
            "limit": limit,
            "offset": offset
        }
        if status:
            params["status"] = status
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                result = await response.json()
                
                if response.status == 200:
                    runs = result.get('items', result.get('runs', []))
                    logger.info(f"Retrieved {len(runs)} agent runs")
                    return {
                        'success': True,
                        'message': f'Retrieved {len(runs)} agent runs',
                        'runs': runs,
                        'total': result.get('total', len(runs))
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
        url = f"{GITHUB_API_BASE_URL}/user/repos"
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


@mcp.tool()
async def github_search_repo(
    query: str,
    username: Optional[str] = None,
    api_token: Optional[str] = None
) -> dict:
    """
    Search for a specific GitHub repository.
    
    Args:
        query: Search query (required)
        username: Filter by username (optional)
        api_token: GitHub API token (optional, defaults to GITHUB_API_TOKEN env var)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'repos': list[dict],
            'total_count': int
        }
    
    Examples:
        - github_search_repo("forest")
        - github_search_repo("react", username="facebook")
    """
    logger.info(f"Searching GitHub repositories: {query}")
    
    token = api_token or GITHUB_API_TOKEN
    if not token:
        return {
            'success': False,
            'message': 'GITHUB_API_TOKEN environment variable must be set'
        }
    
    try:
        # Build search query
        search_query = f"{query} in:name"
        if username:
            search_query += f" user:{username}"
        
        url = f"{GITHUB_API_BASE_URL}/search/repositories"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        params = {"q": search_query}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                result = await response.json()
                
                if response.status == 200:
                    repos = [{'name': r.get('name'), 'full_name': r.get('full_name'),
                             'url': r.get('html_url'), 'description': r.get('description')}
                            for r in result.get('items', [])]
                    logger.info(f"Found {result.get('total_count', 0)} repositories")
                    return {
                        'success': True,
                        'message': f"Found {result.get('total_count', 0)} repositories",
                        'repos': repos,
                        'total_count': result.get('total_count', 0)
                    }
                else:
                    error_msg = result.get('message', f'API request failed with status {response.status}')
                    raise Exception(error_msg)
                    
    except Exception as e:
        error_msg = f"Failed to search repositories: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'repos': [],
            'total_count': 0
        }


# =============================================================================
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


if __name__ == "__main__":
    logger.info("Starting Chrome MCP Server with Full Integration on 0.0.0.0:8000...")
    logger.info("Available tools:")
    logger.info("  - Screenshot: take_screenshot, get_page_title, ask_about_screenshot, health_check")
    logger.info("  - Codegen: codegen_create_agent_run, codegen_get_agent_run, codegen_reply_to_agent_run,")
    logger.info("             codegen_list_agent_runs, codegen_cancel_agent_run")
    logger.info("  - GitHub: github_create_repo, github_list_repos, github_search_repo")
    logger.info("  - Coolify: coolify_list_applications, coolify_list_servers, coolify_get_server_details,")
    logger.info("             coolify_create_application, coolify_restart_application, coolify_stop_application")
    logger.info(f"ImgBB configured: {bool(IMGBB_API_KEY)}")
    logger.info(f"OpenRouter configured: {bool(OPENROUTER_API_KEY)}")
    logger.info(f"Codegen configured: {bool(CODEGEN_ORG_ID and CODEGEN_API_TOKEN)}")
    logger.info(f"GitHub configured: {bool(GITHUB_API_TOKEN)}")
    logger.info(f"Coolify configured: {bool(COOLIFY_API_TOKEN)}")
    
    mcp.run(transport="http", host="0.0.0.0", port=8000)
