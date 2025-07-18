import customtkinter as ctk
from tkinter import messagebox
import subprocess
import threading
import json
import os
import platform
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional


class CommandWallet:
    def maximize_window(self):
        system = platform.system()
        if system == "Windows":
            self.root.state('zoomed')
        elif system == "Darwin":  # macOS
            # No hay un método perfecto, pero esto ayuda
            self.root.attributes('-zoomed', True)
            # O bien: self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        else:  # Linux y otros
            try:
                self.root.attributes('-zoomed', True)
            except:
                # Si falla, usa tamaño grande por defecto
                self.root.geometry("1200x800")

    def __init__(self, root):
        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

        self.root = root
        self.root.title("CommandWallet")
        self.maximize_window()
        
        # Data storage
        self.commands = {}
        self.current_command_id = None
        
        # Create config directory in user home
        self.config_dir = os.path.join(os.path.expanduser("~"), ".command-wallet")
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        self.data_file = os.path.join(self.config_dir, "commands.json")
        self.config_file = os.path.join(self.config_dir, "config.json")
        
        # Load configuration
        self.config = self.load_config()
        
        # Load saved commands
        self.load_commands()
        
        # Initialize conda environments and docker images
        self.conda_environments = self.get_conda_environments()
        self.docker_images = self.get_docker_images()
        
        # Create GUI
        self.create_widgets()
        
        # Load first command if any
        if self.commands:
            first_id = list(self.commands.keys())[0]
            self.load_command(first_id)
    
    def create_widgets(self):
        # Configure fonts - CustomTkinter handles fonts differently
        self.font_size = 14
        
        # Main container
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configure grid weights
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Left panel for commands list
        self.create_left_panel(main_frame)
        
        # Right panel for command editing
        self.create_right_panel(main_frame)
    
    def create_left_panel(self, parent):
        left_frame = ctk.CTkFrame(parent)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(2, weight=1)
        
        # Commands list label
        ctk.CTkLabel(left_frame, text="Commands", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, pady=(10, 5), padx=10)
        
        # Sorting buttons frame
        sort_frame = ctk.CTkFrame(left_frame)
        sort_frame.grid(row=1, column=0, pady=(0, 10), padx=10, sticky="ew")
        sort_frame.grid_columnconfigure(0, weight=1)
        sort_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkButton(sort_frame, text="Sort by Name", command=self.sort_by_name).grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        ctk.CTkButton(sort_frame, text="Sort by Date", command=self.sort_by_date).grid(row=0, column=1, padx=(5, 10), pady=10, sticky="ew")
        
        # Commands listbox - CustomTkinter doesn't have Listbox, so we'll use CTkScrollableFrame
        self.commands_frame = ctk.CTkScrollableFrame(left_frame, label_text="Commands List")
        self.commands_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.commands_frame.grid_columnconfigure(0, weight=1)
        
        # Store command buttons for later reference
        self.command_buttons = []
        
        # Add/Delete buttons frame
        buttons_frame = ctk.CTkFrame(left_frame)
        buttons_frame.grid(row=3, column=0, pady=(0, 10), padx=10, sticky="ew")
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        
        # Add and Delete buttons
        ctk.CTkButton(buttons_frame, text="Add", command=self.add_command).grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        ctk.CTkButton(buttons_frame, text="Delete", command=self.delete_command).grid(row=0, column=1, padx=(5, 10), pady=10, sticky="ew")
        
        self.update_commands_list()
    
    def create_right_panel(self, parent):
        right_frame = ctk.CTkFrame(parent)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        right_frame.grid_columnconfigure(1, weight=1)
        right_frame.grid_rowconfigure(4, weight=1)
        
        # Command name
        ctk.CTkLabel(right_frame, text="Name:", font=ctk.CTkFont(size=14)).grid(row=0, column=0, sticky="w", pady=(10, 5), padx=(10, 5))
        self.name_entry = ctk.CTkEntry(right_frame, font=ctk.CTkFont(family="Consolas", size=12))
        self.name_entry.grid(row=0, column=1, sticky="ew", pady=(10, 5), padx=(0, 10))
        self.name_entry.bind('<KeyRelease>', self.on_name_change)
        
        # Command input
        ctk.CTkLabel(right_frame, text="Command:", font=ctk.CTkFont(size=14)).grid(row=1, column=0, sticky="w", pady=(5, 5), padx=(10, 5))
        self.command_entry = ctk.CTkEntry(right_frame, font=ctk.CTkFont(family="Consolas", size=12))
        self.command_entry.grid(row=1, column=1, sticky="ew", pady=(5, 5), padx=(0, 10))
        self.command_entry.bind('<KeyRelease>', self.on_command_change)
        
        # Execution options frame
        options_frame = ctk.CTkFrame(right_frame)
        options_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 5), padx=10)
        options_frame.grid_columnconfigure(1, weight=1)
        
        # Add label for the options section
        ctk.CTkLabel(options_frame, text="Execution Options", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(10, 10), padx=10, sticky="w")
        
        # Conda environment option
        self.conda_var = ctk.BooleanVar()
        self.conda_checkbox = ctk.CTkCheckBox(options_frame, text="Run in Conda Environment", 
                                             variable=self.conda_var, command=self.toggle_conda)
        self.conda_checkbox.grid(row=1, column=0, sticky="w", pady=(0, 10), padx=(10, 10))
        
        # Create frame for conda environments combo
        conda_frame = ctk.CTkFrame(options_frame)
        conda_frame.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 10))
        conda_frame.grid_columnconfigure(0, weight=1)
        
        self.conda_combo = ctk.CTkComboBox(conda_frame, values=self.conda_environments, state="disabled")
        self.conda_combo.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.conda_combo.bind('<KeyRelease>', self.filter_conda_environments)
        self.conda_combo.bind('<Button-1>', self.on_conda_click)
        self.conda_combo.bind('<<ComboboxSelected>>', self.on_conda_selected)
        self.conda_combo.bind('<FocusOut>', self.on_conda_change)
        
        # Docker container option
        self.docker_var = ctk.BooleanVar()
        self.docker_checkbox = ctk.CTkCheckBox(options_frame, text="Run in Docker Container", 
                                              variable=self.docker_var, command=self.toggle_docker)
        self.docker_checkbox.grid(row=2, column=0, sticky="w", pady=(0, 10), padx=(10, 10))
        
        # Create frame for docker images combo
        docker_frame = ctk.CTkFrame(options_frame)
        docker_frame.grid(row=2, column=1, sticky="ew", padx=(0, 10), pady=(0, 10))
        docker_frame.grid_columnconfigure(0, weight=1)
        
        self.docker_combo = ctk.CTkComboBox(docker_frame, values=self.docker_images, state="disabled")
        self.docker_combo.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.docker_combo.bind('<KeyRelease>', self.filter_docker_images)
        self.docker_combo.bind('<Button-1>', self.on_docker_click)
        self.docker_combo.bind('<<ComboboxSelected>>', self.on_docker_selected)
        self.docker_combo.bind('<FocusOut>', self.on_docker_change)
        
        # Volume mounts
        ctk.CTkLabel(options_frame, text="Volume Mounts:", font=ctk.CTkFont(size=12)).grid(row=3, column=0, sticky="w", pady=(5, 10), padx=(10, 10))
        self.volume_mounts_entry = ctk.CTkEntry(options_frame, state="disabled")
        self.volume_mounts_entry.grid(row=3, column=1, sticky="ew", padx=(0, 10), pady=(5, 10))
        self.volume_mounts_entry.bind('<KeyRelease>', self.on_volume_mounts_change)
        self.volume_mounts_entry.bind('<FocusOut>', self.on_volume_mounts_change)
        
        # Buttons frame (Run Command and Config)
        buttons_frame = ctk.CTkFrame(right_frame)
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=(20, 10), padx=10)
        
        self.run_button = ctk.CTkButton(buttons_frame, text="Run Command", command=self.run_command)
        self.run_button.pack(side="left", padx=(10, 10), pady=10)
        
        ctk.CTkButton(buttons_frame, text="Config", command=self.show_config_dialog).pack(side="left", padx=(0, 10), pady=10)
        
        # Output area
        output_frame = ctk.CTkFrame(right_frame)
        output_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(5, 10), padx=10)
        output_frame.grid_columnconfigure(0, weight=1)
        output_frame.grid_rowconfigure(1, weight=1)
        
        # Output label
        ctk.CTkLabel(output_frame, text="Output", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w", pady=(10, 5), padx=10)
        
        # Output text area - CustomTkinter doesn't have ScrolledText, so we'll use CTkTextbox
        self.output_text = ctk.CTkTextbox(output_frame, wrap="word", state="disabled", font=ctk.CTkFont(family="Consolas", size=11))
        self.output_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Add right-click context menu to output text
        self.create_output_context_menu()
        
        # Configure column weights
        right_frame.columnconfigure(1, weight=1)
        right_frame.rowconfigure(4, weight=1)
    
    def create_output_context_menu(self):
        """Create right-click context menu for output text area"""
        # Import tkinter for Menu (CustomTkinter doesn't have context menus yet)
        import tkinter as tk
        
        # Create context menu
        self.output_menu = tk.Menu(self.root, tearoff=0)
        self.output_menu.add_command(label="Copy All", command=self.copy_all_output)
        self.output_menu.add_command(label="Copy Selection", command=self.copy_selected_output)
        self.output_menu.add_separator()
        self.output_menu.add_command(label="Clear Output", command=self.clear_output)
        
        # Bind right-click to show menu
        self.output_text.bind("<Button-3>", self.show_output_context_menu)  # Right-click
        
        # Also bind Ctrl+C for copy selection
        self.output_text.bind("<Control-c>", lambda e: self.copy_selected_output())
        self.output_text.bind("<Control-a>", lambda e: self.select_all_output())
    
    def show_output_context_menu(self, event):
        """Show context menu at cursor position"""
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
            # Hide menu after a while if not interacted with
            self.output_menu.grab_release()
    
    def copy_all_output(self):
        """Copy all output text to clipboard"""
        try:
            text = self.output_text.get("1.0", "end-1c")
            if text.strip():
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self.root.update()  # Required for clipboard to work properly
                # Show brief status message
                self.show_status_message("All output copied to clipboard")
        except Exception as e:
            print(f"Error copying all output: {e}")
    
    def copy_selected_output(self):
        """Copy selected output text to clipboard"""
        try:
            if self.output_text.tag_ranges("sel"):
                selected_text = self.output_text.get("sel.first", "sel.last")
                if selected_text:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(selected_text)
                    self.root.update()  # Required for clipboard to work properly
                    # Show brief status message
                    self.show_status_message("Selected text copied to clipboard")
            else:
                self.show_status_message("No text selected")
        except Exception as e:
            print(f"Error copying selected output: {e}")
    
    def show_status_message(self, message):
        """Show a brief status message in the output area"""
        try:
            # Temporarily enable the text widget
            self.output_text.configure(state="normal")
            
            # Add status message with a timestamp
            current_text = self.output_text.get("1.0", "end-1c")
            if current_text and not current_text.endswith('\n'):
                self.output_text.insert("end", "\n")
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            status_line = f"[{timestamp}] {message}\n"
            self.output_text.insert("end", status_line)
            self.output_text.see("end")
            
            # Disable the text widget again
            self.output_text.configure(state="disabled")
        except Exception as e:
            print(f"Error showing status message: {e}")
    
    def select_all_output(self):
        """Select all text in output area"""
        try:
            self.output_text.tag_add("sel", "1.0", "end")
            return "break"  # Prevent default behavior
        except Exception as e:
            print(f"Error selecting all output: {e}")
    
    def clear_output(self):
        """Clear all output text"""
        try:
            self.output_text.configure(state="normal")
            self.output_text.delete("1.0", "end")
            self.output_text.configure(state="disabled")
            # Note: We can't show a status message here since we just cleared everything
        except Exception as e:
            print(f"Error clearing output: {e}")
    
    def get_conda_environments(self) -> List[str]:
        """Get list of available conda environments"""
        try:
            result = subprocess.run(['conda', 'env', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                environments = []
                for line in result.stdout.split('\n'):
                    if line.strip() and not line.startswith('#'):
                        parts = line.split()
                        if parts:
                            env_name = parts[0]
                            if env_name != 'base':
                                environments.append(env_name)
                return ['base'] + environments
            return []
        except FileNotFoundError:
            return []
    
    def get_docker_images(self) -> List[str]:
        """Get list of available docker images"""
        try:
            result = subprocess.run(['docker', 'images', '--format', '{{.Repository}}:{{.Tag}}'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                images = []
                for line in result.stdout.split('\n'):
                    if line.strip() and not line.startswith('<none>'):
                        images.append(line.strip())
                return images
            return []
        except FileNotFoundError:
            return []
    
    def toggle_conda(self):
        """Handle conda checkbox toggle"""
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
            self.save_command_data()
    
    def toggle_docker(self):
        """Handle docker checkbox toggle"""
        if self.docker_var.get():
            self.docker_combo.configure(state="normal")
            self.volume_mounts_entry.configure(state="normal")
            self.conda_var.set(False)
            self.conda_combo.configure(state="disabled")
            self.conda_combo.set('')
            # Update volume mounts when Docker is enabled
            self.update_volume_mounts()
        else:
            self.docker_combo.configure(state="disabled")
            self.docker_combo.set('')
            self.volume_mounts_entry.configure(state="disabled")
            self.volume_mounts_entry.delete(0, "end")
        
        if self.current_command_id:
            self.save_command_data()

    def add_command(self):
        """Add a new command"""
        command_id = f"cmd_{len(self.commands) + 1}"
        self.commands[command_id] = {
            'name': f'New Command {len(self.commands) + 1}',
            'command': '',
            'use_conda': False,
            'conda_env': '',
            'use_docker': False,
            'docker_image': '',
            'volume_mounts': '',
            'last_execution': None
        }
        self.update_commands_list()
        self.load_command(command_id)
        self.save_commands()
    
    def delete_command(self):
        """Delete selected command"""
        if self.current_command_id and self.current_command_id in self.commands:
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this command?"):
                del self.commands[self.current_command_id]
                self.update_commands_list()
                self.clear_form()
                self.save_commands()
    
    def update_commands_list(self, sort_by=None):
        """Update the commands list in the scrollable frame"""
        # Clear existing buttons
        for button in self.command_buttons:
            button.destroy()
        self.command_buttons.clear()
        
        if sort_by == 'name':
            # Sort by name alphabetically
            sorted_commands = sorted(self.commands.items(), key=lambda item: item[1]['name'].lower())
        elif sort_by == 'date':
            # Sort by last execution date (most recent first), commands without date go to end
            def get_sort_key(item):
                last_exec = item[1].get('last_execution')
                if last_exec is None:
                    return '1970-01-01 00:00:00'  # Never executed commands go to end
                return last_exec
            
            sorted_commands = sorted(
                self.commands.items(), 
                key=get_sort_key,
                reverse=True
            )
        else:
            # Default order (by command ID)
            sorted_commands = self.commands.items()
        
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
            self.create_tooltip(button, command_data)
    
    def create_tooltip(self, widget, command_data):
        """Create tooltip for command button showing last execution date"""
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
            
            label = ctk.CTkLabel(self.tooltip, text=tooltip_text, 
                               font=ctk.CTkFont(size=10))
            label.pack()
        
        def on_leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
                delattr(self, 'tooltip')
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def sort_by_name(self):
        """Sort commands by name"""
        self.update_commands_list(sort_by='name')
    
    def sort_by_date(self):
        """Sort commands by last execution date"""
        self.update_commands_list(sort_by='date')

    def load_command(self, command_id):
        """Load command data into the form"""
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
    
    def on_name_change(self, event):
        """Handle name change"""
        if self.current_command_id:
            new_name = self.name_entry.get()
            self.commands[self.current_command_id]['name'] = new_name
            self.update_commands_list()
            self.save_commands()
    
    def clear_form(self):
        """Clear the form"""
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
    
    def save_command_data(self):
        """Save current command data"""
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
            self.save_commands()
    
    def run_command(self):
        """Run the selected command"""
        if not self.current_command_id:
            messagebox.showwarning("No Command", "Please select a command to run.")
            return
        
        # Save current data
        self.save_command_data()
        
        command_data = self.commands[self.current_command_id]
        command = command_data['command'].strip()
        
        if not command:
            messagebox.showwarning("Empty Command", "Please enter a command to run.")
            return
        
        # Save execution timestamp
        execution_time = datetime.now()
        timestamp_str = execution_time.strftime("%d/%m/%Y-%H:%M:%S")
        self.commands[self.current_command_id]['last_execution'] = execution_time.strftime("%Y-%m-%d %H:%M:%S")
        self.save_commands()
        
        # Prepare command based on execution options
        final_command = self.prepare_command(command_data)
        
        # Clear output and add starting message
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", f"Started command '{final_command}' at {timestamp_str}\n\n")
        self.output_text.configure(state="disabled")
        
        # Disable run button
        self.run_button.configure(state="disabled")
        
        # Run command in separate thread
        thread = threading.Thread(target=self.execute_command, args=(final_command,))
        thread.daemon = True
        thread.start()
    
    def prepare_command(self, command_data):
        """Prepare the final command based on execution options"""
        command = command_data['command']
        
        if command_data['use_conda'] and command_data['conda_env']:
            # Run in conda environment
            return f"conda run -n {command_data['conda_env']} {command}"
        elif command_data['use_docker'] and command_data['docker_image']:
            # Run in docker container
            # Use volume mounts from the command data (backward compatibility)
            volume_mounts = command_data.get('volume_mounts', command_data.get('additional_mounts', ''))
            
            # If no volume mounts specified, try to infer and add fixed mounts
            if not volume_mounts:
                all_mounts = []
                
                # Add fixed mounts from configuration
                fixed_mounts = self.config.get('fixed_docker_mounts', [])
                all_mounts.extend(fixed_mounts)
                
                # Add inferred mounts
                inferred_mounts = self.infer_docker_mounts(command)
                if inferred_mounts:
                    all_mounts.extend(inferred_mounts.split())
                
                volume_mounts = ' '.join(all_mounts)
            
            return f"docker run --rm -it {volume_mounts} {command_data['docker_image']} {command}"
        else:
            # Run directly
            return command
    
    def execute_command(self, command):
        """Execute command and update output"""
        try:
            # Start process
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read output line by line
            for line in iter(process.stdout.readline, ''):
                self.update_output(line)
            
            process.wait()
            
            # Show completion message
            if process.returncode == 0:
                self.update_output(f"\n--- Command completed successfully (exit code: {process.returncode}) ---\n")
            else:
                self.update_output(f"\n--- Command failed (exit code: {process.returncode}) ---\n")
                
        except Exception as e:
            self.update_output(f"\nError executing command: {str(e)}\n")
        finally:
            # Re-enable run button
            self.root.after(0, lambda: self.run_button.configure(state="normal"))
    
    def update_output(self, text):
        """Update output text widget"""
        def update():
            self.output_text.configure(state="normal")
            self.output_text.insert("end", text)
            self.output_text.see("end")
            self.output_text.configure(state="disabled")
        
        self.root.after(0, update)
    
    def load_commands(self):
        """Load commands from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.commands = json.load(f)
                # Migrate old data format if necessary
                self.migrate_command_data()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load commands: {str(e)}")
            self.commands = {}
    
    def save_commands(self):
        """Save commands to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.commands, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save commands: {str(e)}")
    
    def on_closing(self):
        """Handle application closing"""
        if self.current_command_id:
            self.save_command_data()
        self.root.destroy()

    def filter_conda_environments(self, event):
        """Filter conda environments based on typed text"""
        current_text = event.widget.get()
        typed_text = current_text.lower()
        
        if not typed_text:
            self.conda_combo['values'] = self.conda_environments
            return
        
        # Check if the current text is an exact match (user selected from dropdown)
        if current_text in self.conda_environments:
            return
        
        filtered = [env for env in self.conda_environments if typed_text in env.lower()]
        self.conda_combo['values'] = filtered
        
        # If no matches, show all environments
        if not filtered:
            self.conda_combo['values'] = self.conda_environments
    
    def filter_docker_images(self, event):
        """Filter docker images based on typed text"""
        current_text = event.widget.get()
        typed_text = current_text.lower()
        
        if not typed_text:
            self.docker_combo['values'] = self.docker_images
            return
        
        # Check if the current text is an exact match (user selected from dropdown)
        if current_text in self.docker_images:
            return
        
        filtered = [img for img in self.docker_images if typed_text in img.lower()]
        self.docker_combo['values'] = filtered
        
        # If no matches, show all images
        if not filtered:
            self.docker_combo['values'] = self.docker_images
    
    def infer_docker_mounts(self, command: str) -> str:
        """Infer Docker mounts from command paths"""
        if not command:
            return ""
        
        # Find absolute paths in the command
        path_patterns = [
            r'(?:^|\s)(/[^\s]+)',  # Absolute paths starting with /
            r'(?:^|\s)(\$\w+/[^\s]+)',  # Paths with environment variables
            r'(?:^|\s)(~[^\s]*)',  # Paths starting with ~
        ]
        
        paths = []
        for pattern in path_patterns:
            matches = re.findall(pattern, command)
            for match in matches:
                # Expand ~ to home directory
                if match.startswith('~'):
                    match = os.path.expanduser(match)
                # Skip if it's likely a flag or option
                if not match.startswith('-') and '=' not in match:
                    paths.append(match)
        
        if not paths:
            return ""
        
        # Find common parent directories
        mount_dirs = set()
        for path in paths:
            if os.path.isfile(path):
                mount_dirs.add(os.path.dirname(path))
            elif os.path.isdir(path):
                mount_dirs.add(path)
            else:
                # If path doesn't exist, try to infer parent directory
                parent = os.path.dirname(path)
                if parent and parent != '/':
                    mount_dirs.add(parent)
        
        # Create mount strings
        mounts = []
        for mount_dir in sorted(mount_dirs):
            mounts.append(f"-v {mount_dir}:{mount_dir}")
        
        return " ".join(mounts)
    
    def update_volume_mounts(self):
        """Update volume mounts based on command and configuration"""
        if self.docker_var.get():
            command = self.command_entry.get()
            
            # Combine fixed mounts, inferred mounts, and existing volume mounts
            all_mounts = []
            
            # Add fixed mounts from configuration
            fixed_mounts = self.config.get('fixed_docker_mounts', [])
            all_mounts.extend(fixed_mounts)
            
            # Add inferred mounts
            inferred_mounts = self.infer_docker_mounts(command)
            if inferred_mounts:
                all_mounts.extend(inferred_mounts.split())
            
            # Update the volume mounts field
            mounts_str = ' '.join(all_mounts)
            self.volume_mounts_entry.delete(0, "end")
            self.volume_mounts_entry.insert(0, mounts_str)
    
    def on_command_change(self, event):
        """Handle command text change to update volume mounts and save data"""
        if self.docker_var.get():
            self.update_volume_mounts()
        
        if self.current_command_id:
            self.save_command_data()

    def on_conda_change(self, event):
        """Handle conda environment change to save data"""
        if self.current_command_id:
            self.save_command_data()

    def on_docker_change(self, event):
        """Handle docker image change to save data"""
        if self.current_command_id:
            self.save_command_data()

    def on_volume_mounts_change(self, event):
        """Handle volume mounts change to save data"""
        if self.current_command_id:
            self.save_command_data()

    def on_conda_selected(self, event):
        """Handle conda environment selection to save data"""
        if self.current_command_id:
            self.save_command_data()

    def on_docker_selected(self, event):
        """Handle docker image selection to save data"""
        if self.current_command_id:
            self.save_command_data()

    def on_conda_click(self, event):
        """Handle conda combobox click to reset values"""
        if self.conda_combo['state'] == 'normal':
            self.conda_combo['values'] = self.conda_environments

    def on_docker_click(self, event):
        """Handle docker combobox click to reset values"""
        if self.docker_combo['state'] == 'normal':
            self.docker_combo['values'] = self.docker_images
    
    def migrate_command_data(self):
        """Migrate old command data to new format"""
        for command_id, command_data in self.commands.items():
            # Migrate from 'docker_mounts' to 'volume_mounts'
            if 'docker_mounts' in command_data:
                docker_mounts = command_data.get('docker_mounts', '')
                home_mount = f"-v {os.path.expanduser('~')}:{os.path.expanduser('~')}"
                
                if docker_mounts == home_mount:
                    command_data['volume_mounts'] = ''
                else:
                    command_data['volume_mounts'] = docker_mounts
                
                # Remove old field
                del command_data['docker_mounts']
            
            # Migrate from 'additional_mounts' to 'volume_mounts'
            elif 'additional_mounts' in command_data:
                command_data['volume_mounts'] = command_data.get('additional_mounts', '')
                # Remove old field
                del command_data['additional_mounts']
            
            # Ensure volume_mounts field exists
            if 'volume_mounts' not in command_data:
                command_data['volume_mounts'] = ''
            
            # Ensure last_execution field exists
            if 'last_execution' not in command_data:
                command_data['last_execution'] = None
        
        # Save migrated data
        self.save_commands()
    
    def load_config(self) -> Dict:
        """Load configuration from JSON file"""
        default_config = {
            'fixed_docker_mounts': []
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with default config
                    default_config.update(config)
        except Exception as e:
            print(f"Error loading config: {e}")
        
        return default_config
    
    def save_config(self):
        """Save configuration to JSON file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {str(e)}")

    def show_config_dialog(self):
        """Show configuration dialog"""
        config_window = ctk.CTkToplevel(self.root)
        config_window.title("Configuration")
        config_window.geometry("600x500")
        config_window.transient(self.root)
        
        # Wait for window to be fully created before grabbing focus
        config_window.after(100, lambda: config_window.grab_set())
        
        # Fixed docker mounts section
        ctk.CTkLabel(config_window, text="Fixed Docker Mounts:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 10))
        
        # Frame for mounts list
        mounts_frame = ctk.CTkFrame(config_window)
        mounts_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Scrollable frame for mounts (CustomTkinter doesn't have Listbox)
        mounts_scrollable = ctk.CTkScrollableFrame(mounts_frame, label_text="Current Mounts")
        mounts_scrollable.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Store mount data and widgets
        mount_vars = []
        mount_frames = []
        
        def refresh_mounts():
            # Clear existing widgets
            for frame in mount_frames:
                frame.destroy()
            mount_frames.clear()
            mount_vars.clear()
            
            # Add current mounts with delete buttons
            for i, mount in enumerate(self.config.get('fixed_docker_mounts', [])):
                mount_frame = ctk.CTkFrame(mounts_scrollable)
                mount_frame.pack(fill="x", padx=5, pady=2)
                mount_frames.append(mount_frame)
                
                # Mount text
                mount_label = ctk.CTkLabel(mount_frame, text=mount, anchor="w")
                mount_label.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=5)
                
                # Delete button
                def make_delete_command(index):
                    return lambda: delete_mount(index)
                
                delete_btn = ctk.CTkButton(mount_frame, text="✕", width=30, height=25, 
                                         command=make_delete_command(i), fg_color="red", hover_color="darkred")
                delete_btn.pack(side="right", padx=(5, 10), pady=5)
        
        def delete_mount(index):
            if 0 <= index < len(self.config.get('fixed_docker_mounts', [])):
                self.config['fixed_docker_mounts'].pop(index)
                refresh_mounts()
        
        refresh_mounts()
        
        # Entry for new mount
        entry_frame = ctk.CTkFrame(config_window)
        entry_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(entry_frame, text="Add new mount:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=10, pady=(10, 5))
        
        mount_entry_frame = ctk.CTkFrame(entry_frame)
        mount_entry_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        mount_entry = ctk.CTkEntry(mount_entry_frame, placeholder_text="-v /host/path:/container/path")
        mount_entry.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)
        
        add_button = ctk.CTkButton(mount_entry_frame, text="Add", width=60, command=lambda: add_mount())
        add_button.pack(side="right", padx=(5, 10), pady=10)
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(config_window)
        buttons_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        def add_mount():
            mount = mount_entry.get().strip()
            if mount:
                if 'fixed_docker_mounts' not in self.config:
                    self.config['fixed_docker_mounts'] = []
                self.config['fixed_docker_mounts'].append(mount)
                mount_entry.delete(0, "end")
                refresh_mounts()
        
        def save_and_close():
            self.save_config()
            config_window.destroy()
        
        def cancel():
            config_window.destroy()
        
        # Control buttons
        ctk.CTkButton(buttons_frame, text="Save & Close", command=save_and_close).pack(side="right", padx=(5, 10), pady=10)
        ctk.CTkButton(buttons_frame, text="Cancel", command=cancel, fg_color="gray", hover_color="darkgray").pack(side="right", padx=(5, 5), pady=10)
        
        # Bind Enter key to add mount
        mount_entry.bind('<Return>', lambda e: add_mount())
        
        # Focus on entry field
        config_window.after(200, lambda: mount_entry.focus())


def main():
    root = ctk.CTk()
    app = CommandWallet(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
