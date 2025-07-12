#!/usr/bin/env python3
"""
UltraMCP Local Models Orchestrator
Manages multiple local LLM providers and models
"""

import asyncio
import json
import logging
import httpx
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="UltraMCP Local Models Orchestrator", version="1.0.0")

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
                response = await client.get(f"{self.endpoint}/api/tags", timeout=5.0)
                return response.status_code == 200
        except:
            return False
    
    async def list_models(self) -> List[str]:
        """List available models"""
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

class OllamaProvider(ModelProvider):
    """Ollama provider integration"""
    def __init__(self):
        # Use gateway IP to access host Ollama from container network
        super().__init__("ollama", "http://172.19.0.1", 11434)
        
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

class ModelOrchestrator:
    """Orchestrates multiple local model providers"""
    
    def __init__(self):
        self.providers = {
            "ollama": OllamaProvider(),
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
                    "endpoint": provider.endpoint
                }
                logger.info(f"✅ {provider_name}: {len(models)} models available")
            else:
                self.available_models[provider_name] = {
                    "status": "unhealthy",
                    "models": [],
                    "endpoint": provider.endpoint
                }
                logger.warning(f"❌ {provider_name}: Not available")
    
    async def get_best_model(self, task_type: str = "general") -> Dict:
        """Get the best model for a specific task"""
        await self.refresh_models()
        
        # Model recommendations by task type
        task_preferences = {
            "coding": ["qwen2.5-coder:7b", "deepseek-coder:6.7b", "kimi-k2"],
            "reasoning": ["qwen2.5:14b", "llama3.1:8b", "kimi-k2"],
            "general": ["qwen2.5:14b", "llama3.1:8b", "mistral:7b"],
            "fast": ["mistral:7b", "deepseek-coder:6.7b"]
        }
        
        preferred_models = task_preferences.get(task_type, task_preferences["general"])
        
        for model_name in preferred_models:
            for provider_name, provider_info in self.available_models.items():
                if provider_info["status"] == "healthy" and model_name in provider_info["models"]:
                    return {
                        "provider": provider_name,
                        "model": model_name,
                        "endpoint": provider_info["endpoint"]
                    }
        
        return {"error": "No available models found"}

# Global orchestrator instance
orchestrator = ModelOrchestrator()

# API Models
class GenerateRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    provider: Optional[str] = None
    task_type: str = "general"
    temperature: float = 0.7
    max_tokens: int = 4000

class ModelResponse(BaseModel):
    content: str
    model: str
    provider: str
    metadata: Dict

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("🚀 Starting UltraMCP Local Models Orchestrator")
    await orchestrator.refresh_models()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "UltraMCP Local Models Orchestrator",
        "status": "operational",
        "version": "1.0.0"
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

@app.post("/generate")
async def generate_response(request: GenerateRequest):
    """Generate response using specified or best available model"""
    
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
            metadata={"task_type": request.task_type}
        )
        
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8012,
        log_level="info"
    )