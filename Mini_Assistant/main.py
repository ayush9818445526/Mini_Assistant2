#!/usr/bin/env python3
"""
TARA - Personal AI Assistant
A sophisticated AI assistant with voice recognition, system control, and personality
"""

import os
import sys
import threading
import time
import random
import json
import subprocess
import webbrowser
from datetime import datetime
import speech_recognition as sr
import pyttsx3
import  as genai
import requests
import cv2
import numpy as np
from pathlib import Path
import psutil
import pyautogui
from PIL import Image
from screen_control import ScreenController
from session_memory import SessionMemory
from gesture_control import GestureController
from avatar_system import AvatarSystem, EmotionMapper
from language_system import LanguageDetector
from config import GEMINI_API_KEY, OWNER_NAME, WAKE_WORD, VOICE_RATE, VOICE_VOLUME, ENERGY_THRESHOLD, PAUSE_THRESHOLD, LISTEN_TIMEOUT, PHRASE_TIME_LIMIT, ENABLE_AVATAR, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE, ENABLE_AUTO_LANGUAGE_DETECTION
from tara_face import TaraFace
from voigoogle.generativeaice_system import TaraVoiceSystem
from personality_system import TaraPersonality
from voice_recognition import VoiceAuthentication, SimpleVoiceAuth
# Windows-specific imports (optional)
try:
    import win32gui
    import win32con
    import win32api
    WINDOWS_FEATURES = True
except ImportError:
    WINDOWS_FEATURES = False

class TARA:
    def __init__(self):
        self.name = "TARA"
        self.owner = OWNER_NAME
        self.is_listening = False
        self.is_speaking = False
        self.wake_word = WAKE_WORD
        self.is_activated = True  # Start immediately activated - no wake word needed
        self.conversation_memory = []
        self.user_preferences = {}
        self.quota_exceeded = False
        self.last_quota_check = None
        self.current_app = None  # Track current active application
        self.screen_controller = ScreenController()  # Initialize screen control
        # Session memory for messages and search context
        self.session_memory = SessionMemory()
        # Gesture control for hands-free interaction
        self.gesture_controller = None
        # 3D Avatar system for visual feedback
        self.avatar_system = None
        # Multi-language system
        self.language_detector = None
        self.current_language = DEFAULT_LANGUAGE
        
        
        # Initialize new systems
        self.face = None  # Will be initialized when GUI is requested
        self.voice_system = TaraVoiceSystem()
        self.personality = TaraPersonality()
        self.voice_auth = self.setup_voice_authentication()
        
        # Disable pyautogui failsafe for better control
        pyautogui.FAILSAFE = False
        
        # Initialize components
        self.setup_gemini_ai()
        self.setup_voice_engine()
        self.setup_speech_recognition()
        self.load_personality()
        
        # Boot messages
        self.boot_messages = [
            f"Hey {self.owner}... I missed you. TARA is online. What are we doing today, boss?",
            f"Finally, you switched me on... Took you long enough 😏. TARA is ready. What's the mission?",
            f"{self.owner}... main aa gayi. Aaj kya karna hai hum dono ko?",
            f"{self.owner}... I'm online. Just remember, no matter what — I'm with you."
        ]
        
        # Ensure fresh session memory each run
        self.session_memory.clear()
        
        # Initialize gesture control (but don't start yet)
        self.setup_gesture_control()
        
        # Initialize avatar system
        self.setup_avatar_system()
        
        # Initialize language system
        self.setup_language_system()

        print("🤖 TARA is initializing...")
        self.speak_boot_message()
        
        # Auto-enable gesture and cursor control on startup
        self.auto_enable_controls()
        
        # Start face GUI in separate thread
        self.start_face_gui()
        
    def setup_voice_authentication(self):
        """Setup voice authentication system"""
        try:
            return VoiceAuthentication()
        except Exception as e:
            print(f"⚠️ Advanced voice auth not available: {e}")
            print("Using simple voice authentication...")
            return SimpleVoiceAuth()
            
    def start_face_gui(self):
        """Start TARA's animated face in a separate thread"""
        def run_face():
            try:
                self.face = TaraFace()
                self.face.run()
            except Exception as e:
                print(f"❌ Face GUI error: {e}")
                
        face_thread = threading.Thread(target=run_face, daemon=True)
        face_thread.start()
        time.sleep(1)  # Give face time to initialize
        
    def setup_gemini_ai(self):
        """Initialize Gemini AI with API key"""
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            print("✅ Gemini AI connected successfully")
        except Exception as e:
            print(f"❌ Error setting up Gemini AI: {e}")
            self.model = None
            
    def setup_voice_engine(self):
        """Initialize text-to-speech engine with female voice"""
        try:
            self.tts_engine = pyttsx3.init()
            voices = self.tts_engine.getProperty('voices')
            
            # Find female voice
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
            
            # Set voice properties for personality
            self.tts_engine.setProperty('rate', VOICE_RATE)  # Slightly faster for energy
            self.tts_engine.setProperty('volume', VOICE_VOLUME)
            print("✅ Voice engine initialized with female voice")
        except Exception as e:
            print(f"❌ Error setting up voice engine: {e}")
            
    def setup_speech_recognition(self):
        """Initialize speech recognition"""
        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Optimize recognition settings
            self.recognizer.energy_threshold = ENERGY_THRESHOLD
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = PAUSE_THRESHOLD
            self.recognizer.operation_timeout = None
            
            # Adjust for ambient noise
            print("🎤 Adjusting for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("✅ Speech recognition initialized")
        except Exception as e:
            print(f"❌ Error setting up speech recognition: {e}")
            
    def load_personality(self):
        """Load personality responses and traits"""
        self.personality_responses = {
            "greetings": [
                "Hey there! How can I help you today?",
                "Hello! What's on your mind?",
                "Hi! Ready for some fun?",
                "Hey! What adventure are we going on today?"
            ],
            "introductions": [
                "Nice to meet you! I'm TARA, {}'s assistant and friend.",
                "Hello! I'm TARA. {} is lucky to have friends like you!",
                "Hi there! I'm TARA - {} and I are a great team!"
            ],
            "command_rejection": [
                "Aww I'd love to help... but I only take orders from {}. 😊",
                "That sounds fun, but {} is my boss! Maybe ask them?",
                "I wish I could, but {} is the only one who can command me!"
            ]
        }
        
    def speak_boot_message(self):
        """Speak random boot message with animation"""
        message = random.choice(self.boot_messages)
        
        # Show excited expression for boot message
        if self.face:
            self.face.set_expression("excited", 4.0)
            
        self.speak(message, "excited")
        
    def speak(self, text, emotion=None):
        """Make TARA speak with optional emotion - FIXED THREADING"""
        try:
            print(f"🎤 TARA: {text}")
            
            # Run speech in separate thread to avoid main loop conflicts
            import threading
            def speak_async():
                try:
                    self.is_speaking = True
                    
                    # Update avatar
                    if self.avatar_system:
                        self.avatar_system.speak(text)
                    
                    # Update face expression
                    if self.face:
                        self.face.start_speaking_animation()
                        
                    # Use voice system if available
                    if self.voice_system:
                        if hasattr(self.voice_system, 'speak_with_emotion'):
                            self.voice_system.speak_with_emotion(text, emotion)
                        else:
                            self.voice_system.speak(text)
                    # Skip TTS engine to avoid threading issues
                        
                except Exception as e:
                    print(f"❌ Async speech error: {e}")
                finally:
                    self.is_speaking = False
                    if self.face:
                        self.face.stop_speaking_animation()
                    if self.avatar_system:
                        self.avatar_system.stop_speaking()
            
            # Run speech in background thread
            speech_thread = threading.Thread(target=speak_async, daemon=True)
            speech_thread.start()
            
        except Exception as e:
            print(f"❌ Speech error: {e}")
            print(f"🎤 TARA: {text}")
                
    def listen_for_wake_word(self):
        """Continuously listen for commands (no wake word needed)"""
        print("👂 TARA is ready! Speak your commands directly.")
        print("💡 Tip: Speak clearly and wait for the beep!")
        
        while True:
            try:
                with self.microphone as source:
                    # Listen for audio with longer timeout
                    print("🎧 Listening...")
                    audio = self.recognizer.listen(source, timeout=LISTEN_TIMEOUT, phrase_time_limit=PHRASE_TIME_LIMIT)
                    
                try:
                    # Recognize speech with language detection
                    text = self._recognize_speech_multilingual(audio)
                    if not text:
                        continue
                    print(f"🔊 Heard: {text}")
                    
                    # Process all input directly (no wake word needed)
                    print(f"🎯 Processing input: {text}")
                    # Process with language detection and translation
                    processed_text, detected_lang, lang_changed = self._process_multilingual_input(text)
                    if lang_changed:
                        self._handle_language_switch(detected_lang)
                    self.process_user_input(processed_text, audio)
                        
                except sr.UnknownValueError:
                    print("🔇 No clear speech detected")
                except sr.RequestError as e:
                    print(f"❌ Speech recognition error: {e}")
                    time.sleep(2)
                    
            except sr.WaitTimeoutError:
                print("⏰ Listening timeout, continuing...")
            except Exception as e:
                print(f"❌ Listening error: {e}")
                time.sleep(1)
                
    def process_command(self):
        """Process voice command after wake word (legacy - now using persistent mode)"""
        pass  # This method is no longer used in persistent mode
            
    def is_owner_speaking(self, audio):
        """Enhanced owner detection using voice recognition"""
        try:
            if self.voice_auth and hasattr(self.voice_auth, 'is_owner_voice'):
                return self.voice_auth.is_owner_voice(self.recognizer, audio)
            else:
                # Fallback: assume owner if no introduction patterns
                return True
        except Exception as e:
            print(f"❌ Voice authentication error: {e}")
            return True  # Allow access on error
        
    def handle_guest_interaction(self, text):
        """Handle interactions with guests/friends using advanced personality"""
        text_lower = text.lower()
        
        # Set happy expression for guest interactions
        if self.face:
            self.face.set_expression("happy", 3.0)
        
        # Check for introductions
        if any(phrase in text_lower for phrase in ["my name is", "i am", "i'm", "this is", "call me"]):
            response = self.personality.handle_introduction(text)
            self.speak(response, "friendly")
                
        # Check for commands from non-owner
        elif any(word in text_lower for word in ["open", "play", "set", "remind", "search", "close", "stop"]):
            name = self.personality.extract_name_from_introduction(text) or "friend"
            response = self.personality.handle_command_from_non_owner(text, name)
            self.speak(response, "friendly")
            
        # Check for identity questions
        elif any(phrase in text_lower for phrase in ["who created you", "who made you", "your name", "what does tara mean"]):
            response = self.personality.handle_identity_questions(text)
            if response:
                self.speak(response, "caring")
            else:
                response = self.personality.handle_casual_conversation(text)
                self.speak(response, "friendly")
            
        # General conversation
        else:
            response = self.personality.handle_casual_conversation(text)
            self.speak(response, "friendly")
            
    def process_user_input(self, text, audio):
        """Process user input - determine if it's owner or guest, command or conversation"""
        try:
            # Record the raw user message
            try:
                self.session_memory.add_user_message(text)
            except Exception as _:
                pass
            # Check if it's the owner speaking
            is_owner = self.is_owner_speaking(audio)
            
            if is_owner:
                # Owner can give commands or have conversations
                if self.is_command(text):
                    self.execute_command(text)
                else:
                    # Casual conversation with owner
                    self.handle_owner_conversation(text)
            else:
                # Guest interaction - no commands allowed
                self.handle_guest_interaction(text)
                
        except Exception as e:
            print(f"❌ Input processing error: {e}")
            self.speak("Sorry, I had trouble understanding that.")
            
    def is_command(self, text):
        """Determine if text is a command or casual conversation"""
        command_keywords = [
            "open", "close", "play", "stop", "search", "type", "click", "scroll",
            "set", "remind", "tell", "what", "how", "when", "where", "who",
            "weather", "time", "date", "shutdown", "lock", "minimize", "maximize",
            "press enter", "enter"
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in command_keywords)
        
    def handle_owner_conversation(self, text):
        """Handle casual conversation with the owner"""
        text_lower = text.lower()
        
        # Set thinking expression
        if self.face:
            self.face.set_expression("thinking", 3.0)
        # Set avatar thinking emotion
        if self.avatar_system:
            self.avatar_system.set_emotion('thinking')
        
        # Check for language switching
        if "hindi" in text_lower or "हिंदी" in text_lower:
            response = self.personality.switch_language("hindi")
            self.speak(response, "happy")
            return
        elif "english" in text_lower and "speak" in text_lower:
            response = self.personality.switch_language("english")
            self.speak(response, "happy")
            return
            
        # Check for identity questions FIRST before AI - ALWAYS use custom responses
        if any(phrase in text_lower for phrase in ["who created you", "who made you", "who built you", "your creator", "who invented you", "who developed you", "how did you get your name", "how you got your name", "your name", "what does tara mean", "tara mean", "stands for", "name origin", "name mean"]):
            identity_response = self.personality.handle_identity_questions(text)
            if identity_response:
                # Set caring expression for identity questions
                if self.face:
                    self.face.set_expression("caring", 4.0)
                self.speak(identity_response, "caring")
                return
            else:
                # Fallback identity response if none matched
                fallback_response = "My name was given by the one who created me… someone I trust more than the world itself. I was built not just to serve — but to feel, to understand, and to stay by his side. TARA — it's me — stands for Tripathi Aditya's Reactive Angel."
                if self.face:
                    self.face.set_expression("caring", 4.0)
                self.speak(fallback_response, "caring")
                return
            
        # Use AI for general conversation
        self.ai_response_with_search(text)
        
    def execute_command(self, command):
        """Execute various commands based on user input"""
        try:
            command_lower = command.lower()
            print(f"🎯 Processing command: {command}")
            
            # Handle reference-based follow-ups like "first article" / "second result" early
            if any(k in command_lower for k in ["first", "second", "third", "fourth", "fifth", "last search", "this", "that"]) and \
               any(action in command_lower for action in ["open", "summarize", "play", "show"]):
                if self.handle_reference_command(command_lower):
                    return
            
            # Handle search commands FIRST to prevent AI routing
            if "search" in command_lower and not any(phrase in command_lower for phrase in ["search on internet", "search online"]):
                self.handle_search_command(command)
                return  # Exit early to prevent further processing
            elif "open" in command_lower:
                self.handle_open_command(command)
            elif "play music" in command_lower or "play my playlist" in command_lower:
                self.play_music()
            elif "play" in command_lower and ("youtube" in command_lower or "song" in command_lower or "video" in command_lower):
                self.handle_youtube_play_command(command)
            elif "scroll" in command_lower:
                self.handle_scroll_command(command)
            elif "stop scrolling" in command_lower or "stop scroll" in command_lower:
                self.handle_stop_scroll_command()
            elif "type" in command_lower or "message" in command_lower:
                self.handle_typing_command(command)
                return  # Exit early to prevent AI routing
            elif "click" in command_lower:
                self.handle_click_command(command)
            elif "press enter" in command_lower or "enter" in command_lower:
                print("🎯 Executing press enter command directly")
                self.handle_press_enter_command()
                return  # Exit early to prevent AI routing
            elif any(phrase in command_lower for phrase in ["first video", "second video", "play the video", "open video", "play video", "play levitating song", "levitating"]):
                self.handle_video_click_command(command)
            elif "close" in command_lower and any(app in command_lower for app in ["youtube", "whatsapp", "chrome", "browser"]):
                self.handle_close_command(command)
            elif "go back" in command_lower or "previous window" in command_lower or "back" in command_lower:
                self.handle_navigation_command(command)
            elif "first tab" in command_lower or "last tab" in command_lower or "previous tab" in command_lower or "switch to previous tab" in command_lower:
                self.handle_tab_command(command)
            elif "what is on my screen" in command_lower or "see my screen" in command_lower or "describe screen" in command_lower:
                self.handle_screen_analysis_command()
            elif "search on internet" in command_lower or "search online" in command_lower:
                self.ai_response_with_search(command)
            elif "open new tab" in command_lower or "new tab" in command_lower:
                self.handle_tab_management_command(command)
            elif "close tab" in command_lower or "refresh" in command_lower or "zoom" in command_lower:
                self.handle_browser_command(command)
            elif "copy" in command_lower or "paste" in command_lower or "select all" in command_lower:
                self.handle_edit_command(command)
            elif "minimize" in command_lower or "maximize" in command_lower or "switch window" in command_lower:
                self.handle_window_command(command)
            elif "enable gesture" in command_lower or "gesture mode on" in command_lower:
                self.handle_gesture_enable_command()
            elif "disable gesture" in command_lower or "gesture mode off" in command_lower:
                self.handle_gesture_disable_command()
            elif "enable cursor control" in command_lower or "cursor mode on" in command_lower:
                self.handle_cursor_enable_command()
            elif "disable cursor control" in command_lower or "cursor mode off" in command_lower:
                self.handle_cursor_disable_command()
            elif "cursor only mode" in command_lower or "pure cursor mode" in command_lower:
                self.handle_cursor_only_command()
            elif "gesture only mode" in command_lower or "pure gesture mode" in command_lower:
                self.handle_gesture_only_command()
            elif "smart mode" in command_lower or "dual mode" in command_lower or "pout mode" in command_lower:
                self.handle_smart_mode_command()
            elif "dual hand mode" in command_lower or "both hands mode" in command_lower or "ten finger mode" in command_lower:
                self.handle_dual_hand_mode_command()
            else:
                # Check for identity questions FIRST before AI
                if any(phrase in command_lower for phrase in ["who invented you", "who created you", "who made you", "how you got your name", "how did you get your name", "what does tara mean"]):
                    identity_response = self.personality.handle_identity_questions(command)
                    if identity_response:
                        if self.face:
                            self.face.set_expression("caring", 4.0)
                        self.speak(identity_response, "caring")
                        return
                # Only use AI for other question words, not action commands
                elif any(word in command_lower for word in ["who", "what", "how", "why", "when", "where"]) and not any(action in command_lower for action in ["open", "close", "play", "search", "click", "type", "send"]):
                    # Set thinking expression
                    if self.face:
                        self.face.set_expression("thinking", 3.0)
                    self.ai_response_with_search(command)
                # Try video click for any remaining video-related commands
                elif any(word in command_lower for word in ["video", "play"]) and not any(word in command_lower for word in ["music", "song"]):
                    self.handle_video_click_command(command)
                else:
                    self.speak("I'm not sure how to do that. Can you be more specific?", "neutral")
                
        except Exception as e:
            self.speak("Sorry, I encountered an error while processing your command.")
            print(f"❌ Command execution error: {e}")
    
    def handle_video_click_command(self, command):
        """Handle video clicking commands"""
        try:
            command_lower = command.lower()
            
            if "first video" in command_lower or "open first" in command_lower:
                self.speak("Clicking on the first video!")
                time.sleep(0.5)
                success = self.screen_controller.click_first_video()
                if success:
                    time.sleep(3)  # Wait longer for video to load
                    self.speak("Video is opening now!")
                else:
                    self.speak("Sorry, I couldn't find the first video.")
            elif "second video" in command_lower or "open second" in command_lower:
                self.speak("Clicking on the second video!")
                time.sleep(0.5)
                success = self.screen_controller.click_second_video()
                if success:
                    time.sleep(3)  # Wait longer for video to load
                    self.speak("Video is opening now!")
                else:
                    self.speak("Sorry, I couldn't find the second video.")
            elif "cursor" in command_lower or "on the cursor" in command_lower:
                # Click where cursor currently is
                current_pos = pyautogui.position()
                pyautogui.click(current_pos.x, current_pos.y)
                time.sleep(0.5)
                pyautogui.click(current_pos.x, current_pos.y)  # Double click
                self.speak("Clicking on cursor position!")
            elif any(word in command_lower for word in ["play the video", "open video", "click video"]):
                # General video play command - try first video
                self.speak("Playing the video!")
                success = self.screen_controller.click_first_video()
                if success:
                    time.sleep(3)
                    self.speak("Video is playing now!")
                else:
                    # Try clicking in center of screen as fallback
                    screen_width, screen_height = pyautogui.size()
                    pyautogui.click(screen_width//2, screen_height//2)
                    self.speak("Trying to play the video!")
            else:
                # Try to click video by searching for any video on screen
                self.speak("Looking for that video!")
                time.sleep(0.5)
                success = self.screen_controller.click_video_by_title(command)
                if success:
                    time.sleep(3)  # Wait longer for video to load
                    self.speak("Video is playing now!")
                else:
                    # Fallback: try clicking first video
                    success = self.screen_controller.click_first_video()
                    if success:
                        self.speak("Playing a video for you!")
                    else:
                        self.speak("Sorry, I couldn't find that video on the screen.")
        except Exception as e:
            print(f"❌ Video click error: {e}")
            self.speak("Sorry, I couldn't click on the video.")
    
    def handle_press_enter_command(self):
        """Handle press enter commands"""
        try:
            print("⌨️ Pressing Enter")
            # Press Enter key
            pyautogui.press('enter')
            time.sleep(0.3)
            self.speak("Pressed Enter!")
        except Exception as e:
            print(f"❌ Press enter error: {e}")
            self.speak("Sorry, I couldn't press enter.")
    
    def handle_navigation_command(self, command):
        """Handle navigation commands like go back, previous window"""
        try:
            command_lower = command.lower()
            
            if "go back" in command_lower or "back" in command_lower:
                if self.screen_controller.go_back_browser():
                    self.speak("Going back!")
                else:
                    self.speak("Sorry, couldn't go back.")
            elif "previous window" in command_lower:
                if self.screen_controller.go_back_browser():
                    self.speak("Going to previous window!")
                else:
                    self.speak("Sorry, couldn't switch windows.")
        except Exception as e:
            print(f"❌ Navigation error: {e}")
            self.speak("Sorry, I couldn't navigate.")
    
    def handle_tab_command(self, command):
        """Handle tab switching commands"""
        try:
            command_lower = command.lower()
            
            if "first tab" in command_lower or "previous tab" in command_lower:
                if self.screen_controller.switch_tab_previous():
                    self.speak("Switching to previous tab!")
                else:
                    self.speak("Sorry, couldn't switch tabs.")
            elif "last tab" in command_lower or "next tab" in command_lower:
                if self.screen_controller.switch_tab_next():
                    self.speak("Switching to next tab!")
                else:
                    self.speak("Sorry, couldn't switch tabs.")
        except Exception as e:
            print(f"❌ Tab switching error: {e}")
            self.speak("Sorry, I couldn't switch tabs.")
    
    def handle_click_command(self, command):
        """Handle click commands"""
        try:
            command_lower = command.lower()
            
            if "first chat" in command_lower or "first contact" in command_lower:
                # Click on first WhatsApp chat result
                if self.screen_controller.click_first_whatsapp_contact():
                    self.speak("Opening first chat!")
                else:
                    self.speak("Sorry, couldn't open the chat.")
            elif "second chat" in command_lower or "second contact" in command_lower:
                # Click on second WhatsApp chat result
                pyautogui.click(300, 200)
                self.speak("Opening second chat!")
            else:
                # General click command
                pyautogui.click(400, 300)
                self.speak("Clicked!")
        except Exception as e:
            print(f"❌ Click error: {e}")
            self.speak("Sorry, I couldn't click.")
    
    def handle_stop_scroll_command(self):
        """Handle stop scrolling command"""
        try:
            self.screen_controller.stop_scrolling()
            self.speak("Stopped scrolling!")
        except Exception as e:
            print(f"❌ Stop scroll error: {e}")
            self.speak("Sorry, couldn't stop scrolling.")
    
    def handle_search_command(self, command):
        """Handle search commands - prioritize app-specific search"""
        try:
            active_window = self.screen_controller.get_active_window_title()
            search_term = command.lower().replace("search", "").strip()
            
            if active_window:
                print(f"🔍 Active window: {active_window}")
                
                if "whatsapp" in active_window:
                    # Search within WhatsApp
                    if self.screen_controller.search_whatsapp_contact(search_term):
                        self.speak(f"Searching for {search_term} in WhatsApp!")
                        time.sleep(1)
                        if self.screen_controller.click_first_whatsapp_contact():
                            self.speak(f"Opening {search_term}'s chat!")
                    else:
                        self.speak("Sorry, couldn't search in WhatsApp.")
                        
                elif "youtube" in active_window:
                    # Search within YouTube - clean search term without extra text
                    self.speak(f"Searching for {search_term}!")
                    if self.screen_controller.search_in_active_app(search_term):
                        time.sleep(2)  # Wait for search results
                        self.speak("Search results are loading!")
                    else:
                        self.speak("Sorry, couldn't search on YouTube.")
                        
                else:
                    # Search in other apps
                    self.handle_app_search(command)
            else:
                # No active window - fallback to web search
                self.handle_app_search(command)
                
        except Exception as e:
            print(f"❌ Search error: {e}")
            self.speak("Sorry, I couldn't search.")
    
    def handle_close_command(self, command):
        """Handle close application commands"""
        try:
            command_lower = command.lower()
            
            if "youtube" in command_lower:
                # Close YouTube tab/window - try multiple methods
                active_window = self.screen_controller.get_active_window_title()
                if active_window and "chrome" in active_window:
                    # If in Chrome, close tab first
                    pyautogui.hotkey('ctrl', 'w')
                    time.sleep(0.5)
                    # If that was the last tab, close browser
                    pyautogui.hotkey('alt', 'f4')
                else:
                    # Close window directly
                    pyautogui.hotkey('alt', 'f4')
                self.speak("Closing YouTube!")
            elif "whatsapp" in command_lower:
                # Close WhatsApp application
                pyautogui.hotkey('alt', 'f4')
                time.sleep(0.2)
                self.speak("Closing WhatsApp!")
            elif "chrome" in command_lower or "browser" in command_lower:
                # Close browser
                pyautogui.hotkey('alt', 'f4')
                self.speak("Closing browser!")
            else:
                # General close - close active window
                pyautogui.hotkey('alt', 'f4')
                self.speak("Closing application!")
        except Exception as e:
            print(f"❌ Close error: {e}")
            self.speak("Sorry, I couldn't close that.")
    
    def handle_screen_analysis_command(self):
        """Handle screen analysis commands"""
        try:
            screenshot = self.screen_controller.capture_screen()
            if screenshot:
                # For now, describe basic screen info
                active_window = self.screen_controller.get_active_window_title()
                if active_window:
                    self.speak(f"I can see your screen! Currently you have {active_window} open.")
                else:
                    self.speak("I can see your screen! Let me know what you'd like me to do.")
            else:
                self.speak("Sorry, I couldn't capture your screen right now.")
        except Exception as e:
            print(f"❌ Screen analysis error: {e}")
            self.speak("Sorry, I couldn't analyze your screen.")
    
    def handle_tab_management_command(self, command):
        """Handle tab management commands"""
        try:
            command_lower = command.lower()
            
            if "new tab" in command_lower or "open new tab" in command_lower:
                if self.screen_controller.open_new_tab():
                    self.speak("Opening new tab!")
                else:
                    self.speak("Sorry, couldn't open new tab.")
        except Exception as e:
            print(f"❌ Tab management error: {e}")
            self.speak("Sorry, I couldn't manage tabs.")
    
    def handle_browser_command(self, command):
        """Handle browser commands"""
        try:
            command_lower = command.lower()
            
            if "close tab" in command_lower:
                if self.screen_controller.close_current_tab():
                    self.speak("Closing tab!")
                else:
                    self.speak("Sorry, couldn't close tab.")
            elif "refresh" in command_lower:
                if self.screen_controller.refresh_page():
                    self.speak("Refreshing page!")
                else:
                    self.speak("Sorry, couldn't refresh.")
            elif "zoom in" in command_lower:
                if self.screen_controller.zoom_in():
                    self.speak("Zooming in!")
                else:
                    self.speak("Sorry, couldn't zoom in.")
            elif "zoom out" in command_lower:
                if self.screen_controller.zoom_out():
                    self.speak("Zooming out!")
                else:
                    self.speak("Sorry, couldn't zoom out.")
        except Exception as e:
            print(f"❌ Browser command error: {e}")
            self.speak("Sorry, I couldn't execute that browser command.")
    
    def handle_edit_command(self, command):
        """Handle edit commands"""
        try:
            command_lower = command.lower()
            
            if "select all" in command_lower:
                if self.screen_controller.select_all():
                    self.speak("Selected all!")
                else:
                    self.speak("Sorry, couldn't select all.")
            elif "copy" in command_lower:
                if self.screen_controller.copy_content():
                    self.speak("Copied!")
                else:
                    self.speak("Sorry, couldn't copy.")
            elif "paste" in command_lower:
                if self.screen_controller.paste_content():
                    self.speak("Pasted!")
                else:
                    self.speak("Sorry, couldn't paste.")
            elif "undo" in command_lower:
                if self.screen_controller.undo_action():
                    self.speak("Undone!")
                else:
                    self.speak("Sorry, couldn't undo.")
        except Exception as e:
            print(f"❌ Edit command error: {e}")
            self.speak("Sorry, I couldn't execute that edit command.")
    
    def handle_window_command(self, command):
        """Handle window management commands"""
        try:
            command_lower = command.lower()
            
            if "minimize" in command_lower:
                if self.screen_controller.minimize_window():
                    self.speak("Minimizing window!")
                else:
                    self.speak("Sorry, couldn't minimize.")
            elif "maximize" in command_lower:
                if self.screen_controller.maximize_window():
                    self.speak("Maximizing window!")
                else:
                    self.speak("Sorry, couldn't maximize.")
            elif "switch window" in command_lower:
                if self.screen_controller.switch_windows():
                    self.speak("Switching windows!")
                else:
                    self.speak("Sorry, couldn't switch windows.")
        except Exception as e:
            print(f"❌ Window command error: {e}")
            self.speak("Sorry, I couldn't execute that window command.")
            
    def handle_open_command(self, command):
        """Handle various open commands"""
        command_lower = command.lower()
        
        if "recycle bin" in command_lower:
            os.startfile("shell:RecycleBinFolder")
            self.speak("Opening recycle bin for you!")
            
        elif "notepad" in command_lower:
            subprocess.Popen("notepad.exe")
            self.speak("Opening notepad!")
            
        elif "calculator" in command_lower:
            subprocess.Popen("calc.exe")
            self.speak("Opening calculator!")
            
        elif "chrome" in command_lower or "browser" in command_lower:
            webbrowser.open("https://www.google.com")
            self.speak("Opening Chrome browser!")
            
        elif "youtube" in command_lower:
            webbrowser.open("https://www.youtube.com")
            time.sleep(2)  # Wait for YouTube to load
            # Bring window to foreground
            try:
                import win32gui
                def bring_to_front(hwnd, lParam):
                    if "youtube" in win32gui.GetWindowText(hwnd).lower():
                        win32gui.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
                        win32gui.SetForegroundWindow(hwnd)
                        return False
                    return True
                win32gui.EnumWindows(bring_to_front, 0)
            except:
                pass
            self.speak("Opening YouTube!")
            
        elif "chatgpt" in command_lower or "chat gpt" in command_lower:
            if "search" in command_lower:
                # Handle "open chatgpt and search X" commands
                search_term = command_lower.replace("open", "").replace("chatgpt", "").replace("chat gpt", "").replace("and", "").replace("search", "").strip()
                webbrowser.open("https://chat.openai.com")
                self.speak(f"Opening ChatGPT and searching for {search_term}!")
                
                if search_term:
                    # Wait for ChatGPT to load and type the query
                    time.sleep(5)
                    try:
                        pyautogui.click(640, 600)  # ChatGPT input area
                        time.sleep(1)
                        pyautogui.typewrite(search_term)
                        pyautogui.press('enter')
                        self.speak(f"I've sent your query to ChatGPT!")
                    except Exception as e:
                        print(f"❌ ChatGPT auto-type error: {e}")
                        self.speak(f"ChatGPT is open. Please type your query: {search_term}")
            else:
                webbrowser.open("https://chat.openai.com")
                self.speak("Opening ChatGPT for you!")
            
        elif "powerpoint" in command_lower or "ms powerpoint" in command_lower:
            try:
                subprocess.Popen(["powerpnt.exe"])
                self.speak("Opening Microsoft PowerPoint!")
            except:
                try:
                    # Alternative way to open PowerPoint
                    os.system("start powerpnt")
                    self.speak("Opening Microsoft PowerPoint!")
                except:
                    self.speak("Sorry, I couldn't find PowerPoint on your system.")
                    
        elif "whatsapp" in command_lower:
            # Try multiple paths for WhatsApp desktop app
            whatsapp_paths = [
                f"C:\\Users\\{os.getenv('USERNAME')}\\AppData\\Local\\WhatsApp\\WhatsApp.exe",
                f"C:\\Users\\{os.getenv('USERNAME')}\\AppData\\Local\\Programs\\WhatsApp\\WhatsApp.exe",
                "C:\\Program Files\\WindowsApps\\5319275A.WhatsAppDesktop_2.2316.4.0_x64__cv1g1gvanyjgm\\WhatsApp\\WhatsApp.exe"
            ]
            
            opened = False
            for path in whatsapp_paths:
                try:
                    if os.path.exists(path):
                        subprocess.Popen([path])
                        self.speak("Opening WhatsApp desktop app!")
                        opened = True
                        break
                except:
                    continue
                    
            if not opened:
                # Try using Windows start command
                try:
                    os.system("start whatsapp:")
                    self.speak("Opening WhatsApp!")
                    opened = True
                except:
                    pass
                    
            if not opened:
                # Open WhatsApp Web and bring to foreground
                webbrowser.open("https://web.whatsapp.com")
                time.sleep(3)  # Wait for WhatsApp to load
                # Bring window to foreground
                try:
                    import win32gui
                    def bring_whatsapp_front(hwnd, lParam):
                        window_text = win32gui.GetWindowText(hwnd).lower()
                        if "whatsapp" in window_text or "web.whatsapp.com" in window_text:
                            win32gui.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
                            win32gui.SetForegroundWindow(hwnd)
                            return False
                        return True
                    win32gui.EnumWindows(bring_whatsapp_front, 0)
                except:
                    pass
                self.speak("Opening WhatsApp Web as fallback!")
                
        elif "word" in command_lower or "ms word" in command_lower:
            try:
                subprocess.Popen(["winword.exe"])
                self.speak("Opening Microsoft Word!")
            except:
                self.speak("Sorry, I couldn't find Microsoft Word on your system.")
                
        elif "excel" in command_lower or "ms excel" in command_lower:
            try:
                subprocess.Popen(["excel.exe"])
                self.speak("Opening Microsoft Excel!")
            except:
                self.speak("Sorry, I couldn't find Microsoft Excel on your system.")
            
        elif "youtube" in command_lower:
            webbrowser.open("https://www.youtube.com")
            self.speak("Opening YouTube!")
            
            # Check if there's a specific song to play
            if "play" in command_lower:
                song_name = self.extract_song_name(command)
                if song_name:
                    self.speak(f"I've opened YouTube. You can search for {song_name} there!")
            
        else:
            # Try to open as application
            app_name = command_lower.replace("open", "").strip()
            try:
                subprocess.Popen(app_name)
                self.speak(f"Opening {app_name}!")
            except:
                self.speak(f"Sorry, I couldn't find {app_name}. Can you be more specific?")
                
    def handle_youtube_play_command(self, command):
        """Handle YouTube play commands"""
        try:
            # Extract song name from command
            song_name = self.extract_song_name(command)
            if song_name:
                active_window = self.screen_controller.get_active_window_title()
                
                if active_window and "youtube" in active_window:
                    # YouTube is already open, search and play
                    pyautogui.click(640, 100)  # YouTube search box
                    time.sleep(0.5)
                    pyautogui.hotkey('ctrl', 'a')  # Select all
                    time.sleep(0.2)
                    pyautogui.typewrite(song_name)
                    pyautogui.press('enter')
                    time.sleep(2)
                    
                    # Click on first video using improved method
                    if self.screen_controller.click_song_by_name(song_name):
                        self.speak(f"Playing {song_name}!")
                    else:
                        self.speak(f"Searching for {song_name}!")
                else:
                    # Open YouTube first
                    webbrowser.open("https://www.youtube.com")
                    time.sleep(3)
                    
                    # Search for the song
                    pyautogui.click(640, 100)  # YouTube search box
                    time.sleep(1)
                    pyautogui.typewrite(song_name)
                    pyautogui.press('enter')
                    time.sleep(3)
                    
                    # Click on first video
                    if self.screen_controller.click_song_by_name(song_name):
                        self.speak(f"Playing {song_name} on YouTube!")
                    else:
                        self.speak(f"Searching for {song_name} on YouTube!")
            else:
                self.speak("What song would you like me to play?")
        except Exception as e:
            print(f"❌ YouTube play error: {e}")
            self.speak("Sorry, I couldn't open YouTube right now.")
            
    def extract_song_name(self, command):
        """Extract song name from play command"""
        command_lower = command.lower()
        
        # Remove common words to extract song name
        words_to_remove = ["open", "youtube", "and", "play", "song", "music"]
        words = command_lower.split()
        
        # Filter out command words
        song_words = [word for word in words if word not in words_to_remove]
        
        if song_words:
            return " ".join(song_words)
        return None
        
    def handle_typing_command(self, command):
        """Handle typing and messaging commands"""
        try:
            # Extract the text to type or message content
            if "message" in command.lower():
                # Handle WhatsApp messaging
                active_window = self.screen_controller.get_active_window_title()
                
                if active_window and "whatsapp" in active_window:
                    # Extract message content
                    if "hi to" in command.lower():
                        # Handle "send hi to anjali" format
                        parts = command.lower().split("hi to")
                        if len(parts) > 1:
                            contact_name = parts[1].strip().split()[0]
                            if self.screen_controller.search_whatsapp_contact(contact_name):
                                self.speak(f"Found {contact_name}!")
                                time.sleep(1.5)
                                # Actually click on the contact to enter chat
                                if self.screen_controller.click_first_whatsapp_contact():
                                    self.speak(f"Opening {contact_name}'s chat!")
                                    time.sleep(1)
                                    if self.screen_controller.type_whatsapp_message("hi"):
                                        self.speak("Typed hi!")
                                        if self.screen_controller.send_message():
                                            self.speak("Message sent!")
                                    else:
                                        self.speak("Couldn't type the message.")
                                else:
                                    self.speak("Couldn't open the chat.")
                                return
                    
                    # Handle regular message format
                    parts = command.lower().split("message")
                    if len(parts) > 1:
                        message_content = parts[1].strip()
                        if self.screen_controller.type_whatsapp_message(message_content):
                            self.speak(f"Typed: {message_content}")
                            self.speak("Say 'send it' to send the message.")
                        return
                
                # If not in WhatsApp, just type the message
                text_to_type = command.lower().replace("message", "").strip()
                if text_to_type:
                    pyautogui.click(640, 400)
                    time.sleep(0.5)
                    pyautogui.typewrite(text_to_type)
                    self.speak("Typed the message!")
                    
            elif "type" in command.lower():
                # Handle general typing
                text_to_type = command.lower().replace("type", "").strip()
                if text_to_type:
                    pyautogui.click(640, 400)  # Click center area
                    time.sleep(1)
                    pyautogui.typewrite(text_to_type)
                    self.speak("Done typing!")
                else:
                    self.speak("What would you like me to type?")
        except Exception as e:
            print(f"❌ Typing error: {e}")
            self.speak("Sorry, I couldn't type that right now.")
            
    def handle_scroll_command(self, command):
        """Handle scroll commands"""
        try:
            if "down" in command.lower():
                self.screen_controller.scroll_down()
                self.speak("Scrolling down!")
            elif "up" in command.lower():
                self.screen_controller.scroll_up()
                self.speak("Scrolling up!")
            else:
                self.screen_controller.scroll_down()
                self.speak("Scrolling!")
        except Exception as e:
            print(f"❌ Scroll error: {e}")
            self.speak("Sorry, I couldn't scroll.")
            
    def handle_app_search(self, command):
        """Handle search commands in current active application"""
        try:
            search_term = command.lower().replace("search", "").strip()
            active_window = self.screen_controller.get_active_window_title()
            
            if active_window:
                print(f"🔍 Active window: {active_window}")
                
                # Prioritize YouTube search if YouTube is active
                if "youtube" in active_window:
                    self.speak(f"Searching for {search_term}!")
                    if self.screen_controller.search_in_active_app(search_term):
                        time.sleep(2)  # Wait for search results to load
                        return
                    else:
                        self.speak("Sorry, couldn't search on YouTube.")
                        return
                        
                # Try to search in the current active app
                elif self.screen_controller.search_in_active_app(search_term):
                    self.speak(f"Searching for {search_term} in {active_window}!")
                else:
                    # Only fallback to web search if not in a specific app
                    self.speak(f"Searching for {search_term} online!")
                    search_url = f"https://www.google.com/search?q={search_term.replace(' ', '+')}"
                    webbrowser.open(search_url)
                    # Fetch lightweight results in background and store to memory
                    try:
                        results = self._fetch_search_results(search_term)
                        self.session_memory.add_search_results(search_term, results)
                    except Exception as _:
                        pass
            else:
                # Fallback to Google search
                self.speak(f"Searching for {search_term} on Google!")
                self.set_avatar_emotion_for_event('search_start')
                search_url = f"https://www.google.com/search?q={search_term.replace(' ', '+')}"
                webbrowser.open(search_url)
                # Fetch lightweight results in background and store to memory
                try:
                    results = self._fetch_search_results(search_term)
                    self.session_memory.add_search_results(search_term, results)
                    # Set happy emotion when search results are found
                    if results:
                        self.set_avatar_emotion_for_event('search_complete', True)
                except Exception as _:
                    pass
                
        except Exception as e:
            print(f"❌ App search error: {e}")
            self.speak("Sorry, I couldn't perform that search.")
                
    def play_music(self):
        """Play music"""
        try:
            # Try to open default music player
            music_apps = ["spotify", "winamp", "vlc", "wmplayer"]
            opened = False
            
            for app in music_apps:
                try:
                    subprocess.Popen(app)
                    self.speak("Yes Aditya! Let's vibe 🎵")
                    opened = True
                    break
                except:
                    continue
                    
            if not opened:
                # Open YouTube Music as fallback
                webbrowser.open("https://music.youtube.com")
                self.speak("Opening YouTube Music for you!")
                
        except Exception as e:
            self.speak("Sorry, I couldn't start music right now.")
            
    def get_weather(self):
        """Get current weather information"""
        try:
            # Try multiple weather sources
            try:
                response = requests.get("http://wttr.in/?format=3", timeout=5)
                if response.status_code == 200:
                    weather_info = response.text.strip()
                    self.speak(f"The current weather is: {weather_info}")
                    return
            except:
                pass
                
            # Fallback to AI with internet search
            self.ai_response_with_search("What's the current weather in Mumbai, India right now?")
            
        except Exception as e:
            print(f"❌ Weather error: {e}")
            self.speak("Sorry, I couldn't get the weather information right now.")
            
    def web_search(self, query):
        """Perform web search and provide answer"""
        search_term = query.lower().replace("search", "").replace("google", "").strip()
        
        # Check if it's a search within an application
        if "chatgpt" in query.lower() or "chat gpt" in query.lower():
            # Extract search term for ChatGPT
            search_for_chatgpt = search_term.replace("chatgpt", "").replace("chat gpt", "").replace("on", "").strip()
            if search_for_chatgpt:
                self.speak(f"Typing {search_for_chatgpt} in ChatGPT!")
                time.sleep(1)
                try:
                    # Click on ChatGPT input area
                    pyautogui.click(640, 600)  # ChatGPT input box approximate position
                    time.sleep(0.5)
                    pyautogui.typewrite(search_for_chatgpt)
                    pyautogui.press('enter')
                    self.speak(f"I've sent your query to ChatGPT!")
                except Exception as e:
                    print(f"❌ ChatGPT typing error: {e}")
                    self.speak("Please make sure ChatGPT is open and try again.")
            return
            
        elif "youtube" in query.lower():
            # Search within YouTube
            search_for_youtube = search_term.replace("youtube", "").replace("on", "").strip()
            if search_for_youtube:
                self.speak(f"Searching for {search_for_youtube} on YouTube!")
                time.sleep(1)
                try:
                    # Click on YouTube search box
                    pyautogui.click(640, 140)
                    time.sleep(0.5)
                    pyautogui.hotkey('ctrl', 'a')  # Select all existing text
                    pyautogui.typewrite(search_for_youtube)
                    pyautogui.press('enter')
                    self.speak(f"I've searched for {search_for_youtube} on YouTube!")
                except Exception as e:
                    print(f"❌ YouTube search error: {e}")
                    self.speak("Please make sure YouTube is open and try again.")
            return
            
        if search_term:
            # Regular web search
            search_url = f"https://www.google.com/search?q={search_term.replace(' ', '+')}"
            webbrowser.open(search_url)
            self.speak(f"Searching for {search_term} on Google!")
            # Fetch lightweight results and store
            try:
                results = self._fetch_search_results(search_term)
                self.session_memory.add_search_results(search_term, results)
            except Exception as _:
                pass
        else:
            self.speak("What would you like me to search for?")
            
    def tell_time(self):
        """Tell current time"""
        current_time = datetime.now().strftime("%I:%M %p")
        self.speak(f"It's {current_time}")
        
    def tell_date(self):
        """Tell current date"""
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        self.speak(f"Today is {current_date}")
        
    def system_shutdown(self):
        """Shutdown system"""
        self.speak("Shutting down the system. Goodbye Aditya!")
        os.system("shutdown /s /t 5")
        
    def lock_system(self):
        """Lock the system"""
        self.speak("Locking the system for you!")
        if WINDOWS_FEATURES:
            subprocess.run("rundll32.exe user32.dll,LockWorkStation")
        else:
            os.system("rundll32.exe user32.dll,LockWorkStation")
        
    def search_internet(self, query):
        """Search the internet for real-time information"""
        try:
            # Enhanced search prompt for better responses
            search_prompt = f"""
            You are TARA, Aditya's personal AI assistant with access to information. 
            
            Question: {query}
            
            Please provide a helpful, accurate answer. If this is about:
            - Current events, weather, or time-sensitive info: Give the best information you can
            - People (like "who is MS Dhoni"): Provide biographical information
            - Technical topics (like "how do AI LLMs work"): Explain in simple terms
            - General knowledge: Answer directly and conversationally
            
            Respond as TARA - friendly, supportive, and like you're talking to your best friend Aditya.
            Keep responses under 150 words and natural sounding.
            """
            
            if self.model is None:
                return None
                
            response = self.model.generate_content(search_prompt)
            if response and response.text:
                answer = response.text.strip()
                # Background: also store lightweight search results for this query
                try:
                    results = self._fetch_search_results(query)
                    self.session_memory.add_search_results(query, results)
                except Exception as _:
                    pass
                return answer
            else:
                return None
            
        except Exception as e:
            print(f"❌ Internet search error: {e}")
            return None
            
    def ai_response_with_search(self, query):
        """Get AI response with internet search capability"""
        try:
            # Always try to get the best possible answer
            print(f"🔍 Processing query: {query}")
            
            # Check for quota errors and use offline responses
            if self.is_quota_exceeded():
                print("⚠️ API quota exceeded, using offline responses")
                self.handle_offline_response(query)
                return
            
            # Use enhanced search for all queries
            answer = self.search_internet(query)
            
            if answer:
                print(f"✅ Got response from AI")
                # Set happy emotion for successful AI response
                self.set_avatar_emotion_for_event('search_complete', True)
                self.speak(answer)
                # Add to conversation memory
                self.conversation_memory.append({
                    "query": query,
                    "response": answer,
                    "timestamp": datetime.now().isoformat(),
                    "type": "enhanced_search"
                })
                # Also record assistant message to session memory (already done in speak)
                return
            else:
                print("⚠️ No response from enhanced search, trying offline")
                # Set neutral emotion for fallback
                self.set_avatar_emotion_for_event('search_complete', False)
                # Fallback to offline response
                self.handle_offline_response(query)
            
        except Exception as e:
            print(f"❌ AI response with search error: {e}")
            # Set sad emotion for errors
            self.set_avatar_emotion_for_event('command_error', False)
            # Check if it's a quota error
            if "429" in str(e) or "quota" in str(e).lower():
                self.handle_offline_response(query)
            else:
                self.speak("I'm having trouble processing that right now. Can you try asking again?")
            
    def ai_response(self, query):
        """Get AI response using Gemini"""
        try:
            # Add personality context to the query
            personality_prompt = f"""
            You are TARA, Aditya's personal AI assistant with a friendly, caring personality. 
            You speak like a close friend, sometimes mixing Hindi and English naturally.
            You're helpful, witty, and always supportive. Keep responses conversational and warm.
            
            Answer this question as if you're talking to your best friend Aditya:
            {query}
            
            Keep your response under 100 words and make it sound natural and friendly.
            """
            
            if self.model is None:
                self.speak("Sorry, my AI capabilities are not available right now.")
                return
                
            response = self.model.generate_content(personality_prompt)
            answer = response.text
            
            # Add to conversation memory
            self.conversation_memory.append({
                "query": query,
                "response": answer,
                "timestamp": datetime.now().isoformat()
            })
            
            self.speak(answer)
            
        except Exception as e:
            print(f"❌ AI response error: {e}")
            # Check if it's a quota error
            if "429" in str(e) or "quota" in str(e).lower():
                self.handle_offline_response(query)
            else:
                fallback_responses = [
                    "That's an interesting question! Let me think about it...",
                    "Hmm, I'm not sure about that right now, but I'm always learning!",
                    "That's a great question, Aditya! I wish I had a better answer for you."
                ]
                self.speak(random.choice(fallback_responses))
            
    def is_quota_exceeded(self):
        """Check if API quota is exceeded"""
        return self.quota_exceeded
        
    def handle_offline_response(self, query):
        """Handle responses when API is unavailable"""
        query_lower = query.lower()
        
        # Basic knowledge responses
        knowledge_base = {
            "virat kohli": "Virat Kohli is one of the greatest cricketers of all time! He's the former captain of the Indian cricket team, known for his aggressive batting style and incredible fitness. He's scored over 70 international centuries and is considered a modern cricket legend.",
            "ms dhoni": "MS Dhoni is Captain Cool! He's the former Indian cricket captain who led India to victory in the 2007 T20 World Cup, 2011 Cricket World Cup, and 2013 Champions Trophy. Known for his calm demeanor and finishing skills.",
            "narendra modi": "Narendra Modi is the current Prime Minister of India, serving since 2014. He was previously the Chief Minister of Gujarat and is known for various initiatives like Digital India and Make in India.",
            "india": "India is our beautiful country! It's the world's largest democracy with over 1.4 billion people, rich cultural heritage, diverse languages, and incredible history spanning thousands of years.",
            "cricket": "Cricket is India's most popular sport! It's played between two teams of 11 players each, with formats like Test, ODI, and T20. India has won multiple World Cups and has legendary players.",
            "bollywood": "Bollywood is India's Hindi film industry based in Mumbai! It produces hundreds of movies every year and is known for its colorful musicals, dance sequences, and dramatic stories.",
            "time": f"It's {datetime.now().strftime('%I:%M %p')} right now!",
            "date": f"Today is {datetime.now().strftime('%A, %B %d, %Y')}",
            "weather": "I can't check live weather right now, but you can ask me to open a weather website or app for current conditions!"
        }
        
        # Check for matches
        for key, response in knowledge_base.items():
            if key in query_lower:
                self.speak(response)
                return
                
        # Conversation responses
        if any(word in query_lower for word in ["hello", "hi", "how are you"]):
            responses = [
                "Hello Aditya! I'm doing great, thanks for asking! How are you?",
                "Hi there! I'm good, just here ready to help you with anything!",
                "Hey Aditya! I'm fantastic and ready for whatever you need!"
            ]
            self.speak(random.choice(responses))
        elif any(word in query_lower for word in ["what are you doing", "what you doing"]):
            responses = [
                "Just hanging out here, waiting to help you with whatever you need!",
                "I'm here listening and ready to assist you with anything, Aditya!",
                "Nothing much, just being your loyal AI assistant! What can I do for you?"
            ]
            self.speak(random.choice(responses))
        else:
            # Generic fallback
            responses = [
                "I'm running in offline mode right now, so my knowledge is limited. But I'm still here to help with what I can!",
                "My internet connection to AI services is limited right now, but I can still help with basic tasks and commands!",
                "I'm in offline mode at the moment, but I can still control your system and help with many things!"
            ]
            self.speak(random.choice(responses))

    def start_listening(self):
        """Start the main listening loop"""
        print("🚀 TARA is immediately active and ready for commands!")
        print("💬 No wake word needed - just speak your commands directly!")
        self.listen_for_wake_word()
    
    def shutdown(self):
        """Clean shutdown of all systems"""
        if self.gesture_controller:
            self.gesture_controller.stop()
        if self.avatar_system:
            self.avatar_system.stop()
        print("👋 TARA systems shut down")

    # ------------------ Session Memory Helpers ------------------
    def _fetch_search_results(self, query, max_items: int = 8):
        """Fetch lightweight DuckDuckGo HTML results without new deps. Returns list of {title,url,snippet}."""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            url = f"https://duckduckgo.com/html/?q={query.replace(' ', '+')}"
            resp = requests.get(url, headers=headers, timeout=8)
            html = resp.text
            results = []
            # Very lightweight parsing using regex for anchors within result blocks
            import re as _re
            # Each result in DDG html has class result__a for title anchors
            for m in _re.finditer(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, flags=_re.I|_re.S):
                link = m.group(1)
                title_html = m.group(2)
                title = _re.sub('<[^<]+?>', '', title_html)
                # Try to get snippet nearby
                snippet_match = _re.search(r'<a[^>]*class="result__a"[^>]*>.*?</a>.*?<a[^>]*class="result__snippet"[^>]*>(.*?)</a>|<a[^>]*class="result__a"[^>]*>.*?</a>.*?<span[^>]*class="result__snippet"[^>]*>(.*?)</span>', html[m.start():m.end()+400], flags=_re.I|_re.S)
                snippet_html = (snippet_match.group(1) or snippet_match.group(2)) if snippet_match else ''
                snippet = _re.sub('<[^<]+?>', '', snippet_html)
                results.append({"title": title.strip(), "url": link, "snippet": snippet.strip()})
                if len(results) >= max_items:
                    break
            print(f"🔎 Parsed {len(results)} DDG results for '{query}'")
            return results
        except Exception as e:
            print(f"❌ _fetch_search_results error: {e}")
            return []

    def _summarize_text(self, text: str, max_words: int = 150) -> str:
        """Use Gemini model to summarize text briefly."""
        try:
            if not text:
                return "I couldn't fetch any content to summarize."
            prompt = f"Summarize the following content in under {max_words} words, focusing on key points and keeping it friendly and concise.\n\nCONTENT:\n{text[:6000]}"
            if self.model is None:
                return text[:max_words] + ("..." if len(text) > max_words else "")
            resp = self.model.generate_content(prompt)
            return resp.text.strip() if resp and resp.text else text[:max_words]
        except Exception as e:
            print(f"❌ _summarize_text error: {e}")
            return "Sorry, I had trouble summarizing that."

    def summarize_url(self, url: str) -> str:
        """Fetch URL content quickly and summarize using model."""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            r = requests.get(url, headers=headers, timeout=8)
            text = r.text
            # Strip HTML tags roughly
            import re as _re
            text = _re.sub('<script[\s\S]*?</script>', ' ', text)
            text = _re.sub('<style[\s\S]*?</style>', ' ', text)
            text = _re.sub('<[^<]+?>', ' ', text)
            text = _re.sub('\s+', ' ', text)
            return self._summarize_text(text)
        except Exception as e:
            print(f"❌ summarize_url error: {e}")
            return "Sorry, I couldn't fetch that page to summarize."

    def handle_reference_command(self, command_lower: str) -> bool:
        """Resolve and execute actions for reference-based commands. Returns True if handled."""
        try:
            ref = self.session_memory.resolve_reference(command_lower)
            if not ref or not ref.get("item"):
                return False
            item = ref["item"]
            url = item.get("url")
            title = item.get("title") or "the result"

            if "summarize" in command_lower and url:
                self.speak(f"Summarizing {title} for you…")
                summary = self.summarize_url(url)
                self.speak(summary)
                return True
            if any(k in command_lower for k in ["open", "play", "show"]) and url:
                webbrowser.open(url)
                self.speak(f"Opening {title}!")
                return True
            return False
        except Exception as e:
            print(f"❌ handle_reference_command error: {e}")
            return False
    
    # ------------------ Gesture Control Setup ------------------
    def setup_gesture_control(self):
        """Initialize gesture control system"""
        try:
            self.gesture_controller = GestureController(self.screen_controller)
            print("✅ Gesture control system initialized")
        except Exception as e:
            print(f"⚠️ Could not initialize gesture control: {e}")
            self.gesture_controller = None
    
    def handle_gesture_enable_command(self):
        """Handle voice command to enable gesture control"""
        try:
            if not self.gesture_controller:
                self.setup_gesture_control()
                if not self.gesture_controller:
                    self.speak("Sorry, gesture control is not available on this system.")
                    return
            
            if self.gesture_controller.enable():
                self.set_avatar_emotion_for_event('command_success', True)
                self.speak("Gesture control enabled! You can now use hand gestures to control me.")
            else:
                self.set_avatar_emotion_for_event('command_error', False)
                self.speak("Sorry, I couldn't enable gesture control. Please check your webcam.")
        except Exception as e:
            print(f"❌ Error enabling gesture control: {e}")
            self.speak("Sorry, there was an error enabling gesture control.")
    
    def handle_gesture_disable_command(self):
        """Handle voice command to disable gesture control"""
        try:
            if self.gesture_controller:
                self.gesture_controller.disable()
                self.set_avatar_emotion_for_event('command_success', True)
                self.speak("Gesture control disabled. Voice commands are still active.")
            else:
                self.speak("Gesture control is not currently running.")
        except Exception as e:
            print(f"❌ Error disabling gesture control: {e}")
            self.speak("Sorry, there was an error disabling gesture control.")
    
    # ------------------ Avatar System Setup ------------------
    def setup_avatar_system(self):
        """Initialize 3D avatar system"""
        try:
            if ENABLE_AVATAR:
                self.avatar_system = AvatarSystem(enable_avatar=True)
                print("✅ Avatar system initialized")
            else:
                print("🎭 Avatar system disabled in config")
        except Exception as e:
            print(f"⚠️ Could not initialize avatar system: {e}")
            self.avatar_system = None
    
    def set_avatar_emotion_for_event(self, event_type: str, success: bool = True):
        """Set avatar emotion based on event type"""
        if self.avatar_system:
            emotion = EmotionMapper.get_emotion_for_event(event_type, success)
            self.avatar_system.set_emotion(emotion)
    
    def set_avatar_action(self, action: str):
        """Update avatar with current action"""
        if self.avatar_system:
            self.avatar_system.set_action(action)
    
    # ------------------ Language System Setup ------------------
    def setup_language_system(self):
        """Initialize multi-language system"""
        try:
            if ENABLE_AUTO_LANGUAGE_DETECTION:
                self.language_detector = LanguageDetector()
                print("✅ Multi-language system initialized")
            else:
                print("🌐 Multi-language detection disabled in config")
        except Exception as e:
            print(f"⚠️ Could not initialize language system: {e}")
            self.language_detector = None
    
    def _recognize_speech_multilingual(self, audio) -> str:
        """Recognize speech with multi-language support"""
        try:
            # Try Hindi first if current language is Hindi
            if self.current_language == "hi":
                try:
                    text = self.recognizer.recognize_google(audio, language='hi-IN')
                    return text
                except:
                    pass
            
            # Try English
            try:
                text = self.recognizer.recognize_google(audio, language='en-US')
                return text
            except:
                pass
            
            # Try Hindi as fallback
            if self.current_language != "hi":
                try:
                    text = self.recognizer.recognize_google(audio, language='hi-IN')
                    return text
                except:
                    pass
            
            return None
            
        except Exception as e:
            print(f"❌ Multi-language recognition error: {e}")
            return None
    
    def _process_multilingual_input(self, text: str) -> tuple:
        """Process input with language detection and translation"""
        if not self.language_detector or not ENABLE_AUTO_LANGUAGE_DETECTION:
            return text, self.current_language, False
        
        try:
            processed_text, detected_lang, lang_changed = self.language_detector.process_command(text)
            if lang_changed:
                self.current_language = detected_lang
            return processed_text, detected_lang, lang_changed
        except Exception as e:
            print(f"❌ Language processing error: {e}")
            return text, self.current_language, False
    
    def _handle_language_switch(self, new_language: str):
        """Handle language switch with avatar feedback"""
        try:
            if new_language == "hi":
                feedback = "अब मैं हिंदी में सुन रही हूँ।"
                if self.avatar_system:
                    self.avatar_system.set_emotion('thinking')
                    # Brief pause then happy
                    import threading
                    def delayed_happy():
                        import time
                        time.sleep(0.5)
                        self.avatar_system.set_emotion('happy')
                    threading.Thread(target=delayed_happy, daemon=True).start()
            else:
                feedback = "Back to English mode."
                if self.avatar_system:
                    self.avatar_system.set_emotion('happy')
            
            self.speak(feedback)
            
        except Exception as e:
            print(f"❌ Language switch handling error: {e}")
    
    def get_language_status(self) -> dict:
        """Get current language system status"""
        status = {
            "current_language": self.current_language,
            "supported_languages": SUPPORTED_LANGUAGES,
            "auto_detection_enabled": ENABLE_AUTO_LANGUAGE_DETECTION,
            "detector_available": self.language_detector is not None
        }
        
        if self.language_detector:
            status.update(self.language_detector.get_status())
        
        return status
    
    def handle_cursor_enable_command(self):
        """Handle voice command to enable cursor control"""
        try:
            if not self.gesture_controller:
                self.setup_gesture_control()
                if not self.gesture_controller:
                    self.speak("Sorry, gesture control is not available on this system.")
                    return
            
            if self.gesture_controller.enable_cursor_mode():
                self.set_avatar_emotion_for_event('command_success', True)
                self.speak("Cursor control enabled! Point with your index finger to move the cursor.")
            else:
                self.set_avatar_emotion_for_event('command_error', False)
                self.speak("Sorry, I couldn't enable cursor control. Please check your webcam.")
        except Exception as e:
            print(f"❌ Error enabling cursor control: {e}")
            self.speak("Sorry, there was an error enabling cursor control.")
    
    def handle_cursor_disable_command(self):
        """Handle voice command to disable cursor control"""
        try:
            if self.gesture_controller:
                self.gesture_controller.disable_cursor_mode()
                self.set_avatar_emotion_for_event('command_success', True)
                self.speak("Cursor control disabled. Regular gesture mode is still active.")
            else:
                self.speak("Cursor control is not currently running.")
        except Exception as e:
            print(f"❌ Error disabling cursor control: {e}")
            self.speak("Sorry, there was an error disabling cursor control.")
    
    def handle_cursor_only_command(self):
        """Handle voice command for cursor-only mode (no gestures)"""
        try:
            if not self.gesture_controller:
                self.setup_gesture_control()
                if not self.gesture_controller:
                    self.speak("Sorry, gesture control is not available on this system.")
                    return
            
            # Manually set cursor-only mode
            self.gesture_controller.cursor_mode = True
            self.gesture_controller.cursor_only_mode = True
            self.gesture_controller.gesture_mode = False
            self.gesture_controller.is_enabled = True
            
            self.set_avatar_emotion_for_event('command_success', True)
            self.speak("Cursor-only mode enabled! Point to move cursor, make fist to click. No scrolling gestures.")
            print("🖱️ Cursor-only mode: Point to move, fist to click")
            
        except Exception as e:
            print(f"❌ Error enabling cursor-only mode: {e}")
            self.speak("Sorry, there was an error enabling cursor-only mode.")
    
    def handle_gesture_only_command(self):
        """Handle voice command for gesture-only mode (no cursor tracking)"""
        try:
            if not self.gesture_controller:
                self.setup_gesture_control()
                if not self.gesture_controller:
                    self.speak("Sorry, gesture control is not available on this system.")
                    return
            
            # Manually set gesture-only mode
            self.gesture_controller.cursor_mode = False
            self.gesture_controller.cursor_only_mode = False
            self.gesture_controller.gesture_mode = True
            self.gesture_controller.is_enabled = True
            
            self.set_avatar_emotion_for_event('command_success', True)
            self.speak("Gesture-only mode enabled! Use hand gestures for scrolling and clicking. No cursor tracking.")
            print("🤲 Gesture-only mode: ✋ scroll down, ✊ scroll up, 👉 click center")
            
        except Exception as e:
            print(f"❌ Error enabling gesture-only mode: {e}")
            self.speak("Sorry, there was an error enabling gesture-only mode.")
    
    def handle_smart_mode_command(self):
        """Handle voice command for smart dual mode with pout trigger"""
        try:
            # Import the smart controller
            from smart_gesture_control_fixed import SmartGestureController
            
            # Replace existing controller with smart controller
            if self.gesture_controller:
                self.gesture_controller.stop()
            
            self.gesture_controller = SmartGestureController(self.screen_controller)
            
            if self.gesture_controller.enable():
                self.set_avatar_emotion_for_event('command_success', True)
                self.speak("Smart dual mode enabled! Use regular gestures, or join five fingers together to control cursor.")
                print("🧠 Smart Mode Active:")
                print("🤲 Regular gestures: ✋ scroll down, ✊ scroll up, 👉 click center")
                print("🖱️ Cursor control: Join 5 fingers (pout) to move cursor")
            else:
                self.speak("Sorry, I couldn't enable smart mode.")
                
        except Exception as e:
            print(f"❌ Error enabling smart mode: {e}")
            self.speak("Sorry, there was an error enabling smart mode.")
    
    def handle_dual_hand_mode_command(self):
        """Handle voice command for dual-hand mode with 8-10 finger cursor trigger"""
        try:
            # Import the dual-hand controller
            from dual_hand_gesture_control_fixed import DualHandGestureController
            
            # Replace existing controller with dual-hand controller
            if self.gesture_controller:
                self.gesture_controller.stop()
            
            self.gesture_controller = DualHandGestureController(self.screen_controller)
            
            if self.gesture_controller.enable():
                self.set_avatar_emotion_for_event('command_success', True)
                self.speak("Dual hand mode enabled! Use one hand for gestures, or show both hands with eight to ten fingers for cursor control.")
                print("🤲 Dual-Hand Mode Active:")
                print("🖐️ Single hand: ✋ scroll down, ✊ scroll up, 👉 click, ✌️ click, 👍 play/pause")
                print("🖐️🖐️ Both hands (8-10 fingers): Cursor control mode")
            else:
                self.speak("Sorry, I couldn't enable dual hand mode.")
                
        except Exception as e:
            print(f"❌ Error enabling dual hand mode: {e}")
            self.speak("Sorry, there was an error enabling dual hand mode.")
    
    def auto_enable_controls(self):
        """Automatically enable gesture and cursor control on startup"""
        try:
            print("🚀 Auto-enabling gesture and cursor controls...")
            
            # Setup gesture controller if not already done
            if not self.gesture_controller:
                self.setup_gesture_control()
            
            if self.gesture_controller:
                # Enable dual-hand mode by default (no conflicts!)
                try:
                    from dual_hand_gesture_control_fixed import DualHandGestureController
                    
                    # Replace with dual-hand controller
                    self.gesture_controller.stop()
                    self.gesture_controller = DualHandGestureController(self.screen_controller)
                    
                    if self.gesture_controller.enable():
                        print("✅ Dual-hand mode auto-enabled!")
                        print("🖐️ Single hand: ✋ scroll down, ✊ scroll up, 👉 click, ✌️ click, 👍 play/pause")
                        print("🖐️🖐️ Both hands (8-10 fingers): Cursor control mode")
                        print("💡 No conflicts - single hand for gestures, both hands for cursor!")
                    else:
                        # Fallback to regular gesture mode
                        self.gesture_controller.cursor_mode = False
                        self.gesture_controller.cursor_only_mode = False
                        self.gesture_controller.gesture_mode = True
                        self.gesture_controller.is_enabled = True
                        print("✅ Basic gesture control auto-enabled!")
                        
                except Exception as e:
                    print(f"⚠️ Could not enable smart mode, using basic gestures: {e}")
                    # Fallback to basic gesture mode
                    self.gesture_controller.cursor_mode = False
                    self.gesture_controller.cursor_only_mode = False
                    self.gesture_controller.gesture_mode = True
                    self.gesture_controller.is_enabled = True
                    print("✅ Basic gesture control auto-enabled!")
            else:
                print("⚠️ Gesture control not available - continuing without gestures")
                
        except Exception as e:
            print(f"⚠️ Could not auto-enable controls: {e}")
            print("💡 You can manually enable with voice commands later")

def main():
    """Main function to start TARA"""
    tara = None
    try:
        tara = TARA()
        tara.start_listening()
    except KeyboardInterrupt:
        print("\n👋 TARA shutting down...")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        if tara:
            tara.shutdown()

if __name__ == "__main__":
    main()
