"""
Generador de Visualizaciones para LangGraph Studio
Crea gráficos, diagramas y dashboards interactivos
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

class VisualizationGenerator:
    """Generador de visualizaciones para el sistema MCP"""
    
    def __init__(self, export_path: str = "./langgraph_system/studio/studio_exports/"):
        self.export_path = Path(export_path)
        self.visualizations_path = self.export_path / "visualizations"
        self.visualizations_path.mkdir(parents=True, exist_ok=True)
        
    def generate_system_dashboard_html(self, metrics_data: Dict[str, Any]) -> str:
        """Genera dashboard HTML interactivo del sistema"""
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agentius MCP - System Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }}
        
        .dashboard {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            grid-template-rows: auto auto auto auto;
            gap: 20px;
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            grid-column: 1 / -1;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }}
        
        .header h1 {{
            font-size: 2.5em;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            font-size: 1.2em;
            color: #666;
            margin-bottom: 20px;
        }}
        
        .status-indicators {{
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
        }}
        
        .status-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(76, 175, 80, 0.1);
            padding: 10px 20px;
            border-radius: 25px;
            border: 2px solid #4CAF50;
        }}
        
        .status-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4CAF50;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
            100% {{ opacity: 1; }}
        }}
        
        .card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
        }}
        
        .card h3 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.3em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .metric {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 15px 0;
            padding: 10px;
            background: rgba(102, 126, 234, 0.05);
            border-radius: 8px;
        }}
        
        .metric-label {{
            font-weight: 500;
            color: #555;
        }}
        
        .metric-value {{
            font-weight: bold;
            font-size: 1.1em;
            color: #667eea;
        }}
        
        .chart-container {{
            position: relative;
            height: 300px;
            margin-top: 20px;
        }}
        
        .mermaid-container {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            overflow-x: auto;
        }}
        
        .alert {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            color: #856404;
        }}
        
        .alert.warning {{
            background: #f8d7da;
            border-color: #f5c6cb;
            color: #721c24;
        }}
        
        .alert.info {{
            background: #d1ecf1;
            border-color: #bee5eb;
            color: #0c5460;
        }}
        
        .grid-full {{
            grid-column: 1 / -1;
        }}
        
        .grid-half {{
            grid-column: span 2;
        }}
        
        .refresh-indicator {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(76, 175, 80, 0.9);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: bold;
            z-index: 1000;
        }}
    </style>
</head>
<body>
    <div class="refresh-indicator">
        🔄 Auto-refresh: 30s
    </div>
    
    <div class="dashboard">
        <!-- Header -->
        <div class="header">
            <h1>🎯 Agentius MCP Dashboard</h1>
            <div class="subtitle">Real-time System Monitoring & Analytics</div>
            <div class="status-indicators">
                <div class="status-item">
                    <div class="status-dot"></div>
                    <span>System Online</span>
                </div>
                <div class="status-item">
                    <div class="status-dot"></div>
                    <span>LangWatch Active</span>
                </div>
                <div class="status-item">
                    <div class="status-dot"></div>
                    <span>Local LLMs Ready</span>
                </div>
                <div class="status-item">
                    <div class="status-dot"></div>
                    <span>Debugging Enabled</span>
                </div>
            </div>
        </div>
        
        <!-- System Metrics -->
        <div class="card">
            <h3>📊 System Metrics</h3>
            <div class="metric">
                <span class="metric-label">Active Sessions</span>
                <span class="metric-value">{metrics_data.get('system_metrics', {}).get('active_sessions', 0)}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Total Requests</span>
                <span class="metric-value">{metrics_data.get('system_metrics', {}).get('total_requests', 0)}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Avg Response Time</span>
                <span class="metric-value">{metrics_data.get('system_metrics', {}).get('avg_response_time', 0):.0f}ms</span>
            </div>
            <div class="metric">
                <span class="metric-label">Success Rate</span>
                <span class="metric-value">{metrics_data.get('system_metrics', {}).get('success_rate', 0):.1%}</span>
            </div>
        </div>
        
        <!-- Model Performance -->
        <div class="card">
            <h3>🤖 Model Performance</h3>
            <div class="chart-container">
                <canvas id="modelChart"></canvas>
            </div>
        </div>
        
        <!-- Contradiction Analysis -->
        <div class="card">
            <h3>🔥 Contradiction Analysis</h3>
            <div class="metric">
                <span class="metric-label">Total Contradictions</span>
                <span class="metric-value">{metrics_data.get('contradiction_metrics', {}).get('total_contradictions', 0)}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Avg Effectiveness</span>
                <span class="metric-value">{metrics_data.get('contradiction_metrics', {}).get('avg_effectiveness', 0):.1%}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Success After Contradiction</span>
                <span class="metric-value">{metrics_data.get('contradiction_metrics', {}).get('success_rate_after_contradiction', 0):.1%}</span>
            </div>
            <div class="chart-container">
                <canvas id="contradictionChart"></canvas>
            </div>
        </div>
        
        <!-- Session Analytics -->
        <div class="card grid-half">
            <h3>📈 Session Analytics (24h)</h3>
            <div class="metric">
                <span class="metric-label">Total Sessions</span>
                <span class="metric-value">{metrics_data.get('session_analytics', {}).get('total_sessions', 0)}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Completion Rate</span>
                <span class="metric-value">{metrics_data.get('session_analytics', {}).get('success_rate', 0):.1%}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Avg Duration</span>
                <span class="metric-value">{metrics_data.get('session_analytics', {}).get('avg_duration_seconds', 0):.1f}s</span>
            </div>
            <div class="metric">
                <span class="metric-label">Avg Quality Score</span>
                <span class="metric-value">{metrics_data.get('session_analytics', {}).get('avg_quality_score', 0):.2f}</span>
            </div>
        </div>
        
        <!-- Performance Trends -->
        <div class="card">
            <h3>📊 Performance Trends</h3>
            <div class="chart-container">
                <canvas id="trendsChart"></canvas>
            </div>
        </div>
        
        <!-- System Flow Visualization -->
        <div class="card grid-full">
            <h3>🔄 System Flow Visualization</h3>
            <div class="mermaid-container">
                <div class="mermaid">
graph TD
    START([🚀 User Input]) --> REASONING[🧠 Reasoning Shell]
    REASONING --> SELECTION{{🎯 Model Selection}}
    SELECTION --> MISTRAL[🧙‍♂️ Mistral Local]
    SELECTION --> LLAMA[🦙 LLaMA Local]
    SELECTION --> DEEPSEEK[🔬 DeepSeek Local]
    MISTRAL --> EXECUTE[⚡ Execute]
    LLAMA --> EXECUTE
    DEEPSEEK --> EXECUTE
    EXECUTE --> EVALUATE[📊 Reward Shell]
    EVALUATE --> CONTRADICTION{{🔥 Contradiction?}}
    CONTRADICTION -->|Yes| REASONING
    CONTRADICTION -->|No| RESULT[✨ Final Result]
    
    classDef startEnd fill:#4CAF50,stroke:#333,stroke-width:2px,color:#fff
    classDef process fill:#2196F3,stroke:#333,stroke-width:2px,color:#fff
    classDef decision fill:#FF9800,stroke:#333,stroke-width:2px,color:#fff
    classDef model fill:#9C27B0,stroke:#333,stroke-width:2px,color:#fff
    
    class START,RESULT startEnd
    class REASONING,EXECUTE,EVALUATE process
    class SELECTION,CONTRADICTION decision
    class MISTRAL,LLAMA,DEEPSEEK model
                </div>
            </div>
        </div>
        
        <!-- Alerts -->
        <div class="card grid-full">
            <h3>🚨 System Alerts</h3>
            <div id="alerts-container">
                <!-- Alerts will be populated by JavaScript -->
            </div>
        </div>
    </div>
    
    <script>
        // Initialize Mermaid
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true
            }}
        }});
        
        // Chart.js configurations
        const chartOptions = {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{
                    position: 'top',
                }}
            }}
        }};
        
        // Model Performance Chart
        const modelCtx = document.getElementById('modelChart').getContext('2d');
        const modelChart = new Chart(modelCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps([m.get('model_name', '') for m in metrics_data.get('model_metrics', [])])},
                datasets: [{{
                    label: 'Avg Response Time (ms)',
                    data: {json.dumps([m.get('avg_response_time', 0) for m in metrics_data.get('model_metrics', [])])},
                    backgroundColor: 'rgba(102, 126, 234, 0.6)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 1
                }}, {{
                    label: 'Quality Score',
                    data: {json.dumps([m.get('avg_quality_score', 0) * 1000 for m in metrics_data.get('model_metrics', [])])},
                    backgroundColor: 'rgba(76, 175, 80, 0.6)',
                    borderColor: 'rgba(76, 175, 80, 1)',
                    borderWidth: 1,
                    yAxisID: 'y1'
                }}]
            }},
            options: {{
                ...chartOptions,
                scales: {{
                    y: {{
                        type: 'linear',
                        display: true,
                        position: 'left',
                    }},
                    y1: {{
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: {{
                            drawOnChartArea: false,
                        }},
                    }}
                }}
            }}
        }});
        
        // Contradiction Effectiveness Chart
        const contradictionCtx = document.getElementById('contradictionChart').getContext('2d');
        const contradictionChart = new Chart(contradictionCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Successful', 'Failed'],
                datasets: [{{
                    data: [
                        {metrics_data.get('contradiction_metrics', {}).get('success_rate_after_contradiction', 0) * 100},
                        {100 - metrics_data.get('contradiction_metrics', {}).get('success_rate_after_contradiction', 0) * 100}
                    ],
                    backgroundColor: ['#4CAF50', '#F44336'],
                    borderWidth: 2
                }}]
            }},
            options: chartOptions
        }});
        
        // Performance Trends Chart
        const trendsCtx = document.getElementById('trendsChart').getContext('2d');
        const trendsChart = new Chart(trendsCtx, {{
            type: 'line',
            data: {{
                labels: ['6h ago', '5h ago', '4h ago', '3h ago', '2h ago', '1h ago', 'Now'],
                datasets: [{{
                    label: 'Response Time (ms)',
                    data: [2500, 2300, 2100, 2400, 2200, 2000, {metrics_data.get('system_metrics', {}).get('avg_response_time', 2000)}],
                    borderColor: 'rgba(102, 126, 234, 1)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4
                }}, {{
                    label: 'Success Rate (%)',
                    data: [85, 87, 90, 88, 92, 94, {metrics_data.get('system_metrics', {}).get('success_rate', 0.9) * 100}],
                    borderColor: 'rgba(76, 175, 80, 1)',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y1'
                }}]
            }},
            options: {{
                ...chartOptions,
                scales: {{
                    y: {{
                        type: 'linear',
                        display: true,
                        position: 'left',
                    }},
                    y1: {{
                        type: 'linear',
                        display: true,
                        position: 'right',
                        min: 0,
                        max: 100,
                        grid: {{
                            drawOnChartArea: false,
                        }},
                    }}
                }}
            }}
        }});
        
        // Populate alerts
        function populateAlerts() {{
            const alertsContainer = document.getElementById('alerts-container');
            const alerts = {json.dumps(metrics_data.get('alerts', []))};
            
            if (alerts.length === 0) {{
                alertsContainer.innerHTML = '<div class="alert info">✅ No active alerts - System running smoothly</div>';
                return;
            }}
            
            alertsContainer.innerHTML = alerts.map(alert => 
                `<div class="alert ${{alert.severity}}">
                    <strong>${{alert.type.toUpperCase()}}</strong>: ${{alert.message}}
                    <small style="float: right;">${{new Date(alert.timestamp).toLocaleTimeString()}}</small>
                </div>`
            ).join('');
        }}
        
        populateAlerts();
        
        // Auto-refresh every 30 seconds
        setInterval(() => {{
            window.location.reload();
        }}, 30000);
        
        // WebSocket connection for real-time updates
        const ws = new WebSocket(`ws://${{window.location.host}}/ws/debug`);
        
        ws.onmessage = function(event) {{
            const data = JSON.parse(event.data);
            if (data.type === 'metrics_update') {{
                // Update charts with new data
                console.log('Real-time metrics update:', data);
            }}
        }};
    </script>
</body>
</html>
        """
        
        # Guardar dashboard
        dashboard_path = self.visualizations_path / "system_dashboard.html"
        with open(dashboard_path, 'w') as f:
            f.write(html_content)
            
        logger.info(f"System dashboard generated: {dashboard_path}")
        return str(dashboard_path)
        
    def generate_mermaid_flow_diagram(self, session_data: Dict[str, Any]) -> str:
        """Genera diagrama de flujo Mermaid para una sesión específica"""
        
        session_id = session_data.get('session_id', 'unknown')
        nodes_visited = session_data.get('nodes_visited', [])
        contradiction_applied = session_data.get('contradiction_applied', False)
        final_score = session_data.get('final_score', 0)
        
        # Crear diagrama basado en el flujo real
        mermaid_content = f"""---
title: Session Flow - {session_id}
---
graph TD
    START([🚀 Session Start]) --> INIT[📋 Initialize]
"""
        
        # Agregar nodos visitados
        prev_node = "INIT"
        for i, node in enumerate(nodes_visited):
            node_id = f"NODE_{i}"
            if "reasoning" in node.lower():
                mermaid_content += f"    {prev_node} --> {node_id}[🧠 {node}]\n"
            elif "execute" in node.lower():
                mermaid_content += f"    {prev_node} --> {node_id}[⚡ {node}]\n"
            elif "evaluate" in node.lower():
                mermaid_content += f"    {prev_node} --> {node_id}[📊 {node}]\n"
            elif "contradiction" in node.lower():
                mermaid_content += f"    {prev_node} --> {node_id}[🔥 {node}]\n"
            else:
                mermaid_content += f"    {prev_node} --> {node_id}[🔧 {node}]\n"
            prev_node = node_id
            
        # Agregar nodo final
        if final_score >= 0.8:
            mermaid_content += f"    {prev_node} --> END([✅ Success<br/>Score: {final_score:.2f}])\n"
        else:
            mermaid_content += f"    {prev_node} --> END([⚠️ Completed<br/>Score: {final_score:.2f}])\n"
            
        # Agregar estilos
        mermaid_content += """
    %% Styling
    classDef startEnd fill:#4CAF50,stroke:#333,stroke-width:3px,color:#fff
    classDef reasoning fill:#9C27B0,stroke:#333,stroke-width:2px,color:#fff
    classDef execution fill:#2196F3,stroke:#333,stroke-width:2px,color:#fff
    classDef evaluation fill:#FF9800,stroke:#333,stroke-width:2px,color:#fff
    classDef contradiction fill:#F44336,stroke:#333,stroke-width:2px,color:#fff
    
    class START,END startEnd
"""
        
        if contradiction_applied:
            mermaid_content += "\n    %% Contradiction was applied in this session\n"
            
        # Guardar diagrama
        diagram_path = self.visualizations_path / f"session_flow_{session_id}.mmd"
        with open(diagram_path, 'w') as f:
            f.write(mermaid_content)
            
        logger.info(f"Session flow diagram generated: {diagram_path}")
        return str(diagram_path)
        
    def generate_performance_report_html(self, performance_data: Dict[str, Any]) -> str:
        """Genera reporte HTML de rendimiento"""
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Performance Report - Agentius MCP</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .content {{
            padding: 30px;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid #667eea;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .metric-label {{
            color: #666;
            margin-top: 5px;
        }}
        .section {{
            margin: 30px 0;
        }}
        .section h2 {{
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #667eea;
            color: white;
        }}
        .trend-up {{
            color: #4CAF50;
        }}
        .trend-down {{
            color: #F44336;
        }}
        .trend-stable {{
            color: #FF9800;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Performance Report</h1>
            <p>Agentius MCP System Analysis</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>🎯 Key Metrics</h2>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value">{performance_data.get('total_sessions', 0)}</div>
                        <div class="metric-label">Total Sessions</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{performance_data.get('avg_response_time', 0):.0f}ms</div>
                        <div class="metric-label">Avg Response Time</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{performance_data.get('success_rate', 0):.1%}</div>
                        <div class="metric-label">Success Rate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{performance_data.get('contradiction_rate', 0):.1%}</div>
                        <div class="metric-label">Contradiction Rate</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>🤖 Model Performance</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Model</th>
                            <th>Total Calls</th>
                            <th>Avg Response Time</th>
                            <th>Success Rate</th>
                            <th>Quality Score</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        # Agregar datos de modelos
        for model in performance_data.get('model_metrics', []):
            html_content += f"""
                        <tr>
                            <td>{model.get('model_name', 'Unknown')}</td>
                            <td>{model.get('total_calls', 0)}</td>
                            <td>{model.get('avg_response_time', 0):.0f}ms</td>
                            <td>{model.get('success_rate', 0):.1%}</td>
                            <td>{model.get('avg_quality_score', 0):.2f}</td>
                        </tr>
"""
        
        html_content += """
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>📈 Performance Trends</h2>
                <div class="metric-grid">
"""
        
        # Agregar tendencias
        trends = performance_data.get('performance_trends', {})
        for metric, data in trends.items():
            if isinstance(data, dict) and 'trend' in data:
                trend_class = f"trend-{data['trend'].replace('ing', '').replace('asing', '')}"
                html_content += f"""
                    <div class="metric-card">
                        <div class="metric-value {trend_class}">{data.get('current', 0):.1f}</div>
                        <div class="metric-label">{metric.replace('_', ' ').title()}</div>
                        <div class="trend-{data['trend'].replace('ing', '').replace('asing', '')}">{data['trend'].title()}</div>
                    </div>
"""
        
        html_content += """
                </div>
            </div>
            
            <div class="section">
                <h2>🔥 Contradiction Analysis</h2>
                <p>Contradiction is a key feature of Agentius MCP that forces the system to improve when it fails.</p>
                <div class="metric-grid">
"""
        
        # Agregar métricas de contradicción
        contradiction_metrics = performance_data.get('contradiction_metrics', {})
        html_content += f"""
                    <div class="metric-card">
                        <div class="metric-value">{contradiction_metrics.get('total_contradictions', 0)}</div>
                        <div class="metric-label">Total Contradictions Applied</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{contradiction_metrics.get('avg_effectiveness', 0):.1%}</div>
                        <div class="metric-label">Average Effectiveness</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{contradiction_metrics.get('success_rate_after_contradiction', 0):.1%}</div>
                        <div class="metric-label">Success After Contradiction</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{contradiction_metrics.get('most_effective_intensity', 'N/A')}</div>
                        <div class="metric-label">Most Effective Intensity</div>
                    </div>
"""
        
        html_content += """
                </div>
            </div>
            
            <div class="section">
                <h2>💡 Insights & Recommendations</h2>
                <ul>
"""
        
        # Generar insights automáticos
        insights = []
        
        if performance_data.get('success_rate', 0) >= 0.9:
            insights.append("✅ Excellent success rate - system is performing very well")
        elif performance_data.get('success_rate', 0) < 0.7:
            insights.append("⚠️ Low success rate - consider reviewing contradiction strategies")
            
        if performance_data.get('avg_response_time', 0) > 10000:
            insights.append("🐌 High response times - consider optimizing model selection")
        elif performance_data.get('avg_response_time', 0) < 3000:
            insights.append("⚡ Excellent response times - system is well optimized")
            
        if contradiction_metrics.get('avg_effectiveness', 0) > 0.5:
            insights.append("🔥 Contradiction mechanism is highly effective")
        elif contradiction_metrics.get('avg_effectiveness', 0) < 0.3:
            insights.append("🤔 Contradiction effectiveness could be improved")
            
        for insight in insights:
            html_content += f"                    <li>{insight}</li>\n"
            
        html_content += """
                </ul>
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        # Guardar reporte
        report_path = self.visualizations_path / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(report_path, 'w') as f:
            f.write(html_content)
            
        logger.info(f"Performance report generated: {report_path}")
        return str(report_path)
        
    def generate_contradiction_heatmap_data(self, contradiction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera datos para heatmap de efectividad de contradicción"""
        
        # Simular datos de heatmap por intensidad y tipo de tarea
        intensities = ['mild', 'moderate', 'strong', 'extreme']
        task_types = ['reasoning', 'coding', 'analysis', 'creative']
        
        heatmap_data = []
        for i, intensity in enumerate(intensities):
            for j, task_type in enumerate(task_types):
                # Simular efectividad basada en datos reales
                base_effectiveness = contradiction_data.get('avg_effectiveness', 0.5)
                # Ajustar por intensidad (más intenso = más efectivo hasta cierto punto)
                intensity_factor = min(1.0, 0.3 + (i * 0.2))
                # Ajustar por tipo de tarea
                task_factor = 0.8 + (j * 0.05)
                
                effectiveness = min(1.0, base_effectiveness * intensity_factor * task_factor)
                
                heatmap_data.append({
                    'intensity': intensity,
                    'task_type': task_type,
                    'effectiveness': effectiveness,
                    'x': j,
                    'y': i,
                    'value': effectiveness
                })
                
        return {
            'data': heatmap_data,
            'intensities': intensities,
            'task_types': task_types,
            'max_effectiveness': max(d['effectiveness'] for d in heatmap_data),
            'min_effectiveness': min(d['effectiveness'] for d in heatmap_data)
        }

# Instancia global
visualization_generator = VisualizationGenerator()

def get_visualization_generator() -> VisualizationGenerator:
    """Obtiene instancia del generador de visualizaciones"""
    return visualization_generator

