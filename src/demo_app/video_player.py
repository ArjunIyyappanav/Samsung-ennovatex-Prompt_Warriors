"""
Demo Video Player Application - Target app for battery optimization demonstration
"""

import cv2
import numpy as np
import time
import threading
import logging
from dataclasses import dataclass
from typing import Optional, Callable, Dict, Any
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.reasoning import OptimizationAction
from core.actions import ActionResult

@dataclass
class VideoSettings:
    """Current video playback settings"""
    resolution: tuple  # (width, height)
    frame_rate: float
    quality: float  # 0.0 to 1.0
    brightness: float  # 0.0 to 1.0
    volume: float  # 0.0 to 1.0

class VideoPlayerDemo:
    """
    Demo video player that can be optimized for battery usage
    Shows how target applications can integrate with the battery optimization system
    """
    
    def __init__(self, name: str = "DemoVideoPlayer"):
        self.name = name
        self.logger = logging.getLogger(__name__)
        
        # Video settings
        self.settings = VideoSettings(
            resolution=(1920, 1080),
            frame_rate=30.0,
            quality=1.0,
            brightness=1.0,
            volume=0.8
        )
        
        # Playback state
        self.playing = False
        self.paused = False
        self.current_frame = 0
        self.total_frames = 0
        
        # Video generation
        self.video_thread = None
        self.stop_flag = False
        
        # Battery optimization state
        self.optimization_history = []
        self.baseline_power_consumption = 15.0  # Simulated watts
        self.current_power_consumption = self.baseline_power_consumption
        
        # Performance metrics
        self.frame_drop_count = 0
        self.avg_frame_time = 0.0
        self.cpu_usage_factor = 1.0
        
        # Callbacks for monitoring
        self.power_callback: Optional[Callable] = None
        self.performance_callback: Optional[Callable] = None
        
        self.logger.info(f"🎥 Video player '{self.name}' initialized")
    
    def set_power_callback(self, callback: Callable[[float], None]):
        """Set callback for power consumption updates"""
        self.power_callback = callback
    
    def set_performance_callback(self, callback: Callable[[Dict], None]):
        """Set callback for performance metric updates"""
        self.performance_callback = callback
    
    def _calculate_power_consumption(self) -> float:
        """Calculate current power consumption based on settings"""
        if not self.playing:
            return 2.0  # Idle power
        
        # Base consumption factors
        resolution_factor = (self.settings.resolution[0] * self.settings.resolution[1]) / (1920 * 1080)
        frame_rate_factor = self.settings.frame_rate / 30.0
        quality_factor = self.settings.quality
        brightness_factor = self.settings.brightness
        
        # Calculate total factor
        total_factor = (
            resolution_factor * 0.4 +
            frame_rate_factor * 0.3 +
            quality_factor * 0.2 +
            brightness_factor * 0.1
        )
        
        power = self.baseline_power_consumption * total_factor
        
        # Add some randomness for realism
        power += np.random.normal(0, 0.5)
        power = max(2.0, power)  # Minimum idle power
        
        return power
    
    def _update_power_consumption(self):
        """Update and report power consumption"""
        self.current_power_consumption = self._calculate_power_consumption()
        
        if self.power_callback:
            self.power_callback(self.current_power_consumption)
    
    def _update_performance_metrics(self):
        """Update and report performance metrics"""
        if not self.playing:
            return
        
        # Simulate performance impact based on optimization level
        base_frame_time = 1.0 / self.settings.frame_rate
        actual_frame_time = base_frame_time * self.cpu_usage_factor
        
        # Calculate metrics
        metrics = {
            'frame_rate': 1.0 / actual_frame_time if actual_frame_time > 0 else 0,
            'target_frame_rate': self.settings.frame_rate,
            'frame_drops': self.frame_drop_count,
            'resolution': self.settings.resolution,
            'quality': self.settings.quality,
            'power_watts': self.current_power_consumption,
            'cpu_usage_factor': self.cpu_usage_factor
        }
        
        if self.performance_callback:
            self.performance_callback(metrics)
    
    def start_playback(self, video_path: Optional[str] = None):
        """Start video playback (or simulation)"""
        if self.playing:
            self.logger.warning("⚠️ Video already playing")
            return
        
        self.playing = True
        self.paused = False
        self.stop_flag = False
        
        # Start video simulation thread
        self.video_thread = threading.Thread(target=self._video_simulation_loop, daemon=True)
        self.video_thread.start()
        
        self.logger.info(f"▶️ Started video playback at {self.settings.resolution[0]}x{self.settings.resolution[1]} @ {self.settings.frame_rate}fps")
    
    def stop_playback(self):
        """Stop video playback"""
        if not self.playing:
            return
        
        self.playing = False
        self.stop_flag = True
        
        if self.video_thread:
            self.video_thread.join(timeout=2.0)
        
        self.logger.info("⏹️ Stopped video playback")
    
    def pause_playback(self):
        """Pause video playback"""
        if self.playing and not self.paused:
            self.paused = True
            self.logger.info("⏸️ Paused video playback")
    
    def resume_playback(self):
        """Resume video playback"""
        if self.playing and self.paused:
            self.paused = False
            self.logger.info("▶️ Resumed video playback")
    
    def _video_simulation_loop(self):
        """Main video simulation loop"""
        self.logger.info("🎬 Video simulation loop started")
        frame_count = 0
        
        while self.playing and not self.stop_flag:
            if self.paused:
                time.sleep(0.1)
                continue
            
            frame_start_time = time.time()
            
            # Simulate frame processing
            self._simulate_frame_processing()
            
            # Update metrics
            self._update_power_consumption()
            self._update_performance_metrics()
            
            # Frame timing
            target_frame_time = 1.0 / self.settings.frame_rate
            actual_frame_time = time.time() - frame_start_time
            
            # Sleep for remaining frame time
            sleep_time = target_frame_time - actual_frame_time
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                # Frame drop
                self.frame_drop_count += 1
            
            frame_count += 1
            self.current_frame = frame_count
            
            # Update average frame time
            self.avg_frame_time = (self.avg_frame_time * 0.9) + (actual_frame_time * 0.1)
        
        self.logger.info("🎬 Video simulation loop stopped")
    
    def _simulate_frame_processing(self):
        """Simulate CPU-intensive frame processing"""
        # Simulate processing load based on current settings
        resolution_pixels = self.settings.resolution[0] * self.settings.resolution[1]
        processing_time = (resolution_pixels / (1920 * 1080)) * self.settings.quality * 0.01
        
        # Apply CPU usage factor from optimizations
        processing_time *= self.cpu_usage_factor
        
        # Simulate work with actual computation
        if processing_time > 0:
            # Create and process a small image to simulate video decoding
            size = min(100, int(np.sqrt(resolution_pixels / 10000)))
            if size > 10:
                frame = np.random.randint(0, 256, (size, size, 3), dtype=np.uint8)
                
                # Apply some processing based on quality
                if self.settings.quality > 0.7:
                    # High quality processing
                    frame = cv2.GaussianBlur(frame, (5, 5), 0)
                    frame = cv2.bilateralFilter(frame, 9, 75, 75)
                elif self.settings.quality > 0.4:
                    # Medium quality processing
                    frame = cv2.GaussianBlur(frame, (3, 3), 0)
                
                # Brightness adjustment
                if self.settings.brightness != 1.0:
                    frame = cv2.convertScaleAbs(frame, alpha=self.settings.brightness, beta=0)
    
    def optimize_for_battery(self, action: OptimizationAction) -> ActionResult:
        """
        Battery optimization callback - this is called by the optimization system
        """
        action_id = f"video_opt_{time.time()}"
        previous_settings = VideoSettings(
            resolution=self.settings.resolution,
            frame_rate=self.settings.frame_rate,
            quality=self.settings.quality,
            brightness=self.settings.brightness,
            volume=self.settings.volume
        )
        
        try:
            if action.action_type == "app_throttle":
                # Reduce video quality and frame rate based on optimization intensity
                optimization_factor = 1.0 - action.intensity
                
                # Adjust settings
                if action.intensity > 0.7:  # Aggressive optimization
                    self.settings.resolution = (1280, 720)  # Reduce to 720p
                    self.settings.frame_rate = max(15.0, self.settings.frame_rate * optimization_factor)
                    self.settings.quality = max(0.3, self.settings.quality * optimization_factor)
                elif action.intensity > 0.4:  # Moderate optimization
                    self.settings.frame_rate = max(20.0, self.settings.frame_rate * optimization_factor)
                    self.settings.quality = max(0.5, self.settings.quality * optimization_factor)
                else:  # Light optimization
                    self.settings.quality = max(0.7, self.settings.quality * optimization_factor)
                
                # Adjust CPU usage factor
                self.cpu_usage_factor = optimization_factor
                
                # Record optimization
                self.optimization_history.append({
                    'action_id': action_id,
                    'timestamp': time.time(),
                    'action': action,
                    'previous_settings': previous_settings,
                    'new_settings': VideoSettings(
                        resolution=self.settings.resolution,
                        frame_rate=self.settings.frame_rate,
                        quality=self.settings.quality,
                        brightness=self.settings.brightness,
                        volume=self.settings.volume
                    )
                })
                
                # Calculate estimated power savings
                old_power = self._calculate_power_with_settings(previous_settings)
                new_power = self._calculate_power_consumption()
                power_savings = ((old_power - new_power) / old_power) * 100
                
                self.logger.info(f"🔋 Applied video optimization: "
                               f"quality={self.settings.quality:.2f}, "
                               f"fps={self.settings.frame_rate:.1f}, "
                               f"estimated savings={power_savings:.1f}%")
                
                return ActionResult(
                    action_id=action_id,
                    success=True,
                    previous_value=f"Quality: {previous_settings.quality:.2f}, FPS: {previous_settings.frame_rate:.1f}",
                    new_value=f"Quality: {self.settings.quality:.2f}, FPS: {self.settings.frame_rate:.1f}",
                    estimated_savings=power_savings,
                    actual_impact=action.performance_impact
                )
            
            else:
                return ActionResult(
                    action_id=action_id,
                    success=False,
                    error_message=f"Unknown optimization action: {action.action_type}"
                )
                
        except Exception as e:
            self.logger.error(f"❌ Video optimization error: {e}")
            return ActionResult(
                action_id=action_id,
                success=False,
                error_message=str(e)
            )
    
    def _calculate_power_with_settings(self, settings: VideoSettings) -> float:
        """Calculate power consumption with specific settings"""
        old_settings = self.settings
        self.settings = settings
        power = self._calculate_power_consumption()
        self.settings = old_settings
        return power
    
    def revert_optimization(self, action_id: str) -> ActionResult:
        """Revert a specific optimization"""
        # Find optimization in history
        optimization = None
        for opt in self.optimization_history:
            if opt['action_id'] == action_id:
                optimization = opt
                break
        
        if not optimization:
            return ActionResult(
                action_id=action_id,
                success=False,
                error_message="Optimization not found in history"
            )
        
        try:
            # Restore previous settings
            prev_settings = optimization['previous_settings']
            self.settings = VideoSettings(
                resolution=prev_settings.resolution,
                frame_rate=prev_settings.frame_rate,
                quality=prev_settings.quality,
                brightness=prev_settings.brightness,
                volume=prev_settings.volume
            )
            
            # Reset CPU usage factor
            self.cpu_usage_factor = 1.0
            
            # Remove from history
            self.optimization_history.remove(optimization)
            
            self.logger.info(f"🔄 Reverted video optimization: {action_id}")
            
            return ActionResult(
                action_id=action_id,
                success=True,
                new_value=f"Quality: {self.settings.quality:.2f}, FPS: {self.settings.frame_rate:.1f}"
            )
            
        except Exception as e:
            return ActionResult(
                action_id=action_id,
                success=False,
                error_message=str(e)
            )
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current video player statistics"""
        return {
            'playing': self.playing,
            'paused': self.paused,
            'settings': {
                'resolution': f"{self.settings.resolution[0]}x{self.settings.resolution[1]}",
                'frame_rate': self.settings.frame_rate,
                'quality': self.settings.quality,
                'brightness': self.settings.brightness,
                'volume': self.settings.volume
            },
            'performance': {
                'current_frame': self.current_frame,
                'frame_drops': self.frame_drop_count,
                'avg_frame_time': self.avg_frame_time,
                'power_consumption': self.current_power_consumption,
                'cpu_usage_factor': self.cpu_usage_factor
            },
            'optimizations_applied': len(self.optimization_history)
        }
    
    def reset_to_defaults(self):
        """Reset video settings to defaults"""
        self.settings = VideoSettings(
            resolution=(1920, 1080),
            frame_rate=30.0,
            quality=1.0,
            brightness=1.0,
            volume=0.8
        )
        self.cpu_usage_factor = 1.0
        self.optimization_history.clear()
        self.frame_drop_count = 0
        
        self.logger.info("🔄 Reset video player to default settings")

# Utility function to create test video content
def create_test_video(output_path: str, duration: int = 60, fps: int = 30):
    """Create a test video file for demonstration"""
    try:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (1920, 1080))
        
        total_frames = duration * fps
        
        for frame_num in range(total_frames):
            # Create colorful test pattern
            frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
            
            # Moving gradient
            t = frame_num / total_frames
            color1 = (int(127 * (1 + np.sin(t * 2 * np.pi))), 100, 200)
            color2 = (100, int(127 * (1 + np.cos(t * 2 * np.pi))), 150)
            
            for y in range(1080):
                mix = y / 1080
                color = tuple(int(c1 * (1 - mix) + c2 * mix) for c1, c2 in zip(color1, color2))
                frame[y, :] = color
            
            # Add some text
            text = f"Frame {frame_num + 1}/{total_frames} - Battery Optimization Demo"
            cv2.putText(frame, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            out.write(frame)
        
        out.release()
        print(f"✅ Created test video: {output_path}")
        
    except Exception as e:
        print(f"❌ Error creating test video: {e}")

# Example usage and testing
if __name__ == "__main__":
    import signal
    import logging
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create video player
    player = VideoPlayerDemo("TestVideoPlayer")
    
    # Set up monitoring callbacks
    def power_monitor(power_watts):
        print(f"⚡ Power consumption: {power_watts:.1f}W")
    
    def performance_monitor(metrics):
        print(f"📊 FPS: {metrics['frame_rate']:.1f}/{metrics['target_frame_rate']:.1f}, "
              f"Quality: {metrics['quality']:.2f}, Drops: {metrics['frame_drops']}")
    
    player.set_power_callback(power_monitor)
    player.set_performance_callback(performance_monitor)
    
    # Start playback
    player.start_playback()
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print("\n🛑 Stopping video player...")
        player.stop_playback()
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print("🎥 Video player running... Press Ctrl+C to stop")
        print("📊 Monitoring power consumption and performance...")
        
        # Simulate battery optimization after 10 seconds
        time.sleep(10)
        print("\n🔋 Simulating battery optimization...")
        
        # Create optimization action
        test_action = OptimizationAction(
            action_type='app_throttle',
            intensity=0.6,
            target_component='video_player',
            estimated_savings=15.0,
            performance_impact=0.4,
            confidence=0.8
        )
        
        result = player.optimize_for_battery(test_action)
        print(f"Optimization result: {result}")
        
        # Run optimized for 20 seconds
        time.sleep(20)
        
        # Revert optimization
        print("\n🔄 Reverting optimization...")
        revert_result = player.revert_optimization(result.action_id)
        print(f"Revert result: {revert_result}")
        
        # Continue running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        player.stop_playback()
