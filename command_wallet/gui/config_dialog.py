"""
Configuration dialog module for CommandWallet.

Provides a dialog for managing application configuration,
particularly Docker mount settings.
"""

import customtkinter as ctk
from typing import Dict, Any, Callable, List


class ConfigDialog:
    """Configuration dialog for managing application settings."""
    
    def __init__(self, parent, config: Dict[str, Any], save_callback: Callable[[Dict[str, Any]], None]):
        """
        Initialize the configuration dialog.
        
        Args:
            parent: Parent window.
            config: Current configuration dictionary.
            save_callback: Callback to save configuration changes.
        """
        self.parent = parent
        self.config = config.copy()  # Work with a copy
        self.save_callback = save_callback
        self.window = None
        self.mount_frames = []
    
    def show(self) -> None:
        """Show the configuration dialog."""
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("Configuration")
        self.window.geometry("600x500")
        self.window.transient(self.parent)
        
        # Wait for window to be fully created before grabbing focus
        self.window.after(100, lambda: self.window.grab_set())
        
        self._create_widgets()
        
        # Focus on entry field
        self.window.after(200, lambda: self.mount_entry.focus())
    
    def _create_widgets(self) -> None:
        """Create the dialog widgets."""
        # Fixed docker mounts section
        ctk.CTkLabel(
            self.window, 
            text="Fixed Docker Mounts:", 
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 10))
        
        # Frame for mounts list
        mounts_frame = ctk.CTkFrame(self.window)
        mounts_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Scrollable frame for mounts
        self.mounts_scrollable = ctk.CTkScrollableFrame(mounts_frame, label_text="Current Mounts")
        self.mounts_scrollable.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._refresh_mounts()
        
        # Entry for new mount
        self._create_entry_section()
        
        # Control buttons
        self._create_buttons()
    
    def _create_entry_section(self) -> None:
        """Create the entry section for adding new mounts."""
        entry_frame = ctk.CTkFrame(self.window)
        entry_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            entry_frame, 
            text="Add new mount:", 
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        mount_entry_frame = ctk.CTkFrame(entry_frame)
        mount_entry_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.mount_entry = ctk.CTkEntry(
            mount_entry_frame, 
            placeholder_text="-v /host/path:/container/path"
        )
        self.mount_entry.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)
        
        add_button = ctk.CTkButton(
            mount_entry_frame, 
            text="Add", 
            width=60, 
            command=self._add_mount
        )
        add_button.pack(side="right", padx=(5, 10), pady=10)
        
        # Bind Enter key to add mount
        self.mount_entry.bind('<Return>', lambda e: self._add_mount())
    
    def _create_buttons(self) -> None:
        """Create the control buttons."""
        buttons_frame = ctk.CTkFrame(self.window)
        buttons_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Control buttons
        ctk.CTkButton(
            buttons_frame, 
            text="Save & Close", 
            command=self._save_and_close
        ).pack(side="right", padx=(5, 10), pady=10)
        
        ctk.CTkButton(
            buttons_frame, 
            text="Cancel", 
            command=self._cancel,
            fg_color="gray", 
            hover_color="darkgray"
        ).pack(side="right", padx=(5, 5), pady=10)
    
    def _refresh_mounts(self) -> None:
        """Refresh the mounts display."""
        # Clear existing widgets
        for frame in self.mount_frames:
            frame.destroy()
        self.mount_frames.clear()
        
        # Add current mounts with delete buttons
        for i, mount in enumerate(self.config.get('fixed_docker_mounts', [])):
            mount_frame = ctk.CTkFrame(self.mounts_scrollable)
            mount_frame.pack(fill="x", padx=5, pady=2)
            self.mount_frames.append(mount_frame)
            
            # Mount text
            mount_label = ctk.CTkLabel(mount_frame, text=mount, anchor="w")
            mount_label.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=5)
            
            # Delete button
            delete_btn = ctk.CTkButton(
                mount_frame, 
                text="✕", 
                width=30, 
                height=25,
                command=lambda idx=i: self._delete_mount(idx),
                fg_color="red", 
                hover_color="darkred"
            )
            delete_btn.pack(side="right", padx=(5, 10), pady=5)
    
    def _add_mount(self) -> None:
        """Add a new mount to the configuration."""
        mount = self.mount_entry.get().strip()
        if mount:
            if 'fixed_docker_mounts' not in self.config:
                self.config['fixed_docker_mounts'] = []
            self.config['fixed_docker_mounts'].append(mount)
            self.mount_entry.delete(0, "end")
            self._refresh_mounts()
    
    def _delete_mount(self, index: int) -> None:
        """
        Delete a mount from the configuration.
        
        Args:
            index: Index of the mount to delete.
        """
        if 0 <= index < len(self.config.get('fixed_docker_mounts', [])):
            self.config['fixed_docker_mounts'].pop(index)
            self._refresh_mounts()
    
    def _save_and_close(self) -> None:
        """Save configuration and close dialog."""
        self.save_callback(self.config)
        self.window.destroy()
    
    def _cancel(self) -> None:
        """Cancel and close dialog without saving."""
        self.window.destroy()
