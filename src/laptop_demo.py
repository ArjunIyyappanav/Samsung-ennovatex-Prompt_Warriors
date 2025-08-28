#!/usr/bin/env python3
"""
Laptop-specific demo for visual battery optimization results
"""

import sys
import time
import psutil
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from core.monitoring import SystemMonitor
from core.reasoning import BatteryOptimizationAgent
from core.actions import OptimizationActuator
from demo_app.video_player import VideoPlayerDemo

class LaptopDemo:
    """Laptop-specific demonstration with visual feedback"""
    
    def __init__(self):
        print("💻 LAPTOP BATTERY OPTIMIZATION DEMO")
        print("=" * 60)
        print("🔋 For best results:")
        print("   1. UNPLUG your laptop charger")
        print("   2. Set screen brightness to 80-100%")
        print("   3. Close unnecessary programs")
        print("   4. Watch REAL optimizations happen!")
        print()
        
        confirm = input("📱 Is your laptop unplugged and ready? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("⚠️ Please unplug charger for realistic testing")
            return
        
        self.monitor = SystemMonitor()
        self.agent = BatteryOptimizationAgent()
        self.actuator = OptimizationActuator()
        self.video_player = VideoPlayerDemo()
        
        print("\n✅ System initialized - Starting real laptop demo!")
    
    def show_current_laptop_state(self):
        """Show current laptop battery and power state"""
        print("\n📊 CURRENT LAPTOP STATE")
        print("-" * 40)
        
        battery = psutil.sensors_battery()
        metrics = self.monitor.collect_metrics()
        
        if battery:
            print(f"🔋 Battery: {battery.percent:.1f}%")
            print(f"⚡ Plugged In: {'Yes' if battery.power_plugged else 'No (GOOD!)'}")
            if not battery.power_plugged:
                hours_left = battery.secsleft / 3600 if battery.secsleft != psutil.POWER_TIME_UNLIMITED else "Unknown"
                if isinstance(hours_left, float):
                    print(f"⏰ Time Remaining: {hours_left:.1f} hours")
        
        print(f"💻 CPU: {metrics.cpu_percent:.1f}%")
        print(f"💾 Memory: {metrics.memory_percent:.1f}%")
        print(f"💡 Screen Brightness: {metrics.screen_brightness}%")
        print(f"⚡ Power Draw: {metrics.battery_power_draw:.1f}W")
        
        return battery, metrics
    
    def run_visual_battery_test(self):
        """Run test with visual feedback on laptop"""
        print("\n🎬 VISUAL BATTERY OPTIMIZATION TEST")
        print("=" * 50)
        print("Watch your laptop screen brightness and performance change!")
        
        battery, initial_metrics = self.show_current_laptop_state()
        
        if not battery or battery.power_plugged:
            print("⚠️ Warning: Laptop appears to be plugged in")
            print("   Unplug for realistic battery optimization demo")
        
        print(f"\n🔍 Monitoring every 10 seconds for 2 minutes...")
        print("💡 You should see ACTUAL changes to your laptop!")
        
        for cycle in range(12):  # 2 minutes of monitoring
            print(f"\n--- Cycle {cycle + 1}/12 ---")
            
            battery, metrics = self.show_current_laptop_state()
            
            # Get optimization decisions
            actions = self.agent.decide_optimization(metrics)
            
            if actions:
                print(f"\n🤖 APPLYING {len(actions)} REAL OPTIMIZATIONS:")
                
                # Apply actual optimizations
                results = self.actuator.apply_actions(actions)
                
                for i, (action, result) in enumerate(zip(actions, results), 1):
                    if result.success:
                        print(f"   ✅ {i}. {action.action_type}")
                        print(f"      Intensity: {action.intensity:.2f}")
                        print(f"      Expected Savings: {action.estimated_savings:.1f}%")
                        
                        if action.action_type == "brightness_adjust":
                            print(f"      👀 WATCH: Your screen should get dimmer!")
                        elif action.action_type == "cpu_throttle":
                            print(f"      🐌 CPU frequency reduced for power savings")
                        
                    else:
                        print(f"   ❌ {i}. {action.action_type} - {result.error_message}")
                
                # Show the impact
                print(f"\n📈 OPTIMIZATION IMPACT:")
                successful_optimizations = [r for r in results if r.success]
                if successful_optimizations:
                    total_savings = sum(action.estimated_savings for action, result in zip(actions, results) if result.success)
                    print(f"   💡 Applied {len(successful_optimizations)} optimizations")
                    print(f"   🔋 Estimated battery extension: {total_savings:.1f}%")
                    print(f"   👀 VISUAL: Check if screen brightness changed!")
                
            else:
                print(f"\n✅ No optimizations needed - laptop is efficient")
            
            time.sleep(10)
    
    def run_video_streaming_laptop_test(self):
        """Test video streaming with real optimizations"""
        print("\n🎥 LAPTOP VIDEO STREAMING TEST")
        print("=" * 50)
        print("Starting video player - watch real optimizations!")
        
        # Start video player
        self.video_player.start_playback()
        
        try:
            for minute in range(3):  # 3 minutes of video
                print(f"\n🎥 Video Minute {minute + 1}/3")
                
                battery, metrics = self.show_current_laptop_state()
                
                # Get current video stats
                video_stats = self.video_player.get_current_stats()
                print(f"📺 Video Quality: {video_stats['settings']['quality']:.2f}")
                print(f"📺 Resolution: {video_stats['settings']['resolution']}")
                print(f"📺 Frame Rate: {video_stats['settings']['frame_rate']} fps")
                print(f"📺 Power: {video_stats['performance']['power_consumption']:.1f}W")
                
                # Get optimizations
                actions = self.agent.decide_optimization(metrics)
                
                if actions:
                    # Apply optimizations including video-specific ones
                    results = self.actuator.apply_actions(actions)
                    
                    # Check for video optimizations
                    video_actions = [a for a in actions if a.action_type == 'app_throttle']
                    if video_actions:
                        video_action = video_actions[0]
                        video_result = self.video_player.optimize_for_battery(video_action)
                        
                        if video_result.success:
                            new_stats = self.video_player.get_current_stats()
                            print(f"\n🎥 VIDEO OPTIMIZATION APPLIED:")
                            print(f"   Quality: {video_stats['settings']['quality']:.2f} → {new_stats['settings']['quality']:.2f}")
                            print(f"   Resolution: {video_stats['settings']['resolution']} → {new_stats['settings']['resolution']}")
                            print(f"   Frame Rate: {video_stats['settings']['frame_rate']} → {new_stats['settings']['frame_rate']} fps")
                            print(f"   👀 WATCH: Video quality should be lower but still watchable!")
                
                time.sleep(20)  # 20 seconds per "minute"
                
        finally:
            self.video_player.stop_playback()
            print("\n🎥 Video streaming test complete!")
    
    def show_before_after_comparison(self):
        """Show before/after comparison"""
        print("\n📊 BEFORE/AFTER COMPARISON")
        print("=" * 50)
        
        print("BEFORE optimization:")
        battery_before, metrics_before = self.show_current_laptop_state()
        
        print(f"\nApplying optimizations...")
        actions = self.agent.decide_optimization(metrics_before)
        
        if actions:
            results = self.actuator.apply_actions(actions)
            time.sleep(3)  # Wait for changes to take effect
            
            print(f"\nAFTER optimization:")
            battery_after, metrics_after = self.show_current_laptop_state()
            
            print(f"\n📈 CHANGES:")
            if metrics_before.screen_brightness != metrics_after.screen_brightness:
                print(f"   💡 Brightness: {metrics_before.screen_brightness}% → {metrics_after.screen_brightness}%")
            if abs(metrics_before.cpu_percent - metrics_after.cpu_percent) > 2:
                print(f"   💻 CPU: {metrics_before.cpu_percent:.1f}% → {metrics_after.cpu_percent:.1f}%")
            if abs(metrics_before.battery_power_draw - metrics_after.battery_power_draw) > 0.5:
                print(f"   ⚡ Power: {metrics_before.battery_power_draw:.1f}W → {metrics_after.battery_power_draw:.1f}W")
        
        else:
            print("No optimizations applied - system already efficient")

def main():
    demo = LaptopDemo()
    
    print("\n💻 LAPTOP DEMO OPTIONS:")
    print("1. 🔋 Real-time Battery Monitoring (2 minutes)")
    print("2. 🎥 Video Streaming Test (3 minutes)")
    print("3. 📊 Before/After Comparison")
    print("4. 🌐 Web Dashboard + Manual Testing")
    print("5. ❌ Exit")
    
    choice = input("\nSelect option (1-5): ").strip()
    
    if choice == "1":
        demo.run_visual_battery_test()
    elif choice == "2":
        demo.run_video_streaming_laptop_test()
    elif choice == "3":
        demo.show_before_after_comparison()
    elif choice == "4":
        print("🌐 Starting web dashboard...")
        print("📊 Open http://localhost:5000 in your browser")
        print("💻 Then try these on your laptop:")
        print("   • Stream a video")
        print("   • Open many browser tabs") 
        print("   • Use photo editing software")
        print("   • Watch the dashboard show optimizations!")
        
        # Start full system
        from core.agent_controller import AgentController
        from dashboard.web_dashboard import WebDashboard
        
        controller = AgentController()
        controller.start()
        
        dashboard = WebDashboard(controller)
        dashboard.start(threaded=True)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            controller.stop()
    
    elif choice == "5":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
