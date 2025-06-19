#!/usr/bin/env python3
"""
Sam's Memory Analyzer - Semantic Search System
Sistema avanzado de memoria semántica que permite a Sam aprender de su experiencia
"""

import json
import asyncio
import logging
import hashlib
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import uuid

# Imports para embeddings y análisis
try:
    import openai
    import numpy as np
    from sentence_transformers import SentenceTransformer
    import spacy
    from supabase import create_client, Client
except ImportError as e:
    print(f"Warning: Some dependencies not available: {e}")

class MemoryType(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    ESCALATION = "escalation"
    CRITICAL = "critical"
    LEARNING = "learning"

class ConceptType(Enum):
    ENTITY = "entity"
    ACTION = "action"
    PURPOSE = "purpose"
    RESULT = "result"
    ERROR = "error"
    PATTERN = "pattern"

@dataclass
class ExtractedConcept:
    type: ConceptType
    value: str
    confidence: float
    context: str

@dataclass
class Memory:
    id: str
    summary: str
    embedding: List[float]
    tags: List[str]
    memory_type: MemoryType
    concepts: List[ExtractedConcept]
    created_at: datetime
    raw_data: Dict[str, Any]
    success_score: float
    relevance_boost: float = 1.0

@dataclass
class SemanticSearchResult:
    memory: Memory
    similarity_score: float
    boosted_score: float
    relevance_reason: str

class SamMemoryAnalyzer:
    """
    Sistema principal de análisis de memoria semántica para Sam
    """
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        self.logger = self._setup_logging()
        
        # Configuración de Supabase
        self.supabase_url = supabase_url or self._get_env_var("SUPABASE_URL")
        self.supabase_key = supabase_key or self._get_env_var("SUPABASE_SERVICE_ROLE_KEY")
        self.supabase: Optional[Client] = None
        
        # Configuración de embeddings
        self.openai_client = None
        self.local_embedder = None
        self.nlp = None
        
        # Cache y configuración
        self.embedding_cache = {}
        self.concept_cache = {}
        self.similarity_threshold = 0.7
        self.max_summary_length = 500
        self.max_memories_per_search = 10
        
        # Métricas
        self.metrics = {
            "total_memories": 0,
            "successful_retrievals": 0,
            "failed_retrievals": 0,
            "cache_hits": 0,
            "embedding_calls": 0
        }
        
        # Inicializar componentes
        self._initialize_components()
    
    def _setup_logging(self) -> logging.Logger:
        """Configura logging para el memory analyzer"""
        logger = logging.getLogger("SamMemoryAnalyzer")
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler("/root/supermcp/logs/memory_analyzer.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _get_env_var(self, var_name: str) -> Optional[str]:
        """Obtiene variable de entorno"""
        import os
        return os.getenv(var_name)
    
    def _initialize_components(self):
        """Inicializa todos los componentes del sistema"""
        try:
            # Inicializar Supabase
            if self.supabase_url and self.supabase_key:
                self.supabase = create_client(self.supabase_url, self.supabase_key)
                self.logger.info("Supabase client initialized")
            else:
                self.logger.warning("Supabase credentials not found")
            
            # Inicializar OpenAI para embeddings
            openai_key = self._get_env_var("OPENAI_API_KEY")
            if openai_key:
                openai.api_key = openai_key
                self.openai_client = openai
                self.logger.info("OpenAI client initialized")
            
            # Inicializar embedder local como fallback
            try:
                self.local_embedder = SentenceTransformer('all-MiniLM-L6-v2')
                self.logger.info("Local embedder initialized")
            except Exception as e:
                self.logger.warning(f"Could not initialize local embedder: {e}")
            
            # Inicializar spaCy para NLP
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self.logger.info("spaCy NLP model loaded")
            except Exception as e:
                self.logger.warning(f"Could not load spaCy model: {e}")
                # Fallback a análisis básico
                self.nlp = None
            
            # Crear tabla de memorias si no existe
            self._ensure_memory_table()
            
        except Exception as e:
            self.logger.error(f"Error initializing components: {e}")
    
    def _ensure_memory_table(self):
        """Asegura que la tabla de memorias existe en Supabase"""
        if not self.supabase:
            return
        
        try:
            # Verificar si la tabla existe
            result = self.supabase.table('memories').select('id').limit(1).execute()
            self.logger.info("Memory table exists")
        except Exception as e:
            self.logger.warning(f"Memory table might not exist: {e}")
            # Aquí podrías crear la tabla automáticamente si tienes permisos
    
    async def summarize_and_embed(self, log_data: Dict[str, Any]) -> Optional[str]:
        """
        Pipeline principal: analiza log, extrae conceptos, genera embeddings y almacena
        """
        try:
            self.logger.info(f"Processing log for memory analysis: {log_data.get('task_id', 'unknown')}")
            
            # 1. Summarizer - Resumir si es necesario
            summary = await self._summarizer(log_data)
            
            # 2. Concept Extractor - Extraer conceptos clave
            concepts = await self._concept_extractor(log_data, summary)
            
            # 3. Embedder - Generar vector embedding
            embedding = await self._embedder(summary)
            
            if not embedding:
                self.logger.error("Failed to generate embedding")
                return None
            
            # 4. Determinar tipo de memoria y tags
            memory_type, tags = self._classify_memory(log_data, concepts)
            
            # 5. Calcular success score
            success_score = self._calculate_success_score(log_data)
            
            # 6. Crear objeto Memory
            memory = Memory(
                id=str(uuid.uuid4()),
                summary=summary,
                embedding=embedding,
                tags=tags,
                memory_type=memory_type,
                concepts=concepts,
                created_at=datetime.now(),
                raw_data=log_data,
                success_score=success_score
            )
            
            # 7. Store in Supabase
            memory_id = await self._store_in_supabase(memory)
            
            if memory_id:
                self.metrics["total_memories"] += 1
                self.logger.info(f"Memory stored successfully: {memory_id}")
                return memory_id
            else:
                self.logger.error("Failed to store memory")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in summarize_and_embed: {e}")
            return None
    
    async def _summarizer(self, log_data: Dict[str, Any]) -> str:
        """
        Genera resumen inteligente del log si excede el umbral de longitud
        """
        # Extraer texto principal
        prompt = log_data.get('input', {}).get('prompt', '')
        result = log_data.get('output', {}).get('result', {}).get('content', '')
        error = log_data.get('output', {}).get('error_message', '')
        
        full_text = f"Prompt: {prompt}\nResult: {result}\nError: {error}".strip()
        
        # Si es corto, devolver tal como está
        if len(full_text) <= self.max_summary_length:
            return full_text
        
        # Generar resumen usando LLM
        try:
            if self.openai_client:
                response = await self._openai_summarize(full_text)
                if response:
                    return response
        except Exception as e:
            self.logger.warning(f"OpenAI summarization failed: {e}")
        
        # Fallback: resumen extractivo simple
        return self._extractive_summary(full_text)
    
    async def _openai_summarize(self, text: str) -> Optional[str]:
        """Genera resumen usando OpenAI"""
        try:
            response = await self.openai_client.ChatCompletion.acreate(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Summarize the following interaction in 2-3 sentences, focusing on the task, approach, and outcome."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"OpenAI summarization error: {e}")
            return None
    
    def _extractive_summary(self, text: str) -> str:
        """Resumen extractivo simple como fallback"""
        sentences = text.split('. ')
        
        # Tomar las primeras 2 oraciones y la última
        if len(sentences) <= 3:
            return text[:self.max_summary_length]
        
        summary_parts = sentences[:2] + [sentences[-1]]
        summary = '. '.join(summary_parts)
        
        if len(summary) > self.max_summary_length:
            summary = summary[:self.max_summary_length] + "..."
        
        return summary
    
    async def _concept_extractor(self, log_data: Dict[str, Any], summary: str) -> List[ExtractedConcept]:
        """
        Extrae conceptos clave usando NLP avanzado
        """
        concepts = []
        
        try:
            # Usar spaCy si está disponible
            if self.nlp:
                concepts.extend(self._spacy_concept_extraction(summary))
            
            # Análisis específico del dominio MCP
            concepts.extend(self._domain_specific_extraction(log_data, summary))
            
            # Análisis de patrones de error
            if log_data.get('output', {}).get('error_message'):
                concepts.extend(self._error_pattern_extraction(log_data))
            
            return concepts
            
        except Exception as e:
            self.logger.error(f"Error in concept extraction: {e}")
            return []
    
    def _spacy_concept_extraction(self, text: str) -> List[ExtractedConcept]:
        """Extracción de conceptos usando spaCy"""
        concepts = []
        
        try:
            doc = self.nlp(text)
            
            # Entidades nombradas
            for ent in doc.ents:
                concepts.append(ExtractedConcept(
                    type=ConceptType.ENTITY,
                    value=ent.text,
                    confidence=0.8,
                    context=f"Entity type: {ent.label_}"
                ))
            
            # Verbos principales (acciones)
            for token in doc:
                if token.pos_ == "VERB" and not token.is_stop:
                    concepts.append(ExtractedConcept(
                        type=ConceptType.ACTION,
                        value=token.lemma_,
                        confidence=0.6,
                        context=f"Verb in context: {token.sent.text[:100]}"
                    ))
            
            return concepts
            
        except Exception as e:
            self.logger.error(f"spaCy extraction error: {e}")
            return []
    
    def _domain_specific_extraction(self, log_data: Dict[str, Any], summary: str) -> List[ExtractedConcept]:
        """Extracción específica del dominio MCP"""
        concepts = []
        
        # Detectar tipo de tarea
        task_type = log_data.get('input', {}).get('task_type', '')
        if task_type:
            concepts.append(ExtractedConcept(
                type=ConceptType.PURPOSE,
                value=f"task_type:{task_type}",
                confidence=1.0,
                context="Task classification"
            ))
        
        # Detectar modelo usado
        model_used = log_data.get('output', {}).get('result', {}).get('model_used', '')
        if model_used:
            concepts.append(ExtractedConcept(
                type=ConceptType.ENTITY,
                value=f"model:{model_used}",
                confidence=1.0,
                context="Model identification"
            ))
        
        # Detectar patrones de éxito/fallo
        status = log_data.get('output', {}).get('status', '')
        if status:
            concepts.append(ExtractedConcept(
                type=ConceptType.RESULT,
                value=f"status:{status}",
                confidence=1.0,
                context="Execution outcome"
            ))
        
        # Detectar palabras clave técnicas
        technical_keywords = [
            'coding', 'research', 'analysis', 'debugging', 'optimization',
            'deployment', 'configuration', 'integration', 'testing'
        ]
        
        text_lower = summary.lower()
        for keyword in technical_keywords:
            if keyword in text_lower:
                concepts.append(ExtractedConcept(
                    type=ConceptType.PATTERN,
                    value=f"domain:{keyword}",
                    confidence=0.7,
                    context=f"Technical domain: {keyword}"
                ))
        
        return concepts
    
    def _error_pattern_extraction(self, log_data: Dict[str, Any]) -> List[ExtractedConcept]:
        """Extrae patrones de errores para aprendizaje"""
        concepts = []
        
        error_msg = log_data.get('output', {}).get('error_message', '')
        if not error_msg:
            return concepts
        
        # Patrones comunes de error
        error_patterns = {
            'timeout': r'timeout|timed out|time limit',
            'connection': r'connection|network|unreachable',
            'authentication': r'auth|unauthorized|forbidden|401|403',
            'not_found': r'not found|404|missing|does not exist',
            'syntax': r'syntax|parse|invalid|malformed',
            'memory': r'memory|out of memory|oom',
            'permission': r'permission|access denied|privilege'
        }
        
        error_lower = error_msg.lower()
        for pattern_name, pattern_regex in error_patterns.items():
            if re.search(pattern_regex, error_lower):
                concepts.append(ExtractedConcept(
                    type=ConceptType.ERROR,
                    value=f"error_pattern:{pattern_name}",
                    confidence=0.9,
                    context=f"Error classification: {pattern_name}"
                ))
        
        return concepts
    
    async def _embedder(self, text: str) -> Optional[List[float]]:
        """
        Genera embedding del texto usando OpenAI o modelo local
        """
        # Verificar cache
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.embedding_cache:
            self.metrics["cache_hits"] += 1
            return self.embedding_cache[text_hash]
        
        embedding = None
        
        # Intentar con OpenAI primero
        try:
            if self.openai_client:
                embedding = await self._openai_embedding(text)
                if embedding:
                    self.metrics["embedding_calls"] += 1
        except Exception as e:
            self.logger.warning(f"OpenAI embedding failed: {e}")
        
        # Fallback a modelo local
        if not embedding and self.local_embedder:
            try:
                embedding = self._local_embedding(text)
                if embedding:
                    self.metrics["embedding_calls"] += 1
            except Exception as e:
                self.logger.warning(f"Local embedding failed: {e}")
        
        # Cache el resultado
        if embedding:
            self.embedding_cache[text_hash] = embedding
        
        return embedding
    
    async def _openai_embedding(self, text: str) -> Optional[List[float]]:
        """Genera embedding usando OpenAI"""
        try:
            response = await self.openai_client.Embedding.acreate(
                model="text-embedding-3-large",
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            self.logger.error(f"OpenAI embedding error: {e}")
            return None
    
    def _local_embedding(self, text: str) -> Optional[List[float]]:
        """Genera embedding usando modelo local"""
        try:
            embedding = self.local_embedder.encode(text)
            return embedding.tolist()
            
        except Exception as e:
            self.logger.error(f"Local embedding error: {e}")
            return None
    
    def _classify_memory(self, log_data: Dict[str, Any], concepts: List[ExtractedConcept]) -> Tuple[MemoryType, List[str]]:
        """Clasifica el tipo de memoria y genera tags"""
        status = log_data.get('output', {}).get('status', '')
        
        # Determinar tipo de memoria
        if status == 'success':
            memory_type = MemoryType.SUCCESS
        elif status == 'escalated':
            memory_type = MemoryType.ESCALATION
        elif status == 'error':
            memory_type = MemoryType.FAILURE
        else:
            memory_type = MemoryType.LEARNING
        
        # Generar tags
        tags = [memory_type.value]
        
        # Tags del tipo de tarea
        task_type = log_data.get('input', {}).get('task_type', '')
        if task_type:
            tags.append(f"task:{task_type}")
        
        # Tags del modelo usado
        model_used = log_data.get('output', {}).get('result', {}).get('model_used', '')
        if model_used:
            tags.append(f"model:{model_used}")
        
        # Tags de conceptos importantes
        for concept in concepts:
            if concept.confidence > 0.8:
                tags.append(f"concept:{concept.value}")
        
        # Tags de rendimiento
        execution_time = log_data.get('output', {}).get('result', {}).get('execution_time', 0)
        if execution_time > 30:
            tags.append("slow_execution")
        elif execution_time < 5:
            tags.append("fast_execution")
        
        return memory_type, tags
    
    def _calculate_success_score(self, log_data: Dict[str, Any]) -> float:
        """Calcula puntuación de éxito de la memoria"""
        status = log_data.get('output', {}).get('status', '')
        
        base_score = {
            'success': 1.0,
            'escalated': 0.3,
            'error': 0.0
        }.get(status, 0.5)
        
        # Ajustar por tiempo de ejecución
        execution_time = log_data.get('output', {}).get('result', {}).get('execution_time', 0)
        if execution_time > 0:
            # Penalizar ejecuciones muy lentas
            if execution_time > 60:
                base_score *= 0.8
            elif execution_time < 10:
                base_score *= 1.1  # Bonus por rapidez
        
        # Ajustar por costo (favorecer modelos locales)
        cost = log_data.get('output', {}).get('result', {}).get('cost', 0)
        if cost == 0:  # Modelo local
            base_score *= 1.1
        
        return min(1.0, base_score)
    
    async def _store_in_supabase(self, memory: Memory) -> Optional[str]:
        """Almacena memoria en Supabase"""
        if not self.supabase:
            self.logger.warning("Supabase not available, storing in local cache")
            return memory.id
        
        try:
            # Preparar datos para Supabase
            memory_data = {
                'id': memory.id,
                'summary': memory.summary,
                'embedding': memory.embedding,
                'tags': memory.tags,
                'memory_type': memory.memory_type.value,
                'created_at': memory.created_at.isoformat(),
                'success_score': memory.success_score,
                'raw_json': memory.raw_data,
                'concepts': [asdict(concept) for concept in memory.concepts]
            }
            
            # Insertar en Supabase
            result = self.supabase.table('memories').insert(memory_data).execute()
            
            if result.data:
                return memory.id
            else:
                self.logger.error(f"Failed to insert memory: {result}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error storing memory in Supabase: {e}")
            return None
    
    async def semantic_search(self, query: str, max_results: int = None) -> List[SemanticSearchResult]:
        """
        Búsqueda semántica en las memorias almacenadas
        """
        max_results = max_results or self.max_memories_per_search
        
        try:
            self.logger.info(f"Performing semantic search for: {query[:100]}...")
            
            # 1. Generar embedding del query
            query_embedding = await self._embedder(query)
            if not query_embedding:
                self.logger.error("Failed to generate query embedding")
                return []
            
            # 2. Buscar en Supabase usando vector similarity
            memories = await self._vector_search(query_embedding, max_results * 2)  # Obtener más para filtrar
            
            # 3. Calcular scores y aplicar boosting
            results = []
            for memory_data in memories:
                memory = self._memory_from_data(memory_data)
                if not memory:
                    continue
                
                # Calcular similarity score
                similarity = self._cosine_similarity(query_embedding, memory.embedding)
                
                # Aplicar boosting
                boosted_score = self._apply_boosting(similarity, memory, query)
                
                # Generar razón de relevancia
                relevance_reason = self._generate_relevance_reason(memory, query, similarity)
                
                if similarity >= self.similarity_threshold:
                    results.append(SemanticSearchResult(
                        memory=memory,
                        similarity_score=similarity,
                        boosted_score=boosted_score,
                        relevance_reason=relevance_reason
                    ))
            
            # 4. Ordenar por boosted score y limitar resultados
            results.sort(key=lambda x: x.boosted_score, reverse=True)
            results = results[:max_results]
            
            self.metrics["successful_retrievals"] += 1
            self.logger.info(f"Found {len(results)} relevant memories")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in semantic search: {e}")
            self.metrics["failed_retrievals"] += 1
            return []
    
    async def _vector_search(self, query_embedding: List[float], limit: int) -> List[Dict[str, Any]]:
        """Búsqueda vectorial en Supabase"""
        if not self.supabase:
            return []
        
        try:
            # Usar función de búsqueda vectorial de Supabase
            result = self.supabase.rpc(
                'match_memories',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': self.similarity_threshold,
                    'match_count': limit
                }
            ).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            self.logger.error(f"Vector search error: {e}")
            # Fallback: búsqueda simple
            result = self.supabase.table('memories').select('*').limit(limit).execute()
            return result.data if result.data else []
    
    def _memory_from_data(self, data: Dict[str, Any]) -> Optional[Memory]:
        """Convierte datos de Supabase a objeto Memory"""
        try:
            concepts = []
            if data.get('concepts'):
                for concept_data in data['concepts']:
                    concepts.append(ExtractedConcept(
                        type=ConceptType(concept_data['type']),
                        value=concept_data['value'],
                        confidence=concept_data['confidence'],
                        context=concept_data['context']
                    ))
            
            return Memory(
                id=data['id'],
                summary=data['summary'],
                embedding=data['embedding'],
                tags=data['tags'],
                memory_type=MemoryType(data['memory_type']),
                concepts=concepts,
                created_at=datetime.fromisoformat(data['created_at']),
                raw_data=data['raw_json'],
                success_score=data['success_score']
            )
            
        except Exception as e:
            self.logger.error(f"Error converting memory data: {e}")
            return None
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcula similitud coseno entre dos vectores"""
        try:
            import numpy as np
            
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception as e:
            self.logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def _apply_boosting(self, similarity: float, memory: Memory, query: str) -> float:
        """Aplica boosting basado en tags y características de la memoria"""
        boosted_score = similarity
        
        # Boost por tipo de memoria
        if memory.memory_type == MemoryType.SUCCESS:
            boosted_score *= 1.2
        elif memory.memory_type == MemoryType.CRITICAL:
            boosted_score *= 1.3
        elif memory.memory_type == MemoryType.FAILURE:
            boosted_score *= 1.1  # Los fallos también son valiosos para aprender
        
        # Boost por success score
        boosted_score *= (0.8 + 0.4 * memory.success_score)
        
        # Boost por recencia (memorias más recientes son más relevantes)
        days_old = (datetime.now() - memory.created_at).days
        if days_old < 7:
            boosted_score *= 1.1
        elif days_old > 30:
            boosted_score *= 0.9
        
        # Boost por coincidencia de tags con query
        query_lower = query.lower()
        for tag in memory.tags:
            if tag.lower() in query_lower:
                boosted_score *= 1.15
        
        return min(1.0, boosted_score)
    
    def _generate_relevance_reason(self, memory: Memory, query: str, similarity: float) -> str:
        """Genera explicación de por qué la memoria es relevante"""
        reasons = []
        
        # Razón por similitud
        if similarity > 0.9:
            reasons.append("Very high semantic similarity")
        elif similarity > 0.8:
            reasons.append("High semantic similarity")
        else:
            reasons.append("Moderate semantic similarity")
        
        # Razón por tipo de memoria
        if memory.memory_type == MemoryType.SUCCESS:
            reasons.append("successful execution pattern")
        elif memory.memory_type == MemoryType.FAILURE:
            reasons.append("failure pattern to avoid")
        
        # Razón por tags coincidentes
        query_lower = query.lower()
        matching_tags = [tag for tag in memory.tags if tag.lower() in query_lower]
        if matching_tags:
            reasons.append(f"matching tags: {', '.join(matching_tags[:3])}")
        
        # Razón por conceptos
        relevant_concepts = [c.value for c in memory.concepts if c.confidence > 0.8]
        if relevant_concepts:
            reasons.append(f"relevant concepts: {', '.join(relevant_concepts[:2])}")
        
        return "; ".join(reasons)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema de memoria"""
        return {
            "metrics": self.metrics,
            "cache_size": len(self.embedding_cache),
            "similarity_threshold": self.similarity_threshold,
            "max_memories_per_search": self.max_memories_per_search,
            "components_status": {
                "supabase": self.supabase is not None,
                "openai": self.openai_client is not None,
                "local_embedder": self.local_embedder is not None,
                "nlp": self.nlp is not None
            }
        }
    
    async def cleanup_old_memories(self, days_old: int = 90):
        """Limpia memorias antiguas para mantener el rendimiento"""
        if not self.supabase:
            return
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            result = self.supabase.table('memories').delete().lt(
                'created_at', cutoff_date.isoformat()
            ).execute()
            
            if result.data:
                self.logger.info(f"Cleaned up {len(result.data)} old memories")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up memories: {e}")

# Instancia global del memory analyzer
memory_analyzer = SamMemoryAnalyzer()

# Funciones de conveniencia
async def analyze_and_store_memory(log_data: Dict[str, Any]) -> Optional[str]:
    """Función de conveniencia para analizar y almacenar memoria"""
    return await memory_analyzer.summarize_and_embed(log_data)

async def search_relevant_memories(query: str, max_results: int = 5) -> List[SemanticSearchResult]:
    """Función de conveniencia para búsqueda semántica"""
    return await memory_analyzer.semantic_search(query, max_results)

def get_memory_system_stats() -> Dict[str, Any]:
    """Función de conveniencia para obtener estadísticas"""
    return memory_analyzer.get_memory_stats()

if __name__ == "__main__":
    # Test del sistema
    async def test_memory_analyzer():
        print("=== SAM'S MEMORY ANALYZER TEST ===")
        
        # Test de análisis de memoria
        test_log = {
            "task_id": "test-123",
            "input": {
                "task_type": "coding",
                "prompt": "Write a Python function to calculate fibonacci numbers"
            },
            "output": {
                "status": "success",
                "result": {
                    "content": "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
                    "model_used": "qwen2.5-coder:7b",
                    "execution_time": 5.2,
                    "cost": 0.0
                }
            }
        }
        
        # Analizar y almacenar
        memory_id = await analyze_and_store_memory(test_log)
        print(f"Memory stored: {memory_id}")
        
        # Búsqueda semántica
        results = await search_relevant_memories("fibonacci function python")
        print(f"Found {len(results)} relevant memories")
        
        for result in results:
            print(f"- {result.memory.summary[:100]}... (score: {result.similarity_score:.3f})")
        
        # Estadísticas
        stats = get_memory_system_stats()
        print(f"System stats: {json.dumps(stats, indent=2)}")
    
    # Ejecutar test
    asyncio.run(test_memory_analyzer())

