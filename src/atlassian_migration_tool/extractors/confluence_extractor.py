"""
Confluence Content Extractor

This module provides functionality to extract content from Confluence
using the atlassian-python-api library.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime
import requests

from atlassian import Confluence
from loguru import logger

from atlassian_migration_tool.extractors.base_extractor import BaseExtractor
from atlassian_migration_tool.extractors.bearer_confluence import SimpleBearerConfluence
from atlassian_migration_tool.models.confluence_models import ConfluencePage, ConfluenceSpace


class BearerConfluence(Confluence):
    """Extended Confluence client with bearer token support."""
    
    def __init__(self, url, token=None, username=None, password=None, cloud=True, **kwargs):
        # If token is provided, use bearer auth
        if token:
            self.use_bearer = True
            self.bearer_token = token
            # Initialize parent without auth (we'll override it)
            super().__init__(url=url, username='', password='', cloud=cloud, **kwargs)
            # Remove any basic auth that was set
            if hasattr(self, 'session'):
                self.session.auth = None
        else:
            self.use_bearer = False
            super().__init__(url=url, username=username, password=password, cloud=cloud, **kwargs)
    
    def request(self, method='GET', path='/', data=None, flags=None, params=None, headers=None, files=None, trailing=False, **kwargs):
        """Override request to add bearer token."""
        if self.use_bearer:
            # Ensure session doesn't have basic auth
            if hasattr(self, 'session'):
                self.session.auth = None
            
            # Add bearer token to headers
            if headers is None:
                headers = {}
            headers['Authorization'] = f'Bearer {self.bearer_token}'
            
            # Remove any Authorization header that might be in default_headers
            if hasattr(self, 'default_headers') and 'Authorization' in self.default_headers:
                del self.default_headers['Authorization']
        
        return super().request(method=method, path=path, data=data, flags=flags, 
                              params=params, headers=headers, files=files, 
                              trailing=trailing, **kwargs)


class ConfluenceExtractor(BaseExtractor):
    """
    Extract content from Confluence spaces including pages, attachments, and metadata.

    Usage:
        >>> from atlassian_migration_tool import ConfluenceExtractor
        >>> from atlassian_migration_tool.utils import load_config
        >>>
        >>> config = load_config()
        >>> extractor = ConfluenceExtractor(config['atlassian']['confluence'])
        >>> spaces = extractor.list_spaces()
        >>> space = extractor.extract_space('ENGINEERING')
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Confluence extractor.

        Args:
            config: Confluence configuration dictionary containing:
                - url: Confluence instance URL
                - username: User email/username (not used if use_bearer_token=True)
                - api_token: API token for authentication
                - cloud: Boolean indicating Cloud vs Server/Data Center
                - use_bearer_token: Boolean indicating if bearer token auth should be used
        """
        super().__init__(config)

        # Update output directory for Confluence specifically
        self.output_dir = Path(config.get('output_dir', 'data/extracted/confluence'))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Confluence client with bearer token support
        use_bearer = config.get('use_bearer_token', False)
        
        if use_bearer:
            logger.info(f"Using bearer token authentication for {config['url']}")
            self.confluence = SimpleBearerConfluence(
                url=config['url'],
                token=config['api_token']
            )
        else:
            logger.info(f"Using basic authentication for {config['url']}")
            self.confluence = Confluence(
                url=config['url'],
                username=config['username'],
                password=config['api_token'],
                cloud=config.get('cloud', True)
            )

        logger.info(f"Initialized Confluence extractor for {config['url']}")

    def test_connection(self) -> bool:
        """
        Test connection to Confluence.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to get user info as a connection test
            self.confluence.get_all_spaces(start=0, limit=1)
            logger.info("Confluence connection test successful")
            return True
        except Exception as e:
            logger.error(f"Confluence connection test failed: {e}")
            return False

    def extract(self) -> List[ConfluenceSpace]:
        """
        Extract all configured Confluence spaces.

        Returns:
            List of ConfluenceSpace objects
        """
        spaces = []
        space_keys = self.config.get('spaces', [])

        for space_key in space_keys:
            try:
                space = self.extract_space(space_key)
                spaces.append(space)
            except Exception as e:
                logger.error(f"Failed to extract space {space_key}: {e}")

        return spaces

    def list_spaces(self) -> List[Dict[str, Any]]:
        """
        List all accessible Confluence spaces.

        Returns:
            List of space dictionaries with keys: key, name, type, _links
        """
        logger.info("Fetching list of Confluence spaces")

        try:
            spaces = self.confluence.get_all_spaces(
                start=0,
                limit=500,
                expand='description.plain,homepage'
            )

            logger.info(f"Found {len(spaces['results'])} spaces")
            return spaces['results']

        except Exception as e:
            logger.error(f"Failed to list spaces: {e}")
            raise

    def extract_space(self, space_key: str) -> ConfluenceSpace:
        """
        Extract all content from a Confluence space.

        Args:
            space_key: The space key (e.g., 'ENGINEERING')

        Returns:
            ConfluenceSpace object containing all extracted content
        """
        logger.info(f"Extracting space: {space_key}")

        # Create space directory
        space_dir = self.output_dir / space_key
        space_dir.mkdir(parents=True, exist_ok=True)

        # Try to get space metadata, but don't fail if it errors (IL4 issues)
        space_info = None
        try:
            space_info = self.confluence.get_space(space_key)
            # Save space metadata if we got it
            self._save_json(space_dir / 'space-metadata.json', space_info)
            logger.info(f"Retrieved metadata for space {space_key}")
        except Exception as e:
            logger.warning(f"Could not get space metadata (non-critical): {e}")
            # Create minimal space info
            space_info = {
                'key': space_key,
                'name': space_key,
                'type': 'global'
            }

        # Extract all pages
        pages = self._extract_pages(space_key, space_dir)

        # Create space object
        space = ConfluenceSpace(
            key=space_key,
            name=space_info.get('name', space_key),
            type=space_info.get('type', 'global'),
            pages=pages,
            metadata=space_info
        )

        logger.info(f"Extracted {len(pages)} pages from space {space_key}")
        return space

    def _extract_pages(
            self,
            space_key: str,
            space_dir: Path,
            parent_id: Optional[str] = None
    ) -> List[ConfluencePage]:
        """
        Extract all pages from a space (recursively extracts child pages).

        Args:
            space_key: Space key
            space_dir: Directory to save pages
            parent_id: Parent page ID (for extracting child pages)

        Returns:
            List of ConfluencePage objects
        """
        pages = []
        start = 0
        limit = 5  # IL4 can't handle 100, use 5 like working test

        while True:
            try:
                # Get batch of pages (without expand to avoid IL4 500 errors)
                if parent_id:
                    result = self.confluence.get_page_child_by_type(
                        page_id=parent_id,
                        type='page',
                        start=start,
                        limit=limit
                    )
                else:
                    result = self.confluence.get_all_pages_from_space(
                        space=space_key,
                        start=start,
                        limit=limit
                    )

                # Process each page
                for page_data in result:
                    page = self._process_page(page_data, space_dir)
                    pages.append(page)

                    # Extract child pages recursively
                    children = self._extract_pages(
                        space_key,
                        space_dir,
                        parent_id=page_data['id']
                    )
                    page.children = children

                # Check if there are more pages
                if len(result) < limit:
                    break

                start += limit

            except Exception as e:
                logger.error(f"Error extracting pages: {e}")
                break

        return pages

    def _process_page(
            self,
            page_data: Dict[str, Any],
            space_dir: Path
    ) -> ConfluencePage:
        """
        Process a single page, extracting content and attachments.

        Args:
            page_data: Page data from Confluence API
            space_dir: Directory to save page content

        Returns:
            ConfluencePage object
        """
        page_id = page_data['id']
        page_title = page_data['title']

        logger.debug(f"Processing page: {page_title} (ID: {page_id})")

        # Create safe filename
        safe_title = self._sanitize_filename(page_title)
        page_dir = space_dir / safe_title
        page_dir.mkdir(parents=True, exist_ok=True)

        # Save page content
        content = page_data.get('body', {}).get('storage', {}).get('value', '')
        self._save_text(page_dir / 'content.html', content)

        # Save page metadata
        self._save_json(page_dir / 'metadata.json', {
            'id': page_id,
            'title': page_title,
            'type': page_data['type'],
            'status': page_data['status'],
            'version': page_data['version'],
            'space': page_data['space'],
            'created': page_data['history']['createdDate'],
            'lastUpdated': page_data['version']['when'],
            'createdBy': page_data['history']['createdBy']['displayName'],
            'lastUpdatedBy': page_data['version']['by']['displayName'],
            'labels': self._extract_labels(page_data),
        })

        # Extract attachments if configured
        attachments = []
        if self.config.get('extract_options', {}).get('include_attachments', True):
            attachments = self._extract_attachments(page_id, page_dir)

        # Extract comments if configured
        comments = []
        if self.config.get('extract_options', {}).get('extract_comments', True):
            comments = self._extract_comments(page_id, page_dir)

        # Create page object
        page = ConfluencePage(
            id=page_id,
            title=page_title,
            content=content,
            spaceKey=page_data['space']['key'],
            version=page_data['version']['number'],
            created=page_data['history']['createdDate'],
            lastUpdated=page_data['version']['when'],
            creator=page_data['history']['createdBy']['displayName'],
            lastModifier=page_data['version']['by']['displayName'],
            labels=self._extract_labels(page_data),
            attachments=attachments,
            comments=comments,
            local_path=page_dir
        )

        return page

    def _extract_attachments(
            self,
            page_id: str,
            page_dir: Path
    ) -> List[Dict[str, Any]]:
        """
        Extract and download attachments from a page.

        Args:
            page_id: Page ID
            page_dir: Directory to save attachments

        Returns:
            List of attachment metadata dictionaries
        """
        try:
            attachments_data = self.confluence.get_attachments_from_content(
                page_id=page_id,
                start=0,
                limit=100,
                expand='version'
            )

            attachments = []
            attachments_dir = page_dir / 'attachments'
            attachments_dir.mkdir(exist_ok=True)

            for attachment in attachments_data['results']:
                # Check attachment size
                max_size = self.config.get('extract_options', {}).get(
                    'max_attachment_size_mb', 100
                ) * 1024 * 1024

                if attachment['extensions']['fileSize'] > max_size:
                    logger.warning(
                        f"Skipping large attachment: {attachment['title']} "
                        f"({attachment['extensions']['fileSize']} bytes)"
                    )
                    continue

                # Download attachment
                download_link = self.confluence.url + attachment['_links']['download']
                filename = attachment['title']
                filepath = attachments_dir / filename

                try:
                    # Download file
                    # Note: atlassian-python-api doesn't have download_attachment_from_url
                    # Use requests to download
                    import requests
                    response = requests.get(
                        download_link,
                        auth=(self.config['username'], self.config['api_token'])
                    )
                    response.raise_for_status()

                    with open(filepath, 'wb') as f:
                        f.write(response.content)

                    attachments.append({
                        'id': attachment['id'],
                        'title': attachment['title'],
                        'mediaType': attachment['metadata']['mediaType'],
                        'fileSize': attachment['extensions']['fileSize'],
                        'created': attachment['version']['when'],
                        'createdBy': attachment['version']['by']['displayName'],
                        'local_path': str(filepath)
                    })

                    logger.debug(f"Downloaded attachment: {filename}")

                except Exception as e:
                    logger.error(f"Failed to download attachment {filename}: {e}")

            return attachments

        except Exception as e:
            logger.error(f"Failed to extract attachments for page {page_id}: {e}")
            return []

    def _extract_comments(
            self,
            page_id: str,
            page_dir: Path
    ) -> List[Dict[str, Any]]:
        """
        Extract comments from a page.

        Args:
            page_id: Page ID
            page_dir: Directory to save comments

        Returns:
            List of comment dictionaries
        """
        try:
            comments_data = self.confluence.get_page_child_by_type(
                page_id=page_id,
                type='comment',
                start=0,
                limit=100,
                expand='body.storage,version'
            )

            comments = []
            for comment in comments_data:
                comments.append({
                    'id': comment['id'],
                    'author': comment['version']['by']['displayName'],
                    'created': comment['version']['when'],
                    'content': comment.get('body', {}).get('storage', {}).get('value', ''),
                })

            # Save comments
            if comments:
                self._save_json(page_dir / 'comments.json', comments)

            return comments

        except Exception as e:
            logger.error(f"Failed to extract comments for page {page_id}: {e}")
            return []

    def _extract_labels(self, page_data: Dict[str, Any]) -> List[str]:
        """Extract labels/tags from page metadata."""
        try:
            labels = page_data.get('metadata', {}).get('labels', {}).get('results', [])
            return [label['name'] for label in labels]
        except:
            return []