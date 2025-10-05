#!/usr/bin/env python3
"""
TARA Voice System with ElevenLabs Integration
Natural human-like voice with emotional expressions
"""

import os
import io
import pygame
import requests
import threading
import time
from elevenlabs import generate, set_api_key, Voice, VoiceSettings
from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID

class TaraVoiceSystem:
    def __init__(self):
        self.is_speaking = False
        self.voice_queue = []
        self.setup_elevenlabs()
        self.setup_pygame()
        
    def setup_elevenlabs(self):
        """Initialize ElevenLabs API"""
        try:
            if ELEVENLABS_API_KEY != "your_elevenlabs_api_key_here":
                set_api_key(ELEVENLABS_API_KEY)
                self.elevenlabs_available = True
                print("✅ ElevenLabs voice system initialized")
            else:
                self.elevenlabs_available = False
                print("⚠️ ElevenLabs API key not set, using fallback TTS")
        except Exception as e:
            print(f"❌ ElevenLabs setup error: {e}")
            self.elevenlabs_available = False
            
    def setup_pygame(self):
        """Initialize pygame for audio playback"""
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            print("✅ Audio system initialized")
        except Exception as e:
            print(f"❌ Audio system error: {e}")
            
    def speak_with_emotion(self, text, emotion="neutral", stability=0.5, similarity_boost=0.8):
        """Speak text with emotional voice using ElevenLabs"""
        if not self.elevenlabs_available:
            return self.fallback_speak(text)
            
        try:
            # Adjust voice settings based on emotion
            voice_settings = self.get_emotion_settings(emotion, stability, similarity_boost)
            
            # Generate audio
            audio = generate(
                text=text,
                voice=Voice(
                    voice_id=ELEVENLABS_VOICE_ID,
                    settings=voice_settings
                )
            )
            
            # Play audio
            self.play_audio(audio)
            return True
            
        except Exception as e:
            print(f"❌ ElevenLabs speech error: {e}")
            return self.fallback_speak(text)
            
    def get_emotion_settings(self, emotion, stability, similarity_boost):
        """Get voice settings based on emotion"""
        emotion_settings = {
            "neutral": {"stability": 0.5, "similarity_boost": 0.8, "style": 0.0},
            "happy": {"stability": 0.3, "similarity_boost": 0.9, "style": 0.2},
            "excited": {"stability": 0.2, "similarity_boost": 0.9, "style": 0.4},
            "sad": {"stability": 0.8, "similarity_boost": 0.6, "style": 0.1},
            "thinking": {"stability": 0.7, "similarity_boost": 0.7, "style": 0.0},
            "friendly": {"stability": 0.4, "similarity_boost": 0.8, "style": 0.3},
            "caring": {"stability": 0.6, "similarity_boost": 0.8, "style": 0.2}
        }
        
        settings = emotion_settings.get(emotion, emotion_settings["neutral"])
        
        return VoiceSettings(
            stability=settings["stability"],
            similarity_boost=settings["similarity_boost"],
            style=settings.get("style", 0.0),
            use_speaker_boost=True
        )
        
    def play_audio(self, audio_data):
        """Play audio using pygame"""
        try:
            self.is_speaking = True
            
            # Convert audio data to pygame sound
            audio_io = io.BytesIO(audio_data)
            pygame.mixer.music.load(audio_io)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
            self.is_speaking = False
            
        except Exception as e:
            print(f"❌ Audio playback error: {e}")
            self.is_speaking = False
            
    def fallback_speak(self, text):
        """Fallback to pyttsx3 if ElevenLabs fails"""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            
            # Set female voice if available
            voices = engine.getProperty('voices')
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
                    
            engine.setProperty('rate', 180)
            engine.setProperty('volume', 0.9)
            
            self.is_speaking = True
            engine.say(text)
            engine.runAndWait()
            self.is_speaking = False
            
            return True
            
        except Exception as e:
            print(f"❌ Fallback TTS error: {e}")
            self.is_speaking = False
            return False
            
    def speak_async(self, text, emotion="neutral"):
        """Speak text asynchronously"""
        def speak_thread():
            self.speak_with_emotion(text, emotion)
            
        thread = threading.Thread(target=speak_thread, daemon=True)
        thread.start()
        
    def is_currently_speaking(self):
        """Check if currently speaking"""
        return self.is_speaking
        
    def stop_speaking(self):
        """Stop current speech"""
        try:
            pygame.mixer.music.stop()
            self.is_speaking = False
        except:
            pass

# Test the voice system
if __name__ == "__main__":
    voice = TaraVoiceSystem()
    
    # Test different emotions
    test_phrases = [
        ("Hello! I'm TARA, your personal assistant!", "happy"),
        ("I'm thinking about your request...", "thinking"),
        ("That's so exciting! Let's do it!", "excited"),
        ("I'm here for you, always.", "caring"),
        ("Nice to meet you! I'm TARA.", "friendly")
    ]
    
    for text, emotion in test_phrases:
        print(f"Testing {emotion}: {text}")
        voice.speak_with_emotion(text, emotion)
        time.sleep(1)
