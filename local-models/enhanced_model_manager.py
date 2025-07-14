#!/usr/bin/env python3
"""
UltraMCP Enhanced Local Models Orchestrator
Manages multiple local LLM providers including MiniMax-M1-80k
"""

import asyncio
import json
import logging
import httpx
import subprocess
import os
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="UltraMCP Enhanced Local Models Orchestrator", version="2.0.0")

class ModelProvider:
    """Base class for model providers"""
    def __init__(self, name: str, base_url: str, port: int):
        self.name = name
        self.base_url = base_url
        self.port = port
        self.endpoint = f"{base_url}:{port}"
        
    async def health_check(self) -> bool:
        """Check if provider is healthy"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.endpoint}/health", timeout=5.0)
                return response.status_code == 200
        except:
            return False
    
    async def list_models(self) -> List[str]:
        """List available models"""
        return []

class OllamaProvider(ModelProvider):
    """Ollama provider integration"""
    def __init__(self):
        super().__init__("ollama", "http://172.19.0.1", 11434)
        
    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.endpoint}/api/tags", timeout=5.0)
                return response.status_code == 200
        except:
            return False
    
    async def list_models(self) -> List[str]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.endpoint}/api/tags", timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    return [model['name'] for model in data.get('models', [])]
                return []
        except Exception as e:
            logger.error(f"Error listing models for {self.name}: {e}")
            return []
        
    async def generate(self, model: str, prompt: str, **kwargs) -> Dict:
        """Generate response using Ollama"""
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    **kwargs
                }
                response = await client.post(f"{self.endpoint}/api/generate", json=payload)
                return response.json()
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

class MiniMaxProvider(ModelProvider):
    """MiniMax-M1-80k provider using vLLM"""
    def __init__(self):
        super().__init__("minimax", "http://localhost", 8888)
        self.model_name = "MiniMaxAI/MiniMax-M1-80k"
        self.thinking_budget = 80000
        self.context_length = 1000000  # 1M tokens
        
    async def health_check(self) -> bool:
        """Check if MiniMax vLLM server is running"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.endpoint}/v1/models", timeout=5.0)
                return response.status_code == 200
        except:
            return False
    
    async def list_models(self) -> List[str]:
        """List MiniMax models"""
        if await self.health_check():
            return ["minimax-m1-80k"]
        return []
    
    async def start_server(self) -> bool:
        """Start MiniMax vLLM server if not running"""
        if await self.health_check():
            return True
            
        try:
            logger.info("🚀 Starting MiniMax-M1-80k vLLM server...")
            
            # Check if model is downloaded
            model_path = f"/models/{self.model_name}"
            if not os.path.exists(model_path):
                logger.info("📥 Downloading MiniMax-M1-80k model...")
                download_cmd = [
                    "huggingface-cli", "download", 
                    self.model_name,
                    "--local-dir", model_path,
                    "--local-dir-use-symlinks", "False"
                ]
                subprocess.run(download_cmd, check=True)
            
            # Start vLLM server
            vllm_cmd = [
                "python", "-m", "vllm.entrypoints.openai.api_server",
                "--model", model_path,
                "--host", "0.0.0.0",
                "--port", "8888",
                "--served-model-name", "minimax-m1-80k",
                "--max-model-len", str(self.context_length),
                "--enable-chunked-prefill",
                "--max-num-batched-tokens", "8192",
                "--gpu-memory-utilization", "0.9",
                "--tensor-parallel-size", "1",  # Adjust based on GPU count
                "--trust-remote-code"
            ]
            
            # Start server in background
            subprocess.Popen(vllm_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            for i in range(30):  # 30 second timeout
                await asyncio.sleep(2)
                if await self.health_check():
                    logger.info("✅ MiniMax-M1-80k server started successfully")
                    return True
            
            logger.error("❌ Failed to start MiniMax-M1-80k server")
            return False
            
        except Exception as e:
            logger.error(f"Error starting MiniMax server: {e}")
            return False
    
    async def generate(self, model: str, prompt: str, **kwargs) -> Dict:
        """Generate response using MiniMax-M1-80k"""
        # Ensure server is running
        if not await self.health_check():
            if not await self.start_server():
                raise HTTPException(status_code=503, detail="MiniMax server unavailable")
        
        try:
            # Prepare MiniMax-specific system prompt for reasoning
            system_prompt = """You are MiniMax-M1, a hybrid reasoning model with 80,000 token thinking budget. Use your full reasoning capabilities to provide comprehensive, well-thought-out responses. Take time to think through complex problems step by step."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            async with httpx.AsyncClient(timeout=600.0) as client:  # Extended timeout for reasoning
                payload = {
                    "model": "minimax-m1-80k",
                    "messages": messages,
                    "temperature": kwargs.get("temperature", 1.0),  # MiniMax recommendation
                    "top_p": kwargs.get("top_p", 0.95),  # MiniMax recommendation
                    "max_tokens": kwargs.get("max_tokens", 8192),
                    "stream": False
                }
                
                response = await client.post(f"{self.endpoint}/v1/chat/completions", json=payload)
                return response.json()
                
        except Exception as e:
            logger.error(f"MiniMax generation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

class KimiProvider(ModelProvider):
    """Kimi-K2 provider (when available)"""
    def __init__(self):
        super().__init__("kimi-k2", "http://localhost", 8011)
        
    async def generate(self, model: str, prompt: str, **kwargs) -> Dict:
        """Generate response using Kimi-K2"""
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": kwargs.get("temperature", 0.6),
                    "max_tokens": kwargs.get("max_tokens", 4000)
                }
                response = await client.post(f"{self.endpoint}/v1/chat/completions", json=payload)
                return response.json()
        except Exception as e:
            logger.error(f"Kimi generation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

class EnhancedModelOrchestrator:
    """Enhanced orchestrator with MiniMax-M1-80k support"""
    
    def __init__(self):
        self.providers = {
            "ollama": OllamaProvider(),
            "minimax": MiniMaxProvider(),
            "kimi-k2": KimiProvider()
        }
        self.available_models = {}
        
    async def refresh_models(self):
        """Refresh available models from all providers"""
        self.available_models = {}
        
        for provider_name, provider in self.providers.items():
            if await provider.health_check():
                models = await provider.list_models()
                self.available_models[provider_name] = {
                    "status": "healthy",
                    "models": models,
                    "endpoint": provider.endpoint,
                    "capabilities": self._get_provider_capabilities(provider_name)
                }
                logger.info(f"✅ {provider_name}: {len(models)} models available")
            else:
                self.available_models[provider_name] = {
                    "status": "unhealthy",
                    "models": [],
                    "endpoint": provider.endpoint,
                    "capabilities": self._get_provider_capabilities(provider_name)
                }
                logger.warning(f"❌ {provider_name}: Not available")
    
    def _get_provider_capabilities(self, provider_name: str) -> Dict:
        """Get capabilities for each provider"""
        capabilities = {
            "ollama": {
                "context_length": 32768,
                "specialties": ["general", "coding", "fast"],
                "thinking_budget": 0
            },
            "minimax": {
                "context_length": 1000000,
                "specialties": ["reasoning", "complex-analysis", "mathematics", "engineering"],
                "thinking_budget": 80000,
                "hybrid_attention": True
            },
            "kimi-k2": {
                "context_length": 200000,
                "specialties": ["long-context", "analysis"],
                "thinking_budget": 0
            }
        }
        return capabilities.get(provider_name, {})
    
    async def get_best_model(self, task_type: str = "general") -> Dict:
        """Get the best model for a specific task with MiniMax prioritization"""
        await self.refresh_models()
        
        # Enhanced task preferences with MiniMax for complex tasks
        task_preferences = {
            "reasoning": ["minimax-m1-80k", "qwen2.5:14b", "llama3.1:8b"],
            "mathematics": ["minimax-m1-80k", "qwen2.5:14b", "deepseek-coder:6.7b"],
            "engineering": ["minimax-m1-80k", "qwen2.5-coder:7b", "deepseek-coder:6.7b"],
            "complex-analysis": ["minimax-m1-80k", "kimi-k2", "qwen2.5:14b"],
            "long-context": ["minimax-m1-80k", "kimi-k2", "qwen2.5:14b"],
            "coding": ["qwen2.5-coder:7b", "deepseek-coder:6.7b", "minimax-m1-80k"],
            "general": ["minimax-m1-80k", "qwen2.5:14b", "llama3.1:8b"],
            "fast": ["mistral:7b", "deepseek-coder:6.7b", "qwen2.5:7b"]
        }
        
        preferred_models = task_preferences.get(task_type, task_preferences["general"])
        
        for model_name in preferred_models:
            for provider_name, provider_info in self.available_models.items():
                if provider_info["status"] == "healthy" and model_name in provider_info["models"]:
                    return {
                        "provider": provider_name,
                        "model": model_name,
                        "endpoint": provider_info["endpoint"],
                        "capabilities": provider_info["capabilities"]
                    }
        
        return {"error": "No available models found"}

    async def start_minimax_if_needed(self):
        """Start MiniMax server if not running"""
        minimax_provider = self.providers.get("minimax")
        if minimax_provider and not await minimax_provider.health_check():
            await minimax_provider.start_server()

# Global orchestrator instance
orchestrator = EnhancedModelOrchestrator()

# API Models
class GenerateRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    provider: Optional[str] = None
    task_type: str = "general"
    temperature: float = 0.7
    max_tokens: int = 4000
    use_reasoning: bool = False  # Flag for MiniMax reasoning mode

class ModelResponse(BaseModel):
    content: str
    model: str
    provider: str
    metadata: Dict

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("🚀 Starting UltraMCP Enhanced Local Models Orchestrator")
    await orchestrator.refresh_models()
    # Try to start MiniMax if available
    await orchestrator.start_minimax_if_needed()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "UltraMCP Enhanced Local Models Orchestrator",
        "status": "operational",
        "version": "2.0.0",
        "features": ["MiniMax-M1-80k", "Ollama", "Kimi-K2", "Auto-scaling"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    await orchestrator.refresh_models()
    healthy_providers = sum(1 for p in orchestrator.available_models.values() if p["status"] == "healthy")
    total_models = sum(len(p["models"]) for p in orchestrator.available_models.values())
    
    return {
        "status": "healthy",
        "providers": orchestrator.available_models,
        "healthy_providers": healthy_providers,
        "total_models": total_models
    }

@app.get("/models")
async def list_all_models():
    """List all available models from all providers"""
    await orchestrator.refresh_models()
    return orchestrator.available_models

@app.get("/models/best/{task_type}")
async def get_best_model(task_type: str):
    """Get the best model for a specific task type"""
    return await orchestrator.get_best_model(task_type)

@app.post("/models/minimax/start")
async def start_minimax():
    """Manually start MiniMax-M1-80k server"""
    minimax_provider = orchestrator.providers.get("minimax")
    if not minimax_provider:
        raise HTTPException(status_code=404, detail="MiniMax provider not found")
    
    success = await minimax_provider.start_server()
    if success:
        return {"message": "MiniMax-M1-80k server started successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to start MiniMax server")

@app.post("/generate")
async def generate_response(request: GenerateRequest):
    """Generate response using specified or best available model"""
    
    # If reasoning mode requested, prefer MiniMax
    if request.use_reasoning and not request.model:
        request.task_type = "reasoning"
    
    # If no specific model/provider, get the best one
    if not request.model or not request.provider:
        best_model = await orchestrator.get_best_model(request.task_type)
        if "error" in best_model:
            raise HTTPException(status_code=503, detail="No available models")
        
        model_name = best_model["model"]
        provider_name = best_model["provider"]
    else:
        model_name = request.model
        provider_name = request.provider
    
    # Generate response
    provider = orchestrator.providers.get(provider_name)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")
    
    try:
        if provider_name == "ollama":
            result = await provider.generate(
                model=model_name,
                prompt=request.prompt,
                temperature=request.temperature
            )
            content = result.get("response", "")
        elif provider_name == "minimax":
            result = await provider.generate(
                model=model_name,
                prompt=request.prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        elif provider_name == "kimi-k2":
            result = await provider.generate(
                model=model_name,
                prompt=request.prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            raise HTTPException(status_code=501, detail=f"Provider {provider_name} not implemented")
        
        return ModelResponse(
            content=content,
            model=model_name,
            provider=provider_name,
            metadata={
                "task_type": request.task_type,
                "reasoning_mode": request.use_reasoning,
                "context_length": orchestrator._get_provider_capabilities(provider_name).get("context_length", 0),
                "thinking_budget": orchestrator._get_provider_capabilities(provider_name).get("thinking_budget", 0)
            }
        )
        
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/reasoning")
async def generate_reasoning_response(request: GenerateRequest):
    """Generate response specifically using MiniMax-M1-80k for complex reasoning"""
    request.provider = "minimax"
    request.model = "minimax-m1-80k"
    request.use_reasoning = True
    request.temperature = 1.0  # MiniMax optimal temperature
    
    return await generate_response(request)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8012,
        log_level="info"
    )