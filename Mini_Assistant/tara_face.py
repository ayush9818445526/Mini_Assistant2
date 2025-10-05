#!/usr/bin/env python3
"""
TARA Animated Face GUI
Living face with human-like expressions and animations
"""

import tkinter as tk
from tkinter import Canvas
import threading
import time
import random
import math
from PIL import Image, ImageTk

class TaraFace:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TARA - Your AI Assistant")
        self.root.geometry("400x500")
        self.root.configure(bg='#0a0a0a')
        self.root.resizable(False, False)
        
        # Make window stay on top and look modern
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.95)
        
        # Face state variables
        self.current_expression = "idle"
        self.is_blinking = False
        self.is_speaking = False
        self.eye_blink_timer = 0
        self.expression_timer = 0
        
        # Animation variables
        self.blink_duration = 0.15
        self.last_blink = time.time()
        self.blink_interval = random.uniform(2, 5)
        
        # Setup canvas
        self.canvas = Canvas(
            self.root, 
            width=380, 
            height=380,
            bg='#0a0a0a',
            highlightthickness=0
        )
        self.canvas.pack(pady=20)
        
        # Status label
        self.status_label = tk.Label(
            self.root,
            text="TARA is sleeping...",
            font=("Arial", 12, "bold"),
            fg='#00ff88',
            bg='#0a0a0a'
        )
        self.status_label.pack(pady=10)
        
        # Start animation loop
        self.animate_face()
        
    def draw_face(self):
        """Draw TARA's face with current expression"""
        self.canvas.delete("all")
        
        # Face outline (glowing effect)
        for i in range(5):
            self.canvas.create_oval(
                50 - i*2, 50 - i*2, 
                330 + i*2, 330 + i*2,
                outline=f"#{hex(int(0x00ff88 - i*20))[2:].zfill(6)}",
                width=2
            )
        
        # Main face
        self.canvas.create_oval(
            50, 50, 330, 330,
            fill='#1a1a2e',
            outline='#00ff88',
            width=3
        )
        
        # Eyes
        self.draw_eyes()
        
        # Mouth based on expression
        self.draw_mouth()
        
        # Additional expression elements
        if self.current_expression == "thinking":
            self.draw_thinking_dots()
        elif self.current_expression == "happy":
            self.draw_cheek_blush()
            
    def draw_eyes(self):
        """Draw eyes with blinking animation"""
        eye_y = 130
        left_eye_x = 130
        right_eye_x = 250
        
        if self.is_blinking:
            # Closed eyes (blinking)
            self.canvas.create_line(
                left_eye_x - 20, eye_y,
                left_eye_x + 20, eye_y,
                fill='#00ff88', width=4
            )
            self.canvas.create_line(
                right_eye_x - 20, eye_y,
                right_eye_x + 20, eye_y,
                fill='#00ff88', width=4
            )
        else:
            # Open eyes
            # Eye whites
            self.canvas.create_oval(
                left_eye_x - 25, eye_y - 15,
                left_eye_x + 25, eye_y + 15,
                fill='white', outline='#00ff88', width=2
            )
            self.canvas.create_oval(
                right_eye_x - 25, eye_y - 15,
                right_eye_x + 25, eye_y + 15,
                fill='white', outline='#00ff88', width=2
            )
            
            # Pupils
            pupil_offset = 0
            if self.current_expression == "thinking":
                pupil_offset = 5  # Look slightly up when thinking
            
            self.canvas.create_oval(
                left_eye_x - 8, eye_y - 8 - pupil_offset,
                left_eye_x + 8, eye_y + 8 - pupil_offset,
                fill='#0066cc', outline='#004499', width=1
            )
            self.canvas.create_oval(
                right_eye_x - 8, eye_y - 8 - pupil_offset,
                right_eye_x + 8, eye_y + 8 - pupil_offset,
                fill='#0066cc', outline='#004499', width=1
            )
            
            # Eye shine
            self.canvas.create_oval(
                left_eye_x - 3, eye_y - 5 - pupil_offset,
                left_eye_x + 1, eye_y - 1 - pupil_offset,
                fill='white', outline=''
            )
            self.canvas.create_oval(
                right_eye_x - 3, eye_y - 5 - pupil_offset,
                right_eye_x + 1, eye_y - 1 - pupil_offset,
                fill='white', outline=''
            )
            
    def draw_mouth(self):
        """Draw mouth based on current expression"""
        mouth_x = 190
        mouth_y = 220
        
        if self.current_expression == "idle" or self.current_expression == "sleeping":
            # Neutral mouth
            self.canvas.create_line(
                mouth_x - 15, mouth_y,
                mouth_x + 15, mouth_y,
                fill='#00ff88', width=3
            )
        elif self.current_expression == "happy" or self.current_expression == "excited":
            # Smiling mouth
            self.canvas.create_arc(
                mouth_x - 25, mouth_y - 15,
                mouth_x + 25, mouth_y + 15,
                start=0, extent=180,
                outline='#00ff88', width=4,
                style='arc'
            )
        elif self.current_expression == "speaking":
            # Open mouth (oval)
            self.canvas.create_oval(
                mouth_x - 12, mouth_y - 8,
                mouth_x + 12, mouth_y + 8,
                fill='#2a2a4e', outline='#00ff88', width=3
            )
        elif self.current_expression == "thinking":
            # Slightly open mouth
            self.canvas.create_arc(
                mouth_x - 10, mouth_y - 5,
                mouth_x + 10, mouth_y + 10,
                start=0, extent=180,
                outline='#00ff88', width=3,
                style='arc'
            )
            
    def draw_thinking_dots(self):
        """Draw thinking dots animation"""
        dots_x = 350
        dots_y = 100
        
        for i in range(3):
            alpha = (math.sin(time.time() * 3 + i * 0.5) + 1) / 2
            color_intensity = int(0x88 * alpha)
            color = f"#00ff{color_intensity:02x}"
            
            self.canvas.create_oval(
                dots_x + i * 15 - 3, dots_y - 3,
                dots_x + i * 15 + 3, dots_y + 3,
                fill=color, outline=''
            )
            
    def draw_cheek_blush(self):
        """Draw blushing cheeks for happy expression"""
        # Left cheek
        self.canvas.create_oval(
            90, 170, 110, 190,
            fill='#ff6b9d', outline='', stipple='gray25'
        )
        # Right cheek
        self.canvas.create_oval(
            270, 170, 290, 190,
            fill='#ff6b9d', outline='', stipple='gray25'
        )
        
    def set_expression(self, expression, duration=2.0):
        """Set facial expression"""
        self.current_expression = expression
        self.expression_timer = time.time() + duration
        
        # Update status text
        status_messages = {
            "idle": "TARA is listening...",
            "happy": "TARA is happy! 😊",
            "excited": "TARA is excited! ✨",
            "thinking": "TARA is thinking... 💭",
            "speaking": "TARA is speaking... 💬",
            "sleeping": "TARA is sleeping... 😴"
        }
        
        self.status_label.config(text=status_messages.get(expression, "TARA"))
        
    def blink(self):
        """Trigger a blink animation"""
        self.is_blinking = True
        self.root.after(int(self.blink_duration * 1000), self.stop_blink)
        
    def stop_blink(self):
        """Stop blinking"""
        self.is_blinking = False
        
    def animate_face(self):
        """Main animation loop"""
        current_time = time.time()
        
        # Handle automatic blinking
        if current_time - self.last_blink > self.blink_interval:
            self.blink()
            self.last_blink = current_time
            self.blink_interval = random.uniform(2, 5)
            
        # Reset expression to idle after timer
        if self.expression_timer > 0 and current_time > self.expression_timer:
            self.current_expression = "idle"
            self.expression_timer = 0
            self.status_label.config(text="TARA is listening...")
            
        # Redraw face
        self.draw_face()
        
        # Schedule next frame
        self.root.after(50, self.animate_face)
        
    def show_wake_up_animation(self):
        """Special animation when TARA wakes up"""
        # Quick blink sequence
        for i in range(3):
            self.root.after(i * 200, self.blink)
        
        # Set happy expression
        self.root.after(800, lambda: self.set_expression("excited", 3.0))
        
    def show_sleep_animation(self):
        """Animation when TARA goes to sleep"""
        self.set_expression("sleeping")
        
    def start_speaking_animation(self):
        """Start speaking animation"""
        self.set_expression("speaking")
        self.is_speaking = True
        
    def stop_speaking_animation(self):
        """Stop speaking animation"""
        self.is_speaking = False
        self.set_expression("idle")
        
    def run(self):
        """Start the GUI"""
        self.root.mainloop()
        
    def close(self):
        """Close the face window"""
        self.root.quit()
        self.root.destroy()

# Test the face if run directly
if __name__ == "__main__":
    face = TaraFace()
    
    # Demo different expressions
    def demo():
        time.sleep(2)
        face.set_expression("happy", 2)
        time.sleep(3)
        face.set_expression("thinking", 3)
        time.sleep(4)
        face.set_expression("speaking", 2)
        time.sleep(3)
        face.show_wake_up_animation()
    
    # Run demo in separate thread
    threading.Thread(target=demo, daemon=True).start()
    
    face.run()
