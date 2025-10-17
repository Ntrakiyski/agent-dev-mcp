import base64
from typing import Optional, Literal, List, Dict, Any
from fastmcp import FastMCP, Image
from playwright.sync_api import sync_playwright, Page, Browser
from contextlib import contextmanager

# Initialize FastMCP server
mcp = FastMCP("Enhanced Screenshot MCP Server", version="2.0")

# Type definitions for structured responses
class ScreenshotResult:
    """Result from screenshot capture"""
    def __init__(self, data: str, mime_type: str, format: str, width: int, height: int):
        self.data = data
        self.mime_type = mime_type
        self.format = format
        self.width = width
        self.height = height

class ContentResult:
    """Result from content extraction"""
    def __init__(self, content: str, url: str, title: str, format: str):
        self.content = content
        self.url = url
        self.title = title
        self.format = format

class ElementResult:
    """Result from element content extraction"""
    def __init__(self, content: Optional[str], selector_matched: bool, selector: str, format: str, error: Optional[str] = None):
        self.content = content
        self.selector_matched = selector_matched
        self.selector = selector
        self.format = format
        self.error = error

class InteractionResult:
    """Result from interaction and capture"""
    def __init__(self, success: bool, screenshot: Optional[Image], final_url: str, actions_completed: int, errors: List[str]):
        self.success = success
        self.screenshot = screenshot
        self.final_url = final_url
        self.actions_completed = actions_completed
        self.errors = errors

@contextmanager
def get_browser():
    """Context manager for browser lifecycle management"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']  # Docker-friendly flags
        )
        try:
            yield browser
        finally:
            browser.close()

@mcp.tool()
def capture_screenshot(
    url: str,
    viewport_width: int = 1920,
    viewport_height: int = 1080,
    device_scale_factor: float = 1.0,
    color_scheme: Literal["light", "dark", "no-preference"] = "no-preference",
    full_page: bool = False,
    wait_for_selector: Optional[str] = None,
    wait_timeout: int = 30000,
    output_format: Literal["png", "jpeg"] = "png",
    jpeg_quality: int = 80
) -> Image:
    """
    Capture a screenshot of a web page with extensive customization options.
    
    This tool loads a URL in a headless Chromium browser and captures the rendered page
    as an image. It supports customizable viewports, high-DPI displays, color scheme forcing,
    waiting for specific elements, and both PNG and JPEG output formats.
    
    Args:
        url: The complete URL to capture (must include http:// or https://)
        viewport_width: Viewport width in pixels (default: 1920 for desktop)
        viewport_height: Viewport height in pixels (default: 1080 for desktop)
        device_scale_factor: Device pixel ratio for high-DPI/retina displays (default: 1.0, use 2.0 for retina)
        color_scheme: Force light or dark mode rendering (default: "no-preference")
        full_page: Capture the entire page vs. just the viewport (default: False)
        wait_for_selector: CSS selector to wait for before capturing (optional)
        wait_timeout: Maximum time to wait for selector in milliseconds (default: 30000)
        output_format: Image format - "png" for lossless or "jpeg" for smaller files (default: "png")
        jpeg_quality: JPEG quality 0-100, only used when output_format is "jpeg" (default: 80)
    
    Returns:
        Image object with base64-encoded image data
    
    Examples:
        - Desktop screenshot: {"url": "https://example.com"}
        - Mobile dark mode: {"url": "https://example.com", "viewport_width": 390, "viewport_height": 844, "color_scheme": "dark"}
        - High-DPI capture: {"url": "https://example.com", "device_scale_factor": 2.0}
        - Wait for content: {"url": "https://example.com", "wait_for_selector": ".main-content"}
        - JPEG format: {"url": "https://example.com", "output_format": "jpeg", "jpeg_quality": 90}
    """
    try:
        with get_browser() as browser:
            context = browser.new_context(
                viewport={"width": viewport_width, "height": viewport_height},
                device_scale_factor=device_scale_factor,
                color_scheme=color_scheme
            )
            page = context.new_page()
            
            # Navigate to URL
            page.goto(url, wait_until="networkidle", timeout=wait_timeout)
            
            # Wait for specific selector if provided
            if wait_for_selector:
                page.wait_for_selector(wait_for_selector, timeout=wait_timeout)
            
            # Capture screenshot
            screenshot_options = {
                "full_page": full_page,
                "type": output_format
            }
            if output_format == "jpeg":
                screenshot_options["quality"] = jpeg_quality
            
            screenshot_bytes = page.screenshot(**screenshot_options)
            context.close()
        
        # Encode and return
        image_b64 = base64.b64encode(screenshot_bytes).decode("ascii")
        mime_type = f"image/{output_format}"
        return Image(data=image_b64, mime_type=mime_type)
    
    except Exception as e:
        raise Exception(f"Screenshot capture failed: {str(e)}")

@mcp.tool()
def get_page_content(
    url: str,
    format: Literal["html", "text"] = "text",
    wait_for_selector: Optional[str] = None,
    wait_timeout: int = 30000
) -> Dict[str, Any]:
    """
    Extract the content of a web page as HTML or plain text.
    
    This tool loads a URL and extracts either the full HTML source code or just the
    visible text content. Useful for AI agents that need to analyze page content
    without rendering it visually.
    
    Args:
        url: The complete URL to fetch content from (must include http:// or https://)
        format: Output format - "html" for full HTML source or "text" for visible text only (default: "text")
        wait_for_selector: Optional CSS selector to wait for before extracting (ensures content has loaded)
        wait_timeout: Maximum time to wait for selector in milliseconds (default: 30000)
    
    Returns:
        Dictionary with:
        - content: The extracted content (HTML or text)
        - url: Final URL after any redirects
        - title: Page title
        - format: The format used ("html" or "text")
        - content_length: Length of the extracted content in characters
    
    Examples:
        - Get page text: {"url": "https://example.com"}
        - Get full HTML: {"url": "https://example.com", "format": "html"}
        - Wait for content: {"url": "https://example.com", "wait_for_selector": "article"}
    """
    try:
        with get_browser() as browser:
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=wait_timeout)
            
            if wait_for_selector:
                page.wait_for_selector(wait_for_selector, timeout=wait_timeout)
            
            # Extract content based on format
            if format == "html":
                content = page.content()
            else:
                content = page.inner_text("body")
            
            title = page.title()
            final_url = page.url
        
        return {
            "content": content,
            "url": final_url,
            "title": title,
            "format": format,
            "content_length": len(content)
        }
    
    except Exception as e:
        return {
            "content": None,
            "url": url,
            "title": "",
            "format": format,
            "content_length": 0,
            "error": f"Content extraction failed: {str(e)}"
        }

@mcp.tool()
def get_element_content(
    url: str,
    selector: str,
    format: Literal["html", "text"] = "text",
    wait_timeout: int = 30000
) -> Dict[str, Any]:
    """
    Extract content from a specific element on a web page using a CSS selector.
    
    This tool is perfect for extracting specific content like article text, product
    descriptions, or any targeted element from a web page.
    
    Args:
        url: The complete URL to visit (must include http:// or https://)
        selector: CSS selector for the target element (e.g., ".article-content", "#main-heading")
        format: Output format - "html" for element HTML or "text" for visible text only (default: "text")
        wait_timeout: Maximum time to wait for element to appear in milliseconds (default: 30000)
    
    Returns:
        Dictionary with:
        - content: The extracted content from the element (or None if not found)
        - selector_matched: Boolean indicating if the selector found an element
        - selector: The CSS selector that was used
        - format: The format used ("html" or "text")
        - error: Error message if something went wrong (optional)
    
    Examples:
        - Extract article text: {"url": "https://example.com/article", "selector": "article.main"}
        - Extract heading: {"url": "https://example.com", "selector": "h1", "format": "text"}
        - Extract HTML block: {"url": "https://example.com", "selector": ".content-area", "format": "html"}
    """
    try:
        with get_browser() as browser:
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=wait_timeout)
            
            # Wait for element and extract content
            element = page.wait_for_selector(selector, timeout=wait_timeout)
            
            if element:
                if format == "html":
                    content = element.inner_html()
                else:
                    content = element.inner_text()
                
                return {
                    "content": content,
                    "selector_matched": True,
                    "selector": selector,
                    "format": format
                }
            else:
                return {
                    "content": None,
                    "selector_matched": False,
                    "selector": selector,
                    "format": format,
                    "error": f"Selector '{selector}' did not match any elements"
                }
    
    except Exception as e:
        return {
            "content": None,
            "selector_matched": False,
            "selector": selector,
            "format": format,
            "error": f"Element extraction failed: {str(e)}"
        }

@mcp.tool()
def interact_and_capture(
    url: str,
    actions: List[Dict[str, Any]],
    capture_screenshot: bool = True,
    screenshot_format: Literal["png", "jpeg"] = "png",
    viewport_width: int = 1920,
    viewport_height: int = 1080
) -> Dict[str, Any]:
    """
    Perform browser interactions (click, type, wait) and optionally capture a screenshot of the result.
    
    This powerful tool allows AI agents to interact with web pages before capturing them,
    enabling scenarios like clicking buttons, filling forms, or scrolling to reveal content.
    
    Args:
        url: The complete URL to visit (must include http:// or https://)
        actions: List of actions to perform. Each action is a dictionary with:
            - type: "click", "type", "wait", or "scroll"
            - selector: CSS selector (for click/type actions)
            - value: Text to type (for type actions)
            - duration: Milliseconds to wait (for wait actions)
            - amount: Pixels to scroll (for scroll actions)
        capture_screenshot: Whether to take a screenshot after all actions (default: True)
        screenshot_format: Image format for screenshot - "png" or "jpeg" (default: "png")
        viewport_width: Viewport width in pixels (default: 1920)
        viewport_height: Viewport height in pixels (default: 1080)
    
    Returns:
        Dictionary with:
        - success: Boolean indicating if all actions completed
        - screenshot: Image object if capture_screenshot=True (optional)
        - final_url: URL after all actions (may change due to navigation)
        - actions_completed: Number of actions successfully completed
        - errors: List of any error messages encountered
    
    Examples:
        - Click button and capture: 
          {"url": "https://example.com", "actions": [{"type": "click", "selector": ".menu-button"}]}
        - Fill form and submit:
          {"url": "https://example.com/search", "actions": [
            {"type": "type", "selector": "#search-input", "value": "playwright"},
            {"type": "click", "selector": "#search-button"}
          ]}
        - Scroll and capture:
          {"url": "https://example.com", "actions": [{"type": "scroll", "amount": 1000}]}
    """
    errors = []
    actions_completed = 0
    screenshot_data = None
    final_url = url
    
    try:
        with get_browser() as browser:
            context = browser.new_context(
                viewport={"width": viewport_width, "height": viewport_height}
            )
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Execute each action
            for i, action in enumerate(actions):
                try:
                    action_type = action.get("type")
                    
                    if action_type == "click":
                        selector = action.get("selector")
                        page.click(selector, timeout=10000)
                        actions_completed += 1
                    
                    elif action_type == "type":
                        selector = action.get("selector")
                        value = action.get("value", "")
                        page.fill(selector, value, timeout=10000)
                        actions_completed += 1
                    
                    elif action_type == "wait":
                        duration = action.get("duration", 1000)
                        page.wait_for_timeout(duration)
                        actions_completed += 1
                    
                    elif action_type == "scroll":
                        amount = action.get("amount", 0)
                        page.evaluate(f"window.scrollBy(0, {amount})")
                        actions_completed += 1
                    
                    else:
                        errors.append(f"Action {i}: Unknown action type '{action_type}'")
                
                except Exception as e:
                    errors.append(f"Action {i} ({action_type}): {str(e)}")
            
            # Capture screenshot if requested
            if capture_screenshot:
                try:
                    screenshot_bytes = page.screenshot(type=screenshot_format)
                    image_b64 = base64.b64encode(screenshot_bytes).decode("ascii")
                    screenshot_data = Image(data=image_b64, mime_type=f"image/{screenshot_format}")
                except Exception as e:
                    errors.append(f"Screenshot capture: {str(e)}")
            
            final_url = page.url
            context.close()
        
        return {
            "success": len(errors) == 0,
            "screenshot": screenshot_data,
            "final_url": final_url,
            "actions_completed": actions_completed,
            "errors": errors
        }
    
    except Exception as e:
        return {
            "success": False,
            "screenshot": None,
            "final_url": url,
            "actions_completed": actions_completed,
            "errors": errors + [f"Fatal error: {str(e)}"]
        }

# Legacy compatibility tools (convenience wrappers)
@mcp.tool()
def screenshot_mobile(url: str, full_page: bool = True) -> Image:
    """
    Convenience wrapper for capture_screenshot with mobile viewport (390x844).
    
    This is a simplified tool that captures screenshots at a typical mobile viewport size.
    For more control, use capture_screenshot instead.
    
    Args:
        url: The URL to capture
        full_page: Whether to capture the full page or just the viewport (default: True)
    
    Returns:
        Image object with PNG screenshot data
    """
    return capture_screenshot(
        url=url,
        viewport_width=390,
        viewport_height=844,
        full_page=full_page
    )

@mcp.tool()
def screenshot_desktop(url: str, full_page: bool = True) -> Image:
    """
    Convenience wrapper for capture_screenshot with desktop viewport (1920x1080).
    
    This is a simplified tool that captures screenshots at a typical desktop viewport size.
    For more control, use capture_screenshot instead.
    
    Args:
        url: The URL to capture
        full_page: Whether to capture the full page or just the viewport (default: True)
    
    Returns:
        Image object with PNG screenshot data
    """
    return capture_screenshot(
        url=url,
        viewport_width=1920,
        viewport_height=1080,
        full_page=full_page
    )

if __name__ == "__main__":
    mcp.run()
