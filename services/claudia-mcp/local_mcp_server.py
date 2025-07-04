#!/usr/bin/env python3
"""
Local Models MCP Server for Claudia Integration
Direct interface to 5 local LLM models - zero cost, maximum privacy
"""

import asyncio
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# UltraMCP project root
ULTRAMCP_ROOT = Path("/root/ultramcp")

class LocalModelsMCPServer:
    """Local Models MCP Server for Claudia"""
    
    def __init__(self):
        self.server = Server("ultramcp-local")
        self.setup_handlers()
        
        # Model configurations
        self.models = {
            "qwen2.5:14b": {
                "role": "Strategic Analyst",
                "specialization": "Complex reasoning and strategic analysis",
                "use_cases": ["CFO", "CEO", "Strategic Analyst"]
            },
            "llama3.1:8b": {
                "role": "Balanced Reasoner", 
                "specialization": "High-quality general analysis",
                "use_cases": ["General analysis", "Balanced reasoning"]
            },
            "qwen-coder:7b": {
                "role": "Technical Specialist",
                "specialization": "Code analysis and technical evaluation", 
                "use_cases": ["code_review", "architecture", "debugging", "optimization"]
            },
            "mistral:7b": {
                "role": "Rapid Analyst",
                "specialization": "Quick analysis and practical perspectives",
                "use_cases": ["Quick decisions", "Practical analysis"]
            },
            "deepseek-coder:6.7b": {
                "role": "System Architect",
                "specialization": "Advanced technical evaluation and system design",
                "use_cases": ["System design", "Architecture", "Platform engineering"]
            }
        }
    
    def setup_handlers(self):
        """Setup MCP tool handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available local model tools"""
            tools = []
            
            # Individual model tools
            for model_id, config in self.models.items():
                safe_name = model_id.replace(":", "_").replace(".", "_")
                tools.append(types.Tool(
                    name=safe_name,
                    description=f"{config['role']} - {config['specialization']}",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": f"Message for {config['role']}"
                            },
                            "role": {
                                "type": "string",
                                "description": "Role perspective for analysis",
                                "default": config['role']
                            },
                            "temperature": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "default": 0.7,
                                "description": "Creativity level"
                            }
                        },
                        "required": ["message"]
                    }
                ))
            
            # Auto-select model tool
            tools.append(types.Tool(
                name="auto_select_model",
                description="Automatically select the best local model for the task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Your question or task"
                        },
                        "task_type": {
                            "type": "string",
                            "enum": ["coding", "analysis", "strategy", "creative", "rapid"],
                            "description": "Type of task to optimize model selection"
                        },
                        "privacy_required": {
                            "type": "boolean",
                            "default": True,
                            "description": "Require 100% local processing"
                        }
                    },
                    "required": ["message"]
                }
            ))
            
            # Model status and management tools
            tools.extend([
                types.Tool(
                    name="list_models",
                    description="List all available local models with details",
                    inputSchema={"type": "object", "properties": {}}
                ),
                types.Tool(
                    name="model_performance",
                    description="Get performance metrics for local models",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "model": {
                                "type": "string",
                                "description": "Specific model to check (optional)"
                            }
                        }
                    }
                ),
                types.Tool(
                    name="privacy_score",
                    description="Calculate privacy score for processing mode",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "processing_mode": {
                                "type": "string",
                                "enum": ["local_only", "hybrid", "api_only"],
                                "default": "local_only"
                            }
                        }
                    }
                )
            ])
            
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Handle tool execution"""
            try:
                # Individual model tools
                for model_id in self.models.keys():
                    safe_name = model_id.replace(":", "_").replace(".", "_")
                    if name == safe_name:
                        return await self._handle_model_chat(model_id, arguments)
                
                # Special tools
                if name == "auto_select_model":
                    return await self._handle_auto_select(arguments)
                elif name == "list_models":
                    return await self._handle_list_models()
                elif name == "model_performance":
                    return await self._handle_model_performance(arguments)
                elif name == "privacy_score":
                    return await self._handle_privacy_score(arguments)
                else:
                    return [types.TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )]
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )]
    
    async def _handle_model_chat(self, model_id: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle chat with specific model"""
        message = arguments["message"]
        role = arguments.get("role", self.models[model_id]["role"])
        
        try:
            # Execute local chat with specific model
            cmd = ["make", "local-chat", f"TEXT={message}", f"MODEL={model_id}"]
            
            result = subprocess.run(
                cmd,
                cwd=ULTRAMCP_ROOT,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                chat_result = {
                    "response": result.stdout.strip(),
                    "model": model_id,
                    "role": role,
                    "specialization": self.models[model_id]["specialization"],
                    "privacy_mode": True,
                    "cost": 0.0,
                    "local_processing": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                return [types.TextContent(
                    type="text",
                    text=json.dumps(chat_result, indent=2)
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"Model {model_id} chat failed: {result.stderr}"
                )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Model {model_id} error: {str(e)}"
            )]
    
    async def _handle_auto_select(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle automatic model selection"""
        message = arguments["message"]
        task_type = arguments.get("task_type", "analysis")
        
        # Model selection logic
        model_map = {
            "coding": "qwen-coder:7b",
            "analysis": "llama3.1:8b", 
            "strategy": "qwen2.5:14b",
            "creative": "mistral:7b",
            "rapid": "mistral:7b"
        }
        
        selected_model = model_map.get(task_type, "llama3.1:8b")
        
        # Execute with selected model
        try:
            cmd = ["make", "local-chat", f"TEXT={message}", f"MODEL={selected_model}"]
            
            result = subprocess.run(
                cmd,
                cwd=ULTRAMCP_ROOT,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                auto_result = {
                    "response": result.stdout.strip(),
                    "selected_model": selected_model,
                    "task_type": task_type,
                    "selection_reason": f"Optimized for {task_type} tasks",
                    "model_role": self.models[selected_model]["role"],
                    "privacy_mode": True,
                    "cost": 0.0,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                return [types.TextContent(
                    type="text",
                    text=json.dumps(auto_result, indent=2)
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"Auto-select failed: {result.stderr}"
                )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Auto-select error: {str(e)}"
            )]
    
    async def _handle_list_models(self) -> List[types.TextContent]:
        """List all available models"""
        try:
            # Get system status
            result = subprocess.run(
                ["make", "local-status"],
                cwd=ULTRAMCP_ROOT,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            models_info = {
                "models": self.models,
                "total_models": len(self.models),
                "privacy_score": 100.0,
                "cost_per_request": 0.0,
                "system_status": "available" if result.returncode == 0 else "unavailable",
                "system_output": result.stdout if result.returncode == 0 else result.stderr,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(models_info, indent=2)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error listing models: {str(e)}"
            )]
    
    async def _handle_model_performance(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get model performance metrics"""
        model = arguments.get("model")
        
        # Mock performance data - would integrate with actual metrics
        performance_data = {
            "performance_metrics": {
                "qwen2.5:14b": {
                    "avg_response_time": 2.3,
                    "tokens_per_second": 45.2,
                    "memory_usage": "8.2GB",
                    "cpu_usage": "65%",
                    "success_rate": 99.5
                },
                "llama3.1:8b": {
                    "avg_response_time": 1.8,
                    "tokens_per_second": 52.1,
                    "memory_usage": "6.1GB", 
                    "cpu_usage": "45%",
                    "success_rate": 99.8
                },
                "qwen-coder:7b": {
                    "avg_response_time": 1.5,
                    "tokens_per_second": 58.3,
                    "memory_usage": "5.2GB",
                    "cpu_usage": "40%",
                    "success_rate": 99.2
                },
                "mistral:7b": {
                    "avg_response_time": 1.2,
                    "tokens_per_second": 65.8,
                    "memory_usage": "4.8GB",
                    "cpu_usage": "35%",
                    "success_rate": 99.9
                },
                "deepseek-coder:6.7b": {
                    "avg_response_time": 1.1,
                    "tokens_per_second": 68.2,
                    "memory_usage": "4.5GB",
                    "cpu_usage": "32%",
                    "success_rate": 99.7
                }
            },
            "system_metrics": {
                "total_memory": "32GB",
                "available_memory": "18GB",
                "cpu_cores": 16,
                "gpu_available": False
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if model:
            performance_data = {
                "model": model,
                "metrics": performance_data["performance_metrics"].get(model, {}),
                "timestamp": performance_data["timestamp"]
            }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(performance_data, indent=2)
        )]
    
    async def _handle_privacy_score(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Calculate privacy score"""
        processing_mode = arguments.get("processing_mode", "local_only")
        
        privacy_scores = {
            "local_only": 100.0,
            "hybrid": 75.0,
            "api_only": 25.0
        }
        
        privacy_result = {
            "processing_mode": processing_mode,
            "privacy_score": privacy_scores.get(processing_mode, 100.0),
            "data_sovereignty": processing_mode == "local_only",
            "external_api_calls": processing_mode in ["hybrid", "api_only"],
            "recommendations": [
                "Use local_only mode for maximum privacy",
                "All models support 100% local processing",
                "Zero data leaves your system in local_only mode"
            ] if processing_mode == "local_only" else [
                "Consider local_only mode for sensitive data",
                "Hybrid mode may send data to external APIs",
                "Review data handling policies for API usage"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(privacy_result, indent=2)
        )]

async def main():
    """Main entry point for Local Models MCP Server"""
    server = LocalModelsMCPServer()
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            NotificationOptions()
        )

if __name__ == "__main__":
    asyncio.run(main())