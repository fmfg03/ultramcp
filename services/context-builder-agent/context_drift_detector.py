#!/usr/bin/env python3
"""
UltraMCP ContextBuilderAgent 2.0 - Context Drift Detector
Detects semantic drift in context using BGE-Large embeddings
"""

import asyncio
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import hashlib
import json
from transformers import AutoTokenizer, AutoModel
import torch
from sentence_transformers import SentenceTransformer
import redis.asyncio as redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContextDriftRequest(BaseModel):
    current_context: Dict[str, Any]
    previous_context: Dict[str, Any]
    domain: str
    confidence_threshold: float = 0.78

class ContextDriftResponse(BaseModel):
    drift_detected: bool
    similarity_score: float
    confidence: float
    drift_details: Dict[str, Any]
    timestamp: str
    recommendation: str

class ContextDriftDetector:
    """
    High-performance context drift detector using BGE-Large embeddings
    Detects semantic changes in context that may indicate need for mutation
    """
    
    def __init__(self):
        self.app = FastAPI(title="Context Drift Detector", version="1.0.0")
        self.model = None
        self.redis_client = None
        self.similarity_threshold = 0.78
        self.embedding_cache = {}
        self.performance_metrics = {
            "requests_processed": 0,
            "drift_detected_count": 0,
            "avg_similarity_score": 0.0,
            "cache_hit_rate": 0.0
        }
        
        # Initialize FastAPI routes
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.post("/detect_drift", response_model=ContextDriftResponse)
        async def detect_drift(request: ContextDriftRequest):
            """Detect context drift between current and previous context"""
            try:
                start_time = datetime.utcnow()
                
                # Load model if not already loaded
                if self.model is None:
                    await self._load_model()
                
                # Detect drift
                result = await self._detect_context_drift(
                    request.current_context,
                    request.previous_context,
                    request.domain,
                    request.confidence_threshold
                )
                
                # Update metrics
                self.performance_metrics["requests_processed"] += 1
                if result["drift_detected"]:
                    self.performance_metrics["drift_detected_count"] += 1
                
                # Calculate processing time
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.info(f"Drift detection completed in {processing_time:.2f}ms")
                
                return ContextDriftResponse(**result)
                
            except Exception as e:
                logger.error(f"Error in drift detection: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            try:
                model_loaded = self.model is not None
                redis_connected = self.redis_client is not None
                
                return {
                    "status": "healthy" if model_loaded else "initializing",
                    "model_loaded": model_loaded,
                    "redis_connected": redis_connected,
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
            cache_requests = sum(1 for _ in self.embedding_cache.keys())
            cache_hits = self.performance_metrics.get("cache_hits", 0)
            cache_hit_rate = cache_hits / max(cache_requests, 1)
            
            return {
                **self.performance_metrics,
                "cache_hit_rate": cache_hit_rate,
                "cache_size": len(self.embedding_cache),
                "similarity_threshold": self.similarity_threshold,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _load_model(self):
        """Load BGE-Large model for embeddings"""
        try:
            logger.info("Loading BGE-Large model...")
            
            # Use sentence-transformers for better performance
            self.model = SentenceTransformer('BAAI/bge-large-en-v1.5')
            
            # Connect to Redis for caching
            try:
                self.redis_client = redis.from_url("redis://mcp-redis:6379/1")
                await self.redis_client.ping()
                logger.info("Connected to Redis for embedding cache")
            except Exception as e:
                logger.warning(f"Redis connection failed, using in-memory cache: {e}")
                self.redis_client = None
            
            logger.info("BGE-Large model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    async def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text with caching"""
        # Generate cache key
        text_hash = hashlib.md5(text.encode()).hexdigest()
        cache_key = f"embedding:{text_hash}"
        
        # Try Redis cache first
        if self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    self.performance_metrics["cache_hits"] = self.performance_metrics.get("cache_hits", 0) + 1
                    return np.frombuffer(cached, dtype=np.float32)
            except Exception as e:
                logger.warning(f"Redis cache read failed: {e}")
        
        # Try in-memory cache
        if cache_key in self.embedding_cache:
            self.performance_metrics["cache_hits"] = self.performance_metrics.get("cache_hits", 0) + 1
            return self.embedding_cache[cache_key]
        
        # Generate new embedding
        embedding = self.model.encode(text, normalize_embeddings=True)
        
        # Cache the result
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    cache_key, 
                    3600,  # 1 hour TTL
                    embedding.tobytes()
                )
            except Exception as e:
                logger.warning(f"Redis cache write failed: {e}")
        
        # Also cache in memory (with size limit)
        if len(self.embedding_cache) < 1000:
            self.embedding_cache[cache_key] = embedding
        
        return embedding
    
    def _context_to_text(self, context: Dict[str, Any], domain: str) -> str:
        """Convert context to text representation for embedding"""
        if domain in context:
            domain_context = context[domain]
            
            # Extract key information
            text_parts = []
            
            if isinstance(domain_context, dict):
                if "fields" in domain_context:
                    for field, field_data in domain_context["fields"].items():
                        if isinstance(field_data, dict) and "value" in field_data:
                            value = field_data["value"]
                            if isinstance(value, list):
                                text_parts.append(f"{field}: {', '.join(map(str, value))}")
                            else:
                                text_parts.append(f"{field}: {value}")
                        else:
                            text_parts.append(f"{field}: {field_data}")
                
                # Include metadata if available
                for key in ["type", "confidence", "source"]:
                    if key in domain_context:
                        text_parts.append(f"{key}: {domain_context[key]}")
            
            return " | ".join(text_parts)
        
        # Fallback: convert entire context to string
        return json.dumps(context, ensure_ascii=False)
    
    async def _detect_context_drift(self, current_context: Dict[str, Any], 
                                   previous_context: Dict[str, Any],
                                   domain: str, confidence_threshold: float) -> Dict[str, Any]:
        """Core drift detection logic"""
        
        # Convert contexts to text
        current_text = self._context_to_text(current_context, domain)
        previous_text = self._context_to_text(previous_context, domain)
        
        # Get embeddings
        current_embedding = await self._get_embedding(current_text)
        previous_embedding = await self._get_embedding(previous_text)
        
        # Calculate cosine similarity
        similarity = np.dot(current_embedding, previous_embedding)
        
        # Determine if drift detected
        drift_detected = similarity < confidence_threshold
        
        # Analyze specific changes
        drift_details = await self._analyze_drift_details(
            current_context, previous_context, domain, similarity
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            drift_detected, similarity, drift_details
        )
        
        return {
            "drift_detected": drift_detected,
            "similarity_score": float(similarity),
            "confidence": float(1.0 - similarity) if drift_detected else float(similarity),
            "drift_details": drift_details,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "recommendation": recommendation
        }
    
    async def _analyze_drift_details(self, current: Dict[str, Any], 
                                   previous: Dict[str, Any], domain: str,
                                   similarity: float) -> Dict[str, Any]:
        """Analyze specific details of the drift"""
        details = {
            "domain": domain,
            "similarity_score": float(similarity),
            "changes_detected": [],
            "severity": "low"
        }
        
        if domain in current and domain in previous:
            current_domain = current[domain]
            previous_domain = previous[domain]
            
            # Check for field-level changes
            if "fields" in current_domain and "fields" in previous_domain:
                current_fields = current_domain["fields"]
                previous_fields = previous_domain["fields"]
                
                # Find added fields
                added_fields = set(current_fields.keys()) - set(previous_fields.keys())
                for field in added_fields:
                    details["changes_detected"].append({
                        "type": "field_added",
                        "field": field,
                        "new_value": current_fields[field].get("value", None)
                    })
                
                # Find removed fields
                removed_fields = set(previous_fields.keys()) - set(current_fields.keys())
                for field in removed_fields:
                    details["changes_detected"].append({
                        "type": "field_removed",
                        "field": field,
                        "old_value": previous_fields[field].get("value", None)
                    })
                
                # Find modified fields
                common_fields = set(current_fields.keys()) & set(previous_fields.keys())
                for field in common_fields:
                    current_value = current_fields[field].get("value")
                    previous_value = previous_fields[field].get("value")
                    
                    if current_value != previous_value:
                        details["changes_detected"].append({
                            "type": "field_modified",
                            "field": field,
                            "old_value": previous_value,
                            "new_value": current_value
                        })
        
        # Determine severity
        if similarity < 0.5:
            details["severity"] = "high"
        elif similarity < 0.7:
            details["severity"] = "medium"
        elif len(details["changes_detected"]) > 3:
            details["severity"] = "medium"
        
        return details
    
    def _generate_recommendation(self, drift_detected: bool, similarity: float,
                               drift_details: Dict[str, Any]) -> str:
        """Generate recommendation based on drift analysis"""
        if not drift_detected:
            return "No significant drift detected. Context is stable."
        
        severity = drift_details.get("severity", "low")
        change_count = len(drift_details.get("changes_detected", []))
        
        if severity == "high":
            return f"High drift detected (similarity: {similarity:.3f}). Immediate context validation recommended. Consider Chain of Debate activation."
        elif severity == "medium":
            return f"Medium drift detected with {change_count} changes. Review context mutations and validate coherence."
        else:
            return f"Low drift detected. Monitor for additional changes before taking action."

# Global instance
detector = ContextDriftDetector()

# FastAPI app instance for uvicorn
app = detector.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8020)