#!/usr/bin/env python3
"""
Visual Video Quality Demo - Shows actual video that changes quality in real-time
"""

import cv2
import numpy as np
import time
import threading
from core.reasoning import OptimizationAction
import os

class VisualVideoPlayer:
    """A video player that shows actual visual quality changes"""
    
    def __init__(self):
        self.playing = False
        self.current_quality = "1080p"
        self.current_fps = 30
        self.quality_factor = 1.0
        self.brightness = 1.0
        
    def create_sample_video_frame(self, width, height, frame_num):
        """Create a colorful sample video frame"""
        # Create a colorful animated frame
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Moving gradient background
        for y in range(height):
            for x in range(width):
                r = int(128 + 127 * np.sin(frame_num * 0.1 + x * 0.01))
                g = int(128 + 127 * np.sin(frame_num * 0.1 + y * 0.01))
                b = int(128 + 127 * np.sin(frame_num * 0.1 + (x + y) * 0.005))
                frame[y, x] = [b, g, r]  # BGR format
        
        # Add moving text
        text_x = int(50 + 100 * np.sin(frame_num * 0.05))
        cv2.putText(frame, f"{self.current_quality} @ {self.current_fps}fps", 
                   (text_x, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
        
        # Add quality indicator
        quality_text = f"Quality: {self.quality_factor:.1f}x"
        cv2.putText(frame, quality_text, (50, height - 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Apply quality reduction (blur for lower quality)
        if self.quality_factor < 1.0:
            blur_amount = int((1.0 - self.quality_factor) * 10) + 1
            frame = cv2.blur(frame, (blur_amount, blur_amount))
        
        # Apply brightness
        if self.brightness < 1.0:
            frame = cv2.convertScaleAbs(frame, alpha=self.brightness, beta=0)
        
        return frame
    
    def start_video(self):
        """Start playing the visual video"""
        print("🎥 Starting visual video player...")
        print("📺 You should see a colorful animated video window")
        print("🎯 Watch for quality changes when battery gets low!")
        
        self.playing = True
        frame_num = 0
        
        # Initial settings - Full HD
        width, height = 1920, 1080
        
        while self.playing:
            try:
                # Create frame
                frame = self.create_sample_video_frame(width, height, frame_num)
                
                # Resize for display (so it fits on screen)
                display_frame = cv2.resize(frame, (960, 540))
                
                # Show the frame
                cv2.imshow('Battery-Optimized Video Player', display_frame)
                
                # Handle window events
                key = cv2.waitKey(int(1000 / self.current_fps)) & 0xFF
                if key == ord('q') or key == 27:  # 'q' or ESC to quit
                    break
                
                frame_num += 1
                
            except Exception as e:
                print(f"Video error: {e}")
                break
        
        cv2.destroyAllWindows()
        self.playing = False
    
    def optimize_for_battery(self, battery_level):
        """Apply battery optimization - changes video quality visually"""
        
        if battery_level > 60:
            # Good battery - Full quality
            self.current_quality = "1080p"
            self.current_fps = 30
            self.quality_factor = 1.0
            self.brightness = 1.0
            print("✅ Battery Good: Full 1080p quality")
            
        elif battery_level > 30:
            # Medium battery - Slight reduction
            self.current_quality = "1080p"
            self.current_fps = 24
            self.quality_factor = 0.8
            self.brightness = 0.9
            print("🟡 Battery Medium: Reduced quality, dimmer")
            
        elif battery_level > 15:
            # Low battery - Noticeable reduction
            self.current_quality = "720p"
            self.current_fps = 20
            self.quality_factor = 0.6
            self.brightness = 0.7
            print("🟠 Battery Low: 720p quality, more blur")
            
        else:
            # Critical battery - Maximum savings
            self.current_quality = "480p"
            self.current_fps = 15
            self.quality_factor = 0.3
            self.brightness = 0.5
            print("🔴 Battery Critical: 480p, very dim and blurry")
    
    def stop_video(self):
        """Stop the video"""
        self.playing = False

def battery_simulation_thread(player):
    """Simulate battery dropping and show optimizations"""
    battery_levels = [85, 50, 25, 10, 5, 80]  # Simulate battery changes
    descriptions = [
        "🔋 Battery: 85% - Full quality",
        "🔋 Battery: 50% - Medium optimization", 
        "🔋 Battery: 25% - Low battery optimization",
        "🔋 Battery: 10% - Critical optimization",
        "🔋 Battery: 5% - Emergency mode",
        "🔌 Plugged in: 80% - Quality restored"
    ]
    
    time.sleep(3)  # Let video start
    
    for i, (battery, desc) in enumerate(zip(battery_levels, descriptions)):
        print(f"\n{desc}")
        print("=" * 50)
        player.optimize_for_battery(battery)
        
        # Show each level for 8 seconds
        time.sleep(8)
    
    print("\n🎯 Demo complete! Press 'q' in video window to exit")

def main():
    print("🚀 VISUAL VIDEO QUALITY DEMO")
    print("=" * 60)
    print("This shows ACTUAL video quality reduction like screen brightness!")
    print("📺 A video window will open - watch it change quality")
    print("🔋 Battery levels will simulate dropping automatically")
    print("=" * 60)
    
    player = VisualVideoPlayer()
    
    # Start battery simulation in background
    battery_thread = threading.Thread(target=battery_simulation_thread, args=(player,), daemon=True)
    battery_thread.start()
    
    try:
        # Start the visual video (blocking)
        player.start_video()
    except KeyboardInterrupt:
        print("\n🛑 Stopping demo...")
    finally:
        player.stop_video()

if __name__ == "__main__":
    main()
