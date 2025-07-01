#!/usr/bin/env python3
"""
Training Loop Hardcore - Sistema de Aprendizaje Continuo para Sam
Captura inputs/outputs exitosos y fallidos, reentrena embeddings y afina instrucciones
"""

import asyncio
import json
import logging
import hashlib
import pickle
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, Counter
import uuid
import os
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor

# Imports para ML y reentrenamiento
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support
    from sentence_transformers import SentenceTransformer, losses, InputExample
    from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
    import openai
except ImportError as e:
    print(f"Warning: ML dependencies not available: {e}")

class TrainingDataType(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    ESCALATION = "escalation"
    OPTIMIZATION = "optimization"

class LearningObjective(Enum):
    EMBEDDING_IMPROVEMENT = "embedding_improvement"
    INSTRUCTION_OPTIMIZATION = "instruction_optimization"
    PATTERN_RECOGNITION = "pattern_recognition"
    ERROR_PREVENTION = "error_prevention"

@dataclass
class TrainingExample:
    id: str
    input_text: str
    output_text: str
    success_score: float
    execution_time: float
    model_used: str
    task_type: str
    error_message: Optional[str]
    context: Dict[str, Any]
    timestamp: datetime
    data_type: TrainingDataType
    embedding_input: Optional[List[float]] = None
    embedding_output: Optional[List[float]] = None

@dataclass
class InstructionPattern:
    pattern_id: str
    instruction_template: str
    success_rate: float
    avg_execution_time: float
    usage_count: int
    task_types: Set[str]
    last_updated: datetime
    examples: List[str]

@dataclass
class TrainingMetrics:
    total_examples: int
    success_examples: int
    failure_examples: int
    avg_success_score: float
    embedding_improvement: float
    instruction_optimization_gain: float
    last_training_time: datetime
    training_iterations: int

class HardcoreTrainingLoop:
    """
    Sistema de entrenamiento continuo hardcore para Sam
    """
    
    def __init__(self, db_path: str = "/root/supermcp/data/training_loop.db"):
        self.logger = self._setup_logging()
        self.db_path = db_path
        self.training_data: List[TrainingExample] = []
        self.instruction_patterns: Dict[str, InstructionPattern] = {}
        
        # Configuración de entrenamiento
        self.min_examples_for_training = 50
        self.training_batch_size = 32
        self.embedding_model_path = "/root/supermcp/models/sam_embeddings"
        self.instruction_db_path = "/root/supermcp/data/instructions.json"
        
        # Modelos y optimizadores
        self.embedding_model = None
        self.instruction_optimizer = None
        
        # Métricas
        self.metrics = TrainingMetrics(
            total_examples=0,
            success_examples=0,
            failure_examples=0,
            avg_success_score=0.0,
            embedding_improvement=0.0,
            instruction_optimization_gain=0.0,
            last_training_time=datetime.now(),
            training_iterations=0
        )
        
        # Threading para entrenamiento asíncrono
        self.training_executor = ThreadPoolExecutor(max_workers=2)
        self.training_lock = threading.Lock()
        self.is_training = False
        
        # Inicializar sistema
        self._initialize_system()
    
    def _setup_logging(self) -> logging.Logger:
        """Configura logging para el training loop"""
        logger = logging.getLogger("HardcoreTrainingLoop")
        logger.setLevel(logging.INFO)
        
        os.makedirs("/root/supermcp/logs", exist_ok=True)
        handler = logging.FileHandler("/root/supermcp/logs/training_loop.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _initialize_system(self):
        """Inicializa el sistema de entrenamiento"""
        try:
            # Crear directorios necesarios
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            os.makedirs(os.path.dirname(self.embedding_model_path), exist_ok=True)
            
            # Inicializar base de datos
            self._init_database()
            
            # Cargar datos existentes
            self._load_training_data()
            self._load_instruction_patterns()
            
            # Inicializar modelos
            self._initialize_models()
            
            self.logger.info("Training loop system initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing training system: {e}")
    
    def _init_database(self):
        """Inicializa la base de datos SQLite para almacenar datos de entrenamiento"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabla de ejemplos de entrenamiento
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS training_examples (
                    id TEXT PRIMARY KEY,
                    input_text TEXT NOT NULL,
                    output_text TEXT NOT NULL,
                    success_score REAL NOT NULL,
                    execution_time REAL NOT NULL,
                    model_used TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    error_message TEXT,
                    context TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    embedding_input BLOB,
                    embedding_output BLOB
                )
            ''')
            
            # Tabla de patrones de instrucciones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS instruction_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    instruction_template TEXT NOT NULL,
                    success_rate REAL NOT NULL,
                    avg_execution_time REAL NOT NULL,
                    usage_count INTEGER NOT NULL,
                    task_types TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    examples TEXT NOT NULL
                )
            ''')
            
            # Tabla de métricas de entrenamiento
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS training_metrics (
                    id INTEGER PRIMARY KEY,
                    total_examples INTEGER,
                    success_examples INTEGER,
                    failure_examples INTEGER,
                    avg_success_score REAL,
                    embedding_improvement REAL,
                    instruction_optimization_gain REAL,
                    last_training_time TEXT,
                    training_iterations INTEGER,
                    timestamp TEXT
                )
            ''')
            
            conn.commit()
    
    def _load_training_data(self):
        """Carga datos de entrenamiento desde la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM training_examples ORDER BY timestamp DESC LIMIT 1000')
                
                for row in cursor.fetchall():
                    example = TrainingExample(
                        id=row[0],
                        input_text=row[1],
                        output_text=row[2],
                        success_score=row[3],
                        execution_time=row[4],
                        model_used=row[5],
                        task_type=row[6],
                        error_message=row[7],
                        context=json.loads(row[8]),
                        timestamp=datetime.fromisoformat(row[9]),
                        data_type=TrainingDataType(row[10]),
                        embedding_input=pickle.loads(row[11]) if row[11] else None,
                        embedding_output=pickle.loads(row[12]) if row[12] else None
                    )
                    self.training_data.append(example)
                
                self.logger.info(f"Loaded {len(self.training_data)} training examples")
                
        except Exception as e:
            self.logger.error(f"Error loading training data: {e}")
    
    def _load_instruction_patterns(self):
        """Carga patrones de instrucciones desde la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM instruction_patterns')
                
                for row in cursor.fetchall():
                    pattern = InstructionPattern(
                        pattern_id=row[0],
                        instruction_template=row[1],
                        success_rate=row[2],
                        avg_execution_time=row[3],
                        usage_count=row[4],
                        task_types=set(json.loads(row[5])),
                        last_updated=datetime.fromisoformat(row[6]),
                        examples=json.loads(row[7])
                    )
                    self.instruction_patterns[pattern.pattern_id] = pattern
                
                self.logger.info(f"Loaded {len(self.instruction_patterns)} instruction patterns")
                
        except Exception as e:
            self.logger.error(f"Error loading instruction patterns: {e}")
    
    def _initialize_models(self):
        """Inicializa modelos para entrenamiento"""
        try:
            # Inicializar modelo de embeddings
            if os.path.exists(self.embedding_model_path):
                self.embedding_model = SentenceTransformer(self.embedding_model_path)
                self.logger.info("Loaded existing embedding model")
            else:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                self.logger.info("Initialized new embedding model")
            
            # Inicializar optimizador de instrucciones
            self.instruction_optimizer = InstructionOptimizer()
            
        except Exception as e:
            self.logger.error(f"Error initializing models: {e}")
    
    async def capture_training_example(
        self, 
        input_data: Dict[str, Any], 
        output_data: Dict[str, Any],
        execution_context: Dict[str, Any]
    ) -> str:
        """
        Captura un ejemplo de entrenamiento de una ejecución de Sam
        """
        try:
            # Extraer información clave
            input_text = input_data.get('prompt', '')
            output_text = output_data.get('result', {}).get('content', '')
            success_score = self._calculate_success_score(output_data)
            execution_time = output_data.get('result', {}).get('execution_time', 0.0)
            model_used = output_data.get('result', {}).get('model_used', 'unknown')
            task_type = input_data.get('task_type', 'unknown')
            error_message = output_data.get('error_message')
            
            # Determinar tipo de datos
            data_type = self._classify_training_data(output_data, success_score)
            
            # Generar embeddings
            embedding_input = await self._generate_embedding(input_text)
            embedding_output = await self._generate_embedding(output_text) if output_text else None
            
            # Crear ejemplo de entrenamiento
            example = TrainingExample(
                id=str(uuid.uuid4()),
                input_text=input_text,
                output_text=output_text,
                success_score=success_score,
                execution_time=execution_time,
                model_used=model_used,
                task_type=task_type,
                error_message=error_message,
                context=execution_context,
                timestamp=datetime.now(),
                data_type=data_type,
                embedding_input=embedding_input,
                embedding_output=embedding_output
            )
            
            # Almacenar ejemplo
            await self._store_training_example(example)
            
            # Actualizar métricas
            self._update_metrics(example)
            
            # Verificar si es momento de entrenar
            if self._should_trigger_training():
                asyncio.create_task(self._trigger_training())
            
            self.logger.info(f"Captured training example: {example.id} ({data_type.value})")
            return example.id
            
        except Exception as e:
            self.logger.error(f"Error capturing training example: {e}")
            return None
    
    def _calculate_success_score(self, output_data: Dict[str, Any]) -> float:
        """Calcula puntuación de éxito basada en el output"""
        status = output_data.get('status', '')
        
        base_score = {
            'success': 1.0,
            'escalated': 0.3,
            'error': 0.0
        }.get(status, 0.5)
        
        # Ajustar por tiempo de ejecución
        execution_time = output_data.get('result', {}).get('execution_time', 0)
        if execution_time > 0:
            if execution_time > 60:
                base_score *= 0.8
            elif execution_time < 10:
                base_score *= 1.1
        
        # Ajustar por costo
        cost = output_data.get('result', {}).get('cost', 0)
        if cost == 0:  # Modelo local
            base_score *= 1.1
        
        return min(1.0, base_score)
    
    def _classify_training_data(self, output_data: Dict[str, Any], success_score: float) -> TrainingDataType:
        """Clasifica el tipo de datos de entrenamiento"""
        status = output_data.get('status', '')
        
        if status == 'success' and success_score > 0.8:
            return TrainingDataType.SUCCESS
        elif status == 'escalated':
            return TrainingDataType.ESCALATION
        elif status == 'error' or success_score < 0.3:
            return TrainingDataType.FAILURE
        else:
            return TrainingDataType.OPTIMIZATION
    
    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Genera embedding para el texto"""
        try:
            if self.embedding_model and text:
                embedding = self.embedding_model.encode(text)
                return embedding.tolist()
            return None
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            return None
    
    async def _store_training_example(self, example: TrainingExample):
        """Almacena ejemplo en la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO training_examples 
                    (id, input_text, output_text, success_score, execution_time, 
                     model_used, task_type, error_message, context, timestamp, 
                     data_type, embedding_input, embedding_output)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    example.id,
                    example.input_text,
                    example.output_text,
                    example.success_score,
                    example.execution_time,
                    example.model_used,
                    example.task_type,
                    example.error_message,
                    json.dumps(example.context),
                    example.timestamp.isoformat(),
                    example.data_type.value,
                    pickle.dumps(example.embedding_input) if example.embedding_input else None,
                    pickle.dumps(example.embedding_output) if example.embedding_output else None
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error storing training example: {e}")
    
    def _update_metrics(self, example: TrainingExample):
        """Actualiza métricas con nuevo ejemplo"""
        self.metrics.total_examples += 1
        
        if example.data_type == TrainingDataType.SUCCESS:
            self.metrics.success_examples += 1
        elif example.data_type == TrainingDataType.FAILURE:
            self.metrics.failure_examples += 1
        
        # Recalcular promedio de success score
        total_score = self.metrics.avg_success_score * (self.metrics.total_examples - 1)
        self.metrics.avg_success_score = (total_score + example.success_score) / self.metrics.total_examples
    
    def _should_trigger_training(self) -> bool:
        """Determina si es momento de entrenar"""
        if self.is_training:
            return False
        
        # Entrenar cada 50 ejemplos nuevos
        if len(self.training_data) >= self.min_examples_for_training:
            if len(self.training_data) % 50 == 0:
                return True
        
        # Entrenar si hay muchos fallos recientes
        recent_examples = [ex for ex in self.training_data[-20:] if ex.data_type == TrainingDataType.FAILURE]
        if len(recent_examples) > 10:
            return True
        
        return False
    
    async def _trigger_training(self):
        """Dispara el proceso de entrenamiento"""
        if self.is_training:
            return
        
        with self.training_lock:
            if self.is_training:
                return
            self.is_training = True
        
        try:
            self.logger.info("Starting hardcore training session...")
            
            # Entrenar embeddings
            embedding_improvement = await self._train_embeddings()
            
            # Optimizar instrucciones
            instruction_improvement = await self._optimize_instructions()
            
            # Actualizar métricas
            self.metrics.embedding_improvement = embedding_improvement
            self.metrics.instruction_optimization_gain = instruction_improvement
            self.metrics.last_training_time = datetime.now()
            self.metrics.training_iterations += 1
            
            # Guardar métricas
            await self._save_metrics()
            
            self.logger.info(f"Training completed - Embedding: +{embedding_improvement:.3f}, Instructions: +{instruction_improvement:.3f}")
            
        except Exception as e:
            self.logger.error(f"Error in training session: {e}")
        finally:
            self.is_training = False
    
    async def _train_embeddings(self) -> float:
        """Entrena y mejora el modelo de embeddings"""
        try:
            if not self.embedding_model or len(self.training_data) < self.min_examples_for_training:
                return 0.0
            
            # Preparar datos de entrenamiento
            training_examples = []
            
            # Crear pares positivos (input-output exitosos)
            success_examples = [ex for ex in self.training_data if ex.data_type == TrainingDataType.SUCCESS]
            for example in success_examples[-100:]:  # Últimos 100 éxitos
                if example.output_text:
                    training_examples.append(InputExample(
                        texts=[example.input_text, example.output_text],
                        label=example.success_score
                    ))
            
            # Crear pares negativos (input-error)
            failure_examples = [ex for ex in self.training_data if ex.data_type == TrainingDataType.FAILURE]
            for example in failure_examples[-50:]:  # Últimos 50 fallos
                if example.error_message:
                    training_examples.append(InputExample(
                        texts=[example.input_text, f"ERROR: {example.error_message}"],
                        label=0.0
                    ))
            
            if len(training_examples) < 10:
                return 0.0
            
            # Dividir en train/test
            train_examples, test_examples = train_test_split(training_examples, test_size=0.2, random_state=42)
            
            # Configurar entrenamiento
            train_dataloader = torch.utils.data.DataLoader(train_examples, shuffle=True, batch_size=16)
            train_loss = losses.CosineSimilarityLoss(self.embedding_model)
            
            # Evaluador
            evaluator = EmbeddingSimilarityEvaluator.from_input_examples(test_examples, name='test')
            
            # Entrenar
            initial_score = evaluator(self.embedding_model)
            
            self.embedding_model.fit(
                train_objectives=[(train_dataloader, train_loss)],
                evaluator=evaluator,
                epochs=3,
                warmup_steps=100,
                output_path=self.embedding_model_path
            )
            
            final_score = evaluator(self.embedding_model)
            improvement = final_score - initial_score
            
            self.logger.info(f"Embedding training completed - Improvement: {improvement:.3f}")
            return improvement
            
        except Exception as e:
            self.logger.error(f"Error training embeddings: {e}")
            return 0.0
    
    async def _optimize_instructions(self) -> float:
        """Optimiza patrones de instrucciones basado en resultados"""
        try:
            if not self.instruction_optimizer:
                return 0.0
            
            # Analizar patrones exitosos vs fallidos
            success_patterns = self._extract_instruction_patterns(TrainingDataType.SUCCESS)
            failure_patterns = self._extract_instruction_patterns(TrainingDataType.FAILURE)
            
            # Optimizar patrones existentes
            improvement = 0.0
            for pattern_id, pattern in self.instruction_patterns.items():
                old_success_rate = pattern.success_rate
                
                # Actualizar patrón basado en nuevos datos
                updated_pattern = self.instruction_optimizer.optimize_pattern(
                    pattern, success_patterns, failure_patterns
                )
                
                if updated_pattern:
                    self.instruction_patterns[pattern_id] = updated_pattern
                    improvement += updated_pattern.success_rate - old_success_rate
            
            # Crear nuevos patrones prometedores
            new_patterns = self.instruction_optimizer.discover_new_patterns(
                success_patterns, self.instruction_patterns
            )
            
            for new_pattern in new_patterns:
                self.instruction_patterns[new_pattern.pattern_id] = new_pattern
                improvement += new_pattern.success_rate
            
            # Guardar patrones actualizados
            await self._save_instruction_patterns()
            
            self.logger.info(f"Instruction optimization completed - Improvement: {improvement:.3f}")
            return improvement
            
        except Exception as e:
            self.logger.error(f"Error optimizing instructions: {e}")
            return 0.0
    
    def _extract_instruction_patterns(self, data_type: TrainingDataType) -> List[Dict[str, Any]]:
        """Extrae patrones de instrucciones de los datos de entrenamiento"""
        patterns = []
        
        examples = [ex for ex in self.training_data if ex.data_type == data_type]
        
        for example in examples[-100:]:  # Últimos 100 ejemplos
            pattern = {
                'input': example.input_text,
                'output': example.output_text,
                'task_type': example.task_type,
                'model_used': example.model_used,
                'success_score': example.success_score,
                'execution_time': example.execution_time,
                'context': example.context
            }
            patterns.append(pattern)
        
        return patterns
    
    async def _save_instruction_patterns(self):
        """Guarda patrones de instrucciones en la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Limpiar tabla existente
                cursor.execute('DELETE FROM instruction_patterns')
                
                # Insertar patrones actualizados
                for pattern in self.instruction_patterns.values():
                    cursor.execute('''
                        INSERT INTO instruction_patterns 
                        (pattern_id, instruction_template, success_rate, avg_execution_time,
                         usage_count, task_types, last_updated, examples)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        pattern.pattern_id,
                        pattern.instruction_template,
                        pattern.success_rate,
                        pattern.avg_execution_time,
                        pattern.usage_count,
                        json.dumps(list(pattern.task_types)),
                        pattern.last_updated.isoformat(),
                        json.dumps(pattern.examples)
                    ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error saving instruction patterns: {e}")
    
    async def _save_metrics(self):
        """Guarda métricas de entrenamiento"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO training_metrics 
                    (total_examples, success_examples, failure_examples, avg_success_score,
                     embedding_improvement, instruction_optimization_gain, last_training_time,
                     training_iterations, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self.metrics.total_examples,
                    self.metrics.success_examples,
                    self.metrics.failure_examples,
                    self.metrics.avg_success_score,
                    self.metrics.embedding_improvement,
                    self.metrics.instruction_optimization_gain,
                    self.metrics.last_training_time.isoformat(),
                    self.metrics.training_iterations,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error saving metrics: {e}")
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema de entrenamiento"""
        return {
            "metrics": asdict(self.metrics),
            "training_data_count": len(self.training_data),
            "instruction_patterns_count": len(self.instruction_patterns),
            "is_training": self.is_training,
            "recent_examples": [
                {
                    "id": ex.id,
                    "task_type": ex.task_type,
                    "data_type": ex.data_type.value,
                    "success_score": ex.success_score,
                    "timestamp": ex.timestamp.isoformat()
                }
                for ex in self.training_data[-10:]
            ],
            "top_instruction_patterns": [
                {
                    "pattern_id": pattern.pattern_id,
                    "success_rate": pattern.success_rate,
                    "usage_count": pattern.usage_count,
                    "task_types": list(pattern.task_types)
                }
                for pattern in sorted(
                    self.instruction_patterns.values(),
                    key=lambda p: p.success_rate,
                    reverse=True
                )[:5]
            ]
        }
    
    async def get_optimized_instruction(self, task_type: str, context: Dict[str, Any]) -> Optional[str]:
        """Obtiene instrucción optimizada para un tipo de tarea"""
        try:
            # Buscar patrón más exitoso para el tipo de tarea
            best_pattern = None
            best_score = 0.0
            
            for pattern in self.instruction_patterns.values():
                if task_type in pattern.task_types and pattern.success_rate > best_score:
                    best_pattern = pattern
                    best_score = pattern.success_rate
            
            if best_pattern:
                # Personalizar instrucción basada en contexto
                instruction = self.instruction_optimizer.personalize_instruction(
                    best_pattern.instruction_template, context
                )
                
                # Actualizar uso del patrón
                best_pattern.usage_count += 1
                best_pattern.last_updated = datetime.now()
                
                return instruction
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting optimized instruction: {e}")
            return None

class InstructionOptimizer:
    """
    Optimizador de instrucciones basado en patrones de éxito/fallo
    """
    
    def __init__(self):
        self.logger = logging.getLogger("InstructionOptimizer")
    
    def optimize_pattern(
        self, 
        pattern: InstructionPattern, 
        success_patterns: List[Dict[str, Any]], 
        failure_patterns: List[Dict[str, Any]]
    ) -> Optional[InstructionPattern]:
        """Optimiza un patrón existente basado en nuevos datos"""
        try:
            # Analizar qué funciona y qué no
            success_keywords = self._extract_keywords(success_patterns)
            failure_keywords = self._extract_keywords(failure_patterns)
            
            # Identificar palabras clave exitosas no presentes en el patrón
            missing_success_keywords = success_keywords - set(pattern.instruction_template.lower().split())
            
            # Identificar palabras clave problemáticas presentes en el patrón
            problematic_keywords = failure_keywords & set(pattern.instruction_template.lower().split())
            
            # Optimizar template
            optimized_template = pattern.instruction_template
            
            # Añadir palabras clave exitosas
            for keyword in list(missing_success_keywords)[:3]:  # Top 3
                if keyword not in optimized_template.lower():
                    optimized_template += f" Consider {keyword}."
            
            # Remover o modificar palabras problemáticas
            for keyword in problematic_keywords:
                if keyword in optimized_template.lower():
                    optimized_template = optimized_template.replace(keyword, f"avoid_{keyword}")
            
            # Calcular nueva success rate
            new_success_rate = self._estimate_success_rate(optimized_template, success_patterns, failure_patterns)
            
            if new_success_rate > pattern.success_rate:
                return InstructionPattern(
                    pattern_id=pattern.pattern_id,
                    instruction_template=optimized_template,
                    success_rate=new_success_rate,
                    avg_execution_time=pattern.avg_execution_time,
                    usage_count=pattern.usage_count,
                    task_types=pattern.task_types,
                    last_updated=datetime.now(),
                    examples=pattern.examples
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error optimizing pattern: {e}")
            return None
    
    def discover_new_patterns(
        self, 
        success_patterns: List[Dict[str, Any]], 
        existing_patterns: Dict[str, InstructionPattern]
    ) -> List[InstructionPattern]:
        """Descubre nuevos patrones prometedores"""
        new_patterns = []
        
        try:
            # Agrupar por tipo de tarea
            task_groups = defaultdict(list)
            for pattern in success_patterns:
                task_groups[pattern['task_type']].append(pattern)
            
            for task_type, patterns in task_groups.items():
                if len(patterns) < 5:  # Necesitamos suficientes ejemplos
                    continue
                
                # Extraer características comunes
                common_keywords = self._find_common_keywords(patterns)
                common_structures = self._find_common_structures(patterns)
                
                # Crear nuevo patrón si es prometedor
                if common_keywords and len(common_keywords) >= 3:
                    template = self._generate_template(common_keywords, common_structures)
                    
                    # Verificar que no sea muy similar a patrones existentes
                    if not self._is_similar_to_existing(template, existing_patterns):
                        new_pattern = InstructionPattern(
                            pattern_id=f"auto_{task_type}_{len(existing_patterns)}",
                            instruction_template=template,
                            success_rate=0.8,  # Estimación inicial
                            avg_execution_time=sum(p['execution_time'] for p in patterns) / len(patterns),
                            usage_count=0,
                            task_types={task_type},
                            last_updated=datetime.now(),
                            examples=[p['input'][:100] for p in patterns[:3]]
                        )
                        new_patterns.append(new_pattern)
            
        except Exception as e:
            self.logger.error(f"Error discovering new patterns: {e}")
        
        return new_patterns
    
    def personalize_instruction(self, template: str, context: Dict[str, Any]) -> str:
        """Personaliza una instrucción basada en el contexto"""
        try:
            personalized = template
            
            # Añadir contexto específico
            if 'domain' in context:
                personalized += f" Focus on {context['domain']} domain."
            
            if 'priority' in context:
                if context['priority'] == 'high':
                    personalized += " Prioritize speed and efficiency."
                elif context['priority'] == 'low':
                    personalized += " Take time to ensure quality."
            
            if 'model_preference' in context:
                personalized += f" Use {context['model_preference']} approach."
            
            return personalized
            
        except Exception as e:
            self.logger.error(f"Error personalizing instruction: {e}")
            return template
    
    def _extract_keywords(self, patterns: List[Dict[str, Any]]) -> Set[str]:
        """Extrae palabras clave de los patrones"""
        keywords = set()
        
        for pattern in patterns:
            text = f"{pattern['input']} {pattern['output']}"
            words = text.lower().split()
            
            # Filtrar palabras relevantes (más de 3 caracteres, no stopwords)
            relevant_words = [
                word for word in words 
                if len(word) > 3 and word.isalpha() and word not in {
                    'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'she', 'use', 'way', 'will', 'with'
                }
            ]
            
            keywords.update(relevant_words)
        
        return keywords
    
    def _find_common_keywords(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """Encuentra palabras clave comunes en patrones exitosos"""
        word_counts = Counter()
        
        for pattern in patterns:
            text = f"{pattern['input']} {pattern['output']}"
            words = text.lower().split()
            word_counts.update(words)
        
        # Retornar palabras que aparecen en al menos 50% de los patrones
        threshold = len(patterns) * 0.5
        common_words = [word for word, count in word_counts.items() if count >= threshold and len(word) > 3]
        
        return common_words[:10]  # Top 10
    
    def _find_common_structures(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """Encuentra estructuras comunes en los patrones"""
        structures = []
        
        # Analizar longitud promedio
        avg_length = sum(len(p['input'].split()) for p in patterns) / len(patterns)
        if avg_length < 10:
            structures.append("concise")
        elif avg_length > 30:
            structures.append("detailed")
        
        # Analizar presencia de preguntas
        question_count = sum(1 for p in patterns if '?' in p['input'])
        if question_count > len(patterns) * 0.5:
            structures.append("interrogative")
        
        # Analizar presencia de comandos
        command_words = ['create', 'build', 'make', 'generate', 'write', 'develop']
        command_count = sum(1 for p in patterns if any(cmd in p['input'].lower() for cmd in command_words))
        if command_count > len(patterns) * 0.5:
            structures.append("imperative")
        
        return structures
    
    def _generate_template(self, keywords: List[str], structures: List[str]) -> str:
        """Genera un template basado en palabras clave y estructuras"""
        template_parts = []
        
        # Estructura base
        if "imperative" in structures:
            template_parts.append("Please")
        
        # Añadir palabras clave principales
        if keywords:
            template_parts.append(f"focus on {', '.join(keywords[:3])}")
        
        # Añadir modificadores de estructura
        if "concise" in structures:
            template_parts.append("Be concise and direct.")
        elif "detailed" in structures:
            template_parts.append("Provide detailed explanation.")
        
        if "interrogative" in structures:
            template_parts.append("Consider relevant questions.")
        
        return " ".join(template_parts)
    
    def _is_similar_to_existing(self, template: str, existing_patterns: Dict[str, InstructionPattern]) -> bool:
        """Verifica si un template es muy similar a patrones existentes"""
        template_words = set(template.lower().split())
        
        for pattern in existing_patterns.values():
            pattern_words = set(pattern.instruction_template.lower().split())
            
            # Calcular similitud Jaccard
            intersection = len(template_words & pattern_words)
            union = len(template_words | pattern_words)
            
            if union > 0:
                similarity = intersection / union
                if similarity > 0.7:  # 70% de similitud
                    return True
        
        return False
    
    def _estimate_success_rate(
        self, 
        template: str, 
        success_patterns: List[Dict[str, Any]], 
        failure_patterns: List[Dict[str, Any]]
    ) -> float:
        """Estima la tasa de éxito de un template"""
        template_words = set(template.lower().split())
        
        # Calcular similitud con patrones exitosos
        success_similarity = 0.0
        for pattern in success_patterns:
            pattern_words = set(f"{pattern['input']} {pattern['output']}".lower().split())
            intersection = len(template_words & pattern_words)
            union = len(template_words | pattern_words)
            if union > 0:
                success_similarity += intersection / union
        
        if success_patterns:
            success_similarity /= len(success_patterns)
        
        # Calcular similitud con patrones fallidos
        failure_similarity = 0.0
        for pattern in failure_patterns:
            pattern_words = set(f"{pattern['input']} {pattern['output']}".lower().split())
            intersection = len(template_words & pattern_words)
            union = len(template_words | pattern_words)
            if union > 0:
                failure_similarity += intersection / union
        
        if failure_patterns:
            failure_similarity /= len(failure_patterns)
        
        # Estimar success rate
        if success_similarity > failure_similarity:
            return min(0.95, 0.5 + success_similarity - failure_similarity)
        else:
            return max(0.1, 0.5 - (failure_similarity - success_similarity))

# Instancia global del training loop
hardcore_training_loop = HardcoreTrainingLoop()

# Funciones de conveniencia
async def capture_sam_execution(input_data: Dict[str, Any], output_data: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Función de conveniencia para capturar ejecución de Sam"""
    return await hardcore_training_loop.capture_training_example(input_data, output_data, context)

async def get_optimized_instruction_for_task(task_type: str, context: Dict[str, Any]) -> Optional[str]:
    """Función de conveniencia para obtener instrucción optimizada"""
    return await hardcore_training_loop.get_optimized_instruction(task_type, context)

def get_training_loop_stats() -> Dict[str, Any]:
    """Función de conveniencia para obtener estadísticas"""
    return hardcore_training_loop.get_training_stats()

if __name__ == "__main__":
    # Test del training loop
    async def test_training_loop():
        print("=== HARDCORE TRAINING LOOP TEST ===")
        
        # Simular captura de datos
        test_input = {
            "task_type": "coding",
            "prompt": "Write a Python function to sort a list efficiently"
        }
        
        test_output = {
            "status": "success",
            "result": {
                "content": "def sort_list(lst): return sorted(lst)",
                "model_used": "qwen2.5-coder:7b",
                "execution_time": 3.2,
                "cost": 0.0
            }
        }
        
        test_context = {
            "domain": "sam.chat",
            "priority": "medium"
        }
        
        # Capturar ejemplo
        example_id = await capture_sam_execution(test_input, test_output, test_context)
        print(f"Captured example: {example_id}")
        
        # Obtener instrucción optimizada
        optimized = await get_optimized_instruction_for_task("coding", test_context)
        print(f"Optimized instruction: {optimized}")
        
        # Estadísticas
        stats = get_training_loop_stats()
        print(f"Training stats: {json.dumps(stats, indent=2)}")
    
    # Ejecutar test
    asyncio.run(test_training_loop())

