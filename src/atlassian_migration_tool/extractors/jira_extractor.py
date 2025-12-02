"""
Jira Content Extractor

This module provides functionality to extract content from Jira
using the atlassian-python-api library.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from atlassian import Jira
from loguru import logger

from atlassian_migration_tool.extractors.base_extractor import BaseExtractor
from atlassian_migration_tool.models.jira_models import JiraIssue, JiraProject


class JiraExtractor(BaseExtractor):
    """
    Extract content from Jira projects including issues, attachments, and metadata.

    Usage:
        >>> from atlassian_migration_tool import JiraExtractor
        >>> from atlassian_migration_tool.utils import load_config
        >>>
        >>> config = load_config()
        >>> extractor = JiraExtractor(config['atlassian']['jira'])
        >>> projects = extractor.list_projects()
        >>> project = extractor.extract_project('PROJ')
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Jira extractor.

        Args:
            config: Jira configuration dictionary
        """
        super().__init__(config)

        # Update output directory for Jira specifically
        self.output_dir = Path(config.get('output_dir', 'data/extracted/jira'))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jira client
        self.jira = Jira(
            url=config['url'],
            username=config['username'],
            password=config['api_token'],
            cloud=config.get('cloud', True)
        )

        logger.info(f"Initialized Jira extractor for {config['url']}")

    def test_connection(self) -> bool:
        """Test connection to Jira."""
        try:
            self.jira.myself()
            logger.info("Jira connection test successful")
            return True
        except Exception as e:
            logger.error(f"Jira connection test failed: {e}")
            return False

    def extract(self) -> List[JiraProject]:
        """
        Extract all configured Jira projects.

        Returns:
            List of JiraProject objects
        """
        projects = []
        project_keys = self.config.get('projects', [])

        for project_key in project_keys:
            try:
                project = self.extract_project(project_key)
                projects.append(project)
            except Exception as e:
                logger.error(f"Failed to extract project {project_key}: {e}")

        return projects

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all accessible Jira projects."""
        logger.info("Fetching list of Jira projects")

        try:
            projects = self.jira.projects(included_archived=False)
            logger.info(f"Found {len(projects)} projects")
            return projects
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            raise

    def extract_project(self, project_key: str) -> JiraProject:
        """
        Extract all content from a Jira project.

        Args:
            project_key: The project key (e.g., 'PROJ')

        Returns:
            JiraProject object containing all extracted content
        """
        logger.info(f"Extracting project: {project_key}")

        # Get project info
        project_info = self.jira.project(project_key)
        logger.info(f"Project: {project_info['name']}")

        # Create project directory
        project_dir = self.output_dir / project_key
        project_dir.mkdir(parents=True, exist_ok=True)

        # Save project metadata
        self._save_json(project_dir / 'project-metadata.json', project_info)

        # Extract all issues
        issues = self._extract_issues(project_key, project_dir)

        # Organize by issue type
        self._organize_by_issue_type(issues, project_dir)

        project = JiraProject(
            key=project_key,
            name=project_info['name'],
            type=project_info.get('projectTypeKey', 'software'),
            issues=issues,
            metadata=project_info
        )

        logger.info(f"Extracted {len(issues)} issues from project {project_key}")
        return project

    def _extract_issues(self, project_key: str, project_dir: Path) -> List[JiraIssue]:
        """
        Extract all issues from a project.

        Args:
            project_key: Project key
            project_dir: Directory to save issues

        Returns:
            List of JiraIssue objects
        """
        issues = []
        start = 0
        batch_size = 50

        # JQL to get all issues
        jql = f"project = {project_key} ORDER BY created DESC"

        logger.info(f"Fetching issues for {project_key}...")

        while True:
            try:
                # Get batch of issues
                result = self.jira.jql(
                    jql,
                    start=start,
                    limit=batch_size,
                    fields='*all'
                )

                batch_issues = result.get('issues', [])
                if not batch_issues:
                    break

                logger.info(f"Processing {len(batch_issues)} issues (total: {start + len(batch_issues)})...")

                # Process each issue
                for issue_data in batch_issues:
                    issue = self._process_issue(issue_data, project_dir)
                    issues.append(issue)

                # Check if there are more
                if len(batch_issues) < batch_size:
                    break

                start += batch_size

            except Exception as e:
                logger.error(f"Error extracting issues: {e}")
                break

        return issues

    def _process_issue(self, issue_data: Dict[str, Any], project_dir: Path) -> JiraIssue:
        """
        Process a single issue.

        Args:
            issue_data: Issue data from Jira API
            project_dir: Project directory

        Returns:
            JiraIssue object
        """
        issue_key = issue_data['key']
        fields = issue_data['fields']

        # Create issue directory
        safe_key = issue_key.replace('/', '-')
        issue_dir = project_dir / 'issues' / safe_key
        issue_dir.mkdir(parents=True, exist_ok=True)

        # Save full issue data
        self._save_json(issue_dir / 'issue.json', issue_data)

        # Extract description
        description = fields.get('description', '')
        if description:
            self._save_text(issue_dir / 'description.txt', str(description))

        # Create issue object
        issue = JiraIssue(
            key=issue_key,
            summary=fields.get('summary', ''),
            issue_type=fields.get('issuetype', {}).get('name', 'Unknown'),
            status=fields.get('status', {}).get('name', 'Unknown'),
            metadata=issue_data
        )

        return issue

    def _organize_by_issue_type(self, issues: List[JiraIssue], project_dir: Path) -> None:
        """
        Organize issues into separate files by issue type.

        Args:
            issues: List of issues
            project_dir: Project directory
        """
        # Group by issue type
        by_type = {}
        for issue in issues:
            issue_type = issue.issue_type.lower()
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append(issue)

        # Create summary files for each type
        by_type_dir = project_dir / 'by-issue-type'
        by_type_dir.mkdir(parents=True, exist_ok=True)

        for issue_type, type_issues in by_type.items():
            # Create JSON file with all issues of this type
            type_data = [
                {
                    'key': issue.key,
                    'summary': issue.summary,
                    'status': issue.status,
                    'type': issue.issue_type
                }
                for issue in type_issues
            ]
            self._save_json(by_type_dir / f"{issue_type}.json", type_data)

            # Create CSV for easy viewing
            csv_path = by_type_dir / f"{issue_type}.csv"
            with open(csv_path, 'w') as f:
                f.write("Key,Summary,Status\n")
                for issue in type_issues:
                    f.write(f"{issue.key},\"{issue.summary}\",{issue.status}\n")

            logger.info(f"Created {issue_type} file with {len(type_issues)} issues")
