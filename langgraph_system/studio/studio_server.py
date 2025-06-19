#!/usr/bin/env python3
"""
LangGraph Studio Development Server
Servidor de desarrollo con debugging visual y exportación en tiempo real
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Agregar path del proyecto
sys.path.append(str(Path(__file__).parent.parent.parent))

from langgraph_system.studio.realtime_debugger import get_realtime_debugger, start_debugging
from langgraph_system.studio.export_manager import get_export_manager
from langgraph_system.studio.studio_config import get_studio_config

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="LangGraph Studio - MCP System",
    description="Visual debugging and monitoring for Agentius MCP",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Obtener instancias
debugger = get_realtime_debugger()
export_manager = get_export_manager()
studio_config = get_studio_config()

# Clientes WebSocket conectados
connected_clients = set()

@app.on_event("startup")
async def startup_event():
    """Inicialización del servidor"""
    logger.info("🚀 Starting LangGraph Studio for MCP System")
    
    # Iniciar debugging en background
    start_debugging()
    
    # Exportar grafos iniciales
    export_manager.export_complete_system_graph()
    
    logger.info("✅ LangGraph Studio ready")

@app.get("/")
async def root():
    """Página principal del Studio"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LangGraph Studio - MCP System</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 30px;
            backdrop-filter: blur(10px);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .header h1 {
            font-size: 3em;
            margin: 0;
            background: linear-gradient(45deg, #FFD700, #FFA500);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
            margin: 10px 0;
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 40px 0;
        }
        .feature {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            transition: transform 0.3s ease;
        }
        .feature:hover {
            transform: translateY(-5px);
        }
        .feature h3 {
            font-size: 1.5em;
            margin-bottom: 15px;
            color: #FFD700;
        }
        .endpoints {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 15px;
            padding: 25px;
            margin: 30px 0;
        }
        .endpoint {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        .endpoint:last-child {
            border-bottom: none;
        }
        .method {
            background: #4CAF50;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: bold;
            min-width: 60px;
            text-align: center;
        }
        .method.ws {
            background: #2196F3;
        }
        .status {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 20px 0;
        }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4CAF50;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .btn {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin: 5px;
            transition: all 0.3s ease;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 LangGraph Studio</h1>
            <p>Visual Debugging & Monitoring for Agentius MCP</p>
            <div class="status">
                <div class="status-indicator"></div>
                <span>System Online - Real-time Debugging Active</span>
            </div>
        </div>

        <div class="features">
            <div class="feature">
                <h3>🔍 Real-time Debugging</h3>
                <p>Monitor graph execution in real-time with WebSocket connections. See every node transition, state change, and decision point as it happens.</p>
            </div>
            <div class="feature">
                <h3>📊 Visual Analytics</h3>
                <p>Comprehensive analytics with Langwatch integration. Track performance, quality scores, and contradiction effectiveness.</p>
            </div>
            <div class="feature">
                <h3>🎨 Graph Visualization</h3>
                <p>Export beautiful Mermaid diagrams for documentation and presentations. Multiple formats available including pitch deck versions.</p>
            </div>
            <div class="feature">
                <h3>🔥 Contradiction Analysis</h3>
                <p>Deep insights into contradiction triggers and effectiveness. Learn how the system improves through explicit contradiction.</p>
            </div>
        </div>

        <div class="endpoints">
            <h3>🌐 Available Endpoints</h3>
            <div class="endpoint">
                <span><span class="method">GET</span> /health</span>
                <span>System health check</span>
            </div>
            <div class="endpoint">
                <span><span class="method">GET</span> /graphs/export</span>
                <span>Export all graph visualizations</span>
            </div>
            <div class="endpoint">
                <span><span class="method">GET</span> /graphs/mermaid/{graph_name}</span>
                <span>Get specific Mermaid diagram</span>
            </div>
            <div class="endpoint">
                <span><span class="method">GET</span> /debug/sessions</span>
                <span>List all debug sessions</span>
            </div>
            <div class="endpoint">
                <span><span class="method">GET</span> /debug/session/{session_id}</span>
                <span>Get session details and trace</span>
            </div>
            <div class="endpoint">
                <span><span class="method ws">WS</span> /ws/debug</span>
                <span>Real-time debugging WebSocket</span>
            </div>
        </div>

        <div style="text-align: center; margin-top: 30px;">
            <a href="/health" class="btn">🔍 Check Health</a>
            <a href="/graphs/export" class="btn">📊 Export Graphs</a>
            <a href="/debug/sessions" class="btn">🐛 Debug Sessions</a>
            <a href="/docs" class="btn">📚 API Docs</a>
        </div>
    </div>

    <script>
        // Conectar WebSocket para debugging en tiempo real
        const ws = new WebSocket(`ws://${window.location.host}/ws/debug`);
        
        ws.onopen = function(event) {
            console.log('🔗 Connected to debug WebSocket');
        };
        
        ws.onmessage = function(event) {
            const debugEvent = JSON.parse(event.data);
            console.log('🐛 Debug Event:', debugEvent);
        };
        
        ws.onclose = function(event) {
            console.log('❌ Debug WebSocket closed');
        };
    </script>
</body>
</html>
    """)

@app.get("/health")
async def health_check():
    """Health check del sistema"""
    return {
        "status": "healthy",
        "studio_version": "1.0.0",
        "debugger_active": debugger.is_running,
        "connected_clients": len(connected_clients),
        "export_path": str(export_manager.export_path),
        "features": {
            "realtime_debugging": True,
            "graph_export": True,
            "session_tracking": True,
            "langwatch_integration": True
        }
    }

@app.get("/graphs/export")
async def export_graphs():
    """Exporta todos los grafos del sistema"""
    try:
        exports = export_manager.export_complete_system_graph()
        return {
            "status": "success",
            "exports": exports,
            "timestamp": export_manager._get_timestamp()
        }
    except Exception as e:
        logger.error(f"Error exporting graphs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graphs/mermaid/{graph_name}")
async def get_mermaid_graph(graph_name: str):
    """Obtiene diagrama Mermaid específico"""
    try:
        graph_path = export_manager.export_path / "graphs" / f"{graph_name}.mmd"
        if not graph_path.exists():
            raise HTTPException(status_code=404, detail="Graph not found")
        
        return FileResponse(
            path=str(graph_path),
            media_type="text/plain",
            filename=f"{graph_name}.mmd"
        )
    except Exception as e:
        logger.error(f"Error getting Mermaid graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/sessions")
async def get_debug_sessions():
    """Lista todas las sesiones de debugging"""
    try:
        sessions = list(debugger.session_states.keys())
        return {
            "status": "success",
            "sessions": sessions,
            "total_sessions": len(sessions),
            "active_clients": len(connected_clients)
        }
    except Exception as e:
        logger.error(f"Error getting debug sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/session/{session_id}")
async def get_session_debug_info(session_id: str):
    """Obtiene información de debugging de una sesión específica"""
    try:
        summary = debugger.get_session_summary(session_id)
        if "error" in summary:
            raise HTTPException(status_code=404, detail=summary["error"])
        
        return {
            "status": "success",
            "session_summary": summary,
            "trace_available": True
        }
    except Exception as e:
        logger.error(f"Error getting session debug info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/session/{session_id}/trace")
async def export_session_trace(session_id: str, format: str = "json"):
    """Exporta traza de sesión en formato especificado"""
    try:
        trace = debugger.export_session_trace(session_id, format)
        
        if format == "mermaid":
            return HTMLResponse(content=f"""
<!DOCTYPE html>
<html>
<head>
    <title>Session Trace - {session_id}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
</head>
<body>
    <h1>Session Trace: {session_id}</h1>
    <div class="mermaid">
{trace}
    </div>
    <script>
        mermaid.initialize({{startOnLoad: true}});
    </script>
</body>
</html>
            """)
        else:
            return {"status": "success", "trace": trace, "format": format}
            
    except Exception as e:
        logger.error(f"Error exporting session trace: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/debug")
async def websocket_debug_endpoint(websocket: WebSocket):
    """WebSocket para debugging en tiempo real"""
    await websocket.accept()
    connected_clients.add(websocket)
    logger.info(f"Debug client connected: {websocket.client}")
    
    try:
        # Enviar estado inicial
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "Connected to LangGraph Studio debug stream",
            "active_sessions": list(debugger.session_states.keys())
        }))
        
        # Mantener conexión activa
        while True:
            try:
                # Ping cada 30 segundos para mantener conexión
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Enviar ping
                await websocket.send_text(json.dumps({
                    "type": "ping",
                    "timestamp": debugger._get_timestamp() if hasattr(debugger, '_get_timestamp') else ""
                }))
                
    except WebSocketDisconnect:
        connected_clients.discard(websocket)
        logger.info(f"Debug client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connected_clients.discard(websocket)

@app.get("/studio/config")
async def get_studio_config():
    """Obtiene configuración del Studio"""
    return {
        "status": "success",
        "config": studio_config.config,
        "export_path": str(export_manager.export_path)
    }

@app.post("/studio/config")
async def update_studio_config(config_updates: Dict[str, Any]):
    """Actualiza configuración del Studio"""
    try:
        studio_config.update(config_updates)
        return {
            "status": "success",
            "message": "Configuration updated",
            "config": studio_config.config
        }
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def start_studio_server(host: str = "0.0.0.0", port: int = 8123):
    """Inicia el servidor de LangGraph Studio"""
    logger.info(f"🚀 Starting LangGraph Studio on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        reload=studio_config.get("hot_reload", True),
        access_log=True
    )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LangGraph Studio Development Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8123, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    start_studio_server(args.host, args.port)

