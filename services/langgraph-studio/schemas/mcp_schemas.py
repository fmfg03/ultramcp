"""
Schemas para el sistema LangGraph MCP

Define los tipos de entrada y salida para todos los agentes LangGraph,
manteniendo compatibilidad con el sistema MCP existente.
"""

from typing import Dict, List, Optional, Any, Union
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from enum import Enum

# ============================================================================
# Enums y Constantes
# ============================================================================

class TaskComplexity(str, Enum):
    """Niveles de complejidad de tareas"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"

class ModelType(str, Enum):
    """Tipos de modelos disponibles"""
    MISTRAL_LOCAL = "mistral-local"
    LLAMA_LOCAL = "llama-local"
    DEEPSEEK_LOCAL = "deepseek-local"
    AUTO = "auto"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class TaskStatus(str, Enum):
    """Estados de ejecución de tareas"""
    PENDING = "pending"
    REASONING = "reasoning"
    BUILDING = "building"
    EVALUATING = "evaluating"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"

# ============================================================================
# Schemas Base
# ============================================================================

class BaseTaskInput(TypedDict):
    """Schema base para entrada de tareas"""
    request: str
    session_id: Optional[str]
    user_id: Optional[str]
    options: Optional[Dict[str, Any]]

class BaseTaskOutput(TypedDict):
    """Schema base para salida de tareas"""
    success: bool
    result: Optional[str]
    session_id: str
    metadata: Dict[str, Any]

class LangwatchMetadata(TypedDict):
    """Metadata de tracking de Langwatch"""
    tracking_id: str
    score: float
    contradiction: Optional[Dict[str, Any]]
    tracked: bool
    duration_ms: int
    token_usage: Dict[str, int]

class ContradictionInfo(TypedDict):
    """Información de contradicción explícita"""
    triggered: bool
    intensity: str
    attempt_number: int
    previous_scores: List[float]
    improvement_detected: bool

# ============================================================================
# Reasoning Agent Schemas
# ============================================================================

class ReasoningInput(TypedDict):
    """Input para el agente de razonamiento"""
    request: str
    session_id: Optional[str]
    context: Optional[Dict[str, Any]]
    complexity_hint: Optional[TaskComplexity]

class ReasoningOutput(TypedDict):
    """Output del agente de razonamiento"""
    success: bool
    plan: Dict[str, Any]
    subtasks: List[Dict[str, Any]]
    estimated_complexity: TaskComplexity
    recommended_model: ModelType
    session_id: str
    metadata: Dict[str, Any]

class ReasoningState(ReasoningInput, ReasoningOutput):
    """Estado completo del agente de razonamiento"""
    pass

# ============================================================================
# Builder Agent Schemas  
# ============================================================================

class BuilderInput(TypedDict):
    """Input para el agente constructor"""
    request: str
    plan: Optional[Dict[str, Any]]
    subtasks: Optional[List[Dict[str, Any]]]
    session_id: Optional[str]
    model_type: Optional[ModelType]
    retry_context: Optional[Dict[str, Any]]

class BuilderOutput(TypedDict):
    """Output del agente constructor"""
    success: bool
    result: str
    artifacts: List[Dict[str, Any]]
    execution_log: List[Dict[str, Any]]
    session_id: str
    langwatch_metadata: Optional[LangwatchMetadata]

class BuilderState(BuilderInput, BuilderOutput):
    """Estado completo del agente constructor"""
    pass

# ============================================================================
# Orchestration Agent Schemas
# ============================================================================

class OrchestrationInput(TypedDict):
    """Input para el agente de orquestación completo"""
    request: str
    session_id: Optional[str]
    user_id: Optional[str]
    options: Optional[Dict[str, Any]]
    retry_config: Optional[Dict[str, Any]]

class OrchestrationOutput(TypedDict):
    """Output del agente de orquestación"""
    success: bool
    final_result: str
    reasoning_plan: Dict[str, Any]
    builder_artifacts: List[Dict[str, Any]]
    reward_evaluation: Dict[str, Any]
    retry_history: List[Dict[str, Any]]
    session_id: str
    total_duration_ms: int
    langwatch_summary: Dict[str, Any]

class OrchestrationState(OrchestrationInput, OrchestrationOutput):
    """Estado completo del agente de orquestación"""
    # Estados intermedios
    current_status: Optional[TaskStatus]
    reasoning_result: Optional[ReasoningOutput]
    builder_result: Optional[BuilderOutput]
    reward_score: Optional[float]
    retry_count: Optional[int]
    contradiction_applied: Optional[bool]

# ============================================================================
# Reward/Evaluation Schemas
# ============================================================================

class RewardInput(TypedDict):
    """Input para evaluación de reward"""
    original_request: str
    builder_output: str
    context: Dict[str, Any]
    session_id: str

class RewardOutput(TypedDict):
    """Output de evaluación de reward"""
    score: float
    feedback: str
    retry_recommended: bool
    improvement_suggestions: List[str]
    quality_metrics: Dict[str, float]

# ============================================================================
# Retry/Contradiction Schemas
# ============================================================================

class RetryInput(TypedDict):
    """Input para lógica de retry"""
    original_request: str
    previous_attempts: List[Dict[str, Any]]
    current_score: float
    session_id: str

class RetryOutput(TypedDict):
    """Output de lógica de retry"""
    should_retry: bool
    apply_contradiction: bool
    contradiction_intensity: str
    modified_request: str
    retry_strategy: str

# ============================================================================
# Memory/Context Schemas
# ============================================================================

class MemoryContext(TypedDict):
    """Contexto de memoria para sesiones"""
    session_id: str
    previous_attempts: List[Dict[str, Any]]
    learned_patterns: Dict[str, Any]
    user_preferences: Dict[str, Any]
    success_history: List[Dict[str, Any]]

# ============================================================================
# Pydantic Models para Validación
# ============================================================================

class TaskRequest(BaseModel):
    """Modelo Pydantic para validación de requests"""
    request: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9_-]+$')
    user_id: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9_-]+$')
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        extra = "allow"

class TaskResponse(BaseModel):
    """Modelo Pydantic para validación de responses"""
    success: bool
    result: Optional[str] = None
    session_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        extra = "allow"

# ============================================================================
# Utilidades de Conversión
# ============================================================================

def convert_legacy_request(legacy_data: Dict[str, Any]) -> OrchestrationInput:
    """Convierte requests del sistema legacy al nuevo formato"""
    return OrchestrationInput(
        request=legacy_data.get('request', ''),
        session_id=legacy_data.get('sessionId'),
        user_id=legacy_data.get('userId'),
        options=legacy_data.get('options', {}),
        retry_config=legacy_data.get('retryConfig')
    )

def convert_to_legacy_response(output: OrchestrationOutput) -> Dict[str, Any]:
    """Convierte output de LangGraph al formato legacy"""
    return {
        'success': output['success'],
        'result': output['final_result'],
        'sessionId': output['session_id'],
        'metadata': {
            'reasoning': output['reasoning_plan'],
            'artifacts': output['builder_artifacts'],
            'evaluation': output['reward_evaluation'],
            'retries': output['retry_history'],
            'duration': output['total_duration_ms'],
            'langwatch': output['langwatch_summary']
        }
    }

# ============================================================================
# MCP Agent Schemas (Aliases para compatibilidad)
# ============================================================================

# Aliases para el agente MCP completo
MCPAgentInput = OrchestrationInput
MCPAgentOutput = OrchestrationOutput  
MCPAgentState = OrchestrationState

# ============================================================================
# Configuración de Schemas por Agente
# ============================================================================

AGENT_SCHEMAS = {
    'mcp_reasoning_agent': {
        'input': ReasoningInput,
        'output': ReasoningOutput,
        'state': ReasoningState
    },
    'mcp_builder_agent': {
        'input': BuilderInput,
        'output': BuilderOutput,
        'state': BuilderState
    },
    'mcp_orchestration_agent': {
        'input': OrchestrationInput,
        'output': OrchestrationOutput,
        'state': OrchestrationState
    }
}

# ============================================================================
# Validadores
# ============================================================================

def validate_task_input(data: Dict[str, Any], agent_type: str) -> bool:
    """Valida input para un tipo de agente específico"""
    try:
        schema = AGENT_SCHEMAS[agent_type]['input']
        # Validación básica de campos requeridos
        required_fields = schema.__annotations__.keys()
        for field in required_fields:
            if field not in data and not field.startswith('Optional'):
                return False
        return True
    except Exception:
        return False

def validate_task_output(data: Dict[str, Any], agent_type: str) -> bool:
    """Valida output para un tipo de agente específico"""
    try:
        schema = AGENT_SCHEMAS[agent_type]['output']
        # Validación básica de campos requeridos
        required_fields = ['success', 'session_id']
        for field in required_fields:
            if field not in data:
                return False
        return True
    except Exception:
        return False

