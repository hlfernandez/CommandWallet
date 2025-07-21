"""
Data persistence module for CommandWallet.

Handles loading and saving of commands and configuration data to JSON files.
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime


class DataManager:
    """Manages data persistence for commands and configuration."""
    
    def __init__(self):
        """Initialize the data manager."""
        # Create config directory in user home
        self.config_dir = os.path.join(os.path.expanduser("~"), ".command-wallet")
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        self.data_file = os.path.join(self.config_dir, "commands.json")
        self.config_file = os.path.join(self.config_dir, "config.json")
    
    def load_commands(self) -> Dict[str, Any]:
        """
        Load commands from JSON file.
        
        Returns:
            Dict containing all saved commands.
        """
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    commands = json.load(f)
                self._ensure_command_data_schema(commands)
                return commands
            return {}
        except Exception as e:
            print(f"Error loading commands: {e}")
            return {}
    
    def save_commands(self, commands: Dict[str, Any]) -> bool:
        """
        Save commands to JSON file.
        
        Args:
            commands: Dictionary of commands to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            with open(self.data_file, 'w') as f:
                json.dump(commands, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving commands: {e}")
            return False
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Returns:
            Dict containing configuration data.
        """
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
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Save configuration to JSON file.
        
        Args:
            config: Configuration dictionary to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def create_new_command(self, commands: Dict[str, Any], name: Optional[str] = None) -> str:
        """
        Create a new command entry.
        
        Args:
            commands: Current commands dictionary.
            name: Optional name for the command.
            
        Returns:
            The ID of the newly created command.
        """
        command_id = f"cmd_{len(commands) + 1}"
        command_name = name or f'New Command {len(commands) + 1}'
        
        commands[command_id] = {
            'name': command_name,
            'command': '',
            'use_conda': False,
            'conda_env': '',
            'use_docker': False,
            'docker_image': '',
            'volume_mounts': '',
            'last_execution': None
        }
        
        return command_id
    
    def update_command_execution_time(self, commands: Dict[str, Any], command_id: str) -> None:
        """
        Update the last execution time for a command.
        
        Args:
            commands: Commands dictionary.
            command_id: ID of the command to update.
        """
        if command_id in commands:
            execution_time = datetime.now()
            commands[command_id]['last_execution'] = execution_time.strftime("%Y-%m-%d %H:%M:%S")
    
    def _ensure_command_data_schema(self, commands: Dict[str, Any]) -> None:
        """
        Ensure all commands have the required fields for backward compatibility.
        
        Args:
            commands: Commands dictionary to update.
        """
        for command_id, command_data in commands.items():
            if 'volume_mounts' not in command_data:
                command_data['volume_mounts'] = ''
            if 'last_execution' not in command_data:
                command_data['last_execution'] = None
