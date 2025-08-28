"""
Action Layer - System optimization controls and actuators
"""

import os
import sys
import time
import logging
import platform
import subprocess
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

from .reasoning import OptimizationAction

@dataclass
class ActionResult:
    """Result of an optimization action"""
    action_id: str
    success: bool
    error_message: Optional[str] = None
    previous_value: Optional[Any] = None
    new_value: Optional[Any] = None
    estimated_savings: float = 0.0
    actual_impact: float = 0.0

class BaseOptimizer(ABC):
    """Base class for optimization actuators"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.enabled = True
        self.previous_states = {}
    
    @abstractmethod
    def apply_optimization(self, action: OptimizationAction) -> ActionResult:
        """Apply the optimization action"""
        pass
    
    @abstractmethod
    def revert_optimization(self, action_id: str) -> ActionResult:
        """Revert a previously applied optimization"""
        pass
    
    @abstractmethod
    def get_current_state(self) -> Dict[str, Any]:
        """Get current state of the optimization target"""
        pass
    
    def is_available(self) -> bool:
        """Check if this optimizer is available on current platform"""
        return True

class DisplayOptimizer(BaseOptimizer):
    """Optimizer for display-related settings (brightness, refresh rate)"""
    
    def __init__(self):
        super().__init__("DisplayOptimizer")
        self.platform = platform.system().lower()
        self.current_brightness = self._get_current_brightness()
        self.original_brightness = self.current_brightness
    
    def _get_current_brightness(self) -> int:
        """Get current screen brightness (0-100)"""
        try:
            if self.platform == "windows":
                return self._get_windows_brightness()
            elif self.platform == "linux":
                return self._get_linux_brightness()
            else:
                # Fallback - return simulated value
                return 75
        except Exception as e:
            self.logger.warning(f"Could not get brightness: {e}")
            return 75
    
    def _get_windows_brightness(self) -> int:
        """Get brightness on Windows"""
        try:
            # Use PowerShell to get brightness
            cmd = "powershell -Command \"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness\""
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip())
            else:
                return 75  # Default fallback
        except Exception:
            return 75
    
    def _get_linux_brightness(self) -> int:
        """Get brightness on Linux"""
        try:
            # Try common brightness control paths
            brightness_paths = [
                "/sys/class/backlight/intel_backlight/brightness",
                "/sys/class/backlight/acpi_video0/brightness",
                "/sys/class/backlight/amdgpu_bl0/brightness"
            ]
            
            max_brightness_paths = [
                "/sys/class/backlight/intel_backlight/max_brightness",
                "/sys/class/backlight/acpi_video0/max_brightness", 
                "/sys/class/backlight/amdgpu_bl0/max_brightness"
            ]
            
            for bright_path, max_path in zip(brightness_paths, max_brightness_paths):
                if os.path.exists(bright_path) and os.path.exists(max_path):
                    with open(bright_path, 'r') as f:
                        current = int(f.read().strip())
                    with open(max_path, 'r') as f:
                        maximum = int(f.read().strip())
                    return int((current / maximum) * 100)
            
            # Fallback to xrandr if available
            result = subprocess.run(
                ["xrandr", "--verbose"], 
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                # Parse xrandr output for brightness
                for line in result.stdout.split('\n'):
                    if 'Brightness:' in line:
                        brightness = float(line.split('Brightness:')[1].strip())
                        return int(brightness * 100)
            
            return 75  # Default fallback
            
        except Exception:
            return 75
    
    def _set_brightness(self, brightness: int) -> bool:
        """Set screen brightness (0-100)"""
        try:
            brightness = max(10, min(100, brightness))  # Clamp between 10-100
            
            if self.platform == "windows":
                return self._set_windows_brightness(brightness)
            elif self.platform == "linux":
                return self._set_linux_brightness(brightness)
            else:
                # Simulate success for unsupported platforms
                self.current_brightness = brightness
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to set brightness: {e}")
            return False
    
    def _set_windows_brightness(self, brightness: int) -> bool:
        """Set brightness on Windows"""
        try:
            # Use PowerShell to set brightness
            cmd = f"powershell -Command \"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{brightness})\""
            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
            if result.returncode == 0:
                self.current_brightness = brightness
                return True
            return False
        except Exception:
            return False
    
    def _set_linux_brightness(self, brightness: int) -> bool:
        """Set brightness on Linux"""
        try:
            # Try xrandr first (most compatible)
            brightness_float = brightness / 100.0
            result = subprocess.run(
                ["xrandr", "--output", "$(xrandr | grep ' connected' | head -n1 | cut -d' ' -f1)", 
                 "--brightness", str(brightness_float)], 
                shell=True, capture_output=True, timeout=5
            )
            if result.returncode == 0:
                self.current_brightness = brightness
                return True
            
            # Try writing to sys files (requires root)
            brightness_paths = [
                "/sys/class/backlight/intel_backlight/brightness",
                "/sys/class/backlight/acpi_video0/brightness"
            ]
            
            for path in brightness_paths:
                if os.path.exists(path):
                    try:
                        # Calculate actual brightness value
                        max_path = path.replace("/brightness", "/max_brightness")
                        if os.path.exists(max_path):
                            with open(max_path, 'r') as f:
                                max_bright = int(f.read().strip())
                            actual_bright = int((brightness / 100.0) * max_bright)
                            
                            # Try to write (may need sudo)
                            subprocess.run(
                                f"echo {actual_bright} | sudo tee {path}",
                                shell=True, capture_output=True, timeout=5
                            )
                            self.current_brightness = brightness
                            return True
                    except Exception:
                        continue
            
            return False
        except Exception:
            return False
    
    def apply_optimization(self, action: OptimizationAction) -> ActionResult:
        """Apply display optimization"""
        action_id = f"display_{action.action_type}_{time.time()}"
        
        if action.action_type == "brightness_adjust":
            previous_brightness = self.current_brightness
            
            # Calculate new brightness based on intensity
            reduction = int(action.intensity * 50)  # Max 50% reduction
            new_brightness = max(10, previous_brightness - reduction)
            
            # Store previous state for reversion
            self.previous_states[action_id] = {
                'type': 'brightness',
                'value': previous_brightness
            }
            
            success = self._set_brightness(new_brightness)
            
            return ActionResult(
                action_id=action_id,
                success=success,
                previous_value=previous_brightness,
                new_value=new_brightness if success else previous_brightness,
                estimated_savings=action.estimated_savings,
                error_message=None if success else "Failed to set brightness"
            )
        
        else:
            return ActionResult(
                action_id=action_id,
                success=False,
                error_message=f"Unknown display action: {action.action_type}"
            )
    
    def revert_optimization(self, action_id: str) -> ActionResult:
        """Revert display optimization"""
        if action_id not in self.previous_states:
            return ActionResult(
                action_id=action_id,
                success=False,
                error_message="Action not found in history"
            )
        
        state = self.previous_states[action_id]
        
        if state['type'] == 'brightness':
            success = self._set_brightness(state['value'])
            del self.previous_states[action_id]
            
            return ActionResult(
                action_id=action_id,
                success=success,
                new_value=state['value'] if success else self.current_brightness,
                error_message=None if success else "Failed to revert brightness"
            )
        
        return ActionResult(
            action_id=action_id,
            success=False,
            error_message="Unknown action type"
        )
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current display state"""
        return {
            'brightness': self.current_brightness,
            'platform': self.platform
        }

class CPUOptimizer(BaseOptimizer):
    """Optimizer for CPU frequency and performance settings"""
    
    def __init__(self):
        super().__init__("CPUOptimizer")
        self.platform = platform.system().lower()
        self.cpu_count = os.cpu_count()
        self.original_governor = self._get_current_governor()
    
    def _get_current_governor(self) -> str:
        """Get current CPU governor (Linux) or power plan (Windows)"""
        try:
            if self.platform == "linux":
                # Read CPU governor
                governor_path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
                if os.path.exists(governor_path):
                    with open(governor_path, 'r') as f:
                        return f.read().strip()
                return "unknown"
            elif self.platform == "windows":
                # Get current power plan
                result = subprocess.run(
                    "powercfg /getactivescheme",
                    shell=True, capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    return result.stdout.strip()
                return "balanced"
            else:
                return "unsupported"
        except Exception:
            return "unknown"
    
    def _set_cpu_governor(self, governor: str) -> bool:
        """Set CPU governor (Linux)"""
        try:
            if self.platform != "linux":
                return False
            
            # Set governor for all CPUs
            for i in range(self.cpu_count):
                governor_path = f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_governor"
                if os.path.exists(governor_path):
                    subprocess.run(
                        f"echo {governor} | sudo tee {governor_path}",
                        shell=True, capture_output=True, timeout=5
                    )
            return True
        except Exception as e:
            self.logger.error(f"Failed to set CPU governor: {e}")
            return False
    
    def _set_windows_power_plan(self, plan: str) -> bool:
        """Set Windows power plan"""
        try:
            if self.platform != "windows":
                return False
            
            # Map plan names to GUIDs
            power_plans = {
                "power_saver": "a1841308-3541-4fab-bc81-f71556f20b4a",
                "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
                "high_performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
            }
            
            plan_guid = power_plans.get(plan, power_plans["balanced"])
            
            result = subprocess.run(
                f"powercfg /setactive {plan_guid}",
                shell=True, capture_output=True, timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Failed to set Windows power plan: {e}")
            return False
    
    def _set_cpu_frequency(self, max_freq_percent: float) -> bool:
        """Set maximum CPU frequency as percentage of max"""
        try:
            if self.platform == "linux":
                # Use cpufreq-set if available
                result = subprocess.run(
                    ["which", "cpufreq-set"], 
                    capture_output=True, timeout=5
                )
                if result.returncode == 0:
                    # Get max frequency
                    with open("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq", 'r') as f:
                        max_freq = int(f.read().strip())
                    
                    target_freq = int(max_freq * max_freq_percent / 100)
                    
                    for i in range(self.cpu_count):
                        subprocess.run(
                            f"sudo cpufreq-set -c {i} -u {target_freq}",
                            shell=True, capture_output=True, timeout=5
                        )
                    return True
            
            elif self.platform == "windows":
                # Use powercfg to set processor performance
                processor_perf = int(max_freq_percent)
                
                # Set processor performance for current power scheme
                subprocess.run(
                    f"powercfg /setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMAX {processor_perf}",
                    shell=True, capture_output=True, timeout=10
                )
                subprocess.run(
                    f"powercfg /setdcvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMAX {processor_perf}",
                    shell=True, capture_output=True, timeout=10
                )
                subprocess.run(
                    "powercfg /setactive SCHEME_CURRENT",
                    shell=True, capture_output=True, timeout=10
                )
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Failed to set CPU frequency: {e}")
            return False
    
    def apply_optimization(self, action: OptimizationAction) -> ActionResult:
        """Apply CPU optimization"""
        action_id = f"cpu_{action.action_type}_{time.time()}"
        
        if action.action_type == "cpu_throttle":
            # Calculate throttling based on intensity
            max_freq_percent = 100 - (action.intensity * 50)  # Max 50% throttling
            
            # Store previous state
            self.previous_states[action_id] = {
                'type': 'frequency',
                'governor': self.original_governor,
                'max_freq_percent': 100
            }
            
            # Apply CPU throttling
            success = False
            
            if self.platform == "linux":
                # Set powersave governor for throttling
                success = self._set_cpu_governor("powersave")
                if success:
                    success = self._set_cpu_frequency(max_freq_percent)
            elif self.platform == "windows":
                # Set power saver plan
                success = self._set_windows_power_plan("power_saver")
                if success:
                    success = self._set_cpu_frequency(max_freq_percent)
            else:
                # Simulate success for unsupported platforms
                success = True
            
            return ActionResult(
                action_id=action_id,
                success=success,
                previous_value=100,
                new_value=max_freq_percent if success else 100,
                estimated_savings=action.estimated_savings,
                error_message=None if success else "Failed to throttle CPU"
            )
        
        else:
            return ActionResult(
                action_id=action_id,
                success=False,
                error_message=f"Unknown CPU action: {action.action_type}"
            )
    
    def revert_optimization(self, action_id: str) -> ActionResult:
        """Revert CPU optimization"""
        if action_id not in self.previous_states:
            return ActionResult(
                action_id=action_id,
                success=False,
                error_message="Action not found in history"
            )
        
        state = self.previous_states[action_id]
        success = False
        
        if state['type'] == 'frequency':
            if self.platform == "linux":
                success = self._set_cpu_governor(state['governor'])
                if success:
                    success = self._set_cpu_frequency(state['max_freq_percent'])
            elif self.platform == "windows":
                success = self._set_windows_power_plan("balanced")
                if success:
                    success = self._set_cpu_frequency(state['max_freq_percent'])
            else:
                success = True  # Simulate success
            
            if success:
                del self.previous_states[action_id]
        
        return ActionResult(
            action_id=action_id,
            success=success,
            error_message=None if success else "Failed to revert CPU settings"
        )
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current CPU state"""
        return {
            'governor': self._get_current_governor(),
            'cpu_count': self.cpu_count,
            'platform': self.platform
        }

class NetworkOptimizer(BaseOptimizer):
    """Optimizer for network activity and bandwidth"""
    
    def __init__(self):
        super().__init__("NetworkOptimizer")
        self.platform = platform.system().lower()
        self.active_limits = {}
    
    def _limit_bandwidth(self, interface: str, limit_mbps: float) -> bool:
        """Limit network bandwidth (simplified implementation)"""
        try:
            if self.platform == "linux":
                # Use tc (traffic control) if available
                result = subprocess.run(
                    ["which", "tc"], 
                    capture_output=True, timeout=5
                )
                if result.returncode == 0:
                    # Add bandwidth limiting
                    limit_kbps = int(limit_mbps * 1000)
                    commands = [
                        f"sudo tc qdisc add dev {interface} root handle 1: htb default 30",
                        f"sudo tc class add dev {interface} parent 1: classid 1:1 htb rate {limit_kbps}kbit",
                        f"sudo tc class add dev {interface} parent 1:1 classid 1:10 htb rate {limit_kbps}kbit ceil {limit_kbps}kbit",
                        f"sudo tc filter add dev {interface} protocol ip parent 1:0 prio 1 u32 match ip dst 0.0.0.0/0 flowid 1:10"
                    ]
                    
                    for cmd in commands:
                        subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
                    
                    return True
            
            # Fallback - just log the action (can't actually limit without root/admin)
            self.logger.info(f"Simulated bandwidth limit: {limit_mbps} Mbps on {interface}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to limit bandwidth: {e}")
            return False
    
    def _remove_bandwidth_limit(self, interface: str) -> bool:
        """Remove network bandwidth limit"""
        try:
            if self.platform == "linux":
                subprocess.run(
                    f"sudo tc qdisc del dev {interface} root",
                    shell=True, capture_output=True, timeout=10
                )
                return True
            
            # Fallback
            self.logger.info(f"Simulated bandwidth limit removal on {interface}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove bandwidth limit: {e}")
            return False
    
    def _get_network_interface(self) -> str:
        """Get primary network interface"""
        try:
            if self.platform == "linux":
                result = subprocess.run(
                    "ip route | grep default | head -n1 | awk '{print $5}'",
                    shell=True, capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            
            # Fallback
            return "eth0"
        except Exception:
            return "eth0"
    
    def apply_optimization(self, action: OptimizationAction) -> ActionResult:
        """Apply network optimization"""
        action_id = f"network_{action.action_type}_{time.time()}"
        
        if action.action_type == "network_limit":
            interface = self._get_network_interface()
            
            # Calculate bandwidth limit based on intensity
            base_limit = 100  # Mbps base limit
            limit_mbps = base_limit * (1 - action.intensity)
            
            # Store previous state
            self.previous_states[action_id] = {
                'type': 'bandwidth_limit',
                'interface': interface,
                'had_limit': interface in self.active_limits
            }
            
            success = self._limit_bandwidth(interface, limit_mbps)
            
            if success:
                self.active_limits[interface] = limit_mbps
            
            return ActionResult(
                action_id=action_id,
                success=success,
                previous_value="unlimited" if interface not in self.active_limits else self.active_limits[interface],
                new_value=limit_mbps if success else "unchanged",
                estimated_savings=action.estimated_savings,
                error_message=None if success else "Failed to limit network bandwidth"
            )
        
        else:
            return ActionResult(
                action_id=action_id,
                success=False,
                error_message=f"Unknown network action: {action.action_type}"
            )
    
    def revert_optimization(self, action_id: str) -> ActionResult:
        """Revert network optimization"""
        if action_id not in self.previous_states:
            return ActionResult(
                action_id=action_id,
                success=False,
                error_message="Action not found in history"
            )
        
        state = self.previous_states[action_id]
        success = False
        
        if state['type'] == 'bandwidth_limit':
            interface = state['interface']
            
            if not state['had_limit']:
                # Remove the limit entirely
                success = self._remove_bandwidth_limit(interface)
                if success and interface in self.active_limits:
                    del self.active_limits[interface]
            
            if success:
                del self.previous_states[action_id]
        
        return ActionResult(
            action_id=action_id,
            success=success,
            error_message=None if success else "Failed to revert network settings"
        )
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current network state"""
        return {
            'active_limits': self.active_limits.copy(),
            'interface': self._get_network_interface(),
            'platform': self.platform
        }

class ApplicationOptimizer(BaseOptimizer):
    """Optimizer for target application settings"""
    
    def __init__(self):
        super().__init__("ApplicationOptimizer")
        self.app_optimizations = {}
        self.optimization_callbacks = {}
    
    def register_app_optimizer(self, app_name: str, optimizer_callback: Callable):
        """Register an optimization callback for a specific application"""
        self.optimization_callbacks[app_name] = optimizer_callback
        self.logger.info(f"Registered optimizer for application: {app_name}")
    
    def apply_optimization(self, action: OptimizationAction) -> ActionResult:
        """Apply application-specific optimization"""
        action_id = f"app_{action.action_type}_{time.time()}"
        
        if action.action_type == "app_throttle":
            # Generic application throttling
            target_app = action.target_component
            
            if target_app in self.optimization_callbacks:
                # Use registered callback
                callback = self.optimization_callbacks[target_app]
                try:
                    result = callback(action)
                    
                    self.previous_states[action_id] = {
                        'type': 'app_throttle',
                        'app': target_app,
                        'previous_state': result.previous_value
                    }
                    
                    return ActionResult(
                        action_id=action_id,
                        success=result.success,
                        previous_value=result.previous_value,
                        new_value=result.new_value,
                        estimated_savings=action.estimated_savings,
                        error_message=result.error_message
                    )
                except Exception as e:
                    return ActionResult(
                        action_id=action_id,
                        success=False,
                        error_message=f"Application optimizer error: {e}"
                    )
            else:
                # Generic process priority adjustment
                return self._adjust_process_priority(action_id, target_app, action.intensity)
        
        else:
            return ActionResult(
                action_id=action_id,
                success=False,
                error_message=f"Unknown application action: {action.action_type}"
            )
    
    def _adjust_process_priority(self, action_id: str, app_name: str, intensity: float) -> ActionResult:
        """Adjust process priority for power saving"""
        try:
            import psutil
            
            adjusted_processes = []
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if app_name.lower() in proc.info['name'].lower():
                        old_priority = proc.nice()
                        
                        # Lower priority based on intensity (higher nice value = lower priority)
                        nice_adjustment = int(intensity * 10)  # 0-10 nice adjustment
                        new_priority = min(19, old_priority + nice_adjustment)  # Max nice is 19
                        
                        proc.nice(new_priority)
                        adjusted_processes.append({
                            'pid': proc.pid,
                            'old_priority': old_priority,
                            'new_priority': new_priority
                        })
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if adjusted_processes:
                self.previous_states[action_id] = {
                    'type': 'process_priority',
                    'processes': adjusted_processes
                }
                
                return ActionResult(
                    action_id=action_id,
                    success=True,
                    previous_value=f"{len(adjusted_processes)} processes",
                    new_value=f"Priority reduced for {len(adjusted_processes)} processes",
                    estimated_savings=5.0 * len(adjusted_processes)  # Estimate
                )
            else:
                return ActionResult(
                    action_id=action_id,
                    success=False,
                    error_message=f"No processes found for application: {app_name}"
                )
                
        except Exception as e:
            return ActionResult(
                action_id=action_id,
                success=False,
                error_message=f"Failed to adjust process priority: {e}"
            )
    
    def revert_optimization(self, action_id: str) -> ActionResult:
        """Revert application optimization"""
        if action_id not in self.previous_states:
            return ActionResult(
                action_id=action_id,
                success=False,
                error_message="Action not found in history"
            )
        
        state = self.previous_states[action_id]
        
        if state['type'] == 'process_priority':
            try:
                import psutil
                reverted_count = 0
                
                for proc_info in state['processes']:
                    try:
                        proc = psutil.Process(proc_info['pid'])
                        proc.nice(proc_info['old_priority'])
                        reverted_count += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                del self.previous_states[action_id]
                
                return ActionResult(
                    action_id=action_id,
                    success=True,
                    new_value=f"Reverted priority for {reverted_count} processes"
                )
            except Exception as e:
                return ActionResult(
                    action_id=action_id,
                    success=False,
                    error_message=f"Failed to revert process priorities: {e}"
                )
        
        return ActionResult(
            action_id=action_id,
            success=False,
            error_message="Unknown action type for reversion"
        )
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current application optimization state"""
        return {
            'registered_apps': list(self.optimization_callbacks.keys()),
            'active_optimizations': len(self.previous_states)
        }

class OptimizationActuator:
    """Main controller for all optimization actions"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize optimizers
        self.optimizers = {
            'display': DisplayOptimizer(),
            'cpu': CPUOptimizer(),
            'network': NetworkOptimizer(),
            'application': ApplicationOptimizer()
        }
        
        # Track active actions
        self.active_actions = {}
        self.action_history = []
        
        # Performance monitoring
        self.action_lock = threading.Lock()
        
        self.logger.info("✅ Optimization actuator initialized")
    
    def apply_actions(self, actions: List[OptimizationAction]) -> List[ActionResult]:
        """Apply a list of optimization actions"""
        results = []
        
        with self.action_lock:
            for action in actions:
                try:
                    result = self._apply_single_action(action)
                    results.append(result)
                    
                    if result.success:
                        self.active_actions[result.action_id] = {
                            'action': action,
                            'result': result,
                            'timestamp': time.time()
                        }
                        self.logger.info(f"✅ Applied {action.action_type}: {result.action_id}")
                    else:
                        self.logger.warning(f"❌ Failed to apply {action.action_type}: {result.error_message}")
                        
                except Exception as e:
                    self.logger.error(f"Error applying action {action.action_type}: {e}")
                    results.append(ActionResult(
                        action_id=f"error_{time.time()}",
                        success=False,
                        error_message=str(e)
                    ))
            
            # Add to history
            self.action_history.extend(results)
            
            # Keep history limited
            if len(self.action_history) > 1000:
                self.action_history = self.action_history[-500:]
        
        return results
    
    def _apply_single_action(self, action: OptimizationAction) -> ActionResult:
        """Apply a single optimization action"""
        # Determine which optimizer to use
        optimizer_map = {
            'brightness_adjust': 'display',
            'cpu_throttle': 'cpu',
            'network_limit': 'network',
            'app_throttle': 'application',
            'background_limit': 'application'
        }
        
        optimizer_name = optimizer_map.get(action.action_type)
        
        if not optimizer_name:
            return ActionResult(
                action_id=f"unknown_{time.time()}",
                success=False,
                error_message=f"Unknown action type: {action.action_type}"
            )
        
        optimizer = self.optimizers.get(optimizer_name)
        if not optimizer:
            return ActionResult(
                action_id=f"missing_{time.time()}",
                success=False,
                error_message=f"Optimizer not available: {optimizer_name}"
            )
        
        if not optimizer.enabled:
            return ActionResult(
                action_id=f"disabled_{time.time()}",
                success=False,
                error_message=f"Optimizer disabled: {optimizer_name}"
            )
        
        return optimizer.apply_optimization(action)
    
    def revert_action(self, action_id: str) -> ActionResult:
        """Revert a specific optimization action"""
        with self.action_lock:
            if action_id not in self.active_actions:
                return ActionResult(
                    action_id=action_id,
                    success=False,
                    error_message="Action not found in active actions"
                )
            
            action_info = self.active_actions[action_id]
            action = action_info['action']
            
            # Find the appropriate optimizer
            optimizer_map = {
                'brightness_adjust': 'display',
                'cpu_throttle': 'cpu',
                'network_limit': 'network',
                'app_throttle': 'application',
                'background_limit': 'application'
            }
            
            optimizer_name = optimizer_map.get(action.action_type)
            optimizer = self.optimizers.get(optimizer_name)
            
            if not optimizer:
                return ActionResult(
                    action_id=action_id,
                    success=False,
                    error_message=f"Optimizer not found: {optimizer_name}"
                )
            
            result = optimizer.revert_optimization(action_id)
            
            if result.success:
                del self.active_actions[action_id]
                self.logger.info(f"🔄 Reverted action: {action_id}")
            else:
                self.logger.warning(f"❌ Failed to revert action {action_id}: {result.error_message}")
            
            return result
    
    def revert_all_actions(self) -> List[ActionResult]:
        """Revert all active optimization actions"""
        results = []
        action_ids = list(self.active_actions.keys())
        
        for action_id in action_ids:
            result = self.revert_action(action_id)
            results.append(result)
        
        self.logger.info(f"🔄 Reverted {len(results)} actions")
        return results
    
    def get_active_actions(self) -> Dict[str, Dict]:
        """Get all currently active optimization actions"""
        with self.action_lock:
            return self.active_actions.copy()
    
    def get_system_state(self) -> Dict[str, Dict]:
        """Get current state of all optimizers"""
        state = {}
        for name, optimizer in self.optimizers.items():
            try:
                state[name] = optimizer.get_current_state()
            except Exception as e:
                state[name] = {'error': str(e)}
        return state
    
    def register_app_optimizer(self, app_name: str, optimizer_callback: Callable):
        """Register an optimization callback for a specific application"""
        if 'application' in self.optimizers:
            self.optimizers['application'].register_app_optimizer(app_name, optimizer_callback)
    
    def enable_optimizer(self, optimizer_name: str):
        """Enable a specific optimizer"""
        if optimizer_name in self.optimizers:
            self.optimizers[optimizer_name].enabled = True
            self.logger.info(f"✅ Enabled optimizer: {optimizer_name}")
    
    def disable_optimizer(self, optimizer_name: str):
        """Disable a specific optimizer"""
        if optimizer_name in self.optimizers:
            self.optimizers[optimizer_name].enabled = False
            self.logger.info(f"❌ Disabled optimizer: {optimizer_name}")
    
    def get_action_history(self, limit: int = 100) -> List[ActionResult]:
        """Get recent action history"""
        with self.action_lock:
            return self.action_history[-limit:]

# Example usage and testing
if __name__ == "__main__":
    import logging
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create actuator
    actuator = OptimizationActuator()
    
    # Test actions
    test_actions = [
        OptimizationAction(
            action_type='brightness_adjust',
            intensity=0.3,
            target_component='display',
            estimated_savings=10.0,
            performance_impact=0.1,
            confidence=0.8
        ),
        OptimizationAction(
            action_type='cpu_throttle',
            intensity=0.5,
            target_component='system',
            estimated_savings=15.0,
            performance_impact=0.4,
            confidence=0.7
        )
    ]
    
    # Apply actions
    print("🔧 Applying optimization actions...")
    results = actuator.apply_actions(test_actions)
    
    for result in results:
        print(f"  {result.action_id}: {'✅' if result.success else '❌'} {result.error_message or 'Success'}")
    
    # Show current state
    print("\n📊 Current system state:")
    state = actuator.get_system_state()
    for optimizer, info in state.items():
        print(f"  {optimizer}: {info}")
    
    # Wait a bit then revert
    print("\n⏳ Waiting 5 seconds...")
    time.sleep(5)
    
    print("🔄 Reverting all actions...")
    revert_results = actuator.revert_all_actions()
    
    for result in revert_results:
        print(f"  {result.action_id}: {'✅' if result.success else '❌'} {result.error_message or 'Reverted'}")
