# voice_api.py
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import Response
from typing import Optional
import asyncio
import os
from dotenv import load_dotenv

from mcp_voice_agents import MCPVoiceAgent
from voice_types import *

# Load environment variables
load_dotenv()

app = FastAPI(
    title="MCP Voice System API",
    description="CPU-Optimized Voice Agent System with OpenAI TTS",
    version="2.0.0"
)

# Initialize agents
agents = {
    AgentType.CUSTOMER_SERVICE: MCPVoiceAgent(AgentType.CUSTOMER_SERVICE),
    AgentType.SALES: MCPVoiceAgent(AgentType.SALES),
    AgentType.RAG_ASSISTANT: MCPVoiceAgent(AgentType.RAG_ASSISTANT)
}

@app.get("/")
async def root():
    return {
        "message": "MCP Voice System API - CPU Optimized",
        "version": "2.0.0",
        "status": "ready",
        "agents": list(agents.keys()),
        "providers": ["openai", "espeak"]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agents_loaded": len(agents),
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "langwatch_configured": bool(os.getenv("LANGWATCH_API_KEY"))
    }

@app.post("/voice/customer-service")
async def customer_service_call(
    audio: UploadFile = File(...),
    user_id: str = Form(...),
    language: str = Form(default="es_mx")
):
    """Customer service voice call with premium OpenAI voice"""
    
    if audio.content_type not in ["audio/wav", "audio/mp3", "audio/mpeg", "audio/webm"]:
        raise HTTPException(status_code=400, detail="Invalid audio format")
    
    try:
        lang = Language.SPANISH_MX if language == "es_mx" else Language.ENGLISH
        audio_data = await audio.read()
        
        agent = agents[AgentType.CUSTOMER_SERVICE]
        response = await agent.handle_customer_service_call(audio_data, user_id, lang)
        
        return Response(
            content=response.audio_data,
            media_type="audio/mp3",
            headers={
                "X-Transcript": response.text[:100],
                "X-Duration-Ms": str(response.duration_ms),
                "X-Cost": str(response.cost),
                "X-Voice-Tier": response.tier,
                "X-Provider": response.provider
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/voice/sales")
async def sales_call(
    audio: UploadFile = File(...),
    prospect_id: str = Form(...),
    language: str = Form(default="es_mx")
):
    """Sales voice call with premium persuasive voice"""
    
    try:
        lang = Language.SPANISH_MX if language == "es_mx" else Language.ENGLISH
        audio_data = await audio.read()
        
        agent = agents[AgentType.SALES]
        response = await agent.handle_sales_call(audio_data, prospect_id, lang)
        
        return Response(
            content=response.audio_data,
            media_type="audio/mp3",
            headers={
                "X-Transcript": response.text[:100],
                "X-Duration-Ms": str(response.duration_ms),
                "X-Cost": str(response.cost),
                "X-Voice-Tier": response.tier,
                "X-Provider": response.provider
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/voice/rag")
async def internal_rag_query(
    audio: UploadFile = File(...),
    employee_id: str = Form(...),
    language: str = Form(default="es_mx")
):
    """Internal RAG query with standard voice"""
    
    try:
        lang = Language.SPANISH_MX if language == "es_mx" else Language.ENGLISH
        audio_data = await audio.read()
        
        agent = agents[AgentType.RAG_ASSISTANT]
        response = await agent.handle_internal_rag_query(audio_data, employee_id, lang)
        
        return Response(
            content=response.audio_data,
            media_type="audio/mp3",
            headers={
                "X-Transcript": response.text[:100],
                "X-Duration-Ms": str(response.duration_ms),
                "X-Cost": str(response.cost),
                "X-Voice-Tier": response.tier,
                "X-Provider": response.provider
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.get("/voice/config")
async def get_voice_config():
    """Get current voice configuration"""
    
    sample_agent = agents[AgentType.CUSTOMER_SERVICE]
    
    return {
        "voice_costs": sample_agent.voice_manager.get_voice_costs(),
        "available_voices": sample_agent.voice_manager.get_available_voices(),
        "agent_types": [agent.value for agent in AgentType],
        "languages": [lang.value for lang in Language],
        "tiers": [tier.value for tier in VoiceTier]
    }

@app.post("/voice/test")
async def test_voice_generation(
    text: str = Form(...),
    agent_type: str = Form(default="customer_service"),
    language: str = Form(default="es_mx")
):
    """Test voice generation without audio input"""
    
    try:
        agent_enum = AgentType(agent_type)
        lang_enum = Language.SPANISH_MX if language == "es_mx" else Language.ENGLISH
        
        agent = agents[agent_enum]
        response = await agent.voice_manager.generate_speech(text, agent_enum, lang_enum)
        
        return Response(
            content=response.audio_data,
            media_type="audio/mp3",
            headers={
                "X-Text": text,
                "X-Duration-Ms": str(response.duration_ms),
                "X-Cost": str(response.cost),
                "X-Voice-Tier": response.tier,
                "X-Provider": response.provider,
                "X-Voice-Used": response.voice_used
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
