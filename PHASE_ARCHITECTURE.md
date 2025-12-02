# Independent Phase Execution Architecture

**Date**: December 2, 2024  
**Purpose**: Document the architecture for independent execution of extraction, transformation, and upload phases

---

## Overview

The Atlassian Migration Tool is designed to support **independent execution** of three distinct phases:

1. **Extract**: Pull data from Atlassian (Confluence/Jira) → Save locally
2. **Transform**: Process extracted data → Convert to target format
3. **Upload**: Send transformed data → Push to target systems

Each phase can be executed **independently** and **at different times**, with persistent state tracking between phases.

---

## Architecture Principles

### ✅ **What This Architecture Supports**

1. **Decoupled Execution**
   - Run extract today, transform tomorrow, upload next week
   - No requirement to run all phases together
   - Each phase reads from and writes to well-defined directories

2. **Persistent State**
   - Track what's been extracted, transformed, and uploaded
   - Query status of any phase at any time
   - Resume capabilities if interrupted

3. **Multiple Workflows**
   - Extract multiple sources, transform them separately
   - Transform the same extraction multiple ways (different formats)
   - Upload to multiple targets from the same transformation

4. **Data Persistence**
   - All extracted data saved to `data/extracted/`
   - All transformed data saved to `data/transformed/`
   - State metadata saved to `data/state/migration_state.json`

### ❌ **What This Architecture Does NOT Require**

1. Running all phases in sequence
2. Completing one phase to start another (with proper manual setup)
3. Keeping processes running between phases
4. Network connectivity to both source and target simultaneously

---

## Directory Structure

```
atlassian-migration-tool/
├── data/
│   ├── extracted/           # Phase 1: Extracted content
│   │   ├── confluence/
│   │   │   ├── SPACE1/
│   │   │   │   ├── pages/
│   │   │   │   ├── attachments/
│   │   │   │   └── metadata.json
│   │   │   └── SPACE2/
│   │   └── jira/
│   │       ├── PROJECT1/
│   │       └── PROJECT2/
│   │
│   ├── transformed/         # Phase 2: Transformed content
│   │   ├── confluence/
│   │   │   ├── SPACE1/
│   │   │   │   ├── markdown/
│   │   │   │   └── metadata.json
│   │   │   └── SPACE2/
│   │   └── jira/
│   │       ├── PROJECT1/
│   │       └── PROJECT2/
│   │
│   ├── state/               # State tracking
│   │   └── migration_state.json
│   │
│   ├── logs/                # Application logs
│   │   └── migration.log
│   │
│   └── cache/               # Temporary cache
```

---

## Phase 1: Extract

### Purpose
Pull data from Atlassian systems and save it locally in its original format.

### CLI Usage

```bash
# Extract Confluence space(s)
atlassian-migrate extract \
  --source confluence \
  --spaces ENGINEERING DOCS \
  --output data/extracted

# Extract Jira project(s)
atlassian-migrate extract \
  --source jira \
  --projects PROJECT1 PROJECT2 \
  --output data/extracted

# Extract with date filter
atlassian-migrate extract \
  --source confluence \
  --spaces ENGINEERING \
  --since 2024-01-01

# Dry run to see what would be extracted
atlassian-migrate extract \
  --source confluence \
  --spaces ENGINEERING \
  --dry-run
```

### What Happens

1. **Connects** to Atlassian (Confluence or Jira)
2. **Retrieves** pages/issues, attachments, comments, metadata
3. **Saves** everything to `data/extracted/<source>/<space-or-project>/`
4. **Records state** in `data/state/migration_state.json`
5. **Logs** activity to `data/logs/migration.log`

### Output Structure

**Confluence**:
```
data/extracted/confluence/ENGINEERING/
├── space-metadata.json
├── pages/
│   ├── page-123456.json
│   ├── page-123456.html
│   └── page-789012.json
└── attachments/
    ├── diagram.png
    └── document.pdf
```

**Jira**:
```
data/extracted/jira/PROJECT1/
├── project-metadata.json
├── issues/
│   ├── PROJ-1.json
│   └── PROJ-2.json
└── attachments/
    └── screenshot.png
```

### State Tracking

```json
{
  "extractions": {
    "confluence:ENGINEERING": {
      "source_type": "confluence",
      "source_id": "ENGINEERING",
      "status": "completed",
      "extracted_at": "2024-12-02T15:30:00Z",
      "output_path": "data/extracted/confluence/ENGINEERING",
      "item_count": 234
    }
  }
}
```

---

## Phase 2: Transform

### Purpose
Convert extracted data from its original format to the target system's format.

### CLI Usage

```bash
# Transform Confluence content to Markdown
atlassian-migrate transform \
  --source-type confluence \
  --input data/extracted/confluence/ENGINEERING \
  --output data/transformed/confluence/ENGINEERING \
  --format markdown

# Transform Jira content for OpenProject
atlassian-migrate transform \
  --source-type jira \
  --input data/extracted/jira/PROJECT1 \
  --output data/transformed/jira/PROJECT1

# Dry run transformation
atlassian-migrate transform \
  --source-type confluence \
  --input data/extracted/confluence/ENGINEERING \
  --output data/transformed/confluence/ENGINEERING \
  --format markdown \
  --dry-run
```

### What Happens

1. **Reads** extracted data from `data/extracted/`
2. **Converts** content format (HTML → Markdown, Jira → OpenProject format)
3. **Rewrites** internal links to new target system URLs
4. **Processes** macros and special content
5. **Saves** transformed content to `data/transformed/`
6. **Records state** in `data/state/migration_state.json`

### Transformation Types

**Confluence → Markdown**:
- HTML to Markdown conversion
- Macro handling (code blocks, info panels, TOC)
- Link rewriting
- Attachment path updates
- Metadata extraction

**Jira → OpenProject**:
- Issue type mapping
- Status mapping
- Priority mapping
- Custom field handling
- Relationship preservation

### Output Structure

**Transformed Confluence**:
```
data/transformed/confluence/ENGINEERING/
├── transformation-metadata.json
├── pages/
│   ├── page-123456.md
│   ├── page-123456-meta.json
│   └── page-789012.md
└── attachments/
    ├── diagram.png
    └── document.pdf
```

### State Tracking

```json
{
  "transformations": {
    "confluence:ENGINEERING:markdown": {
      "source_type": "confluence",
      "source_id": "ENGINEERING",
      "target_format": "markdown",
      "status": "completed",
      "transformed_at": "2024-12-02T16:45:00Z",
      "input_path": "data/extracted/confluence/ENGINEERING",
      "output_path": "data/transformed/confluence/ENGINEERING",
      "item_count": 234
    }
  }
}
```

---

## Phase 3: Upload

### Purpose
Send transformed content to target systems (Wiki.js, OpenProject, GitLab).

### CLI Usage

```bash
# Upload to Wiki.js
atlassian-migrate upload \
  --target wikijs \
  --input data/transformed/confluence/ENGINEERING

# Upload to OpenProject
atlassian-migrate upload \
  --target openproject \
  --input data/transformed/jira/PROJECT1

# Upload to GitLab
atlassian-migrate upload \
  --target gitlab \
  --input data/transformed/confluence/ENGINEERING

# Dry run upload
atlassian-migrate upload \
  --target wikijs \
  --input data/transformed/confluence/ENGINEERING \
  --dry-run
```

### What Happens

1. **Reads** transformed data from `data/transformed/`
2. **Connects** to target system
3. **Creates** pages/issues/repositories
4. **Uploads** content and attachments
5. **Preserves** metadata (timestamps, authors, etc.)
6. **Records state** in `data/state/migration_state.json`

### Upload Strategies

**Wiki.js**:
- Create pages via GraphQL API
- Upload attachments
- Set metadata and tags
- Preserve hierarchy

**OpenProject**:
- Create work packages via REST API
- Map users and relationships
- Upload attachments
- Set custom fields

**GitLab**:
- Create/update repositories
- Commit markdown files
- Upload to wiki
- Set repository metadata

### State Tracking

```json
{
  "uploads": {
    "wikijs:confluence:ENGINEERING": {
      "target_system": "wikijs",
      "source_type": "confluence",
      "source_id": "ENGINEERING",
      "status": "completed",
      "uploaded_at": "2024-12-02T17:30:00Z",
      "input_path": "data/transformed/confluence/ENGINEERING",
      "item_count": 234
    }
  }
}
```

---

## State Management

### State File: `data/state/migration_state.json`

Complete state tracking across all phases:

```json
{
  "extractions": {
    "confluence:ENGINEERING": { "status": "completed", ... },
    "confluence:DOCS": { "status": "completed", ... },
    "jira:PROJECT1": { "status": "in_progress", ... }
  },
  "transformations": {
    "confluence:ENGINEERING:markdown": { "status": "completed", ... },
    "confluence:DOCS:markdown": { "status": "not_started", ... }
  },
  "uploads": {
    "wikijs:confluence:ENGINEERING": { "status": "completed", ... },
    "wikijs:confluence:DOCS": { "status": "not_started", ... }
  },
  "metadata": {
    "created_at": "2024-12-01T10:00:00Z",
    "last_updated": "2024-12-02T17:30:00Z"
  }
}
```

### Querying State

```bash
# View overall status
atlassian-migrate status

# View specific phase status
atlassian-migrate status --phase extraction
atlassian-migrate status --phase transformation
atlassian-migrate status --phase upload

# View status for specific source
atlassian-migrate status --source confluence --id ENGINEERING
```

### Output Example

```
Migration Status
═══════════════════════════════════════════════════════

Source: Confluence/ENGINEERING
├── Extraction:     ✅ completed (234 items, 2024-12-02 15:30)
├── Transformation: ✅ completed (234 items, 2024-12-02 16:45)
└── Upload:         ✅ completed (234 items, 2024-12-02 17:30)

Source: Confluence/DOCS
├── Extraction:     ✅ completed (156 items, 2024-12-02 15:45)
├── Transformation: ⏳ not_started
└── Upload:         ⏳ not_started

Source: Jira/PROJECT1
├── Extraction:     🔄 in_progress
├── Transformation: ⏳ not_started
└── Upload:         ⏳ not_started
```

---

## Example Workflows

### Workflow 1: Extract Everything, Transform Later

```bash
# Day 1: Extract all sources
atlassian-migrate extract --source confluence --spaces TEAM1 TEAM2 TEAM3
atlassian-migrate extract --source jira --projects PROJ1 PROJ2

# Day 2: Check what was extracted
atlassian-migrate status --phase extraction

# Day 3: Transform only TEAM1
atlassian-migrate transform \
  --source-type confluence \
  --input data/extracted/confluence/TEAM1 \
  --output data/transformed/confluence/TEAM1

# Day 4: Upload TEAM1
atlassian-migrate upload \
  --target wikijs \
  --input data/transformed/confluence/TEAM1
```

### Workflow 2: One Space at a Time

```bash
# Complete TEAM1
atlassian-migrate extract --source confluence --spaces TEAM1
atlassian-migrate transform --source-type confluence --input data/extracted/confluence/TEAM1
atlassian-migrate upload --target wikijs --input data/transformed/confluence/TEAM1

# Complete TEAM2 (weeks later)
atlassian-migrate extract --source confluence --spaces TEAM2
atlassian-migrate transform --source-type confluence --input data/extracted/confluence/TEAM2
atlassian-migrate upload --target wikijs --input data/transformed/confluence/TEAM2
```

### Workflow 3: Multiple Targets from One Extraction

```bash
# Extract once
atlassian-migrate extract --source confluence --spaces ENGINEERING

# Transform for Wiki.js
atlassian-migrate transform \
  --source-type confluence \
  --input data/extracted/confluence/ENGINEERING \
  --output data/transformed/wikijs/ENGINEERING \
  --format markdown

# Transform for GitLab
atlassian-migrate transform \
  --source-type confluence \
  --input data/extracted/confluence/ENGINEERING \
  --output data/transformed/gitlab/ENGINEERING \
  --format markdown

# Upload to both
atlassian-migrate upload --target wikijs --input data/transformed/wikijs/ENGINEERING
atlassian-migrate upload --target gitlab --input data/transformed/gitlab/ENGINEERING
```

---

## Implementation Status

### ✅ Already Implemented

1. **CLI Commands**
   - `extract` command with source, spaces, projects options
   - `transform` command with source-type, input, output options
   - `upload` command with target, input options
   - All commands support `--dry-run` for testing

2. **Directory Structure**
   - Clear separation: `data/extracted/`, `data/transformed/`
   - Organized by source type and ID

3. **Configuration**
   - YAML-based config supports all sources and targets
   - Environment variable support for secrets

### 🆕 **Just Added**

1. **State Manager** (`utils/state_manager.py`)
   - Track extraction states
   - Track transformation states
   - Track upload states
   - Query pipeline status
   - Persistent JSON storage

### 🔄 In Progress

1. **Complete Extractors**
   - Confluence extractor (partial)
   - Jira extractor (pending)

2. **Implement Transformers**
   - Confluence → Markdown
   - Jira → OpenProject format

3. **Implement Uploaders**
   - Wiki.js uploader
   - OpenProject uploader
   - GitLab uploader

### ⏳ **Needed Enhancements**

1. **Enhanced Status Command**
   - Display pipeline status per source
   - Show extracted/transformed file counts
   - Display disk space usage

2. **State Integration**
   - Integrate StateManager into extract command
   - Integrate StateManager into transform command
   - Integrate StateManager into upload command

3. **GUI Phase Support**
   - Separate tabs for each phase
   - Visual status indicators
   - Per-phase progress tracking

---

## Benefits of This Architecture

### 1. **Flexibility**
- Run phases when convenient
- No time pressure to complete all phases
- Easy to pause and resume

### 2. **Safety**
- Review extracted data before transforming
- Review transformed data before uploading
- Easy rollback - just delete and re-extract

### 3. **Debugging**
- Inspect intermediate data at each phase
- Test transformations without uploading
- Verify uploads without re-extracting

### 4. **Efficiency**
- Extract once, transform multiple times
- Transform once, upload to multiple targets
- Avoid re-downloading from Atlassian

### 5. **Scalability**
- Process large datasets in manageable chunks
- Distribute work across multiple days/weeks
- Parallel processing of independent sources

---

## Recommendations

### For Immediate Use

1. **Use the CLI for independent phases**:
   ```bash
   # Extract today
   atlassian-migrate extract --source confluence --spaces MYSPACE
   
   # Transform tomorrow
   atlassian-migrate transform --source-type confluence --input data/extracted/confluence/MYSPACE
   
   # Upload next week
   atlassian-migrate upload --target wikijs --input data/transformed/confluence/MYSPACE
   ```

2. **Check status between phases**:
   ```bash
   atlassian-migrate status
   ls -lh data/extracted/confluence/MYSPACE
   ls -lh data/transformed/confluence/MYSPACE
   ```

3. **Use dry-run for testing**:
   ```bash
   atlassian-migrate extract --source confluence --spaces MYSPACE --dry-run
   atlassian-migrate transform --source-type confluence --input data/extracted/confluence/MYSPACE --dry-run
   ```

### For Future Development

1. **Implement the extractors completely**
2. **Integrate StateManager into CLI commands**
3. **Add enhanced status command**
4. **Update GUI to support independent phases**
5. **Add data validation between phases**

---

## Conclusion

The Atlassian Migration Tool **already supports** independent phase execution through its CLI architecture. The new StateManager adds persistent tracking to make this workflow even more robust.

**You can absolutely**:
- Extract data and stop
- Transform that data days later
- Upload the transformed data weeks later
- Mix and match sources and targets

**The architecture is designed for**:
- Flexibility in timing
- Independent execution
- Clear data persistence
- Easy status tracking

---

*Document created: December 2, 2024*  
*For questions: See README.md or ASSESSMENT.md*
