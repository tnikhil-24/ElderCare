"""
ElderCare Integration Module

This module helps integrate the ElderCare Voice Assistant with the GUI interface.
It handles the setup and configuration of dependencies to ensure smooth operation.
"""

import os
import sys
import logging
import importlib.util
import subprocess
import json
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='eldercare_integration.log'
)
logger = logging.getLogger('Integration')


def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = [
        'pyttsx3',
        'SpeechRecognition',
        'numpy',
        'pandas',
        'schedule',
        'requests',
        'python-dotenv',
        'pillow',  # For image handling in GUI
    ]

    missing_packages = []

    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            missing_packages.append(package)

    return missing_packages


def install_missing_packages(packages):
    """Install missing packages using pip."""
    try:
        for package in packages:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing packages: {str(e)}")
        return False


def check_api_key():
    """Check if the GROQ API key is set in the environment."""
    # Check .env file first
    try:
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('GROQ_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        if api_key and api_key != "your_api_key_here":
                            return True
    except Exception as e:
        logger.error(f"Error reading .env file: {str(e)}")

    # Check environment variable
    if os.environ.get('GROQ_API_KEY'):
        return True

    return False


def setup_api_key(key):
    """Set up the GROQ API key in the .env file."""
    try:
        # Create or update .env file
        with open('.env', 'w') as f:
            f.write(f"GROQ_API_KEY={key}\n")

        # Also set in current environment
        os.environ['GROQ_API_KEY'] = key

        return True
    except Exception as e:
        logger.error(f"Error setting API key: {str(e)}")
        return False


def check_user_profile():
    """Check if user profile exists, create default if not."""
    try:
        if not os.path.exists('user_profile.json'):
            default_profile = {
                "name": "User",
                "age": 75,
                "conditions": ["diabetes", "hypertension"],
                "medications": [
                    {"name": "Metformin", "dosage": "500mg", "frequency": "twice daily", "times": ["08:00", "20:00"]},
                    {"name": "Lisinopril", "dosage": "10mg", "frequency": "once daily", "times": ["08:00"]}
                ],
                "emergency_contact": {"name": "Family Member", "phone": "123-456-7890"},
                "preferences": {
                    "voice_speed": 0.8,
                    "volume": 0.9,
                    "reminder_frequency": "high",
                    "speaking_style": "gentle"
                }
            }

            with open('user_profile.json', 'w') as file:
                json.dump(default_profile, file, indent=4)

            logger.info("Created default user profile")
    except Exception as e:
        logger.error(f"Error checking/creating user profile: {str(e)}")


def check_health_data():
    """Check if health data file exists, create if not."""
    try:
        if not os.path.exists('health_data.csv'):
            with open('health_data.csv', 'w') as file:
                file.write(
                    'date,glucose_morning,glucose_evening,medication_adherence,sleep_hours,activity_minutes,mood,pain_level,notes\n')

            logger.info("Created empty health data file")
    except Exception as e:
        logger.error(f"Error checking/creating health data file: {str(e)}")


def setup_wizard():
    """Run a setup wizard to configure necessary components."""
    # Create a small Tkinter window for setup
    root = tk.Tk()
    root.title("ElderCare Setup Wizard")
    root.geometry("500x400")

    # Set icon if available
    try:
        root.iconbitmap("eldercare_icon.ico")
    except:
        pass

    # Configure style
    heading_font = tkfont.Font(family="Arial", size=14, weight="bold")
    text_font = tkfont.Font(family="Arial", size=12)

    # Add title
    tk.Label(root, text="ElderCare Voice Assistant Setup", font=heading_font).pack(pady=20)

    # Check dependencies
    tk.Label(root, text="Checking dependencies...", font=text_font).pack(anchor=tk.W, padx=20)

    missing_packages = check_dependencies()

    if missing_packages:
        package_text = ", ".join(missing_packages)
        tk.Label(root, text=f"Missing packages: {package_text}", font=text_font).pack(anchor=tk.W, padx=20)

        def install_packages():
            install_button.config(state=tk.DISABLED, text="Installing...")
            success = install_missing_packages(missing_packages)
            if success:
                status_label.config(text="Installation successful!")
                next_button.config(state=tk.NORMAL)
            else:
                status_label.config(text="Installation failed. Please install manually.")

        install_button = tk.Button(root, text="Install Missing Packages", font=text_font, command=install_packages)
        install_button.pack(pady=10)

        status_label = tk.Label(root, text="", font=text_font)
        status_label.pack()
    else:
        tk.Label(root, text="All required packages are installed.", font=text_font).pack(anchor=tk.W, padx=20)

    # API key setup
    tk.Label(root, text="\nAPI Key Setup", font=heading_font).pack(pady=10)

    if check_api_key():
        tk.Label(root, text="GROQ API key is already configured.", font=text_font).pack(anchor=tk.W, padx=20)
        api_key_configured = True
    else:
        tk.Label(root, text="Please enter your GROQ API key:", font=text_font).pack(anchor=tk.W, padx=20)

        api_key_var = tk.StringVar()
        api_key_entry = tk.Entry(root, textvariable=api_key_var, width=40, font=text_font)
        api_key_entry.pack(padx=20, pady=5)

        def save_api_key():
            key = api_key_var.get().strip()
            if key:
                if setup_api_key(key):
                    api_key_status.config(text="API key saved successfully!")
                    save_key_button.config(state=tk.DISABLED)
                    next_button.config(state=tk.NORMAL)
                else:
                    api_key_status.config(text="Error saving API key.")
            else:
                api_key_status.config(text="Please enter a valid API key.")

        save_key_button = tk.Button(root, text="Save API Key", font=text_font, command=save_api_key)
        save_key_button.pack(pady=5)

        api_key_status = tk.Label(root, text="", font=text_font)
        api_key_status.pack()

        api_key_configured = False

    # Data files check
    check_user_profile()
    check_health_data()

    # Next button to proceed to main application
    def proceed_to_app():
        root.destroy()
        # The main application will be launched by the caller

    next_button = tk.Button(root, text="Launch ElderCare", font=heading_font, command=proceed_to_app)
    next_button.config(state=tk.NORMAL if (not missing_packages or api_key_configured) else tk.DISABLED)
    next_button.pack(pady=20)

    # Run the setup window
    root.mainloop()

    # Return whether setup was completed
    return True  # If root doesn't exist, setup was completed


def main():
    """Main function to run the integration."""
    # Run setup wizard if needed
    setup_completed = setup_wizard()

    if setup_completed:
        # Now we can import and run the main application
        try:
            # First try to import the GUI module
            from eldercare_gui import main as run_gui
            run_gui()
        except ImportError:
            # If the GUI module is not available as a separate file, run as a script
            subprocess.call([sys.executable, "eldercare_gui.py"])
    else:
        logger.warning("Setup was not completed. Application not started.")


if __name__ == "__main__":
    main()