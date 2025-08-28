#!/usr/bin/env python3
"""
Real-Time Video Quality Optimization Demo
Shows instant video quality changes as battery drops
"""

import time
import threading
from demo_app.video_player import VideoPlayerDemo
from core.reasoning import OptimizationAction

def print_separator():
    print("=" * 60)

def print_video_status(player):
    """Print current video status"""
    stats = player.get_current_stats()
    settings = stats['settings']
    performance = stats['performance']
    
    print(f"📺 Resolution: {settings['resolution']}")
    print(f"🎬 Frame Rate: {settings['frame_rate']:.1f} fps")
    print(f"🎨 Quality: {settings['quality']:.2f} (1.00 = maximum)")
    print(f"⚡ Power: {performance['power_consumption']:.1f}W")
    print(f"🎯 Optimizations Applied: {stats['optimizations_applied']}")

def simulate_battery_optimization(player):
    """Simulate battery optimization scenarios"""
    
    print("🎥 Starting Video Player...")
    player.start_playback()
    time.sleep(2)
    
    print("\n📊 INITIAL STATE (Good Battery)")
    print_separator()
    print_video_status(player)
    
    # Let it run for a few seconds
    print("\n⏳ Playing video normally for 5 seconds...")
    time.sleep(5)
    
    # Simulate low battery - moderate optimization
    print("\n🟡 SIMULATING LOW BATTERY (20%)")
    print_separator()
    print("🤖 AI Decision: Apply moderate video optimization...")
    
    moderate_action = OptimizationAction(
        action_type='app_throttle',
        intensity=0.4,  # Moderate optimization
        target_component='video_player',
        estimated_savings=15.0,
        performance_impact=0.3,
        confidence=0.8
    )
    
    result = player.optimize_for_battery(moderate_action)
    print(f"✅ Optimization applied: {result.action_id}")
    
    print("\n📊 AFTER MODERATE OPTIMIZATION")
    print_separator()
    print_video_status(player)
    
    # Let it run optimized
    print("\n⏳ Running with moderate optimization for 8 seconds...")
    time.sleep(8)
    
    # Simulate critical battery - aggressive optimization
    print("\n🔴 SIMULATING CRITICAL BATTERY (8%)")
    print_separator()
    print("🚨 AI Decision: Apply AGGRESSIVE video optimization...")
    
    aggressive_action = OptimizationAction(
        action_type='app_throttle',
        intensity=0.8,  # Aggressive optimization
        target_component='video_player',
        estimated_savings=35.0,
        performance_impact=0.6,
        confidence=0.9
    )
    
    result2 = player.optimize_for_battery(aggressive_action)
    print(f"✅ Aggressive optimization applied: {result2.action_id}")
    
    print("\n📊 AFTER AGGRESSIVE OPTIMIZATION")
    print_separator()
    print_video_status(player)
    
    # Let it run in crisis mode
    print("\n⏳ Running in battery-saving mode for 8 seconds...")
    time.sleep(8)
    
    # Recovery - battery plugged in
    print("\n🔌 SIMULATING POWER PLUGGED IN")
    print_separator()
    print("🔄 AI Decision: Restore video quality...")
    
    print(f"🔄 Reverting aggressive optimization...")
    revert_result = player.revert_optimization(result2.action_id)
    print(f"✅ Reverted: {revert_result.action_id}")
    
    time.sleep(2)
    
    print(f"🔄 Reverting moderate optimization...")
    revert_result2 = player.revert_optimization(result.action_id)
    print(f"✅ Reverted: {revert_result2.action_id}")
    
    print("\n📊 FINAL STATE (Quality Restored)")
    print_separator()
    print_video_status(player)
    
    print("\n⏳ Running restored quality for 5 seconds...")
    time.sleep(5)
    
    player.stop_playback()
    print("\n✅ Demo completed!")

def main():
    print("🚀 REAL-TIME VIDEO OPTIMIZATION DEMO")
    print("=" * 60)
    print("This demo shows how the AI automatically reduces video")
    print("quality to save battery as power levels drop!")
    print("=" * 60)
    
    # Create video player
    player = VideoPlayerDemo("OptimizationDemo")
    
    try:
        simulate_battery_optimization(player)
        
        print("\n🎯 SUMMARY:")
        print("=" * 60)
        print("✅ Normal Battery: Full 1080p @ 30fps, Quality 1.00")
        print("🟡 Low Battery: Reduced quality to 0.60, same resolution")
        print("🔴 Critical Battery: 720p @ 15fps, Quality 0.20")
        print("🔌 Plugged In: Restored to full quality")
        print("=" * 60)
        print("💡 This demonstrates intelligent, adaptive video optimization!")
        
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped by user")
        player.stop_playback()

if __name__ == "__main__":
    main()
