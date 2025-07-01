"""
Debate Handler para Chain-of-Debate SuperMCP

Núcleo del sistema de debate multi-LLM que orquesta conversaciones
entre modelos especializados para alcanzar consenso inteligente.

Proceso de Debate:
1. Asignación de roles especializados
2. Rounds de debate estructurado  
3. Análisis de consenso automático
4. Síntesis de resultado final
5. Evaluación de calidad

Modelos Soportados:
- GPT-4 (OpenAI)
- Claude-3-Sonnet (Anthropic) 
- Gemini-Pro (Google)
- Fallback a modelos locales
"""

import asyncio
import json
import logging
import time
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import openai
import anthropic
import google.generativeai as genai
from datetime import datetime

from dynamic_roles import DynamicRoleOrchestrator, RoleAssignment, RoleType
from model_resilience import ModelResilienceOrchestrator

logger = logging.getLogger(__name__)

class DebateStage(Enum):
    """Etapas del proceso de debate"""
    INITIALIZATION = "initialization"
    OPENING_STATEMENTS = "opening_statements"
    DEBATE_ROUNDS = "debate_rounds"
    CONSENSUS_CHECK = "consensus_check"
    FINAL_SYNTHESIS = "final_synthesis"
    COMPLETED = "completed"

@dataclass
class ModelResponse:
    """Respuesta de un modelo individual"""
    model_name: str
    role: RoleType
    content: str
    confidence: float
    reasoning: str
    timestamp: datetime
    tokens_used: int = 0
    response_time: float = 0.0
    cost: float = 0.0

@dataclass
class DebateRound:
    """Una ronda completa de debate"""
    round_number: int
    topic: str
    responses: List[ModelResponse]
    consensus_score: float
    synthesis: str
    duration: float

@dataclass
class DebateResult:
    """Resultado final del debate"""
    task_id: str
    domain: str
    rounds: List[DebateRound]
    final_result: str
    consensus_score: float
    quality_score: float
    model_outputs: Dict[str, Any]
    total_cost: float
    total_tokens: int
    total_duration: float
    human_intervention_triggered: bool

class DebateHandler:
    """
    Manejador principal del sistema de debate multi-LLM
    """
    
    def __init__(
        self, 
        role_orchestrator: DynamicRoleOrchestrator,
        resilience_orchestrator: ModelResilienceOrchestrator
    ):
        self.role_orchestrator = role_orchestrator
        self.resilience_orchestrator = resilience_orchestrator
        
        # Configuración de APIs
        self._setup_api_clients()
        
        # Configuración de debate
        self.max_rounds = 3
        self.consensus_threshold = 0.7
        self.max_response_time = 30  # segundos
        
        # Métricas
        self.debate_history = []
        
        logger.info("🎪 Debate Handler initialized")
    
    def _setup_api_clients(self):
        """Configurar clientes de APIs para modelos LLM"""
        try:
            # OpenAI GPT-4
            self.openai_client = openai.AsyncOpenAI(
                api_key=os.getenv('OPENAI_API_KEY')
            )
            
            # Anthropic Claude
            self.anthropic_client = anthropic.AsyncAnthropic(
                api_key=os.getenv('ANTHROPIC_API_KEY')
            )
            
            # Google Gemini
            genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
            
            logger.info("✅ API clients configured")
            
        except Exception as e:
            logger.error(f"API setup error: {e}")
    
    async def conduct_debate(
        self,
        content: str,
        domain: str,
        roles: Dict[str, RoleAssignment],
        context: Dict[str, Any] = None,
        max_rounds: int = None
    ) -> Dict[str, Any]:
        """
        Conducir un debate completo entre modelos especializados
        
        Args:
            content: Contenido a debatir
            domain: Dominio de la tarea
            roles: Asignaciones de roles por modelo
            context: Contexto adicional
            max_rounds: Máximo número de rondas
            
        Returns:
            Resultado completo del debate
        """
        debate_start = time.time()
        task_id = f"debate_{int(debate_start)}"
        
        try:
            logger.info(f"🎪 Starting debate: {task_id} ({domain})")
            
            max_rounds = max_rounds or self.max_rounds
            rounds = []
            total_cost = 0.0
            total_tokens = 0
            
            # Ronda inicial: Declaraciones de apertura
            opening_round = await self._conduct_opening_statements(
                content, domain, roles, context
            )
            rounds.append(opening_round)
            total_cost += sum(r.cost for r in opening_round.responses)
            total_tokens += sum(r.tokens_used for r in opening_round.responses)
            
            # Verificar consenso inicial
            if opening_round.consensus_score >= self.consensus_threshold:
                logger.info(f"🎯 Early consensus achieved: {opening_round.consensus_score:.2f}")
                final_result = opening_round.synthesis
                quality_score = opening_round.consensus_score
            else:
                # Rondas de debate iterativo
                final_result, quality_score = await self._conduct_debate_rounds(
                    content, domain, roles, context, rounds, max_rounds
                )
                total_cost += sum(
                    sum(r.cost for r in round.responses) 
                    for round in rounds[1:]
                )
                total_tokens += sum(
                    sum(r.tokens_used for r in round.responses) 
                    for round in rounds[1:]
                )
            
            # Síntesis final si es necesaria
            if len(rounds) > 1:
                final_synthesis = await self._generate_final_synthesis(rounds, domain)
                final_result = final_synthesis
            
            total_duration = time.time() - debate_start
            
            # Construir resultado
            debate_result = DebateResult(
                task_id=task_id,
                domain=domain,
                rounds=rounds,
                final_result=final_result,
                consensus_score=rounds[-1].consensus_score,
                quality_score=quality_score,
                model_outputs=self._extract_model_outputs(rounds),
                total_cost=total_cost,
                total_tokens=total_tokens,
                total_duration=total_duration,
                human_intervention_triggered=quality_score < self.consensus_threshold
            )
            
            # Guardar en historial
            self.debate_history.append(debate_result)
            
            logger.info(f"✅ Debate completed: {task_id} (consensus: {quality_score:.2f}, cost: ${total_cost:.2f})")
            
            return self._format_debate_result(debate_result)
            
        except Exception as e:
            logger.error(f"Debate error for {task_id}: {e}")
            return self._generate_error_result(task_id, str(e))
    
    async def _conduct_opening_statements(
        self,
        content: str,
        domain: str,
        roles: Dict[str, RoleAssignment],
        context: Dict[str, Any]
    ) -> DebateRound:
        """Conducir ronda de declaraciones de apertura"""
        
        round_start = time.time()
        responses = []
        
        # Preparar prompts especializados
        model_tasks = []
        for model_name, role_assignment in roles.items():
            role_prompt = self.role_orchestrator.get_role_prompt(
                role_assignment.role, content, context
            )
            model_tasks.append(
                self._get_model_response(model_name, role_prompt, role_assignment.role)
            )
        
        # Ejecutar en paralelo con timeouts
        try:
            responses = await asyncio.wait_for(
                asyncio.gather(*model_tasks, return_exceptions=True),
                timeout=self.max_response_time
            )
            
            # Filtrar errores y fallbacks
            valid_responses = []
            for response in responses:
                if isinstance(response, ModelResponse):
                    valid_responses.append(response)
                elif isinstance(response, Exception):
                    logger.warning(f"Model response error: {response}")
                    # Usar fallback si es disponible
                    fallback_response = await self.resilience_orchestrator.get_fallback_response(
                        content, str(response)
                    )
                    if fallback_response:
                        valid_responses.append(fallback_response)
            
        except asyncio.TimeoutError:
            logger.warning("Opening statements timeout - using available responses")
            valid_responses = [r for r in responses if isinstance(r, ModelResponse)]
        
        # Calcular consenso inicial
        consensus_score = self._calculate_consensus(valid_responses)
        
        # Generar síntesis inicial
        synthesis = self._synthesize_responses(valid_responses, domain)
        
        round_duration = time.time() - round_start
        
        return DebateRound(
            round_number=1,
            topic="Opening Statements",
            responses=valid_responses,
            consensus_score=consensus_score,
            synthesis=synthesis,
            duration=round_duration
        )
    
    async def _conduct_debate_rounds(
        self,
        content: str,
        domain: str,
        roles: Dict[str, RoleAssignment],
        context: Dict[str, Any],
        rounds: List[DebateRound],
        max_rounds: int
    ) -> Tuple[str, float]:
        """Conducir rondas iterativas de debate"""
        
        current_consensus = rounds[0].consensus_score
        
        for round_num in range(2, max_rounds + 1):
            if current_consensus >= self.consensus_threshold:
                break
            
            logger.info(f"🔄 Starting debate round {round_num}")
            
            # Preparar contexto de ronda anterior
            previous_round = rounds[-1]
            debate_context = {
                "previous_responses": [
                    {
                        "model": r.model_name,
                        "role": r.role.value,
                        "position": r.content[:200] + "..." if len(r.content) > 200 else r.content
                    }
                    for r in previous_round.responses
                ],
                "current_synthesis": previous_round.synthesis,
                "consensus_score": previous_round.consensus_score
            }
            
            # Generar prompts de debate
            debate_round = await self._conduct_debate_round(
                content, domain, roles, context, debate_context, round_num
            )
            
            rounds.append(debate_round)
            current_consensus = debate_round.consensus_score
            
            logger.info(f"Round {round_num} consensus: {current_consensus:.2f}")
        
        # Retornar mejor síntesis y score
        best_round = max(rounds, key=lambda r: r.consensus_score)
        return best_round.synthesis, best_round.consensus_score
    
    async def _conduct_debate_round(
        self,
        content: str,
        domain: str,
        roles: Dict[str, RoleAssignment],
        context: Dict[str, Any],
        debate_context: Dict[str, Any],
        round_number: int
    ) -> DebateRound:
        """Conducir una ronda individual de debate"""
        
        round_start = time.time()
        responses = []
        
        # Prompts de debate iterativo
        model_tasks = []
        for model_name, role_assignment in roles.items():
            debate_prompt = self._generate_debate_prompt(
                role_assignment.role, content, context, debate_context
            )
            model_tasks.append(
                self._get_model_response(model_name, debate_prompt, role_assignment.role)
            )
        
        # Ejecutar debate round
        try:
            responses = await asyncio.wait_for(
                asyncio.gather(*model_tasks, return_exceptions=True),
                timeout=self.max_response_time
            )
            
            valid_responses = [r for r in responses if isinstance(r, ModelResponse)]
            
        except asyncio.TimeoutError:
            logger.warning(f"Round {round_number} timeout")
            valid_responses = [r for r in responses if isinstance(r, ModelResponse)]
        
        # Evaluar consenso
        consensus_score = self._calculate_consensus(valid_responses)
        synthesis = self._synthesize_responses(valid_responses, domain)
        
        round_duration = time.time() - round_start
        
        return DebateRound(
            round_number=round_number,
            topic=f"Debate Round {round_number}",
            responses=valid_responses,
            consensus_score=consensus_score,
            synthesis=synthesis,
            duration=round_duration
        )
    
    async def _get_model_response(
        self, 
        model_name: str, 
        prompt: str, 
        role: RoleType
    ) -> ModelResponse:
        """Obtener respuesta de un modelo específico"""
        
        start_time = time.time()
        
        try:
            if model_name == 'gpt-4':
                response = await self._call_gpt4(prompt)
            elif model_name == 'claude':
                response = await self._call_claude(prompt)
            elif model_name == 'gemini':
                response = await self._call_gemini(prompt)
            else:
                raise ValueError(f"Unknown model: {model_name}")
            
            response_time = time.time() - start_time
            
            return ModelResponse(
                model_name=model_name,
                role=role,
                content=response['content'],
                confidence=response.get('confidence', 0.8),
                reasoning=response.get('reasoning', ''),
                timestamp=datetime.now(),
                tokens_used=response.get('tokens', 0),
                response_time=response_time,
                cost=response.get('cost', 0.0)
            )
            
        except Exception as e:
            logger.error(f"Model {model_name} error: {e}")
            # Return fallback response
            return await self.resilience_orchestrator.get_fallback_response(
                prompt, f"{model_name} error: {str(e)}"
            )
    
    async def _call_gpt4(self, prompt: str) -> Dict[str, Any]:
        """Llamar a GPT-4"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert analyst providing detailed, structured analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            tokens = response.usage.total_tokens
            cost = tokens * 0.00003  # Estimación de costo
            
            return {
                "content": content,
                "tokens": tokens,
                "cost": cost,
                "confidence": 0.85
            }
            
        except Exception as e:
            logger.error(f"GPT-4 API error: {e}")
            raise
    
    async def _call_claude(self, prompt: str) -> Dict[str, Any]:
        """Llamar a Claude"""
        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1500,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text
            tokens = response.usage.input_tokens + response.usage.output_tokens
            cost = tokens * 0.000015  # Estimación de costo
            
            return {
                "content": content,
                "tokens": tokens,
                "cost": cost,
                "confidence": 0.82
            }
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise
    
    async def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        """Llamar a Gemini"""
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=1500,
                    temperature=0.1
                )
            )
            
            content = response.text
            tokens = len(content.split()) * 1.3  # Estimación
            cost = tokens * 0.000001  # Estimación de costo
            
            return {
                "content": content,
                "tokens": int(tokens),
                "cost": cost,
                "confidence": 0.78
            }
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def _calculate_consensus(self, responses: List[ModelResponse]) -> float:
        """Calcular score de consenso entre respuestas"""
        if len(responses) < 2:
            return 0.0
        
        # Análisis de similitud semántica simplificado
        # En producción usaríamos embeddings para comparación
        
        total_similarity = 0.0
        comparisons = 0
        
        for i in range(len(responses)):
            for j in range(i + 1, len(responses)):
                similarity = self._calculate_text_similarity(
                    responses[i].content, 
                    responses[j].content
                )
                total_similarity += similarity
                comparisons += 1
        
        consensus_score = total_similarity / comparisons if comparisons > 0 else 0.0
        
        # Ajustar por confianza promedio
        avg_confidence = sum(r.confidence for r in responses) / len(responses)
        adjusted_score = (consensus_score * 0.7) + (avg_confidence * 0.3)
        
        return min(1.0, adjusted_score)
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calcular similitud básica entre textos"""
        # Implementación simplificada - en producción usar embeddings
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if len(union) == 0:
            return 0.0
        
        jaccard_similarity = len(intersection) / len(union)
        
        # Considerar longitud similar como factor positivo
        length_similarity = 1 - abs(len(text1) - len(text2)) / max(len(text1), len(text2))
        
        return (jaccard_similarity * 0.6) + (length_similarity * 0.4)
    
    def _synthesize_responses(self, responses: List[ModelResponse], domain: str) -> str:
        """Sintetizar respuestas en una conclusión coherente"""
        if not responses:
            return "No responses available for synthesis"
        
        if len(responses) == 1:
            return responses[0].content
        
        # Síntesis ponderada por confianza
        weighted_content = []
        total_weight = sum(r.confidence for r in responses)
        
        for response in responses:
            weight = response.confidence / total_weight
            role_perspective = f"**{response.role.value.replace('_', ' ').title()} Perspective** (confidence: {response.confidence:.2f}):\n{response.content}\n"
            weighted_content.append((weight, role_perspective))
        
        # Ordenar por peso (confianza)
        weighted_content.sort(key=lambda x: x[0], reverse=True)
        
        synthesis = f"## Multi-Model Analysis Summary for {domain.title()}\n\n"
        
        for weight, content in weighted_content:
            synthesis += content + "\n"
        
        # Conclusión integrada
        highest_confidence = max(responses, key=lambda r: r.confidence)
        synthesis += f"\n## Recommended Approach\n"
        synthesis += f"Based on the multi-model analysis, the highest confidence recommendation comes from the {highest_confidence.role.value.replace('_', ' ').title()} perspective:\n\n"
        synthesis += highest_confidence.content[:500] + ("..." if len(highest_confidence.content) > 500 else "")
        
        return synthesis
    
    def _generate_debate_prompt(
        self,
        role: RoleType,
        original_content: str,
        context: Dict[str, Any],
        debate_context: Dict[str, Any]
    ) -> str:
        """Generar prompt para ronda de debate"""
        
        base_prompt = self.role_orchestrator.get_role_prompt(role, original_content, context)
        
        debate_addition = f"""

## DEBATE CONTEXT
Previous round responses:
"""
        
        for prev_response in debate_context['previous_responses']:
            debate_addition += f"- **{prev_response['role'].replace('_', ' ').title()}**: {prev_response['position']}\n"
        
        debate_addition += f"""
Current synthesis: {debate_context['current_synthesis'][:300]}...

## YOUR TASK
Review the previous responses and current synthesis. As a {role.value.replace('_', ' ').title()}, provide:

1. **Agreement/Disagreement**: What aspects do you agree or disagree with from other perspectives?
2. **Additional Insights**: What unique value does your {role.value.replace('_', ' ')} perspective add?
3. **Refinement**: How would you refine or improve the current synthesis?
4. **Final Recommendation**: Your conclusive recommendation from your specialized viewpoint.

Focus on constructive debate that leads to the best possible outcome.
"""
        
        return base_prompt + debate_addition
    
    async def _generate_final_synthesis(self, rounds: List[DebateRound], domain: str) -> str:
        """Generar síntesis final del debate completo"""
        
        # Usar GPT-4 para síntesis final
        synthesis_prompt = f"""
As a senior consultant, synthesize the following multi-round debate into a final, actionable recommendation for {domain}:

"""
        
        for round in rounds:
            synthesis_prompt += f"## Round {round.round_number}: {round.topic}\n"
            synthesis_prompt += f"Consensus Score: {round.consensus_score:.2f}\n"
            synthesis_prompt += f"Synthesis: {round.synthesis[:300]}...\n\n"
        
        synthesis_prompt += """
Provide a final synthesis that:
1. Integrates the best insights from all rounds
2. Resolves any remaining conflicts or disagreements  
3. Provides clear, actionable recommendations
4. Maintains the specialized perspectives that emerged
5. Is practical and implementable

Format as a structured executive summary with clear next steps.
"""
        
        try:
            final_synthesis = await self._call_gpt4(synthesis_prompt)
            return final_synthesis['content']
        except:
            # Fallback to best round synthesis
            best_round = max(rounds, key=lambda r: r.consensus_score)
            return best_round.synthesis
    
    def _extract_model_outputs(self, rounds: List[DebateRound]) -> Dict[str, Any]:
        """Extraer outputs de modelos para respuesta estructurada"""
        model_outputs = {}
        
        for round in rounds:
            for response in round.responses:
                if response.model_name not in model_outputs:
                    model_outputs[response.model_name] = {
                        "role": response.role.value,
                        "responses": [],
                        "total_tokens": 0,
                        "total_cost": 0.0,
                        "avg_confidence": 0.0
                    }
                
                model_outputs[response.model_name]["responses"].append({
                    "round": round.round_number,
                    "content": response.content,
                    "confidence": response.confidence,
                    "tokens": response.tokens_used,
                    "cost": response.cost
                })
                
                model_outputs[response.model_name]["total_tokens"] += response.tokens_used
                model_outputs[response.model_name]["total_cost"] += response.cost
        
        # Calcular confianza promedio
        for model_data in model_outputs.values():
            if model_data["responses"]:
                model_data["avg_confidence"] = sum(
                    r["confidence"] for r in model_data["responses"]
                ) / len(model_data["responses"])
        
        return model_outputs
    
    def _format_debate_result(self, result: DebateResult) -> Dict[str, Any]:
        """Formatear resultado del debate para respuesta API"""
        return {
            "task_id": result.task_id,
            "domain": result.domain,
            "final_result": result.final_result,
            "consensus_score": result.consensus_score,
            "quality_score": result.quality_score,
            "model_outputs": result.model_outputs,
            "rounds_conducted": len(result.rounds),
            "total_cost": result.total_cost,
            "total_tokens": result.total_tokens,
            "total_duration": result.total_duration,
            "human_intervention_required": result.human_intervention_triggered,
            "round_summaries": [
                {
                    "round": r.round_number,
                    "topic": r.topic,
                    "consensus": r.consensus_score,
                    "duration": r.duration
                }
                for r in result.rounds
            ]
        }
    
    def _generate_error_result(self, task_id: str, error_message: str) -> Dict[str, Any]:
        """Generar resultado de error"""
        return {
            "task_id": task_id,
            "error": True,
            "message": error_message,
            "final_result": f"Debate failed: {error_message}",
            "consensus_score": 0.0,
            "quality_score": 0.0,
            "total_cost": 0.0,
            "human_intervention_required": True
        }
    
    def get_debate_analytics(self) -> Dict[str, Any]:
        """Obtener analytics del sistema de debates"""
        if not self.debate_history:
            return {"message": "No debate history available"}
        
        total_debates = len(self.debate_history)
        avg_consensus = sum(d.consensus_score for d in self.debate_history) / total_debates
        avg_cost = sum(d.total_cost for d in self.debate_history) / total_debates
        avg_duration = sum(d.total_duration for d in self.debate_history) / total_debates
        
        consensus_achieved = sum(1 for d in self.debate_history if d.consensus_score >= self.consensus_threshold)
        human_interventions = sum(1 for d in self.debate_history if d.human_intervention_triggered)
        
        return {
            "total_debates": total_debates,
            "average_consensus_score": avg_consensus,
            "consensus_achievement_rate": (consensus_achieved / total_debates) * 100,
            "human_intervention_rate": (human_interventions / total_debates) * 100,
            "average_cost_per_debate": avg_cost,
            "average_duration_seconds": avg_duration,
            "cost_efficiency": avg_consensus / avg_cost if avg_cost > 0 else 0,
            "domains_analyzed": list(set(d.domain for d in self.debate_history))
        }