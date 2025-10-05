#!/usr/bin/env python3
"""
TARA Voice Recognition Security System
Voice pattern recognition to authenticate the owner
"""

import numpy as np
import pickle
import os
from resemblyzer import preprocess_wav, VoiceEncoder
import speech_recognition as sr
from scipy.spatial.distance import cosine
from config import OWNER_NAME

class VoiceAuthentication:
    def __init__(self):
        self.encoder = VoiceEncoder()
        self.owner_voice_print = None
        self.similarity_threshold = 0.7  # Adjust based on testing
        self.voice_samples_file = "owner_voice_samples.pkl"
        self.load_owner_voice_print()
        
    def load_owner_voice_print(self):
        """Load saved owner voice print"""
        try:
            if os.path.exists(self.voice_samples_file):
                with open(self.voice_samples_file, "rb") as f:
                    self.owner_voice_print = pickle.load(f)
                print("✅ Owner voice print loaded")
                return True
        except Exception as e:
            print(f"❌ Error loading voice print: {e}")
        return False
        
    def save_owner_voice_print(self):
        """Save owner voice print"""
        try:
            with open(self.voice_samples_file, "wb") as f:
                pickle.dump(self.owner_voice_print, f)
            print("✅ Owner voice print saved")
            return True
        except Exception as e:
            print(f"❌ Error saving voice print: {e}")
            return False
            
    def register_owner_voice(self, audio_samples):
        """Register owner's voice from multiple audio samples"""
        try:
            embeddings = []
            
            for audio_data in audio_samples:
                # Preprocess audio
                wav = preprocess_wav(audio_data)
                # Generate voice embedding
                embedding = self.encoder.embed_utterance(wav)
                embeddings.append(embedding)
                
            # Average the embeddings for better accuracy
            self.owner_voice_print = np.mean(embeddings, axis=0)
            self.save_owner_voice_print()
            
            print(f"✅ {OWNER_NAME}'s voice registered successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Voice registration error: {e}")
            return False
            
    def verify_voice(self, audio_data):
        """Verify if the voice matches the owner"""
        if self.owner_voice_print is None:
            print("⚠️ Owner voice not registered. Allowing access.")
            return True  # Allow access if no voice print registered
            
        try:
            # Preprocess audio
            wav = preprocess_wav(audio_data)
            # Generate embedding for current voice
            current_embedding = self.encoder.embed_utterance(wav)
            
            # Calculate similarity
            similarity = 1 - cosine(self.owner_voice_print, current_embedding)
            
            print(f"🔍 Voice similarity: {similarity:.3f} (threshold: {self.similarity_threshold})")
            
            return similarity >= self.similarity_threshold
            
        except Exception as e:
            print(f"❌ Voice verification error: {e}")
            return False  # Deny access on error
            
    def is_owner_voice(self, recognizer, audio):
        """Check if the current speaker is the owner"""
        try:
            # Convert speech_recognition audio to numpy array
            audio_data = np.frombuffer(audio.get_raw_data(), dtype=np.int16).astype(np.float32)
            audio_data = audio_data / 32768.0  # Normalize to [-1, 1]
            
            return self.verify_voice(audio_data)
            
        except Exception as e:
            print(f"❌ Owner voice check error: {e}")
            return False
            
    def setup_owner_voice_registration(self):
        """Interactive setup for owner voice registration"""
        print(f"\n🎤 Voice Registration Setup for {OWNER_NAME}")
        print("=" * 50)
        print("Please say the following phrases clearly:")
        
        phrases = [
            "Hey TARA, this is my voice",
            "TARA, remember my voice pattern",
            "Hello TARA, I am your creator",
            "TARA, activate voice recognition",
            "This is my authentic voice sample"
        ]
        
        audio_samples = []
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()
        
        # Adjust for ambient noise
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source)
            
        for i, phrase in enumerate(phrases, 1):
            print(f"\n{i}. Please say: '{phrase}'")
            print("Press Enter when ready, then speak...")
            input()
            
            try:
                with microphone as source:
                    print("🎧 Listening...")
                    audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)
                    
                # Convert to numpy array
                audio_data = np.frombuffer(audio.get_raw_data(), dtype=np.int16).astype(np.float32)
                audio_data = audio_data / 32768.0
                
                audio_samples.append(audio_data)
                print("✅ Sample recorded!")
                
            except Exception as e:
                print(f"❌ Recording error: {e}")
                print("Skipping this sample...")
                
        if audio_samples:
            print(f"\n🔄 Processing {len(audio_samples)} voice samples...")
            if self.register_owner_voice(audio_samples):
                print("🎉 Voice registration complete!")
                return True
        
        print("❌ Voice registration failed!")
        return False

# Simple fallback voice authentication using basic audio features
class SimpleVoiceAuth:
    def __init__(self):
        self.owner_audio_features = None
        self.features_file = "simple_voice_features.pkl"
        self.load_features()
        
    def extract_simple_features(self, audio_data):
        """Extract simple audio features for comparison"""
        try:
            # Basic audio features
            features = {
                'mean': np.mean(audio_data),
                'std': np.std(audio_data),
                'max': np.max(audio_data),
                'min': np.min(audio_data),
                'energy': np.sum(audio_data ** 2)
            }
            return features
        except:
            return None
            
    def register_simple_voice(self, audio_samples):
        """Register voice using simple features"""
        try:
            all_features = []
            for audio in audio_samples:
                features = self.extract_simple_features(audio)
                if features:
                    all_features.append(features)
                    
            if all_features:
                # Average the features
                self.owner_audio_features = {}
                for key in all_features[0].keys():
                    self.owner_audio_features[key] = np.mean([f[key] for f in all_features])
                    
                self.save_features()
                return True
        except Exception as e:
            print(f"❌ Simple voice registration error: {e}")
        return False
        
    def verify_simple_voice(self, audio_data):
        """Verify voice using simple features"""
        if not self.owner_audio_features:
            return True  # Allow if no registration
            
        try:
            current_features = self.extract_simple_features(audio_data)
            if not current_features:
                return False
                
            # Simple similarity check
            similarity_score = 0
            for key in self.owner_audio_features.keys():
                diff = abs(current_features[key] - self.owner_audio_features[key])
                max_val = max(abs(current_features[key]), abs(self.owner_audio_features[key]))
                if max_val > 0:
                    similarity_score += 1 - (diff / max_val)
                    
            avg_similarity = similarity_score / len(self.owner_audio_features)
            return avg_similarity > 0.6  # Threshold
            
        except Exception as e:
            print(f"❌ Simple voice verification error: {e}")
            return False
            
    def load_features(self):
        """Load saved features"""
        try:
            if os.path.exists(self.features_file):
                with open(self.features_file, "rb") as f:
                    self.owner_audio_features = pickle.load(f)
        except:
            pass
            
    def save_features(self):
        """Save features"""
        try:
            with open(self.features_file, "wb") as f:
                pickle.dump(self.owner_audio_features, f)
        except:
            pass

# Test the voice authentication system
if __name__ == "__main__":
    print("🧪 Testing Voice Authentication System")
    
    try:
        # Try advanced voice recognition first
        voice_auth = VoiceAuthentication()
        print("✅ Advanced voice recognition available")
    except Exception as e:
        print(f"⚠️ Advanced voice recognition not available: {e}")
        print("Using simple voice authentication...")
        voice_auth = SimpleVoiceAuth()
        
    # Interactive setup
    if hasattr(voice_auth, 'setup_owner_voice_registration'):
        voice_auth.setup_owner_voice_registration()
    else:
        print("Simple voice authentication ready")
