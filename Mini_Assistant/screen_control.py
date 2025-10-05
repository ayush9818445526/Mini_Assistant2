#!/usr/bin/env python3
"""
TARA Screen Control Module
Advanced screen monitoring and control capabilities
"""

import pyautogui
import time
import win32gui
import subprocess
import cv2
import numpy as np
from PIL import Image
import base64
import io
import win32gui
import win32con
import win32api

class ScreenController:
    def __init__(self):
        self.scrolling = False
        # Disable pyautogui failsafe for better control
        pyautogui.FAILSAFE = False
        
    def get_active_window_title(self):
        """Get the title of the currently active window"""
        try:
            window = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(window)
            return window_title.lower()
        except:
            return None
        
    def scroll_down(self):
        """Scroll down on current screen continuously"""
        try:
            self.scrolling = True
            # 3x faster scrolling - 45 scrolls with maximum force
            for _ in range(45):
                if not self.scrolling:
                    break
                pyautogui.scroll(-15)
                time.sleep(0.01)
        except:
            pass
        
    def scroll_up(self):
        """Scroll up on current screen continuously"""
        try:
            self.scrolling = True
            # 3x faster scrolling - 45 scrolls with maximum force
            for _ in range(45):
                if not self.scrolling:
                    break
                pyautogui.scroll(15)
                time.sleep(0.01)
        except:
            pass
    
    def stop_scrolling(self):
        """Stop continuous scrolling"""
        self.scrolling = False
        
    def search_in_active_app(self, search_term):
        """Search within the currently active application"""
        active_window = self.get_active_window_title()
        
        if not active_window:
            return False
            
        screen_width, screen_height = pyautogui.size()
        
        if "youtube" in active_window:
            # Search in YouTube - target the actual YouTube search box, not browser address bar
            # YouTube search box is typically in the upper area but below the browser address bar
            search_box_positions = [
                (int(screen_width * 0.5), int(screen_height * 0.15)),   # Center, below address bar
                (int(screen_width * 0.45), int(screen_height * 0.15)),  # Slightly left
                (int(screen_width * 0.55), int(screen_height * 0.15)),  # Slightly right
                (int(screen_width * 0.5), int(screen_height * 0.18)),   # Lower
                (int(screen_width * 0.5), int(screen_height * 0.12)),   # Higher
            ]
            
            print(f"Searching for '{search_term}' in YouTube (not browser address bar)")
            
            # Try multiple YouTube search box positions
            for i, (x, y) in enumerate(search_box_positions):
                try:
                    print(f"Trying YouTube search box position {i+1}: ({x}, {y})")
                    
                    # Click on YouTube search box (not browser address bar)
                    pyautogui.click(x, y)
                    time.sleep(1.0)  # Wait longer for focus
                    
                    # Verify we're in the right search box by checking if we can type
                    pyautogui.hotkey('ctrl', 'a')  # Select existing text
                    time.sleep(0.4)
                    pyautogui.typewrite(search_term)
                    time.sleep(0.6)
                    pyautogui.press('enter')
                    
                    print(f"✅ Successfully searched for '{search_term}' in YouTube search box")
                    return True
                    
                except Exception as e:
                    print(f"YouTube search position {i+1} failed: {e}")
                    continue
            
            print("❌ All YouTube search box positions failed")
            return False
            
        elif "chatgpt" in active_window or "openai" in active_window:
            # Search in ChatGPT
            input_x = screen_width // 2
            input_y = int(screen_height * 0.85)  # Bottom 15% of screen
            
            pyautogui.click(input_x, input_y)
            time.sleep(0.5)
            pyautogui.typewrite(search_term)
            pyautogui.press('enter')
            return True
            
        elif "whatsapp" in active_window:
            # Search in WhatsApp - click search box at top
            search_x = int(screen_width * 0.25)  # Left side where search usually is
            search_y = int(screen_height * 0.08)  # Top area
            
            pyautogui.click(search_x, search_y)
            time.sleep(0.8)
            pyautogui.hotkey('ctrl', 'a')  # Clear existing search
            time.sleep(0.3)
            pyautogui.typewrite(search_term)
            time.sleep(1.0)  # Wait for search results
            return True
            
        elif "chrome" in active_window or "firefox" in active_window or "edge" in active_window:
            # Search in browser address bar
            pyautogui.hotkey('ctrl', 'l')  # Focus address bar
            time.sleep(0.5)
            pyautogui.typewrite(search_term)
            pyautogui.press('enter')
            return True
            
        return False
        
    def type_text(self, text):
        """Type text at current cursor position"""
        pyautogui.typewrite(text)
        
    def click_at_position(self, x, y):
        """Click at specific screen coordinates"""
        pyautogui.click(x, y)
        
    def take_screenshot(self):
        """Take a screenshot of current screen"""
        return pyautogui.screenshot()
        
    def click_first_video(self):
        """Click on the first video in YouTube search results"""
        try:
            screen_width, screen_height = pyautogui.size()
            
            # Calculate relative positions based on screen size
            video_positions = [
                (int(screen_width * 0.25), int(screen_height * 0.35)),  # Left column, first video
                (int(screen_width * 0.20), int(screen_height * 0.30)),  # Slightly higher and left
                (int(screen_width * 0.30), int(screen_height * 0.40)),  # Slightly lower and right
                (int(screen_width * 0.25), int(screen_height * 0.25)),  # Higher up
                (int(screen_width * 0.15), int(screen_height * 0.35)),  # More left
                (int(screen_width * 0.35), int(screen_height * 0.35)),  # More right
                (int(screen_width * 0.25), int(screen_height * 0.45)),  # Lower
            ]
            
            print("🎯 Attempting to click first video...")
            for i, pos in enumerate(video_positions):
                try:
                    print(f"   Trying position {i+1}: ({pos[0]}, {pos[1]})")
                    # Move mouse first, then click
                    pyautogui.moveTo(pos[0], pos[1])
                    time.sleep(0.3)
                    pyautogui.click()
                    time.sleep(1.5)  # Wait longer to see if video loads
                    print(f"   ✅ Clicked at position {i+1}")
                    return True
                except Exception as e:
                    print(f"   ❌ Position {i+1} failed: {e}")
                    continue
            print("❌ All video positions failed")
            return False
        except Exception as e:
            print(f"❌ Click first video error: {e}")
            return False
    
    def click_second_video(self):
        """Click on the second video in YouTube search results"""
        try:
            # Second video positions - more comprehensive
            video_positions = [
                (400, 450),  # Second video thumbnail
                (350, 430),  # Slightly left
                (450, 450),  # Slightly right
                (400, 470),  # Slightly lower
                (320, 450),  # Far left
                (480, 450),  # More right
            ]
            
            for pos in video_positions:
                try:
                    # Single click to avoid selecting text
                    pyautogui.click(pos[0], pos[1])
                    time.sleep(0.8)  # Wait for video to load
                    return True
                except:
                    continue
            return False
        except:
            return False
            
    def click_video_by_title(self, title):
        """Try to click a video by searching for title text on screen"""
        try:
            # Take screenshot to analyze
            screenshot = pyautogui.screenshot()
            
            # Convert to OpenCV format for text detection
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Try to find clickable video elements more precisely
            # Focus on typical YouTube video thumbnail positions
            video_areas = [
                (320, 280), (320, 380), (320, 480), (320, 580),  # Left column
                (640, 280), (640, 380), (640, 480), (640, 580),  # Center column
                (960, 280), (960, 380), (960, 480), (960, 580),  # Right column
            ]
            
            # Try precise single click to avoid text selection
            for area in video_areas:
                try:
                    # Use direct click with coordinates to avoid selection
                    pyautogui.click(area[0], area[1], clicks=1, interval=0.0, button='left')
                    time.sleep(0.8)  # Wait for video to load
                    return True
                except:
                    continue
            return False
        except:
            return False
            
    def send_message(self):
        """Send message by pressing Enter"""
        try:
            pyautogui.press('enter')
            return True
        except:
            return False
            
    def search_whatsapp_contact(self, contact_name):
        """Search for a specific contact in WhatsApp"""
        try:
            # Click on WhatsApp search box at top
            pyautogui.click(300, 100)
            time.sleep(0.5)
            
            # Clear existing text and type contact name
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.2)
            pyautogui.typewrite(contact_name)
            time.sleep(1.5)
            
            return True
        except:
            return False
    
    def click_first_whatsapp_contact(self):
        """Click on first contact in WhatsApp search results and enter chat"""
        try:
            screen_width, screen_height = pyautogui.size()
            
            # Calculate relative positions for WhatsApp contacts based on screen size
            contact_positions = [
                (int(screen_width * 0.25), int(screen_height * 0.20)),  # Top left area where contacts appear
                (int(screen_width * 0.20), int(screen_height * 0.18)),  # Slightly higher and left
                (int(screen_width * 0.30), int(screen_height * 0.22)),  # Slightly lower and right
                (int(screen_width * 0.25), int(screen_height * 0.15)),  # Higher up
                (int(screen_width * 0.25), int(screen_height * 0.25)),  # Lower down
                (int(screen_width * 0.15), int(screen_height * 0.20)),  # More left
                (int(screen_width * 0.35), int(screen_height * 0.20)),  # More right
                (int(screen_width * 0.25), int(screen_height * 0.30)),  # Much lower
            ]
            
            print("🎯 Attempting to click WhatsApp contact...")
            for i, pos in enumerate(contact_positions):
                try:
                    print(f"   Trying contact position {i+1}: ({pos[0]}, {pos[1]})")
                    # Move mouse first, then click
                    pyautogui.moveTo(pos[0], pos[1])
                    time.sleep(0.4)
                    pyautogui.click()
                    time.sleep(1.5)  # Wait longer for chat to load
                    print(f"   ✅ Clicked contact at position {i+1}")
                    return True
                except Exception as e:
                    print(f"   ❌ Contact position {i+1} failed: {e}")
                    continue
            print("❌ All contact positions failed")
            return False
        except Exception as e:
            print(f"❌ Click WhatsApp contact error: {e}")
            return False
    
    def type_whatsapp_message(self, message):
        """Type message in WhatsApp chat"""
        try:
            # Click on WhatsApp message input box
            pyautogui.click(600, 650)
            time.sleep(0.5)
            
            # Type the message
            pyautogui.typewrite(message)
            time.sleep(0.3)
            
            return True
        except:
            return False
    
    def click_song_by_name(self, song_name):
        """Click on a specific song in YouTube search results"""
        try:
            # Multiple positions to try for song videos
            song_positions = [
                (320, 280), (320, 380), (320, 480),  # Left column
                (640, 280), (640, 380), (640, 480),  # Center column
                (960, 280), (960, 380), (960, 480),  # Right column
            ]
            
            # Try clicking on different video positions
            for pos in song_positions:
                try:
                    pyautogui.click(pos[0], pos[1])
                    time.sleep(1)
                    return True
                except:
                    continue
            return False
        except:
            return False
    
    def go_back_browser(self):
        """Go back in browser"""
        try:
            pyautogui.hotkey('alt', 'left')
            return True
        except:
            return False
    
    def go_forward_browser(self):
        """Go forward in browser"""
        try:
            pyautogui.hotkey('alt', 'right')
            return True
        except:
            return False
    
    def switch_tab_previous(self):
        """Switch to previous tab"""
        try:
            pyautogui.hotkey('ctrl', 'shift', 'tab')
            return True
        except:
            return False
    
    def switch_tab_next(self):
        """Switch to next tab"""
        try:
            pyautogui.hotkey('ctrl', 'tab')
            return True
        except:
            return False
    
    def capture_screen(self):
        """Capture current screen and return as image"""
        try:
            screenshot = pyautogui.screenshot()
            return screenshot
        except Exception as e:
            print(f"❌ Screen capture error: {e}")
            return None
    
    def analyze_screen_content(self):
        """Analyze what's currently on screen"""
        try:
            screenshot = self.capture_screen()
            if screenshot:
                # Convert to base64 for analysis
                buffer = io.BytesIO()
                screenshot.save(buffer, format='PNG')
                img_str = base64.b64encode(buffer.getvalue()).decode()
                return img_str
            return None
        except Exception as e:
            print(f"❌ Screen analysis error: {e}")
            return None
    
    def open_new_tab(self):
        """Open new tab in browser"""
        try:
            pyautogui.hotkey('ctrl', 't')
            return True
        except:
            return False
    
    def close_current_tab(self):
        """Close current tab"""
        try:
            pyautogui.hotkey('ctrl', 'w')
            return True
        except:
            return False
    
    def refresh_page(self):
        """Refresh current page"""
        try:
            pyautogui.hotkey('ctrl', 'r')
            return True
        except:
            return False
    
    def zoom_in(self):
        """Zoom in on current page"""
        try:
            pyautogui.hotkey('ctrl', '+')
            return True
        except:
            return False
    
    def zoom_out(self):
        """Zoom out on current page"""
        try:
            pyautogui.hotkey('ctrl', '-')
            return True
        except:
            return False
    
    def select_all(self):
        """Select all content"""
        try:
            pyautogui.hotkey('ctrl', 'a')
            return True
        except:
            return False
    
    def copy_content(self):
        """Copy selected content"""
        try:
            pyautogui.hotkey('ctrl', 'c')
            return True
        except:
            return False
    
    def paste_content(self):
        """Paste content"""
        try:
            pyautogui.hotkey('ctrl', 'v')
            return True
        except:
            return False
    
    def undo_action(self):
        """Undo last action"""
        try:
            pyautogui.hotkey('ctrl', 'z')
            return True
        except:
            return False
    
    def redo_action(self):
        """Redo last action"""
        try:
            pyautogui.hotkey('ctrl', 'y')
            return True
        except:
            return False
    
    def minimize_window(self):
        """Minimize current window"""
        try:
            pyautogui.hotkey('win', 'down')
            return True
        except:
            return False
    
    def maximize_window(self):
        """Maximize current window"""
        try:
            pyautogui.hotkey('win', 'up')
            return True
        except:
            return False
    
    def switch_windows(self):
        """Switch between open windows"""
        try:
            pyautogui.hotkey('alt', 'tab')
            return True
        except:
            return False
