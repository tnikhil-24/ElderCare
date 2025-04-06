# ElderCare Voice Assistant

## Overview
ElderCare Voice Assistant is a comprehensive health management system designed specifically for older adults. The application combines an intuitive graphical user interface with voice-based interaction to help seniors track health metrics, manage medications, and maintain their wellbeing with minimal technical expertise required.

## Features
- **Voice-Enabled Interaction**: Natural conversation interface designed for seniors
- **Health Tracking**: Monitor glucose levels, sleep patterns, and other vital metrics
- **Medication Management**: Track medications and receive timely reminders
- **Emergency Assistance**: Quick access to emergency contacts 
- **Accessibility-Focused Design**: Adjustable font sizes, high-contrast options, and simplified navigation
- **AI-Powered Assistance**: Uses Groq LLM API to provide natural, helpful responses

## System Requirements
- Python 3.7 or higher
- Internet connection (for voice processing and AI features)
- Microphone (for voice input)
- Speakers (for voice output)
- 200MB free disk space
- 4GB RAM recommended

## Installation

### Prerequisites
The following Python packages are required:
- pyttsx3
- SpeechRecognition
- numpy
- pandas
- schedule
- requests
- python-dotenv
- pillow
- tkinter (usually comes with Python)

### Quick Start
1. Clone or download this repository
2. Run the launcher script:
```
python eldercare_launcher.py
```
3. Follow the setup wizard to install dependencies and configure your API key
4. The application will automatically create necessary data files on first run

### Manual Setup
If the automatic setup fails, you can install dependencies manually:
```
pip install pyttsx3 SpeechRecognition numpy pandas schedule requests python-dotenv pillow
```

## Configuration
- Create a `.env` file in the application directory with your Groq API key:
```
GROQ_API_KEY=your_api_key_here
```
- Alternatively, set the API key as an environment variable:
```
export GROQ_API_KEY=your_api_key_here  # On Linux/Mac
set GROQ_API_KEY=your_api_key_here     # On Windows
```

## Usage

### Main Interface
The ElderCare Voice Assistant features a tabbed interface with the following sections:

1. **Assistant**: Conversational interface for voice or text interaction
2. **Health Tracking**: Record and view health metrics
3. **Medications**: Manage medication schedule and reminders
4. **Profile**: Update personal information and emergency contacts
5. **Settings**: Customize voice and display preferences

### Voice Commands
Common voice commands include:
- "Record glucose" - Log blood glucose readings
- "Record sleep" - Track sleep duration
- "Record medication" - Log medication adherence
- "How am I doing?" - Get a health summary
- "List medications" - Review current medications
- "Help" - Get assistance with using the application

### Quick Actions
The main screen features quick action buttons for common tasks without requiring voice input.

### Emergency Features
The prominently displayed emergency button provides immediate access to emergency contacts.

## Troubleshooting

### Speech Recognition Issues
- Ensure your microphone is properly connected and selected as the default input device
- Speak clearly and at a moderate pace
- Try adjusting the voice recognition sensitivity in the Settings tab
- If voice recognition consistently fails, use the text input as an alternative

### Text-to-Speech Problems
If the assistant's voice is not working properly:
- Try adjusting the voice settings (speed and volume) in the Settings tab
- Check that your system's audio output is working with other applications
- Try restarting the application
- Ensure pyttsx3 is properly installed

### API Connection Problems
- Verify your internet connection
- Check that your API key is correctly configured
- Ensure your API key has not expired

## Files and Structure

- `eldercare_launcher.py` - Main entry point script
- `eldercare_integration.py` - Handles setup and configuration
- `eldercare_assistant.py` - Core voice assistant functionality
- `eldercare_gui.py` - Graphical user interface
- `user_profile.json` - Stores user information and preferences
- `health_data.csv` - Stores health tracking data
- `.env` - Contains API keys and configuration

## Customization

The application can be customized in several ways:

1. **Voice Settings**: Adjust speed and volume in the Settings tab
2. **Display Settings**: Change font size and color theme for better visibility
3. **Reminder Frequency**: Adjust how often you receive medication reminders
4. **User Profile**: Customize health conditions and medications

## Data Privacy and Security

- All user data is stored locally on your device
- No health information is shared with external services
- API connections for voice processing use secure HTTPS
- Emergency contact information is only used when explicitly requested

## Support and Contributions

For questions, bug reports, or feature requests:
- Open an issue on the GitHub repository
- Contact the development team at: support@eldercare-assistant.example.com

Contributions to the project are welcome:
- Fork the repository
- Make your changes
- Submit a pull request with a detailed description of your improvements

## License
This software is provided under the MIT License. See LICENSE file for details.

## Acknowledgments
- Groq for providing LLM API access
- The Python speech recognition community
- Beta testers and healthcare advisors who provided valuable feedback