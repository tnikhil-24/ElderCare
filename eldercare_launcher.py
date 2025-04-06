#!/usr/bin/env python3
"""
ElderCare Voice Assistant Launcher
---------------------------------
This script provides a simple entry point to start the ElderCare Voice Assistant.
It will handle initial setup and launch the appropriate modules.
"""

import os
import sys
import subprocess
import importlib.util


def check_file_exists(filename):
    """Check if a file exists and is accessible."""
    return os.path.isfile(filename) and os.access(filename, os.R_OK)


def check_module_importable(module_name):
    """Check if a module can be imported."""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def main():
    """Main launcher function."""
    print("Starting ElderCare Voice Assistant...")

    # Check for integration module
    if check_file_exists('eldercare_integration.py'):
        # Run the integration module which handles setup and launching
        subprocess.call([sys.executable, 'eldercare_integration.py'])
    elif check_file_exists('eldercare_gui.py'):
        # If integration is missing but GUI exists, run GUI directly
        subprocess.call([sys.executable, 'eldercare_gui.py'])
    else:
        # If neither file exists, show error
        print("Error: Could not find ElderCare application files.")
        print("Please make sure that eldercare_integration.py and eldercare_gui.py are in the current directory.")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()