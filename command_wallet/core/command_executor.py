"""
Command execution module for CommandWallet.

Handles the execution of commands with support for Conda environments
and Docker containers, providing callbacks for GUI updates.
"""

import subprocess
import threading
import os
import re
from typing import Dict, Any, Callable, List, Optional


class CommandExecutor:
    """Handles command execution with GUI callback support."""
    
    def __init__(self, output_callback: Callable[[str], None]):
        """
        Initialize the command executor.
        
        Args:
            output_callback: Function to call with output text for GUI updates.
        """
        self.output_callback = output_callback
        self.conda_environments = self._get_conda_environments()
        self.docker_images = self._get_docker_images()
    
    def get_conda_environments(self) -> List[str]:
        """Get list of available conda environments."""
        return self.conda_environments.copy()
    
    def get_docker_images(self) -> List[str]:
        """Get list of available docker images."""
        return self.docker_images.copy()
    
    def refresh_environments(self) -> None:
        """Refresh the lists of conda environments and docker images."""
        self.conda_environments = self._get_conda_environments()
        self.docker_images = self._get_docker_images()
    
    def execute_command_async(self, command_data: Dict[str, Any], 
                            config: Dict[str, Any],
                            completion_callback: Optional[Callable[[], None]] = None) -> None:
        """
        Execute a command asynchronously.
        
        Args:
            command_data: Dictionary containing command information.
            config: Application configuration.
            completion_callback: Optional callback to run when command completes.
        """
        final_command = self._prepare_command(command_data, config)
        
        # Run command in separate thread
        thread = threading.Thread(
            target=self._execute_command,
            args=(final_command, completion_callback)
        )
        thread.daemon = True
        thread.start()
    
    def infer_docker_mounts(self, command: str) -> str:
        """
        Infer Docker mounts from command paths.
        
        Args:
            command: The command string to analyze.
            
        Returns:
            String containing inferred Docker mount arguments.
        """
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
    
    def _get_conda_environments(self) -> List[str]:
        """Get list of available conda environments."""
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
    
    def _get_docker_images(self) -> List[str]:
        """Get list of available docker images."""
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
    
    def _prepare_command(self, command_data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """
        Prepare the final command based on execution options.
        
        Args:
            command_data: Command configuration.
            config: Application configuration.
            
        Returns:
            The final command string to execute.
        """
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
                fixed_mounts = config.get('fixed_docker_mounts', [])
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
    
    def _execute_command(self, command: str, completion_callback: Optional[Callable[[], None]] = None) -> None:
        """
        Execute command and update output via callback.
        
        Args:
            command: The command to execute.
            completion_callback: Optional callback to run when command completes.
        """
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
                self.output_callback(line)
            
            process.wait()
            
            # Show completion message
            if process.returncode == 0:
                self.output_callback(f"\n--- Command completed successfully (exit code: {process.returncode}) ---\n")
            else:
                self.output_callback(f"\n--- Command failed (exit code: {process.returncode}) ---\n")
                
        except Exception as e:
            self.output_callback(f"\nError executing command: {str(e)}\n")
        finally:
            # Run completion callback if provided
            if completion_callback:
                completion_callback()
