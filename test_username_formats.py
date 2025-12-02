#!/usr/bin/env python3
"""
Test different username formats for IL4 Confluence authentication.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory
project_root = Path(__file__).parent

# Load .env file from project root
env_path = project_root / ".env"
print(f"Loading .env from: {env_path}")
print(f".env exists: {env_path.exists()}")
load_dotenv(dotenv_path=env_path, override=True)  # Force override existing env vars

sys.path.insert(0, str(project_root / "src"))

from atlassian import Confluence

# Get credentials from environment
api_token = os.getenv('CONFLUENCE_API_TOKEN')
if not api_token:
    print("ERROR: CONFLUENCE_API_TOKEN not set in environment")
    print(f"\nDebug info:")
    print(f"  .env path: {env_path}")
    print(f"  .env exists: {env_path.exists()}")
    print(f"  Current directory: {Path.cwd()}")
    print(f"\nAll environment variables with 'TOKEN':")
    for key, value in os.environ.items():
        if 'TOKEN' in key:
            print(f"  {key}={value[:20]}..." if len(value) > 20 else f"  {key}={value}")
    sys.exit(1)

url = "https://confluence.il4.dso.mil"

# Different username formats to try
username_formats = [
    ("dunnoda", "Just username"),
    ("david.dunnock@l3harris.com", "L3Harris email"),
    ("dunnoda@mail.mil", "Username with @mail.mil"),
    ("dunnoda@dso.mil", "Username with @dso.mil"),
    ("IL4\\dunnoda", "Domain\\username format"),
    ("David Dunnock", "Full name"),
]

print("\n" + "="*70)
print("TESTING DIFFERENT USERNAME FORMATS")
print("="*70 + "\n")
print(f"URL: {url}")
print(f"Token length: {len(api_token)}")
print()

for username, description in username_formats:
    print(f"Testing: {username} ({description})")
    print("-" * 70)
    
    try:
        # Try to connect
        confluence = Confluence(
            url=url,
            username=username,
            password=api_token,
            cloud=False
        )
        
        # Try to list spaces
        result = confluence.get_all_spaces(start=0, limit=1)
        
        print(f"✅ SUCCESS with username: {username}")
        print(f"   Found {len(result.get('results', []))} space(s)")
        print()
        print("="*70)
        print(f"USE THIS USERNAME FORMAT: {username}")
        print("="*70)
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        if hasattr(e, 'response'):
            print(f"   HTTP Status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
        print()

print("="*70)
print("❌ ALL USERNAME FORMATS FAILED")
print("="*70)
print("\nPossible issues:")
print("1. The API token might be incorrect")
print("2. The account might be locked or disabled")
print("3. IL4 might require CAC/PKI authentication")
print("4. You might need to use your actual password instead of API token")
sys.exit(1)
