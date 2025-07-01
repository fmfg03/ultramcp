#!/usr/bin/env python3
"""
Preferred Toolchain System - Local Models First
Wrapper inteligente que prioriza modelos locales sobre APIs externas
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class ModelType(Enum):
    LOCAL_OLLAMA = "local_ollama"
    EXTERNAL_API = "external_api"

class TaskType(Enum):
    CODING = "coding"
    RESEARCH = "research"
    REASONING = "reasoning"
    CREATIVE = "creative"
    ANALYSIS = "analysis"

@dataclass
class ModelConfig:
    name: str
    model_type: ModelType
    endpoint: str
    priority: int  # Lower = higher priority
    specialties: List[TaskType]
    max_tokens: int = 4096
    temperature_range: tuple = (0.1, 0.9)

@dataclass
class ExecutionResult:
    success: bool
    model_used: str
    response: str
    execution_time: float
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    error: Optional[str] = None

class PreferredToolchainSystem:
    """
    Sistema que prioriza modelos locales y maneja fallbacks inteligentes
    """
    
    def __init__(self):
        self.models = self._initialize_models()
        self.execution_log = []
        self.model_performance = {}
        self.logger = self._setup_logging()
        
    def _initialize_models(self) -> List[ModelConfig]:
        """Inicializa la configuración de modelos con prioridades"""
        return [
            # MODELOS LOCALES (PRIORIDAD ALTA)
            ModelConfig(
                name="qwen2.5-coder:7b",
                model_type=ModelType.LOCAL_OLLAMA,
                endpoint="http://localhost:11434/api/generate",
                priority=1,
                specialties=[TaskType.CODING, TaskType.ANALYSIS],
                max_tokens=8192
            ),
            ModelConfig(
                name="deepseek-coder:6.7b",
                model_type=ModelType.LOCAL_OLLAMA,
                endpoint="http://localhost:11434/api/generate",
                priority=2,
                specialties=[TaskType.CODING],
                max_tokens=4096
            ),
            ModelConfig(
                name="qwen2.5:14b",
                model_type=ModelType.LOCAL_OLLAMA,
                endpoint="http://localhost:11434/api/generate",
                priority=3,
                specialties=[TaskType.REASONING, TaskType.ANALYSIS],
                max_tokens=8192
            ),
            ModelConfig(
                name="llama3.1:8b",
                model_type=ModelType.LOCAL_OLLAMA,
                endpoint="http://localhost:11434/api/generate",
                priority=4,
                specialties=[TaskType.REASONING, TaskType.CREATIVE],
                max_tokens=4096
            ),
            ModelConfig(
                name="mistral:7b",
                model_type=ModelType.LOCAL_OLLAMA,
                endpoint="http://localhost:11434/api/generate",
                priority=5,
                specialties=[TaskType.CREATIVE, TaskType.REASONING],
                max_tokens=4096
            ),
            
            # APIS EXTERNAS (FALLBACK)
            ModelConfig(
                name="gpt-4o-mini",
                model_type=ModelType.EXTERNAL_API,
                endpoint="https://api.openai.com/v1/chat/completions",
                priority=10,
                specialties=[TaskType.REASONING, TaskType.CREATIVE, TaskType.ANALYSIS],
                max_tokens=16384
            ),
            ModelConfig(
                name="claude-3-haiku",
                model_type=ModelType.EXTERNAL_API,
                endpoint="https://api.anthropic.com/v1/messages",
                priority=11,
                specialties=[TaskType.REASONING, TaskType.CODING, TaskType.ANALYSIS],
                max_tokens=8192
            )
        ]
    
    def _setup_logging(self) -> logging.Logger:
        """Configura logging para tracking de uso de modelos"""
        logger = logging.getLogger("PreferredToolchain")
        logger.setLevel(logging.INFO)
        
        # Handler para archivo
        handler = logging.FileHandler("/root/supermcp/logs/model_usage.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def select_model(self, task_type: TaskType, prompt: str) -> ModelConfig:
        """
        Selecciona el mejor modelo basado en tipo de tarea y disponibilidad
        """
        # Filtrar modelos por especialidad
        specialized_models = [
            model for model in self.models 
            if task_type in model.specialties
        ]
        
        # Si no hay modelos especializados, usar todos
        if not specialized_models:
            specialized_models = self.models
        
        # Ordenar por prioridad (local first)
        specialized_models.sort(key=lambda x: x.priority)
        
        # Seleccionar el primer modelo disponible
        for model in specialized_models:
            if self._is_model_available(model):
                self.logger.info(f"Selected model: {model.name} for task: {task_type.value}")
                return model
        
        # Fallback al primer modelo de la lista
        self.logger.warning("No specialized models available, using fallback")
        return self.models[0]
    
    def _is_model_available(self, model: ModelConfig) -> bool:
        """
        Verifica si un modelo está disponible
        """
        if model.model_type == ModelType.LOCAL_OLLAMA:
            return self._check_ollama_model(model.name)
        else:
            return True  # Asumimos que APIs externas están disponibles
    
    def _check_ollama_model(self, model_name: str) -> bool:
        """
        Verifica si un modelo de Ollama está cargado y disponible
        """
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(model["name"].startswith(model_name) for model in models)
        except Exception as e:
            self.logger.error(f"Error checking Ollama model {model_name}: {str(e)}")
        
        return False
    
    async def execute_with_fallback(
        self, 
        prompt: str, 
        task_type: TaskType,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_message: Optional[str] = None
    ) -> ExecutionResult:
        """
        Ejecuta prompt con fallback automático entre modelos
        """
        start_time = time.time()
        
        # Seleccionar modelos en orden de prioridad
        specialized_models = [
            model for model in self.models 
            if task_type in model.specialties or not model.specialties
        ]
        specialized_models.sort(key=lambda x: x.priority)
        
        last_error = None
        
        for model in specialized_models:
            try:
                self.logger.info(f"Attempting execution with {model.name}")
                
                if model.model_type == ModelType.LOCAL_OLLAMA:
                    result = await self._execute_ollama(
                        model, prompt, temperature, max_tokens, system_message
                    )
                else:
                    result = await self._execute_external_api(
                        model, prompt, temperature, max_tokens, system_message
                    )
                
                if result.success:
                    execution_time = time.time() - start_time
                    result.execution_time = execution_time
                    
                    # Log successful execution
                    self._log_execution(model, result, task_type)
                    return result
                else:
                    last_error = result.error
                    self.logger.warning(f"Model {model.name} failed: {result.error}")
                    
            except Exception as e:
                last_error = str(e)
                self.logger.error(f"Exception with model {model.name}: {str(e)}")
                continue
        
        # Si todos los modelos fallan
        execution_time = time.time() - start_time
        return ExecutionResult(
            success=False,
            model_used="none",
            response="",
            execution_time=execution_time,
            error=f"All models failed. Last error: {last_error}"
        )
    
    async def _execute_ollama(
        self, 
        model: ModelConfig, 
        prompt: str, 
        temperature: float,
        max_tokens: Optional[int],
        system_message: Optional[str]
    ) -> ExecutionResult:
        """
        Ejecuta prompt usando modelo de Ollama
        """
        payload = {
            "model": model.name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens or model.max_tokens
            }
        }
        
        if system_message:
            payload["system"] = system_message
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    model.endpoint, 
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return ExecutionResult(
                            success=True,
                            model_used=model.name,
                            response=data.get("response", ""),
                            execution_time=0,  # Will be set by caller
                            tokens_used=data.get("eval_count"),
                            cost=0.0  # Local models are free
                        )
                    else:
                        error_text = await response.text()
                        return ExecutionResult(
                            success=False,
                            model_used=model.name,
                            response="",
                            execution_time=0,
                            error=f"HTTP {response.status}: {error_text}"
                        )
        except Exception as e:
            return ExecutionResult(
                success=False,
                model_used=model.name,
                response="",
                execution_time=0,
                error=str(e)
            )
    
    async def _execute_external_api(
        self, 
        model: ModelConfig, 
        prompt: str, 
        temperature: float,
        max_tokens: Optional[int],
        system_message: Optional[str]
    ) -> ExecutionResult:
        """
        Ejecuta prompt usando API externa (OpenAI/Claude)
        """
        if "openai" in model.endpoint:
            return await self._execute_openai(model, prompt, temperature, max_tokens, system_message)
        elif "anthropic" in model.endpoint:
            return await self._execute_claude(model, prompt, temperature, max_tokens, system_message)
        else:
            return ExecutionResult(
                success=False,
                model_used=model.name,
                response="",
                execution_time=0,
                error="Unsupported external API"
            )
    
    async def _execute_openai(
        self, 
        model: ModelConfig, 
        prompt: str, 
        temperature: float,
        max_tokens: Optional[int],
        system_message: Optional[str]
    ) -> ExecutionResult:
        """Ejecuta usando OpenAI API"""
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model.name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or model.max_tokens
        }
        
        headers = {
            "Authorization": f"Bearer {self._get_openai_key()}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    model.endpoint,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        choice = data["choices"][0]
                        usage = data.get("usage", {})
                        
                        return ExecutionResult(
                            success=True,
                            model_used=model.name,
                            response=choice["message"]["content"],
                            execution_time=0,
                            tokens_used=usage.get("total_tokens"),
                            cost=self._calculate_openai_cost(model.name, usage)
                        )
                    else:
                        error_text = await response.text()
                        return ExecutionResult(
                            success=False,
                            model_used=model.name,
                            response="",
                            execution_time=0,
                            error=f"OpenAI API error: {error_text}"
                        )
        except Exception as e:
            return ExecutionResult(
                success=False,
                model_used=model.name,
                response="",
                execution_time=0,
                error=str(e)
            )
    
    async def _execute_claude(
        self, 
        model: ModelConfig, 
        prompt: str, 
        temperature: float,
        max_tokens: Optional[int],
        system_message: Optional[str]
    ) -> ExecutionResult:
        """Ejecuta usando Claude API"""
        payload = {
            "model": model.name,
            "max_tokens": max_tokens or model.max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system_message:
            payload["system"] = system_message
        
        headers = {
            "x-api-key": self._get_claude_key(),
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    model.endpoint,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["content"][0]["text"]
                        usage = data.get("usage", {})
                        
                        return ExecutionResult(
                            success=True,
                            model_used=model.name,
                            response=content,
                            execution_time=0,
                            tokens_used=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                            cost=self._calculate_claude_cost(model.name, usage)
                        )
                    else:
                        error_text = await response.text()
                        return ExecutionResult(
                            success=False,
                            model_used=model.name,
                            response="",
                            execution_time=0,
                            error=f"Claude API error: {error_text}"
                        )
        except Exception as e:
            return ExecutionResult(
                success=False,
                model_used=model.name,
                response="",
                execution_time=0,
                error=str(e)
            )
    
    def _get_openai_key(self) -> str:
        """Obtiene la API key de OpenAI"""
        import os
        return os.getenv("OPENAI_API_KEY", "")
    
    def _get_claude_key(self) -> str:
        """Obtiene la API key de Claude"""
        import os
        return os.getenv("ANTHROPIC_API_KEY", "")
    
    def _calculate_openai_cost(self, model: str, usage: Dict) -> float:
        """Calcula el costo aproximado de OpenAI"""
        # Precios aproximados por 1K tokens
        prices = {
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006}
        }
        
        if model not in prices:
            return 0.0
        
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        cost = (input_tokens / 1000 * prices[model]["input"] + 
                output_tokens / 1000 * prices[model]["output"])
        
        return round(cost, 6)
    
    def _calculate_claude_cost(self, model: str, usage: Dict) -> float:
        """Calcula el costo aproximado de Claude"""
        # Precios aproximados por 1K tokens
        prices = {
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125}
        }
        
        if model not in prices:
            return 0.0
        
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        
        cost = (input_tokens / 1000 * prices[model]["input"] + 
                output_tokens / 1000 * prices[model]["output"])
        
        return round(cost, 6)
    
    def _log_execution(self, model: ModelConfig, result: ExecutionResult, task_type: TaskType):
        """Log de ejecución para análisis posterior"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model.name,
            "model_type": model.model_type.value,
            "task_type": task_type.value,
            "success": result.success,
            "execution_time": result.execution_time,
            "tokens_used": result.tokens_used,
            "cost": result.cost,
            "error": result.error
        }
        
        self.execution_log.append(log_entry)
        
        # Log a archivo
        self.logger.info(f"Execution: {json.dumps(log_entry)}")
        
        # Mantener solo los últimos 1000 logs en memoria
        if len(self.execution_log) > 1000:
            self.execution_log = self.execution_log[-1000:]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de rendimiento de modelos"""
        if not self.execution_log:
            return {"message": "No execution data available"}
        
        stats = {}
        
        for entry in self.execution_log:
            model = entry["model"]
            if model not in stats:
                stats[model] = {
                    "total_executions": 0,
                    "successful_executions": 0,
                    "total_time": 0,
                    "total_tokens": 0,
                    "total_cost": 0,
                    "task_types": {}
                }
            
            stats[model]["total_executions"] += 1
            if entry["success"]:
                stats[model]["successful_executions"] += 1
            
            stats[model]["total_time"] += entry["execution_time"] or 0
            stats[model]["total_tokens"] += entry["tokens_used"] or 0
            stats[model]["total_cost"] += entry["cost"] or 0
            
            task_type = entry["task_type"]
            if task_type not in stats[model]["task_types"]:
                stats[model]["task_types"][task_type] = 0
            stats[model]["task_types"][task_type] += 1
        
        # Calcular métricas derivadas
        for model, data in stats.items():
            if data["total_executions"] > 0:
                data["success_rate"] = data["successful_executions"] / data["total_executions"]
                data["avg_execution_time"] = data["total_time"] / data["total_executions"]
                if data["total_tokens"] > 0:
                    data["avg_tokens_per_execution"] = data["total_tokens"] / data["total_executions"]
        
        return stats

# Instancia global del sistema
toolchain = PreferredToolchainSystem()

# Funciones de conveniencia
async def execute_with_local_priority(
    prompt: str,
    task_type: str = "reasoning",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    system_message: Optional[str] = None
) -> ExecutionResult:
    """
    Función de conveniencia para ejecutar con prioridad local
    """
    task_enum = TaskType(task_type.lower())
    return await toolchain.execute_with_fallback(
        prompt, task_enum, temperature, max_tokens, system_message
    )

def get_model_stats() -> Dict[str, Any]:
    """
    Función de conveniencia para obtener estadísticas
    """
    return toolchain.get_performance_stats()

if __name__ == "__main__":
    # Test del sistema
    async def test_system():
        print("=== PREFERRED TOOLCHAIN SYSTEM TEST ===")
        
        # Test de selección de modelo
        coding_model = toolchain.select_model(TaskType.CODING, "Write a Python function")
        print(f"Selected model for coding: {coding_model.name}")
        
        # Test de ejecución
        result = await toolchain.execute_with_fallback(
            "Write a simple hello world function in Python",
            TaskType.CODING,
            temperature=0.3
        )
        
        print(f"Execution result: {result.success}")
        print(f"Model used: {result.model_used}")
        print(f"Response length: {len(result.response)} characters")
        print(f"Execution time: {result.execution_time:.2f} seconds")
        
        # Mostrar estadísticas
        stats = toolchain.get_performance_stats()
        print(f"Performance stats: {json.dumps(stats, indent=2)}")
    
    # Ejecutar test
    asyncio.run(test_system())

