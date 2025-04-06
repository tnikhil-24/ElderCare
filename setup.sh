#!/bin/bash
# Installation and setup script for ElderCare Voice Assistant

# Create virtual environment
echo "Creating Python virtual environment..."
python -m venv eldercare_env

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source eldercare_env/Scripts/activate
else
    # Linux/Mac
    source eldercare_env/bin/activate
fi

# Install required packages
echo "Installing required packages..."
pip install --upgrade pip
pip install requests
pip install pandas
pip install schedule
pip install SpeechRecognition
pip install gtts
pip install pygame
pip install python-dotenv
pip install numpy

# Install PyAudio (required for speech recognition)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    pip install pipwin
    pipwin install pyaudio
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    brew install portaudio
    pip install pyaudio
else
    # Linux
    sudo apt-get update
    sudo apt-get install python3-pyaudio
fi

# Create .env file for API keys
echo "Creating environment file for API keys..."
cat > .env << EOL
# API Keys
GROQ_API_KEY=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

# Configuration
LOG_LEVEL=INFO
EOL

echo "Setup complete! Please edit the .env file to add your Groq API key."
echo "Run the assistant with: python eldercare_assistant.py"