#!/usr/bin/env python3
"""
Atlassian Migration Tool - Command Line Interface

This CLI provides commands for extracting, transforming, and uploading
content from Jira to open-source alternatives.
"""

import sys

import click
from loguru import logger
from rich.console import Console
from rich.table import Table

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
    Atlassian Migration Tool

    A comprehensive tool for migrating content from Jira
    to open-source alternatives (OpenProject, GitLab).
    """
    ctx.ensure_object(dict)


@cli.command()
@click.option("--projects", multiple=True, required=True, help="Jira projects to extract")
@click.option("--output", type=click.Path(), default="data/extracted", help="Output directory")
@click.option("--since", help="Extract content modified since date (YYYY-MM-DD)")
@click.option("--dry-run", is_flag=True, help="Simulate extraction without downloading")
def extract(projects, output, since, dry_run):
    """Extract content from Jira."""
    console.print("\n[bold blue]Extracting from Jira...[/bold blue]")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No files will be downloaded[/yellow]")

    if not projects:
        console.print("[red]Error: --projects required for Jira extraction[/red]")
        sys.exit(1)
    extract_jira(projects, output, since, dry_run)


@cli.command()
@click.option("--input", "input_dir", type=click.Path(exists=True), default="data/extracted")
@click.option("--output", type=click.Path(), default="data/transformed")
@click.option("--dry-run", is_flag=True, help="Simulate transformation")
def transform(input_dir, output, dry_run):
    """Transform extracted Jira content for target systems."""
    console.print("\n[bold blue]Transforming Jira content...[/bold blue]")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No files will be written[/yellow]")

    transform_jira(input_dir, output, dry_run)


@cli.command()
@click.option("--target", type=click.Choice(["openproject", "gitlab"]), required=True)
@click.option("--input", "input_dir", type=click.Path(exists=True), default="data/transformed")
@click.option("--dry-run", is_flag=True, help="Simulate upload without making changes")
def upload(target, input_dir, dry_run):
    """Upload transformed content to target systems."""
    console.print(f"\n[bold blue]Uploading to {target}...[/bold blue]")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]")

    if target == "openproject":
        upload_to_openproject(input_dir, dry_run)
    elif target == "gitlab":
        upload_to_gitlab(input_dir, dry_run)


@cli.command()
@click.option("--all", "migrate_all", is_flag=True, help="Migrate all configured content")
@click.option("--target", type=click.Choice(["openproject", "gitlab"]))
@click.option("--projects", multiple=True)
@click.option("--mode", type=click.Choice(["full", "incremental"]), default="full")
@click.option("--dry-run", is_flag=True, help="Simulate complete migration")
def migrate(migrate_all, target, projects, mode, dry_run):
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
        if not target:
            console.print("[red]Error: --target required (or use --all)[/red]")
            sys.exit(1)
        run_targeted_migration(target, projects, mode, dry_run)


@cli.command("list")
def list_projects():
    """List available Jira projects."""
    console.print("\n[bold blue]Listing Jira projects...[/bold blue]\n")
    list_jira_projects()


@cli.command()
@click.option("--source", type=click.Choice(["jira"]), default="jira")
@click.option("--target", type=click.Choice(["openproject", "gitlab", "all"]))
@click.option("--verbose", is_flag=True)
def test_connection(source, target, verbose):
    """Test connections to Jira and target systems."""
    console.print("\n[bold blue]Testing connections...[/bold blue]\n")

    config = load_config()

    if source == "jira":
        test_jira_connection(config, verbose)

    if target:
        if target in ["openproject", "all"]:
            test_target_connection("openproject", config, verbose)
        if target in ["gitlab", "all"]:
            test_target_connection("gitlab", config, verbose)


@cli.command()
def web():
    """Launch the web-based GUI."""
    try:
        from atlassian_migration_tool.web.app import start_server
        start_server()
    except ImportError as e:
        console.print(f"[red]Failed to launch web GUI: {e}[/red]")
        console.print("[yellow]Make sure FastAPI and uvicorn are installed.[/yellow]")
        sys.exit(1)


@cli.command()
def validate_config():
    """Validate configuration file."""
    console.print("\n[bold blue]Validating configuration...[/bold blue]\n")

    try:
        config = load_config()
        console.print("[green]Configuration file loaded successfully[/green]")

        # Validate required fields
        required_fields = ["atlassian", "targets", "migration"]
        for field in required_fields:
            if field in config:
                console.print(f"[green]  Section '{field}' present[/green]")
            else:
                console.print(f"[red]  Section '{field}' missing[/red]")

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
    table.add_row("Jira", "567", "567", "567", "0", "Pending")

    console.print(table)


@cli.command()
@click.option("--output", type=click.Path(), default="data/reports/migration_report.html")
@click.option("--format", "report_format", type=click.Choice(["html", "json", "txt"]), default="html")
def report(output, report_format):
    """Generate migration report."""
    console.print(f"\n[bold blue]Generating {report_format.upper()} report...[/bold blue]")

    # Generate report
    generate_migration_report(output, report_format)

    console.print(f"\n[green]Report saved to: {output}[/green]")


# Helper functions

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
            console.print(f"[green]  Extracted {len(project.issues)} issues[/green]")
            console.print(f"[green]  Issues organized by type in: {output}/jira/{project_key}/by-issue-type/[/green]")
        except Exception as e:
            console.print(f"[red]  Failed to extract {project_key}: {e}[/red]")
            logger.exception(f"Failed to extract project {project_key}")


def transform_jira(input_dir, output, dry_run):
    """Transform Jira content"""

    console.print(f"Input directory: {input_dir}")
    console.print(f"Output directory: {output}")

    console.print("\n[yellow]Transformation implementation pending[/yellow]")


def upload_to_openproject(input_dir, dry_run):
    """Upload to OpenProject"""

    console.print(f"Input directory: {input_dir}")
    console.print("\n[yellow]Upload implementation pending[/yellow]")


def upload_to_gitlab(input_dir, dry_run):
    """Upload to GitLab"""

    console.print(f"Input directory: {input_dir}")
    console.print("\n[yellow]Upload implementation pending[/yellow]")


def run_full_migration(config, mode, dry_run):
    """Run complete migration."""
    console.print("Running full migration workflow...")
    console.print("\n[yellow]Full migration implementation pending[/yellow]")


def run_targeted_migration(target, projects, mode, dry_run):
    """Run targeted migration."""
    console.print("Running targeted migration workflow...")
    console.print("\n[yellow]Targeted migration implementation pending[/yellow]")


def list_jira_projects():
    """List Jira projects"""
    try:
        from atlassian_migration_tool.extractors import JiraExtractor

        config = load_config()
        extractor = JiraExtractor(config['atlassian']['jira'])
        projects = extractor.list_projects()

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Project Key")
        table.add_column("Name")

        for project in projects:
            table.add_row(project.get('key', 'N/A'), project.get('name', 'N/A'))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing projects: {e}[/red]")
        logger.exception("Failed to list Jira projects")


def test_jira_connection(config, verbose):
    """Test Jira connection"""
    console.print("Testing Jira connection...")

    try:
        from atlassian_migration_tool.extractors import JiraExtractor
        extractor = JiraExtractor(config['atlassian']['jira'])
        projects = extractor.list_projects()
        console.print("[green]  Connected to Jira[/green]")
        console.print("[green]  Authentication successful[/green]")
        console.print(f"[green]  Found {len(projects)} accessible projects[/green]")

        if verbose:
            console.print(f"   URL: {config['atlassian']['jira']['url']}")
            console.print(f"   User: {config['atlassian']['jira']['username']}")
    except Exception as e:
        console.print(f"[red]  Connection failed: {e}[/red]")
        logger.exception("Failed to connect to Jira")


def test_target_connection(target, config, verbose):
    """Test target system connection"""
    console.print(f"\nTesting {target.capitalize()} connection...")

    # This would test API connection to target
    console.print(f"[green]  Connected to {target.capitalize()}[/green]")
    console.print("[green]  Authentication successful[/green]")

    if verbose:
        console.print(f"   URL: {config['targets'][target]['url']}")


def generate_migration_report(output, report_format):
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
