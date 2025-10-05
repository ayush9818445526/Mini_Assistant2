import asyncio
import websockets
import json
import threading
import webbrowser
import time
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging


class AvatarSystem:
    """
    3D Avatar system for TARA using WebSocket communication.
    Manages avatar window, animations, and emotional expressions.
    """
    
    def __init__(self, enable_avatar: bool = True):
        self.enable_avatar = enable_avatar
        self.websocket_server = None
        self.server_thread = None
        self.connected_clients = set()
        self.is_running = False
        self.avatar_window_opened = False
        
        # WebSocket server settings
        self.host = 'localhost'
        self.port = 8765
        
        # Current state
        self.current_emotion = 'neutral'
        self.is_speaking = False
        
        print(f"🎭 AvatarSystem initialized (enabled: {enable_avatar})")
    
    def start(self):
        """Start the avatar system"""
        if not self.enable_avatar:
            print("🎭 Avatar system disabled in config")
            return False
            
        try:
            # Start WebSocket server in background thread
            self.server_thread = threading.Thread(target=self._start_websocket_server, daemon=True)
            self.server_thread.start()
            
            # Give server time to start
            time.sleep(1)
            
            # Open avatar window
            self._open_avatar_window()
            
            print("✅ Avatar system started successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start avatar system: {e}")
            return False
    
    def stop(self):
        """Stop the avatar system"""
        self.is_running = False
        if self.websocket_server:
            self.websocket_server.close()
        print("🛑 Avatar system stopped")
    
    def _start_websocket_server(self):
        """Start WebSocket server in async event loop"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Start server
            self.is_running = True
            start_server = websockets.serve(
                self._handle_websocket_connection,
                self.host,
                self.port
            )
            
            print(f"🔌 Avatar WebSocket server starting on ws://{self.host}:{self.port}")
            loop.run_until_complete(start_server)
            loop.run_forever()
            
        except Exception as e:
            print(f"❌ WebSocket server error: {e}")
    
    async def _handle_websocket_connection(self, websocket, path):
        """Handle new WebSocket connection from avatar UI"""
        print(f"🔗 Avatar client connected from {websocket.remote_address}")
        self.connected_clients.add(websocket)
        
        try:
            # Send initial state
            await self._send_to_client(websocket, {
                'type': 'emotion',
                'emotion': self.current_emotion
            })
            
            # Keep connection alive and handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_client_message(websocket, data)
                except json.JSONDecodeError:
                    print(f"⚠️ Invalid JSON from avatar client: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Avatar client disconnected")
        except Exception as e:
            print(f"❌ Avatar WebSocket error: {e}")
        finally:
            self.connected_clients.discard(websocket)
    
    async def _handle_client_message(self, websocket, data):
        """Handle messages from avatar client"""
        message_type = data.get('type')
        
        if message_type == 'ready':
            print("[Avatar] Client ready")
        elif message_type == 'error':
            print(f"[Avatar] Client error: {data.get('message', 'Unknown error')}")
        else:
            print(f"[Avatar] Unknown message type: {message_type}")
    
    async def _send_to_client(self, websocket, data):
        """Send data to specific client"""
        try:
            await websocket.send(json.dumps(data))
        except Exception as e:
            print(f"❌ Failed to send to avatar client: {e}")
    
    def _broadcast_to_clients(self, data):
        """Broadcast data to all connected clients"""
        if not self.connected_clients:
            return
            
        # Run in background thread to avoid blocking
        def broadcast():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def send_all():
                    if self.connected_clients:
                        await asyncio.gather(
                            *[self._send_to_client(client, data) for client in self.connected_clients.copy()],
                            return_exceptions=True
                        )
                
                loop.run_until_complete(send_all())
                loop.close()
            except Exception as e:
                print(f"❌ Broadcast error: {e}")
        
        threading.Thread(target=broadcast, daemon=True).start()
    
    def _open_avatar_window(self):
        """Open avatar UI in browser window"""
        try:
            # Get path to avatar UI
            avatar_path = Path(__file__).parent / "avatar_ui" / "index.html"
            avatar_url = f"file:///{avatar_path.absolute().as_posix()}"
            
            print(f"🌐 Opening avatar window: {avatar_url}")
            
            # Try to open in a new window (works on most systems)
            webbrowser.open_new(avatar_url)
            self.avatar_window_opened = True
            
            print("[Avatar] Window opened successfully")
            
        except Exception as e:
            print(f"❌ Failed to open avatar window: {e}")
    
    # Public API methods for TARA integration
    
    def speak(self, text: str, duration: Optional[int] = None):
        """Notify avatar that TARA is speaking"""
        if not self.enable_avatar or not self.connected_clients:
            return
        
        # Estimate duration if not provided (roughly 150 words per minute)
        if duration is None:
            word_count = len(text.split())
            duration = max(1000, int((word_count / 150) * 60 * 1000))  # Convert to milliseconds
        
        print(f"[Avatar] Speaking: {text[:50]}{'...' if len(text) > 50 else ''}")
        
        self._broadcast_to_clients({
            'type': 'speak',
            'text': text,
            'duration': duration
        })
        
        self.is_speaking = True
    
    def stop_speaking(self):
        """Notify avatar to stop speaking animation"""
        if not self.enable_avatar or not self.connected_clients:
            return
        
        print("[Avatar] Stopped speaking")
        
        self._broadcast_to_clients({
            'type': 'stop_speaking'
        })
        
        self.is_speaking = False
    
    def set_emotion(self, emotion: str):
        """Set avatar facial expression"""
        if not self.enable_avatar or not self.connected_clients:
            return
        
        valid_emotions = ['neutral', 'happy', 'thinking', 'surprised', 'sad', 'excited']
        if emotion not in valid_emotions:
            print(f"⚠️ Invalid emotion: {emotion}. Valid: {valid_emotions}")
            return
        
        if self.current_emotion == emotion:
            return  # No change needed
        
        print(f"[Avatar] Expression changed: {emotion}")
        self.current_emotion = emotion
        
        self._broadcast_to_clients({
            'type': 'emotion',
            'emotion': emotion
        })
    
    def set_action(self, action: str):
        """Update avatar status with current action"""
        if not self.enable_avatar or not self.connected_clients:
            return
        
        print(f"[Avatar] Action: {action}")
        
        self._broadcast_to_clients({
            'type': 'action',
            'action': action
        })
    
    def get_status(self) -> Dict[str, Any]:
        """Get current avatar system status"""
        return {
            'enabled': self.enable_avatar,
            'running': self.is_running,
            'connected_clients': len(self.connected_clients),
            'window_opened': self.avatar_window_opened,
            'current_emotion': self.current_emotion,
            'is_speaking': self.is_speaking
        }


# Utility functions for easy integration

def create_avatar_system(enable_avatar: bool = True) -> AvatarSystem:
    """Create and start avatar system"""
    avatar = AvatarSystem(enable_avatar)
    if enable_avatar:
        avatar.start()
    return avatar


# Emotion mapping helpers for common TARA states
class EmotionMapper:
    """Helper class to map TARA states to avatar emotions"""
    
    @staticmethod
    def get_emotion_for_event(event_type: str, success: bool = True) -> str:
        """Map event types to appropriate emotions"""
        emotion_map = {
            'search_complete': 'happy' if success else 'neutral',
            'search_start': 'thinking',
            'command_execute': 'neutral',
            'command_success': 'happy',
            'command_error': 'sad',
            'question_asked': 'thinking',
            'greeting': 'happy',
            'goodbye': 'neutral',
            'surprise': 'surprised',
            'processing': 'thinking',
            'idle': 'neutral'
        }
        
        return emotion_map.get(event_type, 'neutral')
