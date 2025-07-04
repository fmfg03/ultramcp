"""
Chain of Debate consolidated routes
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from ..core.shared_dependencies import get_redis_dependency, cache_get, cache_set

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class EnhancedDebateRequest(BaseModel):
    topic: str = Field(..., description="Debate topic")
    participants: int = Field(3, ge=2, le=5, description="Number of participants")
    rounds: int = Field(3, ge=1, le=5, description="Number of debate rounds")
    privacy_level: str = Field("INTERNAL", description="Privacy level: PUBLIC, INTERNAL, CONFIDENTIAL")
    include_local_models: bool = Field(True, description="Include local models in debate")
    context: Optional[str] = Field(None, description="Additional context for debate")
    use_memory_context: bool = Field(False, description="Use code memory for context")
    project_name: Optional[str] = Field(None, description="Project for memory context")

class LocalDebateRequest(BaseModel):
    topic: str = Field(..., description="Debate topic")
    participants: int = Field(3, ge=2, le=5, description="Number of participants")
    rounds: int = Field(2, ge=1, le=3, description="Number of debate rounds")
    context: Optional[str] = Field(None, description="Additional context")

class DebateResponse(BaseModel):
    debate_id: str
    topic: str
    participants: List[Dict[str, Any]]
    rounds: List[Dict[str, Any]]
    consensus: Optional[str]
    confidence_score: float
    processing_time: float
    privacy_level: str
    local_processing: bool
    cost: float

# Mock debate orchestration (simplified for unified backend)
class MockDebateOrchestrator:
    """Simplified debate orchestrator for unified backend"""
    
    @staticmethod
    async def run_enhanced_debate(request: EnhancedDebateRequest) -> DebateResponse:
        """Run enhanced debate with multiple models"""
        start_time = datetime.utcnow()
        debate_id = f"debate_{int(start_time.timestamp())}"
        
        # Simulate debate process
        await asyncio.sleep(0.5)  # Simulate processing time
        
        participants = [
            {"name": "Claude", "model": "claude-3-sonnet", "type": "api"},
            {"name": "GPT-4", "model": "gpt-4", "type": "api"},
            {"name": "Local-Llama", "model": "llama3.1:8b", "type": "local"}
        ][:request.participants]
        
        rounds = []
        for round_num in range(request.rounds):
            round_data = {
                "round": round_num + 1,
                "arguments": [
                    {
                        "participant": p["name"],
                        "argument": f"Mock argument {round_num + 1} from {p['name']} on: {request.topic}",
                        "stance": "pro" if round_num % 2 == 0 else "con"
                    }
                    for p in participants
                ],
                "analysis": f"Round {round_num + 1} analysis for topic: {request.topic}"
            }
            rounds.append(round_data)
        
        # Generate mock consensus
        consensus = f"Based on the debate about '{request.topic}', the consensus suggests a balanced approach considering multiple perspectives."
        confidence_score = 0.85
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Calculate cost based on privacy level
        cost = 0.0 if request.privacy_level == "CONFIDENTIAL" else 0.05 * request.participants * request.rounds
        
        return DebateResponse(
            debate_id=debate_id,
            topic=request.topic,
            participants=participants,
            rounds=rounds,
            consensus=consensus,
            confidence_score=confidence_score,
            processing_time=processing_time,
            privacy_level=request.privacy_level,
            local_processing=request.privacy_level == "CONFIDENTIAL",
            cost=cost
        )
    
    @staticmethod
    async def run_local_debate(request: LocalDebateRequest) -> DebateResponse:
        """Run local-only debate"""
        start_time = datetime.utcnow()
        debate_id = f"local_debate_{int(start_time.timestamp())}"
        
        # Simulate local processing
        await asyncio.sleep(0.3)
        
        participants = [
            {"name": f"Local-Model-{i+1}", "model": f"llama3.1:8b", "type": "local"}
            for i in range(request.participants)
        ]
        
        rounds = []
        for round_num in range(request.rounds):
            round_data = {
                "round": round_num + 1,
                "arguments": [
                    {
                        "participant": p["name"],
                        "argument": f"Local argument {round_num + 1} from {p['name']} on: {request.topic}",
                        "stance": "balanced"
                    }
                    for p in participants
                ],
                "analysis": f"Local round {round_num + 1} analysis"
            }
            rounds.append(round_data)
        
        consensus = f"Local consensus on '{request.topic}': Privacy-first analysis suggests careful consideration of all factors."
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return DebateResponse(
            debate_id=debate_id,
            topic=request.topic,
            participants=participants,
            rounds=rounds,
            consensus=consensus,
            confidence_score=0.75,
            processing_time=processing_time,
            privacy_level="CONFIDENTIAL",
            local_processing=True,
            cost=0.0
        )

# Routes
@router.post("/enhanced-debate", response_model=DebateResponse)
async def enhanced_debate(
    request: EnhancedDebateRequest,
    background_tasks: BackgroundTasks,
    redis=Depends(get_redis_dependency)
):
    """Start enhanced multi-LLM debate with API and local models"""
    try:
        # Check cache for similar recent debates
        cache_key = f"debate:{hash(request.topic + request.privacy_level)}:{request.participants}"
        cached_result = await cache_get(cache_key)
        
        if cached_result:
            logger.info(f"Returning cached debate result for topic: {request.topic}")
            return DebateResponse.parse_raw(cached_result)
        
        # Run debate
        result = await MockDebateOrchestrator.run_enhanced_debate(request)
        
        # Cache result for 1 hour
        await cache_set(cache_key, result.json(), ttl=3600)
        
        # Log debate for analytics
        background_tasks.add_task(
            log_debate_analytics,
            result.debate_id,
            request.topic,
            result.privacy_level
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Enhanced debate failed: {e}")
        raise HTTPException(status_code=500, detail=f"Debate failed: {str(e)}")

@router.post("/local-debate", response_model=DebateResponse)
async def local_debate(
    request: LocalDebateRequest,
    background_tasks: BackgroundTasks
):
    """Privacy-first local debate with offline models only"""
    try:
        result = await MockDebateOrchestrator.run_local_debate(request)
        
        # Log local debate
        background_tasks.add_task(
            log_debate_analytics,
            result.debate_id,
            request.topic,
            "LOCAL_ONLY"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Local debate failed: {e}")
        raise HTTPException(status_code=500, detail=f"Local debate failed: {str(e)}")

@router.get("/debate/{debate_id}")
async def get_debate_result(debate_id: str):
    """Get debate result by ID"""
    try:
        # In real implementation, this would query database
        # For now, return mock response
        return {
            "debate_id": debate_id,
            "status": "completed",
            "result_available": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get debate result: {e}")
        raise HTTPException(status_code=404, detail="Debate not found")

@router.get("/debates/recent")
async def get_recent_debates(limit: int = 10):
    """Get recent debates"""
    try:
        # Mock recent debates
        recent_debates = [
            {
                "debate_id": f"debate_{i}",
                "topic": f"Mock topic {i}",
                "timestamp": datetime.utcnow().isoformat(),
                "participants": 3,
                "status": "completed"
            }
            for i in range(limit)
        ]
        
        return {
            "debates": recent_debates,
            "total": limit,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent debates: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve debates")

@router.get("/models/available")
async def get_available_models():
    """Get available models for debates"""
    return {
        "api_models": [
            {"name": "Claude 3 Sonnet", "id": "claude-3-sonnet", "cost_per_debate": 0.02},
            {"name": "GPT-4", "id": "gpt-4", "cost_per_debate": 0.03},
            {"name": "GPT-3.5 Turbo", "id": "gpt-3.5-turbo", "cost_per_debate": 0.01}
        ],
        "local_models": [
            {"name": "Llama 3.1 8B", "id": "llama3.1:8b", "cost_per_debate": 0.0},
            {"name": "Qwen 2.5 14B", "id": "qwen2.5:14b", "cost_per_debate": 0.0},
            {"name": "Mistral 7B", "id": "mistral:7b", "cost_per_debate": 0.0}
        ],
        "privacy_levels": ["PUBLIC", "INTERNAL", "CONFIDENTIAL"],
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/health")
async def cod_health():
    """Chain of Debate service health"""
    return {
        "status": "healthy",
        "service": "chain-of-debate",
        "timestamp": datetime.utcnow().isoformat(),
        "capabilities": {
            "enhanced_debate": True,
            "local_debate": True,
            "privacy_aware": True,
            "multi_model": True
        }
    }

# Background tasks
async def log_debate_analytics(debate_id: str, topic: str, privacy_level: str):
    """Log debate analytics for monitoring"""
    try:
        # In real implementation, this would log to analytics system
        logger.info(f"Debate analytics: {debate_id}, topic: {topic}, privacy: {privacy_level}")
        
        # Could store in database, send to analytics service, etc.
        
    except Exception as e:
        logger.warning(f"Failed to log debate analytics: {e}")