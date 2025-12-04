# JIRA Schema Analysis Summary

## Overview
This document summarizes the JIRA API response structure based on actual data analysis from the NSTTCO project.

## Key Findings

### Top-Level Structure
The JIRA API response has these top-level keys:
- `expand`: String with expansion info
- `id`: String with issue ID (e.g., "2522938")
- `self`: URL to the issue
- `key`: Issue key (e.g., "NSTTCO-2005") 
- `fields`: Object containing all the issue fields
- `renderedFields`: Object with rendered versions of fields

### Critical Fields for JiraIssue Model

Based on the schema analysis, here are the correct paths for required fields:

#### Required Fields (currently causing validation errors):
1. **id**: Available at `issue_data['id']` (top level) ✅
2. **created**: Available at `fields['created']` ⚠️  (was looking at top level)
3. **updated**: Available at `fields['updated']` ⚠️  (was looking at top level)
4. **reporter**: Available at `fields['reporter']['displayName']` ✅
5. **projectKey**: Available at `fields['project']['key']` ✅

#### Optional Fields:
- **priority**: `fields['priority']['name']` (can be null)
- **assignee**: `fields['assignee']['displayName']` (can be null)
- **parent_key**: `fields['parent']['key']` (can be null)
- **labels**: `fields['labels']` (array)
- **attachments**: `fields['attachment']` (array)
- **comments**: `fields['comment']['comments']` (array)

### Field Analysis Results
- **Total unique fields found**: 213
- **Required field candidates**: 211 (fields present in all analyzed issues)
- **Most fields are custom fields** (customfield_*)

## Schema Files Generated
1. `data/extracted/NSTTCO/NSTTCO-2005_schema.json` - Detailed schema of single issue
2. `data/extracted/jira/NSTTCO_schema_analysis.json` - Analysis of 5 issues

## Fixes Applied
1. Fixed `created` field access: `issue_data['created']` → `fields.get('created', '')`
2. Fixed `updated` field access: `issue_data['updated']` → `fields.get('updated', '')`
3. Added proper error handling with schema generation on failures
4. Added comprehensive attachment and comment processing

## Schema Generation Tools Available
1. `generate_jira_schema.py` - Standalone schema generator
2. `JiraExtractor.generate_issue_schema()` - Single issue analysis
3. `JiraExtractor.generate_schema_from_sample_issues()` - Multi-issue analysis
4. Automatic debug schema generation on processing errors

## Usage
To generate schema for any JIRA project:
```bash
poetry run python generate_jira_schema.py
```

To analyze a specific issue:
```python
extractor = JiraExtractor(config)
schema = extractor.generate_issue_schema(issue_data, "output_file.json")
```