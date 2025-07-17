import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import json
import os
import platform
import re
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
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Left panel for commands list
        self.create_left_panel(main_frame)
        
        # Right panel for command editing
        self.create_right_panel(main_frame)
    
    def create_left_panel(self, parent):
        left_frame = ttk.Frame(parent)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=1)
        
        # Commands list label
        ttk.Label(left_frame, text="Commands", font=("Arial", 12, "bold")).grid(row=0, column=0, pady=(0, 10))
        
        # Commands listbox
        self.commands_listbox = tk.Listbox(left_frame, width=25)
        self.commands_listbox.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.commands_listbox.bind('<<ListboxSelect>>', self.on_command_select)
        
        # Buttons frame
        buttons_frame = ttk.Frame(left_frame)
        buttons_frame.grid(row=2, column=0, pady=(10, 0), sticky=(tk.W, tk.E))
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        
        # Add and Delete buttons
        ttk.Button(buttons_frame, text="Add", command=self.add_command).grid(row=0, column=0, padx=(0, 5), sticky=(tk.W, tk.E))
        ttk.Button(buttons_frame, text="Delete", command=self.delete_command).grid(row=0, column=1, padx=(5, 0), sticky=(tk.W, tk.E))
        
        self.update_commands_list()
    
    def create_right_panel(self, parent):
        right_frame = ttk.Frame(parent)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(4, weight=1)
        
        # Command name
        ttk.Label(right_frame, text="Command Name:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.name_entry = ttk.Entry(right_frame, width=50)
        self.name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        self.name_entry.bind('<KeyRelease>', self.on_name_change)
        
        # Command input
        ttk.Label(right_frame, text="Command:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.command_entry = ttk.Entry(right_frame, width=50)
        self.command_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        self.command_entry.bind('<KeyRelease>', self.on_command_change)
        
        # Execution options frame
        options_frame = ttk.LabelFrame(right_frame, text="Execution Options", padding="10")
        options_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        options_frame.columnconfigure(1, weight=1)
        
        # Conda environment option
        self.conda_var = tk.BooleanVar()
        self.conda_checkbox = ttk.Checkbutton(options_frame, text="Run in Conda Environment", 
                                             variable=self.conda_var, command=self.toggle_conda)
        self.conda_checkbox.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Create searchable combobox for conda environments
        conda_frame = ttk.Frame(options_frame)
        conda_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(0, 5))
        conda_frame.columnconfigure(0, weight=1)
        
        self.conda_combo = ttk.Combobox(conda_frame, values=self.conda_environments, state="disabled")
        self.conda_combo.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.conda_combo.bind('<KeyRelease>', self.filter_conda_environments)
        self.conda_combo.bind('<Button-1>', self.on_conda_click)
        self.conda_combo.bind('<<ComboboxSelected>>', self.on_conda_selected)
        self.conda_combo.bind('<FocusIn>', lambda e: self.conda_combo.select_range(0, tk.END))
        self.conda_combo.bind('<FocusOut>', self.on_conda_change)
        
        # Docker container option
        self.docker_var = tk.BooleanVar()
        self.docker_checkbox = ttk.Checkbutton(options_frame, text="Run in Docker Container", 
                                              variable=self.docker_var, command=self.toggle_docker)
        self.docker_checkbox.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        # Create searchable combobox for docker images
        docker_frame = ttk.Frame(options_frame)
        docker_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(0, 5))
        docker_frame.columnconfigure(0, weight=1)
        
        self.docker_combo = ttk.Combobox(docker_frame, values=self.docker_images, state="disabled")
        self.docker_combo.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.docker_combo.bind('<KeyRelease>', self.filter_docker_images)
        self.docker_combo.bind('<Button-1>', self.on_docker_click)
        self.docker_combo.bind('<<ComboboxSelected>>', self.on_docker_selected)
        self.docker_combo.bind('<FocusIn>', lambda e: self.docker_combo.select_range(0, tk.END))
        self.docker_combo.bind('<FocusOut>', self.on_docker_change)
        
        # Volume mounts
        ttk.Label(options_frame, text="Volume Mounts:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        self.volume_mounts_entry = ttk.Entry(options_frame, state="disabled")
        self.volume_mounts_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(5, 0))
        self.volume_mounts_entry.bind('<KeyRelease>', self.on_volume_mounts_change)
        self.volume_mounts_entry.bind('<FocusOut>', self.on_volume_mounts_change)
        
        # Buttons frame (Run Command and Config)
        buttons_frame = ttk.Frame(right_frame)
        buttons_frame.grid(row=3, column=0, columnspan=3, pady=(20, 10))
        
        self.run_button = ttk.Button(buttons_frame, text="Run Command", command=self.run_command)
        self.run_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(buttons_frame, text="Config", command=self.show_config_dialog).pack(side=tk.LEFT)
        
        # Output area
        output_frame = ttk.LabelFrame(right_frame, text="Output", padding="5")
        output_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure column weights
        right_frame.columnconfigure(1, weight=1)
        right_frame.rowconfigure(4, weight=1)
    
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
            self.conda_combo.config(state="normal")
            self.docker_var.set(False)
            self.docker_combo.config(state="disabled")
            self.volume_mounts_entry.config(state="disabled")
            self.volume_mounts_entry.delete(0, tk.END)
        else:
            self.conda_combo.config(state="disabled")
            self.conda_combo.set('')
        
        if self.current_command_id:
            self.save_command_data()
    
    def toggle_docker(self):
        """Handle docker checkbox toggle"""
        if self.docker_var.get():
            self.docker_combo.config(state="normal")
            self.volume_mounts_entry.config(state="normal")
            self.conda_var.set(False)
            self.conda_combo.config(state="disabled")
            self.conda_combo.set('')
            # Update volume mounts when Docker is enabled
            self.update_volume_mounts()
        else:
            self.docker_combo.config(state="disabled")
            self.docker_combo.set('')
            self.volume_mounts_entry.config(state="disabled")
            self.volume_mounts_entry.delete(0, tk.END)
        
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
            'volume_mounts': ''
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
    
    def update_commands_list(self):
        """Update the commands listbox"""
        self.commands_listbox.delete(0, tk.END)
        for command_id, command_data in self.commands.items():
            self.commands_listbox.insert(tk.END, command_data['name'])
    
    def on_command_select(self, event):
        """Handle command selection"""
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            command_id = list(self.commands.keys())[index]
            self.load_command(command_id)
    
    def load_command(self, command_id):
        """Load command data into the form"""
        if command_id in self.commands:
            self.current_command_id = command_id
            command_data = self.commands[command_id]
            
            # Load basic data
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, command_data['name'])
            
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, command_data['command'])
            
            # Load conda settings
            self.conda_var.set(command_data['use_conda'])
            if command_data['use_conda']:
                self.conda_combo.config(state="normal")
                self.conda_combo.set(command_data['conda_env'])
                self.volume_mounts_entry.config(state="disabled")
            else:
                self.conda_combo.config(state="disabled")
                self.conda_combo.set('')
            
            # Load docker settings
            self.docker_var.set(command_data['use_docker'])
            if command_data['use_docker']:
                self.docker_combo.config(state="normal")
                self.docker_combo.set(command_data['docker_image'])
                self.volume_mounts_entry.config(state="normal")
                
                # Load volume mounts (backward compatibility)
                volume_mounts = command_data.get('volume_mounts', command_data.get('additional_mounts', ''))
                self.volume_mounts_entry.delete(0, tk.END)
                self.volume_mounts_entry.insert(0, volume_mounts)
            else:
                self.docker_combo.config(state="disabled")
                self.docker_combo.set('')
                self.volume_mounts_entry.config(state="disabled")
                self.volume_mounts_entry.delete(0, tk.END)
    
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
        self.name_entry.delete(0, tk.END)
        self.command_entry.delete(0, tk.END)
        self.conda_var.set(False)
        self.docker_var.set(False)
        self.conda_combo.config(state="disabled")
        self.docker_combo.config(state="disabled")
        self.volume_mounts_entry.config(state="disabled")
        self.volume_mounts_entry.delete(0, tk.END)
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
    
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
        
        # Clear output
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        
        # Disable run button
        self.run_button.config(state="disabled")
        
        # Prepare command based on execution options
        final_command = self.prepare_command(command_data)
        
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
            self.root.after(0, lambda: self.run_button.config(state="normal"))
    
    def update_output(self, text):
        """Update output text widget"""
        def update():
            self.output_text.config(state=tk.NORMAL)
            self.output_text.insert(tk.END, text)
            self.output_text.see(tk.END)
            self.output_text.config(state=tk.DISABLED)
        
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
            self.volume_mounts_entry.delete(0, tk.END)
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
        config_window = tk.Toplevel(self.root)
        config_window.title("Configuration")
        config_window.geometry("500x300")
        config_window.transient(self.root)
        config_window.grab_set()
        
        # Fixed docker mounts section
        ttk.Label(config_window, text="Fixed Docker Mounts:", font=("Arial", 10, "bold")).pack(pady=(10, 5))
        
        # Frame for mounts list
        mounts_frame = ttk.Frame(config_window)
        mounts_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Listbox for mounts
        mounts_listbox = tk.Listbox(mounts_frame)
        mounts_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar for listbox
        scrollbar = ttk.Scrollbar(mounts_frame, orient=tk.VERTICAL, command=mounts_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        mounts_listbox.config(yscrollcommand=scrollbar.set)
        
        # Load current fixed mounts
        for mount in self.config.get('fixed_docker_mounts', []):
            mounts_listbox.insert(tk.END, mount)
        
        # Entry for new mount
        entry_frame = ttk.Frame(config_window)
        entry_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(entry_frame, text="Add mount:").pack(side=tk.LEFT)
        mount_entry = ttk.Entry(entry_frame)
        mount_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        mount_entry.insert(0, "-v /path/on/host:/path/in/container")
        
        # Buttons frame
        buttons_frame = ttk.Frame(config_window)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def add_mount():
            mount = mount_entry.get().strip()
            if mount:
                mounts_listbox.insert(tk.END, mount)
                mount_entry.delete(0, tk.END)
                mount_entry.insert(0, "-v /path/on/host:/path/in/container")
        
        def remove_mount():
            selection = mounts_listbox.curselection()
            if selection:
                mounts_listbox.delete(selection[0])
        
        def save_and_close():
            # Save fixed mounts
            fixed_mounts = []
            for i in range(mounts_listbox.size()):
                fixed_mounts.append(mounts_listbox.get(i))
            
            self.config['fixed_docker_mounts'] = fixed_mounts
            self.save_config()
            config_window.destroy()
        
        ttk.Button(buttons_frame, text="Add", command=add_mount).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="Remove", command=remove_mount).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="Save & Close", command=save_and_close).pack(side=tk.RIGHT)
        
        mount_entry.bind('<Return>', lambda e: add_mount())


def main():
    root = tk.Tk()
    app = CommandWallet(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
