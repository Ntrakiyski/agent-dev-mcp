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
            'screenshot_base64': str (if upload_to_cloud=False)
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
        
        return {
            "status": "healthy" if (is_connected and imgbb_configured) else "degraded",
            "browser_connected": is_connected,
            "imgbb_configured": imgbb_configured,
            "message": "Server is fully operational" if (is_connected and imgbb_configured) 
                      else "Warning: ImgBB API key not configured" if not imgbb_configured
                      else "Browser not connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "browser_connected": False,
            "imgbb_configured": False,
            "message": f"Error: {str(e)}"
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
        url = f"{CODEGEN_BASE_URL}/v1/organizations/{org}/agent-run"
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
        url = f"{CODEGEN_BASE_URL}/v1/organizations/{org}/agent-run/{agent_run_id}"
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
        url = f"{CODEGEN_BASE_URL}/v1/organizations/{org}/agent-run/{agent_run_id}/reply"
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
        url = f"{CODEGEN_BASE_URL}/v1/organizations/{org}/agent-runs"
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


if __name__ == "__main__":
    logger.info("Starting Chrome MCP Server with ImgBB & Codegen Integration on 0.0.0.0:8000...")
    logger.info("Available tools:")
    logger.info("  - Screenshot: take_screenshot, get_page_title, health_check")
    logger.info("  - Codegen: codegen_create_agent_run, codegen_get_agent_run, codegen_reply_to_agent_run")
    logger.info("             codegen_list_agent_runs, codegen_cancel_agent_run")
    logger.info(f"ImgBB configured: {bool(IMGBB_API_KEY)}")
    logger.info(f"Codegen configured: {bool(CODEGEN_ORG_ID and CODEGEN_API_TOKEN)}")
    
    mcp.run(transport="http", host="0.0.0.0", port=8000)
