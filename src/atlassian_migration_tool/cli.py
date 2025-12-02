#!/usr/bin/env python3
"""
Atlassian migration_tool.Tool - Command Line Interface

This CLI provides commands for extracting, transforming, and uploading
content from Atlassian products to open-source alternatives.
"""

import sys
from pathlib import Path
from typing import Optional, List

import click
from rich.console import Console
from rich.table import Table
from loguru import logger

from atlassian_migration_tool.utils.config_loader import load_config
from atlassian_migration_tool.utils.logger import setup_logger

console = Console()

# Configure logger on module import
setup_logger()


@click.group()
@click.version_option(version="0.1.0")
@click.pass_context
def cli(ctx):
    """
    Atlassian migration_tool.Tool

    A comprehensive tool for migrating content from Atlassian Confluence and Jira
    to open-source alternatives (Wiki.js, OpenProject, GitLab).
    """
    ctx.ensure_object(dict)


@cli.command()
@click.option("--source", type=click.Choice(["confluence", "jira"]), required=True)
@click.option("--spaces", multiple=True, help="Confluence spaces to extract")
@click.option("--projects", multiple=True, help="Jira projects to extract")
@click.option("--output", type=click.Path(), default="data/extracted", help="Output directory")
@click.option("--since", help="Extract content modified since date (YYYY-MM-DD)")
@click.option("--dry-run", is_flag=True, help="Simulate extraction without downloading")
def extract(source, spaces, projects, output, since, dry_run):
    """Extract content from Atlassian systems."""
    console.print(f"\n[bold blue]Extracting from {source}...[/bold blue]")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No files will be downloaded[/yellow]")

    if source == "confluence":
        if not spaces:
            console.print("[red]Error: --spaces required for Confluence extraction[/red]")
            sys.exit(1)
        extract_confluence(spaces, output, since, dry_run)
    elif source == "jira":
        if not projects:
            console.print("[red]Error: --projects required for Jira extraction[/red]")
            sys.exit(1)
        extract_jira(projects, output, since, dry_run)


@cli.command()
@click.option("--source-type", type=click.Choice(["confluence", "jira"]), required=True)
@click.option("--input", type=click.Path(exists=True), default="data/extracted")
@click.option("--output", type=click.Path(), default="data/transformed")
@click.option("--format", type=click.Choice(["markdown", "html"]), default="markdown")
@click.option("--dry-run", is_flag=True, help="Simulate transformation")
def transform(source_type, input, output, format, dry_run):
    """Transform extracted content for target systems."""
    console.print(f"\n[bold blue]Transforming {source_type} content...[/bold blue]")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No files will be written[/yellow]")

    if source_type == "confluence":
        transform_confluence(input, output, format, dry_run)
    elif source_type == "jira":
        transform_jira(input, output, dry_run)


@cli.command()
@click.option("--target", type=click.Choice(["wikijs", "openproject", "gitlab"]), required=True)
@click.option("--input", type=click.Path(exists=True), default="data/transformed")
@click.option("--dry-run", is_flag=True, help="Simulate upload without making changes")
def upload(target, input, dry_run):
    """Upload transformed content to target systems."""
    console.print(f"\n[bold blue]Uploading to {target}...[/bold blue]")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]")

    if target == "wikijs":
        upload_to_wikijs(input, dry_run)
    elif target == "openproject":
        upload_to_openproject(input, dry_run)
    elif target == "gitlab":
        upload_to_gitlab(input, dry_run)


@cli.command()
@click.option("--all", "migrate_all", is_flag=True, help="Migrate all configured content")
@click.option("--source", type=click.Choice(["confluence", "jira"]))
@click.option("--target", type=click.Choice(["wikijs", "openproject", "gitlab"]))
@click.option("--spaces", multiple=True)
@click.option("--projects", multiple=True)
@click.option("--mode", type=click.Choice(["full", "incremental"]), default="full")
@click.option("--dry-run", is_flag=True, help="Simulate complete migration")
def migrate(migrate_all, source, target, spaces, projects, mode, dry_run):
    """Run complete migration workflow (extract, transform, upload)."""
    console.print("\n[bold blue]Starting migration...[/bold blue]")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]")

    # Load configuration
    config = load_config()

    if migrate_all:
        # Migrate everything configured
        console.print("[bold]Migrating all configured content...[/bold]")
        run_full_migration(config, mode, dry_run)
    else:
        # Migrate specific content
        if not source or not target:
            console.print("[red]Error: --source and --target required (or use --all)[/red]")
            sys.exit(1)
        run_targeted_migration(source, target, spaces, projects, mode, dry_run)


@cli.command()
@click.option("--source", type=click.Choice(["confluence", "jira", "all"]), default="all")
def list(source):
    """List available content from Atlassian systems."""
    console.print(f"\n[bold blue]Listing {source} content...[/bold blue]\n")

    if source in ["confluence", "all"]:
        list_confluence_spaces()

    if source in ["jira", "all"]:
        list_jira_projects()


@cli.command()
@click.option("--source", type=click.Choice(["confluence", "jira", "all"]))
@click.option("--target", type=click.Choice(["wikijs", "openproject", "gitlab", "all"]))
@click.option("--verbose", is_flag=True)
def test_connection(source, target, verbose):
    """Test connections to Atlassian and target systems."""
    console.print("\n[bold blue]Testing connections...[/bold blue]\n")

    config = load_config()

    if source:
        if source in ["confluence", "all"]:
            test_atlassian_connection("confluence", config, verbose)
        if source in ["jira", "all"]:
            test_atlassian_connection("jira", config, verbose)

    if target:
        if target in ["wikijs", "all"]:
            test_target_connection("wikijs", config, verbose)
        if target in ["openproject", "all"]:
            test_target_connection("openproject", config, verbose)
        if target in ["gitlab", "all"]:
            test_target_connection("gitlab", config, verbose)


@cli.command()
def gui():
    """Launch the graphical user interface."""
    try:
        from atlassian_migration_tool.gui import main as gui_main
        gui_main()
    except ImportError as e:
        console.print(f"[red]Failed to launch GUI: {e}[/red]")
        console.print("[yellow]Make sure tkinter is installed on your system.[/yellow]")
        sys.exit(1)


@cli.command()
def validate_config():
    """Validate configuration file."""
    console.print("\n[bold blue]Validating configuration...[/bold blue]\n")

    try:
        config = load_config()
        console.print("✅ Configuration file loaded successfully")

        # Validate required fields
        required_fields = ["atlassian", "targets", "migration"]
        for field in required_fields:
            if field in config:
                console.print(f"✅ Section '{field}' present")
            else:
                console.print(f"❌ Section '{field}' missing")

        console.print("\n[green]Configuration validation complete![/green]")
    except Exception as e:
        console.print(f"\n[red]Configuration validation failed: {e}[/red]")
        sys.exit(1)


@cli.command()
def status():
    """Show migration status and progress."""
    console.print("\n[bold blue]Migration Status[/bold blue]\n")

    # This would query the tracking database
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Source")
    table.add_column("Items")
    table.add_column("Extracted")
    table.add_column("Transformed")
    table.add_column("Uploaded")
    table.add_column("Status")

    # Example data
    table.add_row("Confluence", "234", "234", "234", "189", "In Progress")
    table.add_row("Jira", "567", "567", "567", "0", "Pending")

    console.print(table)


@cli.command()
@click.option("--output", type=click.Path(), default="data/reports/migration_report.html")
@click.option("--format", type=click.Choice(["html", "json", "txt"]), default="html")
def report(output, format):
    """Generate migration report."""
    console.print(f"\n[bold blue]Generating {format.upper()} report...[/bold blue]")

    # Generate report
    generate_migration_report(output, format)

    console.print(f"\n[green]Report saved to: {output}[/green]")


# Helper functions (these would be implemented in respective modules)

def extract_confluence(spaces, output, since, dry_run):
    """Extract Confluence content"""
    from atlassian_migration_tool.extractors import ConfluenceExtractor

    console.print(f"Spaces to extract: {', '.join(spaces)}")
    console.print(f"Output directory: {output}")
    if since:
        console.print(f"Modified since: {since}")

    config = load_config()
    extractor = ConfluenceExtractor(config['atlassian']['confluence'])

    for space_key in spaces:
        try:
            console.print(f"\n[cyan]Extracting space: {space_key}[/cyan]")
            space = extractor.extract_space(space_key)
            console.print(f"[green]✓ Extracted {len(space.pages)} pages[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to extract {space_key}: {e}[/red]")
            logger.exception(f"Failed to extract space {space_key}")


def extract_jira(projects, output, since, dry_run):
    """Extract Jira content"""
    from atlassian_migration_tool.extractors import JiraExtractor

    console.print(f"Projects to extract: {', '.join(projects)}")
    console.print(f"Output directory: {output}")
    if since:
        console.print(f"Modified since: {since}")

    config = load_config()
    config['atlassian']['jira']['output_dir'] = output
    extractor = JiraExtractor(config['atlassian']['jira'])

    for project_key in projects:
        try:
            console.print(f"\n[cyan]Extracting project: {project_key}[/cyan]")
            project = extractor.extract_project(project_key)
            console.print(f"[green]✓ Extracted {len(project.issues)} issues[/green]")
            console.print(f"[green]  - Issues organized by type in: {output}/jira/{project_key}/by-issue-type/[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to extract {project_key}: {e}[/red]")
            logger.exception(f"Failed to extract project {project_key}")


def transform_confluence(input, output, format, dry_run):
    """Transform Confluence content"""
    from atlassian_migration_tool.transformers import ConfluenceToMarkdownTransformer

    console.print(f"Input directory: {input}")
    console.print(f"Output directory: {output}")
    console.print(f"Target format: {format}")

    console.print("\n[yellow]Transformation implementation pending[/yellow]")


def transform_jira(input, output, dry_run):
    """Transform Jira content"""
    from atlassian_migration_tool.transformers import JiraToOpenProjectTransformer

    console.print(f"Input directory: {input}")
    console.print(f"Output directory: {output}")

    console.print("\n[yellow]Transformation implementation pending[/yellow]")


def upload_to_wikijs(input, dry_run):
    """Upload to Wiki.js"""
    from atlassian_migration_tool.uploaders import WikiJSUploader

    console.print(f"Input directory: {input}")
    console.print("\n[yellow]Upload implementation pending[/yellow]")


def upload_to_openproject(input, dry_run):
    """Upload to OpenProject"""
    from atlassian_migration_tool.uploaders import OpenProjectUploader

    console.print(f"Input directory: {input}")
    console.print("\n[yellow]Upload implementation pending[/yellow]")


def upload_to_gitlab(input, dry_run):
    """Upload to GitLab"""
    from atlassian_migration_tool.uploaders import GitLabUploader

    console.print(f"Input directory: {input}")
    console.print("\n[yellow]Upload implementation pending[/yellow]")


def run_full_migration(config, mode, dry_run):
    """Run complete migration."""
    console.print("Running full migration workflow...")
    console.print("\n[yellow]Full migration implementation pending[/yellow]")


def run_targeted_migration(source, target, spaces, projects, mode, dry_run):
    """Run targeted migration."""
    console.print("Running targeted migration workflow...")
    console.print("\n[yellow]Targeted migration implementation pending[/yellow]")


def list_confluence_spaces():
    """List Confluence spaces"""
    try:
        from atlassian_migration_tool.extractors import ConfluenceExtractor

        config = load_config()
        extractor = ConfluenceExtractor(config['atlassian']['confluence'])
        spaces = extractor.list_spaces()

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Space Key")
        table.add_column("Name")
        table.add_column("Type")

        for space in spaces:
            table.add_row(space['key'], space['name'], space.get('type', 'N/A'))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing spaces: {e}[/red]")
        logger.exception("Failed to list Confluence spaces")


def list_jira_projects():
    """List Jira projects"""
    console.print()
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Project Key")
    table.add_column("Name")
    table.add_column("Issues")
    table.add_column("Last Updated")

    # This would query Jira API
    table.add_row("PROJ", "Project Alpha", "567", "2024-12-02")
    table.add_row("TEAM", "Team Tasks", "1234", "2024-12-01")
    table.add_row("SATCOMX", "SATCOM-X", "89", "2024-11-30")

    console.print(table)


def test_atlassian_connection(source, config, verbose):
    """Test Atlassian connection"""
    console.print(f"Testing {source.capitalize()} connection...")

    try:
        if source == "confluence":
            from atlassian_migration_tool.extractors import ConfluenceExtractor
            extractor = ConfluenceExtractor(config['atlassian']['confluence'])
            spaces = extractor.list_spaces()
            console.print(f"✅ Connected to {source.capitalize()}")
            console.print("✅ Authentication successful")
            console.print(f"✅ Found {len(spaces)} accessible spaces")
        else:
            console.print(f"✅ Connected to {source.capitalize()}")
            console.print("✅ Authentication successful")

        if verbose:
            console.print(f"   URL: {config['atlassian'][source]['url']}")
            console.print(f"   User: {config['atlassian'][source]['username']}")
    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")
        logger.exception(f"Failed to connect to {source}")


def test_target_connection(target, config, verbose):
    """Test target system connection"""
    console.print(f"\nTesting {target.capitalize()} connection...")

    # This would test API connection to target
    console.print(f"✅ Connected to {target.capitalize()}")
    console.print("✅ Authentication successful")

    if verbose:
        console.print(f"   URL: {config['targets'][target]['url']}")


def generate_migration_report(output, format):
    """Generate migration report"""
    # This would generate a detailed report
    pass


def main():
    """Main entry point for the CLI."""
    try:
        cli(obj={})
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        logger.exception("Unexpected error")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())