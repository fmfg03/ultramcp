#!/usr/bin/env python3
"""
JSON Schema Definitions for MCP Orchestrator-Executor System
Especificaciones completas de payload y validación para comunicación Manus-SAM
"""

import json
from typing import Dict, Any, Optional, List
from jsonschema import validate, ValidationError
from datetime import datetime
from enum import Enum

class PayloadType(Enum):
    TASK_EXECUTION = "task_execution"
    TASK_BATCH = "task_batch"
    NOTIFICATION = "notification"
    WEBHOOK_REGISTRATION = "webhook_registration"
    STATUS_REQUEST = "status_request"
    AGENT_END_TASK = "agent_end_task"

# Schema para ejecución de tareas individuales (Manus → SAM)
TASK_EXECUTION_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://mcpenterprise.com/schemas/task-execution.json",
    "title": "Task Execution Request",
    "description": "Schema for task execution requests from Manus to SAM",
    "type": "object",
    "required": ["task_id", "task_type", "description", "priority", "orchestrator_info"],
    "properties": {
        "task_id": {
            "type": "string",
            "pattern": "^[a-zA-Z0-9_-]+$",
            "minLength": 1,
            "maxLength": 100,
            "description": "Unique identifier for the task"
        },
        "task_type": {
            "type": "string",
            "enum": [
                "code_generation",
                "code_debugging", 
                "data_analysis",
                "documentation",
                "testing",
                "deployment",
                "configuration",
                "monitoring",
                "research",
                "general"
            ],
            "description": "Type of task to be executed"
        },
        "description": {
            "type": "string",
            "minLength": 10,
            "maxLength": 10000,
            "description": "Detailed description of the task"
        },
        "priority": {
            "type": "string",
            "enum": ["low", "normal", "high", "critical"],
            "default": "normal",
            "description": "Task priority level"
        },
        "complexity": {
            "type": "string",
            "enum": ["low", "medium", "high", "critical"],
            "default": "medium",
            "description": "Estimated task complexity"
        },
        "estimated_duration": {
            "type": "integer",
            "minimum": 1,
            "maximum": 86400,
            "description": "Estimated duration in seconds"
        },
        "timeout": {
            "type": "integer",
            "minimum": 30,
            "maximum": 3600,
            "default": 300,
            "description": "Maximum execution time in seconds"
        },
        "orchestrator_info": {
            "type": "object",
            "required": ["agent_id", "timestamp"],
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Manus orchestrator agent identifier"
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Request timestamp in ISO 8601 format"
                },
                "session_id": {
                    "type": "string",
                    "description": "Session identifier for tracking"
                },
                "user_id": {
                    "type": "string",
                    "description": "User identifier if applicable"
                },
                "callback_url": {
                    "type": "string",
                    "format": "uri",
                    "description": "URL for status callbacks"
                }
            }
        },
        "parameters": {
            "type": "object",
            "description": "Task-specific parameters",
            "properties": {
                "input_data": {
                    "type": "object",
                    "description": "Input data for the task"
                },
                "configuration": {
                    "type": "object",
                    "description": "Configuration parameters"
                },
                "constraints": {
                    "type": "object",
                    "properties": {
                        "memory_limit": {
                            "type": "integer",
                            "minimum": 128,
                            "description": "Memory limit in MB"
                        },
                        "cpu_limit": {
                            "type": "number",
                            "minimum": 0.1,
                            "maximum": 8.0,
                            "description": "CPU limit in cores"
                        },
                        "disk_limit": {
                            "type": "integer",
                            "minimum": 100,
                            "description": "Disk limit in MB"
                        }
                    }
                },
                "environment": {
                    "type": "object",
                    "description": "Environment variables"
                },
                "dependencies": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Required dependencies"
                }
            }
        },
        "context": {
            "type": "object",
            "description": "Additional context information",
            "properties": {
                "previous_tasks": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Related previous task IDs"
                },
                "memory_context": {
                    "type": "object",
                    "description": "Memory context from previous interactions"
                },
                "user_preferences": {
                    "type": "object",
                    "description": "User preferences and settings"
                }
            }
        },
        "execution_options": {
            "type": "object",
            "properties": {
                "autonomy_level": {
                    "type": "string",
                    "enum": ["manual", "semi_autonomous", "autonomous"],
                    "default": "semi_autonomous",
                    "description": "Level of autonomous execution"
                },
                "model_preference": {
                    "type": "string",
                    "enum": ["local", "api", "hybrid"],
                    "default": "hybrid",
                    "description": "Model execution preference"
                },
                "quality_threshold": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.8,
                    "description": "Minimum quality threshold for results"
                },
                "retry_policy": {
                    "type": "object",
                    "properties": {
                        "max_retries": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 5,
                            "default": 2
                        },
                        "retry_delay": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 300,
                            "default": 30
                        }
                    }
                }
            }
        }
    },
    "additionalProperties": False
}

# Schema para ejecución de lotes de tareas (Manus → SAM)
TASK_BATCH_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://mcpenterprise.com/schemas/task-batch.json",
    "title": "Task Batch Execution Request",
    "description": "Schema for batch task execution requests",
    "type": "object",
    "required": ["batch_id", "tasks", "orchestrator_info"],
    "properties": {
        "batch_id": {
            "type": "string",
            "pattern": "^[a-zA-Z0-9_-]+$",
            "description": "Unique identifier for the batch"
        },
        "tasks": {
            "type": "array",
            "minItems": 1,
            "maxItems": 100,
            "items": {
                "$ref": "#/$defs/task_execution"
            },
            "description": "Array of tasks to execute"
        },
        "batch_options": {
            "type": "object",
            "properties": {
                "execution_mode": {
                    "type": "string",
                    "enum": ["sequential", "parallel", "dependency_based"],
                    "default": "sequential",
                    "description": "Batch execution mode"
                },
                "max_concurrent": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 3,
                    "description": "Maximum concurrent tasks for parallel execution"
                },
                "fail_fast": {
                    "type": "boolean",
                    "default": False,
                    "description": "Stop batch execution on first failure"
                },
                "timeout": {
                    "type": "integer",
                    "minimum": 60,
                    "maximum": 7200,
                    "default": 1800,
                    "description": "Total batch timeout in seconds"
                }
            }
        },
        "orchestrator_info": {
            "$ref": "#/$defs/orchestrator_info"
        }
    },
    "$defs": {
        "task_execution": TASK_EXECUTION_SCHEMA,
        "orchestrator_info": TASK_EXECUTION_SCHEMA["properties"]["orchestrator_info"]
    },
    "additionalProperties": False
}

# Schema para notificaciones (SAM → Manus)
NOTIFICATION_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://mcpenterprise.com/schemas/notification.json",
    "title": "SAM to Manus Notification",
    "description": "Schema for notifications sent from SAM to Manus",
    "type": "object",
    "required": ["notification_id", "notification_type", "task_id", "agent_id", "timestamp", "status"],
    "properties": {
        "notification_id": {
            "type": "string",
            "pattern": "^[a-zA-Z0-9_-]+$",
            "description": "Unique notification identifier"
        },
        "notification_type": {
            "type": "string",
            "enum": [
                "task_started",
                "task_progress", 
                "task_completed",
                "task_failed",
                "task_escalated",
                "agent_status",
                "system_alert"
            ],
            "description": "Type of notification"
        },
        "task_id": {
            "type": "string",
            "description": "Associated task identifier"
        },
        "agent_id": {
            "type": "string",
            "description": "SAM agent identifier"
        },
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "Notification timestamp in ISO 8601 format"
        },
        "status": {
            "type": "string",
            "enum": ["pending", "running", "completed", "failed", "escalated", "cancelled"],
            "description": "Current task status"
        },
        "data": {
            "type": "object",
            "description": "Notification-specific data",
            "oneOf": [
                {
                    "if": {
                        "properties": {
                            "notification_type": {"const": "task_started"}
                        }
                    },
                    "then": {
                        "properties": {
                            "data": {
                                "type": "object",
                                "required": ["task_type", "estimated_duration"],
                                "properties": {
                                    "task_type": {"type": "string"},
                                    "description": {"type": "string"},
                                    "estimated_duration": {"type": "integer"},
                                    "complexity": {"type": "string"},
                                    "model_selected": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                {
                    "if": {
                        "properties": {
                            "notification_type": {"const": "task_progress"}
                        }
                    },
                    "then": {
                        "properties": {
                            "data": {
                                "type": "object",
                                "required": ["progress_percentage", "current_step"],
                                "properties": {
                                    "progress_percentage": {
                                        "type": "number",
                                        "minimum": 0,
                                        "maximum": 100
                                    },
                                    "current_step": {"type": "string"},
                                    "steps_completed": {"type": "integer"},
                                    "total_steps": {"type": "integer"},
                                    "intermediate_results": {"type": "object"},
                                    "estimated_remaining": {"type": "integer"}
                                }
                            }
                        }
                    }
                },
                {
                    "if": {
                        "properties": {
                            "notification_type": {"const": "task_completed"}
                        }
                    },
                    "then": {
                        "properties": {
                            "data": {
                                "type": "object",
                                "required": ["result", "execution_summary"],
                                "properties": {
                                    "result": {"type": "object"},
                                    "output_files": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "metrics": {
                                        "type": "object",
                                        "properties": {
                                            "execution_time": {"type": "number"},
                                            "tokens_used": {"type": "integer"},
                                            "cost": {"type": "number"},
                                            "quality_score": {"type": "number"}
                                        }
                                    },
                                    "execution_summary": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                {
                    "if": {
                        "properties": {
                            "notification_type": {"const": "task_failed"}
                        }
                    },
                    "then": {
                        "properties": {
                            "data": {
                                "type": "object",
                                "required": ["error_type", "error_message"],
                                "properties": {
                                    "error_type": {"type": "string"},
                                    "error_message": {"type": "string"},
                                    "error_details": {"type": "object"},
                                    "partial_results": {"type": "object"},
                                    "recovery_suggestions": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "retry_recommended": {"type": "boolean"}
                                }
                            }
                        }
                    }
                }
            ]
        },
        "metadata": {
            "type": "object",
            "description": "Additional metadata",
            "properties": {
                "agent_version": {"type": "string"},
                "execution_mode": {"type": "string"},
                "model_used": {"type": "string"},
                "resource_usage": {
                    "type": "object",
                    "properties": {
                        "memory_mb": {"type": "integer"},
                        "cpu_seconds": {"type": "number"},
                        "disk_mb": {"type": "integer"}
                    }
                },
                "performance_metrics": {
                    "type": "object",
                    "properties": {
                        "latency_ms": {"type": "integer"},
                        "throughput": {"type": "number"},
                        "error_rate": {"type": "number"}
                    }
                }
            }
        },
        "retry_count": {
            "type": "integer",
            "minimum": 0,
            "default": 0,
            "description": "Number of retry attempts"
        },
        "max_retries": {
            "type": "integer",
            "minimum": 0,
            "default": 3,
            "description": "Maximum retry attempts"
        }
    },
    "additionalProperties": False
}

# Schema para registro de webhooks
WEBHOOK_REGISTRATION_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://mcpenterprise.com/schemas/webhook-registration.json",
    "title": "Webhook Registration",
    "description": "Schema for webhook endpoint registration",
    "type": "object",
    "required": ["endpoint_id", "url"],
    "properties": {
        "endpoint_id": {
            "type": "string",
            "pattern": "^[a-zA-Z0-9_-]+$",
            "description": "Unique endpoint identifier"
        },
        "url": {
            "type": "string",
            "format": "uri",
            "description": "Webhook endpoint URL"
        },
        "secret": {
            "type": "string",
            "minLength": 16,
            "description": "Webhook secret for signature verification"
        },
        "timeout": {
            "type": "integer",
            "minimum": 5,
            "maximum": 300,
            "default": 30,
            "description": "Request timeout in seconds"
        },
        "retry_policy": {
            "type": "object",
            "properties": {
                "max_retries": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 10,
                    "default": 3
                },
                "retry_delay": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 300,
                    "default": 30
                },
                "backoff_multiplier": {
                    "type": "number",
                    "minimum": 1.0,
                    "maximum": 5.0,
                    "default": 2.0
                }
            }
        },
        "filters": {
            "type": "object",
            "description": "Notification filters",
            "properties": {
                "notification_types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "task_started",
                            "task_progress",
                            "task_completed", 
                            "task_failed",
                            "task_escalated",
                            "agent_status",
                            "system_alert"
                        ]
                    }
                },
                "task_types": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "priority_levels": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["low", "normal", "high", "critical"]
                    }
                }
            }
        },
        "active": {
            "type": "boolean",
            "default": True,
            "description": "Whether the webhook is active"
        }
    },
    "additionalProperties": False
}

# Schema para agent_end_task
AGENT_END_TASK_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://mcpenterprise.com/schemas/agent-end-task.json",
    "title": "Agent End Task",
    "description": "Schema for agent task completion notification",
    "type": "object",
    "required": ["task_id", "agent_id", "completion_status", "timestamp"],
    "properties": {
        "task_id": {
            "type": "string",
            "description": "Task identifier"
        },
        "agent_id": {
            "type": "string",
            "description": "Agent identifier"
        },
        "completion_status": {
            "type": "string",
            "enum": ["success", "failure", "partial", "cancelled"],
            "description": "Task completion status"
        },
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "Completion timestamp"
        },
        "result_data": {
            "type": "object",
            "description": "Task result data",
            "properties": {
                "output": {"type": "object"},
                "files_created": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "files_modified": {
                    "type": "array", 
                    "items": {"type": "string"}
                },
                "artifacts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "path": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    }
                }
            }
        },
        "execution_metrics": {
            "type": "object",
            "properties": {
                "start_time": {"type": "string", "format": "date-time"},
                "end_time": {"type": "string", "format": "date-time"},
                "duration_seconds": {"type": "number"},
                "tokens_consumed": {"type": "integer"},
                "api_calls_made": {"type": "integer"},
                "cost_incurred": {"type": "number"},
                "memory_peak_mb": {"type": "integer"},
                "cpu_time_seconds": {"type": "number"}
            }
        },
        "quality_assessment": {
            "type": "object",
            "properties": {
                "overall_score": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "criteria_scores": {
                    "type": "object",
                    "properties": {
                        "correctness": {"type": "number"},
                        "completeness": {"type": "number"},
                        "efficiency": {"type": "number"},
                        "maintainability": {"type": "number"}
                    }
                },
                "feedback": {"type": "string"}
            }
        },
        "error_information": {
            "type": "object",
            "description": "Error details if completion_status is failure",
            "properties": {
                "error_code": {"type": "string"},
                "error_message": {"type": "string"},
                "error_stack": {"type": "string"},
                "recovery_attempted": {"type": "boolean"},
                "recovery_actions": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "next_actions": {
            "type": "object",
            "description": "Recommended next actions",
            "properties": {
                "cleanup_required": {"type": "boolean"},
                "follow_up_tasks": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "escalation_needed": {"type": "boolean"},
                "user_notification_required": {"type": "boolean"}
            }
        }
    },
    "additionalProperties": False
}

# Schema para solicitudes de estado
STATUS_REQUEST_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://mcpenterprise.com/schemas/status-request.json",
    "title": "Status Request",
    "description": "Schema for status requests",
    "type": "object",
    "required": ["request_type"],
    "properties": {
        "request_type": {
            "type": "string",
            "enum": ["task_status", "agent_status", "system_status", "batch_status"],
            "description": "Type of status request"
        },
        "target_id": {
            "type": "string",
            "description": "ID of the target (task, agent, batch, etc.)"
        },
        "include_details": {
            "type": "boolean",
            "default": False,
            "description": "Whether to include detailed information"
        },
        "include_metrics": {
            "type": "boolean",
            "default": False,
            "description": "Whether to include performance metrics"
        },
        "include_history": {
            "type": "boolean",
            "default": False,
            "description": "Whether to include historical data"
        },
        "time_range": {
            "type": "object",
            "properties": {
                "start_time": {"type": "string", "format": "date-time"},
                "end_time": {"type": "string", "format": "date-time"}
            },
            "description": "Time range for historical data"
        }
    },
    "additionalProperties": False
}

class PayloadValidator:
    """
    Validador de payloads para el sistema MCP Orchestrator-Executor
    """
    
    def __init__(self):
        self.schemas = {
            PayloadType.TASK_EXECUTION: TASK_EXECUTION_SCHEMA,
            PayloadType.TASK_BATCH: TASK_BATCH_SCHEMA,
            PayloadType.NOTIFICATION: NOTIFICATION_SCHEMA,
            PayloadType.WEBHOOK_REGISTRATION: WEBHOOK_REGISTRATION_SCHEMA,
            PayloadType.STATUS_REQUEST: STATUS_REQUEST_SCHEMA,
            PayloadType.AGENT_END_TASK: AGENT_END_TASK_SCHEMA
        }
    
    def validate_payload(self, payload: Dict[str, Any], payload_type: PayloadType) -> Dict[str, Any]:
        """
        Validar payload contra el schema correspondiente
        
        Args:
            payload: Datos a validar
            payload_type: Tipo de payload
            
        Returns:
            Dict con resultado de validación
        """
        try:
            schema = self.schemas.get(payload_type)
            if not schema:
                return {
                    "valid": False,
                    "error": f"Unknown payload type: {payload_type}",
                    "error_type": "schema_not_found"
                }
            
            # Validar contra schema
            validate(instance=payload, schema=schema)
            
            return {
                "valid": True,
                "payload_type": payload_type.value,
                "validated_at": datetime.now().isoformat()
            }
            
        except ValidationError as e:
            return {
                "valid": False,
                "error": e.message,
                "error_path": list(e.absolute_path),
                "error_type": "validation_error",
                "schema_path": list(e.schema_path)
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "error_type": "unexpected_error"
            }
    
    def get_schema(self, payload_type: PayloadType) -> Optional[Dict[str, Any]]:
        """Obtener schema para un tipo de payload específico"""
        return self.schemas.get(payload_type)
    
    def get_all_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Obtener todos los schemas disponibles"""
        return {pt.value: schema for pt, schema in self.schemas.items()}

# Instancia global del validador
payload_validator = PayloadValidator()

def create_task_execution_payload(
    task_id: str,
    task_type: str,
    description: str,
    orchestrator_agent_id: str,
    priority: str = "normal",
    **kwargs
) -> Dict[str, Any]:
    """
    Crear payload válido para ejecución de tarea
    """
    payload = {
        "task_id": task_id,
        "task_type": task_type,
        "description": description,
        "priority": priority,
        "orchestrator_info": {
            "agent_id": orchestrator_agent_id,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    # Añadir campos opcionales
    for key, value in kwargs.items():
        if key in TASK_EXECUTION_SCHEMA["properties"]:
            payload[key] = value
    
    return payload

def create_notification_payload(
    notification_type: str,
    task_id: str,
    agent_id: str,
    status: str,
    data: Dict[str, Any],
    **kwargs
) -> Dict[str, Any]:
    """
    Crear payload válido para notificación
    """
    import uuid
    
    payload = {
        "notification_id": str(uuid.uuid4()),
        "notification_type": notification_type,
        "task_id": task_id,
        "agent_id": agent_id,
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "data": data
    }
    
    # Añadir campos opcionales
    for key, value in kwargs.items():
        if key in NOTIFICATION_SCHEMA["properties"]:
            payload[key] = value
    
    return payload

def create_agent_end_task_payload(
    task_id: str,
    agent_id: str,
    completion_status: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Crear payload válido para agent_end_task
    """
    payload = {
        "task_id": task_id,
        "agent_id": agent_id,
        "completion_status": completion_status,
        "timestamp": datetime.now().isoformat()
    }
    
    # Añadir campos opcionales
    for key, value in kwargs.items():
        if key in AGENT_END_TASK_SCHEMA["properties"]:
            payload[key] = value
    
    return payload

# Ejemplos de uso
if __name__ == "__main__":
    # Ejemplo de validación de payload de tarea
    task_payload = create_task_execution_payload(
        task_id="task_001",
        task_type="code_generation",
        description="Generate a Python function to calculate fibonacci numbers",
        orchestrator_agent_id="manus_001",
        priority="normal",
        complexity="medium",
        estimated_duration=300
    )
    
    result = payload_validator.validate_payload(task_payload, PayloadType.TASK_EXECUTION)
    print("Task payload validation:", json.dumps(result, indent=2))
    
    # Ejemplo de validación de notificación
    notification_payload = create_notification_payload(
        notification_type="task_completed",
        task_id="task_001",
        agent_id="sam_001",
        status="completed",
        data={
            "result": {"function": "def fibonacci(n): ..."},
            "execution_summary": "Successfully generated fibonacci function"
        }
    )
    
    result = payload_validator.validate_payload(notification_payload, PayloadType.NOTIFICATION)
    print("Notification payload validation:", json.dumps(result, indent=2))
    
    # Ejemplo de agent_end_task
    end_task_payload = create_agent_end_task_payload(
        task_id="task_001",
        agent_id="sam_001",
        completion_status="success",
        result_data={
            "output": {"function_code": "def fibonacci(n): ..."},
            "files_created": ["fibonacci.py"]
        },
        execution_metrics={
            "duration_seconds": 45.2,
            "tokens_consumed": 1250,
            "cost_incurred": 0.025
        }
    )
    
    result = payload_validator.validate_payload(end_task_payload, PayloadType.AGENT_END_TASK)
    print("Agent end task payload validation:", json.dumps(result, indent=2))

