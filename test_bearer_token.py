#!/usr/bin/env python3
"""
Test Confluence connection using bearer token authentication.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

# Get the project root directory
project_root = Path(__file__).parent

# Load .env file from project root
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Get credentials from environment
api_token = os.getenv('CONFLUENCE_API_TOKEN')
if not api_token:
    print("ERROR: CONFLUENCE_API_TOKEN not set in environment")
    sys.exit(1)

url = "https://confluence.il4.dso.mil"

print("\n" + "="*70)
print("TESTING BEARER TOKEN AUTHENTICATION")
print("="*70 + "\n")
print(f"URL: {url}")
print(f"Token length: {len(api_token)}")
print()

# Test 1: Direct bearer token
print("Test 1: Using Bearer token directly")
print("-" * 70)
try:
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    response = requests.get(
        f"{url}/rest/api/space",
        headers=headers,
        params={"limit": 1},
        verify=True  # Set to False if SSL issues
    )
    
    if response.status_code == 200:
        print("✅ SUCCESS with Bearer token!")
        result = response.json()
        print(f"   Found {len(result.get('results', []))} space(s)")
        print("\n" + "="*70)
        print("USE BEARER TOKEN AUTHENTICATION")
        print("="*70)
        sys.exit(0)
    else:
        print(f"❌ Failed with status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ Failed: {e}")

print()

# Test 2: Token might already be in "username:token" format (base64)
print("Test 2: Decoding base64 token")
print("-" * 70)
try:
    import base64
    decoded = base64.b64decode(api_token).decode('utf-8')
    print(f"   Decoded token format: {decoded.split(':')[0]}:***")
    
    if ':' in decoded:
        username, token = decoded.split(':', 1)
        print(f"   Username from token: {username}")
        print(f"   Token portion length: {len(token)}")
        
        # Try with decoded credentials
        sys.path.insert(0, str(project_root / "src"))
        from atlassian import Confluence
        
        confluence = Confluence(
            url=url,
            username=username,
            password=token,
            cloud=False
        )
        
        result = confluence.get_all_spaces(start=0, limit=1)
        print("✅ SUCCESS with decoded credentials!")
        print(f"   Found {len(result.get('results', []))} space(s)")
        print(f"\n   Username to use: {username}")
        print(f"   Token to use: {token[:10]}...")
        sys.exit(0)
        
except Exception as e:
    print(f"❌ Failed: {e}")

print()

# Test 3: Try with your L3Harris email
print("Test 3: Using L3Harris email with token")
print("-" * 70)
try:
    sys.path.insert(0, str(project_root / "src"))
    from atlassian import Confluence
    
    confluence = Confluence(
        url=url,
        username="david.dunnock@l3harris.com",
        password=api_token,
        cloud=False
    )
    
    result = confluence.get_all_spaces(start=0, limit=1)
    print("✅ SUCCESS with L3Harris email!")
    print(f"   Found {len(result.get('results', []))} space(s)")
    print("\n   Use username: david.dunnock@l3harris.com")
    sys.exit(0)
    
except Exception as e:
    print(f"❌ Failed: {e}")

print()
print("="*70)
print("❌ ALL AUTHENTICATION METHODS FAILED")
print("="*70)
print("\nYou may need to:")
print("1. Generate a Personal Access Token (PAT) in Confluence")
print("2. Use your actual password instead of a token")
print("3. Check if CAC/PKI authentication is required")
sys.exit(1)
