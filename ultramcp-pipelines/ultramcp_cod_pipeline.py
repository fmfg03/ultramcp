"""
UltraMCP Chain-of-Debate Pipeline for Open WebUI
Integrates UltraMCP's Chain-of-Debate Protocol directly into the WebUI interface

This pipeline enables users to:
- Run multi-LLM debates through the WebUI
- Choose between local-only, hybrid, and API-based debates
- Get consensus-driven responses with enhanced quality
- Access UltraMCP's sophisticated reasoning capabilities
"""

import os
import json
import asyncio
import httpx
from typing import List, Dict, Any, Optional, Iterator, Generator
from pydantic import BaseModel

class Pipeline:
    """UltraMCP Chain-of-Debate Pipeline"""
    
    class Valves(BaseModel):
        """Pipeline configuration valves"""
        ultramcp_cod_url: str = "http://ultramcp-cod-service:8001"
        ultramcp_local_models_url: str = "http://ultramcp-local-models-orchestrator:8012"
        enable_cod_by_default: bool = True
        default_cod_mode: str = "local"  # local, hybrid, api, privacy
        default_participants: List[str] = ["qwen2.5:14b", "llama3.1:8b", "deepseek-coder:6.7b"]
        default_rounds: int = 2
        cod_trigger_keywords: List[str] = ["debate", "discuss", "analyze", "compare", "evaluate"]
        quality_threshold: float = 0.75
        enable_consensus_validation: bool = True
        enable_fallback_to_direct: bool = True
        timeout_seconds: int = 120
        
    def __init__(self):
        self.name = "UltraMCP Chain-of-Debate"
        self.valves = self.Valves(
            **{k: os.getenv(k.upper(), v) for k, v in self.Valves().dict().items()}
        )
        
    async def on_startup(self):
        """Initialize pipeline on startup"""
        print(f"🎭 UltraMCP Chain-of-Debate Pipeline initialized")
        print(f"🔗 CoD Service: {self.valves.ultramcp_cod_url}")
        print(f"🤖 Local Models: {self.valves.ultramcp_local_models_url}")
        
    async def on_shutdown(self):
        """Cleanup on shutdown"""
        print("🎭 UltraMCP Chain-of-Debate Pipeline shutting down")
        
    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process incoming requests and enhance with CoD metadata"""
        
        # Add UltraMCP metadata to the request
        if "metadata" not in body:
            body["metadata"] = {}
            
        body["metadata"]["ultramcp_cod_available"] = True
        body["metadata"]["cod_modes"] = ["local", "hybrid", "api", "privacy"]
        body["metadata"]["local_models"] = self.valves.default_participants
        
        # Check if user wants to use CoD
        messages = body.get("messages", [])
        if messages:
            last_message = messages[-1].get("content", "").lower()
            
            # Detect CoD triggers
            should_use_cod = any(keyword in last_message for keyword in self.valves.cod_trigger_keywords)
            
            # Check for explicit CoD commands
            if last_message.startswith("/cod") or last_message.startswith("/debate"):
                should_use_cod = True
                body["metadata"]["explicit_cod_request"] = True
                
            body["metadata"]["should_use_cod"] = should_use_cod or self.valves.enable_cod_by_default
            
        return body
        
    async def pipe(self, user_message: str, model_id: str, messages: List[dict], body: dict) -> Iterator[str]:
        """Main pipeline processing with Chain-of-Debate integration"""
        
        try:
            # Check if we should use Chain-of-Debate
            metadata = body.get("metadata", {})
            should_use_cod = metadata.get("should_use_cod", False)
            explicit_request = metadata.get("explicit_cod_request", False)
            
            # Extract CoD parameters from user message if explicit request
            cod_params = self._extract_cod_parameters(user_message) if explicit_request else {}
            
            if should_use_cod:
                yield "🎭 **Initiating UltraMCP Chain-of-Debate Protocol...**\n\n"
                
                async for chunk in self._run_chain_of_debate(user_message, messages, cod_params):
                    yield chunk
            else:
                # Fallback to direct model response
                async for chunk in self._run_direct_response(user_message, model_id, messages, body):
                    yield chunk
                    
        except Exception as e:
            error_msg = f"❌ **UltraMCP CoD Pipeline Error:** {str(e)}\n\n"
            
            if self.valves.enable_fallback_to_direct:
                yield error_msg
                yield "🔄 **Falling back to direct model response...**\n\n"
                async for chunk in self._run_direct_response(user_message, model_id, messages, body):
                    yield chunk
            else:
                yield error_msg
                yield "Please try again or contact your administrator."
                
    async def _run_chain_of_debate(self, user_message: str, messages: List[dict], params: Dict[str, Any]) -> Iterator[str]:
        """Run Chain-of-Debate Protocol"""
        
        # Extract debate topic
        topic = params.get("topic", user_message)
        mode = params.get("mode", self.valves.default_cod_mode)
        participants = params.get("participants", self.valves.default_participants)
        rounds = params.get("rounds", self.valves.default_rounds)
        
        yield f"**Topic:** {topic}\n"
        yield f"**Mode:** {mode.upper()}\n"
        yield f"**Participants:** {', '.join(participants)}\n"
        yield f"**Rounds:** {rounds}\n\n"
        
        try:
            async with httpx.AsyncClient(timeout=self.valves.timeout_seconds) as client:
                # Prepare CoD request
                cod_request = {
                    "topic": topic,
                    "participants": participants,
                    "rounds": rounds,
                    "mode": mode,
                    "context": {
                        "conversation_history": messages[-3:] if len(messages) > 3 else messages,
                        "user_preferences": params
                    }
                }
                
                yield "🤔 **Starting debate among AI models...**\n\n"
                
                # Call UltraMCP CoD service
                response = await client.post(
                    f"{self.valves.ultramcp_cod_url}/debate",
                    json=cod_request
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    yield "## 🎯 **Debate Results**\n\n"
                    
                    # Show debate rounds if available
                    if "rounds" in result:
                        for i, round_data in enumerate(result["rounds"], 1):
                            yield f"### Round {i}\n"
                            for participant in round_data.get("participants", []):
                                model = participant.get("model", "Unknown")
                                argument = participant.get("argument", "No argument")
                                yield f"**{model}:** {argument}\n\n"
                    
                    # Show consensus
                    consensus = result.get("consensus", {})
                    if consensus:
                        yield "## 🏆 **Consensus**\n\n"
                        yield f"{consensus.get('summary', 'No consensus reached')}\n\n"
                        
                        # Show confidence and quality metrics
                        confidence = consensus.get("confidence", 0)
                        quality_score = result.get("quality_score", 0)
                        
                        yield f"**Confidence:** {confidence:.1%}\n"
                        yield f"**Quality Score:** {quality_score:.2f}\n\n"
                        
                        # Show reasoning if available
                        if "reasoning" in consensus:
                            yield "### 🧠 **Reasoning**\n\n"
                            yield f"{consensus['reasoning']}\n\n"
                            
                    else:
                        yield "❌ **No consensus reached in debate**\n\n"
                        
                else:
                    yield f"❌ **CoD Service Error:** HTTP {response.status_code}\n\n"
                    yield "🔄 **Falling back to direct response...**\n\n"
                    
                    # Fallback to local model
                    async for chunk in self._call_local_model(user_message):
                        yield chunk
                        
        except Exception as e:
            yield f"❌ **Chain-of-Debate Error:** {str(e)}\n\n"
            raise
            
    async def _run_direct_response(self, user_message: str, model_id: str, messages: List[dict], body: dict) -> Iterator[str]:
        """Run direct model response without CoD"""
        
        try:
            # Use UltraMCP Local Models Orchestrator
            async with httpx.AsyncClient(timeout=60.0) as client:
                request_data = {
                    "prompt": user_message,
                    "model": model_id,
                    "context": {
                        "conversation_history": messages,
                        "task_type": "direct_chat"
                    }
                }
                
                response = await client.post(
                    f"{self.valves.ultramcp_local_models_url}/generate",
                    json=request_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    model_response = result.get("response", "No response generated")
                    
                    # Stream the response
                    for chunk in model_response.split(" "):
                        yield f"{chunk} "
                        await asyncio.sleep(0.01)  # Simulate streaming
                        
                else:
                    yield f"❌ **Model Error:** HTTP {response.status_code}"
                    
        except Exception as e:
            yield f"❌ **Direct Response Error:** {str(e)}"
            
    async def _call_local_model(self, prompt: str) -> Iterator[str]:
        """Fallback to local model call"""
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.valves.ultramcp_local_models_url}/generate",
                    json={
                        "prompt": prompt,
                        "model": "qwen2.5:14b",
                        "task_type": "fallback"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    model_response = result.get("response", "Fallback response not available")
                    
                    for chunk in model_response.split(" "):
                        yield f"{chunk} "
                        await asyncio.sleep(0.01)
                        
        except Exception:
            yield "❌ Fallback model not available"
            
    def _extract_cod_parameters(self, message: str) -> Dict[str, Any]:
        """Extract CoD parameters from user message"""
        
        params = {}
        
        # Extract mode
        if "local" in message.lower():
            params["mode"] = "local"
        elif "hybrid" in message.lower():
            params["mode"] = "hybrid"
        elif "privacy" in message.lower():
            params["mode"] = "privacy"
        elif "api" in message.lower():
            params["mode"] = "api"
            
        # Extract topic (text after /cod or /debate command)
        if message.startswith("/cod") or message.startswith("/debate"):
            parts = message.split(" ", 1)
            if len(parts) > 1:
                params["topic"] = parts[1]
                
        # Extract rounds
        import re
        rounds_match = re.search(r"(\d+)\s*rounds?", message.lower())
        if rounds_match:
            params["rounds"] = int(rounds_match.group(1))
            
        return params