<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# CommandWallet Project Instructions

This is a Python desktop application called CommandWallet that provides a GUI for managing and executing CLI commands.

## Project Structure
- `command_wallet.py`: Main application file with tkinter GUI
- `setup.py`: Setup and dependency checker
- `run.sh`: Launch script
- `environment.yml`: Conda environment configuration
- `~/.command-wallet/commands.json`: Data storage for saved commands (created at runtime)
- `~/.command-wallet/config.json`: Application configuration (created at runtime)

## Key Features
- Clean tkinter-based GUI with left panel for command selection
- Command editor with name, command input, and execution options
- Support for running commands in Conda environments with searchable dropdowns
- Support for running commands in Docker containers with:
  - Automatic path inference from command text
  - Configurable fixed mounts through configuration dialog
  - Unified volume mounts field for manual editing
- Real-time output display
- Persistent command storage in JSON format with auto-save on all changes
- Full-screen application startup
- Auto-save functionality for all GUI changes (name, command, execution options, volume mounts)

## Development Guidelines
- Use tkinter for GUI components
- Follow Python best practices and PEP 8 style guide
- Use threading for command execution to prevent GUI freezing
- Handle errors gracefully with proper user feedback
- Maintain backward compatibility with saved command data

## Dependencies
- Python 3.6+
- tkinter (usually included with Python)
- Standard library modules: subprocess, threading, json, os

## Optional Dependencies
- conda: For Conda environment support
- docker: For Docker container support
