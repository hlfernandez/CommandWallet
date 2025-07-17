#!/usr/bin/env python3
"""
Setup script for CommandWallet
"""

import os
import sys
import subprocess

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 6):
        print("Error: Python 3.6 or higher is required.")
        sys.exit(1)

def check_tkinter():
    """Check if tkinter is available"""
    try:
        import tkinter
        print("✓ tkinter is available")
    except ImportError:
        print("Error: tkinter is not available. Please install python3-tk:")
        print("  Ubuntu/Debian: sudo apt-get install python3-tk")
        print("  CentOS/RHEL: sudo yum install tkinter")
        print("  macOS: tkinter should be included with Python")
        sys.exit(1)

def check_dependencies():
    """Check if all required dependencies are available"""
    required_modules = ['tkinter', 'subprocess', 'threading', 'json', 'os']
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module} is available")
        except ImportError:
            print(f"Error: {module} is not available")
            sys.exit(1)

def check_optional_tools():
    """Check if optional tools are available"""
    tools = {
        'conda': 'Conda environment support',
        'docker': 'Docker container support'
    }
    
    print("\nOptional tools:")
    for tool, description in tools.items():
        try:
            result = subprocess.run([tool, '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ {tool} is available - {description}")
            else:
                print(f"✗ {tool} is not available - {description}")
        except FileNotFoundError:
            print(f"✗ {tool} is not available - {description}")

def main():
    print("CommandWallet Setup Check")
    print("=" * 30)
    
    check_python_version()
    print(f"✓ Python {sys.version.split()[0]} is compatible")
    
    check_tkinter()
    check_dependencies()
    check_optional_tools()
    
    print("\n" + "=" * 30)
    print("Setup complete! You can now run:")
    print("  python3 command_wallet.py")

if __name__ == "__main__":
    main()
