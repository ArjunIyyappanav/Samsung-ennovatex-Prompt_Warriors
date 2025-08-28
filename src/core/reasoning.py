"""
Reasoning Layer - Lightweight ML agent for battery optimization decisions
"""

import numpy as np
import logging
import json
import pickle
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from collections import deque
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from .monitoring import SystemMetrics

@dataclass
class OptimizationAction:
    """Represents an optimization action the agent can take"""
    action_type: str  # 'cpu_throttle', 'brightness_adjust', 'network_limit', etc.
    intensity: float  # 0.0 to 1.0, how aggressive the optimization is
    target_component: str  # 'system', 'display', 'network', 'target_app'
    estimated_savings: float  # Estimated battery savings in %
    performance_impact: float  # Estimated performance impact 0.0-1.0
    confidence: float  # Agent's confidence in this action 0.0-1.0

@dataclass
class ContextState:
    """Current context state for decision making"""
    battery_level: str  # 'critical', 'low', 'medium', 'high'
    performance_demand: str  # 'idle', 'light', 'moderate', 'heavy'
    user_activity: str  # 'active', 'away', 'sleeping'
    power_source: str  # 'battery', 'plugged'
    time_of_day: str  # 'morning', 'afternoon', 'evening', 'night'
    app_priority: str  # 'background', 'foreground', 'critical'

class BatteryOptimizationAgent:
    """Lightweight ML agent for making battery optimization decisions"""
    
    def __init__(self, model_path: str = "models/battery_agent.pkl"):
        self.logger = logging.getLogger(__name__)
        self.model_path = Path(model_path)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # ML Models
        self.decision_model = None
        self.scaler = StandardScaler()
        self.model_trained = False
        
        # Experience replay for learning
        self.experience_buffer = deque(maxlen=1000)
        self.action_history = deque(maxlen=100)
        
        # Rule-based fallback system
        self.rules_engine = BatteryRulesEngine()
        
        # Performance tracking
        self.action_outcomes = {}  # Track success/failure of actions
        self.learning_rate = 0.1
        
        # Load pre-trained model if available
        self._load_model()
        
        # Initialize with synthetic training data if no model exists
        if not self.model_trained:
            self._train_initial_model()
    
    def _load_model(self):
        """Load pre-trained model from disk"""
        try:
            if self.model_path.exists():
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.decision_model = model_data['model']
                    self.scaler = model_data['scaler']
                    self.model_trained = True
                    self.logger.info("✅ Loaded pre-trained battery optimization model")
            else:
                self.logger.info("📚 No pre-trained model found, will train new model")
        except Exception as e:
            self.logger.error(f"❌ Error loading model: {e}")
    
    def _save_model(self):
        """Save trained model to disk"""
        try:
            model_data = {
                'model': self.decision_model,
                'scaler': self.scaler,
                'timestamp': time.time()
            }
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            self.logger.info(f"💾 Saved model to {self.model_path}")
        except Exception as e:
            self.logger.error(f"❌ Error saving model: {e}")
    
    def _generate_synthetic_training_data(self, n_samples: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
        """Generate synthetic training data for initial model training"""
        self.logger.info(f"🎯 Generating {n_samples} synthetic training samples")
        
        features = []
        labels = []
        
        for _ in range(n_samples):
            # Generate synthetic system state
            battery_percent = np.random.uniform(5, 100)
            cpu_usage = np.random.uniform(0, 100)
            memory_usage = np.random.uniform(20, 95)
            gpu_usage = np.random.uniform(0, 80)
            network_activity = np.random.uniform(0, 100)
            screen_brightness = np.random.uniform(10, 100)
            time_factor = np.random.uniform(0, 24)  # Hour of day
            power_plugged = np.random.choice([0, 1])
            
            # Create feature vector
            feature_vector = [
                battery_percent, cpu_usage, memory_usage, gpu_usage,
                network_activity, screen_brightness, time_factor, power_plugged
            ]
            features.append(feature_vector)
            
            # Generate label based on battery optimization rules
            action_class = self._synthetic_decision_logic(
                battery_percent, cpu_usage, memory_usage, power_plugged
            )
            labels.append(action_class)
        
        return np.array(features), np.array(labels)
    
    def _synthetic_decision_logic(self, battery: float, cpu: float, memory: float, plugged: int) -> int:
        """Synthetic decision logic for training data generation"""
        if plugged == 1:  # Plugged in
            return 0  # No optimization needed
        
        if battery < 15:  # Critical battery
            return 3  # Aggressive optimization
        elif battery < 30:  # Low battery
            if cpu > 70 or memory > 80:
                return 2  # Moderate optimization
            else:
                return 1  # Light optimization
        elif battery < 60:  # Medium battery
            if cpu > 90:
                return 1  # Light optimization
            else:
                return 0  # No optimization
        else:  # High battery
            return 0  # No optimization needed
    
    def _train_initial_model(self):
        """Train initial model with synthetic data"""
        self.logger.info("🤖 Training initial battery optimization model")
        
        # Generate synthetic training data
        X, y = self._generate_synthetic_training_data(1000)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train ensemble model
        self.decision_model = RandomForestClassifier(
            n_estimators=50,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        self.decision_model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        y_pred = self.decision_model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        self.model_trained = True
        self.logger.info(f"✅ Model trained with accuracy: {accuracy:.3f}")
        
        # Save the trained model
        self._save_model()
    
    def _extract_features(self, metrics: SystemMetrics, context: ContextState) -> np.ndarray:
        """Extract feature vector from system metrics and context"""
        features = [
            metrics.battery_percent,
            metrics.cpu_percent,
            metrics.memory_percent,
            metrics.gpu_percent,
            (metrics.network_bytes_sent + metrics.network_bytes_recv) / 1024 / 1024,  # MB
            metrics.screen_brightness,
            time.localtime().tm_hour,  # Hour of day
            1.0 if metrics.battery_power_draw < 5.0 else 0.0,  # Power plugged estimate
        ]
        return np.array(features).reshape(1, -1)
    
    def _context_to_numeric(self, context: ContextState) -> float:
        """Convert context state to numeric value"""
        # Simple encoding of context states
        battery_map = {'critical': 0, 'low': 1, 'medium': 2, 'high': 3}
        demand_map = {'idle': 0, 'light': 1, 'moderate': 2, 'heavy': 3}
        activity_map = {'sleeping': 0, 'away': 1, 'active': 2}
        
        context_score = (
            battery_map.get(context.battery_level, 2) * 0.4 +
            demand_map.get(context.performance_demand, 1) * 0.3 +
            activity_map.get(context.user_activity, 1) * 0.3
        )
        return context_score
    
    def analyze_context(self, metrics: SystemMetrics) -> ContextState:
        """Analyze current system state to determine context"""
        # Determine battery level category
        if metrics.battery_percent <= 15:
            battery_level = 'critical'
        elif metrics.battery_percent <= 30:
            battery_level = 'low'
        elif metrics.battery_percent <= 60:
            battery_level = 'medium'
        else:
            battery_level = 'high'
        
        # Determine performance demand
        total_usage = metrics.cpu_percent + metrics.gpu_percent
        if total_usage > 80:
            performance_demand = 'heavy'
        elif total_usage > 50:
            performance_demand = 'moderate'
        elif total_usage > 20:
            performance_demand = 'light'
        else:
            performance_demand = 'idle'
        
        # Determine user activity (simplified)
        current_hour = time.localtime().tm_hour
        if 23 <= current_hour or current_hour <= 6:
            user_activity = 'sleeping'
        elif metrics.cpu_percent < 10 and metrics.target_app_cpu < 5:
            user_activity = 'away'
        else:
            user_activity = 'active'
        
        # Determine power source (estimated)
        power_source = 'plugged' if metrics.battery_power_draw < 5.0 else 'battery'
        
        # Determine time of day
        if 6 <= current_hour < 12:
            time_of_day = 'morning'
        elif 12 <= current_hour < 18:
            time_of_day = 'afternoon'
        elif 18 <= current_hour < 22:
            time_of_day = 'evening'
        else:
            time_of_day = 'night'
        
        # Determine app priority
        if metrics.target_app_cpu > 20:
            app_priority = 'critical'
        elif metrics.target_app_cpu > 5:
            app_priority = 'foreground'
        else:
            app_priority = 'background'
        
        return ContextState(
            battery_level=battery_level,
            performance_demand=performance_demand,
            user_activity=user_activity,
            power_source=power_source,
            time_of_day=time_of_day,
            app_priority=app_priority
        )
    
    def decide_optimization(self, metrics: SystemMetrics) -> List[OptimizationAction]:
        """Main decision-making function - returns list of optimization actions"""
        context = self.analyze_context(metrics)
        self.logger.debug(f"🔍 Context: {context}")
        
        actions = []
        
        # Use ML model if trained and confident
        if self.model_trained:
            ml_actions = self._ml_decision(metrics, context)
            actions.extend(ml_actions)
        
        # Always include rule-based backup decisions
        rule_actions = self.rules_engine.get_rule_based_actions(metrics, context)
        
        # Combine and deduplicate actions
        combined_actions = self._combine_actions(actions, rule_actions)
        
        # Record decision for learning
        self._record_decision(metrics, context, combined_actions)
        
        return combined_actions
    
    def _ml_decision(self, metrics: SystemMetrics, context: ContextState) -> List[OptimizationAction]:
        """ML-based decision making"""
        try:
            # Extract features
            features = self._extract_features(metrics, context)
            
            # Make prediction
            features_scaled = self.scaler.transform(features)
            prediction = self.decision_model.predict(features_scaled)[0]
            probabilities = self.decision_model.predict_proba(features_scaled)[0]
            confidence = max(probabilities)
            
            # Convert prediction to actions
            actions = self._prediction_to_actions(prediction, confidence, metrics, context)
            
            self.logger.debug(f"🤖 ML prediction: {prediction}, confidence: {confidence:.3f}")
            return actions
            
        except Exception as e:
            self.logger.error(f"❌ ML decision error: {e}")
            return []
    
    def _prediction_to_actions(self, prediction: int, confidence: float, 
                             metrics: SystemMetrics, context: ContextState) -> List[OptimizationAction]:
        """Convert ML prediction to specific optimization actions"""
        actions = []
        
        if prediction == 0:  # No optimization
            return actions
        elif prediction == 1:  # Light optimization
            if metrics.screen_brightness > 60:
                actions.append(OptimizationAction(
                    action_type='brightness_adjust',
                    intensity=0.3,
                    target_component='display',
                    estimated_savings=5.0,
                    performance_impact=0.1,
                    confidence=confidence
                ))
        elif prediction == 2:  # Moderate optimization
            if metrics.cpu_percent > 50:
                actions.append(OptimizationAction(
                    action_type='cpu_throttle',
                    intensity=0.5,
                    target_component='system',
                    estimated_savings=10.0,
                    performance_impact=0.3,
                    confidence=confidence
                ))
            if metrics.screen_brightness > 40:
                actions.append(OptimizationAction(
                    action_type='brightness_adjust',
                    intensity=0.5,
                    target_component='display',
                    estimated_savings=8.0,
                    performance_impact=0.2,
                    confidence=confidence
                ))
        elif prediction == 3:  # Aggressive optimization
            actions.append(OptimizationAction(
                action_type='cpu_throttle',
                intensity=0.8,
                target_component='system',
                estimated_savings=20.0,
                performance_impact=0.6,
                confidence=confidence
            ))
            actions.append(OptimizationAction(
                action_type='brightness_adjust',
                intensity=0.7,
                target_component='display',
                estimated_savings=15.0,
                performance_impact=0.4,
                confidence=confidence
            ))
            if context.app_priority != 'critical':
                actions.append(OptimizationAction(
                    action_type='app_throttle',
                    intensity=0.6,
                    target_component='target_app',
                    estimated_savings=12.0,
                    performance_impact=0.5,
                    confidence=confidence
                ))
        
        return actions
    
    def _combine_actions(self, ml_actions: List[OptimizationAction], 
                        rule_actions: List[OptimizationAction]) -> List[OptimizationAction]:
        """Combine ML and rule-based actions, avoiding conflicts"""
        combined = {}
        
        # Add ML actions first (higher priority)
        for action in ml_actions:
            key = f"{action.action_type}_{action.target_component}"
            combined[key] = action
        
        # Add rule actions if not conflicting
        for action in rule_actions:
            key = f"{action.action_type}_{action.target_component}"
            if key not in combined:
                combined[key] = action
            else:
                # Take the more conservative action
                existing = combined[key]
                if action.intensity < existing.intensity:
                    combined[key] = action
        
        return list(combined.values())
    
    def _record_decision(self, metrics: SystemMetrics, context: ContextState, 
                        actions: List[OptimizationAction]):
        """Record decision for future learning"""
        decision_record = {
            'timestamp': time.time(),
            'metrics': asdict(metrics),
            'context': asdict(context),
            'actions': [asdict(action) for action in actions]
        }
        self.experience_buffer.append(decision_record)
        self.action_history.append(actions)
    
    def provide_feedback(self, action_id: str, success: bool, battery_savings: float, 
                        performance_impact: float, user_satisfaction: float):
        """Provide feedback on action outcomes for learning"""
        outcome = {
            'action_id': action_id,
            'success': success,
            'battery_savings': battery_savings,
            'performance_impact': performance_impact,
            'user_satisfaction': user_satisfaction,
            'timestamp': time.time()
        }
        
        self.action_outcomes[action_id] = outcome
        self.logger.info(f"📝 Recorded feedback for action {action_id}: success={success}")
        
        # Trigger learning if we have enough feedback
        if len(self.action_outcomes) > 10:
            self._update_model()
    
    def _update_model(self):
        """Update the ML model based on collected feedback"""
        try:
            if len(self.experience_buffer) < 50:
                return  # Need more data
            
            # Prepare training data from experience
            X, y = self._prepare_training_data_from_experience()
            
            if len(X) > 20:  # Minimum samples for retraining
                # Retrain model with new data
                X_scaled = self.scaler.fit_transform(X)
                self.decision_model.fit(X_scaled, y)
                
                self.logger.info(f"🔄 Updated model with {len(X)} new samples")
                self._save_model()
            
        except Exception as e:
            self.logger.error(f"❌ Model update error: {e}")
    
    def _prepare_training_data_from_experience(self) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data from experience buffer with feedback"""
        features = []
        labels = []
        
        for record in self.experience_buffer:
            try:
                # Reconstruct features
                metrics_dict = record['metrics']
                context_dict = record['context']
                
                # Convert back to objects
                metrics = SystemMetrics(**metrics_dict)
                context = ContextState(**context_dict)
                
                # Extract features
                feature_vector = self._extract_features(metrics, context).flatten()
                
                # Determine label based on outcomes
                actions = record['actions']
                if actions:
                    # Use feedback to determine if decision was good
                    action_success = self._evaluate_action_success(actions)
                    label = self._outcome_to_label(action_success, metrics.battery_percent)
                    
                    features.append(feature_vector)
                    labels.append(label)
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Error processing experience record: {e}")
                continue
        
        return np.array(features), np.array(labels)
    
    def _evaluate_action_success(self, actions: List[Dict]) -> bool:
        """Evaluate if the actions taken were successful based on feedback"""
        # Simple heuristic - improve with more sophisticated evaluation
        return len(actions) > 0  # Placeholder
    
    def _outcome_to_label(self, success: bool, battery_percent: float) -> int:
        """Convert outcome to training label"""
        if battery_percent > 60:
            return 0 if success else 1
        elif battery_percent > 30:
            return 1 if success else 2
        elif battery_percent > 15:
            return 2 if success else 3
        else:
            return 3


class BatteryRulesEngine:
    """Rule-based fallback system for battery optimization"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_rule_based_actions(self, metrics: SystemMetrics, 
                             context: ContextState) -> List[OptimizationAction]:
        """Generate rule-based optimization actions"""
        actions = []
        
        # Critical battery rules
        if context.battery_level == 'critical':
            actions.extend(self._critical_battery_rules(metrics, context))
        
        # Low battery rules
        elif context.battery_level == 'low':
            actions.extend(self._low_battery_rules(metrics, context))
        
        # Performance-based rules
        if context.performance_demand == 'heavy' and context.battery_level in ['low', 'critical']:
            actions.extend(self._performance_rules(metrics, context))
        
        # User activity rules
        if context.user_activity == 'away':
            actions.extend(self._away_mode_rules(metrics, context))
        
        return actions
    
    def _critical_battery_rules(self, metrics: SystemMetrics, context: ContextState) -> List[OptimizationAction]:
        """Rules for critical battery situations"""
        actions = []
        
        # Aggressive brightness reduction
        if metrics.screen_brightness > 20:
            actions.append(OptimizationAction(
                action_type='brightness_adjust',
                intensity=0.8,
                target_component='display',
                estimated_savings=20.0,
                performance_impact=0.3,
                confidence=0.9
            ))
        
        # CPU throttling
        if metrics.cpu_percent > 30:
            actions.append(OptimizationAction(
                action_type='cpu_throttle',
                intensity=0.7,
                target_component='system',
                estimated_savings=25.0,
                performance_impact=0.6,
                confidence=0.85
            ))
        
        return actions
    
    def _low_battery_rules(self, metrics: SystemMetrics, context: ContextState) -> List[OptimizationAction]:
        """Rules for low battery situations"""
        actions = []
        
        # Moderate brightness reduction
        if metrics.screen_brightness > 50:
            actions.append(OptimizationAction(
                action_type='brightness_adjust',
                intensity=0.4,
                target_component='display',
                estimated_savings=10.0,
                performance_impact=0.15,
                confidence=0.8
            ))
        
        # Light CPU throttling
        if metrics.cpu_percent > 60:
            actions.append(OptimizationAction(
                action_type='cpu_throttle',
                intensity=0.3,
                target_component='system',
                estimated_savings=12.0,
                performance_impact=0.25,
                confidence=0.75
            ))
        
        return actions
    
    def _performance_rules(self, metrics: SystemMetrics, context: ContextState) -> List[OptimizationAction]:
        """Rules based on high performance demand"""
        actions = []
        
        # Reduce non-essential background activity
        if metrics.target_app_cpu < 50:  # Target app not using much CPU
            actions.append(OptimizationAction(
                action_type='background_limit',
                intensity=0.5,
                target_component='system',
                estimated_savings=8.0,
                performance_impact=0.1,
                confidence=0.7
            ))
        
        return actions
    
    def _away_mode_rules(self, metrics: SystemMetrics, context: ContextState) -> List[OptimizationAction]:
        """Rules for when user is away"""
        actions = []
        
        # Aggressive brightness reduction
        actions.append(OptimizationAction(
            action_type='brightness_adjust',
            intensity=0.9,
            target_component='display',
            estimated_savings=30.0,
            performance_impact=0.1,
            confidence=0.95
        ))
        
        # Network activity limitation
        if metrics.network_bytes_sent + metrics.network_bytes_recv > 1024*1024:  # > 1MB
            actions.append(OptimizationAction(
                action_type='network_limit',
                intensity=0.6,
                target_component='network',
                estimated_savings=15.0,
                performance_impact=0.2,
                confidence=0.8
            ))
        
        return actions

# Example usage and testing
if __name__ == "__main__":
    import logging
    from .monitoring import SystemMonitor
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create agent
    agent = BatteryOptimizationAgent()
    
    # Create mock metrics
    mock_metrics = SystemMetrics(
        timestamp=time.time(),
        battery_percent=25.0,
        battery_power_draw=12.0,
        cpu_percent=65.0,
        cpu_freq_current=2400.0,
        memory_percent=70.0,
        gpu_percent=30.0,
        gpu_memory_percent=45.0,
        network_bytes_sent=1024*1024,
        network_bytes_recv=2*1024*1024,
        disk_io_read=100*1024,
        disk_io_write=50*1024,
        screen_brightness=80,
        active_processes=150,
        target_app_cpu=25.0,
        target_app_memory=15.0
    )
    
    # Test decision making
    actions = agent.decide_optimization(mock_metrics)
    
    print(f"🤖 Agent recommended {len(actions)} optimization actions:")
    for i, action in enumerate(actions, 1):
        print(f"  {i}. {action.action_type} (intensity: {action.intensity:.2f}, "
              f"savings: {action.estimated_savings:.1f}%, confidence: {action.confidence:.2f})")
