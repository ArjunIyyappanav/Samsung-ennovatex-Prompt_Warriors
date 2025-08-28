"""
Web Dashboard for Battery Optimization System Monitoring
"""

import json
import time
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response
from typing import Dict, Any, Optional
import threading
import os
from pathlib import Path

class WebDashboard:
    """Web-based dashboard for monitoring the battery optimization system"""
    
    def __init__(self, agent_controller, host='localhost', port=5000):
        self.agent_controller = agent_controller
        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__)
        
        # Flask app setup
        self.app = Flask(__name__, 
                        template_folder=str(Path(__file__).parent / 'templates'),
                        static_folder=str(Path(__file__).parent / 'static'))
        
        # Real-time data storage
        self.real_time_data = {
            'metrics': [],
            'decisions': [],
            'actions': [],
            'feedback': []
        }
        
        # Setup routes
        self._setup_routes()
        
        # Setup event callbacks
        self._setup_callbacks()
        
        self.logger.info(f"📊 Dashboard initialized at http://{host}:{port}")
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return render_template('dashboard.html')
        
        @self.app.route('/api/status')
        def get_status():
            """Get current system status"""
            return jsonify(self.agent_controller.get_current_state())
        
        @self.app.route('/api/metrics')
        def get_metrics():
            """Get current system metrics"""
            current_metrics = self.agent_controller.monitor.get_current_metrics()
            if current_metrics:
                return jsonify({
                    'timestamp': current_metrics.timestamp,
                    'battery_percent': current_metrics.battery_percent,
                    'battery_power_draw': current_metrics.battery_power_draw,
                    'cpu_percent': current_metrics.cpu_percent,
                    'memory_percent': current_metrics.memory_percent,
                    'gpu_percent': current_metrics.gpu_percent,
                    'screen_brightness': current_metrics.screen_brightness,
                    'target_app_cpu': current_metrics.target_app_cpu,
                    'target_app_memory': current_metrics.target_app_memory
                })
            return jsonify({})
        
        @self.app.route('/api/metrics/history')
        def get_metrics_history():
            """Get metrics history"""
            duration = request.args.get('duration', 300, type=int)  # 5 minutes default
            history = self.agent_controller.monitor.get_metrics_history(duration)
            
            data = []
            for metrics in history:
                data.append({
                    'timestamp': metrics.timestamp,
                    'battery_percent': metrics.battery_percent,
                    'battery_power_draw': metrics.battery_power_draw,
                    'cpu_percent': metrics.cpu_percent,
                    'memory_percent': metrics.memory_percent,
                    'gpu_percent': metrics.gpu_percent,
                    'target_app_cpu': metrics.target_app_cpu
                })
            
            return jsonify(data)
        
        @self.app.route('/api/optimizations')
        def get_active_optimizations():
            """Get currently active optimizations"""
            active_actions = self.agent_controller.actuator.get_active_actions()
            
            optimizations = []
            for action_id, action_info in active_actions.items():
                action = action_info['action']
                result = action_info['result']
                
                optimizations.append({
                    'id': action_id,
                    'type': action.action_type,
                    'intensity': action.intensity,
                    'target': action.target_component,
                    'estimated_savings': action.estimated_savings,
                    'performance_impact': action.performance_impact,
                    'confidence': action.confidence,
                    'timestamp': action_info['timestamp'],
                    'success': result.success,
                    'previous_value': result.previous_value,
                    'new_value': result.new_value
                })
            
            return jsonify(optimizations)
        
        @self.app.route('/api/statistics')
        def get_statistics():
            """Get performance statistics"""
            return jsonify(self.agent_controller.get_performance_statistics())
        
        @self.app.route('/api/system_state')
        def get_system_state():
            """Get current state of all optimizers"""
            return jsonify(self.agent_controller.actuator.get_system_state())
        
        @self.app.route('/api/target_apps')
        def get_target_apps():
            """Get registered target applications"""
            apps = {}
            for app_name, app_instance in self.agent_controller.target_applications.items():
                if hasattr(app_instance, 'get_current_stats'):
                    apps[app_name] = app_instance.get_current_stats()
                else:
                    apps[app_name] = {'name': app_name, 'status': 'registered'}
            
            return jsonify(apps)
        
        @self.app.route('/api/control/pause', methods=['POST'])
        def pause_optimization():
            """Pause optimization"""
            self.agent_controller.pause_optimization()
            return jsonify({'success': True, 'message': 'Optimization paused'})
        
        @self.app.route('/api/control/resume', methods=['POST'])
        def resume_optimization():
            """Resume optimization"""
            self.agent_controller.resume_optimization()
            return jsonify({'success': True, 'message': 'Optimization resumed'})
        
        @self.app.route('/api/control/revert_all', methods=['POST'])
        def revert_all():
            """Revert all optimizations"""
            results = self.agent_controller.actuator.revert_all_actions()
            successful = len([r for r in results if r.success])
            return jsonify({
                'success': True, 
                'message': f'Reverted {successful}/{len(results)} optimizations'
            })
        
        @self.app.route('/api/control/emergency_revert', methods=['POST'])
        def emergency_revert():
            """Emergency revert all optimizations"""
            results = self.agent_controller.emergency_revert()
            successful = len([r for r in results if r.success])
            return jsonify({
                'success': True, 
                'message': f'Emergency reverted {successful}/{len(results)} optimizations'
            })
        
        @self.app.route('/api/control/mode', methods=['POST'])
        def set_optimization_mode():
            """Set optimization mode"""
            data = request.get_json()
            mode = data.get('mode', 'balanced')
            
            try:
                self.agent_controller.set_optimization_mode(mode)
                return jsonify({'success': True, 'message': f'Mode set to {mode}'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/feedback', methods=['POST'])
        def submit_feedback():
            """Submit user feedback"""
            data = request.get_json()
            
            try:
                self.agent_controller.provide_user_feedback(
                    satisfaction_score=data.get('satisfaction', 0.5),
                    performance_acceptable=data.get('performance_acceptable', True),
                    battery_improvement=data.get('battery_improvement', True),
                    comments=data.get('comments', '')
                )
                return jsonify({'success': True, 'message': 'Feedback recorded'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/realtime')
        def realtime_stream():
            """Server-sent events for real-time updates"""
            def generate():
                while True:
                    # Get latest data
                    current_metrics = self.agent_controller.monitor.get_current_metrics()
                    current_state = self.agent_controller.get_current_state()
                    
                    if current_metrics:
                        data = {
                            'timestamp': time.time(),
                            'metrics': {
                                'battery_percent': current_metrics.battery_percent,
                                'battery_power_draw': current_metrics.battery_power_draw,
                                'cpu_percent': current_metrics.cpu_percent,
                                'memory_percent': current_metrics.memory_percent,
                                'gpu_percent': current_metrics.gpu_percent
                            },
                            'state': current_state
                        }
                        
                        yield f"data: {json.dumps(data)}\\n\\n"
                    
                    time.sleep(2)  # Update every 2 seconds
            
            return Response(generate(), mimetype='text/plain')
    
    def _setup_callbacks(self):
        """Setup callbacks to collect real-time data"""
        
        def on_metrics_update(metrics):
            # Store recent metrics (keep last 100)
            metric_data = {
                'timestamp': metrics.timestamp,
                'battery_percent': metrics.battery_percent,
                'cpu_percent': metrics.cpu_percent,
                'power_draw': metrics.battery_power_draw
            }
            
            self.real_time_data['metrics'].append(metric_data)
            if len(self.real_time_data['metrics']) > 100:
                self.real_time_data['metrics'] = self.real_time_data['metrics'][-50:]
        
        def on_decision_made(data):
            # Store decision data
            decision_data = {
                'timestamp': time.time(),
                'actions_count': len(data['filtered_actions']),
                'battery_level': data['metrics'].battery_percent
            }
            
            self.real_time_data['decisions'].append(decision_data)
            if len(self.real_time_data['decisions']) > 50:
                self.real_time_data['decisions'] = self.real_time_data['decisions'][-25:]
        
        def on_action_applied(result):
            # Store action results
            action_data = {
                'timestamp': time.time(),
                'action_id': result.action_id,
                'success': result.success,
                'estimated_savings': result.estimated_savings
            }
            
            self.real_time_data['actions'].append(action_data)
            if len(self.real_time_data['actions']) > 50:
                self.real_time_data['actions'] = self.real_time_data['actions'][-25:]
        
        def on_user_feedback(feedback):
            # Store feedback
            self.real_time_data['feedback'].append({
                'timestamp': feedback['timestamp'],
                'satisfaction': feedback['satisfaction_score'],
                'performance_acceptable': feedback['performance_acceptable']
            })
            if len(self.real_time_data['feedback']) > 20:
                self.real_time_data['feedback'] = self.real_time_data['feedback'][-10:]
        
        # Register callbacks
        self.agent_controller.add_event_callback('metrics_update', on_metrics_update)
        self.agent_controller.add_event_callback('decision_made', on_decision_made)
        self.agent_controller.add_event_callback('action_applied', on_action_applied)
        self.agent_controller.add_event_callback('user_feedback', on_user_feedback)
    
    def start(self, threaded=True, debug=False):
        """Start the web dashboard"""
        try:
            # Create templates directory and basic template if they don't exist
            self._ensure_templates_exist()
            
            if threaded:
                # Run in separate thread
                def run_app():
                    self.app.run(host=self.host, port=self.port, debug=debug, 
                               use_reloader=False, threaded=True)
                
                dashboard_thread = threading.Thread(target=run_app, daemon=True)
                dashboard_thread.start()
                self.logger.info(f"📊 Dashboard started in thread at http://{self.host}:{self.port}")
            else:
                # Run in main thread
                self.app.run(host=self.host, port=self.port, debug=debug)
                
        except Exception as e:
            self.logger.error(f"❌ Failed to start dashboard: {e}")
    
    def _ensure_templates_exist(self):
        """Create basic HTML template if it doesn't exist"""
        templates_dir = Path(__file__).parent / 'templates'
        templates_dir.mkdir(exist_ok=True)
        
        template_file = templates_dir / 'dashboard.html'
        
        if not template_file.exists():
            html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Battery Optimization Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border-left: 4px solid #3498db;
        }
        .card h3 {
            margin-top: 0;
            color: #2c3e50;
            font-size: 1.3em;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 10px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        .metric-value {
            font-weight: bold;
            color: #27ae60;
            font-size: 1.1em;
        }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        .status-active { background-color: #27ae60; }
        .status-inactive { background-color: #e74c3c; }
        .status-warning { background-color: #f39c12; }
        .controls {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin: 20px 0;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }
        .btn-primary { background: #3498db; color: white; }
        .btn-success { background: #27ae60; color: white; }
        .btn-warning { background: #f39c12; color: white; }
        .btn-danger { background: #e74c3c; color: white; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
        .chart-container {
            position: relative;
            height: 300px;
            margin: 20px 0;
        }
        .optimizations-list {
            max-height: 300px;
            overflow-y: auto;
        }
        .optimization-item {
            background: #f8f9fa;
            border-radius: 5px;
            padding: 10px;
            margin: 5px 0;
            border-left: 3px solid #3498db;
        }
        .feedback-form {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .form-group {
            margin: 15px 0;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .alert {
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .alert-success { background: #d4edda; border-color: #c3e6cb; color: #155724; }
        .alert-error { background: #f8d7da; border-color: #f5c6cb; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔋 Battery Optimization Dashboard</h1>
        
        <div class="dashboard-grid">
            <!-- System Status -->
            <div class="card">
                <h3>📊 System Status</h3>
                <div class="metric">
                    <span>Agent Status:</span>
                    <span id="agent-status" class="metric-value">
                        <span class="status-indicator status-inactive"></span>Initializing...
                    </span>
                </div>
                <div class="metric">
                    <span>Battery Level:</span>
                    <span id="battery-level" class="metric-value">---%</span>
                </div>
                <div class="metric">
                    <span>Power Draw:</span>
                    <span id="power-draw" class="metric-value">--- W</span>
                </div>
                <div class="metric">
                    <span>Optimization Mode:</span>
                    <span id="optimization-mode" class="metric-value">---</span>
                </div>
                <div class="metric">
                    <span>Actions Applied:</span>
                    <span id="actions-applied" class="metric-value">0</span>
                </div>
                <div class="metric">
                    <span>Total Savings:</span>
                    <span id="total-savings" class="metric-value">0.0%</span>
                </div>
            </div>
            
            <!-- Current Metrics -->
            <div class="card">
                <h3>⚡ Current Metrics</h3>
                <div class="metric">
                    <span>CPU Usage:</span>
                    <span id="cpu-usage" class="metric-value">---%</span>
                </div>
                <div class="metric">
                    <span>Memory Usage:</span>
                    <span id="memory-usage" class="metric-value">---%</span>
                </div>
                <div class="metric">
                    <span>GPU Usage:</span>
                    <span id="gpu-usage" class="metric-value">---%</span>
                </div>
                <div class="metric">
                    <span>Screen Brightness:</span>
                    <span id="screen-brightness" class="metric-value">---%</span>
                </div>
                <div class="metric">
                    <span>Target App CPU:</span>
                    <span id="target-app-cpu" class="metric-value">---%</span>
                </div>
            </div>
            
            <!-- Controls -->
            <div class="card">
                <h3>🎛️ Controls</h3>
                <div class="controls">
                    <button class="btn btn-success" onclick="resumeOptimization()">▶️ Resume</button>
                    <button class="btn btn-warning" onclick="pauseOptimization()">⏸️ Pause</button>
                    <button class="btn btn-primary" onclick="revertAll()">🔄 Revert All</button>
                    <button class="btn btn-danger" onclick="emergencyRevert()">🚨 Emergency</button>
                </div>
                <div class="form-group">
                    <label for="mode-select">Optimization Mode:</label>
                    <select id="mode-select" onchange="setOptimizationMode()">
                        <option value="conservative">Conservative</option>
                        <option value="balanced" selected>Balanced</option>
                        <option value="aggressive">Aggressive</option>
                    </select>
                </div>
                <div id="control-messages"></div>
            </div>
        </div>
        
        <!-- Charts -->
        <div class="card">
            <h3>📈 Battery & Performance Trends</h3>
            <div class="chart-container">
                <canvas id="metricsChart"></canvas>
            </div>
        </div>
        
        <div class="dashboard-grid">
            <!-- Active Optimizations -->
            <div class="card">
                <h3>🔧 Active Optimizations</h3>
                <div id="optimizations-list" class="optimizations-list">
                    <p>Loading optimizations...</p>
                </div>
            </div>
            
            <!-- User Feedback -->
            <div class="card">
                <h3>💬 User Feedback</h3>
                <div class="feedback-form">
                    <div class="form-group">
                        <label for="satisfaction">Satisfaction (1-10):</label>
                        <input type="range" id="satisfaction" min="1" max="10" value="8">
                        <span id="satisfaction-value">8</span>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="performance-ok" checked> Performance Acceptable
                        </label>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="battery-improved" checked> Battery Life Improved
                        </label>
                    </div>
                    <div class="form-group">
                        <label for="comments">Comments:</label>
                        <textarea id="comments" rows="3" placeholder="Optional feedback..."></textarea>
                    </div>
                    <button class="btn btn-primary" onclick="submitFeedback()">Submit Feedback</button>
                </div>
                <div id="feedback-messages"></div>
            </div>
        </div>
    </div>
    
    <script>
        let metricsChart;
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            initializeChart();
            updateDashboard();
            
            // Update every 3 seconds
            setInterval(updateDashboard, 3000);
            
            // Satisfaction slider
            document.getElementById('satisfaction').oninput = function() {
                document.getElementById('satisfaction-value').textContent = this.value;
            };
        });
        
        function initializeChart() {
            const ctx = document.getElementById('metricsChart').getContext('2d');
            metricsChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Battery %',
                            data: [],
                            borderColor: '#27ae60',
                            backgroundColor: 'rgba(39, 174, 96, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'CPU %',
                            data: [],
                            borderColor: '#3498db',
                            backgroundColor: 'rgba(52, 152, 219, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Power Draw (W)',
                            data: [],
                            borderColor: '#e74c3c',
                            backgroundColor: 'rgba(231, 76, 60, 0.1)',
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                        }
                    }
                }
            });
        }
        
        async function updateDashboard() {
            try {
                // Update status
                const status = await fetch('/api/status').then(r => r.json());
                updateStatus(status);
                
                // Update metrics
                const metrics = await fetch('/api/metrics').then(r => r.json());
                updateMetrics(metrics);
                
                // Update chart
                const history = await fetch('/api/metrics/history?duration=300').then(r => r.json());
                updateChart(history);
                
                // Update optimizations
                const optimizations = await fetch('/api/optimizations').then(r => r.json());
                updateOptimizations(optimizations);
                
            } catch (error) {
                console.error('Dashboard update error:', error);
            }
        }
        
        function updateStatus(status) {
            const indicator = status.active ? 'status-active' : 'status-inactive';
            const statusText = status.active ? 'Active' : 'Inactive';
            
            document.getElementById('agent-status').innerHTML = 
                `<span class="status-indicator ${indicator}"></span>${statusText}`;
            
            document.getElementById('optimization-mode').textContent = status.optimization_mode || 'Unknown';
            document.getElementById('actions-applied').textContent = status.actions_applied || 0;
            document.getElementById('total-savings').textContent = `${(status.total_savings || 0).toFixed(1)}%`;
        }
        
        function updateMetrics(metrics) {
            if (!metrics.battery_percent) return;
            
            document.getElementById('battery-level').textContent = `${metrics.battery_percent.toFixed(1)}%`;
            document.getElementById('power-draw').textContent = `${metrics.battery_power_draw.toFixed(1)} W`;
            document.getElementById('cpu-usage').textContent = `${metrics.cpu_percent.toFixed(1)}%`;
            document.getElementById('memory-usage').textContent = `${metrics.memory_percent.toFixed(1)}%`;
            document.getElementById('gpu-usage').textContent = `${metrics.gpu_percent.toFixed(1)}%`;
            document.getElementById('screen-brightness').textContent = `${metrics.screen_brightness}%`;
            document.getElementById('target-app-cpu').textContent = `${metrics.target_app_cpu.toFixed(1)}%`;
        }
        
        function updateChart(history) {
            if (!history || history.length === 0) return;
            
            const labels = history.map(h => new Date(h.timestamp * 1000).toLocaleTimeString());
            const batteryData = history.map(h => h.battery_percent);
            const cpuData = history.map(h => h.cpu_percent);
            const powerData = history.map(h => h.battery_power_draw);
            
            metricsChart.data.labels = labels;
            metricsChart.data.datasets[0].data = batteryData;
            metricsChart.data.datasets[1].data = cpuData;
            metricsChart.data.datasets[2].data = powerData;
            metricsChart.update('none');
        }
        
        function updateOptimizations(optimizations) {
            const container = document.getElementById('optimizations-list');
            
            if (optimizations.length === 0) {
                container.innerHTML = '<p>No active optimizations</p>';
                return;
            }
            
            const html = optimizations.map(opt => `
                <div class="optimization-item">
                    <strong>${opt.type}</strong> (${opt.target})
                    <br>Intensity: ${(opt.intensity * 100).toFixed(0)}% | 
                    Savings: ${opt.estimated_savings.toFixed(1)}% | 
                    Confidence: ${(opt.confidence * 100).toFixed(0)}%
                    <br><small>Applied: ${new Date(opt.timestamp * 1000).toLocaleString()}</small>
                </div>
            `).join('');
            
            container.innerHTML = html;
        }
        
        function showMessage(containerId, message, isError = false) {
            const container = document.getElementById(containerId);
            const alertClass = isError ? 'alert-error' : 'alert-success';
            container.innerHTML = `<div class="alert ${alertClass}">${message}</div>`;
            setTimeout(() => container.innerHTML = '', 3000);
        }
        
        async function pauseOptimization() {
            try {
                const response = await fetch('/api/control/pause', { method: 'POST' });
                const result = await response.json();
                showMessage('control-messages', result.message, !result.success);
            } catch (error) {
                showMessage('control-messages', 'Error pausing optimization', true);
            }
        }
        
        async function resumeOptimization() {
            try {
                const response = await fetch('/api/control/resume', { method: 'POST' });
                const result = await response.json();
                showMessage('control-messages', result.message, !result.success);
            } catch (error) {
                showMessage('control-messages', 'Error resuming optimization', true);
            }
        }
        
        async function revertAll() {
            try {
                const response = await fetch('/api/control/revert_all', { method: 'POST' });
                const result = await response.json();
                showMessage('control-messages', result.message, !result.success);
            } catch (error) {
                showMessage('control-messages', 'Error reverting optimizations', true);
            }
        }
        
        async function emergencyRevert() {
            if (!confirm('Emergency revert all optimizations?')) return;
            
            try {
                const response = await fetch('/api/control/emergency_revert', { method: 'POST' });
                const result = await response.json();
                showMessage('control-messages', result.message, !result.success);
            } catch (error) {
                showMessage('control-messages', 'Error in emergency revert', true);
            }
        }
        
        async function setOptimizationMode() {
            const mode = document.getElementById('mode-select').value;
            
            try {
                const response = await fetch('/api/control/mode', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mode })
                });
                const result = await response.json();
                showMessage('control-messages', result.message, !result.success);
            } catch (error) {
                showMessage('control-messages', 'Error setting mode', true);
            }
        }
        
        async function submitFeedback() {
            const satisfaction = parseInt(document.getElementById('satisfaction').value) / 10;
            const performanceOk = document.getElementById('performance-ok').checked;
            const batteryImproved = document.getElementById('battery-improved').checked;
            const comments = document.getElementById('comments').value;
            
            try {
                const response = await fetch('/api/feedback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        satisfaction,
                        performance_acceptable: performanceOk,
                        battery_improvement: batteryImproved,
                        comments
                    })
                });
                const result = await response.json();
                showMessage('feedback-messages', result.message, !result.success);
                
                if (result.success) {
                    document.getElementById('comments').value = '';
                }
            } catch (error) {
                showMessage('feedback-messages', 'Error submitting feedback', true);
            }
        }
    </script>
</body>
</html>'''
            
            with open(template_file, 'w') as f:
                f.write(html_content)
            
            self.logger.info("📄 Created dashboard template")

# Example usage and testing
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add parent directory for imports
    sys.path.append(str(Path(__file__).parent.parent))
    
    from core.agent_controller import AgentController
    import logging
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create mock agent controller for testing
    controller = AgentController()
    
    # Create and start dashboard
    dashboard = WebDashboard(controller)
    
    print("🚀 Starting dashboard on http://localhost:5000")
    print("📊 Dashboard will show battery optimization data in real-time")
    print("Press Ctrl+C to stop")
    
    try:
        dashboard.start(threaded=False)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped")
