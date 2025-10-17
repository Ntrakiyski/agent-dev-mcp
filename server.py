import base64
from fastmcp import MCPServer, tool, Image
from playwright.sync_api import sync_playwright

class ScreenshotMCPServer(MCPServer):
    def __init__(self):
        super().__init__(name="Screenshot MCP Server", version="1.0")

    @tool("screenshot_mobile")
    def screenshot_mobile(self, url: str, full_page: bool = True) -> Image:
        """
        Capture a screenshot at mobile viewport width (370px).
        
        Args:
            url: The URL to capture
            full_page: Whether to capture the full page or just the viewport
            
        Returns:
            Image object with PNG screenshot data
        """
        return self._take_screenshot(url, width=370, full_page=full_page)

    @tool("screenshot_desktop")
    def screenshot_desktop(self, url: str, full_page: bool = True) -> Image:
        """
        Capture a screenshot at desktop viewport width (1200px).
        
        Args:
            url: The URL to capture
            full_page: Whether to capture the full page or just the viewport
            
        Returns:
            Image object with PNG screenshot data
        """
        return self._take_screenshot(url, width=1200, full_page=full_page)

    def _take_screenshot(self, url: str, width: int, full_page: bool) -> Image:
        """
        Internal method to capture screenshots with specified dimensions.
        
        Args:
            url: The URL to capture
            width: Viewport width in pixels
            full_page: Whether to capture the full page or just the viewport
            
        Returns:
            Image object with base64-encoded PNG data
        """
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.goto(url, wait_until="networkidle")
            screenshot_bytes = page.screenshot(full_page=full_page)
            browser.close()
        
        image_b64 = base64.b64encode(screenshot_bytes).decode("ascii")
        return Image(data=image_b64, mime_type="image/png")

if __name__ == "__main__":
    server = ScreenshotMCPServer()
    server.serve()

