import asyncio
import time
import os
from typing import Dict, Optional, List, Any
from datetime import datetime
import json

# Langwatch integration
try:
    import langwatch
    from langwatch.types import ChatMessage
    LANGWATCH_AVAILABLE = True
except ImportError:
    LANGWATCH_AVAILABLE = False

from voice_manager_cpu_optimized import CPUOptimizedVoiceManager
from voice_types import *

class MCPVoiceAgent:
    """MCP Voice Agent with comprehensive Langwatch monitoring"""
    
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.voice_manager = CPUOptimizedVoiceManager()
        self.conversation_history = {}
        
        # Agent-specific configurations
        self.agent_configs = {
            AgentType.CUSTOMER_SERVICE: {
                "system_prompt": "Eres un asistente de servicio al cliente profesional y empático. Ayuda a resolver problemas y consultas de manera eficiente.",
                "voice": "nova",
                "temperature": 0.7,
                "max_tokens": 150
            },
            AgentType.SALES: {
                "system_prompt": "Eres un consultor de ventas experto. Ayuda a los clientes a encontrar las mejores soluciones para sus necesidades.",
                "voice": "alloy",
                "temperature": 0.8,
                "max_tokens": 200
            },
            AgentType.RAG_ASSISTANT: {
                "system_prompt": "Eres un asistente inteligente con acceso a una base de conocimientos. Proporciona respuestas precisas y bien fundamentadas.",
                "voice": "echo",
                "temperature": 0.6,
                "max_tokens": 250
            }
        }
        
        print(f"✅ MCP Voice Agent initialized: {agent_type.value}")
    
    def _get_langwatch_tracker(self):
        """Get Langwatch tracker if available"""
        if LANGWATCH_AVAILABLE and hasattr(langwatch, 'get_current_trace'):
            return langwatch.get_current_trace()
        return None
    
    async def process_voice_call(self, audio_data: bytes, user_id: str, language: str, trace_id: str, context: str = "") -> Dict[str, Any]:
        """Process complete voice call with Langwatch monitoring"""
        
        config = self.agent_configs[self.agent_type]
        
        try:
            # Step 1: Speech-to-Text with monitoring
            stt_start = time.time()
            transcript = await self._speech_to_text_with_monitoring(audio_data, language, trace_id)
            stt_duration = time.time() - stt_start
            
            # Step 2: LLM Processing with monitoring
            llm_start = time.time()
            response_text = await self._process_with_llm_monitoring(
                transcript, user_id, language, context, config, trace_id
            )
            llm_duration = time.time() - llm_start
            
            # Step 3: Text-to-Speech with monitoring
            tts_start = time.time()
            audio_response = await self._text_to_speech_with_monitoring(
                response_text, config["voice"], language, trace_id
            )
            tts_duration = time.time() - tts_start
            
            # Track overall performance metrics
            await self._track_overall_performance(trace_id, {
                "stt_duration": stt_duration,
                "llm_duration": llm_duration,
                "tts_duration": tts_duration,
                "total_duration": stt_duration + llm_duration + tts_duration,
                "transcript_length": len(transcript),
                "response_length": len(response_text),
                "audio_size": len(audio_response)
            })
            
            return {
                "audio": audio_response,
                "transcript": transcript,
                "response": response_text,
                "metadata": {
                    "agent_type": self.agent_type.value,
                    "language": language,
                    "trace_id": trace_id,
                    "performance": {
                        "stt_ms": stt_duration * 1000,
                        "llm_ms": llm_duration * 1000,
                        "tts_ms": tts_duration * 1000,
                        "total_ms": (stt_duration + llm_duration + tts_duration) * 1000
                    }
                }
            }
            
        except Exception as e:
            await self._track_error(trace_id, str(e), "voice_processing")
            raise e
    
    async def _speech_to_text_with_monitoring(self, audio_data: bytes, language: str, trace_id: str) -> str:
        """Speech-to-Text with Langwatch monitoring"""
        
        if LANGWATCH_AVAILABLE:
            with langwatch.span(
                name="voice_speech_to_text",
                type="tool",
                input={"audio_size": len(audio_data), "language": language},
                metadata={
                    "audio_size_mb": len(audio_data) / (1024 * 1024),
                    "language": language,
                    "model": "whisper-1"
                }
            ) as span:
                try:
                    transcript = await self.voice_manager.speech_to_text(audio_data, language)
                    
                    span.update(
                        output={"transcript": transcript, "length": len(transcript)},
                        metrics={
                            "transcript_length": len(transcript),
                            "words_count": len(transcript.split()),
                            "audio_to_text_ratio": len(transcript) / len(audio_data) * 1000
                        }
                    )
                    
                    return transcript
                    
                except Exception as e:
                    span.update(error=str(e), status="error")
                    raise e
        else:
            return await self.voice_manager.speech_to_text(audio_data, language)
    
    async def _process_with_llm_monitoring(self, transcript: str, user_id: str, language: str, context: str, config: Dict, trace_id: str) -> str:
        """Process with LLM and Langwatch monitoring"""
        
        # Build conversation context
        conversation_key = f"{user_id}_{self.agent_type.value}"
        if conversation_key not in self.conversation_history:
            self.conversation_history[conversation_key] = []
        
        # Add context if provided
        system_prompt = config["system_prompt"]
        if context:
            system_prompt += f"\n\nContexto adicional: {context}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history[conversation_key][-5:],  # Last 5 messages for context
            {"role": "user", "content": transcript}
        ]
        
        if LANGWATCH_AVAILABLE:
            # Convert to Langwatch format
            chat_messages = [
                ChatMessage(role=msg["role"], content=msg["content"])
                for msg in messages
            ]
            
            with langwatch.span(
                name="voice_llm_processing",
                type="llm",
                input=chat_messages,
                model="gpt-3.5-turbo",
                metadata={
                    "agent_type": self.agent_type.value,
                    "language": language,
                    "context_provided": bool(context),
                    "conversation_length": len(self.conversation_history[conversation_key]),
                    "temperature": config["temperature"],
                    "max_tokens": config["max_tokens"]
                }
            ) as span:
                try:
                    response = await self.voice_manager.generate_response(
                        messages, 
                        temperature=config["temperature"],
                        max_tokens=config["max_tokens"]
                    )
                    
                    span.update(
                        output=response,
                        metrics={
                            "response_length": len(response),
                            "response_words": len(response.split()),
                            "input_to_output_ratio": len(response) / len(transcript) if transcript else 0
                        }
                    )
                    
                    # Update conversation history
                    self.conversation_history[conversation_key].extend([
                        {"role": "user", "content": transcript},
                        {"role": "assistant", "content": response}
                    ])
                    
                    return response
                    
                except Exception as e:
                    span.update(error=str(e), status="error")
                    raise e
        else:
            response = await self.voice_manager.generate_response(
                messages,
                temperature=config["temperature"],
                max_tokens=config["max_tokens"]
            )
            
            # Update conversation history
            self.conversation_history[conversation_key].extend([
                {"role": "user", "content": transcript},
                {"role": "assistant", "content": response}
            ])
            
            return response
    
    async def _text_to_speech_with_monitoring(self, text: str, voice: str, language: str, trace_id: str) -> bytes:
        """Text-to-Speech with Langwatch monitoring"""
        
        if LANGWATCH_AVAILABLE:
            with langwatch.span(
                name="voice_text_to_speech",
                type="tool",
                input={"text": text, "voice": voice, "language": language},
                metadata={
                    "text_length": len(text),
                    "voice_model": voice,
                    "language": language,
                    "words_count": len(text.split())
                }
            ) as span:
                try:
                    audio_data = await self.voice_manager.text_to_speech(text, voice, language)
                    
                    # Estimate audio duration (rough calculation)
                    estimated_duration = len(text.split()) * 0.6  # ~0.6 seconds per word
                    
                    span.update(
                        output={
                            "audio_size": len(audio_data),
                            "estimated_duration": estimated_duration
                        },
                        metrics={
                            "audio_size_kb": len(audio_data) / 1024,
                            "estimated_duration": estimated_duration,
                            "text_to_audio_ratio": len(audio_data) / len(text),
                            "generation_efficiency": len(text) / len(audio_data) * 1000
                        }
                    )
                    
                    return audio_data
                    
                except Exception as e:
                    span.update(error=str(e), status="error")
                    raise e
        else:
            return await self.voice_manager.text_to_speech(text, voice, language)
    
    async def _track_overall_performance(self, trace_id: str, metrics: Dict[str, Any]):
        """Track overall performance metrics"""
        
        if LANGWATCH_AVAILABLE:
            try:
                with langwatch.span(
                    name="voice_call_performance",
                    type="tool",
                    input={"trace_id": trace_id},
                    output=metrics,
                    metadata={
                        "agent_type": self.agent_type.value,
                        "performance_summary": {
                            "total_duration_ms": metrics["total_duration"] * 1000,
                            "stt_percentage": (metrics["stt_duration"] / metrics["total_duration"]) * 100,
                            "llm_percentage": (metrics["llm_duration"] / metrics["total_duration"]) * 100,
                            "tts_percentage": (metrics["tts_duration"] / metrics["total_duration"]) * 100
                        }
                    }
                ) as span:
                    
                    # Calculate performance scores
                    performance_score = 100
                    if metrics["total_duration"] > 5:  # Slow if > 5 seconds
                        performance_score -= 20
                    if metrics["stt_duration"] > 2:  # STT should be < 2 seconds
                        performance_score -= 15
                    if metrics["llm_duration"] > 2:  # LLM should be < 2 seconds
                        performance_score -= 15
                    if metrics["tts_duration"] > 1:  # TTS should be < 1 second
                        performance_score -= 10
                    
                    span.update(
                        metrics={
                            "performance_score": max(0, performance_score),
                            "total_latency": metrics["total_duration"],
                            "stt_latency": metrics["stt_duration"],
                            "llm_latency": metrics["llm_duration"],
                            "tts_latency": metrics["tts_duration"]
                        }
                    )
                    
            except Exception as e:
                print(f"❌ Error tracking performance: {e}")
    
    async def _track_error(self, trace_id: str, error: str, step: str):
        """Track errors in Langwatch"""
        
        if LANGWATCH_AVAILABLE:
            try:
                with langwatch.span(
                    name=f"voice_error_{step}",
                    type="tool",
                    input={"trace_id": trace_id, "step": step},
                    output={"error": error},
                    metadata={
                        "error_type": "voice_processing_error",
                        "step": step,
                        "agent_type": self.agent_type.value,
                        "timestamp": datetime.now().isoformat()
                    }
                ) as span:
                    span.update(
                        error=error,
                        status="error"
                    )
                    
            except Exception as e:
                print(f"❌ Error tracking error: {e}")
    
    def get_conversation_history(self, user_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a user"""
        conversation_key = f"{user_id}_{self.agent_type.value}"
        return self.conversation_history.get(conversation_key, [])
    
    def clear_conversation_history(self, user_id: str):
        """Clear conversation history for a user"""
        conversation_key = f"{user_id}_{self.agent_type.value}"
        if conversation_key in self.conversation_history:
            del self.conversation_history[conversation_key]
    
    async def get_agent_metrics(self) -> Dict[str, Any]:
        """Get agent-specific metrics"""
        return {
            "agent_type": self.agent_type.value,
            "active_conversations": len(self.conversation_history),
            "langwatch_enabled": LANGWATCH_AVAILABLE and bool(os.getenv("LANGWATCH_API_KEY")),
            "configuration": self.agent_configs[self.agent_type],
            "status": "ready"
        }

