"""
Shadow Learning Engine para Chain-of-Debate SuperMCP

Sistema de aprendizaje continuo que captura decisiones reales del sistema
y retroalimenta automáticamente para mejorar la calidad de futuros debates.

Funcionalidades:
- Captura automática de decisiones originales vs finales
- Recolección de intervenciones humanas y feedback
- Análisis de patrones de mejora
- Trigger automático de retraining
- Validación de mejoras en calidad

Pipeline de Mejora:
1. Captura de decisiones y outcomes
2. Análisis de diferencias humano vs modelo
3. Generación de datasets de entrenamiento
4. Trigger de retraining cuando threshold alcanzado
5. Validación A/B de mejoras
"""

import asyncio
import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import pickle
import hashlib
from collections import defaultdict, deque

# Para embeddings y análisis semántico
import openai
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)

class InterventionType(Enum):
    """Tipos de intervención humana"""
    APPROVAL = "approval"
    MODIFICATION = "modification"
    REJECTION = "rejection"
    ESCALATION = "escalation"

class OutcomeType(Enum):
    """Tipos de outcome final"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    UNKNOWN = "unknown"

@dataclass
class ShadowLearningEvent:
    """Evento de aprendizaje capturado"""
    event_id: str
    task_id: str
    domain: str
    original_input: str
    model_outputs: Dict[str, Any]
    human_intervention: Optional[Dict[str, Any]]
    final_decision: str
    client_feedback: Optional[str]
    outcome_success: Optional[bool]
    outcome_metrics: Dict[str, float]
    context_factors: Dict[str, Any]
    timestamp: datetime
    embedding: Optional[List[float]] = None

@dataclass
class LearningPattern:
    """Patrón de aprendizaje identificado"""
    pattern_id: str
    pattern_type: str
    description: str
    confidence: float
    examples: List[str]
    improvement_suggestions: List[str]
    frequency: int

@dataclass
class RetrainingTrigger:
    """Trigger para reentrenamiento automático"""
    trigger_id: str
    domain: str
    threshold_met: bool
    data_points_available: int
    quality_improvement_potential: float
    suggested_improvements: List[str]
    created_at: datetime

class ShadowLearningEngine:
    """
    Motor de aprendizaje sombra que mejora el sistema automáticamente
    """
    
    def __init__(self):
        self.learning_events = deque(maxlen=10000)  # Últimos 10k eventos
        self.learning_patterns = {}
        self.retraining_triggers = []
        
        # Configuración de aprendizaje
        self.min_events_for_pattern = 50
        self.retraining_threshold = 100  # Eventos con intervención
        self.quality_improvement_threshold = 0.15  # 15% mejora mínima
        
        # Análisis semántico
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.embeddings_cache = {}
        
        # Métricas de mejora
        self.improvement_metrics = {
            "total_learning_events": 0,
            "human_interventions": 0,
            "quality_improvements_detected": 0,
            "retraining_cycles": 0,
            "avg_quality_improvement": 0.0
        }
        
        logger.info("🧠 Shadow Learning Engine initialized")
    
    async def log_debate_outcome(
        self,
        task_id: str,
        input_content: str,
        domain: str,
        model_outputs: Dict[str, Any],
        final_result: str,
        consensus_score: float,
        context: Dict[str, Any] = None
    ):
        """Log outcome de debate sin intervención humana"""
        
        event = ShadowLearningEvent(
            event_id=f"debate_{task_id}_{int(datetime.now().timestamp())}",
            task_id=task_id,
            domain=domain,
            original_input=input_content,
            model_outputs=model_outputs,
            human_intervention=None,
            final_decision=final_result,
            client_feedback=None,
            outcome_success=consensus_score > 0.7,
            outcome_metrics={"consensus_score": consensus_score},
            context_factors=context or {},
            timestamp=datetime.now()
        )
        
        # Generar embedding para análisis semántico
        event.embedding = await self._generate_embedding(input_content)
        
        self.learning_events.append(event)
        self.improvement_metrics["total_learning_events"] += 1
        
        # Análisis de patrones en background
        asyncio.create_task(self._analyze_patterns_async())
        
        logger.debug(f"📊 Logged debate outcome: {task_id}")
    
    async def log_human_intervention(
        self,
        task_id: str,
        original_result: Dict[str, Any],
        human_action: str,
        final_result: str,
        context: Dict[str, Any] = None
    ):
        """Log intervención humana para aprendizaje"""
        
        intervention_data = {
            "type": human_action,
            "original_models_result": original_result,
            "human_final_result": final_result,
            "intervention_time": datetime.now().isoformat(),
            "context": context or {}
        }
        
        # Buscar evento original
        original_event = None
        for event in reversed(self.learning_events):
            if event.task_id == task_id:
                original_event = event
                break
        
        if original_event:
            # Actualizar evento con intervención
            original_event.human_intervention = intervention_data
            original_event.final_decision = final_result
            
            # Calcular mejora de calidad
            quality_improvement = await self._calculate_quality_improvement(
                original_event.model_outputs,
                final_result,
                original_event.original_input
            )
            
            original_event.outcome_metrics["quality_improvement"] = quality_improvement
            
            self.improvement_metrics["human_interventions"] += 1
            
            if quality_improvement > self.quality_improvement_threshold:
                self.improvement_metrics["quality_improvements_detected"] += 1
                self.improvement_metrics["avg_quality_improvement"] = (
                    (self.improvement_metrics["avg_quality_improvement"] * 
                     (self.improvement_metrics["quality_improvements_detected"] - 1) + 
                     quality_improvement) / 
                    self.improvement_metrics["quality_improvements_detected"]
                )
            
            # Check para retraining trigger
            await self._check_retraining_trigger(original_event.domain)
            
            logger.info(f"👤 Logged human intervention: {task_id} (improvement: {quality_improvement:.2f})")
        
        else:
            logger.warning(f"Original event not found for task: {task_id}")
    
    async def log_client_feedback(
        self,
        task_id: str,
        feedback: str,
        satisfaction_score: float,
        outcome_success: bool
    ):
        """Log feedback del cliente sobre el resultado"""
        
        # Buscar evento
        for event in reversed(self.learning_events):
            if event.task_id == task_id:
                event.client_feedback = feedback
                event.outcome_success = outcome_success
                event.outcome_metrics.update({
                    "client_satisfaction": satisfaction_score,
                    "outcome_success": outcome_success
                })
                
                logger.info(f"💬 Client feedback logged: {task_id} (satisfaction: {satisfaction_score})")
                return
        
        logger.warning(f"Event not found for client feedback: {task_id}")
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generar embedding para análisis semántico"""
        
        # Cache para evitar regenerar embeddings
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.embeddings_cache:
            return self.embeddings_cache[text_hash]
        
        try:
            # Usar OpenAI embeddings
            client = openai.AsyncOpenAI()
            response = await client.embeddings.create(
                model="text-embedding-ada-002",
                input=text[:8000]  # Limitar longitud
            )
            
            embedding = response.data[0].embedding
            self.embeddings_cache[text_hash] = embedding
            
            # Limitar cache
            if len(self.embeddings_cache) > 5000:
                # Remover 20% más antiguos
                keys_to_remove = list(self.embeddings_cache.keys())[:1000]
                for key in keys_to_remove:
                    del self.embeddings_cache[key]
            
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            # Fallback a TF-IDF
            try:
                tfidf_matrix = self.vectorizer.fit_transform([text])
                return tfidf_matrix.toarray()[0].tolist()
            except:
                return [0.0] * 1536  # Embedding vacío
    
    async def _calculate_quality_improvement(
        self,
        original_outputs: Dict[str, Any],
        final_result: str,
        input_content: str
    ) -> float:
        """Calcular mejora de calidad después de intervención humana"""
        
        try:
            # Obtener embeddings
            input_embedding = await self._generate_embedding(input_content)
            final_embedding = await self._generate_embedding(final_result)
            
            # Calcular relevancia semántica
            relevance_score = cosine_similarity(
                [input_embedding], 
                [final_embedding]
            )[0][0]
            
            # Calcular coherencia (longitud apropiada, estructura)
            coherence_score = self._calculate_coherence_score(final_result)
            
            # Comparar con output original de mejor modelo
            best_original = max(
                original_outputs.values(),
                key=lambda x: x.get('confidence', 0),
                default={}
            )
            
            if best_original:
                original_content = best_original.get('content', '')
                original_embedding = await self._generate_embedding(original_content)
                
                # Mejora relativa
                original_relevance = cosine_similarity(
                    [input_embedding], 
                    [original_embedding]
                )[0][0]
                
                relative_improvement = (relevance_score - original_relevance) / max(original_relevance, 0.1)
                
                # Score compuesto
                quality_improvement = (
                    relative_improvement * 0.4 +
                    coherence_score * 0.3 +
                    relevance_score * 0.3
                )
                
                return max(0.0, min(1.0, quality_improvement))
            
            return relevance_score * coherence_score
            
        except Exception as e:
            logger.error(f"Quality calculation error: {e}")
            return 0.0
    
    def _calculate_coherence_score(self, text: str) -> float:
        """Calcular score de coherencia del texto"""
        
        # Métricas básicas de calidad
        words = text.split()
        sentences = text.split('.')
        
        # Longitud apropiada
        length_score = 1.0 if 50 <= len(words) <= 500 else 0.7
        
        # Estructura de párrafos
        paragraphs = text.split('\n\n')
        structure_score = 1.0 if 1 <= len(paragraphs) <= 5 else 0.8
        
        # Presencia de conectores lógicos
        connectors = ['however', 'therefore', 'moreover', 'furthermore', 'additionally']
        connector_score = min(1.0, sum(1 for c in connectors if c in text.lower()) / 10)
        
        # Repetición excesiva
        word_variety = len(set(words)) / len(words) if words else 0
        variety_score = min(1.0, word_variety * 2)
        
        return (length_score * 0.3 + structure_score * 0.2 + 
                connector_score * 0.2 + variety_score * 0.3)
    
    async def _analyze_patterns_async(self):
        """Análisis de patrones en background"""
        try:
            if len(self.learning_events) < self.min_events_for_pattern:
                return
            
            # Análisis por dominio
            domain_events = defaultdict(list)
            for event in self.learning_events:
                domain_events[event.domain].append(event)
            
            for domain, events in domain_events.items():
                if len(events) >= self.min_events_for_pattern:
                    patterns = await self._identify_domain_patterns(domain, events)
                    self.learning_patterns[domain] = patterns
            
        except Exception as e:
            logger.error(f"Pattern analysis error: {e}")
    
    async def _identify_domain_patterns(
        self, 
        domain: str, 
        events: List[ShadowLearningEvent]
    ) -> List[LearningPattern]:
        """Identificar patrones específicos por dominio"""
        
        patterns = []
        
        # Patrón 1: Intervenciones frecuentes en tipo de contenido
        intervention_events = [e for e in events if e.human_intervention]
        
        if len(intervention_events) >= 10:
            # Clustering de inputs similares con intervenciones
            intervention_embeddings = [e.embedding for e in intervention_events if e.embedding]
            
            if len(intervention_embeddings) >= 5:
                # Análisis de clustering simple
                similarity_clusters = self._simple_clustering(intervention_embeddings, threshold=0.8)
                
                for cluster in similarity_clusters:
                    if len(cluster) >= 3:  # Patrón significativo
                        cluster_events = [intervention_events[i] for i in cluster]
                        
                        # Extraer patrón común
                        common_issues = self._extract_common_issues(cluster_events)
                        
                        pattern = LearningPattern(
                            pattern_id=f"{domain}_intervention_{len(patterns)}",
                            pattern_type="frequent_intervention",
                            description=f"Frequent human intervention needed for {common_issues}",
                            confidence=len(cluster) / len(intervention_events),
                            examples=[e.original_input[:100] for e in cluster_events[:3]],
                            improvement_suggestions=self._generate_improvement_suggestions(cluster_events),
                            frequency=len(cluster)
                        )
                        
                        patterns.append(pattern)
        
        # Patrón 2: Baja calidad consistente en ciertos tipos de requests
        low_quality_events = [
            e for e in events 
            if e.outcome_metrics.get('consensus_score', 1.0) < 0.6
        ]
        
        if len(low_quality_events) >= 5:
            pattern = LearningPattern(
                pattern_id=f"{domain}_low_quality",
                pattern_type="consistent_low_quality",
                description=f"Consistently low quality outputs in {domain}",
                confidence=len(low_quality_events) / len(events),
                examples=[e.original_input[:100] for e in low_quality_events[:3]],
                improvement_suggestions=[
                    "Refine role assignments for this domain",
                    "Add domain-specific context prompts",
                    "Increase consensus threshold requirements"
                ],
                frequency=len(low_quality_events)
            )
            
            patterns.append(pattern)
        
        # Patrón 3: Mejoras exitosas recurrentes
        improved_events = [
            e for e in events 
            if e.outcome_metrics.get('quality_improvement', 0) > self.quality_improvement_threshold
        ]
        
        if len(improved_events) >= 3:
            improvement_types = self._categorize_improvements(improved_events)
            
            for improvement_type, type_events in improvement_types.items():
                if len(type_events) >= 2:
                    pattern = LearningPattern(
                        pattern_id=f"{domain}_improvement_{improvement_type}",
                        pattern_type="successful_improvement",
                        description=f"Successful improvements via {improvement_type} in {domain}",
                        confidence=len(type_events) / len(improved_events),
                        examples=[e.original_input[:100] for e in type_events[:2]],
                        improvement_suggestions=self._extract_improvement_techniques(type_events),
                        frequency=len(type_events)
                    )
                    
                    patterns.append(pattern)
        
        return patterns
    
    def _simple_clustering(
        self, 
        embeddings: List[List[float]], 
        threshold: float = 0.8
    ) -> List[List[int]]:
        """Clustering simple basado en similitud coseno"""
        
        if not embeddings:
            return []
        
        embeddings_array = np.array(embeddings)
        similarity_matrix = cosine_similarity(embeddings_array)
        
        clusters = []
        used_indices = set()
        
        for i in range(len(embeddings)):
            if i in used_indices:
                continue
            
            cluster = [i]
            used_indices.add(i)
            
            for j in range(i + 1, len(embeddings)):
                if j in used_indices:
                    continue
                
                if similarity_matrix[i][j] >= threshold:
                    cluster.append(j)
                    used_indices.add(j)
            
            if len(cluster) > 1:
                clusters.append(cluster)
        
        return clusters
    
    def _extract_common_issues(self, events: List[ShadowLearningEvent]) -> str:
        """Extraer issues comunes de eventos similares"""
        
        # Análisis de palabras clave en interventions
        intervention_texts = []
        for event in events:
            if event.human_intervention:
                human_result = event.human_intervention.get('human_final_result', '')
                intervention_texts.append(human_result)
        
        if intervention_texts:
            # TF-IDF para encontrar términos importantes
            try:
                tfidf = TfidfVectorizer(max_features=10, stop_words='english')
                tfidf_matrix = tfidf.fit_transform(intervention_texts)
                feature_names = tfidf.get_feature_names_out()
                
                # Top términos
                top_terms = feature_names[:5]
                return f"content involving {', '.join(top_terms)}"
            except:
                pass
        
        return "similar content types"
    
    def _generate_improvement_suggestions(
        self, 
        events: List[ShadowLearningEvent]
    ) -> List[str]:
        """Generar sugerencias de mejora basadas en patrones"""
        
        suggestions = []
        
        # Análisis de tipos de intervención
        intervention_types = defaultdict(int)
        for event in events:
            if event.human_intervention:
                intervention_type = event.human_intervention.get('type', 'unknown')
                intervention_types[intervention_type] += 1
        
        most_common_intervention = max(intervention_types.items(), key=lambda x: x[1])[0]
        
        if most_common_intervention == 'modification':
            suggestions.extend([
                "Improve initial model prompts for this content type",
                "Add more specific role context for better initial outputs",
                "Increase consensus threshold to catch quality issues early"
            ])
        elif most_common_intervention == 'rejection':
            suggestions.extend([
                "Review role assignments for this domain",
                "Add domain-specific validation criteria",
                "Implement pre-filtering for problematic content patterns"
            ])
        
        # Análisis de mejoras de calidad
        quality_improvements = [
            e.outcome_metrics.get('quality_improvement', 0) 
            for e in events
        ]
        avg_improvement = sum(quality_improvements) / len(quality_improvements)
        
        if avg_improvement > 0.3:
            suggestions.append("High improvement potential - prioritize this pattern for retraining")
        
        return suggestions[:3]  # Top 3 sugerencias
    
    def _categorize_improvements(
        self, 
        events: List[ShadowLearningEvent]
    ) -> Dict[str, List[ShadowLearningEvent]]:
        """Categorizar tipos de mejoras exitosas"""
        
        categories = defaultdict(list)
        
        for event in events:
            if not event.human_intervention:
                continue
            
            intervention_type = event.human_intervention.get('type', 'unknown')
            quality_improvement = event.outcome_metrics.get('quality_improvement', 0)
            
            if quality_improvement > 0.3:
                categories['major_improvement'].append(event)
            elif quality_improvement > 0.15:
                categories['moderate_improvement'].append(event)
            
            if intervention_type == 'modification':
                categories['content_refinement'].append(event)
            elif intervention_type == 'rejection':
                categories['approach_change'].append(event)
        
        return categories
    
    def _extract_improvement_techniques(
        self, 
        events: List[ShadowLearningEvent]
    ) -> List[str]:
        """Extraer técnicas de mejora exitosas"""
        
        techniques = []
        
        for event in events:
            if event.human_intervention:
                original_content = event.model_outputs
                final_content = event.human_intervention.get('human_final_result', '')
                
                # Análisis de diferencias
                if len(final_content) > len(str(original_content)):
                    techniques.append("Add more detailed explanations")
                
                if 'specific' in final_content.lower() and 'specific' not in str(original_content).lower():
                    techniques.append("Include more specific examples and details")
                
                if final_content.count('\n') > str(original_content).count('\n'):
                    techniques.append("Improve content structure and formatting")
        
        return list(set(techniques))[:3]
    
    async def _check_retraining_trigger(self, domain: str):
        """Verificar si se debe trigger retraining para un dominio"""
        
        # Contar eventos con intervención en último período
        cutoff_date = datetime.now() - timedelta(days=30)
        recent_events = [
            e for e in self.learning_events
            if e.domain == domain and e.timestamp >= cutoff_date
        ]
        
        intervention_events = [e for e in recent_events if e.human_intervention]
        
        if len(intervention_events) >= self.retraining_threshold:
            # Calcular potencial de mejora
            quality_improvements = [
                e.outcome_metrics.get('quality_improvement', 0)
                for e in intervention_events
            ]
            
            avg_improvement = sum(quality_improvements) / len(quality_improvements)
            
            if avg_improvement >= self.quality_improvement_threshold:
                trigger = RetrainingTrigger(
                    trigger_id=f"retrain_{domain}_{int(datetime.now().timestamp())}",
                    domain=domain,
                    threshold_met=True,
                    data_points_available=len(intervention_events),
                    quality_improvement_potential=avg_improvement,
                    suggested_improvements=self._generate_retraining_suggestions(intervention_events),
                    created_at=datetime.now()
                )
                
                self.retraining_triggers.append(trigger)
                self.improvement_metrics["retraining_cycles"] += 1
                
                logger.info(f"🚀 Retraining trigger activated for {domain} (potential: {avg_improvement:.2f})")
                
                # Notificación async para sistema de retraining
                asyncio.create_task(self._notify_retraining_system(trigger))
    
    def _generate_retraining_suggestions(
        self, 
        events: List[ShadowLearningEvent]
    ) -> List[str]:
        """Generar sugerencias específicas para retraining"""
        
        suggestions = []
        
        # Análisis de patrones de mejora
        common_improvements = defaultdict(int)
        
        for event in events:
            if event.human_intervention:
                # Analizar tipo de cambios hechos
                original = str(event.model_outputs)
                final = event.human_intervention.get('human_final_result', '')
                
                if len(final) > len(original) * 1.5:
                    common_improvements['expand_detail'] += 1
                
                if 'structure' in final.lower() or final.count('\n') > original.count('\n'):
                    common_improvements['improve_structure'] += 1
                
                if any(word in final.lower() for word in ['specific', 'example', 'detail']):
                    common_improvements['add_specificity'] += 1
        
        # Convertir a sugerencias
        for improvement_type, count in common_improvements.items():
            if count >= len(events) * 0.3:  # 30% de eventos
                if improvement_type == 'expand_detail':
                    suggestions.append("Train models to provide more comprehensive detail")
                elif improvement_type == 'improve_structure':
                    suggestions.append("Improve output structure and formatting")
                elif improvement_type == 'add_specificity':
                    suggestions.append("Train for more specific examples and concrete details")
        
        return suggestions
    
    async def _notify_retraining_system(self, trigger: RetrainingTrigger):
        """Notificar al sistema de retraining (placeholder)"""
        # En producción, esto triggearía el sistema de retraining automático
        logger.info(f"📧 Retraining notification sent for {trigger.domain}")
        
        # Placeholder para integración con sistema de retraining
        # await retraining_system.schedule_retraining(trigger)
    
    def get_learning_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del sistema de aprendizaje"""
        
        if not self.learning_events:
            return {"message": "No learning data available"}
        
        # Métricas básicas
        total_events = len(self.learning_events)
        intervention_events = sum(1 for e in self.learning_events if e.human_intervention)
        successful_outcomes = sum(1 for e in self.learning_events if e.outcome_success)
        
        # Métricas por dominio
        domain_metrics = defaultdict(lambda: {
            "total_events": 0,
            "interventions": 0,
            "avg_quality": 0.0,
            "success_rate": 0.0
        })
        
        for event in self.learning_events:
            domain = event.domain
            domain_metrics[domain]["total_events"] += 1
            
            if event.human_intervention:
                domain_metrics[domain]["interventions"] += 1
            
            if event.outcome_success:
                domain_metrics[domain]["success_rate"] += 1
            
            consensus_score = event.outcome_metrics.get('consensus_score', 0)
            domain_metrics[domain]["avg_quality"] += consensus_score
        
        # Calcular promedios
        for domain_data in domain_metrics.values():
            if domain_data["total_events"] > 0:
                domain_data["avg_quality"] /= domain_data["total_events"]
                domain_data["success_rate"] /= domain_data["total_events"]
                domain_data["intervention_rate"] = domain_data["interventions"] / domain_data["total_events"]
        
        # Tendencias recientes
        recent_events = [
            e for e in self.learning_events 
            if e.timestamp >= datetime.now() - timedelta(days=7)
        ]
        
        recent_intervention_rate = (
            sum(1 for e in recent_events if e.human_intervention) / len(recent_events)
            if recent_events else 0
        )
        
        return {
            **self.improvement_metrics,
            "total_events": total_events,
            "intervention_rate": intervention_events / total_events * 100 if total_events > 0 else 0,
            "success_rate": successful_outcomes / total_events * 100 if total_events > 0 else 0,
            "recent_intervention_rate": recent_intervention_rate * 100,
            "domain_metrics": dict(domain_metrics),
            "active_patterns": len(self.learning_patterns),
            "pending_retraining_triggers": len([t for t in self.retraining_triggers if t.threshold_met]),
            "learning_efficiency": self._calculate_learning_efficiency(),
            "data_quality_score": self._calculate_data_quality_score()
        }
    
    def _calculate_learning_efficiency(self) -> float:
        """Calcular eficiencia del aprendizaje"""
        
        if not self.learning_events:
            return 0.0
        
        # Eventos con outcome conocido
        events_with_outcome = [e for e in self.learning_events if e.outcome_success is not None]
        
        if not events_with_outcome:
            return 0.0
        
        # Tendencia de mejora a lo largo del tiempo
        events_by_time = sorted(events_with_outcome, key=lambda e: e.timestamp)
        
        if len(events_by_time) < 10:
            return 0.5  # Datos insuficientes
        
        # Comparar primeras vs últimas 10% de decisiones
        early_events = events_by_time[:len(events_by_time)//10]
        recent_events = events_by_time[-len(events_by_time)//10:]
        
        early_success_rate = sum(1 for e in early_events if e.outcome_success) / len(early_events)
        recent_success_rate = sum(1 for e in recent_events if e.outcome_success) / len(recent_events)
        
        improvement = recent_success_rate - early_success_rate
        
        # Normalizar a 0-1
        return max(0.0, min(1.0, 0.5 + improvement))
    
    def _calculate_data_quality_score(self) -> float:
        """Calcular calidad de los datos de aprendizaje"""
        
        if not self.learning_events:
            return 0.0
        
        quality_factors = []
        
        # Factor 1: Completitud de datos
        complete_events = sum(
            1 for e in self.learning_events 
            if e.outcome_success is not None and e.embedding is not None
        )
        completeness = complete_events / len(self.learning_events)
        quality_factors.append(completeness)
        
        # Factor 2: Diversidad de dominios
        domains = set(e.domain for e in self.learning_events)
        domain_diversity = min(1.0, len(domains) / 5)  # Máximo 5 dominios
        quality_factors.append(domain_diversity)
        
        # Factor 3: Balance de outcomes
        positive_outcomes = sum(1 for e in self.learning_events if e.outcome_success)
        outcome_balance = min(positive_outcomes, len(self.learning_events) - positive_outcomes) / len(self.learning_events)
        quality_factors.append(outcome_balance * 2)  # Multiplicar por 2 para normalizar
        
        # Factor 4: Frecuencia de feedback
        events_with_feedback = sum(1 for e in self.learning_events if e.client_feedback)
        feedback_rate = events_with_feedback / len(self.learning_events)
        quality_factors.append(feedback_rate)
        
        return sum(quality_factors) / len(quality_factors)
    
    def get_retraining_status(self) -> Dict[str, Any]:
        """Obtener estado de triggers de retraining"""
        
        active_triggers = [t for t in self.retraining_triggers if t.threshold_met]
        
        return {
            "total_triggers": len(self.retraining_triggers),
            "active_triggers": len(active_triggers),
            "triggers_by_domain": {
                trigger.domain: {
                    "data_points": trigger.data_points_available,
                    "improvement_potential": trigger.quality_improvement_potential,
                    "suggestions": trigger.suggested_improvements,
                    "created_at": trigger.created_at.isoformat()
                }
                for trigger in active_triggers
            },
            "next_recommended_domain": active_triggers[0].domain if active_triggers else None
        }