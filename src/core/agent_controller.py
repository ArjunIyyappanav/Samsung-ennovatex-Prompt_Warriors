"""
Main Agentic Controller - Orchestrates the entire battery optimization system
"""

import json
import time
import logging
import threading
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import queue

from .monitoring import SystemMonitor, SystemMetrics
from .reasoning import BatteryOptimizationAgent, OptimizationAction
from .actions import OptimizationActuator, ActionResult

@dataclass
class AgentState:
    """Current state of the agent"""
    active: bool
    battery_level: str
    optimization_mode: str
    actions_applied: int
    total_savings: float
    user_satisfaction: float
    last_decision_time: float

class AgentController:
    """Main controller that orchestrates the agentic battery optimization system"""
    
    def __init__(self, config_path: str = "config/default.json"):
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize core components
        self.monitor = SystemMonitor(
            update_interval=self.config.get('monitoring_interval', 2.0)
        )
        self.agent = BatteryOptimizationAgent(
            model_path=self.config.get('model_path', 'models/battery_agent.pkl')
        )
        self.actuator = OptimizationActuator()
        
        # Agent state
        self.state = AgentState(
            active=False,
            battery_level='unknown',
            optimization_mode='adaptive',
            actions_applied=0,
            total_savings=0.0,
            user_satisfaction=0.8,
            last_decision_time=0.0
        )
        
        # Control variables
        self.running = False
        self.agent_thread = None
        self.decision_queue = queue.Queue()
        
        # Registered target applications
        self.target_applications = {}
        
        # Performance tracking
        self.performance_history = []
        self.user_feedback_history = []
        
        # Event callbacks
        self.event_callbacks = {
            'metrics_update': [],
            'decision_made': [],
            'action_applied': [],
            'user_feedback': []
        }
        
        # Emergency fallback settings
        self.emergency_mode = False
        self.min_battery_threshold = self.config.get('emergency_battery_threshold', 5.0)
        
        self.logger.info("🤖 Agentic controller initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        config_file = Path(config_path)
        
        # Default configuration
        default_config = {
            'monitoring_interval': 2.0,
            'decision_interval': 10.0,
            'model_path': 'models/battery_agent.pkl',
            'emergency_battery_threshold': 5.0,
            'max_performance_impact': 0.7,
            'learning_rate': 0.1,
            'feedback_timeout': 300.0,
            'optimization_modes': {
                'aggressive': {'max_intensity': 0.9, 'min_confidence': 0.6},
                'balanced': {'max_intensity': 0.6, 'min_confidence': 0.7},
                'conservative': {'max_intensity': 0.3, 'min_confidence': 0.8}
            }
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
                self.logger.info(f"📁 Loaded configuration from {config_path}")
            except Exception as e:
                self.logger.warning(f"⚠️ Error loading config: {e}, using defaults")
        else:
            # Create default config file
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            self.logger.info(f"📁 Created default configuration at {config_path}")
        
        return default_config
    
    def add_event_callback(self, event_type: str, callback: Callable):
        """Add callback for specific events"""
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
    
    def remove_event_callback(self, event_type: str, callback: Callable):
        """Remove event callback"""
        if event_type in self.event_callbacks and callback in self.event_callbacks[event_type]:
            self.event_callbacks[event_type].remove(callback)
    
    def _trigger_event(self, event_type: str, data: Any):
        """Trigger event callbacks"""
        for callback in self.event_callbacks.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                self.logger.error(f"Event callback error ({event_type}): {e}")
    
    def register_target_application(self, app_instance: Any, app_name: str = None):
        """Register a target application for optimization"""
        if app_name is None:
            app_name = getattr(app_instance, 'name', type(app_instance).__name__)
        
        self.target_applications[app_name] = app_instance
        
        # Register app-specific optimizer if available
        if hasattr(app_instance, 'optimize_for_battery'):
            self.actuator.register_app_optimizer(app_name, app_instance.optimize_for_battery)
        
        self.logger.info(f"📱 Registered target application: {app_name}")
    
    def unregister_target_application(self, app_name: str):
        """Unregister a target application"""
        if app_name in self.target_applications:
            del self.target_applications[app_name]
            self.logger.info(f"📱 Unregistered target application: {app_name}")
    
    def set_optimization_mode(self, mode: str):
        """Set optimization mode (aggressive, balanced, conservative)"""
        if mode in self.config['optimization_modes']:
            self.state.optimization_mode = mode
            self.logger.info(f"⚙️ Set optimization mode to: {mode}")
        else:
            self.logger.warning(f"⚠️ Unknown optimization mode: {mode}")
    
    def start(self):
        """Start the agentic system"""
        if self.running:
            self.logger.warning("⚠️ Agent already running")
            return
        
        self.running = True
        self.state.active = True
        
        # Start monitoring
        self.monitor.start()
        
        # Set up monitoring callback
        self.monitor.add_callback(self._on_metrics_update)
        
        # Start agent decision loop
        self.agent_thread = threading.Thread(target=self._agent_loop, daemon=True)
        self.agent_thread.start()
        
        self.logger.info("🚀 Agentic battery optimization system started")
    
    def stop(self):
        """Stop the agentic system"""
        if not self.running:
            return
        
        self.running = False
        self.state.active = False
        
        # Stop monitoring
        self.monitor.stop()
        
        # Revert all active optimizations
        self.actuator.revert_all_actions()
        
        # Wait for agent thread to finish
        if self.agent_thread:
            self.agent_thread.join(timeout=5.0)
        
        self.logger.info("🛑 Agentic battery optimization system stopped")
    
    def _on_metrics_update(self, metrics: SystemMetrics):
        """Handle new system metrics"""
        # Update agent state
        if metrics.battery_percent <= 15:
            self.state.battery_level = 'critical'
        elif metrics.battery_percent <= 30:
            self.state.battery_level = 'low'
        elif metrics.battery_percent <= 60:
            self.state.battery_level = 'medium'
        else:
            self.state.battery_level = 'high'
        
        # Check for emergency mode
        if metrics.battery_percent <= self.min_battery_threshold:
            if not self.emergency_mode:
                self.emergency_mode = True
                self.logger.warning("🚨 Entering emergency battery mode!")
                self._apply_emergency_optimizations()
        else:
            if self.emergency_mode:
                self.emergency_mode = False
                self.logger.info("✅ Exiting emergency battery mode")
        
        # Queue metrics for agent decision making
        self.decision_queue.put(metrics)
        
        # Trigger event
        self._trigger_event('metrics_update', metrics)
    
    def _agent_loop(self):
        """Main agent decision loop"""
        self.logger.info("🧠 Agent decision loop started")
        
        last_decision_time = 0
        decision_interval = self.config.get('decision_interval', 10.0)
        
        while self.running:
            try:
                # Get latest metrics (with timeout)
                try:
                    metrics = self.decision_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Check if it's time for a new decision
                current_time = time.time()
                if current_time - last_decision_time < decision_interval:
                    continue
                
                # Make optimization decision
                self._make_optimization_decision(metrics)
                last_decision_time = current_time
                self.state.last_decision_time = current_time
                
                # Clear the queue to avoid backlog
                while not self.decision_queue.empty():
                    try:
                        self.decision_queue.get_nowait()
                    except queue.Empty:
                        break
                
            except Exception as e:
                self.logger.error(f"❌ Agent loop error: {e}")
                time.sleep(1.0)
        
        self.logger.info("🧠 Agent decision loop stopped")
    
    def _make_optimization_decision(self, metrics: SystemMetrics):
        """Make optimization decision based on current metrics"""
        try:
            # Get optimization actions from the agent
            actions = self.agent.decide_optimization(metrics)
            
            if not actions:
                return  # No optimizations needed
            
            # Filter actions based on current mode and confidence
            filtered_actions = self._filter_actions_by_mode(actions)
            
            if not filtered_actions:
                return  # No actions passed the filter
            
            # Apply the optimization actions
            results = self.actuator.apply_actions(filtered_actions)
            
            # Update state
            successful_actions = [r for r in results if r.success]
            self.state.actions_applied += len(successful_actions)
            
            # Calculate estimated savings
            estimated_savings = sum(r.estimated_savings for r in successful_actions)
            self.state.total_savings += estimated_savings
            
            # Log decision
            self.logger.info(f"🤖 Applied {len(successful_actions)}/{len(actions)} optimizations, "
                           f"estimated savings: {estimated_savings:.1f}%")
            
            # Record performance
            self._record_decision_performance(metrics, actions, results)
            
            # Trigger events
            self._trigger_event('decision_made', {
                'metrics': metrics,
                'actions': actions,
                'filtered_actions': filtered_actions,
                'results': results
            })
            
            for result in results:
                self._trigger_event('action_applied', result)
            
        except Exception as e:
            self.logger.error(f"❌ Decision making error: {e}")
    
    def _filter_actions_by_mode(self, actions: List[OptimizationAction]) -> List[OptimizationAction]:
        """Filter actions based on current optimization mode"""
        mode_config = self.config['optimization_modes'][self.state.optimization_mode]
        max_intensity = mode_config['max_intensity']
        min_confidence = mode_config['min_confidence']
        max_performance_impact = self.config.get('max_performance_impact', 0.7)
        
        filtered = []
        for action in actions:
            # Check intensity limit
            if action.intensity > max_intensity:
                continue
            
            # Check confidence threshold
            if action.confidence < min_confidence:
                continue
            
            # Check performance impact
            if action.performance_impact > max_performance_impact:
                continue
            
            filtered.append(action)
        
        return filtered
    
    def _apply_emergency_optimizations(self):
        """Apply emergency optimizations when battery is critical"""
        self.logger.warning("🚨 Applying emergency optimizations")
        
        # Create emergency actions
        emergency_actions = [
            OptimizationAction(
                action_type='brightness_adjust',
                intensity=0.9,
                target_component='display',
                estimated_savings=25.0,
                performance_impact=0.3,
                confidence=0.95
            ),
            OptimizationAction(
                action_type='cpu_throttle',
                intensity=0.8,
                target_component='system',
                estimated_savings=30.0,
                performance_impact=0.7,
                confidence=0.9
            )
        ]
        
        # Apply emergency actions
        results = self.actuator.apply_actions(emergency_actions)
        
        successful = [r for r in results if r.success]
        self.logger.warning(f"🚨 Applied {len(successful)}/{len(emergency_actions)} emergency optimizations")
    
    def _record_decision_performance(self, metrics: SystemMetrics, actions: List[OptimizationAction], 
                                   results: List[ActionResult]):
        """Record decision performance for learning"""
        performance_record = {
            'timestamp': time.time(),
            'battery_percent': metrics.battery_percent,
            'actions_requested': len(actions),
            'actions_applied': len([r for r in results if r.success]),
            'estimated_savings': sum(r.estimated_savings for r in results if r.success),
            'optimization_mode': self.state.optimization_mode,
            'emergency_mode': self.emergency_mode
        }
        
        self.performance_history.append(performance_record)
        
        # Keep history limited
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-500:]
    
    def provide_user_feedback(self, satisfaction_score: float, performance_acceptable: bool, 
                            battery_improvement: bool, comments: str = ""):
        """Provide user feedback to improve the agent"""
        feedback = {
            'timestamp': time.time(),
            'satisfaction_score': satisfaction_score,  # 0.0 to 1.0
            'performance_acceptable': performance_acceptable,
            'battery_improvement': battery_improvement,
            'comments': comments,
            'current_mode': self.state.optimization_mode,
            'actions_applied': self.state.actions_applied
        }
        
        self.user_feedback_history.append(feedback)
        
        # Update agent satisfaction
        self.state.user_satisfaction = (
            self.state.user_satisfaction * 0.8 + satisfaction_score * 0.2
        )
        
        # Provide feedback to the learning agent
        self.agent.provide_feedback(
            action_id=f"session_{time.time()}",
            success=performance_acceptable and battery_improvement,
            battery_savings=10.0 if battery_improvement else 0.0,  # Placeholder
            performance_impact=0.3 if not performance_acceptable else 0.1,
            user_satisfaction=satisfaction_score
        )
        
        self.logger.info(f"📝 Received user feedback: satisfaction={satisfaction_score:.2f}")
        
        # Trigger event
        self._trigger_event('user_feedback', feedback)
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current state of the agent"""
        state_dict = asdict(self.state)
        state_dict.update({
            'registered_apps': list(self.target_applications.keys()),
            'active_optimizations': len(self.actuator.get_active_actions()),
            'emergency_mode': self.emergency_mode,
            'current_metrics': asdict(self.monitor.get_current_metrics()) if self.monitor.get_current_metrics() else None
        })
        return state_dict
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.performance_history:
            return {}
        
        recent_history = self.performance_history[-100:]  # Last 100 decisions
        
        stats = {
            'total_decisions': len(self.performance_history),
            'recent_decisions': len(recent_history),
            'average_actions_per_decision': sum(r['actions_applied'] for r in recent_history) / len(recent_history),
            'average_estimated_savings': sum(r['estimated_savings'] for r in recent_history) / len(recent_history),
            'emergency_mode_activations': sum(1 for r in recent_history if r['emergency_mode']),
            'user_satisfaction': self.state.user_satisfaction,
            'feedback_count': len(self.user_feedback_history)
        }
        
        return stats
    
    def export_data(self, filepath: str):
        """Export agent data for analysis"""
        export_data = {
            'configuration': self.config,
            'current_state': self.get_current_state(),
            'performance_history': self.performance_history,
            'user_feedback_history': self.user_feedback_history,
            'performance_statistics': self.get_performance_statistics(),
            'export_timestamp': time.time()
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"📁 Exported agent data to {filepath}")
    
    def load_user_preferences(self, preferences: Dict[str, Any]):
        """Load user preferences for optimization behavior"""
        if 'optimization_mode' in preferences:
            self.set_optimization_mode(preferences['optimization_mode'])
        
        if 'emergency_threshold' in preferences:
            self.min_battery_threshold = preferences['emergency_threshold']
        
        if 'max_performance_impact' in preferences:
            self.config['max_performance_impact'] = preferences['max_performance_impact']
        
        if 'decision_interval' in preferences:
            self.config['decision_interval'] = preferences['decision_interval']
        
        self.logger.info("⚙️ Loaded user preferences")
    
    def pause_optimization(self):
        """Temporarily pause optimization decisions"""
        self.state.active = False
        self.logger.info("⏸️ Optimization paused")
    
    def resume_optimization(self):
        """Resume optimization decisions"""
        self.state.active = True
        self.logger.info("▶️ Optimization resumed")
    
    def emergency_revert(self):
        """Emergency revert all optimizations"""
        self.logger.warning("🚨 Emergency revert triggered")
        results = self.actuator.revert_all_actions()
        successful = [r for r in results if r.success]
        self.logger.warning(f"🚨 Emergency reverted {len(successful)}/{len(results)} optimizations")
        return results

# Example usage and testing
if __name__ == "__main__":
    import signal
    import logging
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create controller
    controller = AgentController()
    
    # Add some callbacks for monitoring
    def on_metrics_update(metrics):
        print(f"📊 Battery: {metrics.battery_percent:.1f}%, CPU: {metrics.cpu_percent:.1f}%")
    
    def on_decision_made(data):
        actions = data['filtered_actions']
        if actions:
            print(f"🤖 Agent decided on {len(actions)} optimizations")
    
    controller.add_event_callback('metrics_update', on_metrics_update)
    controller.add_event_callback('decision_made', on_decision_made)
    
    # Start the system
    controller.start()
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down agent...")
        controller.stop()
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Run for a test period
        print("🤖 Agent running... Press Ctrl+C to stop")
        
        # Simulate some user feedback after 30 seconds
        time.sleep(30)
        controller.provide_user_feedback(
            satisfaction_score=0.8,
            performance_acceptable=True,
            battery_improvement=True,
            comments="Working well, battery life improved noticeably"
        )
        
        # Continue running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        controller.stop()
