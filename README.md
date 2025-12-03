# Jira Migration Tool

A Python tool for migrating content from Jira to open-source alternatives (OpenProject, GitLab).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Features

### Supported Migrations

- **Jira to OpenProject**: Migrate issues, projects, and work packages
- **Jira to GitLab**: Export issues to GitLab issues/wikis

### Key Capabilities

- **Web-based GUI**: Modern browser interface that works in WSL and native environments
- **Comprehensive Extraction**: Issues, attachments, comments, and metadata
- **Independent Operations**: Configure, Test, Extract, Transform, and Upload separately
- **Real-time Progress**: Server-Sent Events for live progress updates
- **Flexible Configuration**: YAML-based configuration with environment variable support
- **CLI Interface**: Full command-line support for automation
- **Dry Run Mode**: Test migrations without making changes

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
JIRA_API_TOKEN=your_jira_token
OPENPROJECT_API_KEY=your_openproject_key
GITLAB_TOKEN=your_gitlab_token
```

## Usage

### Web GUI (Recommended)

Launch the web-based GUI:

```bash
# Using the command
atlassian-migrate web

# Or directly
atlassian-migrate-gui
```

This will:
1. Start a local web server on http://127.0.0.1:8080
2. Automatically open your default browser
3. **WSL Support**: In WSL, the browser opens in Windows automatically

#### GUI Features

- **Dashboard**: System status overview and quick actions
- **Configuration**: Visual editor for Jira and target system settings
- **Operations**: Three independent panels for Extract, Transform, and Upload
  - Each operation runs independently with real-time progress
  - Cancel running operations at any time
  - View detailed logs for each operation
- **Logs**: Real-time log viewer with filtering and live streaming

### Command Line Interface

```bash
# Test Jira connection
atlassian-migrate test-connection --source jira

# List Jira projects
atlassian-migrate list

# Extract Jira projects
atlassian-migrate extract --projects PROJECT1 PROJECT2

# Transform extracted data
atlassian-migrate transform --input data/extracted --output data/transformed

# Upload to target system
atlassian-migrate upload --target openproject

# Get help
atlassian-migrate --help
```

### CLI Commands

#### Extract Content

```bash
# Extract specific projects
atlassian-migrate extract --projects PROJECT1 PROJECT2

# Extract with custom output directory
atlassian-migrate extract --projects PROJECT1 --output ./my-export

# Dry run (show what would be extracted)
atlassian-migrate extract --projects PROJECT1 --dry-run
```

#### Transform Content

```bash
# Transform for OpenProject
atlassian-migrate transform --input data/extracted --output data/transformed
```

#### Upload Content

```bash
# Upload to OpenProject
atlassian-migrate upload --target openproject

# Upload to GitLab
atlassian-migrate upload --target gitlab

# Dry run
atlassian-migrate upload --target openproject --dry-run
```

## Configuration

See `config/config.example.yaml` for complete configuration options. Key sections:

- **atlassian.jira**: Jira connection settings
- **targets**: OpenProject and GitLab settings
- **migration**: Migration behavior and options
- **transformation**: Content transformation rules
- **logging**: Logging configuration

## API Authentication

### Jira

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create an API token
3. Add to `.env` file as `JIRA_API_TOKEN`

### OpenProject / GitLab

Generate API tokens/keys in respective admin panels and add to `.env` file.

## WSL Compatibility

The web GUI is designed to work seamlessly in Windows Subsystem for Linux (WSL):

- **Browser Launch**: Uses `cmd.exe` to open the Windows default browser
- **No X Server Required**: Unlike Tkinter, no display server setup needed
- **Works with WSL1 and WSL2**: Compatible with all WSL versions

## API Documentation

When the web server is running, API documentation is available at:

- Swagger UI: http://127.0.0.1:8080/docs
- ReDoc: http://127.0.0.1:8080/redoc

## Troubleshooting

### Web GUI won't start

```bash
# Check if port 8080 is in use
lsof -i :8080

# Use a different port
atlassian-migrate web --port 3000
```

### Connection errors

Enable debug logging in `config/config.yaml`:
```yaml
logging:
  level: "DEBUG"
```

View logs in `data/logs/migration.log` or the Logs page in the web GUI.

## Project Status

**Version**: 0.1.0 (Alpha)

### Completed
- Web-based GUI with real-time progress
- CLI interface
- Configuration system
- Jira extraction
- WSL compatibility

### In Progress
- Content transformers
- Target uploaders (OpenProject, GitLab)

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
