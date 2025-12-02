"""
Simple Confluence client using bearer token authentication.
"""

import requests
from typing import Dict, Any, List, Optional


class SimpleBearerConfluence:
    """Simple Confluence client that uses bearer token authentication."""
    
    def __init__(self, url: str, token: str):
        """
        Initialize the client.
        
        Args:
            url: Confluence base URL
            token: Bearer token for authentication
        """
        self.url = url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })
    
    def _get(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a GET request."""
        import time
        from loguru import logger
        url = f"{self.url}/{path.lstrip('/')}"
        
        # Add delay to avoid overwhelming IL4 (flaky server)
        time.sleep(0.5)  # 500ms delay between calls
        
        # Debug: log the exact request
        logger.debug(f"API Request: {url} with params: {params}")
        
        # Retry logic for IL4 instability
        for attempt in range(3):
            try:
                response = self.session.get(url, params=params, timeout=30)
                logger.debug(f"Response status: {response.status_code}")
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.debug(f"Request failed (attempt {attempt + 1}/3): {e}")
                if attempt < 2:  # Retry
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise
    
    def get_all_spaces(self, start: int = 0, limit: int = 500, expand: Optional[str] = None) -> Dict[str, Any]:
        """Get all spaces."""
        params = {'start': start, 'limit': limit}
        if expand:
            params['expand'] = expand
        return self._get('rest/api/space', params=params)
    
    def get_space(self, space_key: str, expand: Optional[str] = None) -> Dict[str, Any]:
        """Get a specific space."""
        params = {}
        # Don't use expand for IL4 - causes 500 errors
        # if expand:
        #     params['expand'] = expand
        return self._get(f'rest/api/space/{space_key}', params=params)
    
    def get_all_pages_from_space(self, space: str, start: int = 0, limit: int = 100, expand: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all pages from a space."""
        # IL4 is sensitive to parameter order - match working test exactly
        params = {'spaceKey': space, 'limit': limit}
        # Only add start if not 0 (IL4 doesn't like start=0 explicitly)
        if start > 0:
            params['start'] = start
        # Don't use expand for IL4 - causes 500 errors
        # if expand:
        #     params['expand'] = expand
        result = self._get('rest/api/content', params=params)
        return result.get('results', [])
    
    def get_page_by_id(self, page_id: str, expand: Optional[str] = None) -> Dict[str, Any]:
        """Get a page by ID with content."""
        # For IL4, we need to get content separately to avoid 500 errors
        # First get basic page info
        page = self._get(f'rest/api/content/{page_id}')
        
        # Then get the body content separately
        try:
            body = self._get(f'rest/api/content/{page_id}', params={'expand': 'body.storage'})
            if 'body' in body:
                page['body'] = body['body']
        except:
            # If body fails, continue without it
            pass
            
        return page
    
    def get_page_child_by_type(self, page_id: str, type: str = 'page', start: int = 0, limit: int = 100, expand: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get child pages of a page."""
        params = {'start': start, 'limit': limit}
        # Don't use expand for IL4 - causes 500 errors  
        # if expand:
        #     params['expand'] = expand
        result = self._get(f'rest/api/content/{page_id}/child/{type}', params=params)
        return result.get('results', [])
