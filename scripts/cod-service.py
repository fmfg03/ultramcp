#!/usr/bin/env python3
"""
CoD Protocol Service - Advanced Orchestration Component
Only used for complex multi-LLM workflows
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import os

try:
    import uvicorn
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
except ImportError:
    print("❌ Missing dependencies. Install with: pip3 install fastapi uvicorn pydantic")
    sys.exit(1)

# Setup logging to combined log file
def setup_logging():
    log_file = Path("logs/combined.log")
    log_file.parent.mkdir(exist_ok=True)
    
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname.lower(),
                "service": "cod-protocol",
                "message": record.getMessage(),
            }
            if record.exc_info:
                log_entry["error"] = self.formatException(record.exc_info)
            return json.dumps(log_entry)
    
    logger = logging.getLogger("cod-service")
    logger.setLevel(logging.INFO)
    
    # File handler
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# API Models
class DebateRequest(BaseModel):
    task_id: str
    topic: str
    participants: List[str] = ["gpt-4", "claude-3-sonnet"]
    max_rounds: int = 3
    consensus_threshold: float = 0.75

class DebateResponse(BaseModel):
    task_id: str
    consensus: str
    confidence_score: float
    rounds: List[Dict]
    explanation: Dict[str, str]
    metadata: Dict

# FastAPI app
app = FastAPI(title="CoD Protocol Service", version="1.0.0")

class CoDProtocolEngine:
    """Simplified CoD Protocol for terminal-first approach"""
    
    def __init__(self):
        self.active_debates = {}
        
    async def run_debate(self, request: DebateRequest) -> DebateResponse:
        """Run a multi-LLM debate session"""
        logger.info(f"Starting debate: {request.task_id} on topic: {request.topic}")
        
        try:
            # Check if we have API keys for the debate
            openai_key = os.getenv('OPENAI_API_KEY')
            anthropic_key = os.getenv('ANTHROPIC_API_KEY')
            
            if not openai_key:
                logger.warning("No OpenAI API key - using simplified debate mode")
            
            # Simulate debate rounds (replace with actual implementation)
            rounds = []
            
            for round_num in range(request.max_rounds):
                round_data = await self._execute_round(
                    request.topic, 
                    request.participants, 
                    round_num + 1,
                    openai_key,
                    anthropic_key
                )
                rounds.append(round_data)
                
                # Check for early consensus
                if round_data.get('consensus_reached', False):
                    break
            
            # Generate final consensus
            consensus = await self._generate_consensus(rounds, request.topic)
            confidence = self._calculate_confidence(rounds)
            
            # Generate explanations for different audiences
            explanations = {
                "forCFO": f"💰 Financial perspective: {consensus[:200]}...",
                "forCTO": f"🔧 Technical perspective: {consensus[:200]}...",
                "general": consensus
            }
            
            response = DebateResponse(
                task_id=request.task_id,
                consensus=consensus,
                confidence_score=confidence,
                rounds=rounds,
                explanation=explanations,
                metadata={
                    "participants": request.participants,
                    "total_rounds": len(rounds),
                    "duration_seconds": len(rounds) * 30,  # Mock duration
                    "api_keys_available": {
                        "openai": bool(openai_key),
                        "anthropic": bool(anthropic_key)
                    }
                }
            )
            
            logger.info(f"Debate completed: {request.task_id} (Confidence: {confidence}%)")
            return response
            
        except Exception as e:
            logger.error(f"Debate failed: {request.task_id} - {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _execute_round(self, topic: str, participants: List[str], round_num: int, openai_key: str = None, anthropic_key: str = None) -> Dict:
        """Execute a single debate round"""
        logger.info(f"Executing round {round_num} with {len(participants)} participants")
        
        # Mock round execution with some intelligence
        await asyncio.sleep(1)  # Simulate processing time
        
        # Generate mock arguments based on topic analysis
        arguments = []
        for participant in participants:
            if "gpt" in participant.lower():
                arg = f"GPT-4 perspective on {topic}: Consider the scalability and innovation aspects"
            elif "claude" in participant.lower():
                arg = f"Claude perspective on {topic}: Focus on safety and ethical implications"
            else:
                arg = f"{participant} analysis of {topic}: Balanced viewpoint required"
            arguments.append(arg)
        
        return {
            "round": round_num,
            "participants": participants,
            "arguments": arguments,
            "consensus_reached": round_num >= 2,  # Mock consensus logic
            "round_summary": f"Round {round_num}: Analyzed '{topic}' from {len(participants)} perspectives",
            "key_points": [
                f"Point 1 from round {round_num}",
                f"Point 2 from round {round_num}",
                f"Point 3 from round {round_num}"
            ]
        }
    
    async def _generate_consensus(self, rounds: List[Dict], topic: str) -> str:
        """Generate final consensus from all rounds"""
        # Simplified consensus generation with topic awareness
        
        if "research" in topic.lower() or "study" in topic.lower():
            return f"Research consensus on '{topic}': Based on {len(rounds)} rounds of analysis, the evidence suggests a multi-faceted approach considering both immediate benefits and long-term implications is most appropriate."
        elif "investment" in topic.lower() or "financial" in topic.lower():
            return f"Investment consensus on '{topic}': After {len(rounds)} rounds of deliberation, the recommendation is to proceed with measured investment while monitoring key risk indicators and market conditions."
        elif "technology" in topic.lower() or "ai" in topic.lower():
            return f"Technology consensus on '{topic}': Following {len(rounds)} rounds of expert analysis, the optimal approach balances innovation potential with responsible development practices."
        else:
            return f"General consensus on '{topic}': Based on {len(rounds)} rounds of comprehensive analysis, the recommended approach requires careful consideration of multiple factors including risk assessment, strategic alignment, and stakeholder impact."
    
    def _calculate_confidence(self, rounds: List[Dict]) -> float:
        """Calculate confidence score based on round results"""
        # Simplified confidence calculation
        base_confidence = 70.0
        round_bonus = len(rounds) * 5.0
        consensus_bonus = 10.0 if any(r.get('consensus_reached') for r in rounds) else 0
        return min(95.0, base_confidence + round_bonus + consensus_bonus)

# Initialize engine
cod_engine = CoDProtocolEngine()

@app.post("/debate", response_model=DebateResponse)
async def start_debate(request: DebateRequest):
    """Start a new CoD Protocol debate"""
    return await cod_engine.run_debate(request)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "cod-protocol",
        "timestamp": datetime.utcnow().isoformat(),
        "active_debates": len(cod_engine.active_debates),
        "api_keys": {
            "openai": bool(os.getenv('OPENAI_API_KEY')),
            "anthropic": bool(os.getenv('ANTHROPIC_API_KEY'))
        }
    }

@app.get("/status")
async def get_status():
    """Get service status"""
    return {
        "service": "CoD Protocol Service",
        "version": "1.0.0",
        "active_debates": len(cod_engine.active_debates),
        "uptime": "running",  # Simplified
        "endpoints": [
            "POST /debate - Start a debate",
            "GET /health - Health check",
            "GET /status - Service status"
        ]
    }

@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "name": "UltraMCP CoD Protocol Service",
        "description": "Advanced orchestration for multi-LLM debates",
        "version": "1.0.0",
        "status": "operational"
    }

if __name__ == "__main__":
    logger.info("Starting CoD Protocol Service")
    
    # Check if running in dev mode
    dev_mode = "--dev" in sys.argv
    port = int(os.getenv('COD_SERVICE_PORT', 8001))
    
    print(f"🧠 Starting CoD Protocol Service on port {port}")
    if dev_mode:
        print("🔧 Development mode enabled")
    
    try:
        uvicorn.run(
            app,
            host="localhost",
            port=port,
            log_level="info" if dev_mode else "warning",
            reload=dev_mode
        )
    except KeyboardInterrupt:
        logger.info("CoD Protocol Service stopped by user")
    except Exception as e:
        logger.error(f"Failed to start CoD Protocol Service: {e}")
        sys.exit(1)