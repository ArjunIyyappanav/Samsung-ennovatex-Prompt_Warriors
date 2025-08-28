#!/usr/bin/env python3
"""
Real-world testing of battery optimization system
Creates actual system load and monitors optimization responses
"""

import sys
import time
import threading
import multiprocessing
import psutil
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from core.monitoring import SystemMonitor
from core.reasoning import BatteryOptimizationAgent
from core.actions import OptimizationActuator
from core.agent_controller import AgentController

class RealSystemTester:
    """Test the system with real CPU/memory loads"""
    
    def __init__(self):
        print("🔋 REAL SYSTEM BATTERY OPTIMIZATION TEST")
        print("=" * 60)
        
        # Initialize the full system
        self.controller = AgentController()
        self.stress_threads = []
        self.monitoring = True
        
    def create_cpu_load(self, intensity=0.5, duration=30):
        """Create real CPU load to trigger optimizations"""
        print(f"💻 Creating {intensity*100:.0f}% CPU load for {duration} seconds...")
        
        def cpu_stress():
            end_time = time.time() + duration
            while time.time() < end_time and self.monitoring:
                # CPU-intensive calculation
                for _ in range(int(10000 * intensity)):
                    _ = sum(i*i for i in range(1000))
                time.sleep(0.01)  # Small break to control intensity
        
        # Start multiple threads based on CPU cores
        num_threads = max(1, int(multiprocessing.cpu_count() * intensity))
        for _ in range(num_threads):
            thread = threading.Thread(target=cpu_stress, daemon=True)
            thread.start()
            self.stress_threads.append(thread)
    
    def create_memory_load(self, size_mb=500):
        """Create memory pressure"""
        print(f"💾 Creating {size_mb}MB memory load...")
        
        def memory_stress():
            # Allocate memory
            memory_hog = []
            for _ in range(size_mb):
                # Allocate 1MB chunks
                chunk = bytearray(1024 * 1024)
                memory_hog.append(chunk)
                time.sleep(0.01)
            
            # Hold memory for a while
            time.sleep(30)
            del memory_hog
        
        thread = threading.Thread(target=memory_stress, daemon=True)
        thread.start()
        self.stress_threads.append(thread)
    
    def monitor_real_optimization(self, duration=60):
        """Monitor system and show real optimization decisions"""
        print(f"📊 Monitoring real system for {duration} seconds...")
        print("Watch the agent make decisions based on actual system load!")
        print("-" * 60)
        
        start_time = time.time()
        cycle = 0
        
        while time.time() - start_time < duration:
            cycle += 1
            
            # Get real system metrics
            current_metrics = self.controller.monitor.get_current_metrics()
            if not current_metrics:
                time.sleep(2)
                continue
            
            # Show current state
            print(f"\n🔍 Cycle {cycle} - Real System State:")
            print(f"   📊 CPU: {current_metrics.cpu_percent:.1f}%")
            print(f"   💾 Memory: {current_metrics.memory_percent:.1f}%")
            print(f"   🔋 Battery: {current_metrics.battery_percent:.1f}%")
            print(f"   ⚡ Power: {current_metrics.battery_power_draw:.1f}W")
            print(f"   💡 Brightness: {current_metrics.screen_brightness}%")
            
            # Get agent decisions
            actions = self.controller.agent.decide_optimization(current_metrics)
            
            if actions:
                print(f"   🤖 Agent Response: {len(actions)} optimization(s) triggered!")
                
                total_savings = 0
                for i, action in enumerate(actions, 1):
                    print(f"      {i}. {action.action_type}")
                    print(f"         Intensity: {action.intensity:.2f}")
                    print(f"         Savings: {action.estimated_savings:.1f}%")
                    print(f"         Confidence: {action.confidence:.2f}")
                    total_savings += action.estimated_savings
                
                print(f"   💡 Total Potential Savings: {total_savings:.1f}%")
                
                # Actually apply optimizations to see real impact
                results = self.controller.actuator.apply_actions(actions)
                successful = [r for r in results if r.success]
                print(f"   ✅ Applied {len(successful)}/{len(actions)} optimizations")
                
            else:
                print(f"   ✅ No optimizations needed - system is efficient")
            
            time.sleep(5)  # Check every 5 seconds
    
    def run_stress_test_scenario(self):
        """Run a complete stress test scenario"""
        print("\n🚀 STARTING REAL STRESS TEST SCENARIO")
        print("=" * 60)
        
        # Start the agent system
        self.controller.start()
        time.sleep(2)
        
        try:
            # Phase 1: Normal operation
            print("\n📈 PHASE 1: Normal Operation (10 seconds)")
            self.monitor_real_optimization(10)
            
            # Phase 2: Create CPU stress
            print("\n📈 PHASE 2: High CPU Load (20 seconds)")
            self.create_cpu_load(intensity=0.7, duration=20)
            self.monitor_real_optimization(20)
            
            # Phase 3: Add memory pressure
            print("\n📈 PHASE 3: CPU + Memory Load (20 seconds)")
            self.create_memory_load(size_mb=300)
            self.monitor_real_optimization(20)
            
            # Phase 4: Cool down
            print("\n📈 PHASE 4: Cool Down (10 seconds)")
            self.monitoring = False  # Stop stress threads
            self.monitor_real_optimization(10)
            
        except KeyboardInterrupt:
            print("\n🛑 Test interrupted by user")
        
        finally:
            # Clean up
            self.monitoring = False
            self.controller.stop()
            print("\n✅ Test completed")
    
    def show_live_dashboard_instructions(self):
        """Show how to use the web dashboard for real testing"""
        print("\n🌐 LIVE WEB DASHBOARD TESTING")
        print("=" * 60)
        print("1. Open your browser to: http://localhost:5000")
        print("2. You'll see REAL-TIME metrics updating")
        print("3. Open multiple browser tabs or run intensive programs")
        print("4. Watch the dashboard show:")
        print("   • CPU/Memory usage increase")
        print("   • Agent making optimization decisions")
        print("   • Battery optimization recommendations")
        print("5. Try these real activities:")
        print("   • Open 20+ browser tabs")
        print("   • Stream a video")
        print("   • Run a game or intensive program")
        print("   • Use photo/video editing software")
        print("\n💡 The agent will automatically detect the load and optimize!")

def main():
    """Main testing function"""
    tester = RealSystemTester()
    
    print("Choose your test method:")
    print("1. 🔥 Automated Stress Test (Creates real CPU/Memory load)")
    print("2. 🌐 Web Dashboard + Manual Testing")
    print("3. 📊 Monitor Current System Only")
    print("4. ❌ Exit")
    
    try:
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            print("\n⚠️ WARNING: This will create real system load!")
            print("Your CPU usage will increase significantly for testing.")
            confirm = input("Continue? (y/N): ").strip().lower()
            
            if confirm in ['y', 'yes']:
                tester.run_stress_test_scenario()
            else:
                print("Test cancelled")
        
        elif choice == "2":
            tester.show_live_dashboard_instructions()
            tester.controller.start()
            
            # Start web dashboard
            from dashboard.web_dashboard import WebDashboard
            dashboard = WebDashboard(tester.controller)
            dashboard.start(threaded=True)
            
            print("\n📊 System running with web dashboard...")
            print("Press Ctrl+C to stop")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping system...")
                tester.controller.stop()
        
        elif choice == "3":
            tester.controller.start()
            print("\n📊 Monitoring current system state...")
            print("Press Ctrl+C to stop")
            
            try:
                tester.monitor_real_optimization(300)  # 5 minutes
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped")
                tester.controller.stop()
        
        elif choice == "4":
            print("👋 Goodbye!")
        
        else:
            print("❌ Invalid choice")
    
    except KeyboardInterrupt:
        print("\n👋 Test interrupted")

if __name__ == "__main__":
    main()
