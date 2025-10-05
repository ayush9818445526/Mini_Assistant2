#!/usr/bin/env python3
"""
TARA Advanced Features Module
Additional capabilities for enhanced functionality
"""

import schedule
import time
import threading
from datetime import datetime, timedelta
import pickle
import os
import json

# Face recognition is optional
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("⚠️ Face recognition not available - install cmake and dlib for this feature")

class TaraAdvanced:
    def __init__(self, tara_instance):
        self.tara = tara_instance
        self.face_encodings = {}
        self.load_face_data()
        self.setup_scheduler()
        
    def load_face_data(self):
        """Load saved face recognition data"""
        try:
            if os.path.exists("face_data.pkl"):
                with open("face_data.pkl", "rb") as f:
                    self.face_encodings = pickle.load(f)
                print("✅ Face recognition data loaded")
        except Exception as e:
            print(f"❌ Error loading face data: {e}")
            
    def save_face_data(self):
        """Save face recognition data"""
        try:
            with open("face_data.pkl", "wb") as f:
                pickle.dump(self.face_encodings, f)
            print("✅ Face recognition data saved")
        except Exception as e:
            print(f"❌ Error saving face data: {e}")
            
    def register_face(self, name, image_path=None):
        """Register a new face for recognition"""
        if not FACE_RECOGNITION_AVAILABLE:
            self.tara.speak("Face recognition is not available. Please install cmake and dlib first.")
            return False
            
        try:
            if image_path:
                # Load image from file
                image = face_recognition.load_image_file(image_path)
            else:
                # Capture from webcam
                import cv2
                cap = cv2.VideoCapture(0)
                ret, frame = cap.read()
                cap.release()
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
            # Get face encoding
            face_encodings = face_recognition.face_encodings(image)
            
            if face_encodings:
                self.face_encodings[name] = face_encodings[0]
                self.save_face_data()
                self.tara.speak(f"Face registered for {name}!")
                return True
            else:
                self.tara.speak("No face detected. Please try again.")
                return False
                
        except Exception as e:
            print(f"❌ Face registration error: {e}")
            self.tara.speak("Sorry, I couldn't register the face.")
            return False
            
    def recognize_face(self):
        """Recognize face from webcam"""
        if not FACE_RECOGNITION_AVAILABLE:
            return None
            
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return None
                
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(
                    list(self.face_encodings.values()), 
                    face_encoding,
                    tolerance=0.6
                )
                
                if True in matches:
                    match_index = matches.index(True)
                    name = list(self.face_encodings.keys())[match_index]
                    return name
                    
            return "Unknown"
            
        except Exception as e:
            print(f"❌ Face recognition error: {e}")
            return None
            
    def setup_scheduler(self):
        """Setup scheduling system"""
        # Daily wake up reminder
        schedule.every().day.at("05:00").do(self.wake_up_reminder)
        
        # Hourly health reminders
        schedule.every().hour.do(self.health_reminder)
        
        # Start scheduler thread
        scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        scheduler_thread.start()
        
    def run_scheduler(self):
        """Run the scheduler in background"""
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    def wake_up_reminder(self):
        """5 AM wake up reminder"""
        wake_messages = [
            f"{self.tara.owner}… 5:00 baj gaye. Ab sapne dekhna band karo aur unhe poora karne ka waqt hai.",
            f"Good morning {self.tara.owner}! Time to rise and shine. The world is waiting for you!",
            f"Wake up sleepyhead! It's 5 AM and time to conquer the day!",
            f"{self.tara.owner}, morning ho gayi! Let's make today amazing!"
        ]
        
        import random
        message = random.choice(wake_messages)
        self.tara.speak(message)
        
    def health_reminder(self):
        """Hourly health reminders"""
        current_hour = datetime.now().hour
        
        if 9 <= current_hour <= 21:  # Only during active hours
            reminders = [
                "Time to drink some water! Stay hydrated.",
                "Take a 2-minute break and stretch your body.",
                "Blink your eyes and look away from the screen for a moment.",
                "Deep breath in... and out. You're doing great!",
                "Remember to maintain good posture. Sit up straight!"
            ]
            
            import random
            reminder = random.choice(reminders)
            self.tara.speak(reminder)
            
    def set_custom_reminder(self, time_str, message):
        """Set a custom reminder"""
        try:
            # Parse time string (e.g., "14:30" or "2:30 PM")
            if ":" in time_str:
                schedule.every().day.at(time_str).do(
                    lambda: self.tara.speak(f"Reminder: {message}")
                )
                self.tara.speak(f"Reminder set for {time_str}: {message}")
                return True
        except Exception as e:
            self.tara.speak("Sorry, I couldn't set that reminder. Please check the time format.")
            return False
            
    def get_system_stats(self):
        """Get system performance statistics"""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            stats = f"""
            System Performance:
            CPU Usage: {cpu_percent}%
            Memory Usage: {memory_percent}%
            Disk Usage: {disk_percent:.1f}%
            """
            
            self.tara.speak(f"CPU usage is {cpu_percent}%, Memory usage is {memory_percent}%, and disk usage is {disk_percent:.1f}%")
            return stats
            
        except Exception as e:
            self.tara.speak("Sorry, I couldn't get system statistics right now.")
            return None
            
    def smart_home_control(self, device, action):
        """Control smart home devices (placeholder for future integration)"""
        # This can be extended to control actual smart home devices
        smart_responses = {
            "lights": {
                "on": "Turning on the lights for you!",
                "off": "Turning off the lights. Sweet dreams!",
                "dim": "Dimming the lights to a comfortable level."
            },
            "ac": {
                "on": "Turning on the air conditioning.",
                "off": "Turning off the air conditioning.",
                "cool": "Setting AC to cooling mode."
            },
            "music": {
                "play": "Playing your favorite playlist!",
                "stop": "Stopping the music.",
                "next": "Skipping to the next song."
            }
        }
        
        if device in smart_responses and action in smart_responses[device]:
            response = smart_responses[device][action]
            self.tara.speak(response)
            # Here you would integrate with actual smart home APIs
            return True
        else:
            self.tara.speak(f"Sorry, I don't know how to {action} the {device}.")
            return False
            
    def learning_mode(self, user_input, context="general"):
        """Learn from user interactions to improve responses"""
        # Store learning data for future improvements
        learning_data = {
            "timestamp": datetime.now().isoformat(),
            "input": user_input,
            "context": context,
            "user": self.tara.owner
        }
        
        # Save to learning file
        try:
            learning_file = "tara_learning.json"
            if os.path.exists(learning_file):
                with open(learning_file, "r") as f:
                    data = json.load(f)
            else:
                data = []
                
            data.append(learning_data)
            
            with open(learning_file, "w") as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"❌ Learning mode error: {e}")
            
    def emotional_responses(self, emotion_detected):
        """Respond based on detected emotion"""
        emotional_responses = {
            "happy": [
                "I love seeing you happy! Your smile brightens my day too!",
                "You're glowing today! What's making you so cheerful?",
                "Your happiness is contagious! Keep spreading those good vibes!"
            ],
            "sad": [
                "I'm here for you. Want to talk about what's bothering you?",
                "It's okay to feel sad sometimes. I'm here to listen.",
                "Remember, tough times don't last, but tough people do. You've got this!"
            ],
            "stressed": [
                "Take a deep breath with me. In... and out. You're stronger than you think.",
                "Let's take a break. How about some calming music or a short walk?",
                "Stress is temporary, but your resilience is permanent. You'll get through this."
            ],
            "excited": [
                "Your excitement is infectious! Tell me what's got you so pumped!",
                "I love your energy! What amazing thing is happening?",
                "Yes! This enthusiasm is exactly what I love to see!"
            ]
        }
        
        if emotion_detected in emotional_responses:
            import random
            response = random.choice(emotional_responses[emotion_detected])
            self.tara.speak(response)
            return response
        else:
            return "I'm here with you, whatever you're feeling."
