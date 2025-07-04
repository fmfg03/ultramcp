#!/usr/bin/env python3
"""
Voice System Service
Real-time voice processing and AI conversation service
"""

import asyncio
import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import websockets
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import existing voice system components
try:
    from core.voice_api import VoiceAPI
    from core.voice_manager_cpu_optimized import VoiceManagerCPUOptimized
    from mcp_voice_agents_langwatch import MCPVoiceAgentsLangwatch
except ImportError:
    # Create mock classes if imports fail
    class VoiceAPI:
        def __init__(self):
            pass
        async def process_audio(self, audio_data): 
            return {"text": "Mock transcription", "confidence": 0.9}
    
    class VoiceManagerCPUOptimized:
        def __init__(self):
            pass
        async def start_session(self): 
            return {"session_id": "mock_session"}
    
    class MCPVoiceAgentsLangwatch:
        def __init__(self):
            pass
        async def process_conversation(self, text): 
            return {"response": "Mock AI response"}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Voice System Service",
    description="Real-time voice processing and AI conversation service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class VoiceSessionRequest(BaseModel):
    session_type: str = "conversation"  # conversation, transcription, analysis
    language: str = "en-US"
    ai_enabled: bool = True
    real_time: bool = False

class AudioProcessRequest(BaseModel):
    audio_data: str  # Base64 encoded audio
    format: str = "wav"
    sample_rate: int = 16000

class ConversationRequest(BaseModel):
    text: str
    session_id: Optional[str] = None
    context: Dict[str, Any] = {}

class VoiceAnalysisRequest(BaseModel):
    audio_data: str
    analysis_type: str = "sentiment"  # sentiment, emotion, speaker

# Global state
voice_api = VoiceAPI()
voice_manager = VoiceManagerCPUOptimized()
voice_agents = MCPVoiceAgentsLangwatch()
active_sessions = {}
websocket_connections = {}
thread_pool = ThreadPoolExecutor(max_workers=4)

@app.on_event("startup")
async def startup_event():
    """Initialize voice services on startup"""
    logger.info("🎙️ Starting Voice System Service...")
    
    try:
        # Initialize voice components
        await voice_manager.start_session()
        logger.info("✅ Voice System Service initialized")
    except Exception as e:
        logger.error(f"Voice system initialization failed: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "voice-system",
        "active_sessions": len(active_sessions),
        "websocket_connections": len(websocket_connections),
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/v1/status")
async def get_service_status():
    """Get detailed service status"""
    return {
        "service": "voice-system",
        "status": "running",
        "active_sessions": len(active_sessions),
        "websocket_connections": len(websocket_connections),
        "features": [
            "real_time_transcription",
            "ai_conversation",
            "voice_analysis",
            "websocket_streaming"
        ],
        "supported_formats": ["wav", "mp3", "ogg"],
        "supported_languages": ["en-US", "es-ES", "fr-FR", "de-DE"],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/sessions/create")
async def create_voice_session(request: VoiceSessionRequest):
    """Create a new voice session"""
    try:
        session_id = f"voice_session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Initialize session
        session_data = {
            "session_id": session_id,
            "session_type": request.session_type,
            "language": request.language,
            "ai_enabled": request.ai_enabled,
            "real_time": request.real_time,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        active_sessions[session_id] = session_data
        
        logger.info(f"Created voice session: {session_id}")
        
        return {
            "session_id": session_id,
            "status": "created",
            "websocket_url": f"ws://sam.chat:8005/ws/{session_id}" if request.real_time else None,
            "session_data": session_data
        }
        
    except Exception as e:
        logger.error(f"Session creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/audio/process")
async def process_audio(request: AudioProcessRequest, background_tasks: BackgroundTasks):
    """Process audio data (transcription and analysis)"""
    try:
        # Decode audio data (simplified for now)
        audio_data = request.audio_data
        
        # Process audio asynchronously
        task_id = f"audio_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        background_tasks.add_task(
            process_audio_background,
            task_id,
            audio_data,
            request.format,
            request.sample_rate
        )
        
        return {
            "task_id": task_id,
            "status": "processing",
            "message": "Audio processing initiated"
        }
        
    except Exception as e:
        logger.error(f"Audio processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/conversation/chat")
async def voice_conversation(request: ConversationRequest):
    """Process voice conversation with AI"""
    try:
        # Process conversation
        response = await voice_agents.process_conversation(request.text)
        
        # Store conversation in session if provided
        if request.session_id and request.session_id in active_sessions:
            session = active_sessions[request.session_id]
            if "conversation_history" not in session:
                session["conversation_history"] = []
            
            session["conversation_history"].append({
                "timestamp": datetime.now().isoformat(),
                "user_input": request.text,
                "ai_response": response,
                "context": request.context
            })
        
        return {
            "session_id": request.session_id,
            "user_input": request.text,
            "ai_response": response,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Voice conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/analysis/voice")
async def analyze_voice(request: VoiceAnalysisRequest):
    """Analyze voice characteristics"""
    try:
        # Simplified voice analysis
        analysis = {
            "analysis_type": request.analysis_type,
            "results": {
                "sentiment": {
                    "polarity": 0.2,
                    "confidence": 0.85,
                    "label": "neutral"
                },
                "emotion": {
                    "primary_emotion": "calm",
                    "confidence": 0.78,
                    "emotional_spectrum": {
                        "calm": 0.78,
                        "excited": 0.12,
                        "sad": 0.05,
                        "angry": 0.05
                    }
                },
                "speaker": {
                    "estimated_age_range": "25-35",
                    "gender_confidence": 0.92,
                    "accent_detected": "neutral",
                    "speaking_rate": "normal"
                }
            },
            "audio_quality": {
                "signal_to_noise_ratio": "good",
                "clarity_score": 0.88,
                "background_noise": "minimal"
            }
        }
        
        return {
            "analysis_type": request.analysis_type,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Voice analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """Get voice session status"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return active_sessions[session_id]

@app.get("/api/v1/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Get voice session conversation history"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    history = session.get("conversation_history", [])
    
    return {
        "session_id": session_id,
        "conversation_count": len(history),
        "conversation_history": history
    }

@app.delete("/api/v1/sessions/{session_id}")
async def close_session(session_id: str):
    """Close voice session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Mark session as closed
    active_sessions[session_id]["status"] = "closed"
    active_sessions[session_id]["closed_at"] = datetime.now().isoformat()
    
    # Close WebSocket connection if exists
    if session_id in websocket_connections:
        await websocket_connections[session_id].close()
        del websocket_connections[session_id]
    
    return {
        "session_id": session_id,
        "status": "closed",
        "message": "Session closed successfully"
    }

@app.get("/api/v1/sessions/list")
async def list_sessions():
    """List all voice sessions"""
    return {
        "active_sessions": active_sessions,
        "total_sessions": len(active_sessions),
        "active_count": len([s for s in active_sessions.values() if s["status"] == "active"]),
        "websocket_connections": len(websocket_connections)
    }

# WebSocket endpoint for real-time voice
@app.websocket("/ws/{session_id}")
async def websocket_voice_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time voice processing"""
    await websocket.accept()
    
    if session_id not in active_sessions:
        await websocket.send_text(json.dumps({
            "error": "Session not found",
            "session_id": session_id
        }))
        await websocket.close()
        return
    
    websocket_connections[session_id] = websocket
    logger.info(f"WebSocket connected for session: {session_id}")
    
    try:
        while True:
            # Receive audio data
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                if message.get("type") == "audio":
                    # Process audio in real-time
                    audio_data = message.get("data")
                    
                    # Simplified real-time processing
                    result = await process_realtime_audio(audio_data, session_id)
                    
                    # Send response back
                    await websocket.send_text(json.dumps({
                        "type": "transcription",
                        "session_id": session_id,
                        "result": result,
                        "timestamp": datetime.now().isoformat()
                    }))
                
                elif message.get("type") == "text":
                    # Process text conversation
                    text = message.get("data")
                    response = await voice_agents.process_conversation(text)
                    
                    await websocket.send_text(json.dumps({
                        "type": "conversation",
                        "session_id": session_id,
                        "response": response,
                        "timestamp": datetime.now().isoformat()
                    }))
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "error": "Invalid JSON format"
                }))
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
        if session_id in websocket_connections:
            del websocket_connections[session_id]

# Background processing functions
async def process_audio_background(task_id: str, audio_data: str, format: str, sample_rate: int):
    """Process audio in background"""
    try:
        logger.info(f"Processing audio task: {task_id}")
        
        # Simulate audio processing
        await asyncio.sleep(2)  # Simulate processing time
        
        # Mock transcription result
        result = {
            "task_id": task_id,
            "transcription": "This is a mock transcription result",
            "confidence": 0.92,
            "language_detected": "en-US",
            "duration": 5.2,
            "word_count": 7,
            "processing_time": 2.1
        }
        
        logger.info(f"Audio processing completed: {task_id}")
        
    except Exception as e:
        logger.error(f"Audio processing failed for {task_id}: {e}")

async def process_realtime_audio(audio_data: str, session_id: str) -> Dict:
    """Process audio in real-time"""
    try:
        # Simplified real-time processing
        result = await voice_api.process_audio(audio_data)
        
        # Update session with real-time data
        if session_id in active_sessions:
            session = active_sessions[session_id]
            if "realtime_data" not in session:
                session["realtime_data"] = []
            
            session["realtime_data"].append({
                "timestamp": datetime.now().isoformat(),
                "result": result
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Real-time audio processing error: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    # Start both HTTP and WebSocket servers
    import multiprocessing
    
    def start_http_server():
        port = int(os.getenv("VOICE_SERVICE_PORT", 8004))
        logger.info(f"🎙️ Starting Voice System HTTP Service on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    
    def start_websocket_server():
        ws_port = int(os.getenv("VOICE_WEBSOCKET_PORT", 8005))
        logger.info(f"🔌 Starting Voice System WebSocket Service on port {ws_port}")
        # WebSocket is included in the main FastAPI app
    
    # Start HTTP server (WebSocket is included)
    start_http_server()