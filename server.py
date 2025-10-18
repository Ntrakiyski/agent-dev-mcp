"""
Chrome MCP Server with Playwright
Production-ready screenshot service using FastMCP
"""

import asyncio
import base64
import logging
from typing import Optional
from pathlib import Path

from fastmcp import FastMCP
from playwright.async_api import async_playwright, Browser, Page, Playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("chrome-screenshot-server")

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


@mcp.tool()
async def take_screenshot(
    url: str,
    full_page: bool = False,
    viewport_width: int = 1920,
    viewport_height: int = 1080,
    timeout: int = 30000,
    delay: int = 0
) -> str:
    """
    Take a screenshot of a web page using Chromium.
    
    Args:
        url: The URL to capture (e.g., "https://producthunt.com")
        full_page: If True, captures the entire scrollable page. If False, captures only viewport
        viewport_width: Browser viewport width in pixels (default: 1920)
        viewport_height: Browser viewport height in pixels (default: 1080)
        timeout: Page load timeout in milliseconds (default: 30000)
        delay: Additional delay in milliseconds after page loads before taking screenshot (default: 0)
               Useful for waiting for animations, lazy-loaded content, etc.
    
    Returns:
        Base64-encoded PNG screenshot
    
    Examples:
        - take_screenshot("https://producthunt.com")
        - take_screenshot("https://example.com", full_page=True)
        - take_screenshot("https://example.com", viewport_width=1280, viewport_height=720)
        - take_screenshot("https://example.com", delay=2000)  # Wait 2 seconds after load
    """
    logger.info(f"Taking screenshot of {url} (viewport: {viewport_width}x{viewport_height}, delay: {delay}ms)")
    
    try:
        # Get browser instance
        browser = await get_browser()
        
        # Create a new page with specified viewport
        page = await browser.new_page(
            viewport={'width': viewport_width, 'height': viewport_height}
        )
        
        try:
            # Navigate to URL with multiple wait strategies for full page load
            logger.info(f"Navigating to {url}...")
            
            # First, wait for the page to load (DOM content loaded)
            await page.goto(url, timeout=timeout, wait_until='load')
            logger.info("Page loaded (DOM content ready)")
            
            # Wait for network to be idle (all resources loaded)
            try:
                await page.wait_for_load_state('networkidle', timeout=5000)
                logger.info("Network idle - all resources loaded")
            except Exception as e:
                logger.warning(f"Network idle timeout (this is often normal): {e}")
            
            # Additional delay if specified (for animations, lazy loading, etc.)
            if delay > 0:
                logger.info(f"Waiting additional {delay}ms after page load...")
                await asyncio.sleep(delay / 1000)  # Convert ms to seconds
            
            # Take screenshot
            logger.info("Capturing screenshot...")
            screenshot_bytes = await page.screenshot(
                full_page=full_page,
                type='png'
            )
            
            # Encode to base64
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            logger.info(f"Screenshot captured successfully ({len(screenshot_bytes)} bytes)")
            return f"data:image/png;base64,{screenshot_b64}"
            
        finally:
            # Always close the page
            await page.close()
            logger.info("Page closed")
            
    except Exception as e:
        error_msg = f"Failed to capture screenshot: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


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
    """
    Check if the server and browser are running properly.
    
    Returns:
        Health status information
    """
    try:
        browser = await get_browser()
        is_connected = browser.is_connected()
        
        return {
            "status": "healthy" if is_connected else "degraded",
            "browser_connected": is_connected,
            "message": "Server is running" if is_connected else "Browser not connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "browser_connected": False,
            "message": f"Error: {str(e)}"
        }


if __name__ == "__main__":
    logger.info("Starting Chrome MCP Server on 0.0.0.0:8000...")
    logger.info("Available tools: take_screenshot, get_page_title, health_check")
    
    # Run FastMCP HTTP server
    # Binds to 0.0.0.0 for remote access (required for Docker)
    # Note: FastMCP.run() handles its own event loop and graceful shutdown
    mcp.run(transport="http", host="0.0.0.0", port=8000)
