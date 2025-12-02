#!/usr/bin/env python3
"""
Detailed Confluence connection debugging script.

This script provides verbose output to help diagnose connection issues.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory
project_root = Path(__file__).parent

# Load .env file from project root
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

# Add src to path
sys.path.insert(0, str(project_root / "src"))

from atlassian import Confluence
from loguru import logger
from atlassian_migration_tool.utils.config_loader import load_config
from atlassian_migration_tool.utils.logger import setup_logger

# Set up detailed logging
setup_logger(level="DEBUG")


def test_confluence_detailed():
    """Test Confluence connection with detailed output."""
    
    print("\n" + "="*70)
    print("CONFLUENCE CONNECTION DEBUG TEST")
    print("="*70 + "\n")
    
    # Load config
    try:
        config = load_config()
        conf_config = config['atlassian']['confluence']
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False
    
    # Display configuration (redacted)
    print("📋 Configuration:")
    print(f"   URL: {conf_config['url']}")
    print(f"   Username: {conf_config['username']}")
    print(f"   API Token: {'*' * 20} (from env: CONFLUENCE_API_TOKEN)")
    print(f"   Cloud Mode: {conf_config.get('cloud', True)}")
    print(f"   Spaces: {conf_config.get('spaces', [])}")
    print()
    
    # Check environment variable
    api_token = os.getenv('CONFLUENCE_API_TOKEN')
    if not api_token:
        print("⚠️  WARNING: CONFLUENCE_API_TOKEN environment variable not set!")
        print("   The tool will try to use the literal string '${CONFLUENCE_API_TOKEN}'")
        print()
    else:
        print(f"✅ Environment variable CONFLUENCE_API_TOKEN is set (length: {len(api_token)})")
        print()
    
    # Initialize Confluence client
    print("🔌 Initializing Confluence client...")
    try:
        confluence = Confluence(
            url=conf_config['url'],
            username=conf_config['username'],
            password=conf_config['api_token'],
            cloud=conf_config.get('cloud', True)
        )
        print("✅ Confluence client initialized")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize Confluence client: {e}")
        logger.exception("Initialization error")
        return False
    
    # Test 1: Get server info (for Server/DC)
    if not conf_config.get('cloud', True):
        print("🧪 Test 1: Getting server info...")
        try:
            server_info = confluence.get("/rest/api/")
            print(f"✅ Server API accessible")
            print(f"   Server version info: {server_info}")
            print()
        except Exception as e:
            print(f"❌ Failed to get server info: {e}")
            print(f"   Error type: {type(e).__name__}")
            logger.exception("Server info test failed")
            print()
    
    # Test 2: List spaces
    print("🧪 Test 2: Listing spaces...")
    try:
        spaces_response = confluence.get_all_spaces(start=0, limit=5)
        
        if isinstance(spaces_response, dict) and 'results' in spaces_response:
            spaces = spaces_response['results']
            print(f"✅ Successfully retrieved spaces")
            print(f"   Total spaces found: {len(spaces)}")
            
            if spaces:
                print("\n   First few spaces:")
                for space in spaces[:3]:
                    print(f"     - {space.get('key', 'N/A')}: {space.get('name', 'N/A')}")
            print()
        else:
            print(f"⚠️  Unexpected response format: {type(spaces_response)}")
            print(f"   Response: {spaces_response}")
            print()
            
    except Exception as e:
        print(f"❌ Failed to list spaces: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Try to provide more detailed error info
        if hasattr(e, 'response'):
            print(f"   HTTP Status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
            print(f"   Response text: {e.response.text[:200] if hasattr(e.response, 'text') else 'N/A'}...")
        
        logger.exception("Space listing test failed")
        print()
        return False
    
    # Test 3: Get current user info
    print("🧪 Test 3: Getting current user info...")
    try:
        user = confluence.get_current_user()
        print(f"✅ Successfully authenticated as:")
        print(f"   Username: {user.get('username', 'N/A')}")
        print(f"   Display Name: {user.get('displayName', 'N/A')}")
        print(f"   Email: {user.get('email', 'N/A')}")
        print()
    except Exception as e:
        print(f"⚠️  Could not get current user info: {e}")
        print(f"   (This is not critical - some instances don't support this)")
        print()
    
    # Test 4: Try to get a specific space (if configured)
    spaces_to_test = conf_config.get('spaces', [])
    if spaces_to_test:
        test_space = spaces_to_test[0]
        print(f"🧪 Test 4: Accessing specific space '{test_space}'...")
        try:
            space = confluence.get_space(test_space, expand='description.plain,homepage')
            print(f"✅ Successfully accessed space '{test_space}'")
            print(f"   Name: {space.get('name', 'N/A')}")
            print(f"   Type: {space.get('type', 'N/A')}")
            print()
        except Exception as e:
            print(f"❌ Failed to access space '{test_space}': {e}")
            print(f"   Error type: {type(e).__name__}")
            
            if hasattr(e, 'response'):
                print(f"   HTTP Status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
            
            logger.exception(f"Failed to access space {test_space}")
            print()
            return False
    
    print("="*70)
    print("✅ ALL TESTS PASSED - Confluence connection is working!")
    print("="*70 + "\n")
    return True


def main():
    """Run the debug test."""
    try:
        success = test_confluence_detailed()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        logger.exception("Unexpected error during testing")
        sys.exit(1)


if __name__ == "__main__":
    main()
