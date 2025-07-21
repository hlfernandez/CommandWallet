"""
Cron export dialog module for CommandWallet.

Provides a dialog for exporting commands as cron entries
with schedule configuration and preview.
"""

import customtkinter as ctk
from typing import Dict, Any, Callable, List


class CronExportDialog:
    """Dialog for exporting commands as cron entries."""
    
    def __init__(self, parent, command_data: Dict[str, Any], prepare_command_callback: Callable[[Dict[str, Any]], str]):
        """
        Initialize the cron export dialog.
        
        Args:
            parent: Parent window.
            command_data: Command data to export.
            prepare_command_callback: Callback to prepare the final command string.
        """
        self.parent = parent
        self.command_data = command_data
        self.prepare_command_callback = prepare_command_callback
        self.window = None
        self.cron_entries = []
        self.cron_preview_label = None
        self.cron_output_text = None
    
    def show(self) -> None:
        """Show the cron export dialog."""
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("Export to Cron")
        self.window.geometry("700x600")
        self.window.transient(self.parent)
        
        # Wait for window to be fully created before grabbing focus
        self.window.after(100, lambda: self.window.grab_set())
        
        self._create_widgets()
        
        # Initialize preview
        self._update_cron_preview()
        
        # Focus on first entry field
        self.window.after(200, lambda: self.cron_entries[0].focus())
    
    def _create_widgets(self) -> None:
        """Create the dialog widgets."""
        # Title
        ctk.CTkLabel(
            self.window, 
            text="Export Command to Cron",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(20, 10))
        
        # Command info
        self._create_command_info()
        
        # Cron fields
        self._create_cron_fields()
        
        # Preview
        self._create_preview_section()
        
        # Generated cron entry
        self._create_output_section()
        
        # Control buttons
        self._create_buttons()
    
    def _create_command_info(self) -> None:
        """Create the command information section."""
        command_name = self.command_data['name']
        command_text = self.command_data['command']
        
        info_frame = ctk.CTkFrame(self.window)
        info_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            info_frame, 
            text=f"Command: {command_name}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(
            info_frame, 
            text=f"Script: {command_text}",
            font=ctk.CTkFont(size=12), 
            wraplength=650
        ).pack(anchor="w", padx=10, pady=(0, 10))
    
    def _create_cron_fields(self) -> None:
        """Create the cron schedule configuration fields."""
        fields_frame = ctk.CTkFrame(self.window)
        fields_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            fields_frame, 
            text="Cron Schedule Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 15))
        
        # Create grid for cron fields
        grid_frame = ctk.CTkFrame(fields_frame)
        grid_frame.pack(padx=20, pady=(0, 20))
        
        # Field labels and descriptions
        field_info = [
            ("Minute", "0-59", "* means every minute"),
            ("Hour", "0-23", "* means every hour"),
            ("Day", "1-31", "* means every day"),
            ("Month", "1-12", "* means every month"),
            ("Weekday", "0-7", "0 and 7 = Sunday, * means every day")
        ]
        
        # Create cron entry fields
        self.cron_entries = []
        for i, (label, range_text, desc) in enumerate(field_info):
            # Label
            ctk.CTkLabel(
                grid_frame, 
                text=label, 
                font=ctk.CTkFont(size=12, weight="bold")
            ).grid(row=i, column=0, sticky="w", padx=(10, 20), pady=5)
            
            # Entry
            entry = ctk.CTkEntry(grid_frame, width=80, placeholder_text="*")
            entry.grid(row=i, column=1, padx=(0, 20), pady=5)
            entry.insert(0, "*")
            entry.bind('<KeyRelease>', self._update_cron_preview)
            self.cron_entries.append(entry)
            
            # Range
            ctk.CTkLabel(
                grid_frame, 
                text=f"({range_text})",
                font=ctk.CTkFont(size=10)
            ).grid(row=i, column=2, sticky="w", padx=(0, 20), pady=5)
            
            # Description
            ctk.CTkLabel(
                grid_frame, 
                text=desc, 
                font=ctk.CTkFont(size=10),
                text_color="gray"
            ).grid(row=i, column=3, sticky="w", padx=(0, 10), pady=5)
    
    def _create_preview_section(self) -> None:
        """Create the schedule preview section."""
        preview_frame = ctk.CTkFrame(self.window)
        preview_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            preview_frame, 
            text="Schedule Preview",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.cron_preview_label = ctk.CTkLabel(
            preview_frame, 
            text="Every minute",
            font=ctk.CTkFont(size=12), 
            wraplength=650
        )
        self.cron_preview_label.pack(anchor="w", padx=10, pady=(0, 10))
    
    def _create_output_section(self) -> None:
        """Create the generated cron entry output section."""
        output_frame = ctk.CTkFrame(self.window)
        output_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            output_frame, 
            text="Generated Cron Entry",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Text area for cron entry
        self.cron_output_text = ctk.CTkTextbox(
            output_frame, 
            height=120,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.cron_output_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def _create_buttons(self) -> None:
        """Create the control buttons."""
        buttons_frame = ctk.CTkFrame(self.window)
        buttons_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Copy button
        self.copy_btn = ctk.CTkButton(
            buttons_frame, 
            text="Copy to Clipboard", 
            command=self._copy_cron_entry
        )
        self.copy_btn.pack(side="right", padx=(5, 10), pady=10)
        
        # Close button
        ctk.CTkButton(
            buttons_frame, 
            text="Close", 
            command=self._close_dialog,
            fg_color="gray", 
            hover_color="darkgray"
        ).pack(side="right", padx=(5, 5), pady=10)
    
    def _update_cron_preview(self, event=None) -> None:
        """Update cron schedule preview and generated entry."""
        if not self.cron_entries:
            return
        
        # Get values from entries
        minute = self.cron_entries[0].get() or "*"
        hour = self.cron_entries[1].get() or "*"
        day = self.cron_entries[2].get() or "*"
        month = self.cron_entries[3].get() or "*"
        weekday = self.cron_entries[4].get() or "*"
        
        # Generate human-readable description
        description = self._get_cron_description(minute, hour, day, month, weekday)
        self.cron_preview_label.configure(text=description)
        
        # Generate cron entry
        final_command = self.prepare_command_callback(self.command_data)
        
        cron_schedule = f"{minute} {hour} {day} {month} {weekday}"
        cron_entry = f"# {self.command_data['name']} - {description}\n{cron_schedule} {final_command}"
        
        # Update output text
        self.cron_output_text.delete("1.0", "end")
        self.cron_output_text.insert("1.0", cron_entry)
    
    def _get_cron_description(self, minute: str, hour: str, day: str, month: str, weekday: str) -> str:
        """
        Generate human-readable description of cron schedule.
        
        Args:
            minute: Minute field value.
            hour: Hour field value.
            day: Day field value.
            month: Month field value.
            weekday: Weekday field value.
            
        Returns:
            Human-readable description of the schedule.
        """
        # Day names
        day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        month_names = ["", "January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        
        def format_time(m: str, h: str) -> str:
            if m == "*" and h == "*":
                return "every minute"
            elif m == "*":
                if h.isdigit():
                    return f"every minute during hour {h}"
                else:
                    return f"every minute during hours {h}"
            elif h == "*":
                if m.isdigit():
                    return f"at minute {m} of every hour"
                else:
                    return f"at minutes {m} of every hour"
            else:
                if m.isdigit() and h.isdigit():
                    return f"at {h.zfill(2)}:{m.zfill(2)}"
                else:
                    return f"at {h}:{m}"
        
        def format_day_part(d: str, m: str, w: str) -> str:
            parts = []
            
            if d != "*":
                if d.isdigit():
                    parts.append(f"day-of-month {d}")
                else:
                    parts.append(f"days-of-month {d}")
            
            if m != "*":
                if m.isdigit() and 1 <= int(m) <= 12:
                    parts.append(f"in {month_names[int(m)]}")
                else:
                    parts.append(f"in months {m}")
            
            if w != "*":
                if w.isdigit() and 0 <= int(w) <= 7:
                    day_idx = int(w) % 7  # Convert 7 to 0 for Sunday
                    parts.append(f"on {day_names[day_idx]}")
                else:
                    parts.append(f"on weekdays {w}")
            
            return " ".join(parts)
        
        time_part = format_time(minute, hour)
        day_part = format_day_part(day, month, weekday)
        
        if day_part:
            return f"{time_part.capitalize()} {day_part}."
        else:
            return f"{time_part.capitalize()}."
    
    def _copy_cron_entry(self) -> None:
        """Copy the generated cron entry to clipboard."""
        cron_text = self.cron_output_text.get("1.0", "end-1c")
        if cron_text.strip():
            self.window.clipboard_clear()
            self.window.clipboard_append(cron_text)
            self.window.update()
            # Show brief confirmation
            self.copy_btn.configure(text="Copied!")
            self.window.after(1500, lambda: self.copy_btn.configure(text="Copy to Clipboard"))
    
    def _close_dialog(self) -> None:
        """Close the dialog."""
        self.window.destroy()
