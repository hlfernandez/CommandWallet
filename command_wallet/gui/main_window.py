"""
Main window module for CommandWallet.

Contains the main application window with command list,
editor, and output display functionality.
"""

import customtkinter as ctk
from tkinter import messagebox
import platform
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..core.data_manager import DataManager
from ..core.command_executor import CommandExecutor
from .config_dialog import ConfigDialog
from .cron_dialog import CronExportDialog


class CommandWalletWindow:
    """Main application window for CommandWallet."""
    
    def __init__(self):
        """Initialize the main window."""
        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("CommandWallet")
        self._maximize_window()
        
        # Initialize core components
        self.data_manager = DataManager()
        self.command_executor = CommandExecutor(self._update_output)
        
        # Data storage
        self.commands = {}
        self.current_command_id = None
        self.config = {}
        
        # GUI components
        self.command_buttons = []
        self.output_text = None
        self.run_button = None
        
        # Load data and create GUI
        self._load_data()
        self._create_widgets()
        
        # Load first command if any
        if self.commands:
            first_id = list(self.commands.keys())[0]
            self.load_command(first_id)
        
        # Setup window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def run(self) -> None:
        """Run the main application loop."""
        self.root.mainloop()
    
    def _maximize_window(self) -> None:
        """Maximize the window cross-platform."""
        system = platform.system()
        if system == "Windows":
            self.root.state('zoomed')
        elif system == "Darwin":  # macOS
            self.root.attributes('-zoomed', True)
        else:  # Linux and others
            try:
                self.root.attributes('-zoomed', True)
            except:
                # If it fails, use large default size
                self.root.geometry("1200x800")
    
    def _load_data(self) -> None:
        """Load commands and configuration from storage."""
        self.commands = self.data_manager.load_commands()
        self.config = self.data_manager.load_config()
    
    def _create_widgets(self) -> None:
        """Create the main window widgets."""
        # Main container
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configure grid weights
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Left panel for commands list
        self._create_left_panel(main_frame)
        
        # Right panel for command editing
        self._create_right_panel(main_frame)
    
    def _create_left_panel(self, parent) -> None:
        """Create the left panel with command list and controls."""
        left_frame = ctk.CTkFrame(parent)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(2, weight=1)
        
        # Commands list label
        ctk.CTkLabel(
            left_frame, 
            text="Commands", 
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, pady=(10, 5), padx=10)
        
        # Sorting buttons frame
        sort_frame = ctk.CTkFrame(left_frame)
        sort_frame.grid(row=1, column=0, pady=(0, 10), padx=10, sticky="ew")
        sort_frame.grid_columnconfigure(0, weight=1)
        sort_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkButton(
            sort_frame, 
            text="Sort by Name", 
            command=self._sort_by_name
        ).grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        
        ctk.CTkButton(
            sort_frame, 
            text="Sort by Date", 
            command=self._sort_by_date
        ).grid(row=0, column=1, padx=(5, 10), pady=10, sticky="ew")
        
        # Commands list frame
        self.commands_frame = ctk.CTkScrollableFrame(left_frame, label_text="Commands List")
        self.commands_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.commands_frame.grid_columnconfigure(0, weight=1)
        
        # Add/Delete buttons frame
        buttons_frame = ctk.CTkFrame(left_frame)
        buttons_frame.grid(row=3, column=0, pady=(0, 10), padx=10, sticky="ew")
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkButton(
            buttons_frame, 
            text="Add", 
            command=self._add_command
        ).grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        
        ctk.CTkButton(
            buttons_frame, 
            text="Delete", 
            command=self._delete_command
        ).grid(row=0, column=1, padx=(5, 10), pady=10, sticky="ew")
        
        self._update_commands_list()
    
    def _create_right_panel(self, parent) -> None:
        """Create the right panel with command editor and output."""
        right_frame = ctk.CTkFrame(parent)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        right_frame.grid_columnconfigure(1, weight=1)
        right_frame.grid_rowconfigure(4, weight=1)
        
        # Command name
        ctk.CTkLabel(
            right_frame, 
            text="Name:", 
            font=ctk.CTkFont(size=14)
        ).grid(row=0, column=0, sticky="w", pady=(10, 5), padx=(10, 5))
        
        self.name_entry = ctk.CTkEntry(
            right_frame, 
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.name_entry.grid(row=0, column=1, sticky="ew", pady=(10, 5), padx=(0, 10))
        self.name_entry.bind('<KeyRelease>', self._on_name_change)
        
        # Command input
        ctk.CTkLabel(
            right_frame, 
            text="Command:", 
            font=ctk.CTkFont(size=14)
        ).grid(row=1, column=0, sticky="w", pady=(5, 5), padx=(10, 5))
        
        self.command_entry = ctk.CTkEntry(
            right_frame, 
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.command_entry.grid(row=1, column=1, sticky="ew", pady=(5, 5), padx=(0, 10))
        self.command_entry.bind('<KeyRelease>', self._on_command_change)
        
        # Execution options frame
        self._create_execution_options(right_frame)
        
        # Buttons frame
        self._create_action_buttons(right_frame)
        
        # Output area
        self._create_output_area(right_frame)
    
    def _create_execution_options(self, parent) -> None:
        """Create the execution options section."""
        options_frame = ctk.CTkFrame(parent)
        options_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 5), padx=10)
        options_frame.grid_columnconfigure(1, weight=1)
        
        # Options section label
        ctk.CTkLabel(
            options_frame, 
            text="Execution Options", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=(10, 10), padx=10, sticky="w")
        
        # Conda environment option
        self.conda_var = ctk.BooleanVar()
        self.conda_checkbox = ctk.CTkCheckBox(
            options_frame, 
            text="Run in Conda Environment",
            variable=self.conda_var, 
            command=self._toggle_conda
        )
        self.conda_checkbox.grid(row=1, column=0, sticky="w", pady=(0, 10), padx=(10, 10))
        
        # Conda environments combo
        conda_frame = ctk.CTkFrame(options_frame)
        conda_frame.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 10))
        conda_frame.grid_columnconfigure(0, weight=1)
        
        self.conda_combo = ctk.CTkComboBox(
            conda_frame, 
            values=self.command_executor.get_conda_environments(), 
            state="disabled"
        )
        self.conda_combo.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self._bind_conda_events()
        
        # Docker container option
        self.docker_var = ctk.BooleanVar()
        self.docker_checkbox = ctk.CTkCheckBox(
            options_frame, 
            text="Run in Docker Container",
            variable=self.docker_var, 
            command=self._toggle_docker
        )
        self.docker_checkbox.grid(row=2, column=0, sticky="w", pady=(0, 10), padx=(10, 10))
        
        # Docker images combo
        docker_frame = ctk.CTkFrame(options_frame)
        docker_frame.grid(row=2, column=1, sticky="ew", padx=(0, 10), pady=(0, 10))
        docker_frame.grid_columnconfigure(0, weight=1)
        
        self.docker_combo = ctk.CTkComboBox(
            docker_frame, 
            values=self.command_executor.get_docker_images(), 
            state="disabled"
        )
        self.docker_combo.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self._bind_docker_events()
        
        # Volume mounts
        ctk.CTkLabel(
            options_frame, 
            text="Volume Mounts:", 
            font=ctk.CTkFont(size=12)
        ).grid(row=3, column=0, sticky="w", pady=(5, 10), padx=(10, 10))
        
        self.volume_mounts_entry = ctk.CTkEntry(options_frame, state="disabled")
        self.volume_mounts_entry.grid(row=3, column=1, sticky="ew", padx=(0, 10), pady=(5, 10))
        self.volume_mounts_entry.bind('<KeyRelease>', self._on_volume_mounts_change)
        self.volume_mounts_entry.bind('<FocusOut>', self._on_volume_mounts_change)
    
    def _create_action_buttons(self, parent) -> None:
        """Create the action buttons section."""
        buttons_frame = ctk.CTkFrame(parent)
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=(20, 10), padx=10)
        
        self.run_button = ctk.CTkButton(
            buttons_frame, 
            text="Run Command", 
            command=self._run_command
        )
        self.run_button.pack(side="left", padx=(10, 5), pady=10)
        
        ctk.CTkButton(
            buttons_frame, 
            text="Export Cron", 
            command=self._show_cron_dialog
        ).pack(side="left", padx=(5, 5), pady=10)
        
        ctk.CTkButton(
            buttons_frame, 
            text="Config", 
            command=self._show_config_dialog
        ).pack(side="left", padx=(5, 10), pady=10)
    
    def _create_output_area(self, parent) -> None:
        """Create the output display area."""
        output_frame = ctk.CTkFrame(parent)
        output_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(5, 10), padx=10)
        output_frame.grid_columnconfigure(0, weight=1)
        output_frame.grid_rowconfigure(1, weight=1)
        
        # Output label
        ctk.CTkLabel(
            output_frame, 
            text="Output", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(10, 5), padx=10)
        
        # Output text area
        self.output_text = ctk.CTkTextbox(
            output_frame, 
            wrap="word", 
            state="disabled",
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.output_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Add context menu
        self._create_output_context_menu()
    
    def _bind_conda_events(self) -> None:
        """Bind events for conda combo box."""
        conda_envs = self.command_executor.get_conda_environments()
        
        def filter_conda_environments(event):
            current_text = event.widget.get()
            typed_text = current_text.lower()
            
            if not typed_text:
                self.conda_combo.configure(values=conda_envs)
                return
            
            if current_text in conda_envs:
                return
            
            filtered = [env for env in conda_envs if typed_text in env.lower()]
            self.conda_combo.configure(values=filtered if filtered else conda_envs)
        
        def on_conda_click(event):
            if self.conda_combo.cget('state') == 'normal':
                self.conda_combo.configure(values=conda_envs)
        
        self.conda_combo.bind('<KeyRelease>', filter_conda_environments)
        self.conda_combo.bind('<Button-1>', on_conda_click)
        self.conda_combo.bind('<<ComboboxSelected>>', self._on_conda_selected)
        self.conda_combo.bind('<FocusOut>', self._on_conda_change)
    
    def _bind_docker_events(self) -> None:
        """Bind events for docker combo box."""
        docker_images = self.command_executor.get_docker_images()
        
        def filter_docker_images(event):
            current_text = event.widget.get()
            typed_text = current_text.lower()
            
            if not typed_text:
                self.docker_combo.configure(values=docker_images)
                return
            
            if current_text in docker_images:
                return
            
            filtered = [img for img in docker_images if typed_text in img.lower()]
            self.docker_combo.configure(values=filtered if filtered else docker_images)
        
        def on_docker_click(event):
            if self.docker_combo.cget('state') == 'normal':
                self.docker_combo.configure(values=docker_images)
        
        self.docker_combo.bind('<KeyRelease>', filter_docker_images)
        self.docker_combo.bind('<Button-1>', on_docker_click)
        self.docker_combo.bind('<<ComboboxSelected>>', self._on_docker_selected)
        self.docker_combo.bind('<FocusOut>', self._on_docker_change)
    
    def _create_output_context_menu(self) -> None:
        """Create right-click context menu for output text area."""
        import tkinter as tk
        
        # Create context menu
        self.output_menu = tk.Menu(self.root, tearoff=0)
        self.output_menu.add_command(label="Copy All", command=self._copy_all_output)
        self.output_menu.add_command(label="Copy Selection", command=self._copy_selected_output)
        self.output_menu.add_separator()
        self.output_menu.add_command(label="Clear Output", command=self._clear_output)
        
        # Bind right-click to show menu
        self.output_text.bind("<Button-3>", self._show_output_context_menu)
        
        # Bind keyboard shortcuts
        self.output_text.bind("<Control-c>", lambda e: self._copy_selected_output())
        self.output_text.bind("<Control-a>", lambda e: self._select_all_output())
    
    # Event handlers and utility methods continue in the next part...
    
    def _show_output_context_menu(self, event) -> None:
        """Show context menu at cursor position."""
        try:
            # Check if there's a selection to enable/disable copy selection
            if self.output_text.tag_ranges("sel"):
                self.output_menu.entryconfig("Copy Selection", state="normal")
            else:
                self.output_menu.entryconfig("Copy Selection", state="disabled")
            
            # Check if there's any text to enable/disable copy all
            if self.output_text.get("1.0", "end-1c").strip():
                self.output_menu.entryconfig("Copy All", state="normal")
                self.output_menu.entryconfig("Clear Output", state="normal")
            else:
                self.output_menu.entryconfig("Copy All", state="disabled")
                self.output_menu.entryconfig("Clear Output", state="disabled")
            
            # Show menu at cursor position
            self.output_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"Error showing context menu: {e}")
        finally:
            self.output_menu.grab_release()
    
    def _copy_all_output(self) -> None:
        """Copy all output text to clipboard."""
        try:
            text = self.output_text.get("1.0", "end-1c")
            if text.strip():
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self.root.update()
                self._show_status_message("All output copied to clipboard")
        except Exception as e:
            print(f"Error copying all output: {e}")
    
    def _copy_selected_output(self) -> None:
        """Copy selected output text to clipboard."""
        try:
            if self.output_text.tag_ranges("sel"):
                selected_text = self.output_text.get("sel.first", "sel.last")
                if selected_text:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(selected_text)
                    self.root.update()
                    self._show_status_message("Selected text copied to clipboard")
            else:
                self._show_status_message("No text selected")
        except Exception as e:
            print(f"Error copying selected output: {e}")
    
    def _select_all_output(self) -> None:
        """Select all text in output area."""
        try:
            self.output_text.tag_add("sel", "1.0", "end")
            return "break"
        except Exception as e:
            print(f"Error selecting all output: {e}")
    
    def _clear_output(self) -> None:
        """Clear all output text."""
        try:
            self.output_text.configure(state="normal")
            self.output_text.delete("1.0", "end")
            self.output_text.configure(state="disabled")
        except Exception as e:
            print(f"Error clearing output: {e}")
    
    def _show_status_message(self, message: str) -> None:
        """Show a brief status message in the output area."""
        try:
            self.output_text.configure(state="normal")
            
            current_text = self.output_text.get("1.0", "end-1c")
            if current_text and not current_text.endswith('\n'):
                self.output_text.insert("end", "\n")
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            status_line = f"[{timestamp}] {message}\n"
            self.output_text.insert("end", status_line)
            self.output_text.see("end")
            
            self.output_text.configure(state="disabled")
        except Exception as e:
            print(f"Error showing status message: {e}")
    
    def _update_output(self, text: str) -> None:
        """Update output text widget (callback for command executor)."""
        def update():
            self.output_text.configure(state="normal")
            self.output_text.insert("end", text)
            self.output_text.see("end")
            self.output_text.configure(state="disabled")
        
        self.root.after(0, update)
    
    def _add_command(self) -> None:
        """Add a new command."""
        command_id = self.data_manager.create_new_command(self.commands)
        self._update_commands_list()
        self.load_command(command_id)
        self.data_manager.save_commands(self.commands)
    
    def _delete_command(self) -> None:
        """Delete selected command."""
        if self.current_command_id and self.current_command_id in self.commands:
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this command?"):
                del self.commands[self.current_command_id]
                self._update_commands_list()
                self._clear_form()
                self.data_manager.save_commands(self.commands)
    
    def _update_commands_list(self, sort_by: Optional[str] = None) -> None:
        """Update the commands list in the scrollable frame."""
        # Clear existing buttons
        for button in self.command_buttons:
            button.destroy()
        self.command_buttons.clear()
        
        # Sort commands
        if sort_by == 'name':
            sorted_commands = sorted(self.commands.items(), key=lambda item: item[1]['name'].lower())
        elif sort_by == 'date':
            def get_sort_key(item):
                last_exec = item[1].get('last_execution')
                return last_exec or '1970-01-01 00:00:00'
            
            sorted_commands = sorted(self.commands.items(), key=get_sort_key, reverse=True)
        else:
            sorted_commands = self.commands.items()
        
        # Create command buttons
        for i, (command_id, command_data) in enumerate(sorted_commands):
            button = ctk.CTkButton(
                self.commands_frame,
                text=command_data['name'],
                command=lambda cid=command_id: self.load_command(cid),
                anchor="w"
            )
            button.grid(row=i, column=0, sticky="ew", padx=5, pady=2)
            self.command_buttons.append(button)
            
            # Add tooltip
            self._create_tooltip(button, command_data)
    
    def _create_tooltip(self, widget, command_data: Dict[str, Any]) -> None:
        """Create tooltip for command button showing last execution date."""
        def on_enter(event):
            last_exec = command_data.get('last_execution')
            if last_exec:
                try:
                    dt = datetime.strptime(last_exec, "%Y-%m-%d %H:%M:%S")
                    formatted_date = dt.strftime("%d/%m/%Y %H:%M:%S")
                    tooltip_text = f"Last executed: {formatted_date}"
                except:
                    tooltip_text = f"Last executed: {last_exec}"
            else:
                tooltip_text = "Never executed"
            
            # Create tooltip window
            self.tooltip = ctk.CTkToplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = ctk.CTkLabel(self.tooltip, text=tooltip_text, font=ctk.CTkFont(size=10))
            label.pack()
        
        def on_leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
                delattr(self, 'tooltip')
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def _sort_by_name(self) -> None:
        """Sort commands by name."""
        self._update_commands_list(sort_by='name')
    
    def _sort_by_date(self) -> None:
        """Sort commands by last execution date."""
        self._update_commands_list(sort_by='date')
    
    def load_command(self, command_id: str) -> None:
        """Load command data into the form."""
        if command_id in self.commands:
            self.current_command_id = command_id
            command_data = self.commands[command_id]
            
            # Load basic data
            self.name_entry.delete(0, "end")
            self.name_entry.insert(0, command_data['name'])
            
            self.command_entry.delete(0, "end")
            self.command_entry.insert(0, command_data['command'])
            
            # Load conda settings
            self.conda_var.set(command_data['use_conda'])
            if command_data['use_conda']:
                self.conda_combo.configure(state="normal")
                self.conda_combo.set(command_data['conda_env'])
                self.volume_mounts_entry.configure(state="disabled")
            else:
                self.conda_combo.configure(state="disabled")
                self.conda_combo.set('')
            
            # Load docker settings
            self.docker_var.set(command_data['use_docker'])
            if command_data['use_docker']:
                self.docker_combo.configure(state="normal")
                self.docker_combo.set(command_data['docker_image'])
                self.volume_mounts_entry.configure(state="normal")
                
                # Load volume mounts (backward compatibility)
                volume_mounts = command_data.get('volume_mounts', command_data.get('additional_mounts', ''))
                self.volume_mounts_entry.delete(0, "end")
                self.volume_mounts_entry.insert(0, volume_mounts)
            else:
                self.docker_combo.configure(state="disabled")
                self.docker_combo.set('')
                self.volume_mounts_entry.configure(state="disabled")
                self.volume_mounts_entry.delete(0, "end")
    
    def _clear_form(self) -> None:
        """Clear the form."""
        self.current_command_id = None
        self.name_entry.delete(0, "end")
        self.command_entry.delete(0, "end")
        self.conda_var.set(False)
        self.docker_var.set(False)
        self.conda_combo.configure(state="disabled")
        self.docker_combo.configure(state="disabled")
        self.volume_mounts_entry.configure(state="disabled")
        self.volume_mounts_entry.delete(0, "end")
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")
    
    def _save_command_data(self) -> None:
        """Save current command data."""
        if self.current_command_id:
            self.commands[self.current_command_id].update({
                'name': self.name_entry.get(),
                'command': self.command_entry.get(),
                'use_conda': self.conda_var.get(),
                'conda_env': self.conda_combo.get(),
                'use_docker': self.docker_var.get(),
                'docker_image': self.docker_combo.get(),
                'volume_mounts': self.volume_mounts_entry.get()
            })
            self.data_manager.save_commands(self.commands)
    
    def _run_command(self) -> None:
        """Run the selected command."""
        if not self.current_command_id:
            messagebox.showwarning("No Command", "Please select a command to run.")
            return
        
        # Save current data
        self._save_command_data()
        
        command_data = self.commands[self.current_command_id]
        command = command_data['command'].strip()
        
        if not command:
            messagebox.showwarning("Empty Command", "Please enter a command to run.")
            return
        
        # Save execution timestamp
        self.data_manager.update_command_execution_time(self.commands, self.current_command_id)
        self.data_manager.save_commands(self.commands)
        
        # Prepare and display starting message
        execution_time = datetime.now()
        timestamp_str = execution_time.strftime("%d/%m/%Y-%H:%M:%S")
        final_command = self.command_executor._prepare_command(command_data, self.config)
        
        # Clear output and add starting message
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", f"Started command '{final_command}' at {timestamp_str}\n\n")
        self.output_text.configure(state="disabled")
        
        # Disable run button
        self.run_button.configure(state="disabled")
        
        # Execute command asynchronously
        def on_completion():
            self.root.after(0, lambda: self.run_button.configure(state="normal"))
        
        self.command_executor.execute_command_async(command_data, self.config, on_completion)
    
    def _toggle_conda(self) -> None:
        """Handle conda checkbox toggle."""
        if self.conda_var.get():
            self.conda_combo.configure(state="normal")
            self.docker_var.set(False)
            self.docker_combo.configure(state="disabled")
            self.volume_mounts_entry.configure(state="disabled")
            self.volume_mounts_entry.delete(0, "end")
        else:
            self.conda_combo.configure(state="disabled")
            self.conda_combo.set('')
        
        if self.current_command_id:
            self._save_command_data()
    
    def _toggle_docker(self) -> None:
        """Handle docker checkbox toggle."""
        if self.docker_var.get():
            self.docker_combo.configure(state="normal")
            self.volume_mounts_entry.configure(state="normal")
            self.conda_var.set(False)
            self.conda_combo.configure(state="disabled")
            self.conda_combo.set('')
            # Update volume mounts when Docker is enabled
            self._update_volume_mounts()
        else:
            self.docker_combo.configure(state="disabled")
            self.docker_combo.set('')
            self.volume_mounts_entry.configure(state="disabled")
            self.volume_mounts_entry.delete(0, "end")
        
        if self.current_command_id:
            self._save_command_data()
    
    def _update_volume_mounts(self) -> None:
        """Update volume mounts based on command and configuration."""
        if self.docker_var.get():
            command = self.command_entry.get()
            
            # Combine fixed mounts, inferred mounts, and existing volume mounts
            all_mounts = []
            
            # Add fixed mounts from configuration
            fixed_mounts = self.config.get('fixed_docker_mounts', [])
            all_mounts.extend(fixed_mounts)
            
            # Add inferred mounts
            inferred_mounts = self.command_executor.infer_docker_mounts(command)
            if inferred_mounts:
                all_mounts.extend(inferred_mounts.split())
            
            # Update the volume mounts field
            mounts_str = ' '.join(all_mounts)
            self.volume_mounts_entry.delete(0, "end")
            self.volume_mounts_entry.insert(0, mounts_str)
    
    # Event handlers for form changes
    def _on_name_change(self, event) -> None:
        """Handle name change."""
        if self.current_command_id:
            new_name = self.name_entry.get()
            self.commands[self.current_command_id]['name'] = new_name
            self._update_commands_list()
            self.data_manager.save_commands(self.commands)
    
    def _on_command_change(self, event) -> None:
        """Handle command text change."""
        if self.docker_var.get():
            self._update_volume_mounts()
        
        if self.current_command_id:
            self._save_command_data()
    
    def _on_conda_change(self, event) -> None:
        """Handle conda environment change."""
        if self.current_command_id:
            self._save_command_data()
    
    def _on_conda_selected(self, event) -> None:
        """Handle conda environment selection."""
        if self.current_command_id:
            self._save_command_data()
    
    def _on_docker_change(self, event) -> None:
        """Handle docker image change."""
        if self.current_command_id:
            self._save_command_data()
    
    def _on_docker_selected(self, event) -> None:
        """Handle docker image selection."""
        if self.current_command_id:
            self._save_command_data()
    
    def _on_volume_mounts_change(self, event) -> None:
        """Handle volume mounts change."""
        if self.current_command_id:
            self._save_command_data()
    
    def _show_config_dialog(self) -> None:
        """Show configuration dialog."""
        def save_config(new_config):
            self.config = new_config
            self.data_manager.save_config(self.config)
        
        dialog = ConfigDialog(self.root, self.config, save_config)
        dialog.show()
    
    def _show_cron_dialog(self) -> None:
        """Show cron export dialog."""
        if not self.current_command_id:
            messagebox.showwarning("No Command", "Please select a command to export to cron.")
            return
        
        command_data = self.commands[self.current_command_id]
        
        def prepare_command(cmd_data):
            return self.command_executor._prepare_command(cmd_data, self.config)
        
        dialog = CronExportDialog(self.root, command_data, prepare_command)
        dialog.show()
    
    def _on_closing(self) -> None:
        """Handle application closing."""
        if self.current_command_id:
            self._save_command_data()
        self.root.destroy()
