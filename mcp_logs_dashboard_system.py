#!/usr/bin/env python3
"""
MCP Enterprise - Sistema de Logs y Dashboard Completo
Dashboard web completo para visualización de logs, tareas y monitoreo
"""

import json
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LogsAndDashboardSystem:
    """Sistema completo de logs y dashboard"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.db_path = self.config.get("db_path", "mcp_enterprise_logs.db")
        
        # Inicializar base de datos
        self._init_database()
    
    def _init_database(self):
        """Inicializar base de datos de logs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de logs de sistema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                level TEXT,
                component TEXT,
                message TEXT,
                metadata TEXT,
                task_id TEXT,
                agent_id TEXT
            )
        ''')
        
        # Tabla de métricas de performance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                metric_name TEXT,
                metric_value REAL,
                metric_unit TEXT,
                component TEXT,
                task_id TEXT
            )
        ''')
        
        # Tabla de eventos de usuario
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_id TEXT,
                event_type TEXT,
                event_data TEXT,
                ip_address TEXT,
                user_agent TEXT
            )
        ''')
        
        # Tabla de alertas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                alert_type TEXT,
                severity TEXT,
                title TEXT,
                description TEXT,
                component TEXT,
                task_id TEXT,
                resolved BOOLEAN DEFAULT FALSE,
                resolved_at TEXT
            )
        ''')
        
        # Índices para performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_logs_task_id ON system_logs(task_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)')
        
        conn.commit()
        conn.close()
    
    def log_system_event(self, level: str, component: str, message: str, 
                        metadata: Dict[str, Any] = None, task_id: str = None, 
                        agent_id: str = None):
        """Registrar evento del sistema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO system_logs (timestamp, level, component, message, metadata, task_id, agent_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            level,
            component,
            message,
            json.dumps(metadata) if metadata else None,
            task_id,
            agent_id
        ))
        
        conn.commit()
        conn.close()
        
        # Log también en el sistema de logging estándar
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[{component}] {message}")
    
    def log_performance_metric(self, metric_name: str, metric_value: float, 
                              metric_unit: str, component: str, task_id: str = None):
        """Registrar métrica de performance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO performance_metrics (timestamp, metric_name, metric_value, metric_unit, component, task_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            metric_name,
            metric_value,
            metric_unit,
            component,
            task_id
        ))
        
        conn.commit()
        conn.close()
    
    def log_user_event(self, user_id: str, event_type: str, event_data: Dict[str, Any],
                      ip_address: str = None, user_agent: str = None):
        """Registrar evento de usuario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_events (timestamp, user_id, event_type, event_data, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            user_id,
            event_type,
            json.dumps(event_data),
            ip_address,
            user_agent
        ))
        
        conn.commit()
        conn.close()
    
    def create_alert(self, alert_type: str, severity: str, title: str, 
                    description: str, component: str, task_id: str = None):
        """Crear alerta"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (timestamp, alert_type, severity, title, description, component, task_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            alert_type,
            severity,
            title,
            description,
            component,
            task_id
        ))
        
        alert_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return alert_id
    
    def resolve_alert(self, alert_id: int):
        """Resolver alerta"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE alerts SET resolved = TRUE, resolved_at = ? WHERE id = ?
        ''', (datetime.now().isoformat(), alert_id))
        
        conn.commit()
        conn.close()
    
    def get_system_logs(self, limit: int = 100, level: str = None, 
                       component: str = None, task_id: str = None,
                       start_time: str = None, end_time: str = None) -> List[Dict]:
        """Obtener logs del sistema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM system_logs WHERE 1=1"
        params = []
        
        if level:
            query += " AND level = ?"
            params.append(level)
        
        if component:
            query += " AND component = ?"
            params.append(component)
        
        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Convertir a diccionarios
        columns = ['id', 'timestamp', 'level', 'component', 'message', 'metadata', 'task_id', 'agent_id']
        logs = []
        for row in rows:
            log_dict = dict(zip(columns, row))
            if log_dict['metadata']:
                log_dict['metadata'] = json.loads(log_dict['metadata'])
            logs.append(log_dict)
        
        return logs
    
    def get_performance_metrics(self, metric_name: str = None, component: str = None,
                               start_time: str = None, end_time: str = None,
                               limit: int = 1000) -> List[Dict]:
        """Obtener métricas de performance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM performance_metrics WHERE 1=1"
        params = []
        
        if metric_name:
            query += " AND metric_name = ?"
            params.append(metric_name)
        
        if component:
            query += " AND component = ?"
            params.append(component)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Convertir a diccionarios
        columns = ['id', 'timestamp', 'metric_name', 'metric_value', 'metric_unit', 'component', 'task_id']
        return [dict(zip(columns, row)) for row in rows]
    
    def get_alerts(self, resolved: bool = None, severity: str = None,
                  component: str = None, limit: int = 100) -> List[Dict]:
        """Obtener alertas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM alerts WHERE 1=1"
        params = []
        
        if resolved is not None:
            query += " AND resolved = ?"
            params.append(resolved)
        
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        
        if component:
            query += " AND component = ?"
            params.append(component)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Convertir a diccionarios
        columns = ['id', 'timestamp', 'alert_type', 'severity', 'title', 'description', 
                  'component', 'task_id', 'resolved', 'resolved_at']
        return [dict(zip(columns, row)) for row in rows]
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas para dashboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Estadísticas de logs por nivel (última hora)
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        cursor.execute('''
            SELECT level, COUNT(*) FROM system_logs 
            WHERE timestamp >= ? 
            GROUP BY level
        ''', (one_hour_ago,))
        log_stats = dict(cursor.fetchall())
        
        # Alertas activas por severidad
        cursor.execute('''
            SELECT severity, COUNT(*) FROM alerts 
            WHERE resolved = FALSE 
            GROUP BY severity
        ''')
        alert_stats = dict(cursor.fetchall())
        
        # Componentes más activos (última hora)
        cursor.execute('''
            SELECT component, COUNT(*) FROM system_logs 
            WHERE timestamp >= ? 
            GROUP BY component 
            ORDER BY COUNT(*) DESC 
            LIMIT 10
        ''', (one_hour_ago,))
        active_components = dict(cursor.fetchall())
        
        # Métricas de performance promedio (última hora)
        cursor.execute('''
            SELECT metric_name, AVG(metric_value), metric_unit FROM performance_metrics 
            WHERE timestamp >= ? 
            GROUP BY metric_name, metric_unit
        ''', (one_hour_ago,))
        avg_metrics = {}
        for row in cursor.fetchall():
            avg_metrics[row[0]] = {"value": row[1], "unit": row[2]}
        
        # Total de eventos por tipo (último día)
        one_day_ago = (datetime.now() - timedelta(days=1)).isoformat()
        cursor.execute('''
            SELECT event_type, COUNT(*) FROM user_events 
            WHERE timestamp >= ? 
            GROUP BY event_type
        ''', (one_day_ago,))
        user_event_stats = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "log_stats": log_stats,
            "alert_stats": alert_stats,
            "active_components": active_components,
            "avg_metrics": avg_metrics,
            "user_event_stats": user_event_stats,
            "timestamp": datetime.now().isoformat()
        }

# Flask app para dashboard
app = Flask(__name__)
CORS(app)

# Instancia global del sistema de logs
logs_system = None

def init_logs_system(config: Dict[str, Any] = None):
    """Inicializar sistema de logs"""
    global logs_system
    
    if logs_system is None:
        logs_system = LogsAndDashboardSystem(config)

# Template HTML para dashboard
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Enterprise Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .card { @apply bg-white rounded-lg shadow-md p-6 mb-6; }
        .metric-card { @apply bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg p-4; }
        .alert-critical { @apply bg-red-100 border-l-4 border-red-500 text-red-700 p-4; }
        .alert-warning { @apply bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4; }
        .alert-info { @apply bg-blue-100 border-l-4 border-blue-500 text-blue-700 p-4; }
        .log-error { @apply text-red-600; }
        .log-warning { @apply text-yellow-600; }
        .log-info { @apply text-blue-600; }
        .log-debug { @apply text-gray-600; }
    </style>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="mb-8">
            <h1 class="text-4xl font-bold text-gray-800 mb-2">🔍 MCP Enterprise Dashboard</h1>
            <p class="text-gray-600">Sistema de monitoreo y logs en tiempo real</p>
            <div class="text-sm text-gray-500">Última actualización: <span id="lastUpdate"></span></div>
        </div>

        <!-- Métricas principales -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div class="metric-card">
                <h3 class="text-lg font-semibold mb-2">📊 Logs/Hora</h3>
                <div class="text-3xl font-bold" id="logsPerHour">-</div>
            </div>
            <div class="metric-card">
                <h3 class="text-lg font-semibold mb-2">🚨 Alertas Activas</h3>
                <div class="text-3xl font-bold" id="activeAlerts">-</div>
            </div>
            <div class="metric-card">
                <h3 class="text-lg font-semibold mb-2">⚡ Tareas Activas</h3>
                <div class="text-3xl font-bold" id="activeTasks">-</div>
            </div>
            <div class="metric-card">
                <h3 class="text-lg font-semibold mb-2">🎯 Uptime</h3>
                <div class="text-3xl font-bold" id="systemUptime">99.9%</div>
            </div>
        </div>

        <!-- Gráficos -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div class="card">
                <h3 class="text-xl font-semibold mb-4">📈 Logs por Nivel (Última Hora)</h3>
                <canvas id="logsChart" width="400" height="200"></canvas>
            </div>
            <div class="card">
                <h3 class="text-xl font-semibold mb-4">⚡ Performance Metrics</h3>
                <canvas id="metricsChart" width="400" height="200"></canvas>
            </div>
        </div>

        <!-- Alertas activas -->
        <div class="card">
            <h3 class="text-xl font-semibold mb-4">🚨 Alertas Activas</h3>
            <div id="alertsContainer">
                <div class="text-gray-500">Cargando alertas...</div>
            </div>
        </div>

        <!-- Logs recientes -->
        <div class="card">
            <h3 class="text-xl font-semibold mb-4">📝 Logs Recientes</h3>
            <div class="mb-4">
                <select id="logLevelFilter" class="border rounded px-3 py-2 mr-2">
                    <option value="">Todos los niveles</option>
                    <option value="ERROR">Error</option>
                    <option value="WARNING">Warning</option>
                    <option value="INFO">Info</option>
                    <option value="DEBUG">Debug</option>
                </select>
                <select id="componentFilter" class="border rounded px-3 py-2 mr-2">
                    <option value="">Todos los componentes</option>
                </select>
                <button onclick="refreshLogs()" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
                    🔄 Actualizar
                </button>
            </div>
            <div id="logsContainer" class="max-h-96 overflow-y-auto">
                <div class="text-gray-500">Cargando logs...</div>
            </div>
        </div>

        <!-- Componentes activos -->
        <div class="card">
            <h3 class="text-xl font-semibold mb-4">🔧 Componentes Más Activos</h3>
            <div id="componentsContainer">
                <div class="text-gray-500">Cargando componentes...</div>
            </div>
        </div>
    </div>

    <script>
        let logsChart, metricsChart;
        
        // Inicializar dashboard
        document.addEventListener('DOMContentLoaded', function() {
            initCharts();
            loadDashboardData();
            
            // Auto-refresh cada 30 segundos
            setInterval(loadDashboardData, 30000);
            
            // Event listeners para filtros
            document.getElementById('logLevelFilter').addEventListener('change', refreshLogs);
            document.getElementById('componentFilter').addEventListener('change', refreshLogs);
        });
        
        function initCharts() {
            // Gráfico de logs por nivel
            const logsCtx = document.getElementById('logsChart').getContext('2d');
            logsChart = new Chart(logsCtx, {
                type: 'doughnut',
                data: {
                    labels: ['ERROR', 'WARNING', 'INFO', 'DEBUG'],
                    datasets: [{
                        data: [0, 0, 0, 0],
                        backgroundColor: ['#ef4444', '#f59e0b', '#3b82f6', '#6b7280']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
            
            // Gráfico de métricas
            const metricsCtx = document.getElementById('metricsChart').getContext('2d');
            metricsChart = new Chart(metricsCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Response Time (ms)',
                        data: [],
                        borderColor: '#3b82f6',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        
        async function loadDashboardData() {
            try {
                // Cargar estadísticas principales
                const statsResponse = await fetch('/api/dashboard/stats');
                const stats = await statsResponse.json();
                
                updateMainMetrics(stats);
                updateCharts(stats);
                
                // Cargar alertas
                const alertsResponse = await fetch('/api/alerts?resolved=false');
                const alerts = await alertsResponse.json();
                updateAlerts(alerts);
                
                // Cargar logs
                refreshLogs();
                
                // Cargar componentes
                updateComponents(stats.active_components);
                
                // Actualizar timestamp
                document.getElementById('lastUpdate').textContent = new Date().toLocaleString();
                
            } catch (error) {
                console.error('Error loading dashboard data:', error);
            }
        }
        
        function updateMainMetrics(stats) {
            const totalLogs = Object.values(stats.log_stats || {}).reduce((a, b) => a + b, 0);
            const totalAlerts = Object.values(stats.alert_stats || {}).reduce((a, b) => a + b, 0);
            
            document.getElementById('logsPerHour').textContent = totalLogs;
            document.getElementById('activeAlerts').textContent = totalAlerts;
            document.getElementById('activeTasks').textContent = Object.keys(stats.avg_metrics || {}).length;
        }
        
        function updateCharts(stats) {
            // Actualizar gráfico de logs
            const logStats = stats.log_stats || {};
            logsChart.data.datasets[0].data = [
                logStats.ERROR || 0,
                logStats.WARNING || 0,
                logStats.INFO || 0,
                logStats.DEBUG || 0
            ];
            logsChart.update();
            
            // Actualizar gráfico de métricas (simulado)
            const now = new Date();
            const timeLabel = now.toLocaleTimeString();
            
            if (metricsChart.data.labels.length > 20) {
                metricsChart.data.labels.shift();
                metricsChart.data.datasets[0].data.shift();
            }
            
            metricsChart.data.labels.push(timeLabel);
            metricsChart.data.datasets[0].data.push(Math.random() * 100 + 50);
            metricsChart.update();
        }
        
        function updateAlerts(alerts) {
            const container = document.getElementById('alertsContainer');
            
            if (alerts.length === 0) {
                container.innerHTML = '<div class="text-green-600">✅ No hay alertas activas</div>';
                return;
            }
            
            const alertsHtml = alerts.map(alert => {
                const alertClass = alert.severity === 'critical' ? 'alert-critical' : 
                                 alert.severity === 'warning' ? 'alert-warning' : 'alert-info';
                
                return `
                    <div class="${alertClass} mb-2">
                        <div class="font-semibold">${alert.title}</div>
                        <div class="text-sm">${alert.description}</div>
                        <div class="text-xs mt-1">
                            ${alert.component} • ${new Date(alert.timestamp).toLocaleString()}
                            <button onclick="resolveAlert(${alert.id})" class="ml-2 text-xs underline">
                                Resolver
                            </button>
                        </div>
                    </div>
                `;
            }).join('');
            
            container.innerHTML = alertsHtml;
        }
        
        async function refreshLogs() {
            try {
                const level = document.getElementById('logLevelFilter').value;
                const component = document.getElementById('componentFilter').value;
                
                let url = '/api/logs?limit=50';
                if (level) url += `&level=${level}`;
                if (component) url += `&component=${component}`;
                
                const response = await fetch(url);
                const logs = await response.json();
                
                updateLogs(logs);
                
            } catch (error) {
                console.error('Error loading logs:', error);
            }
        }
        
        function updateLogs(logs) {
            const container = document.getElementById('logsContainer');
            
            if (logs.length === 0) {
                container.innerHTML = '<div class="text-gray-500">No hay logs disponibles</div>';
                return;
            }
            
            const logsHtml = logs.map(log => {
                const levelClass = `log-${log.level.toLowerCase()}`;
                
                return `
                    <div class="border-b py-2">
                        <div class="flex justify-between items-start">
                            <div class="flex-1">
                                <span class="${levelClass} font-semibold">[${log.level}]</span>
                                <span class="text-gray-600">[${log.component}]</span>
                                <span class="ml-2">${log.message}</span>
                            </div>
                            <div class="text-xs text-gray-500">
                                ${new Date(log.timestamp).toLocaleString()}
                            </div>
                        </div>
                        ${log.task_id ? `<div class="text-xs text-gray-500 mt-1">Task: ${log.task_id}</div>` : ''}
                    </div>
                `;
            }).join('');
            
            container.innerHTML = logsHtml;
        }
        
        function updateComponents(components) {
            const container = document.getElementById('componentsContainer');
            
            if (!components || Object.keys(components).length === 0) {
                container.innerHTML = '<div class="text-gray-500">No hay componentes activos</div>';
                return;
            }
            
            const componentsHtml = Object.entries(components)
                .sort(([,a], [,b]) => b - a)
                .map(([component, count]) => `
                    <div class="flex justify-between items-center py-2 border-b">
                        <span class="font-medium">${component}</span>
                        <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">${count} eventos</span>
                    </div>
                `).join('');
            
            container.innerHTML = componentsHtml;
            
            // Actualizar filtro de componentes
            const componentFilter = document.getElementById('componentFilter');
            const currentValue = componentFilter.value;
            
            componentFilter.innerHTML = '<option value="">Todos los componentes</option>' +
                Object.keys(components).map(component => 
                    `<option value="${component}">${component}</option>`
                ).join('');
            
            componentFilter.value = currentValue;
        }
        
        async function resolveAlert(alertId) {
            try {
                await fetch(`/api/alerts/${alertId}/resolve`, { method: 'POST' });
                loadDashboardData(); // Refresh data
            } catch (error) {
                console.error('Error resolving alert:', error);
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    """Dashboard principal"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/health')
def health():
    """Health check"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Obtener logs del sistema"""
    limit = int(request.args.get('limit', 100))
    level = request.args.get('level')
    component = request.args.get('component')
    task_id = request.args.get('task_id')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    
    logs = logs_system.get_system_logs(
        limit=limit,
        level=level,
        component=component,
        task_id=task_id,
        start_time=start_time,
        end_time=end_time
    )
    
    return jsonify(logs)

@app.route('/api/logs', methods=['POST'])
def create_log():
    """Crear nuevo log"""
    data = request.json
    
    logs_system.log_system_event(
        level=data['level'],
        component=data['component'],
        message=data['message'],
        metadata=data.get('metadata'),
        task_id=data.get('task_id'),
        agent_id=data.get('agent_id')
    )
    
    return jsonify({"status": "logged"})

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Obtener métricas de performance"""
    metric_name = request.args.get('metric_name')
    component = request.args.get('component')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    limit = int(request.args.get('limit', 1000))
    
    metrics = logs_system.get_performance_metrics(
        metric_name=metric_name,
        component=component,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    return jsonify(metrics)

@app.route('/api/metrics', methods=['POST'])
def create_metric():
    """Crear nueva métrica"""
    data = request.json
    
    logs_system.log_performance_metric(
        metric_name=data['metric_name'],
        metric_value=data['metric_value'],
        metric_unit=data['metric_unit'],
        component=data['component'],
        task_id=data.get('task_id')
    )
    
    return jsonify({"status": "logged"})

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Obtener alertas"""
    resolved = request.args.get('resolved')
    if resolved is not None:
        resolved = resolved.lower() == 'true'
    
    severity = request.args.get('severity')
    component = request.args.get('component')
    limit = int(request.args.get('limit', 100))
    
    alerts = logs_system.get_alerts(
        resolved=resolved,
        severity=severity,
        component=component,
        limit=limit
    )
    
    return jsonify(alerts)

@app.route('/api/alerts', methods=['POST'])
def create_alert():
    """Crear nueva alerta"""
    data = request.json
    
    alert_id = logs_system.create_alert(
        alert_type=data['alert_type'],
        severity=data['severity'],
        title=data['title'],
        description=data['description'],
        component=data['component'],
        task_id=data.get('task_id')
    )
    
    return jsonify({"alert_id": alert_id, "status": "created"})

@app.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Resolver alerta"""
    logs_system.resolve_alert(alert_id)
    return jsonify({"status": "resolved"})

@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    """Obtener estadísticas para dashboard"""
    return jsonify(logs_system.get_dashboard_stats())

@app.route('/api/user-events', methods=['POST'])
def log_user_event():
    """Registrar evento de usuario"""
    data = request.json
    
    logs_system.log_user_event(
        user_id=data['user_id'],
        event_type=data['event_type'],
        event_data=data['event_data'],
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    
    return jsonify({"status": "logged"})

def main():
    """Función principal"""
    print("📊 Iniciando Sistema de Logs y Dashboard...")
    
    # Configuración
    config = {
        "db_path": "mcp_enterprise_logs.db"
    }
    
    # Inicializar sistema
    init_logs_system(config)
    
    # Crear algunos logs de ejemplo
    logs_system.log_system_event("INFO", "dashboard", "Sistema de dashboard iniciado")
    logs_system.log_system_event("INFO", "webhook_monitor", "Monitor de webhooks activo")
    logs_system.log_performance_metric("response_time", 45.2, "ms", "api_server")
    logs_system.create_alert("system", "info", "Sistema iniciado", "El dashboard se ha iniciado correctamente", "dashboard")
    
    print("✅ Sistema de logs y dashboard iniciado")
    print("🌐 Dashboard disponible en: http://localhost:8126")
    print("📊 API disponible en: http://localhost:8126/api/")
    print("📝 Endpoints disponibles:")
    print("   GET  / - Dashboard web")
    print("   GET  /api/logs - Obtener logs")
    print("   POST /api/logs - Crear log")
    print("   GET  /api/metrics - Obtener métricas")
    print("   POST /api/metrics - Crear métrica")
    print("   GET  /api/alerts - Obtener alertas")
    print("   POST /api/alerts - Crear alerta")
    print("   GET  /api/dashboard/stats - Estadísticas")
    
    # Iniciar servidor
    app.run(host='0.0.0.0', port=8126, debug=False)

if __name__ == "__main__":
    main()

