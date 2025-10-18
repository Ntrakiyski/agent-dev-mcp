"""
Quick script to check if MCP server is accessible using FastMCP client
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import httpx


async def check_with_httpx():
    """Check server using httpx with SSE support"""
    print("🔍 Checking MCP Server Status with httpx...\n")
    
    print("1️⃣ Testing basic connectivity to http://localhost:8000")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/mcp", timeout=5)
            print(f"   Status: {response.status_code}")
            if response.status_code == 406:
                print(f"   ✅ Server is responding (406 = needs SSE headers, which is correct!)")
                print(f"   Response: {response.text[:100]}\n")
                return True
            else:
                print(f"   Response: {response.text[:200]}\n")
                return False
    except httpx.ConnectError:
        print("   ❌ Cannot connect to server on localhost:8000")
        print("   Make sure Docker container is running:")
        print("      docker-compose up -d\n")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
        return False


async def test_tools_via_sse():
    """Test tools using SSE requests (the proper way)"""
    print("2️⃣ Testing tools via SSE protocol...\n")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test 1: Health check
            print("   🏥 Testing health_check tool...")
            
            # For SSE endpoints, we need to send JSON-RPC requests
            request_data = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "health_check",
                    "arguments": {}
                }
            }
            
            response = await client.post(
                "http://localhost:8000/sse",
                json=request_data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream"
                }
            )
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Health check successful!")
                print(f"   Response: {response.text[:200]}\n")
            else:
                print(f"   ⚠️  Response: {response.text[:200]}\n")
                
    except Exception as e:
        print(f"   ❌ Error: {e}\n")


async def simple_connection_test():
    """Simple test to verify server is accessible"""
    print("3️⃣ Simple connection test...\n")
    
    try:
        import subprocess
        
        # Check if container is running
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=chrome-mcp-server", "--format", "{{.Status}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.stdout.strip():
            print(f"   ✅ Docker container is running: {result.stdout.strip()}")
        else:
            print(f"   ⚠️  Docker container is not running")
            print(f"   Start it with: docker-compose up -d")
            return False
        
        # Check if port is accessible
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("http://localhost:8000", timeout=2)
                print(f"   ✅ Port 8000 is accessible")
                print(f"   Server returned status: {response.status_code}")
                return True
            except httpx.ConnectError:
                print(f"   ❌ Port 8000 is not accessible")
                print(f"   Check Docker logs: docker-compose logs")
                return False
                
    except FileNotFoundError:
        print(f"   ⚠️  Docker command not found")
        return False
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("Chrome MCP Server - Quick Status Check")
    print("=" * 70)
    print()
    
    # Run checks
    asyncio.run(simple_connection_test())
    print()
    asyncio.run(check_with_httpx())
    
    print("=" * 70)
    print("📝 Understanding the Results:")
    print("=" * 70)
    print()
    print("✅ If you see '406 = needs SSE headers' - the server is working correctly!")
    print("   MCP servers use Server-Sent Events (SSE) protocol, not regular HTTP.")
    print()
    print("✅ To actually use the server, you need:")
    print("   1. An MCP client (like Claude Desktop)")
    print("   2. Or use test_screenshot.py which has proper SSE handling")
    print("   3. Or connect via the FastMCP Python client")
    print()
    print("🚀 Try running: python test_screenshot.py")
    print()

