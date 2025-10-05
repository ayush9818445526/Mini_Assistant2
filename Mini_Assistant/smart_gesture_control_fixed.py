import cv2
import mediapipe as mp
import threading
import time
import numpy as np
from typing import Optional, Tuple, List
import math


class SmartGestureController:
    """
    Fixed smart dual-mode gesture controller with improved pout detection
    """
    
    def __init__(self, screen_controller=None):
        self.screen_controller = screen_controller
        self.is_running = False
        self.is_enabled = False
        self.capture_thread = None
        self.cap = None
        
        # MediaPipe setup
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Gesture detection parameters
        self.last_gesture = None
        self.last_gesture_time = 0
        self.gesture_cooldown = 0.5
        self.frame_skip = 2
        self.frame_count = 0
        
        # Smart dual-mode parameters
        self.is_pout_active = False
        self.pout_start_time = 0
        self.pout_threshold = 0.2  # Reduced from 0.3 for faster activation
        self.cursor_active = False
        
        # Screen and cursor parameters
        self.screen_width = None
        self.screen_height = None
        self.camera_width = 640
        self.camera_height = 480
        self.cursor_smoothing = 0.6  # Reduced for more responsive cursor
        self.last_cursor_x = None
        self.last_cursor_y = None
        
        # Get screen dimensions
        try:
            import pyautogui
            self.screen_width, self.screen_height = pyautogui.size()
        except:
            self.screen_width, self.screen_height = 1920, 1080
        
        print("🧠 Smart Gesture Controller (Fixed) initialized")
        print("💡 Join 5 fingers together to activate cursor mode")
    
    def start(self):
        """Start gesture recognition in background thread"""
        if self.is_running:
            print("⚠️ Smart gesture control already running")
            return False
            
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("❌ Could not open webcam for gesture control")
                return False
                
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.is_running = True
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            print("✅ Smart gesture control started")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start smart gesture control: {e}")
            return False
    
    def stop(self):
        """Stop gesture recognition"""
        self.is_running = False
        self.is_enabled = False
        
        if self.cap:
            try:
                self.cap.release()
            except:
                pass
            self.cap = None
            
        if self.capture_thread:
            try:
                self.capture_thread.join(timeout=1.0)
            except:
                pass
            
        print("🛑 Smart gesture control stopped")
    
    def enable(self):
        """Enable smart dual-mode processing"""
        if not self.is_running:
            if not self.start():
                return False
        self.is_enabled = True
        print("✅ Smart dual-mode enabled!")
        print("🤲 Regular gestures: ✋ scroll down, ✊ scroll up, 👉 click, ✌️ click")
        print("🖱️ Cursor mode: Join 5 fingers together to activate cursor control")
        return True
    
    def disable(self):
        """Disable gesture processing"""
        self.is_enabled = False
        self.cursor_active = False
        self.is_pout_active = False
        print("⏸️ Smart gesture control disabled")
    
    def _capture_loop(self):
        """Main capture and processing loop"""
        print("🎥 Starting smart gesture capture loop")
        
        while self.is_running:
            try:
                if not self.cap or not self.cap.isOpened():
                    break
                    
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                
                # Skip frames for performance
                self.frame_count += 1
                if self.frame_count % self.frame_skip != 0:
                    continue
                
                if self.is_enabled:
                    self._process_smart_gestures(frame)
                
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"❌ Error in smart gesture loop: {e}")
                time.sleep(0.5)
        
        print("🏁 Smart gesture loop ended")
    
    def _process_smart_gestures(self, frame):
        """Process gestures with smart dual-mode logic"""
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            if not results.multi_hand_landmarks:
                # No hand detected - reset states
                self._reset_cursor_mode()
                return
            
            # Get hand landmarks
            hand_landmarks = results.multi_hand_landmarks[0]
            landmarks = []
            for lm in hand_landmarks.landmark:
                landmarks.append([lm.x, lm.y])
            
            # Check for pout gesture first
            is_pout = self._detect_pout_gesture(landmarks)
            
            if is_pout:
                self._handle_pout_gesture(landmarks)
            else:
                # Not pout - handle regular gestures
                self._reset_cursor_mode()
                gesture = self._detect_regular_gesture(landmarks)
                if gesture:
                    self._handle_gesture(gesture)
                    
        except Exception as e:
            print(f"❌ Error processing smart gestures: {e}")
    
    def _detect_pout_gesture(self, landmarks):
        """Improved pout gesture detection (5 fingers joined together)"""
        try:
            # Get fingertip positions
            fingertips = [
                landmarks[4],   # Thumb
                landmarks[8],   # Index
                landmarks[12],  # Middle
                landmarks[16],  # Ring
                landmarks[20]   # Pinky
            ]
            
            # Calculate center point of all fingertips
            center_x = sum(tip[0] for tip in fingertips) / 5
            center_y = sum(tip[1] for tip in fingertips) / 5
            
            # Check if all fingertips are close to center (joined together)
            distances = []
            for tip in fingertips:
                distance = math.sqrt((tip[0] - center_x)**2 + (tip[1] - center_y)**2)
                distances.append(distance)
            
            max_distance = max(distances)
            avg_distance = sum(distances) / len(distances)
            
            # More lenient pout detection
            pout_threshold = 0.08  # Increased from 0.05 for easier detection
            is_pout = max_distance < pout_threshold
            
            # Debug output for pout detection
            if max_distance < 0.12:  # Show debug when close to pout
                print(f"[Debug] Pout check - max distance: {max_distance:.3f}, threshold: {pout_threshold:.3f}, detected: {is_pout}")
            
            return is_pout
            
        except Exception as e:
            print(f"❌ Error detecting pout: {e}")
            return False
    
    def _handle_pout_gesture(self, landmarks):
        """Handle pout gesture and cursor control"""
        current_time = time.time()
        
        if not self.is_pout_active:
            # Pout just started
            self.is_pout_active = True
            self.pout_start_time = current_time
            print("👄 Pout detected - activating cursor...")
        
        # Check if pout held long enough
        pout_duration = current_time - self.pout_start_time
        
        if pout_duration >= self.pout_threshold and not self.cursor_active:
            # Activate cursor mode
            self.cursor_active = True
            print("🖱️ Cursor mode activated! Move joined fingers to control cursor")
        
        if self.cursor_active:
            # Update cursor position using center of joined fingers
            self._update_cursor_from_pout(landmarks)
    
    def _update_cursor_from_pout(self, landmarks):
        """Update cursor position based on pout gesture center"""
        try:
            # Get fingertip positions
            fingertips = [
                landmarks[4],   # Thumb
                landmarks[8],   # Index
                landmarks[12],  # Middle
                landmarks[16],  # Ring
                landmarks[20]   # Pinky
            ]
            
            # Calculate center point
            center_x = sum(tip[0] for tip in fingertips) / 5
            center_y = sum(tip[1] for tip in fingertips) / 5
            
            # Convert to screen coordinates (flipped for mirror effect)
            screen_x = int((1 - center_x) * self.screen_width)
            screen_y = int(center_y * self.screen_height)
            
            # Apply smoothing
            if self.last_cursor_x is not None and self.last_cursor_y is not None:
                screen_x = int(self.cursor_smoothing * self.last_cursor_x + (1 - self.cursor_smoothing) * screen_x)
                screen_y = int(self.cursor_smoothing * self.last_cursor_y + (1 - self.cursor_smoothing) * screen_y)
            
            # Clamp to screen boundaries
            screen_x = max(0, min(screen_x, self.screen_width - 1))
            screen_y = max(0, min(screen_y, self.screen_height - 1))
            
            # Move cursor
            import pyautogui
            pyautogui.moveTo(screen_x, screen_y)
            
            # Store position
            self.last_cursor_x = screen_x
            self.last_cursor_y = screen_y
            
            # Debug output for cursor movement
            print(f"[Debug] Cursor moved to ({screen_x}, {screen_y})")
            
        except Exception as e:
            print(f"❌ Error updating cursor from pout: {e}")
    
    def _reset_cursor_mode(self):
        """Reset cursor mode when pout is released"""
        if self.is_pout_active or self.cursor_active:
            self.is_pout_active = False
            self.cursor_active = False
            print("🤲 Back to gesture mode")
    
    def _detect_regular_gesture(self, landmarks):
        """Detect regular gestures when not in cursor mode"""
        try:
            fingers_up = self._get_fingers_up(landmarks)
            total_fingers = sum(fingers_up)
            
            gesture = None
            
            # Open Palm - 4 or 5 fingers extended (but not pout)
            if total_fingers >= 4:
                gesture = "scroll_down"
                print(f"[Debug] Open Palm - {total_fingers} fingers")
            
            # Closed Fist - 0 or 1 fingers extended
            elif total_fingers <= 1:
                gesture = "scroll_up"
                print(f"[Debug] Closed Fist - {total_fingers} fingers")
            
            # Pointing - only index finger
            elif fingers_up == [0, 1, 0, 0, 0]:
                gesture = "click"
                print(f"[Debug] Pointing gesture")
            
            # Peace sign - index + middle (FIXED)
            elif fingers_up == [0, 1, 1, 0, 0]:
                gesture = "click"
                print(f"[Debug] Peace sign - clicking!")
            
            # Alternative peace sign detection (more lenient)
            elif total_fingers == 2 and fingers_up[1] == 1 and fingers_up[2] == 1:
                gesture = "click"
                print(f"[Debug] Peace sign (alternative) - clicking!")
            
            # Thumbs up
            elif fingers_up[0] == 1 and sum(fingers_up[1:]) <= 1:
                # Check if thumb pointing up
                thumb_tip = landmarks[4]
                wrist = landmarks[0]
                if thumb_tip[1] < wrist[1] - 0.1:
                    gesture = "play_pause"
                    print(f"[Debug] Thumbs up")
            
            # Apply cooldown
            current_time = time.time()
            if gesture and (gesture != self.last_gesture or 
                          current_time - self.last_gesture_time > self.gesture_cooldown):
                self.last_gesture = gesture
                self.last_gesture_time = current_time
                return gesture
            
            return None
            
        except Exception as e:
            print(f"❌ Error detecting regular gesture: {e}")
            return None
    
    def _get_fingers_up(self, landmarks):
        """Determine which fingers are extended"""
        fingers = []
        
        # Thumb
        if landmarks[4][0] > landmarks[3][0]:
            fingers.append(1)
        else:
            fingers.append(0)
        
        # Other fingers
        finger_tips = [8, 12, 16, 20]
        finger_pips = [6, 10, 14, 18]
        
        for tip, pip in zip(finger_tips, finger_pips):
            fingers.append(1 if landmarks[tip][1] < landmarks[pip][1] else 0)
        
        return fingers
    
    def _handle_gesture(self, gesture):
        """Execute action based on detected gesture"""
        try:
            print(f"[SmartGesture] {gesture.replace('_', ' ').title()}")
            
            if gesture == "scroll_down":
                if self.screen_controller:
                    self.screen_controller.scroll_down()
                
            elif gesture == "scroll_up":
                if self.screen_controller:
                    self.screen_controller.scroll_up()
                
            elif gesture == "click":
                import pyautogui
                if self.cursor_active and self.last_cursor_x and self.last_cursor_y:
                    # Click at cursor position if cursor was active
                    pyautogui.click(self.last_cursor_x, self.last_cursor_y)
                    print(f"[SmartGesture] Click at cursor ({self.last_cursor_x}, {self.last_cursor_y})")
                else:
                    # Click at center
                    screen_width, screen_height = pyautogui.size()
                    pyautogui.click(screen_width // 2, screen_height // 2)
                    print("[SmartGesture] Click at center")
                
            elif gesture == "play_pause":
                import pyautogui
                pyautogui.press('space')
                
        except Exception as e:
            print(f"❌ Error handling gesture {gesture}: {e}")
    
    def get_status(self):
        """Get current status"""
        return {
            "running": self.is_running,
            "enabled": self.is_enabled,
            "cursor_active": self.cursor_active,
            "pout_active": self.is_pout_active,
            "last_gesture": self.last_gesture,
            "cursor_position": (self.last_cursor_x, self.last_cursor_y) if self.last_cursor_x else None
        }
