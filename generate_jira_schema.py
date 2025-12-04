#!/usr/bin/env python3
"""
Schema Generator for JIRA Issues

This script analyzes actual JIRA issue data to generate schemas
that can help fix Pydantic models.
"""

import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from atlassian_migration_tool.extractors.jira_extractor import JiraExtractor
from atlassian_migration_tool.utils.config_loader import load_config


def main():
    """Generate schema from JIRA data."""
    try:
        # Load configuration
        config = load_config()
        jira_config = config['atlassian']['jira']
        
        # Initialize extractor
        extractor = JiraExtractor(jira_config)
        
        # Option 1: Generate schema from existing saved issue
        print("Option 1: Generate schema from existing saved issue...")
        issue_file = Path("data/extracted/NSTTCO/issues/NSTTCO-2005/issue.json")
        
        if issue_file.exists():
            import json
            with open(issue_file, 'r', encoding='utf-8') as f:
                issue_data = json.load(f)
            
            schema = extractor.generate_issue_schema(
                issue_data, 
                "data/extracted/NSTTCO/NSTTCO-2005_schema.json"
            )
            print(f"✓ Schema generated from saved issue: NSTTCO-2005")
        
        # Option 2: Generate comprehensive schema from multiple live issues
        print("\nOption 2: Generate schema from multiple live issues...")
        project_key = "NSTTCO"  # Change this to your project
        
        try:
            schema_analysis = extractor.generate_schema_from_sample_issues(project_key, max_issues=5)
            print(f"✓ Comprehensive schema generated for project: {project_key}")
            
            # Print some key findings
            print(f"\nKey findings:")
            print(f"- Total unique fields found: {len(schema_analysis.get('field_analysis', {}))}")
            print(f"- Required field candidates: {len(schema_analysis.get('required_fields_candidates', []))}")
            
            required_fields = schema_analysis.get('required_fields_candidates', [])
            if required_fields:
                print("\nFields that appear in ALL analyzed issues (potential required fields):")
                for field in required_fields[:10]:  # Show first 10
                    print(f"  - {field}")
            
        except Exception as e:
            print(f"✗ Failed to generate live schema: {e}")
            print("This might be due to network/authentication issues.")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have:")
        print("1. Valid JIRA configuration in config/config.yaml")
        print("2. Network access to your JIRA instance")
        print("3. Valid authentication credentials")


if __name__ == "__main__":
    main()