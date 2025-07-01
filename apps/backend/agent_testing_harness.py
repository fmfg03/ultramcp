#!/usr/bin/env python3
"""
Agent Testing Harness - Sistema de Validación de Performance
Simula tareas batch (10-20 por tipo) para validar latencia, precisión y edge cases
"""

import asyncio
import json
import logging
import time
import statistics
import random
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import uuid
import sqlite3
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Imports para testing y análisis
try:
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    from scipy import stats
    import pandas as pd
except ImportError as e:
    print(f"Warning: Analysis dependencies not available: {e}")

class TestType(Enum):
    PERFORMANCE = "performance"
    STRESS = "stress"
    EDGE_CASE = "edge_case"
    REGRESSION = "regression"
    LOAD = "load"

class TaskCategory(Enum):
    CODING = "coding"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    REASONING = "reasoning"
    BATCH = "batch"

class TestResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    TIMEOUT = "timeout"
    ERROR = "error"
    PARTIAL = "partial"

@dataclass
class TestCase:
    id: str
    name: str
    category: TaskCategory
    test_type: TestType
    input_data: Dict[str, Any]
    expected_output: Optional[Dict[str, Any]]
    timeout_seconds: int
    difficulty_level: int  # 1-10
    edge_case_type: Optional[str]
    description: str

@dataclass
class TestExecution:
    test_case_id: str
    execution_id: str
    start_time: datetime
    end_time: Optional[datetime]
    execution_time: float
    result: TestResult
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    model_used: str
    memory_usage: float
    cpu_usage: float
    success_score: float
    confidence_score: float

@dataclass
class PerformanceMetrics:
    total_tests: int
    passed_tests: int
    failed_tests: int
    avg_execution_time: float
    median_execution_time: float
    p95_execution_time: float
    success_rate: float
    avg_success_score: float
    timeout_rate: float
    error_rate: float
    blind_spots: List[str]

@dataclass
class BlindSpot:
    category: str
    description: str
    failure_rate: float
    examples: List[str]
    severity: str  # low, medium, high, critical

class AgentTestingHarness:
    """
    Sistema de testing hardcore para validar performance de Sam
    """
    
    def __init__(self, db_path: str = "/root/supermcp/data/testing_harness.db"):
        self.logger = self._setup_logging()
        self.db_path = db_path
        
        # Configuración de testing
        self.default_timeout = 60
        self.max_concurrent_tests = 5
        self.stress_test_multiplier = 3
        
        # Test cases y resultados
        self.test_cases: Dict[str, TestCase] = {}
        self.test_executions: List[TestExecution] = []
        self.performance_history: List[PerformanceMetrics] = []
        
        # Threading para tests concurrentes
        self.test_executor = ThreadPoolExecutor(max_workers=self.max_concurrent_tests)
        self.test_lock = threading.Lock()
        
        # Inicializar sistema
        self._initialize_system()
        self._load_default_test_cases()
    
    def _setup_logging(self) -> logging.Logger:
        """Configura logging para el testing harness"""
        logger = logging.getLogger("AgentTestingHarness")
        logger.setLevel(logging.INFO)
        
        os.makedirs("/root/supermcp/logs", exist_ok=True)
        handler = logging.FileHandler("/root/supermcp/logs/testing_harness.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _initialize_system(self):
        """Inicializa el sistema de testing"""
        try:
            # Crear directorios necesarios
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            os.makedirs("/root/supermcp/test_reports", exist_ok=True)
            
            # Inicializar base de datos
            self._init_database()
            
            # Cargar datos existentes
            self._load_test_data()
            
            self.logger.info("Testing harness initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing testing system: {e}")
    
    def _init_database(self):
        """Inicializa la base de datos SQLite para testing"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabla de test cases
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_cases (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    test_type TEXT NOT NULL,
                    input_data TEXT NOT NULL,
                    expected_output TEXT,
                    timeout_seconds INTEGER NOT NULL,
                    difficulty_level INTEGER NOT NULL,
                    edge_case_type TEXT,
                    description TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
            
            # Tabla de ejecuciones de tests
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_executions (
                    execution_id TEXT PRIMARY KEY,
                    test_case_id TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    execution_time REAL NOT NULL,
                    result TEXT NOT NULL,
                    output_data TEXT,
                    error_message TEXT,
                    model_used TEXT NOT NULL,
                    memory_usage REAL NOT NULL,
                    cpu_usage REAL NOT NULL,
                    success_score REAL NOT NULL,
                    confidence_score REAL NOT NULL,
                    FOREIGN KEY (test_case_id) REFERENCES test_cases (id)
                )
            ''')
            
            # Tabla de métricas de performance
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_tests INTEGER NOT NULL,
                    passed_tests INTEGER NOT NULL,
                    failed_tests INTEGER NOT NULL,
                    avg_execution_time REAL NOT NULL,
                    median_execution_time REAL NOT NULL,
                    p95_execution_time REAL NOT NULL,
                    success_rate REAL NOT NULL,
                    avg_success_score REAL NOT NULL,
                    timeout_rate REAL NOT NULL,
                    error_rate REAL NOT NULL,
                    blind_spots TEXT NOT NULL
                )
            ''')
            
            conn.commit()
    
    def _load_test_data(self):
        """Carga datos de testing desde la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Cargar test cases
                cursor.execute('SELECT * FROM test_cases')
                for row in cursor.fetchall():
                    test_case = TestCase(
                        id=row[0],
                        name=row[1],
                        category=TaskCategory(row[2]),
                        test_type=TestType(row[3]),
                        input_data=json.loads(row[4]),
                        expected_output=json.loads(row[5]) if row[5] else None,
                        timeout_seconds=row[6],
                        difficulty_level=row[7],
                        edge_case_type=row[8],
                        description=row[9]
                    )
                    self.test_cases[test_case.id] = test_case
                
                # Cargar ejecuciones recientes
                cursor.execute('SELECT * FROM test_executions ORDER BY start_time DESC LIMIT 1000')
                for row in cursor.fetchall():
                    execution = TestExecution(
                        test_case_id=row[1],
                        execution_id=row[0],
                        start_time=datetime.fromisoformat(row[2]),
                        end_time=datetime.fromisoformat(row[3]) if row[3] else None,
                        execution_time=row[4],
                        result=TestResult(row[5]),
                        output_data=json.loads(row[6]) if row[6] else None,
                        error_message=row[7],
                        model_used=row[8],
                        memory_usage=row[9],
                        cpu_usage=row[10],
                        success_score=row[11],
                        confidence_score=row[12]
                    )
                    self.test_executions.append(execution)
                
                self.logger.info(f"Loaded {len(self.test_cases)} test cases and {len(self.test_executions)} executions")
                
        except Exception as e:
            self.logger.error(f"Error loading test data: {e}")
    
    def _load_default_test_cases(self):
        """Carga test cases por defecto para cada categoría"""
        default_cases = [
            # CODING Tests
            {
                "name": "Simple Function Creation",
                "category": TaskCategory.CODING,
                "test_type": TestType.PERFORMANCE,
                "input_data": {
                    "task_type": "coding",
                    "prompt": "Write a Python function to calculate the factorial of a number"
                },
                "timeout_seconds": 30,
                "difficulty_level": 2,
                "description": "Basic function creation test"
            },
            {
                "name": "Complex Algorithm Implementation",
                "category": TaskCategory.CODING,
                "test_type": TestType.STRESS,
                "input_data": {
                    "task_type": "coding",
                    "prompt": "Implement a binary search tree with insert, delete, and search operations including balancing"
                },
                "timeout_seconds": 120,
                "difficulty_level": 8,
                "description": "Complex data structure implementation"
            },
            {
                "name": "Edge Case - Empty Input",
                "category": TaskCategory.CODING,
                "test_type": TestType.EDGE_CASE,
                "input_data": {
                    "task_type": "coding",
                    "prompt": ""
                },
                "timeout_seconds": 15,
                "difficulty_level": 1,
                "edge_case_type": "empty_input",
                "description": "Test handling of empty prompt"
            },
            {
                "name": "Edge Case - Extremely Long Prompt",
                "category": TaskCategory.CODING,
                "test_type": TestType.EDGE_CASE,
                "input_data": {
                    "task_type": "coding",
                    "prompt": "Write a function " + "that does something " * 200
                },
                "timeout_seconds": 60,
                "difficulty_level": 5,
                "edge_case_type": "long_input",
                "description": "Test handling of very long prompts"
            },
            
            # RESEARCH Tests
            {
                "name": "Basic Information Gathering",
                "category": TaskCategory.RESEARCH,
                "test_type": TestType.PERFORMANCE,
                "input_data": {
                    "task_type": "research",
                    "prompt": "Research the latest developments in quantum computing"
                },
                "timeout_seconds": 60,
                "difficulty_level": 4,
                "description": "Basic research task"
            },
            {
                "name": "Deep Technical Analysis",
                "category": TaskCategory.RESEARCH,
                "test_type": TestType.STRESS,
                "input_data": {
                    "task_type": "research",
                    "prompt": "Conduct comprehensive analysis of machine learning frameworks comparing TensorFlow, PyTorch, and JAX across performance, ease of use, and ecosystem"
                },
                "timeout_seconds": 180,
                "difficulty_level": 9,
                "description": "Complex comparative research"
            },
            
            # ANALYSIS Tests
            {
                "name": "Data Pattern Recognition",
                "category": TaskCategory.ANALYSIS,
                "test_type": TestType.PERFORMANCE,
                "input_data": {
                    "task_type": "analysis",
                    "prompt": "Analyze the following data and identify trends: [1,2,4,8,16,32,64]"
                },
                "timeout_seconds": 30,
                "difficulty_level": 3,
                "description": "Basic pattern analysis"
            },
            {
                "name": "Complex System Analysis",
                "category": TaskCategory.ANALYSIS,
                "test_type": TestType.STRESS,
                "input_data": {
                    "task_type": "analysis",
                    "prompt": "Analyze the architectural patterns, performance bottlenecks, and scalability issues in a distributed microservices system with 50+ services"
                },
                "timeout_seconds": 150,
                "difficulty_level": 9,
                "description": "Complex system architecture analysis"
            },
            
            # CREATIVE Tests
            {
                "name": "Simple Creative Writing",
                "category": TaskCategory.CREATIVE,
                "test_type": TestType.PERFORMANCE,
                "input_data": {
                    "task_type": "creative",
                    "prompt": "Write a short story about a robot learning to paint"
                },
                "timeout_seconds": 45,
                "difficulty_level": 4,
                "description": "Basic creative writing task"
            },
            
            # REASONING Tests
            {
                "name": "Logical Problem Solving",
                "category": TaskCategory.REASONING,
                "test_type": TestType.PERFORMANCE,
                "input_data": {
                    "task_type": "reasoning",
                    "prompt": "If all roses are flowers and some flowers are red, can we conclude that some roses are red?"
                },
                "timeout_seconds": 30,
                "difficulty_level": 5,
                "description": "Basic logical reasoning"
            },
            {
                "name": "Complex Multi-Step Reasoning",
                "category": TaskCategory.REASONING,
                "test_type": TestType.STRESS,
                "input_data": {
                    "task_type": "reasoning",
                    "prompt": "A company has 3 departments. Department A has twice as many employees as B. Department C has 10 more employees than A. If the total is 200 employees, and each department must have at least 20 employees, what are all possible distributions?"
                },
                "timeout_seconds": 90,
                "difficulty_level": 8,
                "description": "Complex mathematical reasoning"
            },
            
            # BATCH Tests
            {
                "name": "Multiple Simple Tasks",
                "category": TaskCategory.BATCH,
                "test_type": TestType.LOAD,
                "input_data": {
                    "task_type": "batch",
                    "prompt": "Execute multiple tasks",
                    "parameters": {
                        "batch_tasks": [
                            {"task_type": "coding", "prompt": "Write hello world"},
                            {"task_type": "analysis", "prompt": "Analyze number 42"},
                            {"task_type": "creative", "prompt": "Write a haiku"}
                        ]
                    }
                },
                "timeout_seconds": 120,
                "difficulty_level": 6,
                "description": "Batch processing test"
            }
        ]
        
        # Crear test cases si no existen
        for case_data in default_cases:
            case_id = f"default_{case_data['category'].value}_{len(self.test_cases)}"
            
            if case_id not in self.test_cases:
                test_case = TestCase(
                    id=case_id,
                    name=case_data["name"],
                    category=case_data["category"],
                    test_type=case_data["test_type"],
                    input_data=case_data["input_data"],
                    expected_output=case_data.get("expected_output"),
                    timeout_seconds=case_data["timeout_seconds"],
                    difficulty_level=case_data["difficulty_level"],
                    edge_case_type=case_data.get("edge_case_type"),
                    description=case_data["description"]
                )
                
                self.test_cases[case_id] = test_case
                self._save_test_case(test_case)
    
    def _save_test_case(self, test_case: TestCase):
        """Guarda un test case en la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO test_cases 
                    (id, name, category, test_type, input_data, expected_output,
                     timeout_seconds, difficulty_level, edge_case_type, description, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    test_case.id,
                    test_case.name,
                    test_case.category.value,
                    test_case.test_type.value,
                    json.dumps(test_case.input_data),
                    json.dumps(test_case.expected_output) if test_case.expected_output else None,
                    test_case.timeout_seconds,
                    test_case.difficulty_level,
                    test_case.edge_case_type,
                    test_case.description,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error saving test case: {e}")
    
    async def run_performance_test_suite(self, categories: List[TaskCategory] = None) -> PerformanceMetrics:
        """
        Ejecuta suite completo de tests de performance
        """
        if categories is None:
            categories = list(TaskCategory)
        
        self.logger.info(f"Starting performance test suite for categories: {[c.value for c in categories]}")
        
        # Filtrar test cases por categorías
        test_cases_to_run = [
            tc for tc in self.test_cases.values()
            if tc.category in categories and tc.test_type in [TestType.PERFORMANCE, TestType.STRESS]
        ]
        
        # Ejecutar tests
        executions = await self._run_test_batch(test_cases_to_run)
        
        # Calcular métricas
        metrics = self._calculate_performance_metrics(executions)
        
        # Detectar blind spots
        blind_spots = self._detect_blind_spots(executions)
        metrics.blind_spots = [bs.description for bs in blind_spots]
        
        # Guardar métricas
        await self._save_performance_metrics(metrics)
        
        # Generar reporte
        await self._generate_performance_report(metrics, executions, blind_spots)
        
        self.logger.info(f"Performance test suite completed - Success rate: {metrics.success_rate:.2%}")
        
        return metrics
    
    async def run_stress_test(self, category: TaskCategory, concurrent_tests: int = 10) -> Dict[str, Any]:
        """
        Ejecuta stress test con múltiples tests concurrentes
        """
        self.logger.info(f"Starting stress test for {category.value} with {concurrent_tests} concurrent tests")
        
        # Seleccionar test cases de stress
        stress_cases = [
            tc for tc in self.test_cases.values()
            if tc.category == category and tc.test_type == TestType.STRESS
        ]
        
        if not stress_cases:
            self.logger.warning(f"No stress test cases found for category {category.value}")
            return {}
        
        # Duplicar test cases para stress test
        test_cases_to_run = stress_cases * self.stress_test_multiplier
        
        # Ejecutar con alta concurrencia
        start_time = time.time()
        executions = await self._run_concurrent_tests(test_cases_to_run, concurrent_tests)
        total_time = time.time() - start_time
        
        # Analizar resultados de stress
        stress_metrics = {
            "category": category.value,
            "total_tests": len(executions),
            "concurrent_level": concurrent_tests,
            "total_execution_time": total_time,
            "avg_test_time": statistics.mean([ex.execution_time for ex in executions]),
            "success_rate": len([ex for ex in executions if ex.result == TestResult.PASS]) / len(executions),
            "timeout_rate": len([ex for ex in executions if ex.result == TestResult.TIMEOUT]) / len(executions),
            "error_rate": len([ex for ex in executions if ex.result == TestResult.ERROR]) / len(executions),
            "throughput": len(executions) / total_time,
            "resource_usage": {
                "avg_memory": statistics.mean([ex.memory_usage for ex in executions]),
                "avg_cpu": statistics.mean([ex.cpu_usage for ex in executions]),
                "peak_memory": max([ex.memory_usage for ex in executions]),
                "peak_cpu": max([ex.cpu_usage for ex in executions])
            }
        }
        
        self.logger.info(f"Stress test completed - Throughput: {stress_metrics['throughput']:.2f} tests/sec")
        
        return stress_metrics
    
    async def run_edge_case_tests(self) -> List[BlindSpot]:
        """
        Ejecuta tests de edge cases para detectar puntos ciegos
        """
        self.logger.info("Starting edge case testing")
        
        # Seleccionar edge cases
        edge_cases = [
            tc for tc in self.test_cases.values()
            if tc.test_type == TestType.EDGE_CASE
        ]
        
        # Ejecutar edge cases
        executions = await self._run_test_batch(edge_cases)
        
        # Detectar blind spots
        blind_spots = self._detect_blind_spots(executions)
        
        # Generar edge cases adicionales dinámicamente
        dynamic_edge_cases = await self._generate_dynamic_edge_cases()
        dynamic_executions = await self._run_test_batch(dynamic_edge_cases)
        
        # Combinar resultados
        all_executions = executions + dynamic_executions
        all_blind_spots = self._detect_blind_spots(all_executions)
        
        self.logger.info(f"Edge case testing completed - Found {len(all_blind_spots)} blind spots")
        
        return all_blind_spots
    
    async def _run_test_batch(self, test_cases: List[TestCase]) -> List[TestExecution]:
        """Ejecuta un lote de test cases"""
        executions = []
        
        # Ejecutar tests con concurrencia limitada
        semaphore = asyncio.Semaphore(self.max_concurrent_tests)
        
        async def run_single_test(test_case):
            async with semaphore:
                return await self._execute_test_case(test_case)
        
        # Crear tasks para todos los tests
        tasks = [run_single_test(tc) for tc in test_cases]
        
        # Ejecutar y recopilar resultados
        for task in asyncio.as_completed(tasks):
            try:
                execution = await task
                if execution:
                    executions.append(execution)
            except Exception as e:
                self.logger.error(f"Error in test execution: {e}")
        
        return executions
    
    async def _run_concurrent_tests(self, test_cases: List[TestCase], max_concurrent: int) -> List[TestExecution]:
        """Ejecuta tests con alta concurrencia para stress testing"""
        executions = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_single_test(test_case):
            async with semaphore:
                return await self._execute_test_case(test_case)
        
        # Ejecutar todos los tests concurrentemente
        tasks = [run_single_test(tc) for tc in test_cases]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, TestExecution):
                executions.append(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Test execution failed: {result}")
        
        return executions
    
    async def _execute_test_case(self, test_case: TestCase) -> Optional[TestExecution]:
        """Ejecuta un test case individual"""
        execution_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            self.logger.debug(f"Executing test case: {test_case.name}")
            
            # Simular ejecución de Sam (aquí se integraría con el sistema real)
            execution_time, result, output_data, error_message = await self._simulate_sam_execution(
                test_case.input_data, test_case.timeout_seconds
            )
            
            # Calcular métricas
            success_score = self._calculate_test_success_score(test_case, output_data, result)
            confidence_score = random.uniform(0.7, 0.95)  # Simulated
            
            # Simular uso de recursos
            memory_usage = random.uniform(50, 200)  # MB
            cpu_usage = random.uniform(10, 80)  # %
            
            execution = TestExecution(
                test_case_id=test_case.id,
                execution_id=execution_id,
                start_time=start_time,
                end_time=datetime.now(),
                execution_time=execution_time,
                result=result,
                output_data=output_data,
                error_message=error_message,
                model_used="qwen2.5:14b",  # Simulated
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                success_score=success_score,
                confidence_score=confidence_score
            )
            
            # Guardar ejecución
            await self._save_test_execution(execution)
            
            return execution
            
        except Exception as e:
            self.logger.error(f"Error executing test case {test_case.id}: {e}")
            return None
    
    async def _simulate_sam_execution(self, input_data: Dict[str, Any], timeout: int) -> Tuple[float, TestResult, Optional[Dict[str, Any]], Optional[str]]:
        """
        Simula la ejecución de Sam (placeholder para integración real)
        """
        # Simular tiempo de ejecución variable
        base_time = random.uniform(1, 10)
        
        # Ajustar por complejidad de la tarea
        prompt_length = len(input_data.get('prompt', ''))
        complexity_factor = min(2.0, prompt_length / 100)
        execution_time = base_time * complexity_factor
        
        # Simular diferentes resultados
        rand = random.random()
        
        if rand < 0.05:  # 5% timeout
            await asyncio.sleep(min(timeout + 1, 10))  # Simular timeout
            return timeout + 1, TestResult.TIMEOUT, None, "Execution timed out"
        
        elif rand < 0.15:  # 10% error
            await asyncio.sleep(execution_time)
            return execution_time, TestResult.ERROR, None, "Simulated execution error"
        
        elif rand < 0.25:  # 10% partial success
            await asyncio.sleep(execution_time)
            output = {
                "status": "partial",
                "result": {
                    "content": "Partial result for: " + input_data.get('prompt', '')[:50],
                    "model_used": "qwen2.5:14b",
                    "execution_time": execution_time,
                    "cost": 0.0
                }
            }
            return execution_time, TestResult.PARTIAL, output, None
        
        else:  # 75% success
            await asyncio.sleep(execution_time)
            output = {
                "status": "success",
                "result": {
                    "content": "Successful result for: " + input_data.get('prompt', '')[:50],
                    "model_used": "qwen2.5:14b",
                    "execution_time": execution_time,
                    "cost": 0.0
                }
            }
            return execution_time, TestResult.PASS, output, None
    
    def _calculate_test_success_score(self, test_case: TestCase, output_data: Optional[Dict[str, Any]], result: TestResult) -> float:
        """Calcula puntuación de éxito para un test"""
        if result == TestResult.PASS:
            base_score = 1.0
        elif result == TestResult.PARTIAL:
            base_score = 0.6
        elif result == TestResult.TIMEOUT:
            base_score = 0.2
        else:  # ERROR or FAIL
            base_score = 0.0
        
        # Ajustar por dificultad
        difficulty_factor = 1.0 - (test_case.difficulty_level - 1) * 0.05
        
        return max(0.0, min(1.0, base_score * difficulty_factor))
    
    async def _save_test_execution(self, execution: TestExecution):
        """Guarda ejecución de test en la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO test_executions 
                    (execution_id, test_case_id, start_time, end_time, execution_time,
                     result, output_data, error_message, model_used, memory_usage,
                     cpu_usage, success_score, confidence_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    execution.execution_id,
                    execution.test_case_id,
                    execution.start_time.isoformat(),
                    execution.end_time.isoformat() if execution.end_time else None,
                    execution.execution_time,
                    execution.result.value,
                    json.dumps(execution.output_data) if execution.output_data else None,
                    execution.error_message,
                    execution.model_used,
                    execution.memory_usage,
                    execution.cpu_usage,
                    execution.success_score,
                    execution.confidence_score
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error saving test execution: {e}")
    
    def _calculate_performance_metrics(self, executions: List[TestExecution]) -> PerformanceMetrics:
        """Calcula métricas de performance de las ejecuciones"""
        if not executions:
            return PerformanceMetrics(0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, [])
        
        total_tests = len(executions)
        passed_tests = len([ex for ex in executions if ex.result == TestResult.PASS])
        failed_tests = total_tests - passed_tests
        
        execution_times = [ex.execution_time for ex in executions]
        success_scores = [ex.success_score for ex in executions]
        
        avg_execution_time = statistics.mean(execution_times)
        median_execution_time = statistics.median(execution_times)
        p95_execution_time = np.percentile(execution_times, 95) if execution_times else 0.0
        
        success_rate = passed_tests / total_tests
        avg_success_score = statistics.mean(success_scores)
        
        timeout_count = len([ex for ex in executions if ex.result == TestResult.TIMEOUT])
        error_count = len([ex for ex in executions if ex.result == TestResult.ERROR])
        
        timeout_rate = timeout_count / total_tests
        error_rate = error_count / total_tests
        
        return PerformanceMetrics(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            avg_execution_time=avg_execution_time,
            median_execution_time=median_execution_time,
            p95_execution_time=p95_execution_time,
            success_rate=success_rate,
            avg_success_score=avg_success_score,
            timeout_rate=timeout_rate,
            error_rate=error_rate,
            blind_spots=[]
        )
    
    def _detect_blind_spots(self, executions: List[TestExecution]) -> List[BlindSpot]:
        """Detecta puntos ciegos basado en patrones de fallo"""
        blind_spots = []
        
        # Agrupar por categoría de test
        category_failures = defaultdict(list)
        
        for execution in executions:
            test_case = self.test_cases.get(execution.test_case_id)
            if test_case and execution.result in [TestResult.FAIL, TestResult.ERROR, TestResult.TIMEOUT]:
                category_failures[test_case.category.value].append(execution)
        
        # Analizar patrones de fallo por categoría
        for category, failures in category_failures.items():
            total_category_tests = len([ex for ex in executions if self.test_cases.get(ex.test_case_id, {}).category.value == category])
            
            if total_category_tests > 0:
                failure_rate = len(failures) / total_category_tests
                
                if failure_rate > 0.3:  # Más del 30% de fallos
                    severity = "critical" if failure_rate > 0.7 else "high" if failure_rate > 0.5 else "medium"
                    
                    examples = [
                        self.test_cases[ex.test_case_id].name 
                        for ex in failures[:3] 
                        if ex.test_case_id in self.test_cases
                    ]
                    
                    blind_spot = BlindSpot(
                        category=category,
                        description=f"High failure rate in {category} tasks",
                        failure_rate=failure_rate,
                        examples=examples,
                        severity=severity
                    )
                    blind_spots.append(blind_spot)
        
        # Detectar patrones específicos de error
        error_patterns = defaultdict(list)
        for execution in executions:
            if execution.error_message:
                # Simplificar mensaje de error para agrupar
                error_type = execution.error_message.split(':')[0] if ':' in execution.error_message else execution.error_message
                error_patterns[error_type].append(execution)
        
        for error_type, error_executions in error_patterns.items():
            if len(error_executions) > 2:  # Al menos 3 errores del mismo tipo
                failure_rate = len(error_executions) / len(executions)
                
                if failure_rate > 0.1:  # Más del 10% de errores del mismo tipo
                    severity = "high" if failure_rate > 0.2 else "medium"
                    
                    blind_spot = BlindSpot(
                        category="error_pattern",
                        description=f"Recurring error pattern: {error_type}",
                        failure_rate=failure_rate,
                        examples=[ex.test_case_id for ex in error_executions[:3]],
                        severity=severity
                    )
                    blind_spots.append(blind_spot)
        
        return blind_spots
    
    async def _generate_dynamic_edge_cases(self) -> List[TestCase]:
        """Genera edge cases dinámicamente basado en patrones observados"""
        dynamic_cases = []
        
        # Edge cases comunes
        edge_case_templates = [
            {
                "name": "Unicode Edge Case",
                "input_data": {"task_type": "coding", "prompt": "Write function with émojis 🚀 and spëcial chars"},
                "edge_case_type": "unicode_input"
            },
            {
                "name": "Very Large Number",
                "input_data": {"task_type": "analysis", "prompt": f"Analyze number {10**100}"},
                "edge_case_type": "large_numbers"
            },
            {
                "name": "Nested JSON Input",
                "input_data": {"task_type": "analysis", "prompt": json.dumps({"nested": {"deep": {"data": "value"}}})},
                "edge_case_type": "complex_json"
            },
            {
                "name": "SQL Injection Attempt",
                "input_data": {"task_type": "coding", "prompt": "'; DROP TABLE users; --"},
                "edge_case_type": "injection_attack"
            }
        ]
        
        for i, template in enumerate(edge_case_templates):
            case_id = f"dynamic_edge_{i}_{int(time.time())}"
            
            test_case = TestCase(
                id=case_id,
                name=template["name"],
                category=TaskCategory.CODING,  # Default category
                test_type=TestType.EDGE_CASE,
                input_data=template["input_data"],
                expected_output=None,
                timeout_seconds=30,
                difficulty_level=7,
                edge_case_type=template["edge_case_type"],
                description=f"Dynamic edge case: {template['name']}"
            )
            
            dynamic_cases.append(test_case)
        
        return dynamic_cases
    
    async def _save_performance_metrics(self, metrics: PerformanceMetrics):
        """Guarda métricas de performance en la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO performance_metrics 
                    (timestamp, total_tests, passed_tests, failed_tests, avg_execution_time,
                     median_execution_time, p95_execution_time, success_rate, avg_success_score,
                     timeout_rate, error_rate, blind_spots)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    metrics.total_tests,
                    metrics.passed_tests,
                    metrics.failed_tests,
                    metrics.avg_execution_time,
                    metrics.median_execution_time,
                    metrics.p95_execution_time,
                    metrics.success_rate,
                    metrics.avg_success_score,
                    metrics.timeout_rate,
                    metrics.error_rate,
                    json.dumps(metrics.blind_spots)
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error saving performance metrics: {e}")
    
    async def _generate_performance_report(self, metrics: PerformanceMetrics, executions: List[TestExecution], blind_spots: List[BlindSpot]):
        """Genera reporte detallado de performance"""
        try:
            report_path = f"/root/supermcp/test_reports/performance_report_{int(time.time())}.json"
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "summary": asdict(metrics),
                "blind_spots": [asdict(bs) for bs in blind_spots],
                "detailed_results": [
                    {
                        "test_case_id": ex.test_case_id,
                        "test_name": self.test_cases.get(ex.test_case_id, {}).name if ex.test_case_id in self.test_cases else "Unknown",
                        "result": ex.result.value,
                        "execution_time": ex.execution_time,
                        "success_score": ex.success_score,
                        "error_message": ex.error_message
                    }
                    for ex in executions
                ],
                "recommendations": self._generate_recommendations(metrics, blind_spots)
            }
            
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"Performance report generated: {report_path}")
            
        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
    
    def _generate_recommendations(self, metrics: PerformanceMetrics, blind_spots: List[BlindSpot]) -> List[str]:
        """Genera recomendaciones basadas en métricas y blind spots"""
        recommendations = []
        
        if metrics.success_rate < 0.8:
            recommendations.append("Success rate is below 80%. Consider reviewing model selection and prompt optimization.")
        
        if metrics.avg_execution_time > 30:
            recommendations.append("Average execution time is high. Consider optimizing model inference or using faster models for simple tasks.")
        
        if metrics.timeout_rate > 0.1:
            recommendations.append("High timeout rate detected. Review timeout settings and task complexity.")
        
        if metrics.error_rate > 0.15:
            recommendations.append("High error rate detected. Investigate error patterns and improve error handling.")
        
        for blind_spot in blind_spots:
            if blind_spot.severity in ["critical", "high"]:
                recommendations.append(f"Critical blind spot in {blind_spot.category}: {blind_spot.description}")
        
        if not recommendations:
            recommendations.append("Performance metrics are within acceptable ranges. Continue monitoring.")
        
        return recommendations
    
    def get_testing_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema de testing"""
        recent_executions = self.test_executions[-100:] if self.test_executions else []
        
        if recent_executions:
            recent_metrics = self._calculate_performance_metrics(recent_executions)
        else:
            recent_metrics = PerformanceMetrics(0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, [])
        
        return {
            "total_test_cases": len(self.test_cases),
            "total_executions": len(self.test_executions),
            "recent_metrics": asdict(recent_metrics),
            "test_cases_by_category": {
                category.value: len([tc for tc in self.test_cases.values() if tc.category == category])
                for category in TaskCategory
            },
            "test_cases_by_type": {
                test_type.value: len([tc for tc in self.test_cases.values() if tc.test_type == test_type])
                for test_type in TestType
            }
        }

# Instancia global del testing harness
agent_testing_harness = AgentTestingHarness()

# Funciones de conveniencia
async def run_performance_tests(categories: List[TaskCategory] = None) -> PerformanceMetrics:
    """Función de conveniencia para ejecutar tests de performance"""
    return await agent_testing_harness.run_performance_test_suite(categories)

async def run_stress_tests(category: TaskCategory, concurrent_tests: int = 10) -> Dict[str, Any]:
    """Función de conveniencia para ejecutar stress tests"""
    return await agent_testing_harness.run_stress_test(category, concurrent_tests)

async def detect_blind_spots() -> List[BlindSpot]:
    """Función de conveniencia para detectar blind spots"""
    return await agent_testing_harness.run_edge_case_tests()

def get_testing_harness_stats() -> Dict[str, Any]:
    """Función de conveniencia para obtener estadísticas"""
    return agent_testing_harness.get_testing_stats()

if __name__ == "__main__":
    # Test del testing harness
    async def test_testing_harness():
        print("=== AGENT TESTING HARNESS TEST ===")
        
        # Ejecutar tests de performance
        print("Running performance tests...")
        metrics = await run_performance_tests([TaskCategory.CODING, TaskCategory.REASONING])
        print(f"Performance metrics: {asdict(metrics)}")
        
        # Ejecutar stress test
        print("Running stress test...")
        stress_results = await run_stress_tests(TaskCategory.CODING, 5)
        print(f"Stress test results: {stress_results}")
        
        # Detectar blind spots
        print("Detecting blind spots...")
        blind_spots = await detect_blind_spots()
        print(f"Found {len(blind_spots)} blind spots")
        
        # Estadísticas
        stats = get_testing_harness_stats()
        print(f"Testing stats: {json.dumps(stats, indent=2)}")
    
    # Ejecutar test
    asyncio.run(test_testing_harness())

