#!/usr/bin/env python3
"""
Web-based Visual Video Quality Demo
Shows actual video quality changes in your browser - just like screen brightness!
"""

from flask import Flask, render_template_string, Response, jsonify
import cv2
import numpy as np
import time
import threading
import io
import base64

app = Flask(__name__)

class WebVideoPlayer:
    def __init__(self):
        self.current_quality = "1080p"
        self.current_fps = 30
        self.quality_factor = 1.0
        self.brightness = 1.0
        self.battery_level = 85
        self.frame_count = 0
        self.running = True
        
    def create_video_frame(self):
        """Create a colorful sample video frame"""
        # Base size
        width, height = 640, 360
        
        # Create animated background
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Moving gradient
        for y in range(height):
            for x in range(width):
                r = int(128 + 127 * np.sin(self.frame_count * 0.05 + x * 0.02))
                g = int(128 + 127 * np.sin(self.frame_count * 0.05 + y * 0.02))
                b = int(128 + 127 * np.sin(self.frame_count * 0.05 + (x + y) * 0.01))
                frame[y, x] = [b, g, r]
        
        # Add moving circle
        center_x = int(width/2 + 100 * np.sin(self.frame_count * 0.1))
        center_y = int(height/2 + 50 * np.cos(self.frame_count * 0.1))
        cv2.circle(frame, (center_x, center_y), 30, (255, 255, 255), -1)
        
        # Add quality text
        cv2.putText(frame, f"{self.current_quality} @ {self.current_fps}fps", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Add battery level
        cv2.putText(frame, f"Battery: {self.battery_level}%", 
                   (10, height - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Add quality factor
        cv2.putText(frame, f"Quality: {self.quality_factor:.1f}x", 
                   (10, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Apply quality reduction (blur)
        if self.quality_factor < 1.0:
            blur_amount = int((1.0 - self.quality_factor) * 8) + 1
            frame = cv2.blur(frame, (blur_amount, blur_amount))
        
        # Apply brightness reduction
        if self.brightness < 1.0:
            frame = cv2.convertScaleAbs(frame, alpha=self.brightness, beta=0)
        
        # Add noise for lower quality
        if self.quality_factor < 0.7:
            noise = np.random.randint(0, 30, frame.shape, dtype=np.uint8)
            frame = cv2.add(frame, noise)
        
        self.frame_count += 1
        return frame
    
    def optimize_for_battery(self, battery_level):
        """Apply battery optimization"""
        self.battery_level = battery_level
        
        if battery_level > 60:
            self.current_quality = "1080p"
            self.current_fps = 30
            self.quality_factor = 1.0
            self.brightness = 1.0
        elif battery_level > 30:
            self.current_quality = "720p"
            self.current_fps = 24
            self.quality_factor = 0.8
            self.brightness = 0.9
        elif battery_level > 15:
            self.current_quality = "480p"
            self.current_fps = 20
            self.quality_factor = 0.5
            self.brightness = 0.7
        else:
            self.current_quality = "360p"
            self.current_fps = 15
            self.quality_factor = 0.3
            self.brightness = 0.5

# Global video player
video_player = WebVideoPlayer()

# HTML Template
VIDEO_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>🔋 Live Video Quality Demo</title>
    <style>
        body { 
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            margin: 0;
            padding: 20px;
            text-align: center;
        }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { font-size: 2.5rem; margin-bottom: 20px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .video-container { 
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            backdrop-filter: blur(10px);
        }
        .video-frame { 
            border: 3px solid #fff;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .controls { 
            display: flex;
            justify-content: center;
            gap: 15px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        .btn { 
            padding: 12px 24px;
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 14px;
        }
        .btn:hover { 
            background: rgba(255,255,255,0.3);
            transform: translateY(-2px);
        }
        .status { 
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            font-size: 1.1rem;
        }
        .explanation {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: left;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔋 Live Video Quality Demo</h1>
        <p style="font-size: 1.2rem;">Watch the video quality change LIVE - just like screen brightness!</p>
        
        <div class="video-container">
            <img id="video-frame" class="video-frame" src="/video_feed" alt="Live Video" />
        </div>
        
        <div class="controls">
            <button class="btn" onclick="setBattery(85)">🔋 85% - Full Quality</button>
            <button class="btn" onclick="setBattery(50)">🟡 50% - Medium Quality</button>
            <button class="btn" onclick="setBattery(25)">🟠 25% - Low Quality</button>
            <button class="btn" onclick="setBattery(10)">🔴 10% - Critical</button>
            <button class="btn" onclick="setBattery(5)">🚨 5% - Emergency</button>
        </div>
        
        <div class="status" id="status">
            Battery: 85% | Quality: Full | Status: Ready
        </div>
        
        <div class="explanation">
            <h3>🎯 How It Works:</h3>
            <ul>
                <li><strong>🔋 85% Battery:</strong> Full 1080p quality, bright and crisp</li>
                <li><strong>🟡 50% Battery:</strong> 720p quality, slightly dimmer</li>
                <li><strong>🟠 25% Battery:</strong> 480p quality, more blur and dimming</li>
                <li><strong>🔴 10% Battery:</strong> 360p quality, very dim and blurry</li>
                <li><strong>🚨 5% Battery:</strong> Emergency mode - maximum power saving</li>
            </ul>
            <p><strong>💡 Key Point:</strong> The video quality changes INSTANTLY when you click the buttons - 
            just like how screen brightness changes immediately when battery gets low!</p>
        </div>
    </div>

    <script>
        function setBattery(level) {
            fetch('/set_battery/' + level)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').innerHTML = 
                        `Battery: ${data.battery}% | Quality: ${data.quality} | FPS: ${data.fps}`;
                });
        }
        
        // Auto-refresh video frame
        setInterval(() => {
            document.getElementById('video-frame').src = '/video_feed?' + new Date().getTime();
        }, 200);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(VIDEO_HTML)

@app.route('/video_feed')
def video_feed():
    """Generate video frames"""
    frame = video_player.create_video_frame()
    
    # Convert to JPEG
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    frame_bytes = buffer.tobytes()
    
    return Response(frame_bytes, mimetype='image/jpeg')

@app.route('/set_battery/<int:level>')
def set_battery(level):
    """Set battery level and optimize video"""
    video_player.optimize_for_battery(level)
    
    return jsonify({
        'battery': level,
        'quality': video_player.current_quality,
        'fps': video_player.current_fps,
        'brightness': video_player.brightness
    })

def main():
    print("🚀 Starting Web Video Quality Demo...")
    print("📺 This shows ACTUAL video quality changes like screen brightness!")
    print("🌐 Open your browser to: http://localhost:5001")
    print("🔋 Click the battery buttons to see instant quality changes!")
    print("🛑 Press Ctrl+C to stop")
    
    app.run(host='0.0.0.0', port=5001, debug=False)

if __name__ == "__main__":
    main()
