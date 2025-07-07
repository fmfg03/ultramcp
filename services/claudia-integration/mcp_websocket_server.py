#!/usr/bin/env python3
"""
MCP WebSocket Server for Claudia Frontend
Provides real-time MCP protocol communication via WebSocket
"""

import asyncio
import json
import logging
import websockets
from typing import Dict, Set, Any
from datetime import datetime
import uuid

from mcp_protocol import MCPServer, MCPMessage, MCPTool, UltraMCPToolRegistry
from ultramcp_service_adapters import UltraMCPServiceAdapters

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPWebSocketServer:
    """WebSocket server implementing MCP protocol"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8014):
        self.host = host
        self.port = port
        self.mcp_server = MCPServer()
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.service_adapters = UltraMCPServiceAdapters()
        
        # Initialize UltraMCP tools
        asyncio.create_task(self._initialize_ultramcp_tools())
    
    async def _initialize_ultramcp_tools(self):
        """Initialize MCP tools from UltraMCP services"""
        try:
            logger.info("Initializing UltraMCP MCP tools...")
            
            # Create tool registry
            registry = UltraMCPToolRegistry()
            tools = await registry.create_mcp_tools()
            
            # Register tools with handlers
            for tool in tools:
                handler = await self._create_tool_handler(tool.name)
                self.mcp_server.register_tool(tool, handler)
            
            # Register some sample resources
            from mcp_protocol import MCPResource, MCPPrompt
            
            self.mcp_server.register_resource(MCPResource(
                uri="ultramcp://services/status",
                name="UltraMCP Services Status",
                description="Real-time status of all UltraMCP microservices",
                mimeType="application/json"
            ))
            
            self.mcp_server.register_resource(MCPResource(
                uri="ultramcp://logs/recent",
                name="Recent System Logs",
                description="Recent logs from UltraMCP services",
                mimeType="text/plain"
            ))
            
            # Register prompt templates
            self.mcp_server.register_prompt(MCPPrompt(
                name="security_analysis",
                description="Generate comprehensive security analysis prompt",
                arguments=[
                    {"name": "project_path", "description": "Path to analyze", "required": True},
                    {"name": "focus_areas", "description": "Specific security areas to focus on", "required": False}
                ]
            ))
            
            self.mcp_server.register_prompt(MCPPrompt(
                name="code_review",
                description="Generate code review prompt with best practices",
                arguments=[
                    {"name": "language", "description": "Programming language", "required": True},
                    {"name": "file_path", "description": "File to review", "required": True},
                    {"name": "review_type", "description": "Type of review (security, performance, style)", "required": False}
                ]
            ))
            
            logger.info(f"Initialized {len(tools)} MCP tools successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize UltraMCP tools: {e}")
    
    async def _create_tool_handler(self, tool_name: str):
        """Create async handler for UltraMCP tool"""
        async def handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
            try:
                logger.info(f"Executing MCP tool: {tool_name} with args: {arguments}")
                
                if tool_name == "ultramcp_security_scan":
                    return await self.service_adapters.execute_security_scan(arguments)
                elif tool_name == "ultramcp_code_analysis":
                    return await self.service_adapters.execute_code_analysis(arguments)
                elif tool_name == "ultramcp_ai_debate":
                    return await self.service_adapters.execute_ai_debate(arguments)
                elif tool_name == "ultramcp_voice_assist":
                    return await self.service_adapters.execute_voice_assist(arguments)
                else:
                    return {
                        "error": f"Unknown tool: {tool_name}",
                        "status": "failed"
                    }
                    
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                return {
                    "error": str(e),
                    "status": "failed",
                    "tool": tool_name
                }
        
        return handler
    
    async def handle_client(self, websocket, path):
        """Handle new WebSocket client connection"""
        client_id = str(uuid.uuid4())
        logger.info(f"New MCP client connected: {client_id}")
        
        self.clients.add(websocket)
        self.mcp_server.clients.add(websocket)
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.debug(f"Received message from {client_id}: {data}")
                    
                    # Handle MCP message
                    response = await self.mcp_server.handle_message(data, websocket)
                    
                    if response:
                        response_data = json.dumps(response.to_dict())
                        await websocket.send(response_data)
                        logger.debug(f"Sent response to {client_id}: {response_data}")
                    
                except json.JSONDecodeError:
                    error_response = MCPMessage(
                        error={"code": -32700, "message": "Parse error"}
                    )
                    await websocket.send(json.dumps(error_response.to_dict()))
                
                except Exception as e:
                    logger.error(f"Error handling message from {client_id}: {e}")
                    error_response = MCPMessage(
                        error={"code": -32603, "message": f"Internal error: {str(e)}"}
                    )
                    await websocket.send(json.dumps(error_response.to_dict()))
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        
        finally:
            self.clients.discard(websocket)
            self.mcp_server.clients.discard(websocket)
    
    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting MCP WebSocket server on {self.host}:{self.port}")
        
        server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        )
        
        logger.info(f"MCP WebSocket server started on ws://{self.host}:{self.port}")
        return server
    
    async def broadcast_notification(self, notification_type: str, data: Dict[str, Any]):
        """Broadcast notification to all connected clients"""
        notification = {
            "type": notification_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        await self.mcp_server.notify_clients(notification)
    
    async def tool_execution_started(self, tool_name: str, execution_id: str, arguments: Dict[str, Any]):
        """Notify clients that tool execution started"""
        await self.broadcast_notification("tool_execution_started", {
            "tool_name": tool_name,
            "execution_id": execution_id,
            "arguments": arguments
        })
    
    async def tool_execution_progress(self, execution_id: str, progress: float, status: str):
        """Notify clients of tool execution progress"""
        await self.broadcast_notification("tool_execution_progress", {
            "execution_id": execution_id,
            "progress": progress,
            "status": status
        })
    
    async def tool_execution_completed(self, execution_id: str, result: Dict[str, Any]):
        """Notify clients that tool execution completed"""
        await self.broadcast_notification("tool_execution_completed", {
            "execution_id": execution_id,
            "result": result
        })
    
    async def service_status_changed(self, service_name: str, status: str, details: Dict[str, Any]):
        """Notify clients of service status changes"""
        await self.broadcast_notification("service_status_changed", {
            "service_name": service_name,
            "status": status,
            "details": details
        })

class MCPHealthMonitor:
    """Monitor UltraMCP services and broadcast status updates"""
    
    def __init__(self, websocket_server: MCPWebSocketServer):
        self.websocket_server = websocket_server
        self.service_urls = {
            "asterisk": "http://sam.chat:8002/health",
            "blockoli": "http://sam.chat:8080/health",
            "cod": "http://sam.chat:8001/health",
            "voice": "http://sam.chat:8004/health",
            "memory": "http://sam.chat:8009/health",
            "control_tower": "http://sam.chat:8007/health"
        }
        self.last_status = {}
    
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        logger.info("Starting UltraMCP services health monitoring")
        
        while True:
            try:
                for service_name, url in self.service_urls.items():
                    current_status = await self._check_service_health(service_name, url)
                    
                    # Check if status changed
                    if service_name not in self.last_status or self.last_status[service_name] != current_status:
                        await self.websocket_server.service_status_changed(
                            service_name, 
                            current_status["status"], 
                            current_status
                        )
                        self.last_status[service_name] = current_status
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _check_service_health(self, service_name: str, url: str) -> Dict[str, Any]:
        """Check health of a single service"""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "healthy",
                            "response_time_ms": response.headers.get("X-Response-Time", "unknown"),
                            "details": data
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"HTTP {response.status}",
                            "details": {}
                        }
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "error": "Service did not respond within 5 seconds",
                "details": {}
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "details": {}
            }

async def main():
    """Main entry point for MCP WebSocket server"""
    
    # Create WebSocket server
    mcp_ws_server = MCPWebSocketServer()
    
    # Start health monitoring
    health_monitor = MCPHealthMonitor(mcp_ws_server)
    
    # Start server and monitoring
    server = await mcp_ws_server.start_server()
    
    # Start health monitoring in background
    asyncio.create_task(health_monitor.start_monitoring())
    
    try:
        # Keep server running
        await server.wait_closed()
    except KeyboardInterrupt:
        logger.info("Shutting down MCP WebSocket server")
        server.close()
        await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())