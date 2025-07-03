#!/usr/bin/env python3
"""
VoyageAI Integration Service for UltraMCP Supreme Stack
Provides hybrid embedding and reranking with privacy-first fallback
"""

import os
import json
import asyncio
import aiohttp
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
import hashlib
import time
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrivacyLevel(Enum):
    """Privacy levels for content processing"""
    PUBLIC = "public"           # Use VoyageAI APIs
    INTERNAL = "internal"       # Use local models only
    CONFIDENTIAL = "confidential"  # Use local models only
    RESTRICTED = "restricted"   # Use local models only

class EmbeddingModel(Enum):
    """Available embedding models"""
    VOYAGE_CODE_2 = "voyage-code-2"
    VOYAGE_LARGE_2 = "voyage-large-2" 
    VOYAGE_FINANCE = "voyage-finance-2"
    VOYAGE_HEALTHCARE = "voyage-healthcare-2"
    VOYAGE_LAW = "voyage-law-2"
    LOCAL_SENTENCE = "local-sentence-transformer"
    LOCAL_CODE = "local-code-transformer"

class RerankModel(Enum):
    """Available reranking models"""
    RERANK_LITE = "rerank-lite-1"
    RERANK_2 = "rerank-2"
    LOCAL_RERANK = "local-rerank"

@dataclass
class EmbeddingRequest:
    """Request for embedding generation"""
    texts: List[str]
    model: EmbeddingModel
    privacy_level: PrivacyLevel
    input_type: str = "document"  # document, query, classification
    domain: Optional[str] = None
    truncate: bool = True

@dataclass
class RerankRequest:
    """Request for result reranking"""
    query: str
    documents: List[str]
    model: RerankModel
    privacy_level: PrivacyLevel
    top_k: int = 20
    domain: Optional[str] = None

@dataclass
class EmbeddingResult:
    """Result from embedding generation"""
    embeddings: List[List[float]]
    model_used: str
    privacy_compliant: bool
    processing_time: float
    token_count: int
    cost: float = 0.0
    cached: bool = False

@dataclass
class RerankResult:
    """Result from reranking"""
    reranked_documents: List[Dict[str, Any]]
    model_used: str
    privacy_compliant: bool
    processing_time: float
    cost: float = 0.0
    cached: bool = False

class VoyageAIClient:
    """Client for VoyageAI API with intelligent fallback"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("VOYAGE_API_KEY")
        self.base_url = "https://api.voyageai.com/v1"
        self.session = None
        
        # Rate limiting
        self.requests_per_minute = 300
        self.request_times = []
        
        # Cost tracking
        self.embedding_cost_per_1k_tokens = 0.00013  # $0.13 per 1M tokens
        self.rerank_cost_per_1k_queries = 0.05      # $0.05 per 1K queries
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _check_rate_limit(self):
        """Check if we're within rate limits"""
        now = time.time()
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        if len(self.request_times) >= self.requests_per_minute:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        self.request_times.append(now)
    
    async def embed(self, 
                   texts: List[str], 
                   model: str = "voyage-code-2",
                   input_type: str = "document") -> Dict[str, Any]:
        """Generate embeddings using VoyageAI"""
        self._check_rate_limit()
        
        if not self.api_key:
            raise HTTPException(status_code=401, detail="VoyageAI API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": texts,
            "model": model,
            "input_type": input_type
        }
        
        start_time = time.time()
        
        try:
            async with self.session.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                processing_time = time.time() - start_time
                
                # Calculate cost
                total_tokens = result.get("usage", {}).get("total_tokens", len(" ".join(texts)) // 4)
                cost = (total_tokens / 1000) * self.embedding_cost_per_1k_tokens
                
                return {
                    "embeddings": [data["embedding"] for data in result["data"]],
                    "model": model,
                    "processing_time": processing_time,
                    "token_count": total_tokens,
                    "cost": cost
                }
                
        except Exception as e:
            logger.error(f"VoyageAI embedding error: {e}")
            raise HTTPException(status_code=500, detail=f"VoyageAI API error: {str(e)}")
    
    async def rerank(self, 
                    query: str, 
                    documents: List[str],
                    model: str = "rerank-lite-1",
                    top_k: int = 20) -> Dict[str, Any]:
        """Rerank documents using VoyageAI"""
        self._check_rate_limit()
        
        if not self.api_key:
            raise HTTPException(status_code=401, detail="VoyageAI API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "documents": documents,
            "model": model,
            "top_k": min(top_k, len(documents))
        }
        
        start_time = time.time()
        
        try:
            async with self.session.post(
                f"{self.base_url}/rerank",
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                processing_time = time.time() - start_time
                
                # Calculate cost
                cost = (1 / 1000) * self.rerank_cost_per_1k_queries
                
                return {
                    "reranked_documents": result["data"],
                    "model": model,
                    "processing_time": processing_time,
                    "cost": cost
                }
                
        except Exception as e:
            logger.error(f"VoyageAI reranking error: {e}")
            raise HTTPException(status_code=500, detail=f"VoyageAI API error: {str(e)}")

class LocalEmbeddingService:
    """Local embedding service for privacy-first processing"""
    
    def __init__(self):
        self.models = {}
        self.default_model = "all-MiniLM-L6-v2"
        self.code_model = "microsoft/codebert-base"
        
    async def initialize(self):
        """Initialize local models"""
        try:
            # Load default sentence transformer
            self.models["sentence"] = SentenceTransformer(self.default_model)
            logger.info(f"Loaded local sentence model: {self.default_model}")
            
            # Try to load code-specific model
            try:
                from transformers import AutoTokenizer, AutoModel
                self.models["code_tokenizer"] = AutoTokenizer.from_pretrained(self.code_model)
                self.models["code_model"] = AutoModel.from_pretrained(self.code_model)
                logger.info(f"Loaded local code model: {self.code_model}")
            except Exception as e:
                logger.warning(f"Could not load code model: {e}")
                
        except Exception as e:
            logger.error(f"Error initializing local models: {e}")
            raise
    
    def embed_texts(self, texts: List[str], model_type: str = "sentence") -> List[List[float]]:
        """Generate embeddings using local models"""
        try:
            if model_type == "sentence" and "sentence" in self.models:
                embeddings = self.models["sentence"].encode(texts)
                return [emb.tolist() for emb in embeddings]
            
            elif model_type == "code" and "code_model" in self.models:
                # Use CodeBERT for code embeddings
                import torch
                embeddings = []
                
                for text in texts:
                    inputs = self.models["code_tokenizer"](
                        text, 
                        padding=True, 
                        truncation=True, 
                        return_tensors="pt",
                        max_length=512
                    )
                    
                    with torch.no_grad():
                        outputs = self.models["code_model"](**inputs)
                        # Use [CLS] token embedding
                        embedding = outputs.last_hidden_state[:, 0, :].squeeze().numpy()
                        embeddings.append(embedding.tolist())
                
                return embeddings
            
            else:
                # Fallback to sentence transformer
                embeddings = self.models["sentence"].encode(texts)
                return [emb.tolist() for emb in embeddings]
                
        except Exception as e:
            logger.error(f"Local embedding error: {e}")
            raise
    
    def rerank_documents(self, query: str, documents: List[str], top_k: int = 20) -> List[Dict[str, Any]]:
        """Simple local reranking using similarity scores"""
        try:
            # Encode query and documents
            query_embedding = self.models["sentence"].encode([query])[0]
            doc_embeddings = self.models["sentence"].encode(documents)
            
            # Calculate similarities
            similarities = []
            for i, doc_emb in enumerate(doc_embeddings):
                similarity = np.dot(query_embedding, doc_emb) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(doc_emb)
                )
                similarities.append({
                    "index": i,
                    "document": documents[i],
                    "relevance_score": float(similarity)
                })
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x["relevance_score"], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Local reranking error: {e}")
            raise

class CacheManager:
    """Simple in-memory cache for embeddings and reranking results"""
    
    def __init__(self, max_size: int = 10000, ttl_seconds: int = 3600):
        self.cache = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
    
    def _generate_key(self, data: Union[str, List[str]], model: str) -> str:
        """Generate cache key"""
        if isinstance(data, list):
            content = "|".join(data)
        else:
            content = data
        
        return hashlib.md5(f"{content}:{model}".encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached result"""
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                return result
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Set cached result"""
        # Simple LRU eviction
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        self.cache[key] = (value, time.time())

class HybridEmbeddingService:
    """Hybrid service that intelligently chooses between VoyageAI and local models"""
    
    def __init__(self):
        self.voyage_client = None
        self.local_service = LocalEmbeddingService()
        self.cache = CacheManager()
        
        # Model mapping
        self.domain_models = {
            "code": EmbeddingModel.VOYAGE_CODE_2,
            "finance": EmbeddingModel.VOYAGE_FINANCE,
            "healthcare": EmbeddingModel.VOYAGE_HEALTHCARE,
            "legal": EmbeddingModel.VOYAGE_LAW,
            "general": EmbeddingModel.VOYAGE_LARGE_2
        }
    
    async def initialize(self):
        """Initialize the hybrid service"""
        # Initialize local service
        await self.local_service.initialize()
        
        # Initialize VoyageAI client if API key is available
        if os.getenv("VOYAGE_API_KEY"):
            self.voyage_client = VoyageAIClient()
            logger.info("VoyageAI client initialized")
        else:
            logger.warning("VoyageAI API key not found, using local-only mode")
    
    def _should_use_voyage(self, privacy_level: PrivacyLevel) -> bool:
        """Determine if VoyageAI should be used based on privacy level"""
        return (
            privacy_level == PrivacyLevel.PUBLIC and 
            self.voyage_client is not None
        )
    
    def _select_model(self, domain: Optional[str], privacy_level: PrivacyLevel) -> Tuple[str, bool]:
        """Select appropriate model based on domain and privacy"""
        use_voyage = self._should_use_voyage(privacy_level)
        
        if use_voyage:
            if domain in self.domain_models:
                return self.domain_models[domain].value, True
            else:
                return EmbeddingModel.VOYAGE_LARGE_2.value, True
        else:
            # Use local models
            if domain == "code":
                return "code", False
            else:
                return "sentence", False
    
    async def embed_texts(self, request: EmbeddingRequest) -> EmbeddingResult:
        """Generate embeddings with hybrid approach"""
        start_time = time.time()
        
        # Check cache first
        cache_key = self.cache._generate_key(request.texts, request.model.value)
        cached_result = self.cache.get(cache_key)
        if cached_result:
            cached_result["cached"] = True
            return EmbeddingResult(**cached_result)
        
        # Select model
        model_name, use_voyage = self._select_model(request.domain, request.privacy_level)
        
        try:
            if use_voyage and self.voyage_client:
                async with self.voyage_client as client:
                    result = await client.embed(
                        texts=request.texts,
                        model=model_name,
                        input_type=request.input_type
                    )
                    
                    embedding_result = EmbeddingResult(
                        embeddings=result["embeddings"],
                        model_used=f"voyage-{result['model']}",
                        privacy_compliant=(request.privacy_level == PrivacyLevel.PUBLIC),
                        processing_time=result["processing_time"],
                        token_count=result["token_count"],
                        cost=result["cost"],
                        cached=False
                    )
            else:
                # Use local models
                embeddings = self.local_service.embed_texts(request.texts, model_name)
                processing_time = time.time() - start_time
                
                embedding_result = EmbeddingResult(
                    embeddings=embeddings,
                    model_used=f"local-{model_name}",
                    privacy_compliant=True,
                    processing_time=processing_time,
                    token_count=sum(len(text.split()) for text in request.texts),
                    cost=0.0,
                    cached=False
                )
            
            # Cache result
            self.cache.set(cache_key, asdict(embedding_result))
            
            return embedding_result
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            
            # Fallback to local if VoyageAI fails
            if use_voyage:
                logger.info("Falling back to local embeddings")
                embeddings = self.local_service.embed_texts(request.texts, "sentence")
                processing_time = time.time() - start_time
                
                return EmbeddingResult(
                    embeddings=embeddings,
                    model_used="local-fallback",
                    privacy_compliant=True,
                    processing_time=processing_time,
                    token_count=sum(len(text.split()) for text in request.texts),
                    cost=0.0,
                    cached=False
                )
            else:
                raise
    
    async def rerank_documents(self, request: RerankRequest) -> RerankResult:
        """Rerank documents with hybrid approach"""
        start_time = time.time()
        
        # Check cache
        cache_key = self.cache._generate_key(
            [request.query] + request.documents, 
            request.model.value
        )
        cached_result = self.cache.get(cache_key)
        if cached_result:
            cached_result["cached"] = True
            return RerankResult(**cached_result)
        
        use_voyage = self._should_use_voyage(request.privacy_level)
        
        try:
            if use_voyage and self.voyage_client and request.model != RerankModel.LOCAL_RERANK:
                async with self.voyage_client as client:
                    result = await client.rerank(
                        query=request.query,
                        documents=request.documents,
                        model=request.model.value,
                        top_k=request.top_k
                    )
                    
                    rerank_result = RerankResult(
                        reranked_documents=result["reranked_documents"],
                        model_used=f"voyage-{result['model']}",
                        privacy_compliant=(request.privacy_level == PrivacyLevel.PUBLIC),
                        processing_time=result["processing_time"],
                        cost=result["cost"],
                        cached=False
                    )
            else:
                # Use local reranking
                reranked_docs = self.local_service.rerank_documents(
                    request.query, 
                    request.documents, 
                    request.top_k
                )
                processing_time = time.time() - start_time
                
                rerank_result = RerankResult(
                    reranked_documents=reranked_docs,
                    model_used="local-similarity",
                    privacy_compliant=True,
                    processing_time=processing_time,
                    cost=0.0,
                    cached=False
                )
            
            # Cache result
            self.cache.set(cache_key, asdict(rerank_result))
            
            return rerank_result
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            
            # Fallback to local reranking
            if use_voyage:
                logger.info("Falling back to local reranking")
                reranked_docs = self.local_service.rerank_documents(
                    request.query, 
                    request.documents, 
                    request.top_k
                )
                processing_time = time.time() - start_time
                
                return RerankResult(
                    reranked_documents=reranked_docs,
                    model_used="local-fallback",
                    privacy_compliant=True,
                    processing_time=processing_time,
                    cost=0.0,
                    cached=False
                )
            else:
                raise

# FastAPI application
app = FastAPI(
    title="VoyageAI Hybrid Service",
    description="Hybrid embedding and reranking service with privacy-first fallback",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instance
hybrid_service = HybridEmbeddingService()

@app.on_event("startup")
async def startup_event():
    """Initialize the service on startup"""
    await hybrid_service.initialize()
    logger.info("VoyageAI Hybrid Service started successfully")

# API Models
class EmbedRequest(BaseModel):
    texts: List[str] = Field(..., description="List of texts to embed")
    model: EmbeddingModel = Field(EmbeddingModel.VOYAGE_LARGE_2, description="Embedding model to use")
    privacy_level: PrivacyLevel = Field(PrivacyLevel.PUBLIC, description="Privacy level for processing")
    input_type: str = Field("document", description="Type of input: document, query, classification")
    domain: Optional[str] = Field(None, description="Domain for specialized models: code, finance, healthcare, legal")

class RerankRequest(BaseModel):
    query: str = Field(..., description="Search query")
    documents: List[str] = Field(..., description="Documents to rerank")
    model: RerankModel = Field(RerankModel.RERANK_LITE, description="Reranking model to use")
    privacy_level: PrivacyLevel = Field(PrivacyLevel.PUBLIC, description="Privacy level for processing")
    top_k: int = Field(20, description="Number of top results to return")
    domain: Optional[str] = Field(None, description="Domain context for reranking")

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "voyage-ai-hybrid",
        "timestamp": datetime.utcnow().isoformat(),
        "voyage_available": hybrid_service.voyage_client is not None,
        "local_models_loaded": len(hybrid_service.local_service.models) > 0
    }

@app.post("/embed", response_model=Dict[str, Any])
async def embed_texts(request: EmbedRequest):
    """Generate embeddings for texts"""
    try:
        embedding_request = EmbeddingRequest(
            texts=request.texts,
            model=request.model,
            privacy_level=request.privacy_level,
            input_type=request.input_type,
            domain=request.domain
        )
        
        result = await hybrid_service.embed_texts(embedding_request)
        return asdict(result)
        
    except Exception as e:
        logger.error(f"Embedding request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rerank", response_model=Dict[str, Any])
async def rerank_documents(request: RerankRequest):
    """Rerank documents for a query"""
    try:
        rerank_request = RerankRequest(
            query=request.query,
            documents=request.documents,
            model=request.model,
            privacy_level=request.privacy_level,
            top_k=request.top_k,
            domain=request.domain
        )
        
        result = await hybrid_service.rerank_documents(rerank_request)
        return asdict(result)
        
    except Exception as e:
        logger.error(f"Reranking request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def list_models():
    """List available models"""
    return {
        "embedding_models": [model.value for model in EmbeddingModel],
        "reranking_models": [model.value for model in RerankModel],
        "privacy_levels": [level.value for level in PrivacyLevel],
        "domains": ["code", "finance", "healthcare", "legal", "general"]
    }

@app.get("/stats")
async def get_stats():
    """Get service statistics"""
    return {
        "cache_size": len(hybrid_service.cache.cache),
        "cache_hit_rate": "Not implemented",  # TODO: Implement cache analytics
        "total_requests": "Not implemented",   # TODO: Implement request tracking
        "cost_savings": "Not implemented"     # TODO: Implement cost tracking
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)