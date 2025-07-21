#!/usr/bin/env python3
"""
CommandWallet - A modern CLI command management application.

Main entry point for the refactored modular application.
"""

from command_wallet.gui.main_window import CommandWalletWindow


def main():
    """Main entry point for CommandWallet."""
    try:
        app = CommandWalletWindow()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
    except Exception as e:
        print(f"Error starting CommandWallet: {e}")


if __name__ == "__main__":
    main()
