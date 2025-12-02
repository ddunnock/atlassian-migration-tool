#!/usr/bin/env python3
"""
Test which Confluence API endpoints actually work on IL4.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
import time

# Load .env
project_root = Path(__file__).parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path, override=True)

token = os.getenv('CONFLUENCE_API_TOKEN')
url = "https://confluence.il4.dso.mil"
space_key = "NSTTCONORBIT"

session = requests.Session()
session.headers.update({
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
})

print("\n" + "="*70)
print("TESTING IL4 CONFLUENCE API ENDPOINTS")
print("="*70 + "\n")

# Test 1: Basic content list (what worked before)
print("Test 1: Basic content list (from our working test)")
print("-" * 70)
try:
    response = session.get(
        f"{url}/rest/api/content",
        params={'spaceKey': space_key, 'limit': 5},
        timeout=30
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS - Found {len(data.get('results', []))} pages")
        if data.get('results'):
            print(f"   First page ID: {data['results'][0].get('id')}")
            print(f"   First page title: {data['results'][0].get('title')}")
    else:
        print(f"❌ Failed: {response.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")

time.sleep(2)

# Test 2: Try with type filter
print("\nTest 2: Content list with type=page filter")
print("-" * 70)
try:
    response = session.get(
        f"{url}/rest/api/content",
        params={'spaceKey': space_key, 'type': 'page', 'limit': 5},
        timeout=30
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS - Found {len(data.get('results', []))} pages")
    else:
        print(f"❌ Failed: {response.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")

time.sleep(2)

# Test 3: Try different start values
print("\nTest 3: Content list with start=0 explicitly")
print("-" * 70)
try:
    response = session.get(
        f"{url}/rest/api/content",
        params={'spaceKey': space_key, 'start': 0, 'limit': 5},
        timeout=30
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS - Found {len(data.get('results', []))} pages")
    else:
        print(f"❌ Failed: {response.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")

time.sleep(2)

# Test 4: Try with larger limit
print("\nTest 4: Content list with limit=100")
print("-" * 70)
try:
    response = session.get(
        f"{url}/rest/api/content",
        params={'spaceKey': space_key, 'start': 0, 'limit': 100},
        timeout=30
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS - Found {len(data.get('results', []))} pages")
    else:
        print(f"❌ Failed: {response.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*70)
print("RECOMMENDATION")
print("="*70)
print("\nIf Test 1 succeeded but later tests with more params failed,")
print("IL4 has issues with certain parameter combinations.")
print("We need to use the simplest API call possible.")
