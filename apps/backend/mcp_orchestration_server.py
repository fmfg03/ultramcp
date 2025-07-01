#!/usr/bin/env python3
"""
MCP Orchestration Server - Endpoint para comunicación Manus-Sam
Servidor que expone Sam como herramienta MCP para Manus
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import json
import logging
from datetime import datetime
import os
import sys

# Añadir el directorio backend al path
sys.path.append('/root/supermcp/backend')

# Importar sistemas de Sam
try:
    from sam_langgraph_integration import execute_sam_from_langgraph, get_sam_tool_definition, get_sam_execution_stats
    from memory_injection_system import inject_memory_to_sam
    from preferred_toolchain_system import get_model_stats
    from agent_autonomy_system import get_autonomy_status
except ImportError as e:
    print(f"Warning: Could not import Sam systems: {e}")

app = Flask(__name__)
CORS(app)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/supermcp/logs/mcp_orchestration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "mcp_orchestration_server",
        "version": "1.0.0"
    })

@app.route('/mcp/sam/definition', methods=['GET'])
def get_sam_definition():
    """
    Obtiene la definición de la herramienta Sam para LangGraph
    """
    try:
        definition = get_sam_tool_definition()
        return jsonify({
            "success": True,
            "tool_definition": definition
        })
    except Exception as e:
        logger.error(f"Error getting Sam definition: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/mcp/sam/execute', methods=['POST'])
def execute_sam_task():
    """
    Endpoint principal para que Manus ejecute tareas en Sam
    """
    try:
        # Validar request
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Request must be JSON"
            }), 400
        
        input_data = request.get_json()
        
        # Log de la request
        logger.info(f"Received Sam execution request: {input_data.get('task_type', 'unknown')} - {input_data.get('prompt', '')[:100]}...")
        
        # Ejecutar de forma asíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(execute_sam_from_langgraph(input_data))
        finally:
            loop.close()
        
        # Log del resultado
        logger.info(f"Sam execution completed: {result.get('status')} - Task ID: {result.get('task_id')}")
        
        return jsonify({
            "success": True,
            "result": result
        })
        
    except Exception as e:
        logger.error(f"Error executing Sam task: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/mcp/sam/batch', methods=['POST'])
def execute_sam_batch():
    """
    Endpoint para ejecutar múltiples tareas en lote
    """
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Request must be JSON"
            }), 400
        
        batch_data = request.get_json()
        
        # Validar que tenga tasks
        if "tasks" not in batch_data or not batch_data["tasks"]:
            return jsonify({
                "success": False,
                "error": "Batch request must include 'tasks' array"
            }), 400
        
        # Preparar input para Sam
        input_data = {
            "task_type": "batch",
            "prompt": f"Execute batch of {len(batch_data['tasks'])} tasks",
            "parameters": {
                "batch_tasks": batch_data["tasks"],
                "priority": batch_data.get("priority", "medium"),
                "autonomy_level": batch_data.get("autonomy_level", "semi_autonomous")
            }
        }
        
        logger.info(f"Received Sam batch request: {len(batch_data['tasks'])} tasks")
        
        # Ejecutar batch
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(execute_sam_from_langgraph(input_data))
        finally:
            loop.close()
        
        logger.info(f"Sam batch execution completed: {result.get('status')} - Batch ID: {result.get('batch_id')}")
        
        return jsonify({
            "success": True,
            "result": result
        })
        
    except Exception as e:
        logger.error(f"Error executing Sam batch: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/mcp/sam/status', methods=['GET'])
def get_sam_status():
    """
    Obtiene el estado completo del sistema Sam
    """
    try:
        status = {
            "timestamp": datetime.now().isoformat(),
            "sam_integration": get_sam_execution_stats(),
            "autonomy_system": get_autonomy_status(),
            "model_performance": get_model_stats(),
            "memory_injection": {
                "available": True,
                "last_update": datetime.now().isoformat()
            }
        }
        
        return jsonify({
            "success": True,
            "status": status
        })
        
    except Exception as e:
        logger.error(f"Error getting Sam status: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/mcp/sam/context', methods=['GET'])
def get_sam_context():
    """
    Obtiene el contexto actual que Sam tiene del proyecto
    """
    try:
        context_payload = inject_memory_to_sam()
        
        return jsonify({
            "success": True,
            "context": {
                "memory_hash": context_payload["memory_hash"],
                "injection_timestamp": context_payload["injection_timestamp"],
                "context_summary": {
                    "system_info": context_payload["context"].get("system_info", {}),
                    "file_structure_keys": list(context_payload["context"].get("file_structure", {}).keys()),
                    "todo_files": list(context_payload["context"].get("todo_lists", {}).keys()),
                    "key_references": list(context_payload["context"].get("key_references", {}).keys()),
                    "agent_status": context_payload["context"].get("agent_status", {})
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting Sam context: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/mcp/sam/models', methods=['GET'])
def get_available_models():
    """
    Obtiene la lista de modelos disponibles para Sam
    """
    try:
        # Verificar modelos de Ollama
        import requests
        ollama_models = []
        
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                ollama_models = [model["name"] for model in models_data.get("models", [])]
        except Exception as e:
            logger.warning(f"Could not fetch Ollama models: {str(e)}")
        
        # Modelos externos configurados
        external_models = []
        if os.getenv("OPENAI_API_KEY"):
            external_models.append("gpt-4o-mini")
        if os.getenv("ANTHROPIC_API_KEY"):
            external_models.append("claude-3-haiku")
        if os.getenv("PERPLEXITY_API_KEY"):
            external_models.append("perplexity-research")
        
        return jsonify({
            "success": True,
            "models": {
                "local_ollama": ollama_models,
                "external_apis": external_models,
                "total_available": len(ollama_models) + len(external_models)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting available models: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/mcp/langgraph/config', methods=['GET'])
def get_langgraph_config():
    """
    Obtiene la configuración de LangGraph para integrar Sam
    """
    try:
        from sam_langgraph_integration import generate_langgraph_config
        
        config = generate_langgraph_config()
        
        return jsonify({
            "success": True,
            "langgraph_config": config
        })
        
    except Exception as e:
        logger.error(f"Error generating LangGraph config: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/mcp/test', methods=['POST'])
def test_mcp_integration():
    """
    Endpoint de prueba para validar la integración MCP
    """
    try:
        test_data = request.get_json() if request.is_json else {}
        
        # Test básico de Sam
        test_input = {
            "task_type": "reasoning",
            "prompt": test_data.get("prompt", "Test Sam integration: List the current system status"),
            "parameters": {
                "temperature": 0.3,
                "priority": "low",
                "autonomy_level": "semi_autonomous"
            }
        }
        
        logger.info("Running MCP integration test")
        
        # Ejecutar test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(execute_sam_from_langgraph(test_input))
        finally:
            loop.close()
        
        # Obtener estadísticas adicionales
        status = get_autonomy_status()
        models = get_model_stats()
        
        return jsonify({
            "success": True,
            "test_result": result,
            "system_status": status,
            "model_stats": models,
            "test_timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error running MCP test: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "available_endpoints": [
            "/health",
            "/mcp/sam/definition",
            "/mcp/sam/execute",
            "/mcp/sam/batch", 
            "/mcp/sam/status",
            "/mcp/sam/context",
            "/mcp/sam/models",
            "/mcp/langgraph/config",
            "/mcp/test"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500

if __name__ == '__main__':
    # Crear directorio de logs si no existe
    os.makedirs('/root/supermcp/logs', exist_ok=True)
    
    logger.info("Starting MCP Orchestration Server")
    logger.info("Available endpoints:")
    logger.info("  GET  /health - Health check")
    logger.info("  GET  /mcp/sam/definition - Get Sam tool definition")
    logger.info("  POST /mcp/sam/execute - Execute Sam task")
    logger.info("  POST /mcp/sam/batch - Execute Sam batch")
    logger.info("  GET  /mcp/sam/status - Get Sam status")
    logger.info("  GET  /mcp/sam/context - Get Sam context")
    logger.info("  GET  /mcp/sam/models - Get available models")
    logger.info("  GET  /mcp/langgraph/config - Get LangGraph config")
    logger.info("  POST /mcp/test - Test MCP integration")
    
    # Ejecutar servidor
    app.run(
        host='0.0.0.0',
        port=3001,  # Puerto diferente al backend principal
        debug=False,
        threaded=True
    )

