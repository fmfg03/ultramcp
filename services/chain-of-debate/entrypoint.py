"""
Chain-of-Debate Dinámico - SuperMCP Enterprise
Flask App Puerto 5555

Sistema de superinteligencia colectiva con debate multi-LLM contextual,
role assignment dinámico, shadow learning automático, y decision replay
para auditoría evolutiva.

Filosofía: "brutal pero funcional"
"""

from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os
import logging
from dataclasses import dataclass, asdict
from enum import Enum

# Importar componentes del sistema
from dynamic_roles import DynamicRoleOrchestrator
from shadow_learning import ShadowLearningEngine
from decision_replay import DecisionReplaySystem
from model_resilience import ModelResilienceOrchestrator
from debate_handler import DebateHandler

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar Flask
app = Flask(__name__)
CORS(app, origins=["*"])
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-key-chain-of-debate')

class TaskDomain(Enum):
    """Dominios de tareas soportados"""
    PROPOSAL = "proposal"
    CONTENT = "content"
    CONTRACT = "contract"
    STRATEGY = "strategy"
    TECHNICAL = "technical"
    FINANCIAL = "financial"

class DebateStatus(Enum):
    """Estados del proceso de debate"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CONSENSUS_REACHED = "consensus_reached"
    HUMAN_INTERVENTION = "human_intervention"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class DebateTask:
    """Tarea de debate en el sistema"""
    task_id: str
    domain: TaskDomain
    input_content: str
    context: Dict[str, Any]
    status: DebateStatus
    created_at: datetime
    deadline: Optional[datetime] = None
    priority: int = 1
    model_outputs: Dict[str, Any] = None
    consensus_result: str = None
    human_intervention_used: bool = False
    cost: float = 0.0
    quality_score: float = 0.0

# Inicializar componentes del sistema
role_orchestrator = DynamicRoleOrchestrator()
shadow_learning = ShadowLearningEngine()
replay_system = DecisionReplaySystem()
resilience_orchestrator = ModelResilienceOrchestrator()
debate_handler = DebateHandler(
    role_orchestrator=role_orchestrator,
    resilience_orchestrator=resilience_orchestrator
)

# Estado global del sistema
active_debates = {}
pending_human_reviews = {}
system_metrics = {
    "total_debates": 0,
    "consensus_rate": 0.0,
    "human_intervention_rate": 0.0,
    "avg_quality_score": 0.0,
    "total_revenue": 0.0
}

# === RUTAS PRINCIPALES ===

@app.route('/')
def dashboard():
    """Dashboard principal del sistema"""
    try:
        dashboard_data = {
            "active_debates": len(active_debates),
            "pending_reviews": len(pending_human_reviews),
            "system_metrics": system_metrics,
            "recent_tasks": list(active_debates.values())[-5:] if active_debates else []
        }
        return render_template('dashboard.html', data=dashboard_data)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return jsonify({"error": "Dashboard unavailable"}), 500

@app.route('/api/v1/debate/submit', methods=['POST'])
async def submit_debate_task():
    """
    Endpoint principal para iniciar un debate multi-LLM
    POST /api/v1/debate/submit
    """
    try:
        data = request.get_json()
        
        # Validar entrada
        if not data or 'content' not in data:
            return jsonify({
                "error": "Missing required field: content",
                "status": "error"
            }), 400
        
        # Crear tarea de debate
        task_id = str(uuid.uuid4())
        domain = TaskDomain(data.get('domain', 'strategy'))
        
        task = DebateTask(
            task_id=task_id,
            domain=domain,
            input_content=data['content'],
            context=data.get('context', {}),
            status=DebateStatus.PENDING,
            created_at=datetime.now(),
            deadline=_parse_deadline(data.get('deadline')),
            priority=data.get('priority', 1)
        )
        
        active_debates[task_id] = task
        
        # Iniciar debate asíncrono
        asyncio.create_task(_process_debate_task(task))
        
        logger.info(f"🎯 Debate task submitted: {task_id} ({domain.value})")
        
        return jsonify({
            "task_id": task_id,
            "status": "submitted",
            "estimated_completion": "2-5 minutes",
            "domain": domain.value,
            "message": "Debate iniciado - superinteligencia colectiva activada"
        }), 202
        
    except Exception as e:
        logger.error(f"Submit debate error: {e}")
        return jsonify({
            "error": f"Failed to submit debate: {str(e)}",
            "status": "error"
        }), 500

@app.route('/api/v1/debate/status/<task_id>')
def get_debate_status(task_id: str):
    """
    Obtener estado actual de un debate
    GET /api/v1/debate/status/{task_id}
    """
    try:
        if task_id not in active_debates:
            return jsonify({
                "error": "Task not found",
                "task_id": task_id
            }), 404
        
        task = active_debates[task_id]
        
        response = {
            "task_id": task_id,
            "status": task.status.value,
            "domain": task.domain.value,
            "created_at": task.created_at.isoformat(),
            "progress": _calculate_progress(task),
            "human_intervention_used": task.human_intervention_used,
            "cost": task.cost
        }
        
        # Agregar resultado si está completo
        if task.status == DebateStatus.COMPLETED and task.consensus_result:
            response["result"] = task.consensus_result
            response["quality_score"] = task.quality_score
            response["model_outputs"] = task.model_outputs
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({"error": "Status check failed"}), 500

@app.route('/api/v1/human/pending')
def get_pending_reviews():
    """
    Obtener tareas pendientes de revisión humana
    GET /api/v1/human/pending
    """
    try:
        pending_tasks = []
        
        for task_id, task in pending_human_reviews.items():
            time_remaining = _calculate_time_remaining(task)
            
            pending_tasks.append({
                "task_id": task_id,
                "domain": task.domain.value,
                "input_content": task.input_content[:200] + "..." if len(task.input_content) > 200 else task.input_content,
                "time_remaining_seconds": time_remaining,
                "priority": task.priority,
                "cost_if_intervene": 1.0,  # $1 por intervención
                "created_at": task.created_at.isoformat()
            })
        
        # Ordenar por prioridad y tiempo restante
        pending_tasks.sort(key=lambda x: (x['priority'], x['time_remaining_seconds']))
        
        return jsonify({
            "pending_count": len(pending_tasks),
            "tasks": pending_tasks,
            "total_intervention_cost": len(pending_tasks) * 1.0
        }), 200
        
    except Exception as e:
        logger.error(f"Pending reviews error: {e}")
        return jsonify({"error": "Failed to get pending reviews"}), 500

@app.route('/human/review/<task_id>')
def human_review_interface(task_id: str):
    """
    Interfaz de revisión humana tipo Slack thread
    """
    try:
        if task_id not in pending_human_reviews:
            return redirect(url_for('dashboard'))
        
        task = pending_human_reviews[task_id]
        
        review_data = {
            "task": asdict(task),
            "model_outputs": task.model_outputs or {},
            "time_remaining": _calculate_time_remaining(task),
            "intervention_cost": 1.0
        }
        
        return render_template('review_task.html', data=review_data)
        
    except Exception as e:
        logger.error(f"Review interface error: {e}")
        return redirect(url_for('dashboard'))

@app.route('/api/v1/human/intervene/<task_id>', methods=['POST'])
async def human_intervention(task_id: str):
    """
    Processar intervención humana en un debate
    POST /api/v1/human/intervene/{task_id}
    """
    try:
        if task_id not in pending_human_reviews:
            return jsonify({"error": "Task not found in pending reviews"}), 404
        
        data = request.get_json()
        action = data.get('action')  # 'approve', 'modify', 'reject'
        
        task = pending_human_reviews[task_id]
        
        if action == 'approve':
            # Aprobar resultado sin costo adicional
            task.status = DebateStatus.COMPLETED
            task.cost += 0.0  # Sin costo por aprobar
            
        elif action == 'modify':
            # Modificar resultado - costo $1
            task.consensus_result = data.get('modified_result', task.consensus_result)
            task.status = DebateStatus.COMPLETED
            task.human_intervention_used = True
            task.cost += 1.0
            
        elif action == 'reject':
            # Rechazar y reiniciar - costo $2
            task.status = DebateStatus.PENDING
            task.human_intervention_used = True
            task.cost += 2.0
            # Reiniciar debate con contexto adicional
            asyncio.create_task(_process_debate_task(task, retry=True))
        
        # Mover de pending a active
        active_debates[task_id] = task
        del pending_human_reviews[task_id]
        
        # Actualizar métricas
        _update_system_metrics(task)
        
        # Log para shadow learning
        await shadow_learning.log_human_intervention(
            task_id=task_id,
            original_result=task.model_outputs,
            human_action=action,
            final_result=task.consensus_result,
            context=task.context
        )
        
        logger.info(f"👤 Human intervention: {action} on {task_id} (cost: ${task.cost})")
        
        return jsonify({
            "status": "intervention_processed",
            "action": action,
            "final_cost": task.cost,
            "task_status": task.status.value
        }), 200
        
    except Exception as e:
        logger.error(f"Human intervention error: {e}")
        return jsonify({"error": "Intervention failed"}), 500

@app.route('/api/v1/replay/dashboard')
def replay_dashboard():
    """
    Dashboard de auditoría evolutiva
    GET /api/v1/replay/dashboard
    """
    try:
        replay_analytics = replay_system.get_improvement_analytics()
        
        return jsonify({
            "system_evolution": replay_analytics,
            "recent_improvements": replay_system.get_recent_improvements(),
            "roi_justification": replay_system.calculate_roi_metrics(),
            "quality_trends": replay_system.get_quality_trends()
        }), 200
        
    except Exception as e:
        logger.error(f"Replay dashboard error: {e}")
        return jsonify({"error": "Replay dashboard unavailable"}), 500

@app.route('/api/v1/replay/execute/<task_id>', methods=['POST'])
async def execute_replay(task_id: str):
    """
    Ejecutar replay de una decisión pasada
    POST /api/v1/replay/execute/{task_id}
    """
    try:
        improvement_analysis = await replay_system.replay_decision(task_id)
        
        return jsonify({
            "replay_id": improvement_analysis.get("replay_id"),
            "improvement_score": improvement_analysis.get("improvement_score"),
            "key_differences": improvement_analysis.get("differences"),
            "recommendation": improvement_analysis.get("recommendation")
        }), 200
        
    except Exception as e:
        logger.error(f"Replay execution error: {e}")
        return jsonify({"error": "Replay failed"}), 500

@app.route('/api/v1/metrics')
def get_system_metrics():
    """
    Métricas del sistema en tiempo real
    GET /api/v1/metrics
    """
    try:
        current_metrics = {
            **system_metrics,
            "active_debates": len(active_debates),
            "pending_reviews": len(pending_human_reviews),
            "model_health": resilience_orchestrator.get_health_status(),
            "learning_progress": shadow_learning.get_learning_metrics(),
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(current_metrics), 200
        
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return jsonify({"error": "Metrics unavailable"}), 500

# === FUNCIONES AUXILIARES ===

async def _process_debate_task(task: DebateTask, retry: bool = False):
    """Procesar una tarea de debate con los modelos"""
    try:
        task.status = DebateStatus.IN_PROGRESS
        
        # Obtener roles dinámicos basados en contexto
        roles = role_orchestrator.assign_roles_by_context(
            task.input_content, 
            task.domain.value,
            task.context
        )
        
        # Ejecutar debate multi-LLM
        debate_result = await debate_handler.conduct_debate(
            content=task.input_content,
            domain=task.domain.value,
            roles=roles,
            context=task.context
        )
        
        task.model_outputs = debate_result.get("model_outputs", {})
        consensus_score = debate_result.get("consensus_score", 0.0)
        
        # Determinar si necesita intervención humana
        if _needs_human_intervention(task, consensus_score, retry):
            task.status = DebateStatus.HUMAN_INTERVENTION
            pending_human_reviews[task.task_id] = task
            logger.info(f"🤔 Task {task.task_id} requires human intervention (consensus: {consensus_score})")
            
            # Auto-fallback después de timeout
            asyncio.create_task(_auto_fallback_after_timeout(task.task_id))
            
        else:
            # Consenso alcanzado automáticamente
            task.status = DebateStatus.COMPLETED
            task.consensus_result = debate_result.get("final_result")
            task.quality_score = debate_result.get("quality_score", 0.0)
            task.cost += debate_result.get("total_cost", 0.0)
            
            logger.info(f"✅ Debate completed automatically: {task.task_id} (score: {task.quality_score})")
        
        # Log para shadow learning
        await shadow_learning.log_debate_outcome(
            task_id=task.task_id,
            input_content=task.input_content,
            domain=task.domain.value,
            model_outputs=task.model_outputs,
            final_result=task.consensus_result,
            consensus_score=consensus_score,
            context=task.context
        )
        
        # Actualizar métricas
        _update_system_metrics(task)
        
    except Exception as e:
        logger.error(f"Debate processing error for {task.task_id}: {e}")
        task.status = DebateStatus.FAILED
        task.consensus_result = f"Error: {str(e)}"

def _needs_human_intervention(task: DebateTask, consensus_score: float, retry: bool) -> bool:
    """Determinar si una tarea necesita intervención humana"""
    # Reglas para intervención humana
    if consensus_score < 0.7:  # Consenso bajo
        return True
    
    if task.priority >= 8:  # Alta prioridad siempre revisada
        return True
    
    if retry:  # Segunda oportunidad después de rechazo
        return False
    
    # Intervención aleatoria para training (10%)
    import random
    if random.random() < 0.1:
        return True
    
    return False

async def _auto_fallback_after_timeout(task_id: str):
    """Auto-fallback después de timeout de intervención humana"""
    await asyncio.sleep(300)  # 5 minutos timeout
    
    if task_id in pending_human_reviews:
        task = pending_human_reviews[task_id]
        
        # Usar el mejor resultado disponible
        if task.model_outputs:
            best_output = max(task.model_outputs.values(), key=lambda x: x.get('confidence', 0))
            task.consensus_result = best_output.get('content', 'Auto-fallback result')
            task.quality_score = best_output.get('confidence', 0.5)
        
        task.status = DebateStatus.COMPLETED
        active_debates[task_id] = task
        del pending_human_reviews[task_id]
        
        logger.info(f"⏰ Auto-fallback executed for {task_id}")

def _calculate_progress(task: DebateTask) -> float:
    """Calcular progreso de una tarea"""
    if task.status == DebateStatus.PENDING:
        return 0.0
    elif task.status == DebateStatus.IN_PROGRESS:
        return 0.5
    elif task.status == DebateStatus.HUMAN_INTERVENTION:
        return 0.8
    elif task.status == DebateStatus.COMPLETED:
        return 1.0
    else:
        return 0.1

def _calculate_time_remaining(task: DebateTask) -> int:
    """Calcular tiempo restante para timeout (en segundos)"""
    if task.deadline:
        remaining = (task.deadline - datetime.now()).total_seconds()
        return max(0, int(remaining))
    
    # Default: 5 minutos para intervención
    elapsed = (datetime.now() - task.created_at).total_seconds()
    return max(0, int(300 - elapsed))

def _parse_deadline(deadline_str: Optional[str]) -> Optional[datetime]:
    """Parse deadline string to datetime"""
    if not deadline_str:
        return None
    
    try:
        return datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
    except:
        return None

def _update_system_metrics(task: DebateTask):
    """Actualizar métricas del sistema"""
    global system_metrics
    
    system_metrics["total_debates"] += 1
    
    if task.status == DebateStatus.COMPLETED:
        system_metrics["total_revenue"] += task.cost
        
        # Calcular tasas
        total_tasks = system_metrics["total_debates"]
        human_interventions = sum(1 for t in active_debates.values() if t.human_intervention_used)
        
        system_metrics["human_intervention_rate"] = (human_interventions / total_tasks) * 100
        
        # Calcular calidad promedio
        completed_tasks = [t for t in active_debates.values() if t.status == DebateStatus.COMPLETED]
        if completed_tasks:
            avg_quality = sum(t.quality_score for t in completed_tasks) / len(completed_tasks)
            system_metrics["avg_quality_score"] = avg_quality

if __name__ == '__main__':
    logger.info("🚀 Starting Chain-of-Debate Dinámico on port 5555")
    logger.info("🧠 Superinteligencia colectiva activada")
    
    # Configuración para desarrollo
    app.run(
        host='0.0.0.0',
        port=5555,
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
        threaded=True
    )