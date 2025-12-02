# Atlassian Migration Tool

A comprehensive Python tool for migrating content from Atlassian products (Confluence and Jira) to open-source alternatives (Wiki.js, OpenProject, and GitLab).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Features

### ✅ Supported Migrations

- **Confluence → Wiki.js**: Migrate documentation, pages, and spaces
- **Jira → OpenProject**: Migrate issues, projects, and work packages
- **Content → GitLab**: Export documentation to GitLab wikis and repositories

### 🎯 Key Capabilities

- **Comprehensive Extraction**: Pages, issues, attachments, comments, labels, and metadata
- **Smart Transformation**: Automatic content format conversion (HTML → Markdown)
- **Flexible Configuration**: YAML-based configuration with environment variable support
- **GUI & CLI Interfaces**: Choose between graphical and command-line interfaces
- **Progress Tracking**: Real-time status monitoring and detailed logging
- **Dry Run Mode**: Test migrations without making changes
- **Incremental Sync**: Support for incremental updates (future feature)

## Quick Start

### Installation

#### Prerequisites

- Python 3.10 or higher
- Poetry (for dependency management)
- Git

#### Install with Poetry

```bash
# Clone the repository
git clone https://github.com/ddunnock/atlassian-migration-tool.git
cd atlassian-migration-tool

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Configuration

1. **Copy the example configuration:**

```bash
cp config/config.example.yaml config/config.yaml
```

2. **Edit `config/config.yaml` with your settings**

3. **Set environment variables** (create `.env` file):

```bash
CONFLUENCE_API_TOKEN=your_confluence_token
JIRA_API_TOKEN=your_jira_token
WIKIJS_API_TOKEN=your_wikijs_token
OPENPROJECT_API_KEY=your_openproject_key
GITLAB_TOKEN=your_gitlab_token
```

## Usage

### Graphical User Interface (Recommended)

```bash
# Launch the GUI
atlassian-migrate gui
```

#### GUI Features:

- **Dashboard**: System status overview and quick actions
- **Configuration**: Visual editor for settings (no YAML editing!)
- **Migration**: Step-by-step workflow with real-time progress
- **Status**: Migration statistics and monitoring
- **Logs**: View logs and troubleshoot issues

### Command Line Interface

```bash
# Test connections
atlassian-migrate test-connection --source confluence --target wikijs

# List available content
atlassian-migrate list --source confluence

# Run complete migration
atlassian-migrate migrate --all

# Get help
atlassian-migrate --help
```

For detailed CLI usage, see the full documentation below.

## Detailed Documentation

### CLI Commands

#### List Available Content

```bash
# List Confluence spaces
atlassian-migrate list --source confluence

# List Jira projects
atlassian-migrate list --source jira
```

#### Test Connections

```bash
# Test all connections
atlassian-migrate test-connection --source all --target all
```

#### Extract Content

```bash
# Extract Confluence spaces
atlassian-migrate extract --source confluence --spaces ENGINEERING DOCS

# Extract Jira projects
atlassian-migrate extract --source jira --projects PROJECT1
```

#### Complete Migration

```bash
# Migrate everything
atlassian-migrate migrate --all

# Specific migration
atlassian-migrate migrate --source confluence --target wikijs --spaces DOCS

# Dry run
atlassian-migrate migrate --all --dry-run
```

## Configuration

See `config/config.example.yaml` for complete configuration options. Key sections:

- **atlassian**: Confluence and Jira settings
- **targets**: Wiki.js, OpenProject, and GitLab settings
- **migration**: Migration behavior and options
- **transformation**: Content transformation rules
- **logging**: Logging configuration

## API Authentication

### Atlassian (Confluence/Jira)

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create API token
3. Add to `.env` file

### Wiki.js / OpenProject / GitLab

Generate API tokens/keys in respective admin panels and add to `.env` file.

## Troubleshooting

### GUI won't launch

Install tkinter:
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# macOS
brew install python-tk
```

### Debug logging

Enable in `config/config.yaml`:
```yaml
logging:
  level: "DEBUG"
```

View logs: `data/logs/migration.log`

## Project Status

**Version**: 0.1.0 (Alpha)

### Completed
- ✅ GUI and CLI interfaces
- ✅ Configuration system
- ✅ Confluence extractor (partial)
- ✅ Data models and logging

### In Progress
- 🔄 Complete extractors
- 🔄 Content transformers
- 🔄 Target uploaders

See [ASSESSMENT.md](ASSESSMENT.md) for detailed status and roadmap.

## Development

```bash
# Install dev dependencies
poetry install --with dev

# Run tests
pytest

# Run linters
ruff check src/
mypy src/
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linters
5. Submit a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file.

## Author

David Dunnock - dunnoda@gmail.com

## Support

- **Issues**: [GitHub Issues](https://github.com/ddunnock/atlassian-migration-tool/issues)
- **Documentation**: See `docs/` directory
- **Project Assessment**: See [ASSESSMENT.md](ASSESSMENT.md)

---

**Note**: This project is in active development. Check [ASSESSMENT.md](ASSESSMENT.md) for current implementation status and timeline.
