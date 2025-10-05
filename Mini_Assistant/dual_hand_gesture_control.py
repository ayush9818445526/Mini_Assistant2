import cv2
import mediapipe as mp
import threading
import time
import numpy as np
from typing import Optional, Tuple, List
import math


class DualHandGestureController:
    """
    Dual-hand gesture controller with 8-10 finger cursor trigger
    - Single hand: Regular gestures (scroll, click, play/pause)
    - Both hands (8-10 fingers): Cursor control mode
    """
    
    def __init__(self, screen_controller=None):
        self.screen_controller = screen_controller
        self.is_running = False
        self.is_enabled = False
        self.capture_thread = None
        self.cap = None
        
        # MediaPipe setup for dual hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,  # Track both hands
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
        
        # Dual-hand cursor parameters
        self.cursor_active = False
        self.cursor_activation_threshold = 8  # Minimum fingers for cursor mode
        self.cursor_start_time = 0
        self.cursor_hold_time = 0.2  # Hold time before activation
        
        # Screen and cursor parameters
        self.screen_width = None
        self.screen_height = None
        self.camera_width = 640
        self.camera_height = 480
        self.cursor_smoothing = 0.6
        self.last_cursor_x = None
        self.last_cursor_y = None
        
        # Get screen dimensions
        try:
            import pyautogui
            self.screen_width, self.screen_height = pyautogui.size()
        except:
            self.screen_width, self.screen_height = 1920, 1080
        
        print("🤲 Dual-Hand Gesture Controller initialized")
        print("💡 Show both hands (8-10 fingers) to activate cursor mode")
    
    def start(self):
        """Start gesture recognition in background thread"""
        if self.is_running:
            print("⚠️ Dual-hand gesture control already running")
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
            
            print("✅ Dual-hand gesture control started")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start dual-hand gesture control: {e}")
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
            
        print("🛑 Dual-hand gesture control stopped")
    
    def enable(self):
        """Enable dual-hand processing"""
        if not self.is_running:
            if not self.start():
                return False
        self.is_enabled = True
        print("✅ Dual-hand mode enabled!")
        print("🤲 Single hand: ✋ scroll down, ✊ scroll up, 👉 click, ✌️ click, 👍 play/pause")
        print("🖐️🖐️ Both hands (8-10 fingers): Cursor control mode")
        return True
    
    def disable(self):
        """Disable gesture processing"""
        self.is_enabled = False
        self.cursor_active = False
        print("⏸️ Dual-hand gesture control disabled")
    
    def _capture_loop(self):
        """Main capture and processing loop"""
        print("🎥 Starting dual-hand gesture capture loop")
        
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
                    self._process_dual_hand_gestures(frame)
                
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"❌ Error in dual-hand gesture loop: {e}")
                time.sleep(0.5)
        
        print("🏁 Dual-hand gesture loop ended")
    
    def _process_dual_hand_gestures(self, frame):
        """Process gestures with dual-hand logic"""
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            if not results.multi_hand_landmarks:
                # No hands detected - reset cursor mode
                self._reset_cursor_mode()
                return
            
            # Get all hand landmarks
            all_hands = []
            for hand_landmarks in results.multi_hand_landmarks:
                landmarks = []
                for lm in hand_landmarks.landmark:
                    landmarks.append([lm.x, lm.y])
                all_hands.append(landmarks)
            
            # Count total extended fingers across all hands
            total_fingers = self._count_total_fingers(all_hands)
            
            # Check for cursor activation (8-10 fingers)
            if total_fingers >= self.cursor_activation_threshold:
                self._handle_cursor_mode(all_hands, total_fingers)
            else:
                # Single hand gestures
                self._reset_cursor_mode()
                if len(all_hands) == 1:
                    gesture = self._detect_single_hand_gesture(all_hands[0])
                    if gesture:
                        self._handle_gesture(gesture)
                        
        except Exception as e:
            print(f"❌ Error processing dual-hand gestures: {e}")
    
    def _count_total_fingers(self, all_hands):
        """Count total extended fingers across all hands"""
        total_fingers = 0
        
        for hand_landmarks in all_hands:
            fingers_up = self._get_fingers_up(hand_landmarks)
            total_fingers += sum(fingers_up)
        
        return total_fingers
    
    def _handle_cursor_mode(self, all_hands, total_fingers):
        """Handle cursor mode when 8-10 fingers detected"""
        current_time = time.time()
        
        if not self.cursor_active:
            if self.cursor_start_time == 0:
                # Just started showing many fingers
                self.cursor_start_time = current_time
                print(f"🖐️ {total_fingers} fingers detected - hold to activate cursor...")
            
            # Check if held long enough
            hold_duration = current_time - self.cursor_start_time
            if hold_duration >= self.cursor_hold_time:
                self.cursor_active = True
                print(f"🖱️ Cursor mode activated with {total_fingers} fingers!")
                print("🖐️🖐️ Move both hands to control cursor")
        
        if self.cursor_active:
            # Update cursor position using center of all hands
            self._update_cursor_from_hands(all_hands)
    
    def _update_cursor_from_hands(self, all_hands):
        """Update cursor position based on center of both hands"""
        try:
            # Calculate center point of all fingertips from both hands
            all_fingertips = []
            
            for hand_landmarks in all_hands:
                # Get fingertips for this hand
                fingertips = [
                    hand_landmarks[4],   # Thumb
                    hand_landmarks[8],   # Index
                    hand_landmarks[12],  # Middle
                    hand_landmarks[16],  # Ring
                    hand_landmarks[20]   # Pinky
                ]
                all_fingertips.extend(fingertips)
            
            # Calculate center of all fingertips
            center_x = sum(tip[0] for tip in all_fingertips) / len(all_fingertips)
            center_y = sum(tip[1] for tip in all_fingertips) / len(all_fingertips)
            
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
            
            # Debug output (less frequent)
            if self.frame_count % 15 == 0:  # Every 15 frames
                print(f"[Debug] Cursor at ({screen_x}, {screen_y}) with {len(all_hands)} hands")
            
        except Exception as e:
            print(f"❌ Error updating cursor from hands: {e}")
    
    def _reset_cursor_mode(self):
        """Reset cursor mode when not enough fingers"""
        if self.cursor_active:
            self.cursor_active = False
            print("🤲 Back to single-hand gesture mode")
        self.cursor_start_time = 0
    
    def _detect_single_hand_gesture(self, hand_landmarks):
        """Detect gestures with single hand"""
        try:
            fingers_up = self._get_fingers_up(hand_landmarks)
            total_fingers = sum(fingers_up)
            
            gesture = None
            
            # Open Palm - 4 or 5 fingers extended
            if total_fingers >= 4:
                gesture = "scroll_down"
                print(f"[Debug] Single hand - Open Palm ({total_fingers} fingers)")
            
            # Closed Fist - 0 or 1 fingers extended
            elif total_fingers <= 1:
                gesture = "scroll_up"
                print(f"[Debug] Single hand - Closed Fist ({total_fingers} fingers)")
            
            # Pointing - only index finger
            elif fingers_up == [0, 1, 0, 0, 0]:
                gesture = "click"
                print(f"[Debug] Single hand - Pointing")
            
            # Peace sign - index + middle
            elif fingers_up == [0, 1, 1, 0, 0]:
                gesture = "click"
                print(f"[Debug] Single hand - Peace sign")
            
            # Thumbs up
            elif fingers_up[0] == 1 and sum(fingers_up[1:]) <= 1:
                # Check if thumb pointing up
                thumb_tip = hand_landmarks[4]
                wrist = hand_landmarks[0]
                if thumb_tip[1] < wrist[1] - 0.1:
                    gesture = "play_pause"
                    print(f"[Debug] Single hand - Thumbs up")
            
            # Apply cooldown
            current_time = time.time()
            if gesture and (gesture != self.last_gesture or 
                          current_time - self.last_gesture_time > self.gesture_cooldown):
                self.last_gesture = gesture
                self.last_gesture_time = current_time
                return gesture
            
            return None
            
        except Exception as e:
            print(f"❌ Error detecting single hand gesture: {e}")
            return None
    
    def _get_fingers_up(self, landmarks):
        """Determine which fingers are extended for one hand"""
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
            print(f"[DualHandGesture] {gesture.replace('_', ' ').title()}")
            
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
                    print(f"[DualHandGesture] Click at cursor ({self.last_cursor_x}, {self.last_cursor_y})")
                else:
                    # Click at center
                    screen_width, screen_height = pyautogui.size()
                    pyautogui.click(screen_width // 2, screen_height // 2)
                    print("[DualHandGesture] Click at center")
                
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
            "last_gesture": self.last_gesture,
            "cursor_position": (self.last_cursor_x, self.last_cursor_y) if self.last_cursor_x else None
        }
