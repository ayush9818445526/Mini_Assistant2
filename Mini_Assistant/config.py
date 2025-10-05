#!/usr/bin/env python3
"""
TARA Configuration File
Store sensitive configuration data here
"""

# Gemini AI Configuration
GEMINI_API_KEY = "AIzaSyC3dEbfROlWewhVZPCMwKEXRSPTPekBjR8"

# ElevenLabs Voice Configuration
ELEVENLABS_API_KEY = "sk_adee1c3c4ca64d462b4a3c1c94fb207075f7d5197a8c5fd2"  # ElevenLabs API key
ELEVENLABS_VOICE_ID = "Dk3lflqf310KiWVmwB9F"  # The voice ID you provided

# TARA Settings
OWNER_NAME = "Aditya"
WAKE_WORD = "tara"
TARA_FULL_NAME = "Tripathi Aditya's Reactive Angel"

# Voice Settings
VOICE_RATE = 180
VOICE_VOLUME = 0.9

# Speech Recognition Settings
ENERGY_THRESHOLD = 300
PAUSE_THRESHOLD = 0.8
LISTEN_TIMEOUT = 2
PHRASE_TIME_LIMIT = 5

# Language Settings
SUPPORTED_LANGUAGES = ["en", "hi"]  # English and Hindi support
DEFAULT_LANGUAGE = "en"  # Default language
ENABLE_AUTO_LANGUAGE_DETECTION = True  # Auto-detect and switch languages

# System Settings
ENABLE_FACE_RECOGNITION = False  # Set to True when face_recognition is installed
ENABLE_AVATAR = True  # Set to False to disable 3D avatar system
DEBUG_MODE = False
