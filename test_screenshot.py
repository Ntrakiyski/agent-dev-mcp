"""
Test script for Chrome MCP Server
Tests screenshot functionality with ProductHunt.com
"""

import asyncio
import base64
import json
from pathlib import Path
from playwright.async_api import async_playwright


async def test_screenshot_locally():
    """Test screenshot functionality locally without the MCP server"""
    print("🧪 Testing Playwright screenshot locally...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ]
        )
        
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        # Test with ProductHunt
        url = "https://www.producthunt.com"
        print(f"📸 Capturing screenshot of {url}...")
        
        try:
            await page.goto(url, timeout=30000, wait_until='networkidle')
            
            # Get page title
            title = await page.title()
            print(f"✅ Page title: {title}")
            
            # Take screenshot
            screenshot_bytes = await page.screenshot(type='png')
            
            # Save to file
            output_dir = Path("screenshots")
            output_dir.mkdir(exist_ok=True)
            
            output_file = output_dir / "producthunt_test.png"
            output_file.write_bytes(screenshot_bytes)
            
            print(f"✅ Screenshot saved to {output_file} ({len(screenshot_bytes)} bytes)")
            print(f"✅ Screenshot size: {len(screenshot_bytes) / 1024:.2f} KB")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            
        finally:
            await page.close()
            await browser.close()


async def test_mcp_server():
    """Test the MCP server via HTTP (if running)"""
    print("\n🌐 Testing MCP Server (make sure server is running on localhost:8000)...")
    
    try:
        import httpx
        
        client = httpx.AsyncClient(timeout=60.0)
        
        # Test health check
        print("🏥 Testing health check...")
        response = await client.post(
            "http://localhost:8000/call-tool",
            json={
                "name": "health_check",
                "arguments": {}
            }
        )
        print(f"Health check response: {response.json()}")
        
        # Test screenshot
        print("\n📸 Testing screenshot via MCP server...")
        response = await client.post(
            "http://localhost:8000/call-tool",
            json={
                "name": "take_screenshot",
                "arguments": {
                    "url": "https://www.producthunt.com",
                    "viewport_width": 1920,
                    "viewport_height": 1080
                }
            }
        )
        
        result = response.json()
        
        if "result" in result:
            # Extract base64 data
            data_url = result["result"]
            if data_url.startswith("data:image/png;base64,"):
                base64_data = data_url.split(",")[1]
                screenshot_bytes = base64.b64decode(base64_data)
                
                # Save screenshot
                output_dir = Path("screenshots")
                output_dir.mkdir(exist_ok=True)
                output_file = output_dir / "producthunt_mcp.png"
                output_file.write_bytes(screenshot_bytes)
                
                print(f"✅ Screenshot saved to {output_file} ({len(screenshot_bytes)} bytes)")
            else:
                print(f"✅ Screenshot captured (unexpected format)")
        else:
            print(f"❌ Error in response: {result}")
            
        await client.aclose()
        
    except ImportError:
        print("❌ httpx not installed. Install with: pip install httpx")
    except Exception as e:
        print(f"❌ Error connecting to MCP server: {e}")
        print("Make sure the server is running with: docker-compose up")


if __name__ == "__main__":
    print("=" * 60)
    print("Chrome MCP Server - Screenshot Test")
    print("=" * 60)
    
    # Run local test
    asyncio.run(test_screenshot_locally())
    
    # Run MCP server test
    asyncio.run(test_mcp_server())
    
    print("\n" + "=" * 60)
    print("✅ Tests completed!")
    print("=" * 60)

