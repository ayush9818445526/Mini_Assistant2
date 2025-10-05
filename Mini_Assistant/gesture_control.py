import cv2
import mediapipe as mp
import threading
import time
import numpy as np
from typing import Optional, Tuple, List
import math


class GestureController:
    """
    Real-time hand gesture recognition using MediaPipe Hands.
    Detects gestures like open palm, fist, pointing, thumbs up for controlling TARA.
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
            max_num_hands=1,  # Track only one hand for simplicity
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Gesture detection parameters
        self.last_gesture = None
        self.last_gesture_time = 0
        self.gesture_cooldown = 0.5  # Seconds between same gesture triggers (reduced for better responsiveness)
        self.frame_skip = 2  # Process every nth frame for performance
        self.frame_count = 0
        
        # Gesture thresholds
        self.fist_threshold = 0.6  # Finger curl threshold for fist
        self.open_palm_threshold = 0.3  # Finger extension threshold for open palm
        self.pointing_threshold = 0.8  # Index finger extension for pointing
        
        # Cursor control parameters
        self.cursor_mode = False  # Enable/disable cursor tracking
        self.gesture_mode = True   # Enable/disable gesture detection
        self.cursor_only_mode = False  # Pure cursor mode (no gestures)
        self.screen_width = None
        self.screen_height = None
        self.camera_width = 640
        self.camera_height = 480
        
        # Smoothing for cursor movement
        self.cursor_smoothing = 0.7  # Higher = smoother but slower
        self.last_cursor_x = None
        self.last_cursor_y = None
        
        # Get screen dimensions
        try:
            import pyautogui
            self.screen_width, self.screen_height = pyautogui.size()
        except:
            self.screen_width, self.screen_height = 1920, 1080  # Default
        
        print("🤲 GestureController initialized with cursor control")
    
    def start(self):
        """Start gesture recognition in background thread"""
        if self.is_running:
            print("⚠️ Gesture control already running")
            return False
            
        try:
            # Try to initialize webcam
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("❌ Could not open webcam for gesture control")
                return False
                
            # Set camera properties for performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.is_running = True
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            print("✅ Gesture control started successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start gesture control: {e}")
            return False
    
    def stop(self):
        """Stop gesture recognition"""
        self.is_running = False
        self.is_enabled = False
        
        if self.cap:
            self.cap.release()
            self.cap = None
            
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
            
        print("🛑 Gesture control stopped")
    
    def enable(self):
        """Enable gesture processing"""
        if not self.is_running:
            if not self.start():
                return False
        self.is_enabled = True
        print("✅ Gesture control enabled")
        return True
    
    def disable(self):
        """Disable gesture processing but keep camera running"""
        self.is_enabled = False
        self.cursor_mode = False
        print("⏸️ Gesture control disabled")
    
    def enable_cursor_mode(self):
        """Enable cursor tracking mode"""
        if not self.is_running:
            if not self.start():
                return False
        self.is_enabled = True
        self.cursor_mode = True
        print("🖱️ Cursor control mode enabled")
        return True
    
    def disable_cursor_mode(self):
        """Disable cursor tracking mode"""
        self.cursor_mode = False
        print("🖱️ Cursor control mode disabled")
    
    def _capture_loop(self):
        """Main capture and processing loop running in background thread"""
        print("🎥 Starting gesture capture loop")
        
        while self.is_running:
            try:
                if not self.cap or not self.cap.isOpened():
                    break
                    
                ret, frame = self.cap.read()
                if not ret:
                    print("⚠️ Failed to read frame from webcam")
                    time.sleep(0.1)
                    continue
                
                # Skip frames for performance
                self.frame_count += 1
                if self.frame_count % self.frame_skip != 0:
                    continue
                
                # Only process if enabled
                if self.is_enabled:
                    # Handle cursor tracking if enabled
                    if self.cursor_mode:
                        self._update_cursor_position(frame)
                    
                    # Handle gesture detection (only if not in cursor-only mode)
                    if self.gesture_mode and not self.cursor_only_mode:
                        gesture = self.detect_gesture(frame)
                        if gesture:
                            self._handle_gesture(gesture)
                    
                    # In cursor-only mode, only detect click gestures
                    elif self.cursor_only_mode:
                        gesture = self._detect_click_only(frame)
                        if gesture:
                            self._handle_gesture(gesture)
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"❌ Error in gesture capture loop: {e}")
                time.sleep(0.5)
        
        print("🏁 Gesture capture loop ended")
    
    def detect_gesture(self, frame) -> Optional[str]:
        """
        Detect hand gesture from frame.
        Returns: gesture type string or None
        """
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            if not results.multi_hand_landmarks:
                return None
            
            # Get first hand landmarks
            hand_landmarks = results.multi_hand_landmarks[0]
            landmarks = []
            
            # Extract landmark coordinates
            for lm in hand_landmarks.landmark:
                landmarks.append([lm.x, lm.y])
            
            # Detect specific gestures
            gesture = self._classify_gesture(landmarks)
            return gesture
            
        except Exception as e:
            print(f"❌ Error detecting gesture: {e}")
            return None
    
    def _classify_gesture(self, landmarks: List[List[float]]) -> Optional[str]:
        """
        Classify gesture based on hand landmarks.
        landmarks: List of [x, y] coordinates for 21 hand landmarks
        """
        if len(landmarks) != 21:
            return None
        
        try:
            # Get key landmark points
            thumb_tip = landmarks[4]
            thumb_ip = landmarks[3]
            index_tip = landmarks[8]
            index_pip = landmarks[6]
            middle_tip = landmarks[12]
            middle_pip = landmarks[10]
            ring_tip = landmarks[16]
            ring_pip = landmarks[14]
            pinky_tip = landmarks[20]
            pinky_pip = landmarks[18]
            wrist = landmarks[0]
            
            # Calculate finger states (extended or curled)
            fingers_up = self._get_fingers_up(landmarks)
            total_fingers = sum(fingers_up)
            
            # Debug print for gesture detection
            print(f"[Debug] Fingers up: {fingers_up}, Total: {total_fingers}")
            
            # Gesture classification with more reliable detection
            gesture = None
            
            # Open Palm - 4 or 5 fingers extended
            if total_fingers >= 4:
                gesture = "scroll_down"
                print(f"[Debug] Detected Open Palm - {total_fingers} fingers up")
            
            # Closed Fist - 0 or 1 fingers extended
            elif total_fingers <= 1:
                gesture = "scroll_up"
                print(f"[Debug] Detected Closed Fist - {total_fingers} fingers up")
            
            # Pointing - only index finger extended (strict)
            elif fingers_up == [0, 1, 0, 0, 0]:
                gesture = "click"
                print(f"[Debug] Detected Pointing - index finger only")
            
            # Thumbs Up - only thumb extended upward
            elif fingers_up[0] == 1 and sum(fingers_up[1:]) <= 1:
                # Check if thumb is pointing up (y coordinate smaller than wrist)
                if thumb_tip[1] < wrist[1] - 0.1:
                    gesture = "play_pause"
                    print(f"[Debug] Detected Thumbs Up")
            
            # Alternative pointing detection - index + middle (peace sign) also counts as click
            elif fingers_up == [0, 1, 1, 0, 0] or total_fingers == 2:
                gesture = "click"
                print(f"[Debug] Detected Alternative Pointing - 2 fingers")
            
            # Add cooldown to prevent rapid repeated gestures
            current_time = time.time()
            if gesture and (gesture != self.last_gesture or 
                          current_time - self.last_gesture_time > self.gesture_cooldown):
                self.last_gesture = gesture
                self.last_gesture_time = current_time
                return gesture
            
            return None
            
        except Exception as e:
            print(f"❌ Error classifying gesture: {e}")
            return None
    
    def _get_fingers_up(self, landmarks: List[List[float]]) -> List[int]:
        """
        Determine which fingers are extended.
        Returns: [thumb, index, middle, ring, pinky] as 0 (down) or 1 (up)
        """
        fingers = []
        
        # Thumb - compare tip with IP joint (x-coordinate for left/right)
        if landmarks[4][0] > landmarks[3][0]:  # Right hand assumption
            fingers.append(1)
        else:
            fingers.append(0)
        
        # Other fingers - compare tip with PIP joint (y-coordinate for up/down)
        finger_tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky
        finger_pips = [6, 10, 14, 18]
        
        for tip, pip in zip(finger_tips, finger_pips):
            fingers.append(1 if landmarks[tip][1] < landmarks[pip][1] else 0)
        
        return fingers
    
    def _handle_gesture(self, gesture: str):
        """Execute action based on detected gesture"""
        try:
            print(f"[GestureControl] {gesture.replace('_', ' ').title()}")
            
            if not self.screen_controller:
                print("⚠️ No screen controller available for gesture actions")
                return
            
            if gesture == "scroll_down":
                self.screen_controller.scroll_down()
                
            elif gesture == "scroll_up":
                self.screen_controller.scroll_up()
                
            elif gesture == "click":
                # Click at current cursor position or center
                import pyautogui
                if self.cursor_mode and self.last_cursor_x and self.last_cursor_y:
                    pyautogui.click(self.last_cursor_x, self.last_cursor_y)
                    print(f"[GestureControl] Click at ({self.last_cursor_x}, {self.last_cursor_y})")
                else:
                    screen_width, screen_height = pyautogui.size()
                    pyautogui.click(screen_width // 2, screen_height // 2)
                    print("[GestureControl] Click at center")
                
            elif gesture == "play_pause":
                # Try to play/pause video (spacebar)
                import pyautogui
                pyautogui.press('space')
                
        except Exception as e:
            print(f"❌ Error handling gesture {gesture}: {e}")
    
    def _update_cursor_position(self, frame):
        """Update cursor position based on hand tracking"""
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            if not results.multi_hand_landmarks:
                return
            
            # Get first hand landmarks
            hand_landmarks = results.multi_hand_landmarks[0]
            
            # Use index finger tip for cursor position (landmark 8)
            index_tip = hand_landmarks.landmark[8]
            
            # Convert normalized coordinates to screen coordinates
            # Flip X coordinate for mirror effect
            screen_x = int((1 - index_tip.x) * self.screen_width)
            screen_y = int(index_tip.y * self.screen_height)
            
            # Apply smoothing to reduce jitter
            if self.last_cursor_x is not None and self.last_cursor_y is not None:
                screen_x = int(self.cursor_smoothing * self.last_cursor_x + (1 - self.cursor_smoothing) * screen_x)
                screen_y = int(self.cursor_smoothing * self.last_cursor_y + (1 - self.cursor_smoothing) * screen_y)
            
            # Clamp to screen boundaries
            screen_x = max(0, min(screen_x, self.screen_width - 1))
            screen_y = max(0, min(screen_y, self.screen_height - 1))
            
            # Update cursor position
            import pyautogui
            pyautogui.moveTo(screen_x, screen_y)
            
            # Store for smoothing and clicking
            self.last_cursor_x = screen_x
            self.last_cursor_y = screen_y
            
        except Exception as e:
            print(f"❌ Error updating cursor position: {e}")
    
    def get_status(self) -> dict:
        """Get current status of gesture controller"""
        return {
            "running": self.is_running,
            "enabled": self.is_enabled,
            "cursor_mode": getattr(self, 'cursor_mode', False),
            "camera_available": self.cap is not None and self.cap.isOpened() if self.cap else False,
            "last_gesture": self.last_gesture,
            "last_gesture_time": self.last_gesture_time,
            "cursor_position": (getattr(self, 'last_cursor_x', None), getattr(self, 'last_cursor_y', None))
        }

    def enable_cursor_mode(self):
        """Enable cursor tracking mode"""
        if not self.is_running:
            if not self.start():
                return False
        self.is_enabled = True
        self.cursor_mode = True
        print("🖱️ Cursor control mode enabled")
        return True
    
    def disable_cursor_mode(self):
        """Disable cursor tracking mode"""
        self.cursor_mode = False
        print("🖱️ Cursor control mode disabled")
