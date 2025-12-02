#!/usr/bin/env python3
"""
Test which Confluence space endpoints work on IL4.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

# Load .env
project_root = Path(__file__).parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path, override=True)

token = os.getenv('CONFLUENCE_API_TOKEN')
if not token:
    print("ERROR: CONFLUENCE_API_TOKEN not set")
    sys.exit(1)

url = "https://confluence.il4.dso.mil"
session = requests.Session()
session.headers.update({
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
})

print("\n" + "="*70)
print("TESTING IL4 CONFLUENCE SPACE ACCESS")
print("="*70 + "\n")

# Test different space keys
space_keys = [
    "NSTTCONORBIT",
    "nsttconorbit",  # lowercase
    "NSTTC",
    "~NSTTCONORBIT",
]

print("Test 1: Try getting space metadata directly")
print("-" * 70)
for key in space_keys:
    try:
        response = session.get(f"{url}/rest/api/space/{key}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Space key '{key}' found!")
            print(f"   Name: {data.get('name', 'N/A')}")
            print(f"   Key: {data.get('key', 'N/A')}")
            print(f"   Type: {data.get('type', 'N/A')}")
            break
        else:
            print(f"❌ Space key '{key}': {response.status_code}")
    except Exception as e:
        print(f"❌ Space key '{key}': {e}")

print("\n" + "="*70)
print("Test 2: Try listing content directly (pages)")
print("="*70 + "\n")

for key in space_keys:
    try:
        response = session.get(
            f"{url}/rest/api/content",
            params={'spaceKey': key, 'limit': 5}
        )
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            if results:
                print(f"✅ Found {len(results)} pages with space key '{key}'!")
                print(f"   First page: {results[0].get('title', 'N/A')}")
                print(f"\n   Use this space key: {key}")
                sys.exit(0)
            else:
                print(f"⚠️  Space key '{key}' returned 200 but no pages")
        else:
            print(f"❌ Space key '{key}': {response.status_code}")
    except Exception as e:
        print(f"❌ Space key '{key}': {e}")

print("\n" + "="*70)
print("Test 3: Search for NSTTC in space names")
print("="*70 + "\n")

try:
    # Try to list just a few spaces without expand
    response = session.get(f"{url}/rest/api/space", params={'limit': 100})
    if response.status_code == 200:
        data = response.json()
        spaces = data.get('results', [])
        print(f"Found {len(spaces)} spaces. Searching for NSTTC...")
        
        for space in spaces:
            name = space.get('name', '')
            key = space.get('key', '')
            if 'NSTTC' in name.upper() or 'NSTTC' in key.upper():
                print(f"   ✅ {key}: {name}")
    else:
        print(f"❌ List spaces failed: {response.status_code}")
except Exception as e:
    print(f"❌ Failed to list spaces: {e}")

print("\n" + "="*70)
print("Could not find the correct space key")
print("="*70)
print("\nPlease check the space key in Confluence web UI:")
print("1. Go to https://confluence.il4.dso.mil")
print("2. Navigate to your space")
print("3. Look at the URL - it will show the space key")
print("   Example: .../display/SPACEKEY/...")
