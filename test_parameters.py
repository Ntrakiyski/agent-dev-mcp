"""
Test script to demonstrate the new MCP parameters:
- delay: Wait time after page loads
- viewport_width: Custom viewport width
- viewport_height: Custom viewport height
"""

import asyncio
import base64
from pathlib import Path
from playwright.async_api import async_playwright


async def test_screenshot_with_parameters():
    """Test screenshots with different parameters"""
    print("🧪 Testing Playwright Screenshots with Different Parameters\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
            ]
        )
        
        # Create output directory
        output_dir = Path("screenshots")
        output_dir.mkdir(exist_ok=True)
        
        # Test configurations
        test_configs = [
            {
                "name": "Default (1920x1080, no delay)",
                "url": "https://example.com",
                "width": 1920,
                "height": 1080,
                "delay": 0,
                "filename": "test_default.png"
            },
            {
                "name": "Mobile (375x812, no delay)",
                "url": "https://example.com",
                "width": 375,
                "height": 812,
                "delay": 0,
                "filename": "test_mobile.png"
            },
            {
                "name": "Tablet (768x1024, no delay)",
                "url": "https://example.com",
                "width": 768,
                "height": 1024,
                "delay": 0,
                "filename": "test_tablet.png"
            },
            {
                "name": "Desktop with 2 second delay",
                "url": "https://example.com",
                "width": 1920,
                "height": 1080,
                "delay": 2000,
                "filename": "test_with_delay.png"
            },
        ]
        
        for config in test_configs:
            print(f"📸 {config['name']}")
            print(f"   URL: {config['url']}")
            print(f"   Viewport: {config['width']}x{config['height']}")
            print(f"   Delay: {config['delay']}ms")
            
            try:
                # Create page with specific viewport
                page = await browser.new_page(
                    viewport={'width': config['width'], 'height': config['height']}
                )
                
                # Navigate to URL - wait for DOM to load
                await page.goto(config['url'], timeout=30000, wait_until='load')
                print(f"   ✅ Page loaded (DOM ready)")
                
                # Wait for network idle (all resources)
                try:
                    await page.wait_for_load_state('networkidle', timeout=5000)
                    print(f"   ✅ Network idle (all resources loaded)")
                except Exception:
                    print(f"   ⚠️  Network idle timeout (continuing anyway)")
                
                # Apply delay if specified
                if config['delay'] > 0:
                    print(f"   ⏳ Waiting {config['delay']}ms...")
                    await asyncio.sleep(config['delay'] / 1000)
                
                # Take screenshot
                screenshot_bytes = await page.screenshot(type='png')
                
                # Save to file
                output_file = output_dir / config['filename']
                output_file.write_bytes(screenshot_bytes)
                
                print(f"   ✅ Screenshot saved: {output_file}")
                print(f"   ✅ Size: {len(screenshot_bytes) / 1024:.2f} KB\n")
                
                await page.close()
                
            except Exception as e:
                print(f"   ❌ Error: {e}\n")
        
        await browser.close()


if __name__ == "__main__":
    print("=" * 70)
    print("Chrome MCP Server - Parameter Testing")
    print("=" * 70)
    print()
    
    asyncio.run(test_screenshot_with_parameters())
    
    print("=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)
    print()
    print("📁 Screenshots saved to: ./screenshots/")
    print()
    print("🎯 How to use these parameters with the MCP server:")
    print()
    print("   take_screenshot(")
    print('       url="https://example.com",')
    print("       viewport_width=1920,  # Custom width")
    print("       viewport_height=1080, # Custom height")
    print("       delay=2000            # Wait 2 seconds after load")
    print("   )")
    print()
    print("💡 Common viewport sizes:")
    print("   • Mobile (iPhone 14):    390 x 844")
    print("   • Mobile (iPhone 14 Pro Max): 430 x 932")
    print("   • Tablet (iPad):         768 x 1024")
    print("   • Desktop HD:            1920 x 1080")
    print("   • Desktop 4K:            3840 x 2160")
    print()
    print("💡 Delay recommendations:")
    print("   • Static pages:          0 ms (no delay needed)")
    print("   • Pages with animations: 1000-2000 ms")
    print("   • Heavy dynamic content: 3000-5000 ms")
    print()

