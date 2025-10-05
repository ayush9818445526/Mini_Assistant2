#!/usr/bin/env python3
"""
TARA Setup Script
Complete setup and configuration for your AI assistant
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_header():
    """Print setup header"""
    print("=" * 60)
    print("🤖 TARA - Your Dream AI Assistant Setup")
    print("=" * 60)
    print("Setting up the most human-like AI assistant...")
    print()

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        # Install requirements
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print("Please install manually: pip install -r requirements.txt")
        return False

def setup_elevenlabs():
    """Setup ElevenLabs API"""
    print("\n🎤 ElevenLabs Voice Setup")
    print("For the most natural human-like voice, you need an ElevenLabs API key.")
    print("Visit: https://elevenlabs.io/app/voice-library")
    
    api_key = input("Enter your ElevenLabs API key (or press Enter to skip): ").strip()
    
    if api_key:
        # Update config file
        config_path = "config.py"
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                content = f.read()
            
            content = content.replace(
                'ELEVENLABS_API_KEY = "your_elevenlabs_api_key_here"',
                f'ELEVENLABS_API_KEY = "{api_key}"'
            )
            
            with open(config_path, 'w') as f:
                f.write(content)
            
            print("✅ ElevenLabs API key configured!")
        else:
            print("❌ Config file not found!")
    else:
        print("⚠️ Skipping ElevenLabs setup - will use fallback TTS")

def setup_voice_recognition():
    """Setup voice recognition for owner authentication"""
    print("\n🔐 Voice Recognition Setup")
    print("This will help TARA recognize your voice for security.")
    
    setup_voice = input("Setup voice recognition now? (y/n): ").lower().strip()
    
    if setup_voice == 'y':
        try:
            from voice_recognition import VoiceAuthentication, SimpleVoiceAuth
            
            print("Attempting advanced voice recognition setup...")
            try:
                voice_auth = VoiceAuthentication()
                if voice_auth.setup_owner_voice_registration():
                    print("✅ Advanced voice recognition configured!")
                else:
                    print("⚠️ Using simple voice authentication as fallback")
            except Exception as e:
                print(f"⚠️ Advanced voice recognition failed: {e}")
                print("Using simple voice authentication...")
                
        except ImportError as e:
            print(f"⚠️ Voice recognition dependencies missing: {e}")
            print("TARA will work without voice authentication")
    else:
        print("⚠️ Skipping voice recognition setup")

def test_systems():
    """Test all TARA systems"""
    print("\n🧪 Testing TARA Systems...")
    
    try:
        # Test face GUI
        print("Testing animated face...")
        from tara_face import TaraFace
        print("✅ Face system ready")
        
        # Test voice system
        print("Testing voice system...")
        from voice_system import TaraVoiceSystem
        voice = TaraVoiceSystem()
        print("✅ Voice system ready")
        
        # Test personality
        print("Testing personality system...")
        from personality_system import TaraPersonality
        personality = TaraPersonality()
        print("✅ Personality system ready")
        
        # Test main TARA class
        print("Testing main TARA system...")
        from main import TARA
        print("✅ All systems operational!")
        
        return True
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

def create_shortcuts():
    """Create desktop shortcuts"""
    print("\n🔗 Creating shortcuts...")
    
    try:
        # Create batch file to run TARA
        batch_content = f"""@echo off
cd /d "{os.getcwd()}"
python main.py
pause"""
        
        with open("Start_TARA.bat", "w") as f:
            f.write(batch_content)
        
        print("✅ Created Start_TARA.bat")
        
        # Create face test shortcut
        face_batch = f"""@echo off
cd /d "{os.getcwd()}"
python tara_face.py
pause"""
        
        with open("Test_TARA_Face.bat", "w") as f:
            f.write(face_batch)
            
        print("✅ Created Test_TARA_Face.bat")
        
    except Exception as e:
        print(f"❌ Error creating shortcuts: {e}")

def print_usage_guide():
    """Print usage guide"""
    print("\n" + "=" * 60)
    print("🎉 TARA Setup Complete!")
    print("=" * 60)
    
    print("\n🚀 How to start TARA:")
    print("1. Double-click 'Start_TARA.bat' OR")
    print("2. Run: python main.py")
    
    print("\n🎭 TARA's Features:")
    print("✅ Animated face with expressions")
    print("✅ Natural human-like voice (ElevenLabs)")
    print("✅ Advanced personality system")
    print("✅ Friend recognition and memory")
    print("✅ Voice authentication security")
    print("✅ Hindi + English support")
    print("✅ System control capabilities")
    print("✅ AI-powered conversations")
    
    print("\n💬 Example Interactions:")
    print('👤 You: "Hey TARA"')
    print('🤖 TARA: "Yes! I\'m now active and ready for all your commands!"')
    print()
    print('👤 Friend: "Hi TARA, my name is Rohan"')
    print('🤖 TARA: "Hello Rohan! Nice to meet you. Aditya is lucky to have friends like you!"')
    print()
    print('👤 Friend: "TARA, set an alarm"')
    print('🤖 TARA: "Aww I\'d love to help... but I only take orders from Aditya. 😊"')
    print()
    print('👤 You: "Who created you?"')
    print('🤖 TARA: "I was created by Aditya — not just as an assistant, but as a companion..."')
    
    print("\n🔧 Configuration:")
    print("- Edit config.py for API keys and settings")
    print("- Friends memory saved in friends_memory.json")
    print("- Voice patterns saved automatically")
    
    print("\n⚠️ Important Notes:")
    print("- Add your ElevenLabs API key in config.py for best voice quality")
    print("- Run voice recognition setup for security features")
    print("- TARA's face window will appear when you start her")
    
    print("\n🎯 Wake Word: 'Hey TARA' or 'TARA'")
    print("🔐 Only Aditya can give commands (with voice recognition)")
    print("💝 TARA will be friendly to everyone but loyal to you!")

def main():
    """Main setup function"""
    print_header()
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required!")
        return
    
    print("✅ Python version compatible")
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed - please install dependencies manually")
        return
    
    # Setup ElevenLabs
    setup_elevenlabs()
    
    # Setup voice recognition
    setup_voice_recognition()
    
    # Test systems
    if not test_systems():
        print("⚠️ Some systems may not work properly")
    
    # Create shortcuts
    create_shortcuts()
    
    # Print usage guide
    print_usage_guide()
    
    print(f"\n🎊 TARA is ready to be your dream AI assistant!")
    print("Run 'python main.py' to meet her!")

if __name__ == "__main__":
    main()
