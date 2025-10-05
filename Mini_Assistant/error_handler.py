#!/usr/bin/env python3
"""
TARA Error Handler and Logger
Comprehensive error handling and debugging utilities
"""

import logging
import traceback
from datetime import datetime
import os

class TaraErrorHandler:
    def __init__(self, log_file="tara_errors.log"):
        self.log_file = log_file
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def log_error(self, error, context="General"):
        """Log error with context"""
        error_msg = f"[{context}] {str(error)}"
        self.logger.error(error_msg)
        self.logger.error(traceback.format_exc())
        
    def log_info(self, message, context="Info"):
        """Log information"""
        info_msg = f"[{context}] {message}"
        self.logger.info(info_msg)
        
    def log_warning(self, message, context="Warning"):
        """Log warning"""
        warn_msg = f"[{context}] {message}"
        self.logger.warning(warn_msg)
        
    def safe_execute(self, func, *args, **kwargs):
        """Safely execute a function with error handling"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.log_error(e, f"Function: {func.__name__}")
            return None
            
    def check_dependencies(self):
        """Check if all required dependencies are available"""
        dependencies = {
            'speech_recognition': 'speechrecognition',
            'pyttsx3': 'pyttsx3',
            'pyautogui': 'pyautogui',
            'google.generativeai': 'google-generativeai',
            'cv2': 'opencv-python',
            'numpy': 'numpy',
            'PIL': 'pillow',
            'requests': 'requests',
            'psutil': 'psutil',
            'win32gui': 'pywin32'
        }
        
        missing_deps = []
        for module, package in dependencies.items():
            try:
                __import__(module)
                self.log_info(f"✅ {package} - Available")
            except ImportError:
                missing_deps.append(package)
                self.log_warning(f"❌ {package} - Missing")
                
        if missing_deps:
            self.log_warning(f"Missing dependencies: {', '.join(missing_deps)}")
            return False
        else:
            self.log_info("All dependencies are available")
            return True
            
    def diagnose_audio_issues(self):
        """Diagnose common audio-related issues"""
        try:
            import speech_recognition as sr
            import pyttsx3
            
            # Test microphone
            r = sr.Recognizer()
            mic = sr.Microphone()
            
            self.log_info("Testing microphone access...")
            with mic as source:
                r.adjust_for_ambient_noise(source, duration=1)
            self.log_info("✅ Microphone access successful")
            
            # Test TTS
            self.log_info("Testing text-to-speech...")
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            self.log_info(f"✅ Found {len(voices)} voices available")
            
            return True
            
        except Exception as e:
            self.log_error(e, "Audio Diagnosis")
            return False
            
    def diagnose_ai_connection(self):
        """Diagnose AI connection issues"""
        try:
            import google.generativeai as genai
            from config import GEMINI_API_KEY
            
            self.log_info("Testing Gemini AI connection...")
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Test with a simple query
            response = model.generate_content("Hello, this is a test.")
            if response and response.text:
                self.log_info("✅ Gemini AI connection successful")
                return True
            else:
                self.log_warning("❌ Gemini AI response empty")
                return False
                
        except Exception as e:
            self.log_error(e, "AI Connection Diagnosis")
            return False
            
    def run_full_diagnosis(self):
        """Run complete system diagnosis"""
        self.log_info("=" * 50)
        self.log_info("TARA System Diagnosis Started")
        self.log_info("=" * 50)
        
        results = {
            'dependencies': self.check_dependencies(),
            'audio': self.diagnose_audio_issues(),
            'ai_connection': self.diagnose_ai_connection()
        }
        
        self.log_info("=" * 50)
        self.log_info("Diagnosis Summary:")
        for component, status in results.items():
            status_text = "✅ PASS" if status else "❌ FAIL"
            self.log_info(f"{component.upper()}: {status_text}")
        
        all_good = all(results.values())
        if all_good:
            self.log_info("🎉 All systems operational!")
        else:
            self.log_warning("⚠️ Some issues detected. Check logs above.")
            
        self.log_info("=" * 50)
        return all_good
