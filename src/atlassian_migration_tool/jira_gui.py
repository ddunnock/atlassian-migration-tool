#!/usr/bin/env python3
"""
Simple Jira Export GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
import threading
import os

from atlassian_migration_tool.utils.config_loader import load_config
from atlassian_migration_tool.extractors import JiraExtractor
from loguru import logger


class JiraExportGUI:
    """Simple GUI for exporting Jira issues."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Jira Export Tool")
        self.root.geometry("800x600")
        
        # Load config
        try:
            self.config = load_config()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config:\n{e}")
            self.config = None
        
        self.create_ui()
    
    def create_ui(self):
        """Create the user interface."""
        # Title
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Label(title_frame, text="Jira Export Tool", 
                 font=('Helvetica', 18, 'bold')).pack()
        ttk.Label(title_frame, text="Export Jira issues organized by type", 
                 font=('Helvetica', 10)).pack(pady=5)
        
        # Project selection
        project_frame = ttk.LabelFrame(self.root, text="Project Configuration", padding=15)
        project_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(project_frame, 
                 text="Enter project keys separated by commas (e.g., NSTTC-O, PROJECT2)").pack(anchor='w', pady=5)
        
        input_frame = ttk.Frame(project_frame)
        input_frame.pack(fill='x', pady=5)
        
        ttk.Label(input_frame, text="Projects:", width=10).pack(side='left')
        self.projects_var = tk.StringVar(value="NSTTC-O")
        ttk.Entry(input_frame, textvariable=self.projects_var, width=50).pack(side='left', padx=5, fill='x', expand=True)
        
        # Info
        info_frame = ttk.LabelFrame(self.root, text="Export Information", padding=15)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        info_text = """Output Location: data/extracted/jira/PROJECT/by-issue-type/

Issues will be organized into separate files by type:
  • Initiatives
  • Epics  
  • Stories
  • Bugs
  • Tasks

Each type will have both JSON and CSV formats for easy viewing."""
        
        ttk.Label(info_frame, text=info_text, justify='left').pack(anchor='w')
        
        # Progress log
        log_frame = ttk.LabelFrame(self.root, text="Export Progress", padding=10)
        log_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state='disabled')
        self.log_text.pack(fill='both', expand=True)
        
        # Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill='x', padx=20, pady=10)
        
        self.export_btn = ttk.Button(button_frame, text="Start Export", 
                                      command=self.start_export)
        self.export_btn.pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="Open Output Folder", 
                  command=self.open_output).pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="Clear Log", 
                  command=self.clear_log).pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="Exit", 
                  command=self.root.quit).pack(side='right', padx=5)
        
        self.log("Ready. Click 'Start Export' to begin.")
    
    def log(self, message: str):
        """Add message to log."""
        self.log_text.config(state='normal')
        self.log_text.insert('end', f"{message}\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')
    
    def clear_log(self):
        """Clear the log."""
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.config(state='disabled')
    
    def start_export(self):
        """Start the export process."""
        if not self.config:
            messagebox.showerror("Error", "Configuration not loaded!")
            return
        
        projects = [p.strip() for p in self.projects_var.get().split(',') if p.strip()]
        if not projects:
            messagebox.showerror("Error", "Please enter at least one project key!")
            return
        
        # Disable button
        self.export_btn.config(state='disabled', text="Exporting...")
        
        # Run in thread
        thread = threading.Thread(target=self.run_export, args=(projects,), daemon=True)
        thread.start()
    
    def run_export(self, projects):
        """Run the actual export."""
        try:
            self.log("\n" + "="*60)
            self.log("Starting Jira Export")
            self.log("="*60)
            
            extractor = JiraExtractor(self.config['atlassian']['jira'])
            
            for project_key in projects:
                self.log(f"\nExporting project: {project_key}...")
                
                try:
                    project = extractor.extract_project(project_key)
                    self.log(f"✓ Extracted {len(project.issues)} issues from {project_key}")
                    
                    # Show breakdown
                    types = {}
                    for issue in project.issues:
                        t = issue.issue_type
                        types[t] = types.get(t, 0) + 1
                    
                    self.log(f"\nIssue breakdown:")
                    for itype, count in sorted(types.items()):
                        self.log(f"  • {itype}: {count} issues")
                    
                    self.log(f"\n  Saved to: data/extracted/jira/{project_key}/by-issue-type/")
                    
                except Exception as e:
                    self.log(f"✗ Failed to export {project_key}: {e}")
                    logger.exception(f"Export failed for {project_key}")
            
            self.log("\n" + "="*60)
            self.log("Export Complete!")
            self.log("="*60)
            
            self.root.after(0, lambda: self.export_btn.config(state='normal', text="Start Export"))
            self.root.after(0, lambda: messagebox.showinfo("Success", "Export completed successfully!"))
            
        except Exception as e:
            self.log(f"\n✗ ERROR: {e}")
            logger.exception("Export failed")
            self.root.after(0, lambda: self.export_btn.config(state='normal', text="Start Export"))
            self.root.after(0, lambda: messagebox.showerror("Error", f"Export failed:\n{e}"))
    
    def open_output(self):
        """Open the output folder."""
        output_path = Path("data/extracted/jira").absolute()
        output_path.mkdir(parents=True, exist_ok=True)
        
        try:
            if os.name == 'nt':
                os.startfile(output_path)
            else:
                os.system(f'xdg-open "{output_path}"')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder:\n{e}")


def main():
    """Main entry point."""
    root = tk.Tk()
    app = JiraExportGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
