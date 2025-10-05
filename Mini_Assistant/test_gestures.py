#!/usr/bin/env python3
"""
Simple Gesture and Cursor Control Test
Clean, single file for testing all TARA gestures
"""

import time
import threading
from dual_hand_gesture_control_fixed import DualHandGestureController
from screen_control import ScreenController


class GestureTester:
    """Simple gesture tester with console feedback"""
    
    def __init__(self):
        self.screen_controller = ScreenController()
        self.gesture_controller = DualHandGestureController(self.screen_controller)
        self.running = False
        
        # Stats
        self.gesture_count = 0
        self.cursor_activations = 0
        self.start_time = time.time()
        
        print("🎮 TARA Gesture Tester")
        print("=" * 40)
    
    def start_test(self):
        """Start gesture testing"""
        try:
            print("\n🚀 Starting gesture controller...")
            if not self.gesture_controller.enable():
                print("❌ Failed to start gesture controller")
                return
            
            self.running = True
            self._show_instructions()
            
            # Monitor gestures
            print("\n📊 LIVE GESTURE MONITORING:")
            print("-" * 40)
            
            try:
                while self.running:
                    status = self.gesture_controller.get_status()
                    self._show_status(status)
                    time.sleep(0.3)
                    
            except KeyboardInterrupt:
                print("\n\n👋 Stopping test...")
                self.running = False
            
            self.gesture_controller.stop()
            self._show_summary()
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def _show_instructions(self):
        """Show testing instructions"""
        print("\n🖐️ SINGLE HAND GESTURES:")
        print("  ✋ Open Palm (4-5 fingers) → Scroll Down")
        print("  ✊ Closed Fist (0-1 fingers) → Scroll Up")
        print("  👉 Pointing (index only) → Click Center")
        print("  ✌️ Peace Sign (index+middle) → Click Center")
        print("  👍 Thumbs Up → Play/Pause")
        
        print("\n🖐️🖐️ DUAL HAND MODE:")
        print("  🖐️🖐️ Both hands (8+ fingers) → Cursor Control")
        print("  👆👆 Pinch 2 fingers together → Click at Cursor")
        
        print("\n💡 TIPS:")
        print("  • Make clear, distinct gestures")
        print("  • Hold gestures for 1-2 seconds")
        print("  • For cursor: show both hands with fingers extended")
        print("  • For cursor click: pinch index+middle or thumb+index")
        
        print("\n🎯 Press Ctrl+C to stop testing")
    
    def _show_status(self, status):
        """Show current status"""
        try:
            timestamp = time.strftime("%H:%M:%S")
            
            if status.get('cursor_active'):
                self.cursor_activations += 1
                pos = status.get('cursor_position')
                if pos and len(pos) >= 2:
                    print(f"[{timestamp}] 🖱️  CURSOR MODE - Position: ({pos[0]}, {pos[1]})")
                else:
                    print(f"[{timestamp}] 🖱️  CURSOR MODE - Initializing...")
                
            elif status.get('last_gesture'):
                self.gesture_count += 1
                gesture = status['last_gesture'].replace('_', ' ').title()
                print(f"[{timestamp}] 🤲 GESTURE: {gesture}")
                
            else:
                # Show waiting status less frequently
                if int(time.time()) % 5 == 0:
                    elapsed = int(time.time() - self.start_time)
                    print(f"[{timestamp}] ⏸️  Waiting for gestures... ({elapsed}s)")
                    
        except Exception as e:
            print(f"[{timestamp}] ❌ Status error: {e}")
    
    def _show_summary(self):
        """Show test summary"""
        elapsed = int(time.time() - self.start_time)
        
        print("\n" + "=" * 40)
        print("📊 TEST SUMMARY")
        print("=" * 40)
        print(f"⏱️  Runtime: {elapsed} seconds")
        print(f"🤲 Total Gestures: {self.gesture_count}")
        print(f"🖱️  Cursor Activations: {self.cursor_activations}")
        
        if elapsed > 0:
            rate = (self.gesture_count * 60) // elapsed
            print(f"📈 Gestures per minute: {rate}")
        
        print("=" * 40)
        print("✅ Test completed!")


def main():
    """Main function"""
    print("🎮 TARA Gesture and Cursor Control Test")
    print("=" * 50)
    
    print("\n🎯 This test will:")
    print("• Start the dual-hand gesture controller")
    print("• Monitor all gestures in real-time")
    print("• Show cursor position when active")
    print("• Track gesture statistics")
    
    choice = input("\n🚀 Start gesture test? (y/n): ").lower()
    if choice != 'y':
        print("👋 Test cancelled")
        return
    
    try:
        tester = GestureTester()
        tester.start_test()
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
