"""
System Monitoring Layer - Sensors for battery, CPU, network, and application metrics
"""

import psutil
import time
import threading
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Callable
from collections import deque
import json
import platform

# Try to import GPU monitoring (optional)
try:
    import pynvml
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

@dataclass
class SystemMetrics:
    """Container for system metrics"""
    timestamp: float
    battery_percent: float
    battery_power_draw: float  # Watts
    cpu_percent: float
    cpu_freq_current: float
    memory_percent: float
    gpu_percent: float
    gpu_memory_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    disk_io_read: int
    disk_io_write: int
    screen_brightness: int
    active_processes: int
    target_app_cpu: float
    target_app_memory: float

class SystemMonitor:
    """Real-time system monitoring with lightweight sensors"""
    
    def __init__(self, update_interval: float = 1.0):
        self.logger = logging.getLogger(__name__)
        self.update_interval = update_interval
        self.running = False
        self.monitor_thread = None
        
        # Data storage
        self.metrics_history = deque(maxlen=1000)  # Keep last 1000 readings
        self.current_metrics = None
        
        # Callbacks for real-time notifications
        self.callbacks: List[Callable[[SystemMetrics], None]] = []
        
        # Initialize GPU monitoring if available
        self.gpu_initialized = False
        if GPU_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self.gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                self.gpu_initialized = True
                self.logger.info("✅ GPU monitoring initialized")
            except Exception as e:
                self.logger.warning(f"⚠️  GPU monitoring not available: {e}")
        
        # Platform-specific initialization
        self.platform = platform.system().lower()
        self._init_platform_specific()
        
        # Baseline measurements for delta calculations
        self.baseline_net = psutil.net_io_counters()
        self.baseline_disk = psutil.disk_io_counters()
        
    def _init_platform_specific(self):
        """Initialize platform-specific monitoring capabilities"""
        if self.platform == "windows":
            self.logger.info("🖥️ Windows monitoring mode")
            # Windows-specific battery monitoring
        elif self.platform == "linux":
            self.logger.info("🐧 Linux monitoring mode")
            # Linux-specific power monitoring via /sys/class/power_supply/
        else:
            self.logger.info(f"🔧 Generic monitoring mode for {self.platform}")
    
    def add_callback(self, callback: Callable[[SystemMetrics], None]):
        """Add callback for real-time metric updates"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[SystemMetrics], None]):
        """Remove callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def _get_battery_info(self) -> tuple[float, float]:
        """Get battery percentage and power draw"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                # Estimate power draw based on battery drain rate
                percent = battery.percent
                # Simple estimation - actual implementation would need platform-specific APIs
                power_draw = 10.0 if not battery.power_plugged else 5.0  # Watts estimate
                return percent, power_draw
            else:
                # Simulated battery for desktop systems
                return 85.0, 8.0
        except Exception as e:
            self.logger.warning(f"Battery monitoring error: {e}")
            return 50.0, 10.0
    
    def _get_gpu_info(self) -> tuple[float, float]:
        """Get GPU utilization and memory usage"""
        if not self.gpu_initialized:
            return 0.0, 0.0
        
        try:
            util = pynvml.nvmlDeviceGetUtilizationRates(self.gpu_handle)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(self.gpu_handle)
            gpu_percent = util.gpu
            gpu_memory_percent = (mem_info.used / mem_info.total) * 100
            return gpu_percent, gpu_memory_percent
        except Exception as e:
            self.logger.warning(f"GPU monitoring error: {e}")
            return 0.0, 0.0
    
    def _get_screen_brightness(self) -> int:
        """Get current screen brightness (0-100)"""
        # Platform-specific implementation needed
        # For demo purposes, return simulated value
        try:
            if self.platform == "windows":
                # Would use Windows API for actual brightness
                return 75
            elif self.platform == "linux":
                # Would read from /sys/class/backlight/
                return 80
            else:
                return 70
        except Exception:
            return 50
    
    def _get_target_app_metrics(self, app_name: str = "python") -> tuple[float, float]:
        """Get CPU and memory usage of target application"""
        try:
            target_cpu = 0.0
            target_memory = 0.0
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    if app_name.lower() in proc.info['name'].lower():
                        target_cpu += proc.info['cpu_percent'] or 0.0
                        target_memory += proc.info['memory_percent'] or 0.0
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return target_cpu, target_memory
        except Exception as e:
            self.logger.warning(f"Target app monitoring error: {e}")
            return 0.0, 0.0
    
    def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        timestamp = time.time()
        
        # Battery metrics
        battery_percent, battery_power_draw = self._get_battery_info()
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_freq = psutil.cpu_freq()
        cpu_freq_current = cpu_freq.current if cpu_freq else 0.0
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # GPU metrics
        gpu_percent, gpu_memory_percent = self._get_gpu_info()
        
        # Network metrics
        net_io = psutil.net_io_counters()
        net_sent = net_io.bytes_sent - self.baseline_net.bytes_sent
        net_recv = net_io.bytes_recv - self.baseline_net.bytes_recv
        
        # Disk I/O metrics
        disk_io = psutil.disk_io_counters()
        if disk_io:
            disk_read = disk_io.read_bytes - self.baseline_disk.read_bytes
            disk_write = disk_io.write_bytes - self.baseline_disk.write_bytes
        else:
            disk_read = disk_write = 0
        
        # Screen brightness
        screen_brightness = self._get_screen_brightness()
        
        # Process count
        active_processes = len(psutil.pids())
        
        # Target application metrics
        target_app_cpu, target_app_memory = self._get_target_app_metrics()
        
        metrics = SystemMetrics(
            timestamp=timestamp,
            battery_percent=battery_percent,
            battery_power_draw=battery_power_draw,
            cpu_percent=cpu_percent,
            cpu_freq_current=cpu_freq_current,
            memory_percent=memory_percent,
            gpu_percent=gpu_percent,
            gpu_memory_percent=gpu_memory_percent,
            network_bytes_sent=net_sent,
            network_bytes_recv=net_recv,
            disk_io_read=disk_read,
            disk_io_write=disk_write,
            screen_brightness=screen_brightness,
            active_processes=active_processes,
            target_app_cpu=target_app_cpu,
            target_app_memory=target_app_memory
        )
        
        return metrics
    
    def _monitor_loop(self):
        """Main monitoring loop running in separate thread"""
        self.logger.info("📊 Starting system monitoring loop")
        
        while self.running:
            try:
                # Collect metrics
                metrics = self.collect_metrics()
                self.current_metrics = metrics
                self.metrics_history.append(metrics)
                
                # Notify callbacks
                for callback in self.callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        self.logger.error(f"Callback error: {e}")
                
                # Sleep until next update
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(self.update_interval)
    
    def start(self):
        """Start the monitoring system"""
        if self.running:
            self.logger.warning("⚠️ Monitor already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("✅ System monitor started")
    
    def stop(self):
        """Stop the monitoring system"""
        if not self.running:
            return
        
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        self.logger.info("🛑 System monitor stopped")
    
    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Get the most recent metrics"""
        return self.current_metrics
    
    def get_metrics_history(self, duration_seconds: int = 300) -> List[SystemMetrics]:
        """Get metrics history for the specified duration"""
        cutoff_time = time.time() - duration_seconds
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]
    
    def get_average_metrics(self, duration_seconds: int = 60) -> Optional[Dict]:
        """Get averaged metrics over specified duration"""
        history = self.get_metrics_history(duration_seconds)
        if not history:
            return None
        
        # Calculate averages
        avg_metrics = {}
        metrics_dict = [asdict(m) for m in history]
        
        for key in metrics_dict[0].keys():
            if key != 'timestamp':
                values = [m[key] for m in metrics_dict if isinstance(m[key], (int, float))]
                if values:
                    avg_metrics[key] = sum(values) / len(values)
        
        return avg_metrics
    
    def export_metrics(self, filepath: str, duration_seconds: int = 3600):
        """Export metrics history to JSON file"""
        history = self.get_metrics_history(duration_seconds)
        data = [asdict(m) for m in history]
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"📁 Exported {len(data)} metrics to {filepath}")

# Example usage and testing
if __name__ == "__main__":
    import signal
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create and start monitor
    monitor = SystemMonitor(update_interval=2.0)
    
    def print_metrics(metrics: SystemMetrics):
        print(f"🔋 Battery: {metrics.battery_percent:.1f}% | "
              f"CPU: {metrics.cpu_percent:.1f}% | "
              f"Memory: {metrics.memory_percent:.1f}% | "
              f"Power: {metrics.battery_power_draw:.1f}W")
    
    monitor.add_callback(print_metrics)
    monitor.start()
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print("\n🛑 Stopping monitor...")
        monitor.stop()
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop()
