import sys
import os
import json
import datetime
import threading
import queue
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, font
import pandas as pd
from PIL import Image, ImageTk
import logging

# Import the voice assistant class from your existing module
from eldercare_assistant import ElderCareVoiceAssistant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='eldercare_gui.log'
)
logger = logging.getLogger('ElderCareGUI')


class ElderCareGUI:
    """GUI interface for the ElderCare Voice Assistant."""

    def __init__(self, root):
        """Initialize the GUI with the main window and components."""
        self.root = root
        self.root.title("ElderCare Voice Assistant")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # Set app icon (create a placeholder if needed)
        try:
            self.root.iconbitmap("eldercare_icon.ico")
        except:
            # Proceed without icon if not found
            pass

        # Load user profile
        try:
            with open('user_profile.json', 'r') as file:
                self.user_profile = json.load(file)
        except FileNotFoundError:
            # Create a default profile if not found
            self.user_profile = {
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

        # Load health data
        try:
            self.health_data = pd.read_csv('health_data.csv')
        except FileNotFoundError:
            # Create empty health data tracking
            self.health_data = pd.DataFrame(columns=[
                'date', 'glucose_morning', 'glucose_evening',
                'medication_adherence', 'sleep_hours', 'activity_minutes',
                'mood', 'pain_level', 'notes'
            ])
            self.health_data.to_csv('health_data.csv', index=False)

        # Create voice assistant instance
        self.voice_assistant = None
        try:
            self.voice_assistant = ElderCareVoiceAssistant()
            self.assistant_ready = True
        except Exception as e:
            logger.error(f"Error initializing voice assistant: {str(e)}")
            self.assistant_ready = False
            messagebox.showerror("Initialization Error",
                                 f"Could not initialize voice assistant: {str(e)}\n\nYou can still use the GUI features, but voice features will be disabled.")

        # Set up the GUI components
        self.setup_styles()
        self.create_widgets()
        self.setup_reminder_thread()

        # Perform an initial greeting
        self.display_assistant_message(
            f"Hello {self.user_profile['name']}! Welcome to ElderCare Assistant. How can I help you today?")

    def setup_styles(self):
        """Configure styles for the GUI components with accessibility in mind."""
        # Create custom fonts
        self.title_font = font.Font(family="Arial", size=18, weight="bold")
        self.heading_font = font.Font(family="Arial", size=14, weight="bold")
        self.text_font = font.Font(family="Arial", size=12)
        self.button_font = font.Font(family="Arial", size=12, weight="bold")

        # Configure ttk styles
        style = ttk.Style()

        # Configure button style
        style.configure("Large.TButton",
                        font=self.button_font,
                        padding=10,
                        background="#4682B4")

        # Configure tab style
        style.configure("TNotebook.Tab",
                        font=self.text_font,
                        padding=[10, 5])

        # Configure frame style
        style.configure("Card.TFrame",
                        background="#f0f0f0",
                        relief="raised",
                        borderwidth=2)

        # Configure label styles
        style.configure("Title.TLabel",
                        font=self.title_font,
                        foreground="#0056b3",
                        padding=10)

        style.configure("Heading.TLabel",
                        font=self.heading_font,
                        foreground="#0056b3",
                        padding=5)

        style.configure("Normal.TLabel",
                        font=self.text_font,
                        padding=5)

    def create_widgets(self):
        """Create and arrange all GUI components."""
        # Create main container with padding
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create header with logo and title
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=10)

        # Add logo (create a placeholder if needed)
        try:
            logo_img = Image.open("eldercare_logo.png")
            logo_img = logo_img.resize((80, 80), Image.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = ttk.Label(header_frame, image=self.logo_photo)
            logo_label.pack(side=tk.LEFT, padx=10)
        except:
            # Proceed without logo if not found
            pass

        # Add title
        title_label = ttk.Label(header_frame,
                                text="ElderCare Voice Assistant",
                                style="Title.TLabel")
        title_label.pack(side=tk.LEFT, padx=10)

        # Add notebook (tabbed interface)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create tabs
        self.assistant_tab = ttk.Frame(self.notebook, padding=10)
        self.health_tab = ttk.Frame(self.notebook, padding=10)
        self.medications_tab = ttk.Frame(self.notebook, padding=10)
        self.profile_tab = ttk.Frame(self.notebook, padding=10)
        self.settings_tab = ttk.Frame(self.notebook, padding=10)

        # Add tabs to notebook
        self.notebook.add(self.assistant_tab, text="Assistant")
        self.notebook.add(self.health_tab, text="Health Tracking")
        self.notebook.add(self.medications_tab, text="Medications")
        self.notebook.add(self.profile_tab, text="Profile")
        self.notebook.add(self.settings_tab, text="Settings")

        # Set up each tab's content
        self.setup_assistant_tab()
        self.setup_health_tab()
        self.setup_medications_tab()
        self.setup_profile_tab()
        self.setup_settings_tab()

        # Add status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        self.status_label = ttk.Label(status_frame,
                                      text="Status: Ready",
                                      font=self.text_font)
        self.status_label.pack(side=tk.LEFT)

        time_label = ttk.Label(status_frame,
                               text=datetime.datetime.now().strftime("%A, %B %d, %Y"),
                               font=self.text_font)
        time_label.pack(side=tk.RIGHT)

        # Add emergency button at the bottom
        emergency_frame = ttk.Frame(main_frame)
        emergency_frame.pack(fill=tk.X, pady=10)

        self.emergency_button = ttk.Button(emergency_frame,
                                           text="EMERGENCY",
                                           style="Large.TButton",
                                           command=self.handle_emergency)
        self.emergency_button.configure(padding=(20, 10))
        self.emergency_button.pack(pady=5)

        # Add quit button
        quit_button = ttk.Button(emergency_frame,
                                 text="Exit ElderCare",
                                 command=self.on_closing)
        quit_button.pack(pady=5)

        # Set protocol for window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_assistant_tab(self):
        """Set up the main assistant tab with conversation interface."""
        # Create conversation display
        conversation_frame = ttk.Frame(self.assistant_tab)
        conversation_frame.pack(fill=tk.BOTH, expand=True)

        # Label for conversation
        conversation_label = ttk.Label(conversation_frame,
                                       text="Conversation with ElderCare",
                                       style="Heading.TLabel")
        conversation_label.pack(anchor=tk.W, pady=(0, 5))

        # Text area for conversation
        self.conversation_display = scrolledtext.ScrolledText(conversation_frame,
                                                              wrap=tk.WORD,
                                                              font=self.text_font,
                                                              height=15)
        self.conversation_display.pack(fill=tk.BOTH, expand=True, pady=5)
        self.conversation_display.config(state=tk.DISABLED)

        # Create quick action buttons
        actions_frame = ttk.LabelFrame(self.assistant_tab, text="Quick Actions", padding=10)
        actions_frame.pack(fill=tk.X, pady=10)

        # Create a grid for the buttons
        button_grid_frame = ttk.Frame(actions_frame)
        button_grid_frame.pack(fill=tk.X)

        button_texts = [
            "Record Glucose", "Record Sleep", "Record Medication",
            "Health Report", "List Medications", "Help"
        ]

        button_commands = [
            lambda: self.handle_quick_action("record glucose"),
            lambda: self.handle_quick_action("record sleep"),
            lambda: self.handle_quick_action("record medication"),
            lambda: self.handle_quick_action("health data"),
            lambda: self.handle_quick_action("list medications"),
            lambda: self.handle_quick_action("help")
        ]

        # Create the grid of buttons
        for i in range(2):
            for j in range(3):
                index = i * 3 + j
                if index < len(button_texts):
                    button = ttk.Button(button_grid_frame,
                                        text=button_texts[index],
                                        command=button_commands[index],
                                        style="Large.TButton")
                    button.grid(row=i, column=j, padx=5, pady=5, sticky="nsew")

        # Configure grid columns to be equal width
        for j in range(3):
            button_grid_frame.columnconfigure(j, weight=1)

        # Create input area
        input_frame = ttk.Frame(self.assistant_tab)
        input_frame.pack(fill=tk.X, pady=10)

        # Voice input button
        voice_button = ttk.Button(input_frame,
                                  text="🎤 Speak",
                                  command=self.handle_voice_input)
        voice_button.pack(side=tk.LEFT, padx=(0, 5))

        # Text input field
        self.text_input = ttk.Entry(input_frame, font=self.text_font)
        self.text_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.text_input.bind("<Return>", self.handle_text_input)

        # Send button
        send_button = ttk.Button(input_frame,
                                 text="Send",
                                 command=self.handle_text_input)
        send_button.pack(side=tk.LEFT, padx=(5, 0))

        # Set focus to text input
        self.text_input.focus_set()

    def setup_health_tab(self):
        """Set up the health tracking tab."""
        # Create header for health tracking
        health_header = ttk.Label(self.health_tab,
                                  text="Health Tracking",
                                  style="Heading.TLabel")
        health_header.pack(anchor=tk.W, pady=(0, 10))

        # Create main content in two columns
        health_content = ttk.Frame(self.health_tab)
        health_content.pack(fill=tk.BOTH, expand=True)

        # Left column - Data Entry
        left_frame = ttk.LabelFrame(health_content, text="Record Health Data", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Glucose frame
        glucose_frame = ttk.Frame(left_frame)
        glucose_frame.pack(fill=tk.X, pady=5)

        ttk.Label(glucose_frame, text="Blood Glucose:", font=self.text_font).grid(row=0, column=0, sticky=tk.W)
        self.glucose_var = tk.StringVar()
        ttk.Entry(glucose_frame, textvariable=self.glucose_var, width=10).grid(row=0, column=1, padx=5)

        glucose_time_var = tk.StringVar(value="Morning")
        ttk.Radiobutton(glucose_frame, text="Morning", variable=glucose_time_var, value="Morning").grid(row=0, column=2,
                                                                                                        padx=5)
        ttk.Radiobutton(glucose_frame, text="Evening", variable=glucose_time_var, value="Evening").grid(row=0, column=3,
                                                                                                        padx=5)

        ttk.Button(glucose_frame, text="Record",
                   command=lambda: self.record_glucose(self.glucose_var.get(), glucose_time_var.get())).grid(row=0,
                                                                                                             column=4,
                                                                                                             padx=5)

        # Sleep frame
        sleep_frame = ttk.Frame(left_frame)
        sleep_frame.pack(fill=tk.X, pady=5)

        ttk.Label(sleep_frame, text="Sleep Hours:", font=self.text_font).grid(row=0, column=0, sticky=tk.W)
        self.sleep_var = tk.StringVar()
        ttk.Entry(sleep_frame, textvariable=self.sleep_var, width=10).grid(row=0, column=1, padx=5)

        ttk.Button(sleep_frame, text="Record",
                   command=lambda: self.record_sleep(self.sleep_var.get())).grid(row=0, column=2, padx=5)

        # Medication frame
        medication_frame = ttk.Frame(left_frame)
        medication_frame.pack(fill=tk.X, pady=5)

        ttk.Label(medication_frame, text="Medications Taken:", font=self.text_font).grid(row=0, column=0, sticky=tk.W)
        self.medication_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(medication_frame, text="All medications", variable=self.medication_var).grid(row=0, column=1,
                                                                                                     padx=5)

        ttk.Button(medication_frame, text="Record",
                   command=lambda: self.record_medication(self.medication_var.get())).grid(row=0, column=2, padx=5)

        # Notes frame
        notes_frame = ttk.Frame(left_frame)
        notes_frame.pack(fill=tk.X, pady=5)

        ttk.Label(notes_frame, text="Notes:", font=self.text_font).pack(anchor=tk.W)
        self.notes_text = scrolledtext.ScrolledText(notes_frame, height=4, font=self.text_font)
        self.notes_text.pack(fill=tk.X, pady=5)

        ttk.Button(notes_frame, text="Save Notes",
                   command=self.save_health_notes).pack(anchor=tk.E)

        # Right column - Data Display
        right_frame = ttk.LabelFrame(health_content, text="Recent Health Data", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Create a display for recent health data
        self.health_data_display = scrolledtext.ScrolledText(right_frame, height=15, font=self.text_font)
        self.health_data_display.pack(fill=tk.BOTH, expand=True, pady=5)
        self.health_data_display.config(state=tk.DISABLED)

        # Refresh health data button
        ttk.Button(right_frame, text="Refresh Data",
                   command=self.refresh_health_data).pack(anchor=tk.E)

        # Load initial health data
        self.refresh_health_data()

    def setup_medications_tab(self):
        """Set up the medications management tab."""
        # Create header
        meds_header = ttk.Label(self.medications_tab,
                                text="Medication Management",
                                style="Heading.TLabel")
        meds_header.pack(anchor=tk.W, pady=(0, 10))

        # Create main content in two columns
        meds_content = ttk.Frame(self.medications_tab)
        meds_content.pack(fill=tk.BOTH, expand=True)

        # Left column - Current Medications
        left_frame = ttk.LabelFrame(meds_content, text="Current Medications", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Create a treeview for medications
        self.meds_tree = ttk.Treeview(left_frame, columns=("Dosage", "Frequency", "Times"), show="headings")

        # Define headings
        self.meds_tree.heading("Dosage", text="Dosage")
        self.meds_tree.heading("Frequency", text="Frequency")
        self.meds_tree.heading("Times", text="Times")

        # Define columns
        self.meds_tree.column("Dosage", width=100)
        self.meds_tree.column("Frequency", width=100)
        self.meds_tree.column("Times", width=150)

        # Add scrollbar
        meds_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.meds_tree.yview)
        self.meds_tree.configure(yscrollcommand=meds_scroll.set)

        # Pack widgets
        self.meds_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        meds_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons for modifying medications
        meds_buttons = ttk.Frame(left_frame)
        meds_buttons.pack(fill=tk.X, pady=10)

        ttk.Button(meds_buttons, text="Edit Selected",
                   command=self.edit_medication).pack(side=tk.LEFT, padx=5)

        ttk.Button(meds_buttons, text="Remove Selected",
                   command=self.remove_medication).pack(side=tk.LEFT, padx=5)

        ttk.Button(meds_buttons, text="Medication Taken",
                   command=self.mark_medication_taken).pack(side=tk.LEFT, padx=5)

        # Right column - Add New Medication
        right_frame = ttk.LabelFrame(meds_content, text="Add New Medication", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Form for adding new medication
        form_frame = ttk.Frame(right_frame)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Medication name
        ttk.Label(form_frame, text="Medication Name:", font=self.text_font).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.med_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.med_name_var).grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Dosage
        ttk.Label(form_frame, text="Dosage:", font=self.text_font).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.med_dosage_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.med_dosage_var).grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # Frequency
        ttk.Label(form_frame, text="Frequency:", font=self.text_font).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.med_frequency_var = tk.StringVar()
        frequency_combo = ttk.Combobox(form_frame, textvariable=self.med_frequency_var)
        frequency_combo['values'] = ("once daily", "twice daily", "three times daily", "as needed")
        frequency_combo.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        # Times
        ttk.Label(form_frame, text="Times:", font=self.text_font).grid(row=3, column=0, sticky=tk.W, pady=5)
        times_frame = ttk.Frame(form_frame)
        times_frame.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        # Morning checkbox
        self.morning_var = tk.BooleanVar()
        ttk.Checkbutton(times_frame, text="Morning (8:00 AM)", variable=self.morning_var).pack(anchor=tk.W)

        # Noon checkbox
        self.noon_var = tk.BooleanVar()
        ttk.Checkbutton(times_frame, text="Noon (12:00 PM)", variable=self.noon_var).pack(anchor=tk.W)

        # Evening checkbox
        self.evening_var = tk.BooleanVar()
        ttk.Checkbutton(times_frame, text="Evening (6:00 PM)", variable=self.evening_var).pack(anchor=tk.W)

        # Bedtime checkbox
        self.bedtime_var = tk.BooleanVar()
        ttk.Checkbutton(times_frame, text="Bedtime (10:00 PM)", variable=self.bedtime_var).pack(anchor=tk.W)

        # Notes
        ttk.Label(form_frame, text="Notes:", font=self.text_font).grid(row=4, column=0, sticky=tk.W, pady=5)
        self.med_notes_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.med_notes_var).grid(row=4, column=1, sticky="ew", padx=5, pady=5)

        # Configure grid column
        form_frame.columnconfigure(1, weight=1)

        # Add button
        ttk.Button(right_frame, text="Add Medication",
                   command=self.add_medication).pack(anchor=tk.E, pady=10)

        # Load initial medication data
        self.load_medications()

    def setup_profile_tab(self):
        """Set up the user profile tab."""
        # Create header
        profile_header = ttk.Label(self.profile_tab,
                                   text="User Profile",
                                   style="Heading.TLabel")
        profile_header.pack(anchor=tk.W, pady=(0, 10))

        # Create main content
        profile_frame = ttk.Frame(self.profile_tab)
        profile_frame.pack(fill=tk.BOTH, expand=True)

        # Personal information section
        personal_frame = ttk.LabelFrame(profile_frame, text="Personal Information", padding=10)
        personal_frame.pack(fill=tk.X, pady=5)

        # Name
        name_frame = ttk.Frame(personal_frame)
        name_frame.pack(fill=tk.X, pady=5)

        ttk.Label(name_frame, text="Name:", width=15, font=self.text_font).pack(side=tk.LEFT)
        self.name_var = tk.StringVar(value=self.user_profile["name"])
        ttk.Entry(name_frame, textvariable=self.name_var, font=self.text_font).pack(side=tk.LEFT, fill=tk.X,
                                                                                    expand=True)

        # Age
        age_frame = ttk.Frame(personal_frame)
        age_frame.pack(fill=tk.X, pady=5)

        ttk.Label(age_frame, text="Age:", width=15, font=self.text_font).pack(side=tk.LEFT)
        self.age_var = tk.StringVar(value=str(self.user_profile["age"]))
        ttk.Entry(age_frame, textvariable=self.age_var, font=self.text_font).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Health conditions
        conditions_frame = ttk.Frame(personal_frame)
        conditions_frame.pack(fill=tk.X, pady=5)

        ttk.Label(conditions_frame, text="Health Conditions:", width=15, font=self.text_font).pack(side=tk.LEFT,
                                                                                                   anchor=tk.N)

        conditions_subframe = ttk.Frame(conditions_frame)
        conditions_subframe.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Create checkboxes for common conditions
        self.diabetes_var = tk.BooleanVar(value="diabetes" in self.user_profile["conditions"])
        ttk.Checkbutton(conditions_subframe, text="Diabetes", variable=self.diabetes_var).pack(anchor=tk.W)

        self.hypertension_var = tk.BooleanVar(value="hypertension" in self.user_profile["conditions"])
        ttk.Checkbutton(conditions_subframe, text="Hypertension", variable=self.hypertension_var).pack(anchor=tk.W)

        self.arthritis_var = tk.BooleanVar(value="arthritis" in self.user_profile["conditions"])
        ttk.Checkbutton(conditions_subframe, text="Arthritis", variable=self.arthritis_var).pack(anchor=tk.W)

        self.heart_var = tk.BooleanVar(value="heart disease" in self.user_profile["conditions"])
        ttk.Checkbutton(conditions_subframe, text="Heart Disease", variable=self.heart_var).pack(anchor=tk.W)

        # Other conditions
        other_frame = ttk.Frame(personal_frame)
        other_frame.pack(fill=tk.X, pady=5)

        ttk.Label(other_frame, text="Other Conditions:", width=15, font=self.text_font).pack(side=tk.LEFT)
        self.other_conditions_var = tk.StringVar()
        ttk.Entry(other_frame, textvariable=self.other_conditions_var, font=self.text_font).pack(side=tk.LEFT,
                                                                                                 fill=tk.X, expand=True)

        # Emergency contact section
        emergency_frame = ttk.LabelFrame(profile_frame, text="Emergency Contact", padding=10)
        emergency_frame.pack(fill=tk.X, pady=10)

        # Contact name
        contact_name_frame = ttk.Frame(emergency_frame)
        contact_name_frame.pack(fill=tk.X, pady=5)

        ttk.Label(contact_name_frame, text="Contact Name:", width=15, font=self.text_font).pack(side=tk.LEFT)
        self.contact_name_var = tk.StringVar(value=self.user_profile["emergency_contact"]["name"])
        ttk.Entry(contact_name_frame, textvariable=self.contact_name_var, font=self.text_font).pack(side=tk.LEFT,
                                                                                                    fill=tk.X,
                                                                                                    expand=True)

        # Contact phone
        contact_phone_frame = ttk.Frame(emergency_frame)
        contact_phone_frame.pack(fill=tk.X, pady=5)

        ttk.Label(contact_phone_frame, text="Contact Phone:", width=15, font=self.text_font).pack(side=tk.LEFT)
        self.contact_phone_var = tk.StringVar(value=self.user_profile["emergency_contact"]["phone"])
        ttk.Entry(contact_phone_frame, textvariable=self.contact_phone_var, font=self.text_font).pack(side=tk.LEFT,
                                                                                                      fill=tk.X,
                                                                                                      expand=True)

        # Save button
        ttk.Button(profile_frame, text="Save Profile",
                   command=self.save_profile).pack(pady=10)

    def setup_settings_tab(self):
        """Set up the settings tab."""
        # Create header
        settings_header = ttk.Label(self.settings_tab,
                                    text="Voice and Display Settings",
                                    style="Heading.TLabel")
        settings_header.pack(anchor=tk.W, pady=(0, 10))

        # Create main content
        settings_frame = ttk.Frame(self.settings_tab)
        settings_frame.pack(fill=tk.BOTH, expand=True)

        # Voice settings section
        voice_frame = ttk.LabelFrame(settings_frame, text="Voice Settings", padding=10)
        voice_frame.pack(fill=tk.X, pady=5)

        # Voice speed
        speed_frame = ttk.Frame(voice_frame)
        speed_frame.pack(fill=tk.X, pady=5)

        ttk.Label(speed_frame, text="Voice Speed:", font=self.text_font).pack(side=tk.LEFT)

        self.voice_speed_var = tk.DoubleVar(value=self.user_profile["preferences"].get("voice_speed", 0.8) * 100)
        speed_scale = ttk.Scale(speed_frame, from_=50, to=150, variable=self.voice_speed_var,
                                orient=tk.HORIZONTAL, length=200)
        speed_scale.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        speed_label = ttk.Label(speed_frame, textvariable=tk.StringVar(value=f"{self.voice_speed_var.get():.0f}%"))
        self.voice_speed_var.trace_add("write", lambda *args: speed_label.config(
            text=f"{self.voice_speed_var.get():.0f}%"))
        speed_label.pack(side=tk.LEFT, padx=5)

        # Voice volume
        volume_frame = ttk.Frame(voice_frame)
        volume_frame.pack(fill=tk.X, pady=5)

        ttk.Label(volume_frame, text="Voice Volume:", font=self.text_font).pack(side=tk.LEFT)

        self.voice_volume_var = tk.DoubleVar(value=self.user_profile["preferences"].get("volume", 0.9) * 100)
        volume_scale = ttk.Scale(volume_frame, from_=50, to=100, variable=self.voice_volume_var,
                                 orient=tk.HORIZONTAL, length=200)
        volume_scale.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        volume_label = ttk.Label(volume_frame, textvariable=tk.StringVar(value=f"{self.voice_volume_var.get():.0f}%"))
        self.voice_volume_var.trace_add("write", lambda *args: volume_label.config(
            text=f"{self.voice_volume_var.get():.0f}%"))
        volume_label.pack(side=tk.LEFT, padx=5)

        # Test voice button
        ttk.Button(voice_frame, text="Test Voice Settings",
                   command=self.test_voice_settings).pack(anchor=tk.E, pady=5)

        # Display settings section
        display_frame = ttk.LabelFrame(settings_frame, text="Display Settings", padding=10)
        display_frame.pack(fill=tk.X, pady=10)

        # Font size
        font_frame = ttk.Frame(display_frame)
        font_frame.pack(fill=tk.X, pady=5)

        ttk.Label(font_frame, text="Font Size:", font=self.text_font).pack(side=tk.LEFT)

        self.font_size_var = tk.IntVar(value=12)  # Default size
        font_sizes = [("Small", 10), ("Medium", 12), ("Large", 14), ("Extra Large", 16)]

        font_radio_frame = ttk.Frame(font_frame)
        font_radio_frame.pack(side=tk.LEFT, padx=10)

        for text, size in font_sizes:
            ttk.Radiobutton(font_radio_frame, text=text, variable=self.font_size_var,
                            value=size).pack(side=tk.LEFT, padx=10)

        # Color theme
        theme_frame = ttk.Frame(display_frame)
        theme_frame.pack(fill=tk.X, pady=5)

        ttk.Label(theme_frame, text="Color Theme:", font=self.text_font).pack(side=tk.LEFT)

        self.theme_var = tk.StringVar(value="Default")
        themes = ["Default", "High Contrast", "Warm", "Cool"]

        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var, values=themes, state="readonly")
        theme_combo.pack(side=tk.LEFT, padx=10)

        # Apply button
        ttk.Button(display_frame, text="Apply Display Settings",
                   command=self.apply_display_settings).pack(anchor=tk.E, pady=5)

        # Reminder settings section
        reminder_frame = ttk.LabelFrame(settings_frame, text="Reminder Settings", padding=10)
        reminder_frame.pack(fill=tk.X, pady=10)

        # Reminder frequency
        freq_frame = ttk.Frame(reminder_frame)
        freq_frame.pack(fill=tk.X, pady=5)

        ttk.Label(freq_frame, text="Reminder Frequency:", font=self.text_font).pack(side=tk.LEFT)

        self.reminder_freq_var = tk.StringVar(value=self.user_profile["preferences"].get("reminder_frequency", "high"))
        freq_options = [("Low", "low"), ("Medium", "medium"), ("High", "high")]

        freq_radio_frame = ttk.Frame(freq_frame)
        freq_radio_frame.pack(side=tk.LEFT, padx=10)

        for text, value in freq_options:
            ttk.Radiobutton(freq_radio_frame, text=text, variable=self.reminder_freq_var,
                            value=value).pack(side=tk.LEFT, padx=10)

        # Save settings button
        ttk.Button(settings_frame, text="Save All Settings",
                   command=self.save_settings).pack(pady=10)

    def setup_reminder_thread(self):
        """Set up a thread to check for reminders."""
        self.reminder_queue = queue.Queue()

        def check_reminders():
            """Check for reminders in the background."""
            while True:
                try:
                    # Check reminder queue from voice assistant
                    if self.assistant_ready and hasattr(self.voice_assistant, 'response_queue'):
                        try:
                            reminder = self.voice_assistant.response_queue.get_nowait()
                            self.reminder_queue.put(reminder)
                            # Schedule UI update for the reminder
                            self.root.after(0, self.process_reminder, reminder)
                        except queue.Empty:
                            pass

                    # Check time-based reminders
                    self.check_time_based_reminders()

                    # Sleep to avoid high CPU usage
                    threading.Event().wait(30)  # Check every 30 seconds
                except Exception as e:
                    logger.error(f"Error in reminder thread: {str(e)}")
                    threading.Event().wait(60)  # Wait a bit longer after an error

        # Start the reminder thread
        reminder_thread = threading.Thread(target=check_reminders, daemon=True)
        reminder_thread.start()

    def check_time_based_reminders(self):
        """Check if any time-based reminders need to be triggered."""
        current_time = datetime.datetime.now().time()
        current_time_str = current_time.strftime("%H:%M")

        # Check medication times
        for medication in self.user_profile["medications"]:
            for time_str in medication["times"]:
                # If it's exactly medication time (checking every 30 seconds gives some flexibility)
                if time_str == current_time_str:
                    reminder = f"Time to take your {medication['name']}, {medication['dosage']}."
                    self.reminder_queue.put(reminder)
                    # Schedule UI update for the reminder
                    self.root.after(0, self.process_reminder, reminder)

    def process_reminder(self, reminder_text):
        """Process a reminder in the UI thread."""
        # Display reminder message
        self.display_assistant_message(reminder_text)

        # Show a popup notification
        messagebox.showinfo("ElderCare Reminder", reminder_text)

        # Speak the reminder if voice assistant is ready
        if self.assistant_ready:
            self.voice_assistant.speak(reminder_text)

    # def display_assistant_message(self, message):
    #     """Display a message from the assistant in the conversation display."""
    #     self.conversation_display.config(state=tk.NORMAL)
    #     self.conversation_display.insert(tk.END, f"ElderCare: {message}\n\n")
    #     self.conversation_display.see(tk.END)
    #     self.conversation_display.config(state=tk.DISABLED)
    def display_assistant_message(self, message):
        """Display a message from the assistant in the conversation display."""
        self.conversation_display.config(state=tk.NORMAL)
        self.conversation_display.insert(tk.END, f"ElderCare: {message}\n\n")
        self.conversation_display.see(tk.END)
        self.conversation_display.config(state=tk.DISABLED)

        # Only attempt to speak if the assistant is ready and not already speaking
        if self.assistant_ready and hasattr(self.voice_assistant, 'speak') and not self.voice_assistant.is_speaking:
            # Use a separate thread to avoid UI freezing during speech
            threading.Thread(target=lambda: self.voice_assistant.speak(message), daemon=True).start()

    def display_user_message(self, message):
        """Display a message from the user in the conversation display."""
        self.conversation_display.config(state=tk.NORMAL)
        self.conversation_display.insert(tk.END, f"You: {message}\n\n")
        self.conversation_display.see(tk.END)
        self.conversation_display.config(state=tk.DISABLED)

    def handle_text_input(self, event=None):
        """Handle text input from the entry field."""
        user_input = self.text_input.get().strip()

        if not user_input:
            return

        # Display user message
        self.display_user_message(user_input)

        # Clear input field
        self.text_input.delete(0, tk.END)

        # Process the input
        self.process_user_input(user_input)

    def handle_voice_input(self):
        """Handle voice input via the voice assistant."""
        if not self.assistant_ready:
            messagebox.showinfo("Voice Input", "Voice assistant is not available. Please use text input instead.")
            return

        # Update status
        self.status_label.config(text="Status: Listening...")

        # Use a separate thread for listening to avoid UI freeze
        def listen_thread():
            try:
                user_input = self.voice_assistant.listen()

                # Process results in the UI thread
                def process_results():
                    if user_input:
                        self.display_user_message(user_input)
                        self.process_user_input(user_input)
                    else:
                        self.display_assistant_message(
                            "I'm sorry, I couldn't understand you. Please try again or use text input.")

                    # Reset status
                    self.status_label.config(text="Status: Ready")

                self.root.after(0, process_results)

            except Exception as e:
                logger.error(f"Error in voice input: {str(e)}")
                self.root.after(0, lambda: self.status_label.config(text="Status: Ready"))

        threading.Thread(target=listen_thread, daemon=True).start()

    def handle_quick_action(self, action):
        """Handle quick action button clicks."""
        # Update status
        self.status_label.config(text=f"Status: Processing {action}...")

        # Display action in conversation
        self.display_user_message(f"[Quick Action: {action}]")

        # Process the action
        self.process_user_input(action)

    def process_user_input(self, user_input):
        """Process user input and generate a response."""
        # Handle special commands directly
        command = self.identify_command(user_input)

        if command == "exit":
            self.display_assistant_message("Goodbye! Closing the application...")
            self.root.after(2000, self.on_closing)  # Close after 2 seconds
            return

        # Use the voice assistant for processing if available
        if self.assistant_ready:
            # Process with voice assistant in a separate thread
            self.status_label.config(text="Status: Thinking...")

            def process_thread():
                try:
                    if command == "record glucose":
                        # Switch to health tab
                        self.notebook.select(self.health_tab)
                        self.handle_record_glucose_command()
                    elif command == "record sleep":
                        # Switch to health tab
                        self.notebook.select(self.health_tab)
                        self.handle_record_sleep_command()
                    elif command == "record medication":
                        # Switch to health tab
                        self.notebook.select(self.health_tab)
                        self.handle_record_medication_command()
                    elif command == "health data":
                        self.handle_health_data_command()
                    elif command == "emergency":
                        self.handle_emergency()
                    elif command == "list medications":
                        # Switch to medications tab
                        self.notebook.select(self.medications_tab)
                        self.handle_list_medications_command()
                    elif command == "help":
                        self.handle_help_command()
                    else:
                        # General processing with LLM
                        response = self.voice_assistant.process_with_groq(user_input)

                        # Update UI in the main thread
                        self.root.after(0, lambda: self.display_assistant_message(response))

                    # Reset status in the main thread
                    self.root.after(0, lambda: self.status_label.config(text="Status: Ready"))

                except Exception as e:
                    logger.error(f"Error processing input: {str(e)}")
                    self.root.after(0, lambda: self.display_assistant_message(
                        "I'm sorry, I encountered an error processing your request."))
                    self.root.after(0, lambda: self.status_label.config(text="Status: Ready"))

            threading.Thread(target=process_thread, daemon=True).start()

        else:
            # Simple fallback responses if assistant is not available
            if command:
                self.display_assistant_message(
                    f"I recognized the '{command}' command, but the voice assistant is not available. Please use the interface buttons instead.")
            else:
                self.display_assistant_message(
                    "I'm sorry, the voice assistant is not available. Please use the interface buttons for health tracking and other functions.")

            self.status_label.config(text="Status: Ready")

    def identify_command(self, user_input):
        """Identify command type from user input."""
        if not user_input:
            return None

        # Clean user input
        clean_input = user_input.lower().strip()

        # Command keywords dictionary
        command_keywords = {
            "record glucose": ["record glucose", "blood sugar", "glucose reading", "sugar level"],
            "record sleep": ["record sleep", "how i slept", "sleep hours", "hours of sleep"],
            "record medication": ["record medication", "took my pills", "medication taken", "medicines"],
            "health data": ["how am i doing", "my health data", "health report", "progress"],
            "emergency": ["emergency", "help me", "need help", "call for help", "urgent"],
            "update profile": ["update profile", "change my information", "update my details", "my profile"],
            "list medications": ["list medication", "my medication", "what medications", "show medicines"],
            "adjust voice": ["adjust voice", "change voice", "voice settings", "speak slower", "speak faster"],
            "help": ["help", "what can you do", "commands", "options", "features"],
            "exit": ["exit", "quit", "goodbye", "bye", "stop listening", "shut down"]
        }

        # Match commands
        for command, keywords in command_keywords.items():
            if clean_input in keywords:
                return command

            # Try partial matching
            if any(keyword in clean_input for keyword in keywords):
                return command

        return None

    # Health tab functions
    def record_glucose(self, value, time_period):
        """Record a glucose reading."""
        try:
            # Validate input
            if not value:
                messagebox.showinfo("Input Error", "Please enter a glucose value.")
                return

            glucose_value = float(value)

            # Check if the value is in a reasonable range
            if glucose_value < 20 or glucose_value > 600:
                messagebox.showinfo("Input Error", "Please enter a valid glucose value between 20 and 600.")
                return

            # Get today's date
            today = datetime.date.today().strftime('%Y-%m-%d')

            # Check if we already have an entry for today
            today_data = self.health_data[self.health_data['date'] == today]
            if today_data.empty:
                # Create new row for today
                new_row = {'date': today}
                self.health_data = pd.concat([self.health_data, pd.DataFrame([new_row])], ignore_index=True)

            # Update the appropriate column
            if time_period == "Morning":
                self.health_data.loc[self.health_data['date'] == today, 'glucose_morning'] = glucose_value
                feedback = f"Morning glucose recorded as {glucose_value}."
            else:
                self.health_data.loc[self.health_data['date'] == today, 'glucose_evening'] = glucose_value
                feedback = f"Evening glucose recorded as {glucose_value}."

            # Save data
            self.health_data.to_csv('health_data.csv', index=False)

            # Update display
            self.refresh_health_data()

            # Provide feedback
            messagebox.showinfo("Glucose Recorded", feedback)
            self.display_assistant_message(feedback)

            # Clear input
            self.glucose_var.set("")

        except ValueError:
            messagebox.showinfo("Input Error", "Please enter a numeric value for glucose.")

    def record_sleep(self, value):
        """Record sleep hours."""
        try:
            # Validate input
            if not value:
                messagebox.showinfo("Input Error", "Please enter sleep hours.")
                return

            sleep_hours = float(value)

            # Check if the value is in a reasonable range
            if sleep_hours < 0 or sleep_hours > 24:
                messagebox.showinfo("Input Error", "Please enter valid sleep hours between 0 and 24.")
                return

            # Get today's date
            today = datetime.date.today().strftime('%Y-%m-%d')

            # Check if we already have an entry for today
            today_data = self.health_data[self.health_data['date'] == today]
            if today_data.empty:
                # Create new row for today
                new_row = {'date': today}
                self.health_data = pd.concat([self.health_data, pd.DataFrame([new_row])], ignore_index=True)

            # Update sleep hours
            self.health_data.loc[self.health_data['date'] == today, 'sleep_hours'] = sleep_hours

            # Save data
            self.health_data.to_csv('health_data.csv', index=False)

            # Update display
            self.refresh_health_data()

            # Provide feedback
            feedback = f"Sleep hours recorded as {sleep_hours}."
            messagebox.showinfo("Sleep Recorded", feedback)
            self.display_assistant_message(feedback)

            # Clear input
            self.sleep_var.set("")

        except ValueError:
            messagebox.showinfo("Input Error", "Please enter a numeric value for sleep hours.")

    def record_medication(self, all_taken):
        """Record medication adherence."""
        # Get today's date
        today = datetime.date.today().strftime('%Y-%m-%d')

        # Check if we already have an entry for today
        today_data = self.health_data[self.health_data['date'] == today]
        if today_data.empty:
            # Create new row for today
            new_row = {'date': today}
            self.health_data = pd.concat([self.health_data, pd.DataFrame([new_row])], ignore_index=True)

        # Update medication adherence
        adherence_value = 1.0 if all_taken else 0.5
        self.health_data.loc[self.health_data['date'] == today, 'medication_adherence'] = adherence_value

        # Save data
        self.health_data.to_csv('health_data.csv', index=False)

        # Update display
        self.refresh_health_data()

        # Provide feedback
        if all_taken:
            feedback = "Great job! All medications taken today."
        else:
            feedback = "Some medications taken today. Remember to take all your prescribed medications."

        messagebox.showinfo("Medication Recorded", feedback)
        self.display_assistant_message(feedback)

    def save_health_notes(self):
        """Save notes to the health data."""
        # Get notes
        notes = self.notes_text.get("1.0", tk.END).strip()

        if not notes:
            return

        # Get today's date
        today = datetime.date.today().strftime('%Y-%m-%d')

        # Check if we already have an entry for today
        today_data = self.health_data[self.health_data['date'] == today]
        if today_data.empty:
            # Create new row for today
            new_row = {'date': today}
            self.health_data = pd.concat([self.health_data, pd.DataFrame([new_row])], ignore_index=True)

        # Update notes
        self.health_data.loc[self.health_data['date'] == today, 'notes'] = notes

        # Save data
        self.health_data.to_csv('health_data.csv', index=False)

        # Update display
        self.refresh_health_data()

        # Provide feedback
        messagebox.showinfo("Notes Saved", "Your health notes have been saved.")

        # Clear notes
        self.notes_text.delete("1.0", tk.END)

    def refresh_health_data(self):
        """Refresh the health data display."""
        # Clear current display
        self.health_data_display.config(state=tk.NORMAL)
        self.health_data_display.delete("1.0", tk.END)

        # Get recent data (last 7 days)
        recent_data = self.health_data.tail(7)

        if len(recent_data) == 0:
            self.health_data_display.insert(tk.END, "No health data recorded yet.")
        else:
            # Display date headers and data
            for _, row in recent_data.iterrows():
                date_str = row['date']

                # Try to format the date nicely
                try:
                    date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%A, %B %d, %Y')
                except:
                    formatted_date = date_str

                self.health_data_display.insert(tk.END, f"\n{formatted_date}\n", "heading")
                self.health_data_display.insert(tk.END, "-" * 40 + "\n")

                # Display glucose
                morning_glucose = row.get('glucose_morning')
                if pd.notna(morning_glucose):
                    self.health_data_display.insert(tk.END, f"Morning Glucose: {morning_glucose}\n")

                evening_glucose = row.get('glucose_evening')
                if pd.notna(evening_glucose):
                    self.health_data_display.insert(tk.END, f"Evening Glucose: {evening_glucose}\n")

                # Display sleep
                sleep_hours = row.get('sleep_hours')
                if pd.notna(sleep_hours):
                    self.health_data_display.insert(tk.END, f"Sleep Hours: {sleep_hours}\n")

                # Display medication
                med_adherence = row.get('medication_adherence')
                if pd.notna(med_adherence):
                    adherence_percent = int(med_adherence * 100)
                    self.health_data_display.insert(tk.END, f"Medication Adherence: {adherence_percent}%\n")

                # Display notes
                notes = row.get('notes')
                if pd.notna(notes) and notes:
                    self.health_data_display.insert(tk.END, f"\nNotes: {notes}\n")

                self.health_data_display.insert(tk.END, "\n")

        # Configure text tags
        self.health_data_display.tag_configure("heading", font=self.heading_font)

        self.health_data_display.config(state=tk.DISABLED)

    # Medications tab functions
    def load_medications(self):
        """Load medications into the treeview."""
        # Clear current items
        for item in self.meds_tree.get_children():
            self.meds_tree.delete(item)

        # Add medications from user profile
        for med in self.user_profile["medications"]:
            # Format times for display
            times_formatted = []
            for time_str in med["times"]:
                hour, minute = map(int, time_str.split(":"))
                if hour < 12:
                    time_display = f"{hour}:{minute:02d} AM"
                elif hour == 12:
                    time_display = f"12:{minute:02d} PM"
                else:
                    time_display = f"{hour - 12}:{minute:02d} PM"
                times_formatted.append(time_display)

            # Insert into treeview
            self.meds_tree.insert("", "end", text=med["name"],
                                  values=(med["dosage"], med["frequency"], ", ".join(times_formatted)))

    def add_medication(self):
        """Add a new medication to the user profile."""
        # Get medication details
        name = self.med_name_var.get().strip()
        dosage = self.med_dosage_var.get().strip()
        frequency = self.med_frequency_var.get()

        # Validate input
        if not name:
            messagebox.showinfo("Input Error", "Please enter a medication name.")
            return

        if not dosage:
            dosage = "N/A"

        if not frequency:
            frequency = "daily"

        # Collect selected times
        times = []
        if self.morning_var.get():
            times.append("08:00")
        if self.noon_var.get():
            times.append("12:00")
        if self.evening_var.get():
            times.append("18:00")
        if self.bedtime_var.get():
            times.append("22:00")

        if not times:
            messagebox.showinfo("Input Error", "Please select at least one medication time.")
            return

        # Create new medication entry
        new_med = {
            "name": name,
            "dosage": dosage,
            "frequency": frequency,
            "times": times
        }

        # Add to user profile
        self.user_profile["medications"].append(new_med)

        # Save user profile
        with open('user_profile.json', 'w') as file:
            json.dump(self.user_profile, file, indent=4)

        # Reload medications
        self.load_medications()

        # Provide feedback
        feedback = f"Medication '{name}' added successfully."
        messagebox.showinfo("Medication Added", feedback)
        self.display_assistant_message(feedback)

        # Clear input fields
        self.med_name_var.set("")
        self.med_dosage_var.set("")
        self.med_frequency_var.set("")
        self.morning_var.set(False)
        self.noon_var.set(False)
        self.evening_var.set(False)
        self.bedtime_var.set(False)
        self.med_notes_var.set("")

    def edit_medication(self):
        """Edit selected medication."""
        # Get selected item
        selected_item = self.meds_tree.selection()

        if not selected_item:
            messagebox.showinfo("Selection Error", "Please select a medication to edit.")
            return

        # Get medication name
        med_name = self.meds_tree.item(selected_item, "text")

        # Find medication in user profile
        for i, med in enumerate(self.user_profile["medications"]):
            if med["name"] == med_name:
                # Create popup for editing
                edit_window = tk.Toplevel(self.root)
                edit_window.title(f"Edit Medication: {med_name}")
                edit_window.geometry("400x400")
                edit_window.grab_set()  # Make window modal

                # Create form
                ttk.Label(edit_window, text="Medication Name:", font=self.text_font).pack(anchor=tk.W, pady=5)
                name_var = tk.StringVar(value=med["name"])
                ttk.Entry(edit_window, textvariable=name_var, font=self.text_font).pack(fill=tk.X, pady=5)

                ttk.Label(edit_window, text="Dosage:", font=self.text_font).pack(anchor=tk.W, pady=5)
                dosage_var = tk.StringVar(value=med["dosage"])
                ttk.Entry(edit_window, textvariable=dosage_var, font=self.text_font).pack(fill=tk.X, pady=5)

                ttk.Label(edit_window, text="Frequency:", font=self.text_font).pack(anchor=tk.W, pady=5)
                frequency_var = tk.StringVar(value=med["frequency"])
                frequency_combo = ttk.Combobox(edit_window, textvariable=frequency_var)
                frequency_combo['values'] = ("once daily", "twice daily", "three times daily", "as needed")
                frequency_combo.pack(fill=tk.X, pady=5)

                ttk.Label(edit_window, text="Times:", font=self.text_font).pack(anchor=tk.W, pady=5)

                # Time checkboxes
                morning_var = tk.BooleanVar(value="08:00" in med["times"])
                noon_var = tk.BooleanVar(value="12:00" in med["times"])
                evening_var = tk.BooleanVar(value="18:00" in med["times"])
                bedtime_var = tk.BooleanVar(value="22:00" in med["times"])

                ttk.Checkbutton(edit_window, text="Morning (8:00 AM)", variable=morning_var).pack(anchor=tk.W)
                ttk.Checkbutton(edit_window, text="Noon (12:00 PM)", variable=noon_var).pack(anchor=tk.W)
                ttk.Checkbutton(edit_window, text="Evening (6:00 PM)", variable=evening_var).pack(anchor=tk.W)
                ttk.Checkbutton(edit_window, text="Bedtime (10:00 PM)", variable=bedtime_var).pack(anchor=tk.W)

                # Save button
                def save_edit():
                    # Get updated values
                    new_name = name_var.get().strip()
                    new_dosage = dosage_var.get().strip()
                    new_frequency = frequency_var.get()

                    # Validate name
                    if not new_name:
                        messagebox.showinfo("Input Error", "Medication name cannot be empty.", parent=edit_window)
                        return

                    # Collect selected times
                    new_times = []
                    if morning_var.get():
                        new_times.append("08:00")
                    if noon_var.get():
                        new_times.append("12:00")
                    if evening_var.get():
                        new_times.append("18:00")
                    if bedtime_var.get():
                        new_times.append("22:00")

                    if not new_times:
                        messagebox.showinfo("Input Error", "Please select at least one medication time.",
                                            parent=edit_window)
                        return

                    # Update medication
                    self.user_profile["medications"][i]["name"] = new_name
                    self.user_profile["medications"][i]["dosage"] = new_dosage
                    self.user_profile["medications"][i]["frequency"] = new_frequency
                    self.user_profile["medications"][i]["times"] = new_times

                    # Save user profile
                    with open('user_profile.json', 'w') as file:
                        json.dump(self.user_profile, file, indent=4)

                    # Reload medications
                    self.load_medications()

                    # Close window
                    edit_window.destroy()

                    # Provide feedback
                    messagebox.showinfo("Medication Updated", f"Medication '{new_name}' updated successfully.")

                ttk.Button(edit_window, text="Save Changes", command=save_edit).pack(pady=20)

                # Cancel button
                ttk.Button(edit_window, text="Cancel", command=edit_window.destroy).pack()

                return

        # If we get here, medication was not found
        messagebox.showinfo("Error", "Could not find this medication in your profile.")

    def remove_medication(self):
        """Remove the selected medication."""
        # Get selected item
        selected_item = self.meds_tree.selection()

        if not selected_item:
            messagebox.showinfo("Selection Error", "Please select a medication to remove.")
            return

        # Get medication name
        med_name = self.meds_tree.item(selected_item, "text")

        # Confirm removal
        confirm = messagebox.askyesno("Confirm Removal",
                                      f"Are you sure you want to remove {med_name} from your medications?")

        if not confirm:
            return

        # Find and remove medication
        for i, med in enumerate(self.user_profile["medications"]):
            if med["name"] == med_name:
                del self.user_profile["medications"][i]

                # Save user profile
                with open('user_profile.json', 'w') as file:
                    json.dump(self.user_profile, file, indent=4)

                # Reload medications
                self.load_medications()

                # Provide feedback
                messagebox.showinfo("Medication Removed", f"Medication '{med_name}' removed successfully.")
                return

        # If we get here, medication was not found
        messagebox.showinfo("Error", "Could not find this medication in your profile.")

    def mark_medication_taken(self):
        """Mark the selected medication as taken."""
        # Get selected item
        selected_item = self.meds_tree.selection()

        if not selected_item:
            messagebox.showinfo("Selection Error", "Please select a medication to mark as taken.")
            return

        # Get medication name
        med_name = self.meds_tree.item(selected_item, "text")

        # Get today's date
        today = datetime.date.today().strftime('%Y-%m-%d')

        # Check if we already have an entry for today
        today_data = self.health_data[self.health_data['date'] == today]
        if today_data.empty:
            # Create new row for today
            new_row = {'date': today}
            self.health_data = pd.concat([self.health_data, pd.DataFrame([new_row])], ignore_index=True)

        # Update medication adherence (we would need a more sophisticated system to track individual medications)
        # For now, we'll just mark it as taken
        med_adherence = self.health_data.loc[self.health_data['date'] == today, 'medication_adherence'].iloc[
            0] if not today_data.empty and 'medication_adherence' in today_data.columns and not pd.isna(
            today_data['medication_adherence'].iloc[0]) else 0

        # Update to at least 0.5 if not already fully taken
        if pd.isna(med_adherence) or med_adherence < 0.5:
            self.health_data.loc[self.health_data['date'] == today, 'medication_adherence'] = 0.5

        # Save data
        self.health_data.to_csv('health_data.csv', index=False)

        # Update health data display
        self.refresh_health_data()

        # Provide feedback
        feedback = f"Recorded that you took {med_name} today."
        messagebox.showinfo("Medication Taken", feedback)
        self.display_assistant_message(feedback)

    # Profile tab functions
    def save_profile(self):
        """Save the user profile."""
        # Get profile data
        name = self.name_var.get().strip()

        try:
            age = int(self.age_var.get().strip())
            if age < 0 or age > 120:
                messagebox.showinfo("Input Error", "Please enter a valid age between 0 and 120.")
                return
        except ValueError:
            messagebox.showinfo("Input Error", "Please enter a numeric value for age.")
            return

        # Collect health conditions
        conditions = []
        if self.diabetes_var.get():
            conditions.append("diabetes")
        if self.hypertension_var.get():
            conditions.append("hypertension")
        if self.arthritis_var.get():
            conditions.append("arthritis")
        if self.heart_var.get():
            conditions.append("heart disease")

        # Add other conditions
        other_conditions = self.other_conditions_var.get().strip()
        if other_conditions:
            # Split by commas
            for condition in other_conditions.split(','):
                clean_condition = condition.strip().lower()
                if clean_condition and clean_condition not in conditions:
                    conditions.append(clean_condition)

        # Get emergency contact info
        contact_name = self.contact_name_var.get().strip()
        contact_phone = self.contact_phone_var.get().strip()

        # Update user profile
        self.user_profile["name"] = name
        self.user_profile["age"] = age
        self.user_profile["conditions"] = conditions
        self.user_profile["emergency_contact"]["name"] = contact_name
        self.user_profile["emergency_contact"]["phone"] = contact_phone

        # Save user profile
        with open('user_profile.json', 'w') as file:
            json.dump(self.user_profile, file, indent=4)

        # Provide feedback
        messagebox.showinfo("Profile Saved", "Your profile has been updated successfully.")

    # Settings tab functions
    def test_voice_settings(self):
        """Test the current voice settings."""
        if not self.assistant_ready:
            messagebox.showinfo("Voice Error", "Voice assistant is not available. Please check your API settings.")
            return

        # Update voice settings
        voice_speed = self.voice_speed_var.get() / 100 * 200  # Convert to speech engine rate
        voice_volume = self.voice_volume_var.get() / 100  # Convert to 0-1 scale

        self.voice_assistant.tts_engine.setProperty('rate', voice_speed)
        self.voice_assistant.tts_engine.setProperty('volume', voice_volume)

        # Speak test message
        self.voice_assistant.speak(
            f"Hello {self.user_profile['name']}. This is a test of the voice settings. How does this sound?")

    def apply_display_settings(self):
        """Apply the display settings."""
        # Get font size
        font_size = self.font_size_var.get()

        # Update fonts
        self.title_font.configure(size=font_size + 6)
        self.heading_font.configure(size=font_size + 2)
        self.text_font.configure(size=font_size)
        self.button_font.configure(size=font_size)

        # Update text areas
        self.conversation_display.configure(font=self.text_font)
        self.health_data_display.configure(font=self.text_font)

        # Apply theme (simplified)
        theme = self.theme_var.get()
        if theme == "High Contrast":
            self.root.configure(background="black")
            self.conversation_display.configure(background="black", foreground="white")
            self.health_data_display.configure(background="black", foreground="white")
        elif theme == "Warm":
            self.root.configure(background="#FFF8E1")
            self.conversation_display.configure(background="#FFECB3", foreground="black")
            self.health_data_display.configure(background="#FFECB3", foreground="black")
        elif theme == "Cool":
            self.root.configure(background="#E3F2FD")
            self.conversation_display.configure(background="#BBDEFB", foreground="black")
            self.health_data_display.configure(background="#BBDEFB", foreground="black")
        else:  # Default
            self.root.configure(background="")
            self.conversation_display.configure(background="white", foreground="black")
            self.health_data_display.configure(background="white", foreground="black")

        # Provide feedback
        messagebox.showinfo("Settings Applied", "Display settings have been applied.")

    def save_settings(self):
        """Save all settings to user profile."""
        # Get voice settings
        voice_speed = self.voice_speed_var.get() / 100
        voice_volume = self.voice_volume_var.get() / 100
        reminder_frequency = self.reminder_freq_var.get()

        # Update user profile
        self.user_profile["preferences"]["voice_speed"] = voice_speed
        self.user_profile["preferences"]["volume"] = voice_volume
        self.user_profile["preferences"]["reminder_frequency"] = reminder_frequency

        # Save user profile
        with open('user_profile.json', 'w') as file:
            json.dump(self.user_profile, file, indent=4)

        # Apply voice settings if assistant is ready
        if self.assistant_ready:
            self.voice_assistant.tts_engine.setProperty('rate', voice_speed * 200)
            self.voice_assistant.tts_engine.setProperty('volume', voice_volume)

        # Apply display settings
        self.apply_display_settings()

        # Provide feedback
        messagebox.showinfo("Settings Saved", "All settings have been saved successfully.")

    # Command handling functions
    def handle_record_glucose_command(self):
        """Handle the record glucose command."""
        self.display_assistant_message(
            "Please enter your glucose reading in the health tab. You can specify if it's morning or evening.")

    def handle_record_sleep_command(self):
        """Handle the record sleep command."""
        self.display_assistant_message("Please enter your sleep hours in the health tab.")

    def handle_record_medication_command(self):
        """Handle the record medication command."""
        self.display_assistant_message(
            "Please use the medication tracking in the health tab to record your medication.")

    def handle_health_data_command(self):
        """Handle the health data command."""
        # Switch to health tab
        self.notebook.select(self.health_tab)

        # Analyze health data
        if self.assistant_ready:
            analysis = self.voice_assistant.analyze_health_data()
            self.display_assistant_message(analysis)
        else:
            # Provide simple analysis if assistant is not available
            try:
                recent_data = self.health_data.tail(7)

                if len(recent_data) < 3:
                    self.display_assistant_message("I don't have enough health data yet to identify any trends.")
                    return

                insights = []

                # Check glucose
                if 'glucose_morning' in recent_data.columns and not recent_data['glucose_morning'].isna().all():
                    avg_morning = recent_data['glucose_morning'].mean()
                    if avg_morning > 180:
                        insights.append(
                            f"Your morning blood sugar has been running high at around {avg_morning:.0f} on average.")
                    elif avg_morning < 70:
                        insights.append(
                            f"Your morning blood sugar has been running low at around {avg_morning:.0f} on average.")
                    else:
                        insights.append(
                            f"Your morning blood sugar has been in a good range at around {avg_morning:.0f} on average.")

                # Check sleep
                if 'sleep_hours' in recent_data.columns and not recent_data['sleep_hours'].isna().all():
                    avg_sleep = recent_data['sleep_hours'].mean()
                    if avg_sleep < 6:
                        insights.append(
                            f"You've been getting about {avg_sleep:.1f} hours of sleep on average, which is less than recommended.")
                    else:
                        insights.append(
                            f"You've been getting about {avg_sleep:.1f} hours of sleep on average, which is good.")

                if insights:
                    self.display_assistant_message(" ".join(insights))
                else:
                    self.display_assistant_message(
                        "I don't have enough data to provide insights. Please continue recording your health data.")

            except Exception as e:
                logger.error(f"Error analyzing health data: {str(e)}")
                self.display_assistant_message("I'm having trouble analyzing your health data right now.")

    def handle_emergency(self):
        """Handle emergency situation."""
        emergency_window = tk.Toplevel(self.root)
        emergency_window.title("EMERGENCY")
        emergency_window.geometry("500x300")
        emergency_window.configure(background="#ffcccc")
        emergency_window.grab_set()  # Make window modal

        ttk.Label(emergency_window, text="EMERGENCY CONTACT",
                  font=font.Font(family="Arial", size=16, weight="bold"),
                  background="#ffcccc").pack(pady=10)

        contact = self.user_profile["emergency_contact"]

        ttk.Label(emergency_window, text=f"Contacting: {contact['name']}",
                  font=self.heading_font,
                  background="#ffcccc").pack(pady=5)

        ttk.Label(emergency_window, text=f"Phone: {contact['phone']}",
                  font=self.heading_font,
                  background="#ffcccc").pack(pady=5)

        ttk.Label(emergency_window, text="Please describe your emergency:",
                  background="#ffcccc").pack(pady=10)

        emergency_text = scrolledtext.ScrolledText(emergency_window, height=5, width=40)
        emergency_text.pack(pady=5, padx=20)

        def call_emergency():
            # In a real app, this would connect to an actual emergency service
            emergency_note = emergency_text.get("1.0", tk.END).strip()

            messagebox.showinfo("Emergency Contact",
                                f"Emergency services would be contacted with message: {emergency_note}",
                                parent=emergency_window)

            self.display_assistant_message(f"Emergency contact {contact['name']} would be notified with your message.")

            emergency_window.destroy()

        ttk.Button(emergency_window, text="CALL FOR HELP",
                   command=call_emergency,
                   style="Large.TButton").pack(pady=20)

        ttk.Button(emergency_window, text="Cancel - Not an Emergency",
                   command=emergency_window.destroy).pack()

        # Speak emergency message if assistant is ready
        if self.assistant_ready:
            self.voice_assistant.speak(
                f"Emergency mode activated. Preparing to contact {contact['name']}. Please describe your emergency.")

    def handle_list_medications_command(self):
        """Handle the list medications command."""
        medications = self.user_profile["medications"]

        if not medications:
            self.display_assistant_message("You don't have any medications in your profile yet.")
            return

        med_list = "Here are your current medications:\n\n"

        for med in medications:
            # Format times
            times_of_day = []
            for time_str in med["times"]:
                hour = int(time_str.split(":")[0])
                if hour < 12:
                    times_of_day.append(f"{hour} AM")
                elif hour == 12:
                    times_of_day.append("noon")
                else:
                    times_of_day.append(f"{hour - 12} PM")

            times_formatted = ", ".join(times_of_day)

            med_list += f"- {med['name']}, {med['dosage']}, {med['frequency']}, at {times_formatted}\n"

        self.display_assistant_message(med_list)

    def handle_help_command(self):
        """Handle the help command."""
        help_text = """
Here are things I can help you with:

HEALTH TRACKING:
- Record glucose
- Record sleep
- Record medication
- View health data trends

MEDICATIONS:
- List medications
- Add/edit/remove medications
- Medication reminders

PROFILE & SETTINGS:
- Update your profile
- Adjust voice settings
- Change display settings

You can use the buttons or type your requests. For detailed help on specific features, switch to the relevant tab.
"""
        self.display_assistant_message(help_text)

    def on_closing(self):
        """Handle application closing."""
        # Save data
        if hasattr(self, 'health_data'):
            self.health_data.to_csv('health_data.csv', index=False)

        with open('user_profile.json', 'w') as file:
            json.dump(self.user_profile, file, indent=4)

        # Close the voice assistant if available
        if self.assistant_ready:
            self.voice_assistant.save_user_data()

        # Close the application
        self.root.destroy()


# Main application
def main():
    root = tk.Tk()
    app = ElderCareGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()