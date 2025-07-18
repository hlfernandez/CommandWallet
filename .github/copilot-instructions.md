<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# CommandWallet Project Instructions

This is a Python desktop application called CommandWallet that provides a modern GUI for managing and executing CLI commands.

## Project Structure
- `command_wallet.py`: Main application file with CustomTkinter GUI
- `setup.py`: Setup and dependency checker
- `run.sh`: Launch script
- `environment.yml`: Conda environment configuration with CustomTkinter dependency
- `~/.command-wallet/commands.json`: Data storage for saved commands (created at runtime)
- `~/.command-wallet/config.json`: Application configuration (created at runtime)

## Key Features
- Modern CustomTkinter-based GUI with dark theme and enhanced visual appeal
- Left panel with scrollable command list using CTkButtons instead of traditional Listbox
- Command editor with clean layout using CustomTkinter widgets (CTkEntry, CTkComboBox, CTkCheckBox, etc.)
- Support for running commands in Conda environments with searchable dropdowns
- Support for running commands in Docker containers with:
  - Automatic path inference from command text
  - Configurable fixed mounts through configuration dialog
  - Unified volume mounts field for manual editing
- Real-time output display with execution timestamps using CTkTextbox
- Command execution history tracking with last execution date storage
- Command sorting by name or last execution date with proper handling of never-executed commands
- Custom tooltip system showing last execution dates when hovering over command buttons
- Persistent command storage in JSON format with auto-save on all changes
- Full-screen application startup
- Auto-save functionality for all GUI changes (name, command, execution options, volume mounts)

## Development Guidelines
- Use CustomTkinter for GUI components
- Follow Python best practices and PEP 8 style guide
- Use threading for command execution to prevent GUI freezing
- Handle errors gracefully with proper user feedback
- Maintain backward compatibility with saved command data

## Dependencies
- Python 3.6+
- CustomTkinter (for modern GUI)
- Standard library modules: subprocess, threading, json, os

## Optional Dependencies
- conda: For Conda environment support
- docker: For Docker container support
