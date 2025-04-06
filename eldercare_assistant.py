"""
Eldercare Improved Voice Assistant - A GenAI-powered health management system for older adults
With enhanced voice recognition and more natural conversation flow
"""

import os
import json
import datetime
import time
import threading
import queue
import numpy as np
import pandas as pd
import schedule
import requests
import pyttsx3
import speech_recognition as sr
import logging
from dotenv import load_dotenv
import re

# Load environment variables for API keys
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='eldercare_assistant.log'
)
logger = logging.getLogger('ElderCare')


class ElderCareVoiceAssistant:
    """Voice-based assistant for helping older adults manage health conditions."""

    def __init__(self):
        """Initialize the assistant with user profile and necessary components."""
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            logger.error("GROQ API key not found. Please set it in your environment variables.")
            raise ValueError("GROQ API key not found")

        # Initialize text-to-speech engine
        self.tts_engine = pyttsx3.init()

        # Configure voice properties
        voices = self.tts_engine.getProperty('voices')
        # Try to find a female voice (often preferred for assistants)
        for voice in voices:
            if "female" in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break

        # Set default voice properties - slower and clearer for older adults
        self.tts_engine.setProperty('rate', 150)  # Slower speed
        self.tts_engine.setProperty('volume', 0.9)  # Slightly louder

        # Initialize speech recognition
        self.recognizer = sr.Recognizer()

        # Adjust speech recognition parameters for better performance
        self.recognizer.energy_threshold = 300  # Default is 300
        self.recognizer.dynamic_energy_threshold = True  # Automatically adjust for ambient noise
        self.recognizer.pause_threshold = 1.0  # How much silence to allow before considering a phrase complete (longer)

        # Response queue for scheduled reminders
        self.response_queue = queue.Queue()

        # User data storage
        self.user_profile = self._load_user_profile()
        self.health_data = self._load_health_data()

        # Set current context
        self.context = {
            "last_interaction_time": None,
            "current_conversation": [],
            "pending_reminders": [],
            "listening_mode": True,
            "confidence_threshold": 0.5,  # Lower threshold to catch more speech
            "listening_timeout": 10,  # Longer timeout
            "phrase_time_limit": 15  # Longer phrase time limit
        }

        # Wait indicators
        self.wait_phrases = [
            "I'm listening...",
            "Go ahead, I'm listening.",
            "Please continue, I'm listening.",
            "Take your time, I'm here."
        ]

        # Command keywords
        self.command_keywords = {
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

        # Optional audio feedback
        self.use_audio_feedback = True

        # Wait flag to prevent interruptions
        self.is_speaking = False

        logger.info("ElderCare Voice Assistant initialized successfully")

    def _load_user_profile(self):
        """Load user profile from file or create default profile if not exists."""
        try:
            with open('user_profile.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            # Create a default profile
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
                    "voice_speed": 0.8,  # Slower default speed
                    "volume": 0.9,
                    "reminder_frequency": "high",
                    "speaking_style": "gentle"
                }
            }

            with open('user_profile.json', 'w') as file:
                json.dump(default_profile, file, indent=4)
            logger.info("Created default user profile")
            return default_profile

    def _load_health_data(self):
        """Load health tracking data or create empty dataset if not exists."""
        try:
            return pd.read_csv('health_data.csv')
        except FileNotFoundError:
            # Create empty health data tracking
            df = pd.DataFrame(columns=[
                'date', 'glucose_morning', 'glucose_evening',
                'medication_adherence', 'sleep_hours', 'activity_minutes',
                'mood', 'pain_level', 'notes'
            ])
            df.to_csv('health_data.csv', index=False)
            logger.info("Created empty health data tracking file")
            return df

    def save_user_data(self):
        """Save user profile and health data to files."""
        with open('user_profile.json', 'w') as file:
            json.dump(self.user_profile, file, indent=4)

        self.health_data.to_csv('health_data.csv', index=False)
        logger.info("Saved user data to files")

    def audio_feedback(self, sound_type):
        """Provide audio feedback for different interactions."""
        if not self.use_audio_feedback:
            return

        if sound_type == "listening":
            # A short gentle tone to indicate listening
            print("🎤 Listening...")
            self.tts_engine.setProperty('rate', 200)
            self.tts_engine.setProperty('volume', 0.4)
            self.tts_engine.say("I'm listening.")
            self.tts_engine.runAndWait()
            # Reset to normal properties
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
        elif sound_type == "acknowledged":
            # A short confirmation sound
            print("✓ Acknowledged")

    def listen(self):
        """Enhanced listening function with multiple attempts and better feedback."""
        # Visual indicator that assistant is ready to listen
        print("\n" + "=" * 50)
        print("🎤 I'm listening... (speak clearly, take your time)")
        print("=" * 50)

        # Audio feedback
        self.audio_feedback("listening")

        # Track failed attempts
        attempts = 0
        max_attempts = 3

        while attempts < max_attempts:
            try:
                with sr.Microphone() as source:
                    # Adjust for ambient noise before each listening attempt
                    print("Adjusting for ambient noise... (please be quiet for a moment)")
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)

                    # Randomly select a wait phrase for longer waiting
                    if attempts > 0:
                        wait_phrase = np.random.choice(self.wait_phrases)
                        print(f"\n{wait_phrase}")

                    # Longer timeout and phrase time limit
                    audio = self.recognizer.listen(
                        source,
                        timeout=self.context["listening_timeout"],
                        phrase_time_limit=self.context["phrase_time_limit"]
                    )

                    print("Processing what you said...")

                    # Try to recognize speech with Google (most accurate)
                    try:
                        text = self.recognizer.recognize_google(audio)
                        if text:
                            print(f"\nYou said: \"{text}\"")
                            logger.info(f"Recognized speech: {text}")
                            return text.lower()
                    except sr.UnknownValueError:
                        # Couldn't understand the speech
                        attempts += 1
                        if attempts < max_attempts:
                            print("I didn't quite catch that. Could you please speak a bit more clearly?")
                            time.sleep(1)  # Brief pause before next attempt
                        continue
                    except sr.RequestError:
                        # API unavailable, try local recognition as fallback
                        try:
                            # Try to use an offline recognition engine if available
                            text = self.recognizer.recognize_sphinx(audio)
                            if text:
                                print(f"\nYou said: \"{text}\" (offline recognition)")
                                logger.info(f"Recognized speech (offline): {text}")
                                return text.lower()
                        except:
                            # Offline recognition also failed
                            attempts += 1
                            if attempts < max_attempts:
                                print("I'm having trouble understanding. Let's try again.")
                                time.sleep(1)
                            continue

            except Exception as e:
                logger.error(f"Error in speech recognition: {str(e)}")
                attempts += 1
                if attempts < max_attempts:
                    print(f"Sorry, there was a problem with the microphone. Let's try again.")
                    time.sleep(1)
                continue

        # If we get here, all attempts failed
        print("\nI'm having trouble understanding you. You can type 'help' for assistance or try speaking again later.")
        return None

    # def speak(self, text):
    #     """Convert text to speech with improved flow and clarity."""
    #     try:
    #         # Set speaking flag to prevent interruptions
    #         self.is_speaking = True
    #
    #         # Log what will be spoken
    #         print(f"\nElderCare: {text}")
    #
    #         # Break text into natural sentences for more natural speech
    #         sentences = re.split(r'(?<=[.!?])\s+', text)
    #
    #         for sentence in sentences:
    #             if sentence.strip():  # Skip empty sentences
    #                 # Speak the sentence
    #                 self.tts_engine.say(sentence.strip())
    #                 self.tts_engine.runAndWait()
    #
    #                 # Brief pause between sentences for more natural flow
    #                 time.sleep(0.3)
    #
    #         # Add to conversation context
    #         self.context["current_conversation"].append({"role": "assistant", "content": text})
    #         logger.info(f"Assistant spoke: {text}")
    #
    #         # Clear speaking flag
    #         self.is_speaking = False
    #
    #     except Exception as e:
    #         logger.error(f"Error in text-to-speech: {str(e)}")
    #         print(f"\nElderCare: {text} (TTS Error)")
    #         self.is_speaking = False
    def speak(self, text):
        """Convert text to speech with improved flow and clarity."""
        try:
            # Set speaking flag to prevent interruptions
            self.is_speaking = True

            # Log what will be spoken
            print(f"\nElderCare: {text}")

            # Check if the text-to-speech engine is initialized properly
            if not self.tts_engine:
                self.tts_engine = pyttsx3.init()
                # Reset voice properties
                self.tts_engine.setProperty('rate', 150)  # Slower speed
                self.tts_engine.setProperty('volume', 0.9)  # Slightly louder

            # Break text into natural sentences for more natural speech
            sentences = re.split(r'(?<=[.!?])\s+', text)

            for sentence in sentences:
                if sentence.strip():  # Skip empty sentences
                    # Remove any special characters that might interfere with speech
                    clean_sentence = re.sub(r'[^a-zA-Z0-9.,!? ]', '', sentence.strip())

                    # Speak the sentence
                    self.tts_engine.say(clean_sentence)
                    self.tts_engine.runAndWait()

                    # Brief pause between sentences for more natural flow
                    time.sleep(0.3)

            # Add to conversation context
            self.context["current_conversation"].append({"role": "assistant", "content": text})
            logger.info(f"Assistant spoke: {text}")

            # Clear speaking flag
            self.is_speaking = False

        except Exception as e:
            logger.error(f"Error in text-to-speech: {str(e)}")
            print(f"\nElderCare: {text} (TTS Error)")
            self.is_speaking = False

    def process_with_groq(self, user_input):
        """Process user input using Groq LLM API with improved context management."""
        try:
            # Prepare system prompt that defines the assistant's behavior
            system_prompt = """
            You are a health assistant for older adults named ElderCare. Your primary goal is to help older adults manage their health conditions, particularly diabetes, medication adherence, and healthy lifestyle. 

            Important guidelines:
            1. Use clear, simple language appropriate for older adults (avoid jargon)
            2. Be patient and use shorter sentences with one idea per sentence
            3. Provide specific, actionable advice
            4. Always maintain a warm, respectful tone
            5. Focus on positive reinforcement and encouragement
            6. Keep responses concise - no more than 3-4 short sentences at a time
            7. Recognize possible emergency situations and advise appropriate action
            8. For non-emergency medical questions, remind users to consult healthcare professionals
            9. Always check understanding before moving to a new topic
            10. Don't rush the conversation - older adults need time to process information

            When asked about health data, analyze trends and provide gentle observations.
            """

            # Build conversation history for context
            messages = [{"role": "system", "content": system_prompt}]

            # Add relevant user profile information for context
            user_context = f"""
            USER PROFILE INFORMATION:
            Name: {self.user_profile['name']}
            Age: {self.user_profile['age']}
            Health conditions: {', '.join(self.user_profile['conditions'])}
            Medications: {', '.join([med['name'] + ' ' + med['dosage'] + ' ' + med['frequency'] for med in self.user_profile['medications']])}

            Current date and time: {datetime.datetime.now().strftime('%A, %B %d, %Y, %H:%M')}
            """
            messages.append({"role": "system", "content": user_context})

            # Add recent conversation history for context (last 5 exchanges)
            for exchange in self.context["current_conversation"][-10:]:
                messages.append(exchange)

            # Add current user input
            messages.append({"role": "user", "content": user_input})

            # Add specific guidance for response format
            response_format = """
            Response Guidelines:
            1. Break information into small, digestible chunks
            2. Use simple language with clear transitions between topics
            3. Keep responses under 150 words total
            4. Talk about one thing at a time (don't overwhelm with multiple topics)
            5. Include pauses for processing information
            6. Ask one simple question at a time, if appropriate
            7. Avoid rushing or overwhelming the user
            """
            messages.append({"role": "system", "content": response_format})

            # Make API call to Groq
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "llama3-70b-8192",  # Using Llama 3 70B through Groq
                "messages": messages,
                "temperature": 0.6,  # Lower temperature for more consistent responses
                "max_tokens": 350,  # Shorter responses
                "top_p": 0.9
            }

            print("Thinking...")

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                assistant_response = result["choices"][0]["message"]["content"]

                # Store in conversation context
                self.context["current_conversation"].append({"role": "user", "content": user_input})

                logger.info(f"Received response from Groq API: {assistant_response[:100]}...")
                return assistant_response
            else:
                logger.error(f"Error from Groq API: {response.status_code} {response.text}")
                return "I'm having trouble thinking right now. Can we try again in a moment?"

        except Exception as e:
            logger.error(f"Error processing with Groq: {str(e)}")
            return "I apologize, but I'm experiencing a technical issue. Let's try again."

    def identify_command(self, user_input):
        """Identify the command type from user input using improved matching."""
        if not user_input:
            return None

        # Clean user input to improve matching
        clean_input = user_input.lower().strip()

        # Match exact commands first
        for command, keywords in self.command_keywords.items():
            if clean_input in keywords:
                return command

        # Then try partial matching
        for command, keywords in self.command_keywords.items():
            if any(keyword in clean_input for keyword in keywords):
                return command

        return None

    def analyze_health_data(self):
        """Analyze health data for trends and generate insights."""
        try:
            if len(self.health_data) < 3:
                return "I don't have enough health data yet to identify any trends."

            recent_data = self.health_data.tail(7)  # Look at last week

            insights = []

            # Analyze glucose
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

            # Analyze medication adherence
            if 'medication_adherence' in recent_data.columns and not recent_data['medication_adherence'].isna().all():
                adherence_rate = recent_data['medication_adherence'].mean() * 100
                if adherence_rate < 80:
                    insights.append(
                        f"You've been taking your medications about {adherence_rate:.0f}% of the time. Let's work on improving that.")
                else:
                    insights.append(f"Great job taking your medications about {adherence_rate:.0f}% of the time.")

            # Analyze sleep patterns
            if 'sleep_hours' in recent_data.columns and not recent_data['sleep_hours'].isna().all():
                avg_sleep = recent_data['sleep_hours'].mean()
                if avg_sleep < 6:
                    insights.append(
                        f"You've been getting about {avg_sleep:.1f} hours of sleep on average, which is less than recommended.")
                else:
                    insights.append(
                        f"You've been getting about {avg_sleep:.1f} hours of sleep on average, which is good.")

            # Combine insights
            if not insights:
                return "I don't have enough recent health data to provide meaningful insights."

            return " ".join(insights)

        except Exception as e:
            logger.error(f"Error analyzing health data: {str(e)}")
            return "I'm having trouble analyzing your health data right now."

    def _schedule_reminders(self):
        """Set up scheduled medication and activity reminders."""
        # Clear existing jobs
        schedule.clear()

        # Schedule medication reminders
        for medication in self.user_profile["medications"]:
            for time_str in medication["times"]:
                hour, minute = map(int, time_str.split(":"))
                reminder_text = f"Time to take your {medication['name']}, {medication['dosage']}."

                schedule.every().day.at(time_str).do(
                    lambda text=reminder_text: self.response_queue.put(text)
                )
                logger.info(f"Scheduled medication reminder for {medication['name']} at {time_str}")

        # Schedule general health reminders
        schedule.every().day.at("10:00").do(
            lambda: self.response_queue.put("Remember to drink water throughout the day.")
        )

        schedule.every().day.at("14:00").do(
            lambda: self.response_queue.put("It's a good time for a short walk if you're feeling up to it.")
        )

        schedule.every().day.at("20:00").do(
            lambda: self.response_queue.put("Would you like to record your health data for today?")
        )

    def _reminder_thread(self):
        """Background thread to check and trigger scheduled reminders."""
        while True:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds

    def record_health_data(self, data_type):
        """Guide the user through recording specific health data with improved interaction."""
        today = datetime.date.today().strftime('%Y-%m-%d')

        # Check if we already have an entry for today
        today_data = self.health_data[self.health_data['date'] == today]
        if today_data.empty:
            # Create new row for today
            new_row = {'date': today}
            self.health_data = pd.concat([self.health_data, pd.DataFrame([new_row])], ignore_index=True)

        if data_type == "glucose":
            self.speak("Let's record your blood glucose reading. What was your blood glucose number?")
            value = self.listen()

            # If voice recognition fails, try again with clearer instructions
            if not value:
                self.speak("I need a number for your blood glucose reading. For example, say one hundred and twenty.")
                value = self.listen()

                # If it fails again, give up
                if not value:
                    self.speak(
                        "I'm having trouble understanding your glucose reading. Let's try again later when the voice recognition is working better.")
                    return

            try:
                # Extract numbers from the response
                number_match = re.search(r'\d+\.?\d*', value)
                if number_match:
                    glucose_value = float(number_match.group())
                else:
                    # Try removing non-numeric characters
                    glucose_value = float(value.replace("mg", "").strip())

                # Ask for timing with clear options
                self.speak("Was this your morning reading or evening reading?")
                timing = self.listen()

                # If voice recognition fails, try with more structured options
                if not timing:
                    self.speak("Please say either 'morning' or 'evening' to tell me when you took this reading.")
                    timing = self.listen()

                    # If it fails again, default to morning
                    if not timing:
                        self.speak("I'll record this as your morning glucose reading.")
                        timing = "morning"

                if "morning" in timing.lower():
                    self.health_data.loc[self.health_data['date'] == today, 'glucose_morning'] = glucose_value
                    self.speak(
                        f"I've recorded your morning glucose as {glucose_value}. Is there anything else about your glucose you'd like to share?")
                else:
                    self.health_data.loc[self.health_data['date'] == today, 'glucose_evening'] = glucose_value
                    self.speak(
                        f"I've recorded your evening glucose as {glucose_value}. Is there anything else about your glucose you'd like to share?")

                self.save_user_data()

            except Exception as e:
                logger.error(f"Error recording glucose: {str(e)}")
                self.speak("I'm sorry, I couldn't understand that reading. Let's try again later.")

        elif data_type == "sleep":
            self.speak("Let's record your sleep. How many hours did you sleep last night?")
            value = self.listen()

            # If voice recognition fails, try again with clearer instructions
            if not value:
                self.speak(
                    "Please tell me the number of hours you slept. For example, say 'seven hours' or 'six and a half hours'.")
                value = self.listen()

                # If it fails again, give up
                if not value:
                    self.speak(
                        "I'm having trouble understanding your sleep hours. Let's try again later when the voice recognition is working better.")
                    return

            try:
                # Extract numbers from the response
                number_match = re.search(r'\d+\.?\d*', value)
                if number_match:
                    hours = float(number_match.group())
                else:
                    hours = float(value.replace("hours", "").replace("hour", "").strip())

                # Validate the number makes sense
                if hours > 0 and hours <= 24:
                    self.health_data.loc[self.health_data['date'] == today, 'sleep_hours'] = hours

                    # Provide feedback based on amount of sleep
                    if hours < 6:
                        self.speak(
                            f"I've recorded {hours} hours of sleep. That's a bit low. Did you have trouble sleeping?")
                    elif hours > 10:
                        self.speak(
                            f"I've recorded {hours} hours of sleep. That's quite a lot of sleep. Are you feeling well rested?")
                    else:
                        self.speak(
                            f"I've recorded {hours} hours of sleep. That's a good amount of sleep. Are you feeling rested today?")
                else:
                    self.speak(f"{hours} hours doesn't seem right. Please tell me again how many hours you slept.")
                    return

                self.save_user_data()
            except Exception as e:
                logger.error(f"Error recording sleep: {str(e)}")
                self.speak("I'm sorry, I couldn't understand that value. Let's try again later.")

        elif data_type == "medication":
            self.speak("Let's record your medication. Did you take all your medications today? Please say yes or no.")
            response = self.listen()

            # If voice recognition fails, try again with more structured options
            if not response:
                self.speak("I need to know if you took your medications. Please say yes or no.")
                response = self.listen()

                # If it fails again, ask for more information
                if not response:
                    self.speak(
                        "I'm having trouble understanding. Let's try a different approach. Which medications did you take today?")
                    medications_taken = self.listen()

                    if medications_taken and any(med['name'].lower() in medications_taken.lower() for med in
                                                 self.user_profile["medications"]):
                        self.health_data.loc[self.health_data['date'] == today, 'medication_adherence'] = 0.75
                        self.speak("Thank you. I've recorded your medication information.")
                        self.save_user_data()
                    else:
                        self.speak(
                            "Let's try recording your medications again later when voice recognition is working better.")
                    return

            # Process the yes/no response
            if "yes" in response.lower() or "yeah" in response.lower() or "took them" in response.lower():
                self.health_data.loc[self.health_data['date'] == today, 'medication_adherence'] = 1.0
                self.speak(
                    "Great job! I've recorded that you took all your medications today. Is there anything else you'd like to tell me about your medications?")
            else:
                self.speak("Which medications did you miss today?")
                missed = self.listen()

                # Even if we don't understand exactly what was missed, record partial adherence
                self.health_data.loc[self.health_data['date'] == today, 'medication_adherence'] = 0.5
                self.speak(
                    "I've recorded your medication information. Is there anything I can do to help you remember to take all your medications?")

            self.save_user_data()

    def handle_emergency(self):
        """Handle potential emergency situations with improved sensitivity."""
        self.speak("You mentioned an emergency. Are you experiencing an urgent medical situation right now?")
        response = self.listen()

        # If voice recognition fails, assume potential emergency for safety
        if not response:
            self.speak(
                "I couldn't understand your response, but I take any mention of emergency seriously. Do you need me to call your emergency contact?")
            response = self.listen()

            # If still no clear response, err on the side of caution
            if not response or "yes" in response.lower():
                contact = self.user_profile["emergency_contact"]
                self.speak(f"I'll call {contact['name']} at {contact['phone']} for you right away.")
                # In a real implementation, integrate with phone calling API
                logger.warning(f"EMERGENCY: System would call {contact['name']} at {contact['phone']}")
                return

        # Process the response
        if "yes" in response.lower() or "help" in response.lower() or "please" in response.lower():
            contact = self.user_profile["emergency_contact"]
            self.speak(f"I'll call {contact['name']} at {contact['phone']} for you right away.")
            # In a real implementation, integrate with phone calling API
            logger.warning(f"EMERGENCY: System would call {contact['name']} at {contact['phone']}")
        else:
            self.speak(
                "I understand it's not an immediate emergency. Would you like to talk about what's concerning you?")

    def display_help(self):
        """Display available commands in a clear, organized way."""
        help_intro = "Here are some things you can ask me to do. I'll pause after each option so you can listen carefully."
        self.speak(help_intro)
        time.sleep(0.5)

        # Group commands by category for easier comprehension
        help_sections = [
            "For health tracking, you can say: record glucose, record sleep, or record medication.",
            "To check your information, you can say: how am I doing, or list medications.",
            "If you need to update information, you can say: update profile.",
            "To change how I speak, you can say: adjust voice.",
            "In an emergency, simply say: help me or emergency.",
            "To end our conversation, just say: goodbye or exit."
        ]

        # Speak each section with pauses between
        for section in help_sections:
            self.speak(section)
            time.sleep(1)  # Pause between sections

        # Confirm understanding
        self.speak("Would you like me to repeat any of these options?")

    def adjust_voice(self):
        """Allow user to adjust voice settings with improved guidance."""
        self.speak("I can change how I speak to you. Would you like me to speak faster, slower, louder, or quieter?")
        adjustment = self.listen()

        # If voice recognition fails, provide clearer options
        if not adjustment:
            self.speak("Please tell me one of these options: faster, slower, louder, or quieter.")
            adjustment = self.listen()

            # If it fails again, give up
            if not adjustment:
                self.speak("I'm having trouble understanding. My voice settings will stay the same for now.")
                return

        adjustment = adjustment.lower()

        if "faster" in adjustment:
            current_rate = self.tts_engine.getProperty('rate')
            new_rate = min(current_rate + 25, 220)  # Cap at 220 (still understandable)
            self.tts_engine.setProperty('rate', new_rate)
            self.user_profile["preferences"]["voice_speed"] = new_rate / 200
            self.speak("I'm speaking faster now. Is this speed better for you?")
            self.save_user_data()

        elif "slower" in adjustment:
            current_rate = self.tts_engine.getProperty('rate')
            new_rate = max(current_rate - 25, 100)  # Floor at 100 (still intelligible)
            self.tts_engine.setProperty('rate', new_rate)
            self.user_profile["preferences"]["voice_speed"] = new_rate / 200
            self.speak("I'm speaking more slowly now. Is this speed better for you?")
            self.save_user_data()

        elif "louder" in adjustment:
            current_vol = self.tts_engine.getProperty('volume')
            new_vol = min(current_vol + 0.1, 1.0)  # Cap at 1.0
            self.tts_engine.setProperty('volume', new_vol)
            self.user_profile["preferences"]["volume"] = new_vol
            self.speak("I'm speaking louder now. Can you hear me better?")
            self.save_user_data()

        elif "quieter" in adjustment:
            current_vol = self.tts_engine.getProperty('volume')
            new_vol = max(current_vol - 0.1, 0.5)  # Floor at 0.5 (still audible)
            self.tts_engine.setProperty('volume', new_vol)
            self.user_profile["preferences"]["volume"] = new_vol
            self.speak("I'm speaking more quietly now. Is this volume better for you?")
            self.save_user_data()

        # Follow up to confirm satisfaction
        response = self.listen()
        if response and ("no" in response.lower() or "not" in response.lower()):
            self.speak("Let's try a different adjustment. What would work better for you?")
            self.adjust_voice()  # Recursive call to try again
        elif response and ("yes" in response.lower() or "better" in response.lower()):
            self.speak("Great! I'll keep talking like this.")

    def update_profile(self):
        """Guide the user through updating profile information with improved interaction."""
        self.speak(
            "I can help you update your profile. What would you like to update: your name, age, medications, or emergency contact?")
        update_item = self.listen()

        # If voice recognition fails, provide more structure
        if not update_item:
            self.speak(
                "Please tell me what you want to update. You can say: name, age, medications, or emergency contact.")
            update_item = self.listen()

            # If it fails again, give up
            if not update_item:
                self.speak(
                    "I'm having trouble understanding. Let's try updating your profile later when voice recognition is working better.")
                return

        update_item = update_item.lower()

        if "name" in update_item:
            self.speak(f"Your current name is {self.user_profile['name']}. What would you like me to call you instead?")
            new_name = self.listen()

            # If voice recognition fails, try once more
            if not new_name:
                self.speak("I didn't catch your name. Please say your name clearly.")
                new_name = self.listen()

                # If it fails again, give up
                if not new_name:
                    self.speak("I'm having trouble understanding your name. Let's try again later.")
                    return

            # Clean and validate the name
            cleaned_name = re.sub(r'[^a-zA-Z\s\-\']', '', new_name).strip()
            if cleaned_name:
                self.user_profile['name'] = cleaned_name.title()  # Capitalize the name
                self.speak(f"Thank you. I'll call you {self.user_profile['name']} from now on. Is that correct?")
                confirmation = self.listen()

                if confirmation and "no" in confirmation.lower():
                    self.speak("Let's try again. What would you like me to call you?")
                    return self.update_profile()  # Restart the update process

                self.save_user_data()
            else:
                self.speak("I couldn't understand that name. Let's try again later.")

        elif "age" in update_item:
            self.speak(f"Your current age is {self.user_profile['age']}. What is your correct age?")
            age_response = self.listen()

            # If voice recognition fails, provide clearer instructions
            if not age_response:
                self.speak("Please say your age as a number, like sixty-five or seventy.")
                age_response = self.listen()

                # If it fails again, give up
                if not age_response:
                    self.speak("I'm having trouble understanding your age. Let's try again later.")
                    return

            try:
                # Extract numeric age from response
                age_match = re.search(r'\d+', age_response)
                if age_match:
                    new_age = int(age_match.group())
                    if 50 <= new_age <= 110:  # Reasonable age range for the application's target users
                        self.user_profile['age'] = new_age
                        self.speak(f"Thank you. I've updated your age to {new_age}. Is that correct?")
                        confirmation = self.listen()

                        if confirmation and "no" in confirmation.lower():
                            self.speak("Let's try again. What is your correct age?")
                            return self.update_profile()  # Restart the update process

                        self.save_user_data()
                    else:
                        self.speak(
                            f"The age {new_age} doesn't seem right for this application. Please try again with your correct age.")
                else:
                    self.speak("I couldn't detect a valid age in what you said.")
            except Exception as e:
                logger.error(f"Error updating age: {str(e)}")
                self.speak("Sorry, I couldn't understand that age.")

        elif "medication" in update_item:
            self.speak("Would you like to add a new medication or remove an existing one? Please say add or remove.")
            med_action = self.listen()

            # If voice recognition fails, provide clearer options
            if not med_action:
                self.speak("Please say either add or remove to tell me what you want to do with your medications.")
                med_action = self.listen()

                # If it fails again, give up
                if not med_action:
                    self.speak(
                        "I'm having trouble understanding. Let's try again later when voice recognition is working better.")
                    return

            med_action = med_action.lower()

            if "add" in med_action:
                # More structured approach to adding medication
                self.speak("Let's add your new medication. What is the name of the medication?")
                med_name = self.listen()

                if not med_name:
                    self.speak("I need the name of your medication. Let's try again later.")
                    return

                self.speak(f"I heard {med_name}. Is that correct? Please say yes or no.")
                confirmation = self.listen()

                if not confirmation or "no" in confirmation.lower():
                    self.speak("Let's try again. What is the name of your medication?")
                    med_name = self.listen()
                    if not med_name:
                        self.speak("I'm still having trouble understanding. Let's try again later.")
                        return

                # Get dosage with clear instructions
                self.speak(f"What is the dosage of {med_name}? For example, 10 milligrams or 500 milligrams.")
                med_dosage = self.listen()

                if not med_dosage:
                    # Default to unknown if we can't understand
                    med_dosage = "Unknown dosage"
                    self.speak("I couldn't understand the dosage. I'll mark it as unknown for now.")

                # Get frequency with clear options
                self.speak("How often do you take it? For example, once daily, twice daily, or as needed.")
                med_frequency = self.listen()

                if not med_frequency:
                    med_frequency = "daily"
                    self.speak("I'll set the frequency as daily.")

                # Get times with structured options
                self.speak("When do you take this medication? Morning, afternoon, evening, or bedtime?")
                med_times_spoken = self.listen()

                if not med_times_spoken:
                    med_times = ["08:00"]  # Default to morning
                    self.speak("I'll set the default time as morning, 8 AM.")
                else:
                    # Parse times from speech with improved logic
                    med_times = []
                    med_times_lower = med_times_spoken.lower()

                    if "morning" in med_times_lower:
                        med_times.append("08:00")
                    if "noon" in med_times_lower or "afternoon" in med_times_lower:
                        med_times.append("14:00")
                    if "evening" in med_times_lower or "dinner" in med_times_lower:
                        med_times.append("18:00")
                    if "night" in med_times_lower or "bedtime" in med_times_lower:
                        med_times.append("22:00")

                    # If no times were identified, default to morning
                    if not med_times:
                        med_times = ["08:00"]
                        self.speak("I couldn't understand the time. I'll set it for morning, 8 AM.")

                # Summarize and confirm
                times_of_day = []
                for time_str in med_times:
                    hour = int(time_str.split(":")[0])
                    if hour < 12:
                        times_of_day.append("morning")
                    elif hour < 17:
                        times_of_day.append("afternoon")
                    elif hour < 21:
                        times_of_day.append("evening")
                    else:
                        times_of_day.append("bedtime")

                times_summary = ", ".join(times_of_day)

                self.speak(
                    f"Let me confirm: You take {med_name}, {med_dosage}, {med_frequency}, in the {times_summary}. Is that correct?")
                final_confirmation = self.listen()

                if not final_confirmation or "yes" in final_confirmation.lower():
                    # Add the new medication
                    new_med = {
                        "name": med_name,
                        "dosage": med_dosage,
                        "frequency": med_frequency,
                        "times": med_times
                    }

                    self.user_profile["medications"].append(new_med)
                    self.speak(
                        f"I've added {med_name} to your medications. I'll remind you to take it {med_frequency}.")
                    self.save_user_data()
                else:
                    self.speak("Let's try again another time to make sure we get your medication details correct.")

            elif "remove" in med_action:
                if not self.user_profile["medications"]:
                    self.speak("You don't have any medications in your profile.")
                    return

                # List current medications more clearly
                self.speak("Here are your current medications:")
                for i, med in enumerate(self.user_profile["medications"]):
                    # Pause between each medication for clarity
                    self.speak(f"Number {i + 1}: {med['name']}, {med['dosage']}, {med['frequency']}")
                    time.sleep(0.5)

                self.speak("Which medication would you like to remove? Please say the number or name.")
                med_to_remove = self.listen()

                if not med_to_remove:
                    self.speak("I couldn't understand which medication to remove. Let's try again later.")
                    return

                # First try to match by number
                number_match = re.search(r'\d+', med_to_remove)
                if number_match:
                    med_index = int(number_match.group()) - 1
                    if 0 <= med_index < len(self.user_profile["medications"]):
                        removed_med = self.user_profile["medications"].pop(med_index)
                        self.speak(
                            f"I've removed {removed_med['name']} from your medications. Is there anything else you want to update?")
                        self.save_user_data()
                        return

                # If not by number, try by name with fuzzy matching
                closest_match = None
                highest_similarity = 0

                for i, med in enumerate(self.user_profile["medications"]):
                    # Simple matching - check if medication name appears in what user said
                    if med['name'].lower() in med_to_remove.lower():
                        removed_med = self.user_profile["medications"].pop(i)
                        self.speak(
                            f"I've removed {removed_med['name']} from your medications. Is there anything else you want to update?")
                        self.save_user_data()
                        return

                self.speak("I couldn't find that medication in your list. Let's try again later.")

        elif "emergency" in update_item or "contact" in update_item:
            self.speak("Let's update your emergency contact information. This is important for your safety.")

            # Get contact name with clear instructions
            self.speak("Please tell me the name of your emergency contact - this might be a family member or friend.")
            contact_name = self.listen()

            if not contact_name:
                self.speak("I need a name for your emergency contact. Let's try again later.")
                return

            # Confirm the name
            self.speak(f"I understood the name as {contact_name}. Is that correct? Please say yes or no.")
            confirmation = self.listen()

            if not confirmation or "no" in confirmation.lower():
                self.speak("Let's try again. Who is your emergency contact?")
                contact_name = self.listen()
                if not contact_name:
                    self.speak("I'm still having trouble understanding. Let's try again later.")
                    return

            # Get phone number with structured guidance
            self.speak(
                "Now, please say the phone number digit by digit. For example, say: three one zero, five five five, one two three four.")
            self.speak("Go ahead and say the phone number now.")
            contact_phone = self.listen()

            if not contact_phone:
                self.speak("I couldn't understand the phone number. Let's try again later.")
                return

            # Try to extract digits from the spoken phone number
            digits = re.findall(r'\d', contact_phone)
            if len(digits) >= 10:  # Assume at least 10 digits for a valid phone number
                # Format phone number as XXX-XXX-XXXX
                formatted_phone = f"{''.join(digits[:3])}-{''.join(digits[3:6])}-{''.join(digits[6:10])}"

                # Confirm the number by reading it back
                self.speak(
                    f"I understood the phone number as {', '.join(digits[:3])}, {', '.join(digits[3:6])}, {', '.join(digits[6:10])}. Is that correct?")
                confirmation = self.listen()

                if not confirmation or "yes" in confirmation.lower():
                    self.user_profile["emergency_contact"] = {
                        "name": contact_name,
                        "phone": formatted_phone
                    }

                    self.speak(
                        f"Thank you. I've updated your emergency contact to {contact_name} with phone number {formatted_phone}.")
                    self.save_user_data()
                else:
                    self.speak("Let's try setting up your emergency contact again later.")
            else:
                self.speak(
                    "I couldn't recognize a valid phone number. We need at least 10 digits. Let's try again later.")

        else:
            self.speak(
                "I'm sorry, I didn't understand what profile information you want to update. You can update your name, age, medications, or emergency contact.")

    def list_medications(self):
        """Read out the user's current medications with improved clarity and pacing."""
        if not self.user_profile["medications"]:
            self.speak("You don't have any medications in your profile yet. Would you like to add some?")
            return

        self.speak("Here are your current medications:")
        time.sleep(0.5)  # Brief pause for context switching

        for i, med in enumerate(self.user_profile["medications"]):
            # Convert time format to more natural speech
            times_of_day = []
            for time_str in med["times"]:
                hour = int(time_str.split(":")[0])
                if hour < 12:
                    times_of_day.append(f"{hour} AM")
                elif hour == 12:
                    times_of_day.append("noon")
                else:
                    times_of_day.append(f"{hour - 12} PM")

            times_spoken = ", ".join(times_of_day)

            # Speak each medication with pauses between for clarity
            self.speak(f"{med['name']}, {med['dosage']}, {med['frequency']}, at {times_spoken}")
            time.sleep(1)  # Pause between medications for better comprehension

        # Follow up to ensure all needs are met
        self.speak("Is there anything about your medications you'd like to know more about?")

    def _convert_24h_to_12h(self, time_str):
        """Convert 24-hour time format to 12-hour format for speech."""
        hour, minute = map(int, time_str.split(":"))
        period = "AM" if hour < 12 else "PM"
        hour = hour % 12
        hour = 12 if hour == 0 else hour
        return f"{hour}:{minute:02d} {period}"

    def run(self):
        """Main loop for the voice assistant with improved interaction flow."""
        # Start reminder thread
        self._schedule_reminders()
        reminder_thread = threading.Thread(target=self._reminder_thread, daemon=True)
        reminder_thread.start()

        # Welcome message with clear introduction
        print("\n" + "=" * 60)
        print(" ELDERCARE IMPROVED VOICE ASSISTANT - HEALTH MANAGEMENT SYSTEM ")
        print("=" * 60)

        greeting = f"Hello {self.user_profile['name']}. I'm your health assistant. I'm here to help you manage your health. How are you feeling today?"
        self.speak(greeting)

        consecutive_failures = 0
        max_failures = 3

        try:
            while True:
                # Check for scheduled reminders
                try:
                    reminder = self.response_queue.get_nowait()
                    self.speak(reminder)
                except queue.Empty:
                    pass

                # Listen for user input with improved error handling
                user_input = self.listen()

                if not user_input:
                    consecutive_failures += 1

                    if consecutive_failures >= max_failures:
                        self.speak(
                            "I'm having trouble understanding you. Let me ask a simple question. Are you still there?")
                        response = self.listen()

                        if not response:
                            self.speak(
                                "Since I can't hear you clearly, I'll pause our conversation. Say 'hello' or press Enter when you want to continue.")
                            input("Press Enter to continue...")  # Fallback to keyboard input
                            self.speak("Welcome back! Let's try again. How can I help you?")
                            consecutive_failures = 0
                        else:
                            consecutive_failures = 1  # Reset but not completely
                            self.speak("Let's try again. You can say 'help' if you need to know what I can do.")

                    print("Listening again...")
                    continue
                else:
                    consecutive_failures = 0  # Reset the failure counter on success

                # Update last interaction time
                self.context["last_interaction_time"] = datetime.datetime.now()

                # Identify command type
                command = self.identify_command(user_input)

                # Handle exit commands
                if command == "exit":
                    self.speak(f"Goodbye, {self.user_profile['name']}. I'll be here when you need me. Have a good day.")
                    self.save_user_data()
                    break

                # Handle specific commands with better response flow
                elif command == "help":
                    self.display_help()

                elif command == "emergency":
                    self.handle_emergency()

                elif command == "record glucose":
                    self.record_health_data("glucose")

                elif command == "record sleep":
                    self.record_health_data("sleep")

                elif command == "record medication":
                    self.record_health_data("medication")

                elif command == "update profile":
                    self.update_profile()

                elif command == "list medications":
                    self.list_medications()

                elif command == "adjust voice":
                    self.adjust_voice()

                elif command == "health data":
                    insights = self.analyze_health_data()
                    self.speak(insights)

                # Process general queries with Groq
                else:
                    response = self.process_with_groq(user_input)
                    self.speak(response)

                # Brief pause between interactions for more natural conversation flow
                time.sleep(0.5)

        except KeyboardInterrupt:
            self.speak("I understand you want to end our conversation. Take care of yourself. Goodbye.")
            self.save_user_data()
            logger.info("Assistant shut down by user")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            self.speak("I encountered an unexpected error and need to shut down. Your data has been saved.")
            self.save_user_data()


if __name__ == "__main__":
    assistant = ElderCareVoiceAssistant()
    assistant.run()