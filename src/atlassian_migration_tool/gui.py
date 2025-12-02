#!/usr/bin/env python3
"""
Atlassian Migration Tool - GUI Application

A modern graphical user interface for the Atlassian Migration Tool.
Provides easy configuration management, migration workflow, and status monitoring.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from pathlib import Path
from typing import Dict, Any, Optional
import threading
import yaml
import os
from datetime import datetime

from atlassian_migration_tool.utils.config_loader import load_config
from atlassian_migration_tool.utils.logger import setup_logger
from loguru import logger


class MigrationToolGUI:
    """Main GUI application for the Atlassian Migration Tool."""

    def __init__(self, root: tk.Tk):
        """Initialize the GUI application."""
        self.root = root
        self.root.title("Jira Export Tool")
        self.root.geometry("1000x700")
        
        # Initialize config
        self.config: Optional[Dict[str, Any]] = None
        self.config_path = "config/config.yaml"
        
        # Setup logger
        setup_logger()
        
        # Configure styles
        self.setup_styles()
        
        # Create UI
        self.create_menu()
        self.create_main_layout()
        
        # Try to load config
        self.load_configuration()
    
    def setup_styles(self) -> None:
        """Configure ttk styles for the application."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'))
        style.configure('Subtitle.TLabel', font=('Helvetica', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Warning.TLabel', foreground='orange')
        
    def create_menu(self) -> None:
        """Create the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Config", command=self.open_config_file)
        file_menu.add_command(label="Reload Config", command=self.load_configuration)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Test Connections", command=self.test_all_connections)
        tools_menu.add_command(label="View Logs", command=self.view_logs)
        tools_menu.add_command(label="Clear Cache", command=self.clear_cache)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_main_layout(self) -> None:
        """Create the main application layout."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_config_tab()
        self.create_migration_tab()
        self.create_status_tab()
        self.create_logs_tab()
    
    def create_dashboard_tab(self) -> None:
        """Create the dashboard tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Dashboard")
        
        # Title
        title = ttk.Label(frame, text="Jira Export Tool", style='Title.TLabel')
        title.pack(pady=20)
        
        subtitle = ttk.Label(frame, text="Export Jira issues organized by type", style='Subtitle.TLabel')
        subtitle.pack(pady=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(frame, text="System Status", padding=20)
        status_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Configuration status
        config_frame = ttk.Frame(status_frame)
        config_frame.pack(fill='x', pady=5)
        ttk.Label(config_frame, text="Configuration:").pack(side='left')
        self.config_status_label = ttk.Label(config_frame, text="Not Loaded", style='Error.TLabel')
        self.config_status_label.pack(side='left', padx=10)
        
        # Connection status
        conn_frame = ttk.Frame(status_frame)
        conn_frame.pack(fill='x', pady=5)
        ttk.Label(conn_frame, text="Connections:").pack(side='left')
        self.conn_status_label = ttk.Label(conn_frame, text="Not Tested")
        self.conn_status_label.pack(side='left', padx=10)
        ttk.Button(conn_frame, text="Test", command=self.test_all_connections).pack(side='left', padx=5)
        
        # Quick actions
        actions_frame = ttk.LabelFrame(frame, text="Quick Actions", padding=20)
        actions_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        button_frame = ttk.Frame(actions_frame)
        button_frame.pack()
        
        ttk.Button(button_frame, text="Load Configuration", 
                  command=self.load_configuration, width=20).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(button_frame, text="Edit Configuration", 
                  command=lambda: self.notebook.select(1), width=20).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(button_frame, text="Start Migration", 
                  command=lambda: self.notebook.select(2), width=20).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(button_frame, text="View Status", 
                  command=lambda: self.notebook.select(3), width=20).grid(row=1, column=1, padx=5, pady=5)
        
        # Recent activity
        activity_frame = ttk.LabelFrame(frame, text="Recent Activity", padding=20)
        activity_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.activity_text = scrolledtext.ScrolledText(activity_frame, height=10, state='disabled')
        self.activity_text.pack(fill='both', expand=True)
        self.log_activity("Application started")
    
    def create_config_tab(self) -> None:
        """Create the configuration tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Configuration")
        
        # Config file path
        path_frame = ttk.Frame(frame)
        path_frame.pack(fill='x', padx=20, pady=10)
        ttk.Label(path_frame, text="Config File:").pack(side='left')
        self.config_path_var = tk.StringVar(value=self.config_path)
        ttk.Entry(path_frame, textvariable=self.config_path_var, width=60).pack(side='left', padx=10)
        ttk.Button(path_frame, text="Browse", command=self.browse_config_file).pack(side='left')
        ttk.Button(path_frame, text="Reload", command=self.load_configuration).pack(side='left', padx=5)
        
        # Create notebook for config sections
        config_notebook = ttk.Notebook(frame)
        config_notebook.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Atlassian configuration
        self.create_atlassian_config(config_notebook)
        
        # Target systems configuration
        self.create_targets_config(config_notebook)
        
        # Migration settings
        self.create_migration_settings(config_notebook)
        
        # Save button
        save_frame = ttk.Frame(frame)
        save_frame.pack(fill='x', padx=20, pady=10)
        ttk.Button(save_frame, text="Save Configuration", 
                  command=self.save_configuration).pack(side='right')
    
    def create_atlassian_config(self, parent: ttk.Notebook) -> None:
        """Create Atlassian configuration section."""
        frame = ttk.Frame(parent)
        parent.add(frame, text="Atlassian")
        
        # Confluence section
        confluence_frame = ttk.LabelFrame(frame, text="Confluence Configuration", padding=10)
        confluence_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.confluence_vars = {}
        fields = [
            ("URL:", "url", "https://confluence.example.com"),
            ("Username:", "username", "your-email@example.com"),
            ("API Token:", "api_token", ""),
        ]
        
        for i, (label, key, default) in enumerate(fields):
            ttk.Label(confluence_frame, text=label).grid(row=i, column=0, sticky='w', padx=5, pady=5)
            var = tk.StringVar()
            entry = ttk.Entry(confluence_frame, textvariable=var, width=50)
            if key == "api_token":
                entry.config(show="*")
            entry.grid(row=i, column=1, padx=5, pady=5)
            self.confluence_vars[key] = var
        
        # Cloud checkbox
        self.confluence_cloud_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(confluence_frame, text="Cloud Instance", 
                       variable=self.confluence_cloud_var).grid(row=len(fields), column=0, columnspan=2, pady=5)
        
        # Jira section
        jira_frame = ttk.LabelFrame(frame, text="Jira Configuration", padding=10)
        jira_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.jira_vars = {}
        for i, (label, key, default) in enumerate(fields):
            ttk.Label(jira_frame, text=label).grid(row=i, column=0, sticky='w', padx=5, pady=5)
            var = tk.StringVar()
            entry = ttk.Entry(jira_frame, textvariable=var, width=50)
            if key == "api_token":
                entry.config(show="*")
            entry.grid(row=i, column=1, padx=5, pady=5)
            self.jira_vars[key] = var
        
        self.jira_cloud_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(jira_frame, text="Cloud Instance", 
                       variable=self.jira_cloud_var).grid(row=len(fields), column=0, columnspan=2, pady=5)
    
    def create_targets_config(self, parent: ttk.Notebook) -> None:
        """Create target systems configuration section."""
        frame = ttk.Frame(parent)
        parent.add(frame, text="Targets")
        
        # Wiki.js section
        wikijs_frame = ttk.LabelFrame(frame, text="Wiki.js Configuration", padding=10)
        wikijs_frame.pack(fill='both', padx=10, pady=10)
        
        self.wikijs_vars = {}
        self.wikijs_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(wikijs_frame, text="Enable Wiki.js Upload", 
                       variable=self.wikijs_enabled_var).pack(anchor='w', pady=5)
        
        fields = [
            ("URL:", "url"),
            ("API Token:", "api_token"),
        ]
        
        for label, key in fields:
            frame_row = ttk.Frame(wikijs_frame)
            frame_row.pack(fill='x', pady=5)
            ttk.Label(frame_row, text=label, width=15).pack(side='left')
            var = tk.StringVar()
            entry = ttk.Entry(frame_row, textvariable=var, width=50)
            if key == "api_token":
                entry.config(show="*")
            entry.pack(side='left', padx=5)
            self.wikijs_vars[key] = var
        
        # OpenProject section
        openproject_frame = ttk.LabelFrame(frame, text="OpenProject Configuration", padding=10)
        openproject_frame.pack(fill='both', padx=10, pady=10)
        
        self.openproject_vars = {}
        self.openproject_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(openproject_frame, text="Enable OpenProject Upload", 
                       variable=self.openproject_enabled_var).pack(anchor='w', pady=5)
        
        for label, key in [("URL:", "url"), ("API Key:", "api_key")]:
            frame_row = ttk.Frame(openproject_frame)
            frame_row.pack(fill='x', pady=5)
            ttk.Label(frame_row, text=label, width=15).pack(side='left')
            var = tk.StringVar()
            entry = ttk.Entry(frame_row, textvariable=var, width=50)
            if key == "api_key":
                entry.config(show="*")
            entry.pack(side='left', padx=5)
            self.openproject_vars[key] = var
        
        # GitLab section
        gitlab_frame = ttk.LabelFrame(frame, text="GitLab Configuration", padding=10)
        gitlab_frame.pack(fill='both', padx=10, pady=10)
        
        self.gitlab_vars = {}
        self.gitlab_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(gitlab_frame, text="Enable GitLab Upload", 
                       variable=self.gitlab_enabled_var).pack(anchor='w', pady=5)
        
        for label, key in [("URL:", "url"), ("Token:", "token")]:
            frame_row = ttk.Frame(gitlab_frame)
            frame_row.pack(fill='x', pady=5)
            ttk.Label(frame_row, text=label, width=15).pack(side='left')
            var = tk.StringVar()
            entry = ttk.Entry(frame_row, textvariable=var, width=50)
            if key == "token":
                entry.config(show="*")
            entry.pack(side='left', padx=5)
            self.gitlab_vars[key] = var
    
    def create_migration_settings(self, parent: ttk.Notebook) -> None:
        """Create migration settings section."""
        frame = ttk.Frame(parent)
        parent.add(frame, text="Migration Settings")
        
        settings_frame = ttk.LabelFrame(frame, text="General Settings", padding=10)
        settings_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Migration mode
        mode_frame = ttk.Frame(settings_frame)
        mode_frame.pack(fill='x', pady=5)
        ttk.Label(mode_frame, text="Mode:").pack(side='left')
        self.migration_mode_var = tk.StringVar(value="full")
        ttk.Radiobutton(mode_frame, text="Full", variable=self.migration_mode_var, 
                       value="full").pack(side='left', padx=10)
        ttk.Radiobutton(mode_frame, text="Incremental", variable=self.migration_mode_var, 
                       value="incremental").pack(side='left')
        
        # Options
        self.preserve_timestamps_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Preserve Timestamps", 
                       variable=self.preserve_timestamps_var).pack(anchor='w', pady=5)
        
        self.download_attachments_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Download Attachments", 
                       variable=self.download_attachments_var).pack(anchor='w', pady=5)
        
        self.dry_run_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings_frame, text="Dry Run (Simulate Only)", 
                       variable=self.dry_run_var).pack(anchor='w', pady=5)
        
        # Workers
        workers_frame = ttk.Frame(settings_frame)
        workers_frame.pack(fill='x', pady=5)
        ttk.Label(workers_frame, text="Max Workers:").pack(side='left')
        self.max_workers_var = tk.IntVar(value=4)
        ttk.Spinbox(workers_frame, from_=1, to=16, textvariable=self.max_workers_var, 
                   width=10).pack(side='left', padx=10)
    
    def create_migration_tab(self) -> None:
        """Create the migration workflow tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Migration")
        
        # Jira Projects
        source_frame = ttk.LabelFrame(frame, text="Jira Projects to Export", padding=15)
        source_frame.pack(fill='x', padx=20, pady=10)
        
        info_label = ttk.Label(source_frame, text="Enter project keys separated by commas (e.g., NSTTC-O, PROJECT2)")
        info_label.pack(anchor='w', pady=(0, 10))
        
        jira_group = ttk.Frame(source_frame)
        jira_group.pack(fill='x', pady=5)
        
        ttk.Label(jira_group, text="Projects:", width=12).pack(side='left')
        self.jira_projects_var = tk.StringVar(value="NSTTC-O")
        ttk.Entry(jira_group, textvariable=self.jira_projects_var, 
                 width=50).pack(side='left', padx=5)
        ttk.Button(jira_group, text="List Available", 
                  command=self.list_jira_projects).pack(side='left', padx=5)
        
        # Output options
        output_frame = ttk.LabelFrame(frame, text="Export Options", padding=15)
        output_frame.pack(fill='x', padx=20, pady=10)
        
        output_info = ttk.Label(output_frame, 
                               text="Issues will be exported to: data/extracted/jira/PROJECT/by-issue-type/\n" +
                               "Organized by: Initiatives, Epics, Stories, Bugs, Tasks")
        output_info.pack(anchor='w')
        
        # Progress
        progress_frame = ttk.LabelFrame(frame, text="Export Progress", padding=10)
        progress_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.migration_status_label = ttk.Label(progress_frame, text="Ready to start")
        self.migration_status_label.pack(pady=5)
        
        self.migration_progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.migration_progress.pack(fill='x', pady=10)
        
        self.migration_log = scrolledtext.ScrolledText(progress_frame, height=15, state='disabled')
        self.migration_log.pack(fill='both', expand=True)
        
        # Control buttons
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill='x', padx=20, pady=10)
        
        self.start_migration_btn = ttk.Button(control_frame, text="Start Export", 
                                              command=self.start_migration, style='Accent.TButton')
        self.start_migration_btn.pack(side='left', padx=5)
        
        self.stop_migration_btn = ttk.Button(control_frame, text="Stop Export", 
                                             command=self.stop_migration, state='disabled')
        self.stop_migration_btn.pack(side='left', padx=5)
        
        ttk.Button(control_frame, text="Open Output Folder", 
                  command=self.open_output_folder).pack(side='right', padx=5)
    
    def create_status_tab(self) -> None:
        """Create the status monitoring tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Status")
        
        # Statistics
        stats_frame = ttk.LabelFrame(frame, text="Migration Statistics", padding=10)
        stats_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=20, state='disabled')
        self.stats_text.pack(fill='both', expand=True)
        
        # Refresh button
        ttk.Button(frame, text="Refresh Statistics", 
                  command=self.refresh_statistics).pack(pady=10)
    
    def create_logs_tab(self) -> None:
        """Create the logs viewing tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Logs")
        
        # Log viewer
        log_frame = ttk.LabelFrame(frame, text="Application Logs", padding=10)
        log_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=30, state='disabled')
        self.log_text.pack(fill='both', expand=True)
        
        # Control buttons
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(control_frame, text="Refresh Logs", 
                  command=self.refresh_logs).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Clear Display", 
                  command=self.clear_log_display).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Open Log File", 
                  command=self.open_log_file).pack(side='left', padx=5)
    
    # Configuration methods
    
    def load_configuration(self) -> None:
        """Load configuration from file."""
        try:
            config_path = self.config_path_var.get() if hasattr(self, 'config_path_var') else self.config_path
            self.config = load_config(config_path)
            
            # Update UI with config values
            self.populate_config_ui()
            
            self.config_status_label.config(text="Loaded", style='Success.TLabel')
            self.log_activity(f"Configuration loaded from {config_path}")
            messagebox.showinfo("Success", "Configuration loaded successfully!")
        except Exception as e:
            self.config_status_label.config(text="Error", style='Error.TLabel')
            self.log_activity(f"Failed to load configuration: {e}")
            messagebox.showerror("Error", f"Failed to load configuration:\n{e}")
    
    def populate_config_ui(self) -> None:
        """Populate UI fields with configuration values."""
        if not self.config:
            return
        
        try:
            # Populate Atlassian config
            if 'atlassian' in self.config:
                if 'confluence' in self.config['atlassian']:
                    conf = self.config['atlassian']['confluence']
                    self.confluence_vars['url'].set(conf.get('url', ''))
                    self.confluence_vars['username'].set(conf.get('username', ''))
                    self.confluence_vars['api_token'].set(conf.get('api_token', ''))
                    self.confluence_cloud_var.set(conf.get('cloud', True))
                
                if 'jira' in self.config['atlassian']:
                    jira = self.config['atlassian']['jira']
                    self.jira_vars['url'].set(jira.get('url', ''))
                    self.jira_vars['username'].set(jira.get('username', ''))
                    self.jira_vars['api_token'].set(jira.get('api_token', ''))
                    self.jira_cloud_var.set(jira.get('cloud', True))
            
            # Populate target systems
            if 'targets' in self.config:
                if 'wikijs' in self.config['targets']:
                    wikijs = self.config['targets']['wikijs']
                    self.wikijs_enabled_var.set(wikijs.get('enabled', False))
                    self.wikijs_vars['url'].set(wikijs.get('url', ''))
                    self.wikijs_vars['api_token'].set(wikijs.get('api_token', ''))
                
                if 'openproject' in self.config['targets']:
                    op = self.config['targets']['openproject']
                    self.openproject_enabled_var.set(op.get('enabled', False))
                    self.openproject_vars['url'].set(op.get('url', ''))
                    self.openproject_vars['api_key'].set(op.get('api_key', ''))
                
                if 'gitlab' in self.config['targets']:
                    gl = self.config['targets']['gitlab']
                    self.gitlab_enabled_var.set(gl.get('enabled', False))
                    self.gitlab_vars['url'].set(gl.get('url', ''))
                    self.gitlab_vars['token'].set(gl.get('token', ''))
            
            # Populate migration settings
            if 'migration' in self.config:
                mig = self.config['migration']
                self.migration_mode_var.set(mig.get('mode', 'full'))
                self.preserve_timestamps_var.set(mig.get('preserve_timestamps', True))
                self.download_attachments_var.set(mig.get('download_attachments', True))
                self.dry_run_var.set(mig.get('dry_run', False))
                self.max_workers_var.set(mig.get('max_workers', 4))
        
        except Exception as e:
            logger.error(f"Error populating config UI: {e}")
            self.log_activity(f"Error populating UI: {e}")
    
    def save_configuration(self) -> None:
        """Save configuration to file."""
        try:
            # Build config dict from UI values
            config = {
                'atlassian': {
                    'confluence': {
                        'url': self.confluence_vars['url'].get(),
                        'username': self.confluence_vars['username'].get(),
                        'api_token': self.confluence_vars['api_token'].get(),
                        'cloud': self.confluence_cloud_var.get(),
                    },
                    'jira': {
                        'url': self.jira_vars['url'].get(),
                        'username': self.jira_vars['username'].get(),
                        'api_token': self.jira_vars['api_token'].get(),
                        'cloud': self.jira_cloud_var.get(),
                    }
                },
                'targets': {
                    'wikijs': {
                        'enabled': self.wikijs_enabled_var.get(),
                        'url': self.wikijs_vars['url'].get(),
                        'api_token': self.wikijs_vars['api_token'].get(),
                    },
                    'openproject': {
                        'enabled': self.openproject_enabled_var.get(),
                        'url': self.openproject_vars['url'].get(),
                        'api_key': self.openproject_vars['api_key'].get(),
                    },
                    'gitlab': {
                        'enabled': self.gitlab_enabled_var.get(),
                        'url': self.gitlab_vars['url'].get(),
                        'token': self.gitlab_vars['token'].get(),
                    }
                },
                'migration': {
                    'mode': self.migration_mode_var.get(),
                    'preserve_timestamps': self.preserve_timestamps_var.get(),
                    'download_attachments': self.download_attachments_var.get(),
                    'dry_run': self.dry_run_var.get(),
                    'max_workers': self.max_workers_var.get(),
                }
            }
            
            # Save to file
            config_path = self.config_path_var.get()
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
            self.log_activity(f"Configuration saved to {config_path}")
            messagebox.showinfo("Success", "Configuration saved successfully!")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            messagebox.showerror("Error", f"Failed to save configuration:\n{e}")
    
    def browse_config_file(self) -> None:
        """Browse for configuration file."""
        filename = filedialog.askopenfilename(
            title="Select Configuration File",
            filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")]
        )
        if filename:
            self.config_path_var.set(filename)
    
    def open_config_file(self) -> None:
        """Open configuration file in external editor."""
        config_path = self.config_path_var.get() if hasattr(self, 'config_path_var') else self.config_path
        try:
            if os.path.exists(config_path):
                os.startfile(config_path) if os.name == 'nt' else os.system(f'xdg-open "{config_path}"')
            else:
                messagebox.showwarning("Warning", "Configuration file does not exist!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open config file:\n{e}")
    
    # Migration methods
    
    def start_migration(self) -> None:
        """Start the migration process."""
        if not self.config:
            messagebox.showerror("Error", "Please load configuration first!")
            return
        
        # Validate project selection
        projects = [p.strip() for p in self.jira_projects_var.get().split(',') if p.strip()]
        if not projects:
            messagebox.showerror("Error", "Please enter at least one project key!")
            return
        
        # Update UI
        self.start_migration_btn.config(state='disabled')
        self.stop_migration_btn.config(state='normal')
        self.migration_progress.start()
        self.migration_status_label.config(text="Export in progress...")
        
        # Start export in background thread
        thread = threading.Thread(target=self.run_migration, daemon=True)
        thread.start()
        
        self.log_activity("Export started")
        self.append_migration_log("Export started\n")
    
    def run_migration(self) -> None:
        """Run the export process (in background thread)."""
        try:
            self.append_migration_log("Initializing Jira export...\n")
            
            # Extract Jira
            self.append_migration_log("\n--- Extracting from Jira ---\n")
            projects = [p.strip() for p in self.jira_projects_var.get().split(',') if p.strip()]
            self.append_migration_log(f"Projects: {', '.join(projects)}\n")
            
            try:
                from atlassian_migration_tool.extractors import JiraExtractor
                extractor = JiraExtractor(self.config['atlassian']['jira'])
                
                for project_key in projects:
                    self.append_migration_log(f"\nExtracting project: {project_key}...\n")
                    project = extractor.extract_project(project_key)
                    self.append_migration_log(f"✓ Extracted {len(project.issues)} issues\n")
                    self.append_migration_log(f"  Issues organized by type in: data/extracted/jira/{project_key}/by-issue-type/\n")
                    
                    # Show issue type breakdown
                    types = {}
                    for issue in project.issues:
                        t = issue.issue_type
                        types[t] = types.get(t, 0) + 1
                    
                    for itype, count in sorted(types.items()):
                        self.append_migration_log(f"  - {itype}: {count} issues\n")
                
            except Exception as e:
                self.append_migration_log(f"ERROR: Failed to extract Jira: {e}\n")
                logger.exception("Jira extraction failed")
            
            self.append_migration_log("\nExport completed successfully!\n")
            self.root.after(0, self.migration_complete, True)
            
        except Exception as e:
            logger.exception("Migration failed")
            self.append_migration_log(f"\nERROR: {e}\n")
            self.root.after(0, self.migration_complete, False)
    
    def migration_complete(self, success: bool) -> None:
        """Handle migration completion."""
        self.migration_progress.stop()
        self.start_migration_btn.config(state='normal')
        self.stop_migration_btn.config(state='disabled')
        
        if success:
            self.migration_status_label.config(text="Migration completed successfully!")
            self.log_activity("Migration completed successfully")
        else:
            self.migration_status_label.config(text="Migration failed!")
            self.log_activity("Migration failed")
    
    def stop_migration(self) -> None:
        """Stop the migration process."""
        # TODO: Implement graceful shutdown
        self.append_migration_log("\nStopping migration...\n")
        self.migration_complete(False)
    
    def append_migration_log(self, message: str) -> None:
        """Append message to migration log."""
        self.migration_log.config(state='normal')
        self.migration_log.insert('end', message)
        self.migration_log.see('end')
        self.migration_log.config(state='disabled')
    
    # Connection testing
    
    def test_all_connections(self) -> None:
        """Test connections to all configured systems."""
        if not self.config:
            messagebox.showerror("Error", "Please load configuration first!")
            return
        
        results = []
        
        # Test Confluence
        try:
            from atlassian_migration_tool.extractors import ConfluenceExtractor
            extractor = ConfluenceExtractor(self.config['atlassian']['confluence'])
            if extractor.test_connection():
                results.append("✓ Confluence: Connected")
            else:
                results.append("✗ Confluence: Failed")
        except Exception as e:
            results.append(f"✗ Confluence: {str(e)[:50]}")
        
        # TODO: Test other systems
        
        message = "\n".join(results)
        self.conn_status_label.config(text="Tested")
        self.log_activity("Connection tests completed")
        messagebox.showinfo("Connection Test Results", message)
    
    def list_confluence_spaces(self) -> None:
        """List available Confluence spaces."""
        if not self.config:
            messagebox.showerror("Error", "Please load configuration first!")
            return
        
        try:
            from atlassian_migration_tool.extractors import ConfluenceExtractor
            extractor = ConfluenceExtractor(self.config['atlassian']['confluence'])
            spaces = extractor.list_spaces()
            
            # Show in dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("Confluence Spaces")
            dialog.geometry("600x400")
            
            text = scrolledtext.ScrolledText(dialog)
            text.pack(fill='both', expand=True, padx=10, pady=10)
            
            for space in spaces:
                text.insert('end', f"{space['key']}: {space['name']}\n")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to list spaces:\n{e}")
    
    def list_jira_projects(self) -> None:
        """List available Jira projects."""
        if not self.config:
            messagebox.showerror("Error", "Please load configuration first!")
            return
        
        try:
            from atlassian_migration_tool.extractors import JiraExtractor
            extractor = JiraExtractor(self.config['atlassian']['jira'])
            projects = extractor.list_projects()
            
            # Show in dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("Jira Projects")
            dialog.geometry("600x400")
            
            text = scrolledtext.ScrolledText(dialog)
            text.pack(fill='both', expand=True, padx=10, pady=10)
            
            for project in projects:
                text.insert('end', f"{project['key']}: {project['name']}\n")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to list projects:\n{e}")
    
    def open_output_folder(self) -> None:
        """Open the output folder in file explorer."""
        output_path = Path("data/extracted/jira").absolute()
        output_path.mkdir(parents=True, exist_ok=True)
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(output_path)
            else:  # Linux/Mac
                os.system(f'xdg-open "{output_path}"')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder:\n{e}")
    
    # Utility methods
    
    def log_activity(self, message: str) -> None:
        """Log activity to the dashboard."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.activity_text.config(state='normal')
        self.activity_text.insert('end', f"[{timestamp}] {message}\n")
        self.activity_text.see('end')
        self.activity_text.config(state='disabled')
    
    def refresh_statistics(self) -> None:
        """Refresh migration statistics."""
        self.stats_text.config(state='normal')
        self.stats_text.delete('1.0', 'end')
        self.stats_text.insert('end', "Migration statistics not yet available.\n\n")
        self.stats_text.insert('end', "Statistics will be shown here after running migrations.")
        self.stats_text.config(state='disabled')
    
    def refresh_logs(self) -> None:
        """Refresh log display."""
        try:
            log_file = Path("data/logs/migration.log")
            if log_file.exists():
                with open(log_file, 'r') as f:
                    content = f.read()
                    self.log_text.config(state='normal')
                    self.log_text.delete('1.0', 'end')
                    self.log_text.insert('end', content)
                    self.log_text.see('end')
                    self.log_text.config(state='disabled')
            else:
                messagebox.showinfo("Info", "Log file not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read log file:\n{e}")
    
    def clear_log_display(self) -> None:
        """Clear the log display."""
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.config(state='disabled')
    
    def open_log_file(self) -> None:
        """Open log file in external editor."""
        log_file = Path("data/logs/migration.log")
        try:
            if log_file.exists():
                os.startfile(str(log_file)) if os.name == 'nt' else os.system(f'xdg-open "{log_file}"')
            else:
                messagebox.showinfo("Info", "Log file not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open log file:\n{e}")
    
    def view_logs(self) -> None:
        """Switch to logs tab."""
        self.notebook.select(4)
        self.refresh_logs()
    
    def clear_cache(self) -> None:
        """Clear application cache."""
        cache_dir = Path("data/cache")
        if cache_dir.exists():
            try:
                import shutil
                shutil.rmtree(cache_dir)
                cache_dir.mkdir(parents=True, exist_ok=True)
                messagebox.showinfo("Success", "Cache cleared successfully!")
                self.log_activity("Cache cleared")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear cache:\n{e}")
        else:
            messagebox.showinfo("Info", "Cache directory does not exist")
    
    def show_documentation(self) -> None:
        """Show documentation."""
        messagebox.showinfo("Documentation", 
                          "Documentation is available in the project README.md file.\n\n"
                          "For more information, visit:\n"
                          "https://github.com/ddunnock/atlassian-migration-tool")
    
    def show_about(self) -> None:
        """Show about dialog."""
        about_text = """
Atlassian Migration Tool
Version 0.1.0

A comprehensive tool for migrating content from 
Atlassian products (Confluence, Jira) to open-source 
alternatives (Wiki.js, OpenProject, GitLab).

Author: David Dunnock
License: MIT
Repository: github.com/ddunnock/atlassian-migration-tool
        """
        messagebox.showinfo("About", about_text)


def main() -> None:
    """Main entry point for the GUI application."""
    root = tk.Tk()
    app = MigrationToolGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
