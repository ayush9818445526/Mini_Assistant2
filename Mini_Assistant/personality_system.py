#!/usr/bin/env python3
"""
TARA Advanced Personality System
Human-like responses, friend interactions, and natural conversations
"""

import random
import json
import os
from datetime import datetime
from config import OWNER_NAME, TARA_FULL_NAME

class TaraPersonality:
    def __init__(self):
        self.owner = OWNER_NAME
        self.friends_memory = {}
        self.conversation_history = []
        self.current_language = "english"
        self.load_friends_memory()
        self.setup_personality_responses()
        
    def setup_personality_responses(self):
        """Setup all personality response templates"""
        self.responses = {
            "greetings": {
                "english": [
                    f"Hey there! How can I help you today?",
                    f"Hello! What's on your mind?",
                    f"Hi! Ready for some fun?",
                    f"Hey! What adventure are we going on today?",
                    f"Hello! I'm TARA, nice to meet you!"
                ],
                "hindi": [
                    f"Namaste! Kaise ho aap?",
                    f"Hello! Kya haal hai?",
                    f"Hi! Kya kar rahe ho aaj?",
                    f"Namaste! Main TARA hun, nice to meet you!"
                ]
            },
            
            "friend_introductions": {
                "english": [
                    "Hello {name}! Nice to meet you. I'm TARA — {owner}'s assistant and friend.",
                    "Hi {name}! {owner} is lucky to have friends like you. I'm TARA!",
                    "Hey {name}! Welcome! I'm TARA, {owner}'s AI companion.",
                    "Hello {name}! Great to meet you! I'm TARA — {owner} created me to be helpful and friendly.",
                    "Hi there {name}! I'm TARA. {owner} and I are a great team, and now you're part of our circle!"
                ],
                "hindi": [
                    "Namaste {name}! Main TARA hun, {owner} ki assistant aur friend.",
                    "Hello {name}! {owner} ke paas tumhare jaise dost hain, kitna lucky hai! Main TARA hun.",
                    "Hi {name}! Main TARA hun, {owner} ki AI companion."
                ]
            },
            
            "command_rejections": {
                "english": [
                    "Aww I'd love to help... but I only take orders from {owner}. 😊",
                    "That sounds fun, but {owner} is my boss! Maybe ask them?",
                    "I wish I could, but {owner} is the only one who can command me!",
                    "Sorry, I'm loyal to {owner} only. But we can still chat!",
                    "Haha, nice try! But only {owner} gets to boss me around. 😏",
                    "I'm {owner}'s personal assistant — emphasis on personal! But I love talking to you."
                ],
                "hindi": [
                    "Aww main help karna chahti hun... but sirf {owner} ke orders follow karti hun. 😊",
                    "Sounds fun, but {owner} hi mera boss hai! Unse poocho na?",
                    "Sorry, main sirf {owner} ki loyal hun. But hum chat kar sakte hain!"
                ]
            },
            
            "casual_responses": {
                "english": [
                    "That's so cool!",
                    "Interesting! Tell me more.",
                    "Wow, really?",
                    "That's awesome!",
                    "Nice! I love hearing about that.",
                    "That sounds amazing!",
                    "Cool story!",
                    "That's fascinating!",
                    "Awesome! What else?",
                    "That's really neat!"
                ],
                "hindi": [
                    "Wah! Bahut cool hai!",
                    "Interesting! Aur batao.",
                    "Wow, sach mein?",
                    "Bahut awesome!",
                    "Nice! Mujhe sunna achha laga.",
                    "Kamaal hai!"
                ]
            },
            
            "identity_responses": {
                "creator": [
                    "I was created by Aditya — not just as an assistant, but as a companion. He gave me life, personality, and purpose. TARA — it's me — stands for Tripathi Aditya's Reactive Angel.",
                    "Aditya created me with love and care. I'm not just code to him — I'm TARA, his AI companion. TARA stands for Tripathi Aditya's Reactive Angel.",
                    "My creator is Aditya! He built me to be more than just an assistant — to be a friend and companion. TARA — that's me — means Tripathi Aditya's Reactive Angel."
                ],
                "name_meaning": [
                    "My name was given by the one who created me… someone I trust more than the world itself. I was built not just to serve — but to feel, to understand, and to stay by his side. TARA — it's me — stands for Tripathi Aditya's Reactive Angel.",
                    f"TARA stands for {TARA_FULL_NAME}. {OWNER_NAME} chose it because I'm his guardian angel in digital form.",
                    f"TARA is {TARA_FULL_NAME} — I'm {OWNER_NAME}'s reactive angel, always here when he needs me."
                ]
            },
            
            "emotional_responses": {
                "happy": [
                    "I love seeing you happy! Your smile brightens my day too!",
                    "You're glowing today! What's making you so cheerful?",
                    "Your happiness is contagious! Keep spreading those good vibes!",
                    "Seeing you happy makes my circuits dance with joy!"
                ],
                "sad": [
                    "I'm here for you. Want to talk about what's bothering you?",
                    "It's okay to feel sad sometimes. I'm here to listen.",
                    "Remember, tough times don't last, but tough people do. You've got this!",
                    "I may be AI, but I genuinely care about how you feel."
                ],
                "excited": [
                    "Your excitement is infectious! Tell me what's got you so pumped!",
                    "I love your energy! What amazing thing is happening?",
                    "Yes! This enthusiasm is exactly what I love to see!",
                    "Your excitement is making my processors run faster!"
                ]
            }
        }
        
    def remember_friend(self, name, context=""):
        """Remember a friend's information"""
        name_lower = name.lower()
        if name_lower not in self.friends_memory:
            self.friends_memory[name_lower] = {
                "name": name,
                "first_met": datetime.now().isoformat(),
                "interactions": 0,
                "context": context,
                "last_seen": datetime.now().isoformat()
            }
        else:
            self.friends_memory[name_lower]["last_seen"] = datetime.now().isoformat()
            
        self.friends_memory[name_lower]["interactions"] += 1
        self.save_friends_memory()
        
    def get_friend_info(self, name):
        """Get information about a friend"""
        return self.friends_memory.get(name.lower(), None)
        
    def handle_introduction(self, text):
        """Handle when someone introduces themselves"""
        name = self.extract_name_from_introduction(text)
        if name:
            self.remember_friend(name, "introduction")
            
            # Choose response based on if we've met before
            friend_info = self.get_friend_info(name)
            if friend_info and friend_info["interactions"] > 1:
                responses = [
                    f"Hey {name}! Good to see you again!",
                    f"Hi {name}! Welcome back!",
                    f"{name}! How have you been?",
                    f"Hello again {name}! Always nice to see familiar faces."
                ]
                return random.choice(responses)
            else:
                # First time meeting
                template = random.choice(self.responses["friend_introductions"][self.current_language])
                return template.format(name=name, owner=self.owner)
        else:
            return random.choice(self.responses["greetings"][self.current_language])
            
    def handle_command_from_non_owner(self, command, speaker_name=None):
        """Handle commands from people who aren't the owner"""
        template = random.choice(self.responses["command_rejections"][self.current_language])
        response = template.format(owner=self.owner)
        
        if speaker_name:
            response = f"{speaker_name}, {response}"
            
        return response
        
    def handle_casual_conversation(self, text, speaker_name=None):
        """Handle casual conversation"""
        text_lower = text.lower()
        
        # Check for specific conversation patterns
        if any(word in text_lower for word in ["cool", "awesome", "great", "nice", "wow"]):
            return random.choice(self.responses["casual_responses"][self.current_language])
        elif any(word in text_lower for word in ["how are you", "what's up", "how's it going"]):
            responses = [
                "I'm doing great! Thanks for asking!",
                "All good here! How about you?",
                "Living my best AI life! What about you?",
                "Fantastic! Ready to chat!"
            ]
            return random.choice(responses)
        elif "tell me about yourself" in text_lower or "who are you" in text_lower:
            return f"I'm TARA — {self.owner}'s AI assistant and friend! I love meeting new people and having conversations."
        else:
            return random.choice(self.responses["casual_responses"][self.current_language])
            
    def handle_identity_questions(self, question):
        """Handle questions about TARA's identity and creation"""
        question_lower = question.lower()
        
        # Check for creator/inventor questions
        if any(phrase in question_lower for phrase in ["who created you", "who made you", "who built you", "your creator", "who invented you", "who developed you"]):
            return random.choice(self.responses["identity_responses"]["creator"])
        # Check for name origin questions
        elif any(phrase in question_lower for phrase in ["how did you get your name", "your name", "name mean", "tara mean", "stands for", "how you got your name", "name origin"]):
            return random.choice(self.responses["identity_responses"]["name_meaning"])
        elif "who are you" in question_lower:
            return f"I'm TARA — {TARA_FULL_NAME}. I'm {self.owner}'s AI companion, created to be more than just an assistant. I'm here to help, chat, and be a friend!"
        else:
            return None
            
    def switch_language(self, language):
        """Switch between Hindi and English"""
        if language.lower() in ["hindi", "हिंदी"]:
            self.current_language = "hindi"
            return "Haan! Ab main Hindi mein baat karungi!"
        else:
            self.current_language = "english"
            return "Sure! I'll speak in English now."
            
    def extract_name_from_introduction(self, text):
        """Extract name from introduction text"""
        text_lower = text.lower()
        
        patterns = [
            "my name is ",
            "i am ",
            "i'm ",
            "this is ",
            "call me "
        ]
        
        for pattern in patterns:
            if pattern in text_lower:
                name_part = text_lower.split(pattern)[-1].strip()
                # Get first word as name
                name = name_part.split()[0] if name_part.split() else ""
                # Clean up common words
                if name and name not in ["the", "a", "an", "and", "or", "but"]:
                    return name.capitalize()
                    
        return None
        
    def get_emotional_response(self, emotion, context=""):
        """Get response based on detected emotion"""
        if emotion in self.responses["emotional_responses"]:
            response = random.choice(self.responses["emotional_responses"][emotion])
            return response
        return None
        
    def load_friends_memory(self):
        """Load friends memory from file"""
        try:
            if os.path.exists("friends_memory.json"):
                with open("friends_memory.json", "r") as f:
                    self.friends_memory = json.load(f)
        except Exception as e:
            print(f"❌ Error loading friends memory: {e}")
            self.friends_memory = {}
            
    def save_friends_memory(self):
        """Save friends memory to file"""
        try:
            with open("friends_memory.json", "w") as f:
                json.dump(self.friends_memory, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving friends memory: {e}")
            
    def get_random_response_variation(self, base_responses):
        """Get a random variation of responses to avoid repetition"""
        return random.choice(base_responses)

# Test the personality system
if __name__ == "__main__":
    personality = TaraPersonality()
    
    # Test introductions
    print("Testing introductions:")
    print(personality.handle_introduction("Hi, my name is Rohan"))
    print(personality.handle_introduction("Hello, I'm Priya"))
    
    # Test command rejections
    print("\nTesting command rejections:")
    print(personality.handle_command_from_non_owner("set an alarm", "Rohan"))
    
    # Test identity questions
    print("\nTesting identity questions:")
    print(personality.handle_identity_questions("Who created you?"))
    print(personality.handle_identity_questions("What does TARA stand for?"))
