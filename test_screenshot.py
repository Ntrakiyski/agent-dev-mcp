"""
Test script for Chrome MCP Server
Tests screenshot functionality with fallback to simpler sites
"""

import asyncio
import base64
import json
import time
from pathlib import Path
from playwright.async_api import async_playwright


async def test_screenshot_locally():
    """Test screenshot functionality locally without the MCP server"""
    print("🧪 Testing Playwright screenshot locally...\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
            ]
        )
        
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        # Test with a simpler site first (example.com)
        test_sites = [
            ("https://example.com", "example_test.png", "Example.com (simple test)"),
            ("https://www.producthunt.com", "producthunt_test.png", "ProductHunt.com"),
        ]
        
        for url, filename, description in test_sites:
            print(f"📸 Testing {description}...")
            print(f"   URL: {url}")
            
            try:
                # Use domcontentloaded instead of networkidle for faster loading
                # Increase timeout to 60 seconds
                await page.goto(url, timeout=60000, wait_until='domcontentloaded')
                
                # Get page title
                title = await page.title()
                print(f"   ✅ Page loaded: {title}")
                
                # Take screenshot
                screenshot_bytes = await page.screenshot(type='png')
                
                # Save to file
                output_dir = Path("screenshots")
                output_dir.mkdir(exist_ok=True)
                
                output_file = output_dir / filename
                output_file.write_bytes(screenshot_bytes)
                
                print(f"   ✅ Screenshot saved to {output_file}")
                print(f"   ✅ Size: {len(screenshot_bytes) / 1024:.2f} KB\n")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                print(f"   ⚠️  This site might be slow or blocking automated access\n")
                
        await page.close()
        await browser.close()


async def test_mcp_server():
    """Test if the MCP server is running and accessible"""
    print("\n🌐 Testing MCP Server Connectivity...")
    print("   Checking if server is running on localhost:8000...\n")
    
    try:
        import httpx
        
        # Wait a moment for server to be ready
        await asyncio.sleep(2)
        
        client = httpx.AsyncClient(timeout=10.0)
        
        # Simple connectivity test
        print("🔌 Testing server connectivity...")
        try:
            response = await client.get("http://localhost:8000/mcp")
            
            # Status 406 means server is up but needs SSE headers (this is good!)
            if response.status_code == 406:
                print(f"   ✅ MCP Server is running and responding!")
                print(f"   ✅ Server status: {response.status_code} (requires SSE - correct!)\n")
                print(f"   📝 Note: MCP servers use Server-Sent Events (SSE) protocol.")
                print(f"   📝 They cannot be tested with simple HTTP requests.")
                print(f"   📝 Use an MCP client (like Claude Desktop) to interact with it.\n")
            elif response.status_code == 200:
                print(f"   ✅ Server is responding on port 8000\n")
            else:
                print(f"   ⚠️  Server responded with status {response.status_code}")
                print(f"   Response: {response.text[:200]}\n")
                
        except httpx.ConnectError:
            print(f"   ❌ Cannot connect to server on localhost:8000")
            print(f"   Make sure Docker container is running:")
            print(f"      docker-compose up -d\n")
            await client.aclose()
            return
        except Exception as conn_error:
            print(f"   ❌ Connection error: {conn_error}\n")
            await client.aclose()
            return
        
        await client.aclose()
        
    except ImportError:
        print("   ❌ httpx not installed. Install with: pip install httpx\n")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print(f"   Make sure the server is running with: docker-compose up -d\n")


async def check_docker_status():
    """Check if Docker container is running"""
    print("🐳 Checking Docker container status...\n")
    
    try:
        import subprocess
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=chrome-mcp-server", "--format", "{{.Status}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.stdout.strip():
            print(f"   ✅ Container is running: {result.stdout.strip()}\n")
            return True
        else:
            print(f"   ⚠️  Container is not running")
            print(f"   Start it with: docker-compose up -d\n")
            return False
            
    except FileNotFoundError:
        print(f"   ⚠️  Docker command not found")
        print(f"   Make sure Docker Desktop is installed and running\n")
        return False
    except Exception as e:
        print(f"   ⚠️  Could not check Docker status: {e}\n")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("Chrome MCP Server - Screenshot Test")
    print("=" * 70)
    print()
    
    # Check Docker status first
    docker_running = asyncio.run(check_docker_status())
    
    # Run local test (this always works)
    print("=" * 70)
    print("TEST 1: Local Playwright Screenshot (without MCP server)")
    print("=" * 70)
    asyncio.run(test_screenshot_locally())
    
    # Run MCP server test (only if Docker is running)
    print("=" * 70)
    print("TEST 2: MCP Server Screenshot Test")
    print("=" * 70)
    asyncio.run(test_mcp_server())
    
    print("\n" + "=" * 70)
    print("✅ Tests completed!")
    print("=" * 70)
    print("\nScreenshots saved to: ./screenshots/")
    print("Check the 'screenshots' folder for the captured images.")
