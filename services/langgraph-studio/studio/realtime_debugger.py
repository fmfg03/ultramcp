"""
Real-time Debugger for LangGraph Studio
Proporciona debugging visual en tiempo real y monitoreo de sesiones
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import websockets
import threading
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class DebugEvent:
    """Evento de debugging"""
    timestamp: str
    session_id: str
    event_type: str  # node_enter, node_exit, edge_taken, state_update, error
    node_name: str
    state_before: Dict[str, Any]
    state_after: Dict[str, Any]
    metadata: Dict[str, Any]
    duration_ms: Optional[float] = None
    error: Optional[str] = None

class RealtimeDebugger:
    """Debugger en tiempo real para LangGraph Studio"""
    
    def __init__(self, port: int = 8124):
        self.port = port
        self.clients = set()
        self.events_buffer = []
        self.max_buffer_size = 1000
        self.session_states = {}
        self.node_timings = {}
        self.is_running = False
        
    async def start_server(self):
        """Inicia el servidor WebSocket para debugging"""
        self.is_running = True
        logger.info(f"Starting realtime debugger on port {self.port}")
        
        async def handle_client(websocket, path):
            self.clients.add(websocket)
            logger.info(f"Debug client connected: {websocket.remote_address}")
            
            try:
                # Enviar eventos del buffer al cliente nuevo
                for event in self.events_buffer[-50:]:  # Últimos 50 eventos
                    await websocket.send(json.dumps(asdict(event)))
                
                # Mantener conexión activa
                await websocket.wait_closed()
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                self.clients.discard(websocket)
                logger.info(f"Debug client disconnected")
        
        start_server = websockets.serve(handle_client, "0.0.0.0", self.port)
        await start_server
        
        # Mantener servidor corriendo
        while self.is_running:
            await asyncio.sleep(1)
    
    def start_background_server(self):
        """Inicia servidor en background thread"""
        def run_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.start_server())
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        logger.info("Realtime debugger started in background")
    
    def log_event(self, event: DebugEvent):
        """Registra un evento de debugging"""
        # Agregar al buffer
        self.events_buffer.append(event)
        if len(self.events_buffer) > self.max_buffer_size:
            self.events_buffer.pop(0)
        
        # Actualizar estado de sesión
        if event.session_id not in self.session_states:
            self.session_states[event.session_id] = {
                "start_time": event.timestamp,
                "current_node": None,
                "nodes_visited": [],
                "total_duration": 0,
                "error_count": 0
            }
        
        session_state = self.session_states[event.session_id]
        
        if event.event_type == "node_enter":
            session_state["current_node"] = event.node_name
            session_state["nodes_visited"].append(event.node_name)
            
        elif event.event_type == "node_exit":
            if event.duration_ms:
                session_state["total_duration"] += event.duration_ms
                
        elif event.event_type == "error":
            session_state["error_count"] += 1
        
        # Enviar a clientes conectados
        asyncio.create_task(self._broadcast_event(event))
    
    async def _broadcast_event(self, event: DebugEvent):
        """Envía evento a todos los clientes conectados"""
        if not self.clients:
            return
        
        message = json.dumps(asdict(event))
        disconnected = set()
        
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
        
        # Limpiar clientes desconectados
        self.clients -= disconnected
    
    def create_node_wrapper(self, node_name: str, original_func: Callable):
        """Crea wrapper para nodo que registra eventos de debugging"""
        
        async def wrapped_node(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
            session_id = state.get("session_id", "unknown")
            start_time = time.time()
            timestamp = datetime.now().isoformat()
            
            # Evento de entrada al nodo
            enter_event = DebugEvent(
                timestamp=timestamp,
                session_id=session_id,
                event_type="node_enter",
                node_name=node_name,
                state_before=state.copy(),
                state_after={},
                metadata={"kwargs": kwargs}
            )
            self.log_event(enter_event)
            
            try:
                # Ejecutar nodo original
                if asyncio.iscoroutinefunction(original_func):
                    result = await original_func(state, **kwargs)
                else:
                    result = original_func(state, **kwargs)
                
                # Calcular duración
                duration_ms = (time.time() - start_time) * 1000
                
                # Evento de salida del nodo
                exit_event = DebugEvent(
                    timestamp=datetime.now().isoformat(),
                    session_id=session_id,
                    event_type="node_exit",
                    node_name=node_name,
                    state_before=state.copy(),
                    state_after=result.copy() if isinstance(result, dict) else {},
                    metadata={"success": True},
                    duration_ms=duration_ms
                )
                self.log_event(exit_event)
                
                return result
                
            except Exception as e:
                # Evento de error
                error_event = DebugEvent(
                    timestamp=datetime.now().isoformat(),
                    session_id=session_id,
                    event_type="error",
                    node_name=node_name,
                    state_before=state.copy(),
                    state_after={},
                    metadata={"error_type": type(e).__name__},
                    error=str(e)
                )
                self.log_event(error_event)
                raise
        
        return wrapped_node
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Obtiene resumen de una sesión"""
        if session_id not in self.session_states:
            return {"error": "Session not found"}
        
        session_state = self.session_states[session_id]
        events = [e for e in self.events_buffer if e.session_id == session_id]
        
        return {
            "session_id": session_id,
            "start_time": session_state["start_time"],
            "current_node": session_state["current_node"],
            "nodes_visited": session_state["nodes_visited"],
            "total_duration_ms": session_state["total_duration"],
            "error_count": session_state["error_count"],
            "total_events": len(events),
            "node_timings": self._calculate_node_timings(events),
            "flow_path": self._extract_flow_path(events)
        }
    
    def _calculate_node_timings(self, events: List[DebugEvent]) -> Dict[str, Dict[str, float]]:
        """Calcula tiempos por nodo"""
        timings = {}
        
        for event in events:
            if event.event_type == "node_exit" and event.duration_ms:
                node_name = event.node_name
                if node_name not in timings:
                    timings[node_name] = {
                        "total_time": 0,
                        "call_count": 0,
                        "avg_time": 0,
                        "max_time": 0,
                        "min_time": float('inf')
                    }
                
                timing = timings[node_name]
                timing["total_time"] += event.duration_ms
                timing["call_count"] += 1
                timing["max_time"] = max(timing["max_time"], event.duration_ms)
                timing["min_time"] = min(timing["min_time"], event.duration_ms)
                timing["avg_time"] = timing["total_time"] / timing["call_count"]
        
        return timings
    
    def _extract_flow_path(self, events: List[DebugEvent]) -> List[Dict[str, Any]]:
        """Extrae el camino de flujo de la sesión"""
        path = []
        
        for event in events:
            if event.event_type in ["node_enter", "node_exit"]:
                path.append({
                    "timestamp": event.timestamp,
                    "node": event.node_name,
                    "event": event.event_type,
                    "duration": event.duration_ms
                })
        
        return path
    
    def export_session_trace(self, session_id: str, format: str = "json") -> str:
        """Exporta traza de sesión en formato especificado"""
        summary = self.get_session_summary(session_id)
        events = [asdict(e) for e in self.events_buffer if e.session_id == session_id]
        
        trace_data = {
            "session_summary": summary,
            "events": events,
            "export_timestamp": datetime.now().isoformat(),
            "format_version": "1.0"
        }
        
        if format == "json":
            return json.dumps(trace_data, indent=2)
        elif format == "mermaid":
            return self._generate_mermaid_trace(events)
        else:
            return json.dumps(trace_data, indent=2)
    
    def _generate_mermaid_trace(self, events: List[Dict[str, Any]]) -> str:
        """Genera diagrama Mermaid de la traza"""
        mermaid = "graph TD\n"
        mermaid += "    %% Session Trace Diagram\n\n"
        
        nodes_seen = set()
        edges = []
        
        prev_node = None
        for event in events:
            if event["event_type"] == "node_enter":
                node_name = event["node_name"]
                if node_name not in nodes_seen:
                    mermaid += f"    {node_name}[{node_name}]\n"
                    nodes_seen.add(node_name)
                
                if prev_node and prev_node != node_name:
                    edge = f"    {prev_node} --> {node_name}\n"
                    if edge not in edges:
                        edges.append(edge)
                
                prev_node = node_name
        
        mermaid += "\n"
        mermaid += "".join(edges)
        
        return mermaid
    
    def stop(self):
        """Detiene el debugger"""
        self.is_running = False
        logger.info("Realtime debugger stopped")

# Instancia global del debugger
realtime_debugger = RealtimeDebugger()

def get_realtime_debugger() -> RealtimeDebugger:
    """Obtiene instancia del debugger"""
    return realtime_debugger

def start_debugging():
    """Inicia debugging en background"""
    realtime_debugger.start_background_server()

def create_debug_wrapper(node_name: str):
    """Decorator para crear wrapper de debugging"""
    def decorator(func):
        return realtime_debugger.create_node_wrapper(node_name, func)
    return decorator

