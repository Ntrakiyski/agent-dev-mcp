"""
Test script to demonstrate full-page screenshots vs viewport-only screenshots
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


async def test_fullpage_vs_viewport():
    """Compare full-page vs viewport-only screenshots"""
    print("🧪 Testing Full Page vs Viewport Screenshots\n")
    
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
        
        # Test with a page that has scrollable content
        url = "https://example.com"
        
        print(f"📸 Testing with: {url}\n")
        
        # Test 1: Full page screenshot (DEFAULT)
        print("1️⃣ Full Page Screenshot (NEW DEFAULT)")
        print("   This captures the ENTIRE scrollable page")
        
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        await page.goto(url, timeout=30000, wait_until='load')
        
        # Wait for network idle
        try:
            await page.wait_for_load_state('networkidle', timeout=5000)
        except Exception:
            pass
        
        # Take FULL PAGE screenshot
        screenshot_bytes = await page.screenshot(type='png', full_page=True)
        
        output_file = output_dir / "compare_fullpage.png"
        output_file.write_bytes(screenshot_bytes)
        
        print(f"   ✅ Saved: {output_file}")
        print(f"   ✅ Size: {len(screenshot_bytes) / 1024:.2f} KB")
        print(f"   ✅ Captures ALL content (including below the fold)\n")
        
        await page.close()
        
        # Test 2: Viewport only screenshot
        print("2️⃣ Viewport Only Screenshot")
        print("   This captures ONLY what's visible in the viewport")
        
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        await page.goto(url, timeout=30000, wait_until='load')
        
        # Wait for network idle
        try:
            await page.wait_for_load_state('networkidle', timeout=5000)
        except Exception:
            pass
        
        # Take VIEWPORT ONLY screenshot
        screenshot_bytes = await page.screenshot(type='png', full_page=False)
        
        output_file = output_dir / "compare_viewport.png"
        output_file.write_bytes(screenshot_bytes)
        
        print(f"   ✅ Saved: {output_file}")
        print(f"   ✅ Size: {len(screenshot_bytes) / 1024:.2f} KB")
        print(f"   ✅ Captures ONLY visible area (1920x1080)\n")
        
        await page.close()
        
        await browser.close()


if __name__ == "__main__":
    print("=" * 70)
    print("Full Page vs Viewport - Comparison Test")
    print("=" * 70)
    print()
    
    asyncio.run(test_fullpage_vs_viewport())
    
    print("=" * 70)
    print("✅ Comparison Complete!")
    print("=" * 70)
    print()
    print("📁 Check the screenshots folder:")
    print("   • compare_fullpage.png  - Entire scrollable page (NEW DEFAULT)")
    print("   • compare_viewport.png  - Only visible viewport (1920x1080)")
    print()
    print("🎯 The MCP server now defaults to full_page=True")
    print("   This means you'll capture the entire page by default!")
    print()
    print("💡 To capture only the viewport, set full_page=False:")
    print('   take_screenshot("https://example.com", full_page=False)')
    print()

