#!/usr/bin/env python3
"""
Voice System Dashboard and Alerts
Real-time web dashboard for monitoring MCP Voice Agents with Langwatch integration
"""

from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import threading
import time

# Import our metrics system
from voice_metrics_observability import voice_metrics, get_voice_dashboard, get_voice_alerts, record_voice_interaction

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Dashboard HTML template
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Voice System Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: #f5f7fa; 
            color: #333;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.2em; opacity: 0.9; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border-left: 5px solid #667eea;
            transition: transform 0.3s ease;
        }
        .metric-card:hover { transform: translateY(-5px); }
        .metric-card h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        .metric-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-healthy { background: #4CAF50; }
        .status-warning { background: #FF9800; }
        .status-error { background: #F44336; }
        .chart-container {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .alerts-section {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .alert-item {
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid;
        }
        .alert-error { 
            background: #ffebee; 
            border-left-color: #f44336; 
        }
        .alert-warning { 
            background: #fff3e0; 
            border-left-color: #ff9800; 
        }
        .alert-info { 
            background: #e3f2fd; 
            border-left-color: #2196f3; 
        }
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
            margin-bottom: 20px;
            transition: background 0.3s ease;
        }
        .refresh-btn:hover { background: #5a6fd8; }
        .agent-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .agent-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .agent-card h4 {
            color: #667eea;
            margin-bottom: 15px;
            text-transform: capitalize;
        }
        .agent-stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        .agent-stat {
            text-align: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 6px;
        }
        .agent-stat-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
        }
        .agent-stat-label {
            font-size: 0.8em;
            color: #666;
            margin-top: 5px;
        }
        .timestamp {
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎤 MCP Voice System Dashboard</h1>
        <p>Real-time monitoring with Langwatch integration</p>
    </div>
    
    <div class="container">
        <button class="refresh-btn" onclick="refreshDashboard()">🔄 Refresh Data</button>
        
        <!-- Overall Metrics -->
        <div class="metrics-grid" id="overall-metrics">
            <!-- Populated by JavaScript -->
        </div>
        
        <!-- Performance Chart -->
        <div class="chart-container">
            <h3>📊 Hourly Performance Trends</h3>
            <canvas id="performanceChart" width="400" height="200"></canvas>
        </div>
        
        <!-- Agent Performance -->
        <div class="agent-grid" id="agent-performance">
            <!-- Populated by JavaScript -->
        </div>
        
        <!-- Alerts Section -->
        <div class="alerts-section">
            <h3>🚨 Recent Alerts</h3>
            <div id="alerts-container">
                <!-- Populated by JavaScript -->
            </div>
        </div>
        
        <div class="timestamp" id="last-updated">
            <!-- Populated by JavaScript -->
        </div>
    </div>

    <script>
        let performanceChart;
        
        async function fetchDashboardData() {
            try {
                const response = await fetch('/api/dashboard');
                return await response.json();
            } catch (error) {
                console.error('Error fetching dashboard data:', error);
                return null;
            }
        }
        
        function updateOverallMetrics(data) {
            const container = document.getElementById('overall-metrics');
            const overall = data.overall_performance;
            
            container.innerHTML = `
                <div class="metric-card">
                    <h3><span class="status-indicator ${getStatusClass(overall.success_rate)}"></span>Success Rate</h3>
                    <div class="metric-value">${overall.success_rate.toFixed(1)}%</div>
                    <div class="metric-label">Last Hour</div>
                </div>
                <div class="metric-card">
                    <h3>⚡ Avg Response Time</h3>
                    <div class="metric-value">${overall.avg_duration.toFixed(2)}s</div>
                    <div class="metric-label">Total Duration</div>
                </div>
                <div class="metric-card">
                    <h3>📞 Total Calls</h3>
                    <div class="metric-value">${overall.total_calls}</div>
                    <div class="metric-label">Last Hour</div>
                </div>
                <div class="metric-card">
                    <h3>🚀 Throughput</h3>
                    <div class="metric-value">${overall.throughput_per_minute.toFixed(1)}</div>
                    <div class="metric-label">Calls/Minute</div>
                </div>
                <div class="metric-card">
                    <h3>📈 P95 Latency</h3>
                    <div class="metric-value">${overall.p95_duration.toFixed(2)}s</div>
                    <div class="metric-label">95th Percentile</div>
                </div>
                <div class="metric-card">
                    <h3>❌ Error Count</h3>
                    <div class="metric-value">${overall.error_count}</div>
                    <div class="metric-label">Last Hour</div>
                </div>
            `;
        }
        
        function updateAgentPerformance(data) {
            const container = document.getElementById('agent-performance');
            const agents = data.agent_performance;
            
            let html = '';
            for (const [agentType, stats] of Object.entries(agents)) {
                if (stats.metrics === 'no_data') {
                    html += `
                        <div class="agent-card">
                            <h4>${agentType.replace('_', ' ')}</h4>
                            <p>No data available</p>
                        </div>
                    `;
                } else {
                    html += `
                        <div class="agent-card">
                            <h4>${agentType.replace('_', ' ')}</h4>
                            <div class="agent-stats">
                                <div class="agent-stat">
                                    <div class="agent-stat-value">${stats.total_calls}</div>
                                    <div class="agent-stat-label">Total Calls</div>
                                </div>
                                <div class="agent-stat">
                                    <div class="agent-stat-value">${stats.success_rate.toFixed(1)}%</div>
                                    <div class="agent-stat-label">Success Rate</div>
                                </div>
                                <div class="agent-stat">
                                    <div class="agent-stat-value">${stats.avg_total_duration.toFixed(2)}s</div>
                                    <div class="agent-stat-label">Avg Duration</div>
                                </div>
                                <div class="agent-stat">
                                    <div class="agent-stat-value">${stats.avg_llm_duration.toFixed(2)}s</div>
                                    <div class="agent-stat-label">LLM Time</div>
                                </div>
                            </div>
                        </div>
                    `;
                }
            }
            container.innerHTML = html;
        }
        
        function updatePerformanceChart(data) {
            const ctx = document.getElementById('performanceChart').getContext('2d');
            const trends = data.hourly_trends;
            
            if (performanceChart) {
                performanceChart.destroy();
            }
            
            performanceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: trends.map(t => new Date(t.timestamp).toLocaleTimeString()),
                    datasets: [{
                        label: 'Avg Duration (s)',
                        data: trends.map(t => t.avg_duration),
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4
                    }, {
                        label: 'Success Rate (%)',
                        data: trends.map(t => t.success_rate),
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y1'
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: { display: true, text: 'Duration (seconds)' }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: { display: true, text: 'Success Rate (%)' },
                            grid: { drawOnChartArea: false }
                        }
                    }
                }
            });
        }
        
        function updateAlerts(data) {
            const container = document.getElementById('alerts-container');
            const alerts = data.recent_alerts;
            
            if (alerts.length === 0) {
                container.innerHTML = '<p>No recent alerts 🎉</p>';
                return;
            }
            
            let html = '';
            alerts.forEach(alert => {
                html += `
                    <div class="alert-item alert-${alert.severity}">
                        <strong>${alert.type.replace('_', ' ').toUpperCase()}</strong>: ${alert.message}
                        <br><small>Trace: ${alert.trace_id} | ${new Date(alert.timestamp).toLocaleString()}</small>
                    </div>
                `;
            });
            container.innerHTML = html;
        }
        
        function getStatusClass(successRate) {
            if (successRate >= 95) return 'status-healthy';
            if (successRate >= 80) return 'status-warning';
            return 'status-error';
        }
        
        async function refreshDashboard() {
            const data = await fetchDashboardData();
            if (!data) return;
            
            updateOverallMetrics(data);
            updateAgentPerformance(data);
            updatePerformanceChart(data);
            updateAlerts(data);
            
            document.getElementById('last-updated').textContent = 
                `Last updated: ${new Date(data.timestamp).toLocaleString()}`;
        }
        
        // Initial load and auto-refresh
        refreshDashboard();
        setInterval(refreshDashboard, 30000); // Refresh every 30 seconds
    </script>
</body>
</html>
"""

class AlertManager:
    """Manages alerts and notifications for voice system"""
    
    def __init__(self):
        self.alert_rules = {
            "high_latency": {"threshold": 10, "severity": "warning"},
            "very_high_latency": {"threshold": 20, "severity": "error"},
            "low_success_rate": {"threshold": 80, "severity": "warning"},
            "very_low_success_rate": {"threshold": 50, "severity": "error"},
            "high_error_rate": {"threshold": 10, "severity": "warning"},
            "stt_slow": {"threshold": 5, "severity": "warning"},
            "llm_slow": {"threshold": 5, "severity": "warning"},
            "tts_slow": {"threshold": 3, "severity": "warning"}
        }
        
        self.notification_channels = []
        self.alert_history = []
        
    def check_system_health(self) -> List[Dict[str, Any]]:
        """Check overall system health and generate alerts"""
        alerts = []
        dashboard_data = get_voice_dashboard()
        overall = dashboard_data["overall_performance"]
        
        # Check success rate
        if overall["success_rate"] < self.alert_rules["very_low_success_rate"]["threshold"]:
            alerts.append({
                "type": "very_low_success_rate",
                "severity": "error",
                "message": f"Critical: Success rate is {overall['success_rate']:.1f}%",
                "timestamp": datetime.now().isoformat(),
                "value": overall["success_rate"]
            })
        elif overall["success_rate"] < self.alert_rules["low_success_rate"]["threshold"]:
            alerts.append({
                "type": "low_success_rate",
                "severity": "warning",
                "message": f"Warning: Success rate is {overall['success_rate']:.1f}%",
                "timestamp": datetime.now().isoformat(),
                "value": overall["success_rate"]
            })
        
        # Check latency
        if overall["avg_duration"] > self.alert_rules["very_high_latency"]["threshold"]:
            alerts.append({
                "type": "very_high_latency",
                "severity": "error",
                "message": f"Critical: Average latency is {overall['avg_duration']:.2f}s",
                "timestamp": datetime.now().isoformat(),
                "value": overall["avg_duration"]
            })
        elif overall["avg_duration"] > self.alert_rules["high_latency"]["threshold"]:
            alerts.append({
                "type": "high_latency",
                "severity": "warning",
                "message": f"Warning: Average latency is {overall['avg_duration']:.2f}s",
                "timestamp": datetime.now().isoformat(),
                "value": overall["avg_duration"]
            })
        
        # Check error rate
        if overall["total_calls"] > 0:
            error_rate = (overall["error_count"] / overall["total_calls"]) * 100
            if error_rate > self.alert_rules["high_error_rate"]["threshold"]:
                alerts.append({
                    "type": "high_error_rate",
                    "severity": "warning",
                    "message": f"Warning: Error rate is {error_rate:.1f}%",
                    "timestamp": datetime.now().isoformat(),
                    "value": error_rate
                })
        
        return alerts
    
    def send_alert(self, alert: Dict[str, Any]):
        """Send alert through configured channels"""
        # Add to history
        self.alert_history.append(alert)
        
        # Keep only last 1000 alerts
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
        
        # Send through notification channels
        for channel in self.notification_channels:
            try:
                channel.send(alert)
            except Exception as e:
                print(f"❌ Error sending alert through {channel}: {e}")

# Global alert manager
alert_manager = AlertManager()

# Flask routes
@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template_string(DASHBOARD_TEMPLATE)

@app.route('/api/dashboard')
def api_dashboard():
    """API endpoint for dashboard data"""
    return jsonify(get_voice_dashboard())

@app.route('/api/alerts')
def api_alerts():
    """API endpoint for alerts"""
    severity = request.args.get('severity')
    return jsonify(get_voice_alerts(severity))

@app.route('/api/metrics/agent/<agent_type>')
def api_agent_metrics(agent_type):
    """API endpoint for agent-specific metrics"""
    time_window = int(request.args.get('time_window', 60))
    return jsonify(voice_metrics.get_agent_performance(agent_type, time_window))

@app.route('/api/metrics/language/<language>')
def api_language_metrics(language):
    """API endpoint for language-specific metrics"""
    time_window = int(request.args.get('time_window', 60))
    return jsonify(voice_metrics.get_language_performance(language, time_window))

@app.route('/api/health')
def api_health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "metrics_collector": "active",
        "dashboard": "running",
        "alerts": len(alert_manager.alert_history)
    })

@app.route('/api/test/simulate')
def api_simulate_data():
    """Simulate voice interaction data for testing"""
    import random
    
    # Simulate 5 random interactions
    for i in range(5):
        record_voice_interaction(
            trace_id=f"test_trace_{int(time.time())}_{i}",
            user_id=f"test_user_{i % 3}",
            agent_type=random.choice(["customer_service", "sales", "rag_assistant"]),
            language=random.choice(["es_mx", "en_us"]),
            stt_duration=random.uniform(0.5, 3.0),
            llm_duration=random.uniform(1.0, 4.0),
            tts_duration=random.uniform(0.3, 1.5),
            transcript_length=random.randint(50, 200),
            response_length=random.randint(100, 300),
            audio_size=random.randint(50000, 200000),
            success=random.choice([True, True, True, False])  # 75% success rate
        )
    
    return jsonify({"message": "Simulated 5 voice interactions", "status": "success"})

def run_background_monitoring():
    """Background thread for continuous monitoring"""
    while True:
        try:
            # Check system health every minute
            alerts = alert_manager.check_system_health()
            for alert in alerts:
                alert_manager.send_alert(alert)
            
            time.sleep(60)  # Check every minute
            
        except Exception as e:
            print(f"❌ Error in background monitoring: {e}")
            time.sleep(60)

if __name__ == "__main__":
    print("🎤 Starting Voice System Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:5000")
    print("🔄 Auto-refresh every 30 seconds")
    print("🚨 Background monitoring active")
    
    # Start background monitoring thread
    monitoring_thread = threading.Thread(target=run_background_monitoring, daemon=True)
    monitoring_thread.start()
    
    # Run Flask app
    app.run(host="0.0.0.0", port=5000, debug=False)

