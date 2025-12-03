#!/usr/bin/env python3
"""
Atlassian Migration Tool - Main Entry Point

This module serves as the entry point when running the package as a module:
    python -m atlassian_migration

It imports and executes the CLI interface.
"""

import sys

from atlassian_migration_tool.cli import main

if __name__ == "__main__":
    sys.exit(main())
