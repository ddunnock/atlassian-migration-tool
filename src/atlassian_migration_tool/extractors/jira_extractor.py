"""
Jira Content Extractor

This module provides functionality to extract content from Jira
using the atlassian-python-api library.
"""

import json
from pathlib import Path
from typing import Any

from atlassian import Jira
from loguru import logger

from atlassian_migration_tool.extractors.base_extractor import BaseExtractor
from atlassian_migration_tool.models.jira_models import (
    JiraAttachment,
    JiraComment,
    JiraIssue,
    JiraProject,
)


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

    def __init__(self, config: dict[str, Any]):
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

    def extract(self) -> list[JiraProject]:
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

    def list_projects(self) -> list[dict[str, Any]]:
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

    def _extract_issues(self, project_key: str, project_dir: Path) -> list[JiraIssue]:
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
                    try:
                        issue = self._process_issue(issue_data, project_dir)
                        issues.append(issue)
                    except Exception as process_error:
                        logger.error(f"Error processing issue {issue_data.get('key', 'unknown')}: {process_error}")
                        
                        # Generate schema for debugging
                        issue_key = issue_data.get('key', 'unknown')
                        schema_file = project_dir / f"debug_schema_{issue_key}.json"
                        try:
                            self.generate_issue_schema(issue_data, schema_file)
                            logger.info(f"Debug schema generated for failed issue: {schema_file}")
                        except Exception as schema_error:
                            logger.error(f"Failed to generate debug schema: {schema_error}")
                        
                        # Re-raise the original error
                        raise

                # Check if there are more
                if len(batch_issues) < batch_size:
                    break

                start += batch_size

            except Exception as e:
                logger.error(f"Error extracting issues: {e}")
                break

        return issues

    def _process_issue(self, issue_data: dict[str, Any], project_dir: Path) -> JiraIssue:
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

        # Process attachments
        attachments = []
        for attachment_data in fields.get('attachment', []):
            attachment = JiraAttachment(
                id=attachment_data['id'],
                filename=attachment_data['filename'],
                mimeType=attachment_data['mimeType'],
                size=attachment_data['size'],
                created=attachment_data['created'],
                author=attachment_data['author']['displayName']
            )
            attachments.append(attachment)

        # Process comments
        comments = []
        comment_data = fields.get('comment', {})
        for comment_item in comment_data.get('comments', []):
            comment = JiraComment(
                id=comment_item['id'],
                author=comment_item['author']['displayName'],
                created=comment_item['created'],
                updated=comment_item.get('updated'),
                body=comment_item['body']
            )
            comments.append(comment)

        # Create issue object
        issue = JiraIssue(
            id=issue_data['id'],
            key=issue_key,
            summary=fields.get('summary', ''),
            description=description,
            issue_type=fields.get('issuetype', {}).get('name', 'Unknown'),
            status=fields.get('status', {}).get('name', 'Unknown'),
            priority=fields.get('priority', {}).get('name') if fields.get('priority') else None,
            assignee=fields.get('assignee', {}).get('displayName') if fields.get('assignee') else None,
            reporter=fields.get('reporter', {}).get('displayName', 'Unknown'),
            created=fields.get('created', ''),
            updated=fields.get('updated', ''),
            projectKey=fields.get('project', {}).get('key', 'Unknown'),
            parent_key=fields.get('parent', {}).get('key') if fields.get('parent') else None,
            labels=fields.get('labels', []),
            attachments=attachments,
            comments=comments,
            custom_fields={k: v for k, v in fields.items() if k.startswith('customfield')},
            local_path=issue_dir
        )

        return issue

    def _organize_by_issue_type(self, issues: list[JiraIssue], project_dir: Path) -> None:
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
            with open(csv_path, 'w', encoding='utf-8') as f:
                f.write("Key,Summary,Status\n")
                for issue in type_issues:
                    f.write(f"{issue.key},\"{issue.summary}\",{issue.status}\n")

            logger.info(f"Created {issue_type} file with {len(type_issues)} issues")

    def generate_issue_schema(self, issue_data: dict[str, Any], output_path: str | Path = None) -> dict[str, Any]:
        """
        Generate a schema from raw JIRA issue data to help understand the structure.
        
        Args:
            issue_data: Raw issue data from JIRA API
            output_path: Optional path to save the schema file
            
        Returns:
            Dict representing the schema structure
        """
        def analyze_value(value: Any, path: str = "") -> dict[str, Any]:
            """Recursively analyze a value to determine its schema."""
            if value is None:
                return {"type": "null", "path": path}
            elif isinstance(value, bool):
                return {"type": "boolean", "path": path}
            elif isinstance(value, int):
                return {"type": "integer", "path": path}
            elif isinstance(value, float):
                return {"type": "number", "path": path}
            elif isinstance(value, str):
                return {"type": "string", "path": path, "example": value[:50] + "..." if len(value) > 50 else value}
            elif isinstance(value, list):
                if not value:
                    return {"type": "array", "items": "empty", "path": path}
                # Analyze first few items to understand array structure
                item_schemas = []
                for i, item in enumerate(value[:3]):  # Only check first 3 items
                    item_schema = analyze_value(item, f"{path}[{i}]")
                    item_schemas.append(item_schema)
                return {"type": "array", "length": len(value), "items": item_schemas, "path": path}
            elif isinstance(value, dict):
                schema = {"type": "object", "path": path, "properties": {}}
                for key, val in value.items():
                    new_path = f"{path}.{key}" if path else key
                    schema["properties"][key] = analyze_value(val, new_path)
                return schema
            else:
                return {"type": str(type(value).__name__), "path": path}
        
        # Generate schema for the issue
        schema = analyze_value(issue_data)
        
        # Add metadata
        schema_with_meta = {
            "metadata": {
                "generated_from": "JIRA API Response",
                "issue_key": issue_data.get("key", "unknown"),
                "analysis_timestamp": logger.bind()._core.min_level,  # Using logger timestamp
                "total_fields": len(issue_data.get("fields", {})),
                "top_level_keys": list(issue_data.keys())
            },
            "schema": schema
        }
        
        # Save to file if output path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(schema_with_meta, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Schema saved to: {output_path}")
        
        return schema_with_meta

    def generate_schema_from_sample_issues(self, project_key: str, max_issues: int = 5) -> dict[str, Any]:
        """
        Generate schema by analyzing multiple sample issues from a project.
        
        Args:
            project_key: JIRA project key
            max_issues: Maximum number of issues to analyze
            
        Returns:
            Combined schema from multiple issues
        """
        logger.info(f"Generating schema from sample issues in project: {project_key}")
        
        # Fetch sample issues
        jql = f"project = {project_key} ORDER BY created DESC"
        issues = self.jira.jql(jql, limit=max_issues, expand="*")['issues']
        
        if not issues:
            logger.warning(f"No issues found in project {project_key}")
            return {}
        
        # Analyze each issue and combine schemas
        combined_fields = {}
        top_level_keys = set()
        
        for i, issue_data in enumerate(issues):
            logger.info(f"Analyzing issue {i+1}/{len(issues)}: {issue_data.get('key', 'unknown')}")
            
            # Track top-level keys
            top_level_keys.update(issue_data.keys())
            
            # Analyze fields structure
            fields = issue_data.get('fields', {})
            for field_name, field_value in fields.items():
                if field_name not in combined_fields:
                    combined_fields[field_name] = {
                        "seen_in_issues": [],
                        "types_seen": set(),
                        "examples": []
                    }
                
                combined_fields[field_name]["seen_in_issues"].append(issue_data.get('key', 'unknown'))
                combined_fields[field_name]["types_seen"].add(type(field_value).__name__)
                
                # Store a few examples
                if len(combined_fields[field_name]["examples"]) < 3:
                    if field_value is not None and field_value != "":
                        example = str(field_value)[:100] + "..." if len(str(field_value)) > 100 else str(field_value)
                        combined_fields[field_name]["examples"].append(example)
        
        # Convert sets to lists for JSON serialization
        for field_info in combined_fields.values():
            field_info["types_seen"] = list(field_info["types_seen"])
        
        schema_summary = {
            "metadata": {
                "project": project_key,
                "issues_analyzed": len(issues),
                "analysis_timestamp": "now",  # You could use datetime here
                "top_level_keys": list(top_level_keys)
            },
            "field_analysis": combined_fields,
            "required_fields_candidates": [
                field for field, info in combined_fields.items() 
                if len(info["seen_in_issues"]) == len(issues) and None not in [ex for ex in info["examples"]]
            ]
        }
        
        # Save schema
        schema_file = self.output_dir / f"{project_key}_schema_analysis.json"
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema_summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Schema analysis saved to: {schema_file}")
        return schema_summary
