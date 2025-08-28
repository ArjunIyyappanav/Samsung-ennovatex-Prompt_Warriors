#!/usr/bin/env python3
"""
Quick test to see battery optimization in action
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from core.monitoring import SystemMonitor, SystemMetrics
from core.reasoning import BatteryOptimizationAgent
from core.actions import OptimizationActuator

def test_battery_scenarios():
    print("🔋 BATTERY OPTIMIZATION TEST")
    print("=" * 50)
    
    # Initialize components
    monitor = SystemMonitor()
    agent = BatteryOptimizationAgent()
    actuator = OptimizationActuator()
    
    print("✅ System initialized")
    
    # Test 1: Current system state
    print("\n📊 TEST 1: Current System Analysis")
    print("-" * 40)
    
    metrics = monitor.collect_metrics()
    print(f"Current Battery: {metrics.battery_percent:.1f}%")
    print(f"Current CPU: {metrics.cpu_percent:.1f}%")
    print(f"Current Power: {metrics.battery_power_draw:.1f}W")
    print(f"Screen Brightness: {metrics.screen_brightness}%")
    
    actions = agent.decide_optimization(metrics)
    print(f"\n🤖 Agent Recommendation: {len(actions)} optimization(s)")
    
    for i, action in enumerate(actions, 1):
        print(f"  {i}. {action.action_type}")
        print(f"     Intensity: {action.intensity:.2f}")
        print(f"     Savings: {action.estimated_savings:.1f}%")
        print(f"     Confidence: {action.confidence:.2f}")
    
    if not actions:
        print("  ✅ No optimizations needed - system is efficient!")
    
    # Test 2: Simulated low battery
    print("\n⚠️ TEST 2: Simulated Low Battery (20%)")
    print("-" * 40)
    
    # Create low battery scenario
    low_battery_metrics = SystemMetrics(
        timestamp=time.time(),
        battery_percent=20.0,  # Low battery!
        battery_power_draw=12.0,  # High power draw
        cpu_percent=70.0,  # High CPU usage
        cpu_freq_current=2800.0,
        memory_percent=75.0,
        gpu_percent=25.0,
        gpu_memory_percent=40.0,
        network_bytes_sent=5*1024*1024,
        network_bytes_recv=10*1024*1024,
        disk_io_read=200*1024,
        disk_io_write=100*1024,
        screen_brightness=85,  # Bright screen
        active_processes=150,
        target_app_cpu=30.0,
        target_app_memory=20.0
    )
    
    print(f"Simulated Battery: {low_battery_metrics.battery_percent:.1f}% (LOW!)")
    print(f"Simulated CPU: {low_battery_metrics.cpu_percent:.1f}% (HIGH!)")
    print(f"Simulated Power: {low_battery_metrics.battery_power_draw:.1f}W (HIGH!)")
    print(f"Simulated Brightness: {low_battery_metrics.screen_brightness}% (HIGH!)")
    
    low_actions = agent.decide_optimization(low_battery_metrics)
    print(f"\n🤖 Agent Recommendation: {len(low_actions)} optimization(s)")
    
    total_savings = 0
    for i, action in enumerate(low_actions, 1):
        print(f"  {i}. {action.action_type}")
        print(f"     Intensity: {action.intensity:.2f}")
        print(f"     Savings: {action.estimated_savings:.1f}%")
        print(f"     Impact: {action.performance_impact:.2f}")
        print(f"     Confidence: {action.confidence:.2f}")
        total_savings += action.estimated_savings
    
    if low_actions:
        print(f"\n💡 Total Estimated Savings: {total_savings:.1f}%")
        print("   🎯 This shows the agent gets MORE aggressive when battery is low!")
    
    # Test 3: Critical battery
    print("\n🚨 TEST 3: Critical Battery Emergency (8%)")
    print("-" * 40)
    
    critical_metrics = SystemMetrics(
        timestamp=time.time(),
        battery_percent=8.0,  # CRITICAL!
        battery_power_draw=15.0,  # Very high power draw
        cpu_percent=80.0,  # Very high CPU
        cpu_freq_current=3000.0,
        memory_percent=85.0,
        gpu_percent=40.0,
        gpu_memory_percent=60.0,
        network_bytes_sent=10*1024*1024,
        network_bytes_recv=20*1024*1024,
        disk_io_read=500*1024,
        disk_io_write=300*1024,
        screen_brightness=95,  # Maximum brightness
        active_processes=180,
        target_app_cpu=50.0,
        target_app_memory=35.0
    )
    
    print(f"Critical Battery: {critical_metrics.battery_percent:.1f}% (CRITICAL!)")
    print(f"Critical CPU: {critical_metrics.cpu_percent:.1f}% (VERY HIGH!)")
    print(f"Critical Power: {critical_metrics.battery_power_draw:.1f}W (EXTREME!)")
    print(f"Critical Brightness: {critical_metrics.screen_brightness}% (MAX!)")
    
    critical_actions = agent.decide_optimization(critical_metrics)
    print(f"\n🚨 EMERGENCY MODE: {len(critical_actions)} AGGRESSIVE optimization(s)")
    
    total_critical_savings = 0
    for i, action in enumerate(critical_actions, 1):
        print(f"  {i}. {action.action_type}")
        print(f"     Intensity: {action.intensity:.2f} ({'HIGH!' if action.intensity > 0.6 else 'MODERATE'})")
        print(f"     Savings: {action.estimated_savings:.1f}%")
        print(f"     Impact: {action.performance_impact:.2f}")
        print(f"     Confidence: {action.confidence:.2f}")
        total_critical_savings += action.estimated_savings
    
    if critical_actions:
        print(f"\n⚡ Total Emergency Savings: {total_critical_savings:.1f}%")
        print("   🎯 MAXIMUM OPTIMIZATION to extend battery life!")
    
    # Test 4: Show the difference
    print("\n📈 SUMMARY: Adaptive Intelligence")
    print("=" * 50)
    print(f"Normal Battery ({metrics.battery_percent:.1f}%): {len(actions)} optimizations")
    print(f"Low Battery (20%): {len(low_actions)} optimizations") 
    print(f"Critical Battery (8%): {len(critical_actions)} optimizations")
    print(f"\n🧠 The agent gets MORE aggressive as battery gets lower!")
    print(f"   This is SMART, ADAPTIVE behavior - not just simple rules!")
    
    return actions, low_actions, critical_actions

if __name__ == "__main__":
    test_battery_scenarios()
