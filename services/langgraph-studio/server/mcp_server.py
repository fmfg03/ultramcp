"""
LangGraph Server con endpoint MCP

Servidor que expone los agentes LangGraph como herramientas MCP
usando el protocolo Streamable HTTP.
"""

import sys
import os
import asyncio
from typing import Dict, Any, List, Optional
import json
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn

# Agregar el directorio del proyecto al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Importar agentes y schemas
from langgraph_system.agents.complete_mcp_agent import (
    get_mcp_agent, execute_mcp_task, stream_mcp_task, get_mcp_graph_info
)
from langgraph_system.schemas.mcp_schemas import (
    MCPAgentInput, MCPAgentOutput, ModelType
)

# Importar servicios existentes
try:
    from backend.src.utils.logger import logger
    from backend.src.middleware.langwatchMiddleware import langwatchMiddleware
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    
    # Mock middleware
    def langwatchMiddleware():
        return lambda request, call_next: call_next(request)

# ============================================================================
# Configuración de FastAPI
# ============================================================================

app = FastAPI(
    title="LangGraph MCP Server",
    description="Servidor LangGraph que expone agentes como herramientas MCP",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agregar middleware de Langwatch
app.middleware("http")(langwatchMiddleware())

# ============================================================================
# Endpoints MCP Estándar
# ============================================================================

@app.get("/mcp")
async def mcp_root():
    """Endpoint raíz MCP que describe las herramientas disponibles"""
    try:
        agent = get_mcp_agent()
        graph_info = get_mcp_graph_info()
        
        return {
            "protocol": "mcp",
            "version": "1.0.0",
            "server": {
                "name": "langgraph-mcp-server",
                "version": "1.0.0"
            },
            "tools": [
                {
                    "name": "mcp_reasoning_agent",
                    "description": "Agente de razonamiento avanzado con LLMs locales y Langwatch",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "request": {
                                "type": "string",
                                "description": "Solicitud o tarea a procesar"
                            },
                            "options": {
                                "type": "object",
                                "properties": {
                                    "model_type": {
                                        "type": "string",
                                        "enum": ["auto", "mistral-local", "llama-local", "deepseek-local"],
                                        "description": "Tipo de modelo a usar"
                                    },
                                    "session_id": {
                                        "type": "string",
                                        "description": "ID de sesión para tracking"
                                    },
                                    "max_retries": {
                                        "type": "integer",
                                        "description": "Máximo número de reintentos"
                                    }
                                }
                            }
                        },
                        "required": ["request"]
                    },
                    "outputSchema": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean"},
                            "result": {"type": "string"},
                            "score": {"type": "number"},
                            "metadata": {"type": "object"}
                        }
                    }
                },
                {
                    "name": "mcp_builder_agent",
                    "description": "Agente constructor especializado en crear contenido y código",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "request": {"type": "string"},
                            "build_type": {
                                "type": "string",
                                "enum": ["website", "code", "document", "analysis"],
                                "description": "Tipo de construcción"
                            },
                            "options": {"type": "object"}
                        },
                        "required": ["request"]
                    },
                    "outputSchema": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean"},
                            "result": {"type": "string"},
                            "artifacts": {"type": "array"},
                            "metadata": {"type": "object"}
                        }
                    }
                }
            ],
            "graph_info": graph_info,
            "capabilities": [
                "local_llms",
                "langwatch_tracking",
                "contradiction_analysis",
                "adaptive_retry",
                "memory_persistence",
                "streaming_support"
            ]
        }
    
    except Exception as e:
        logger.error(f"❌ Error en mcp_root: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/mcp_reasoning_agent")
async def mcp_reasoning_agent(request: Request):
    """Herramienta MCP para agente de razonamiento"""
    try:
        body = await request.json()
        
        # Extraer parámetros
        user_request = body.get('request', '')
        options = body.get('options', {})
        
        if not user_request:
            raise HTTPException(status_code=400, detail="Request es requerido")
        
        logger.info(f"🎯 MCP Reasoning Agent: {user_request[:100]}...")
        
        # Ejecutar agente
        result = await execute_mcp_task(user_request, **options)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"❌ Error en mcp_reasoning_agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/mcp_builder_agent")
async def mcp_builder_agent(request: Request):
    """Herramienta MCP para agente constructor"""
    try:
        body = await request.json()
        
        user_request = body.get('request', '')
        build_type = body.get('build_type', 'general')
        options = body.get('options', {})
        
        if not user_request:
            raise HTTPException(status_code=400, detail="Request es requerido")
        
        # Configurar opciones específicas para construcción
        options.update({
            'build_type': build_type,
            'specialized_mode': True
        })
        
        logger.info(f"🏗️ MCP Builder Agent ({build_type}): {user_request[:100]}...")
        
        result = await execute_mcp_task(user_request, **options)
        
        # Agregar información específica de construcción
        if result.get('success'):
            result['artifacts'] = result.get('metadata', {}).get('artifacts', [])
            result['build_type'] = build_type
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"❌ Error en mcp_builder_agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Endpoints de Streaming
# ============================================================================

@app.post("/mcp/stream/reasoning")
async def stream_reasoning_agent(request: Request):
    """Streaming del agente de razonamiento"""
    try:
        body = await request.json()
        user_request = body.get('request', '')
        options = body.get('options', {})
        
        if not user_request:
            raise HTTPException(status_code=400, detail="Request es requerido")
        
        async def generate_stream():
            try:
                async for chunk in stream_mcp_task(user_request, **options):
                    yield f"data: {json.dumps(chunk)}\n\n"
                
                # Enviar evento de finalización
                yield f"data: {json.dumps({'type': 'complete'})}\n\n"
            
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
    
    except Exception as e:
        logger.error(f"❌ Error en stream_reasoning_agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Endpoints de Información y Debugging
# ============================================================================

@app.get("/mcp/info")
async def mcp_info():
    """Información detallada del servidor MCP"""
    try:
        graph_info = get_mcp_graph_info()
        
        return {
            "server_info": {
                "name": "LangGraph MCP Server",
                "version": "1.0.0",
                "protocol": "mcp",
                "capabilities": [
                    "local_llms",
                    "langwatch_tracking", 
                    "contradiction_analysis",
                    "adaptive_retry",
                    "memory_persistence",
                    "streaming_support"
                ]
            },
            "graph_info": graph_info,
            "available_models": [
                "mistral-local",
                "llama-local", 
                "deepseek-local"
            ],
            "endpoints": {
                "tools": [
                    "/mcp/tools/mcp_reasoning_agent",
                    "/mcp/tools/mcp_builder_agent"
                ],
                "streaming": [
                    "/mcp/stream/reasoning"
                ],
                "info": [
                    "/mcp/info",
                    "/mcp/health",
                    "/mcp/graph"
                ]
            }
        }
    
    except Exception as e:
        logger.error(f"❌ Error en mcp_info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/health")
async def mcp_health():
    """Health check del servidor MCP"""
    try:
        # Verificar que el agente se puede inicializar
        agent = get_mcp_agent()
        
        # Verificar modelos (esto debería usar el health check node)
        from langgraph_system.nodes.llm_langwatch_nodes import model_health_check_node
        
        health_result = await model_health_check_node({})
        
        return {
            "status": "healthy" if health_result.get('system_healthy', False) else "degraded",
            "timestamp": time.time(),
            "agent_status": "ready",
            "model_health": health_result.get('model_health', {}),
            "available_models": health_result.get('available_models', []),
            "graph_compiled": agent.compiled_graph is not None
        }
    
    except Exception as e:
        logger.error(f"❌ Error en mcp_health: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "error": str(e)
        }

@app.get("/mcp/graph")
async def mcp_graph():
    """Información del grafo LangGraph"""
    try:
        return get_mcp_graph_info()
    
    except Exception as e:
        logger.error(f"❌ Error en mcp_graph: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Endpoints de Testing
# ============================================================================

@app.post("/mcp/test")
async def test_mcp_agent(request: Request):
    """Endpoint de testing para el agente MCP"""
    try:
        body = await request.json()
        test_request = body.get('request', 'Test del agente MCP')
        
        logger.info(f"🧪 Testing MCP Agent: {test_request}")
        
        result = await execute_mcp_task(test_request, session_id=f"test_{int(time.time())}")
        
        return {
            "test_status": "completed",
            "test_request": test_request,
            "result": result,
            "timestamp": time.time()
        }
    
    except Exception as e:
        logger.error(f"❌ Error en test_mcp_agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Configuración del Servidor
# ============================================================================

def create_app() -> FastAPI:
    """Crea y configura la aplicación FastAPI"""
    return app

async def startup_event():
    """Evento de inicio del servidor"""
    logger.info("🚀 Iniciando LangGraph MCP Server...")
    
    try:
        # Inicializar agente
        agent = get_mcp_agent()
        logger.info("✅ Agente MCP inicializado")
        
        # Verificar salud del sistema
        health = await mcp_health()
        logger.info(f"🏥 Estado del sistema: {health['status']}")
        
    except Exception as e:
        logger.error(f"❌ Error en startup: {str(e)}")

async def shutdown_event():
    """Evento de cierre del servidor"""
    logger.info("🛑 Cerrando LangGraph MCP Server...")

# Registrar eventos
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)

# ============================================================================
# Función Principal
# ============================================================================

def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Ejecuta el servidor LangGraph MCP"""
    logger.info(f"🌐 Iniciando servidor en http://{host}:{port}")
    
    uvicorn.run(
        "langgraph_system.server.mcp_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    run_server()

# ============================================================================
# Exportar
# ============================================================================

__all__ = [
    'app',
    'create_app',
    'run_server'
]

