import re
import requests
import json
from typing import Optional, Dict, Tuple, List
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
import unicodedata


class LanguageDetector:
    """
    Multi-language detection and translation system for TARA.
    Supports automatic language detection and command translation.
    """
    
    def __init__(self):
        # Set seed for consistent language detection
        DetectorFactory.seed = 0
        
        # Supported languages
        self.supported_languages = ["en", "hi"]
        self.current_language = "en"
        
        # Hindi command translation dictionary
        self.hindi_commands = {
            # Basic actions
            "kholo": "open",
            "khole": "open", 
            "band karo": "close",
            "band kar": "close",
            "chalu karo": "start",
            "chalu kar": "start",
            "roko": "stop",
            "rok": "stop",
            "band": "close",
            
            # Navigation
            "upar": "up",
            "neeche": "down", 
            "peeche": "back",
            "aage": "forward",
            "left": "left",
            "right": "right",
            "baaye": "left",
            "daaye": "right",
            
            # Scroll commands
            "scroll karo": "scroll",
            "scroll kar": "scroll",
            "upar karo": "scroll up",
            "upar kar": "scroll up",
            "neeche karo": "scroll down",
            "neeche kar": "scroll down",
            
            # Media controls
            "chalao": "play",
            "chala": "play",
            "video chalao": "play video",
            "gaana chalao": "play music",
            "music chalao": "play music",
            "pause karo": "pause",
            "pause kar": "pause",
            
            # Search commands
            "dhundo": "search",
            "dhundho": "search",
            "search karo": "search",
            "search kar": "search",
            "google karo": "google search",
            "google kar": "google search",
            
            # Numbers and ordinals
            "pehla": "first",
            "pahla": "first",
            "dusra": "second",
            "teesra": "third",
            "chautha": "fourth",
            "paanchva": "fifth",
            "aakhri": "last",
            "last": "last",
            
            # Applications
            "youtube": "youtube",
            "whatsapp": "whatsapp",
            "chrome": "chrome",
            "browser": "browser",
            "notepad": "notepad",
            "calculator": "calculator",
            
            # Common words
            "video": "video",
            "gaana": "song",
            "music": "music",
            "message": "message",
            "type karo": "type",
            "type kar": "type",
            "click karo": "click",
            "click kar": "click",
            "send karo": "send",
            "send kar": "send",
            
            # Questions
            "kya": "what",
            "kaun": "who", 
            "kaise": "how",
            "kab": "when",
            "kahan": "where",
            "kyun": "why",
            "kitna": "how much",
            "kitne": "how many",
            
            # Responses
            "haan": "yes",
            "nahi": "no",
            "theek hai": "okay",
            "accha": "good",
            "dhanyawad": "thank you",
            "shukriya": "thank you",
            
            # Extended commands
            "band kar do": "close",
            "chalu kar do": "start",
            "rukh jao": "stop",
            "ruk jao": "stop",
            "dekho": "look",
            "dekh": "look",
            "sunao": "tell",
            "suna": "tell",
            "batao": "tell",
            "bata": "tell",
            "samjhao": "explain",
            "samjha": "explain",
            
            # More navigation
            "aage badho": "go forward",
            "peeche jao": "go back",
            "wapas jao": "go back",
            "ghar jao": "go home",
            "home jao": "go home",
            
            # Volume and controls
            "awaz badha": "volume up",
            "awaz kam kar": "volume down",
            "chup": "mute",
            "chup kar": "mute",
            "band kar awaz": "mute",
            
            # More media
            "next": "next",
            "agla": "next",
            "pichla": "previous",
            "previous": "previous",
            "repeat": "repeat",
            "dobara": "repeat",
            "phir se": "again",
            
            # Time and date
            "samay": "time",
            "time": "time",
            "tarikh": "date",
            "date": "date",
            "aaj": "today",
            "kal": "tomorrow",
            "parso": "day after tomorrow",
            
            # Weather
            "mausam": "weather",
            "weather": "weather",
            "barish": "rain",
            "dhoop": "sun",
            "thand": "cold",
            "garmi": "hot"
        }
        
        # Reverse mapping for English to Hindi responses
        self.english_to_hindi_responses = {
            "Hello": "नमस्ते",
            "Thank you": "धन्यवाद", 
            "You're welcome": "कोई बात नहीं",
            "Good": "अच्छा",
            "Okay": "ठीक है",
            "Yes": "हाँ",
            "No": "नहीं",
            "Sorry": "माफ़ करें",
            "Please wait": "कृपया प्रतीक्षा करें",
            "Done": "हो गया",
            "Opening": "खोल रहा हूँ",
            "Searching": "खोज रहा हूँ",
            "Playing": "चला रहा हूँ"
        }
        
        print("🌐 Language system initialized with Hindi support")
    
    def detect_language(self, text: str) -> str:
        """
        Detect language of input text.
        Returns: 'hi' for Hindi, 'en' for English, or current language as fallback
        """
        if not text or not text.strip():
            return self.current_language
        
        try:
            # Check for Devanagari script (Hindi)
            if self._contains_devanagari(text):
                print(f"[Language] Devanagari script detected → Hindi")
                return "hi"
            
            # Check for Hindi words in Roman script
            if self._contains_hindi_words(text):
                print(f"[Language] Hindi words detected → Hindi")
                return "hi"
            
            # Use langdetect for more sophisticated detection
            detected = detect(text)
            
            if detected in self.supported_languages:
                print(f"[Language] Detected: {detected}")
                return detected
            else:
                print(f"[Language] Unsupported language {detected} → fallback to {self.current_language}")
                return self.current_language
                
        except LangDetectException:
            print(f"[Language] Detection failed → fallback to {self.current_language}")
            return self.current_language
    
    def _contains_devanagari(self, text: str) -> bool:
        """Check if text contains Devanagari script characters"""
        for char in text:
            if '\u0900' <= char <= '\u097F':  # Devanagari Unicode range
                return True
        return False
    
    def _contains_hindi_words(self, text: str) -> bool:
        """Check if text contains common Hindi words in Roman script"""
        text_lower = text.lower()
        hindi_indicators = [
            "karo", "kar", "kya", "hai", "hoon", "hun", "mein", "main",
            "aap", "tum", "yeh", "woh", "iska", "uska", "kaise", "kahan",
            "kyun", "kab", "kitna", "kitne", "chalao", "chala", "kholo",
            "khole", "dhundo", "dhundho", "gaana", "paani", "khana"
        ]
        
        words = text_lower.split()
        for word in words:
            if word in hindi_indicators:
                return True
        return False
    
    def translate_hindi_command(self, text: str) -> str:
        """
        Translate Hindi command to English using dictionary mapping.
        Falls back to Google Translate if available.
        """
        if not text:
            return text
        
        print(f"[Language] Translating Hindi command: '{text}'")
        
        # First try dictionary translation
        translated = self._dictionary_translate(text)
        
        if translated != text:
            print(f"[Language] Dictionary translation: '{text}' → '{translated}'")
            return translated
        
        # Try Google Translate as fallback
        google_translated = self._google_translate(text)
        if google_translated and google_translated != text:
            print(f"[Language] Google translation: '{text}' → '{google_translated}'")
            return google_translated
        
        print(f"[Language] No translation found, using original: '{text}'")
        return text
    
    def _dictionary_translate(self, text: str) -> str:
        """Translate using local dictionary"""
        text_lower = text.lower().strip()
        
        # Direct mapping
        if text_lower in self.hindi_commands:
            return self.hindi_commands[text_lower]
        
        # Word-by-word translation for compound commands
        words = text_lower.split()
        translated_words = []
        
        for word in words:
            if word in self.hindi_commands:
                translated_words.append(self.hindi_commands[word])
            else:
                translated_words.append(word)
        
        translated = " ".join(translated_words)
        
        # Clean up common patterns
        translated = self._clean_translation(translated)
        
        return translated if translated != text_lower else text
    
    def _clean_translation(self, text: str) -> str:
        """Clean up translated text"""
        # Common cleanup patterns
        cleanups = {
            "open youtube": "open youtube",
            "play video": "play video", 
            "scroll down": "scroll down",
            "scroll up": "scroll up",
            "search google": "search",
            "first video": "first video",
            "second video": "second video"
        }
        
        text_lower = text.lower()
        for pattern, replacement in cleanups.items():
            if pattern in text_lower:
                return replacement
        
        return text
    
    def _google_translate(self, text: str, target_lang: str = "en") -> Optional[str]:
        """
        Translate using simple web-based translation (fallback only).
        Returns None if translation fails.
        """
        try:
            # Simple web-based translation using requests
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                'client': 'gtx',
                'sl': 'hi',
                'tl': target_lang,
                'dt': 't',
                'q': text
            }
            
            response = requests.get(url, params=params, timeout=3)
            if response.status_code == 200:
                result = response.json()
                if result and len(result) > 0 and len(result[0]) > 0:
                    translated = result[0][0][0]
                    return translated.strip()
            
        except Exception as e:
            print(f"[Language] Web translation error: {e}")
        
        return None
    
    def switch_language(self, new_language: str) -> Tuple[bool, str]:
        """
        Switch current language.
        Returns: (success, feedback_message)
        """
        if new_language not in self.supported_languages:
            return False, f"Language {new_language} not supported"
        
        if self.current_language == new_language:
            return True, f"Already in {new_language} mode"
        
        old_language = self.current_language
        self.current_language = new_language
        
        print(f"[Language] Switched from {old_language} to {new_language}")
        
        if new_language == "hi":
            return True, "अब मैं हिंदी में सुन रही हूँ।"
        else:
            return True, "Back to English mode."
    
    def process_command(self, text: str) -> Tuple[str, str, bool]:
        """
        Process voice command with language detection and translation.
        Returns: (processed_command, detected_language, language_changed)
        """
        if not text:
            return text, self.current_language, False
        
        # Detect language
        detected_lang = self.detect_language(text)
        language_changed = detected_lang != self.current_language
        
        # Switch language if needed
        if language_changed:
            success, message = self.switch_language(detected_lang)
            if success:
                print(f"[Language] Auto-switched to {detected_lang}: {message}")
        
        # Translate if Hindi
        processed_text = text
        if detected_lang == "hi":
            processed_text = self.translate_hindi_command(text)
        
        return processed_text, detected_lang, language_changed
    
    def get_response_in_language(self, english_response: str, target_language: str = None) -> str:
        """
        Get response in appropriate language.
        """
        if target_language is None:
            target_language = self.current_language
        
        if target_language == "hi":
            # Try to translate response to Hindi
            for eng_phrase, hindi_phrase in self.english_to_hindi_responses.items():
                if eng_phrase.lower() in english_response.lower():
                    return english_response.replace(eng_phrase, hindi_phrase)
            
            # For longer responses, use Google Translate
            translated = self._google_translate(english_response, "hi")
            if translated:
                return translated
        
        return english_response
    
    def get_status(self) -> Dict:
        """Get current language system status"""
        return {
            "current_language": self.current_language,
            "supported_languages": self.supported_languages,
            "dictionary_size": len(self.hindi_commands)
        }
