#!/usr/bin/env python3
"""
UltraMCP ContextBuilderAgent 2.0 - Contradiction Resolver
Resolves contextual contradictions using weighted consensus from local LLMs
"""

import asyncio
import aiohttp
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import json
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContradictionRequest(BaseModel):
    conflicting_statements: List[Dict[str, Any]]
    context_domain: str
    confidence_threshold: float = 0.85

class ContradictionResponse(BaseModel):
    resolution_found: bool
    resolved_statement: Dict[str, Any]
    confidence: float
    reasoning: str
    consensus_details: Dict[str, Any]
    timestamp: str

class ContradictionResolver:
    """
    Resolves contextual contradictions using multiple local LLMs
    Uses weighted consensus algorithm to reach coherent resolution
    """
    
    def __init__(self):
        self.app = FastAPI(title="Contradiction Resolver", version="1.0.0")
        self.ollama_host = "http://sam.chat:11434"
        self.model_pool = ["qwen2.5:14b", "llama3.1:8b", "mistral:7b"]
        self.model_weights = {
            "qwen2.5:14b": 0.4,  # Highest weight for analytical tasks
            "llama3.1:8b": 0.35,
            "mistral:7b": 0.25
        }
        self.confidence_threshold = 0.85
        self.performance_metrics = {
            "requests_processed": 0,
            "resolutions_found": 0,
            "avg_confidence": 0.0,
            "model_usage": {model: 0 for model in self.model_pool}
        }
        
        # Initialize FastAPI routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.post("/resolve_contradiction", response_model=ContradictionResponse)
        async def resolve_contradiction(request: ContradictionRequest):
            """Resolve contradiction between conflicting statements"""
            try:
                start_time = datetime.utcnow()
                
                result = await self._resolve_contradiction(
                    request.conflicting_statements,
                    request.context_domain,
                    request.confidence_threshold
                )
                
                # Update metrics
                self.performance_metrics["requests_processed"] += 1
                if result["resolution_found"]:
                    self.performance_metrics["resolutions_found"] += 1
                
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.info(f"Contradiction resolution completed in {processing_time:.2f}ms")
                
                return ContradictionResponse(**result)
                
            except Exception as e:
                logger.error(f"Error in contradiction resolution: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            try:
                # Test Ollama connection
                ollama_healthy = await self._test_ollama_connection()
                
                return {
                    "status": "healthy" if ollama_healthy else "degraded",
                    "ollama_connected": ollama_healthy,
                    "available_models": self.model_pool,
                    "metrics": self.performance_metrics,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
        
        @self.app.get("/metrics")
        async def get_metrics():
            """Get performance metrics"""
            success_rate = 0
            if self.performance_metrics["requests_processed"] > 0:
                success_rate = self.performance_metrics["resolutions_found"] / self.performance_metrics["requests_processed"]
            
            return {
                **self.performance_metrics,
                "success_rate": success_rate,
                "model_weights": self.model_weights,
                "confidence_threshold": self.confidence_threshold,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _test_ollama_connection(self) -> bool:
        """Test connection to Ollama"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_host}/api/tags") as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def _query_model(self, model: str, prompt: str) -> Dict[str, Any]:
        """Query a specific Ollama model"""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_ctx": 4096
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_host}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.performance_metrics["model_usage"][model] += 1
                        return {
                            "success": True,
                            "response": result.get("response", ""),
                            "model": model
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}",
                            "model": model
                        }
        except Exception as e:
            logger.error(f"Error querying model {model}: {e}")
            return {
                "success": False,
                "error": str(e),
                "model": model
            }
    
    def _create_resolution_prompt(self, statements: List[Dict[str, Any]], 
                                 domain: str) -> str:
        """Create prompt for contradiction resolution"""
        
        prompt = f"""You are an expert context analyst tasked with resolving contradictions in the {domain} domain.

Given the following conflicting statements, analyze them and provide a coherent resolution:

CONFLICTING STATEMENTS:
"""
        
        for i, statement in enumerate(statements, 1):
            source = statement.get("source", "unknown")
            confidence = statement.get("confidence", 0.0)
            content = statement.get("content", statement.get("value", str(statement)))
            
            prompt += f"\nStatement {i} (Source: {source}, Confidence: {confidence}):\n{content}\n"
        
        prompt += f"""
ANALYSIS REQUIREMENTS:
1. Identify the core contradiction between the statements
2. Evaluate the credibility of each source
3. Consider the confidence levels provided
4. Propose a coherent resolution that synthesizes the best elements
5. Provide your confidence level (0.0-1.0) in the resolution

RESPONSE FORMAT:
Resolution: [Your resolved statement]
Confidence: [0.0-1.0]
Reasoning: [Detailed explanation of your analysis and resolution approach]

Please provide a clear, actionable resolution that maintains semantic coherence while resolving the contradiction."""
        
        return prompt
    
    async def _resolve_contradiction(self, statements: List[Dict[str, Any]],
                                   domain: str, confidence_threshold: float) -> Dict[str, Any]:
        """Core contradiction resolution logic"""
        
        if len(statements) < 2:
            return {
                "resolution_found": False,
                "resolved_statement": {},
                "confidence": 0.0,
                "reasoning": "Insufficient statements for contradiction analysis",
                "consensus_details": {},
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        # Create resolution prompt
        prompt = self._create_resolution_prompt(statements, domain)
        
        # Query multiple models in parallel
        tasks = []
        for model in self.model_pool:
            tasks.append(self._query_model(model, prompt))
        
        model_responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process responses
        valid_responses = []
        for response in model_responses:
            if isinstance(response, dict) and response.get("success"):
                parsed = self._parse_model_response(response["response"], response["model"])
                if parsed:
                    valid_responses.append(parsed)
        
        if not valid_responses:
            return {
                "resolution_found": False,
                "resolved_statement": {},
                "confidence": 0.0,
                "reasoning": "No valid responses from models",
                "consensus_details": {"attempted_models": self.model_pool},
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        # Apply weighted consensus
        consensus_result = self._apply_weighted_consensus(valid_responses)
        
        # Check if consensus meets threshold
        resolution_found = consensus_result["confidence"] >= confidence_threshold
        
        return {
            "resolution_found": resolution_found,
            "resolved_statement": consensus_result["resolved_statement"],
            "confidence": consensus_result["confidence"],
            "reasoning": consensus_result["reasoning"],
            "consensus_details": consensus_result["consensus_details"],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _parse_model_response(self, response: str, model: str) -> Optional[Dict[str, Any]]:
        """Parse model response into structured format"""
        try:
            lines = response.strip().split('\n')
            
            resolution = ""
            confidence = 0.0
            reasoning = ""
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                if line.startswith("Resolution:"):
                    current_section = "resolution"
                    resolution = line.replace("Resolution:", "").strip()
                elif line.startswith("Confidence:"):
                    current_section = "confidence"
                    conf_str = line.replace("Confidence:", "").strip()
                    try:
                        confidence = float(conf_str)
                    except ValueError:
                        confidence = 0.5  # Default
                elif line.startswith("Reasoning:"):
                    current_section = "reasoning"
                    reasoning = line.replace("Reasoning:", "").strip()
                else:
                    # Continue previous section
                    if current_section == "resolution" and line:
                        resolution += " " + line
                    elif current_section == "reasoning" and line:
                        reasoning += " " + line
            
            if resolution and confidence > 0:
                return {
                    "model": model,
                    "resolution": resolution.strip(),
                    "confidence": min(max(confidence, 0.0), 1.0),
                    "reasoning": reasoning.strip()
                }
        
        except Exception as e:
            logger.warning(f"Failed to parse response from {model}: {e}")
        
        return None
    
    def _apply_weighted_consensus(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply weighted consensus algorithm to model responses"""
        
        if not responses:
            return {
                "resolved_statement": {},
                "confidence": 0.0,
                "reasoning": "No valid responses for consensus",
                "consensus_details": {}
            }
        
        # Calculate weighted confidence
        total_weight = 0
        weighted_confidence = 0
        
        for response in responses:
            model = response["model"]
            weight = self.model_weights.get(model, 0.2)  # Default weight
            confidence = response["confidence"]
            
            weighted_confidence += confidence * weight
            total_weight += weight
        
        final_confidence = weighted_confidence / max(total_weight, 1.0)
        
        # Select best resolution (highest confidence from highest weighted model)
        best_response = max(responses, key=lambda r: (
            r["confidence"] * self.model_weights.get(r["model"], 0.2)
        ))
        
        # Combine reasoning from all models
        combined_reasoning = f"Consensus from {len(responses)} models. "
        combined_reasoning += f"Primary resolution from {best_response['model']}: {best_response['reasoning']}"
        
        # Create consensus details
        consensus_details = {
            "participating_models": [r["model"] for r in responses],
            "individual_confidences": {r["model"]: r["confidence"] for r in responses},
            "weighted_average_confidence": final_confidence,
            "selected_model": best_response["model"],
            "agreement_level": self._calculate_agreement_level(responses)
        }
        
        return {
            "resolved_statement": {
                "content": best_response["resolution"],
                "confidence": final_confidence,
                "source": "contradiction_resolver_consensus",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "consensus_method": "weighted_llm_consensus"
            },
            "confidence": final_confidence,
            "reasoning": combined_reasoning,
            "consensus_details": consensus_details
        }
    
    def _calculate_agreement_level(self, responses: List[Dict[str, Any]]) -> str:
        """Calculate agreement level between model responses"""
        if len(responses) < 2:
            return "single_response"
        
        # Simple heuristic: check confidence variance
        confidences = [r["confidence"] for r in responses]
        avg_confidence = sum(confidences) / len(confidences)
        variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)
        
        if variance < 0.05:
            return "high_agreement"
        elif variance < 0.15:
            return "moderate_agreement"
        else:
            return "low_agreement"

# Global instance
resolver = ContradictionResolver()

# FastAPI app instance for uvicorn
app = resolver.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8021)