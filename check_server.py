"""
Quick script to check if MCP server is accessible
"""

import requests
import json

print("🔍 Checking MCP Server Status...\n")

# Test 1: Basic connectivity
print("1️⃣ Testing basic connectivity to http://localhost:8000")
try:
    response = requests.get("http://localhost:8000", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}\n")
except requests.exceptions.ConnectionError:
    print("   ❌ Cannot connect - server might not be running")
    print("   Start with: docker-compose up -d\n")
    exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}\n")
    exit(1)

# Test 2: Health check tool
print("2️⃣ Testing health_check tool")
try:
    response = requests.post(
        "http://localhost:8000/mcp/tools/call",
        json={"name": "health_check", "arguments": {}},
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# Test 3: Get page title (lightweight test)
print("3️⃣ Testing get_page_title tool with example.com")
try:
    response = requests.post(
        "http://localhost:8000/mcp/tools/call",
        json={
            "name": "get_page_title",
            "arguments": {"url": "https://example.com"}
        },
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Response: {json.dumps(result, indent=2)}\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

print("✅ Server check completed!")
print("\nIf all tests passed, the server is working correctly.")
print("The browser error is expected - MCP servers require SSE headers.")
