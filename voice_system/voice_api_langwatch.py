from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import Response
from typing import Optional, Dict, Any
import asyncio
import os
import time
import uuid
from datetime import datetime
from dotenv import load_dotenv
import json

# Langwatch integration
try:
    import langwatch
    from langwatch.types import ChatMessage, LLMSpan
    LANGWATCH_AVAILABLE = True
except ImportError:
    LANGWATCH_AVAILABLE = False
    print("⚠️ Langwatch not available. Install with: pip install langwatch")

from mcp_voice_agents import MCPVoiceAgent
from voice_types import *

# Load environment variables
load_dotenv()

# Initialize Langwatch if available
if LANGWATCH_AVAILABLE and os.getenv("LANGWATCH_API_KEY"):
    langwatch.login(api_key=os.getenv("LANGWATCH_API_KEY"))
    print("✅ Langwatch initialized successfully")
else:
    print("⚠️ Langwatch not configured. Set LANGWATCH_API_KEY environment variable")

app = FastAPI(
    title="MCP Voice System API with Langwatch",
    description="CPU-Optimized Voice Agent System with OpenAI TTS and Langwatch Monitoring",
    version="3.0.0"
)

# Initialize agents
agents = {
    AgentType.CUSTOMER_SERVICE: MCPVoiceAgent(AgentType.CUSTOMER_SERVICE),
    AgentType.SALES: MCPVoiceAgent(AgentType.SALES),
    AgentType.RAG_ASSISTANT: MCPVoiceAgent(AgentType.RAG_ASSISTANT)
}

# Langwatch tracking utilities
class VoiceLangwatchTracker:
    def __init__(self):
        self.active_traces = {}
    
    def start_voice_trace(self, user_id: str, agent_type: str, language: str) -> str:
        """Start a new Langwatch trace for voice interaction"""
        trace_id = str(uuid.uuid4())
        
        if LANGWATCH_AVAILABLE and os.getenv("LANGWATCH_API_KEY"):
            try:
                # Initialize trace with metadata
                langwatch.get_current_trace().update(
                    trace_id=trace_id,
                    metadata={
                        "user_id": user_id,
                        "agent_type": agent_type,
                        "language": language,
                        "interaction_type": "voice",
                        "timestamp": datetime.now().isoformat(),
                        "session_type": "voice_call"
                    },
                    tags=["voice", "mcp", agent_type, language]
                )
                
                self.active_traces[trace_id] = {
                    "start_time": time.time(),
                    "user_id": user_id,
                    "agent_type": agent_type,
                    "language": language,
                    "steps": []
                }
                
                print(f"🎯 Langwatch trace started: {trace_id}")
                return trace_id
                
            except Exception as e:
                print(f"❌ Error starting Langwatch trace: {e}")
                return trace_id
        
        return trace_id
    
    def track_audio_processing(self, trace_id: str, step: str, duration: float, metadata: Dict[str, Any]):
        """Track audio processing steps"""
        if LANGWATCH_AVAILABLE and trace_id in self.active_traces:
            try:
                langwatch.get_current_span().update(
                    name=f"voice_{step}",
                    type="tool",
                    input=metadata.get("input", {}),
                    output=metadata.get("output", {}),
                    metadata={
                        "duration_ms": duration * 1000,
                        "step": step,
                        **metadata
                    }
                )
                
                self.active_traces[trace_id]["steps"].append({
                    "step": step,
                    "duration": duration,
                    "timestamp": time.time(),
                    "metadata": metadata
                })
                
            except Exception as e:
                print(f"❌ Error tracking audio processing: {e}")
    
    def track_llm_interaction(self, trace_id: str, messages: list, response: str, model: str, duration: float):
        """Track LLM interactions within voice calls"""
        if LANGWATCH_AVAILABLE and trace_id in self.active_traces:
            try:
                # Convert to Langwatch format
                chat_messages = [
                    ChatMessage(role=msg.get("role", "user"), content=msg.get("content", ""))
                    for msg in messages
                ]
                
                with langwatch.span(
                    name="voice_llm_call",
                    type="llm",
                    input=chat_messages,
                    output=response,
                    model=model,
                    metadata={
                        "duration_ms": duration * 1000,
                        "token_count": len(response.split()),
                        "interaction_type": "voice_to_text_to_voice"
                    }
                ) as span:
                    span.update(
                        metrics={
                            "latency": duration,
                            "tokens": len(response.split())
                        }
                    )
                
            except Exception as e:
                print(f"❌ Error tracking LLM interaction: {e}")
    
    def track_tts_generation(self, trace_id: str, text: str, voice: str, duration: float, audio_length: float):
        """Track Text-to-Speech generation"""
        if LANGWATCH_AVAILABLE and trace_id in self.active_traces:
            try:
                with langwatch.span(
                    name="voice_tts_generation",
                    type="tool",
                    input={"text": text, "voice": voice},
                    output={"audio_duration": audio_length},
                    metadata={
                        "generation_duration_ms": duration * 1000,
                        "audio_duration_ms": audio_length * 1000,
                        "text_length": len(text),
                        "voice_model": voice,
                        "efficiency_ratio": audio_length / duration if duration > 0 else 0
                    }
                ) as span:
                    span.update(
                        metrics={
                            "generation_latency": duration,
                            "audio_length": audio_length,
                            "text_length": len(text)
                        }
                    )
                
            except Exception as e:
                print(f"❌ Error tracking TTS generation: {e}")
    
    def end_voice_trace(self, trace_id: str, success: bool = True, error: str = None):
        """End voice trace with final metrics"""
        if trace_id in self.active_traces:
            trace_data = self.active_traces[trace_id]
            total_duration = time.time() - trace_data["start_time"]
            
            if LANGWATCH_AVAILABLE:
                try:
                    langwatch.get_current_trace().update(
                        metadata={
                            **langwatch.get_current_trace().metadata,
                            "total_duration_ms": total_duration * 1000,
                            "success": success,
                            "error": error,
                            "steps_count": len(trace_data["steps"]),
                            "end_timestamp": datetime.now().isoformat()
                        }
                    )
                    
                    if not success and error:
                        langwatch.get_current_trace().update(
                            error=error,
                            status="error"
                        )
                    
                except Exception as e:
                    print(f"❌ Error ending Langwatch trace: {e}")
            
            del self.active_traces[trace_id]
            print(f"🏁 Voice trace completed: {trace_id} ({total_duration:.2f}s)")

# Global tracker instance
voice_tracker = VoiceLangwatchTracker()

@app.get("/")
async def root():
    return {
        "message": "MCP Voice System API with Langwatch - CPU Optimized",
        "version": "3.0.0",
        "status": "ready",
        "agents": list(agents.keys()),
        "providers": ["openai", "espeak"],
        "monitoring": {
            "langwatch_enabled": LANGWATCH_AVAILABLE and bool(os.getenv("LANGWATCH_API_KEY")),
            "active_traces": len(voice_tracker.active_traces)
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agents_loaded": len(agents),
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "langwatch_configured": LANGWATCH_AVAILABLE and bool(os.getenv("LANGWATCH_API_KEY")),
        "langwatch_available": LANGWATCH_AVAILABLE,
        "active_voice_traces": len(voice_tracker.active_traces),
        "monitoring_status": "active" if LANGWATCH_AVAILABLE else "disabled"
    }

@app.get("/voice/metrics")
async def get_voice_metrics():
    """Get current voice system metrics"""
    return {
        "active_traces": len(voice_tracker.active_traces),
        "langwatch_status": "enabled" if LANGWATCH_AVAILABLE and os.getenv("LANGWATCH_API_KEY") else "disabled",
        "agents_status": {agent_type.value: "ready" for agent_type in agents.keys()},
        "system_info": {
            "version": "3.0.0",
            "monitoring": "langwatch",
            "timestamp": datetime.now().isoformat()
        }
    }

@app.post("/voice/customer-service")
async def customer_service_call(
    audio: UploadFile = File(...),
    user_id: str = Form(...),
    language: str = Form(default="es_mx")
):
    """Customer service voice call with Langwatch monitoring"""
    
    # Start Langwatch trace
    trace_id = voice_tracker.start_voice_trace(user_id, "customer_service", language)
    
    try:
        start_time = time.time()
        
        # Track audio upload
        audio_data = await audio.read()
        upload_duration = time.time() - start_time
        
        voice_tracker.track_audio_processing(
            trace_id, 
            "audio_upload", 
            upload_duration,
            {
                "input": {"file_size": len(audio_data), "content_type": audio.content_type},
                "output": {"status": "uploaded"},
                "file_size_mb": len(audio_data) / (1024 * 1024)
            }
        )
        
        # Process with agent
        agent = agents[AgentType.CUSTOMER_SERVICE]
        
        # Track the full voice processing
        process_start = time.time()
        result = await agent.process_voice_call(audio_data, user_id, language, trace_id)
        process_duration = time.time() - process_start
        
        voice_tracker.track_audio_processing(
            trace_id,
            "voice_processing_complete",
            process_duration,
            {
                "input": {"audio_length": len(audio_data)},
                "output": {"response_generated": True},
                "language": language,
                "agent_type": "customer_service"
            }
        )
        
        # End trace successfully
        voice_tracker.end_voice_trace(trace_id, success=True)
        
        return Response(
            content=result["audio"],
            media_type="audio/mpeg",
            headers={
                "X-Trace-ID": trace_id,
                "X-Processing-Time": str(process_duration),
                "X-Agent-Type": "customer_service",
                "X-Language": language
            }
        )
        
    except Exception as e:
        # End trace with error
        voice_tracker.end_voice_trace(trace_id, success=False, error=str(e))
        raise HTTPException(status_code=500, detail=f"Voice processing failed: {str(e)}")

@app.post("/voice/sales")
async def sales_call(
    audio: UploadFile = File(...),
    user_id: str = Form(...),
    language: str = Form(default="es_mx"),
    product_context: str = Form(default="")
):
    """Sales voice call with Langwatch monitoring"""
    
    trace_id = voice_tracker.start_voice_trace(user_id, "sales", language)
    
    try:
        start_time = time.time()
        audio_data = await audio.read()
        
        voice_tracker.track_audio_processing(
            trace_id,
            "audio_upload",
            time.time() - start_time,
            {
                "input": {"file_size": len(audio_data), "product_context": product_context},
                "output": {"status": "uploaded"},
                "context_provided": bool(product_context)
            }
        )
        
        agent = agents[AgentType.SALES]
        
        process_start = time.time()
        result = await agent.process_voice_call(audio_data, user_id, language, trace_id, product_context)
        process_duration = time.time() - process_start
        
        voice_tracker.end_voice_trace(trace_id, success=True)
        
        return Response(
            content=result["audio"],
            media_type="audio/mpeg",
            headers={
                "X-Trace-ID": trace_id,
                "X-Processing-Time": str(process_duration),
                "X-Agent-Type": "sales"
            }
        )
        
    except Exception as e:
        voice_tracker.end_voice_trace(trace_id, success=False, error=str(e))
        raise HTTPException(status_code=500, detail=f"Sales call failed: {str(e)}")

@app.post("/voice/rag-assistant")
async def rag_assistant_call(
    audio: UploadFile = File(...),
    user_id: str = Form(...),
    language: str = Form(default="es_mx"),
    knowledge_base: str = Form(default="general")
):
    """RAG assistant voice call with Langwatch monitoring"""
    
    trace_id = voice_tracker.start_voice_trace(user_id, "rag_assistant", language)
    
    try:
        start_time = time.time()
        audio_data = await audio.read()
        
        voice_tracker.track_audio_processing(
            trace_id,
            "audio_upload",
            time.time() - start_time,
            {
                "input": {"file_size": len(audio_data), "knowledge_base": knowledge_base},
                "output": {"status": "uploaded"},
                "knowledge_base": knowledge_base
            }
        )
        
        agent = agents[AgentType.RAG_ASSISTANT]
        
        process_start = time.time()
        result = await agent.process_voice_call(audio_data, user_id, language, trace_id, knowledge_base)
        process_duration = time.time() - process_start
        
        voice_tracker.end_voice_trace(trace_id, success=True)
        
        return Response(
            content=result["audio"],
            media_type="audio/mpeg",
            headers={
                "X-Trace-ID": trace_id,
                "X-Processing-Time": str(process_duration),
                "X-Agent-Type": "rag_assistant"
            }
        )
        
    except Exception as e:
        voice_tracker.end_voice_trace(trace_id, success=False, error=str(e))
        raise HTTPException(status_code=500, detail=f"RAG assistant call failed: {str(e)}")

@app.get("/voice/traces")
async def get_active_traces():
    """Get information about active voice traces"""
    return {
        "active_traces": len(voice_tracker.active_traces),
        "traces": [
            {
                "trace_id": trace_id,
                "user_id": data["user_id"],
                "agent_type": data["agent_type"],
                "language": data["language"],
                "duration": time.time() - data["start_time"],
                "steps_completed": len(data["steps"])
            }
            for trace_id, data in voice_tracker.active_traces.items()
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

