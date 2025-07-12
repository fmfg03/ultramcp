"""
CoD Agent Adapter for Scenario Framework Integration
Wraps UltraMCP Chain-of-Debate agents for testing with Scenario framework
"""

import asyncio
import httpx
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import structlog

# Import from scenario framework
import sys
sys.path.append('/root/scenario/python')
import scenario
from scenario.agent_adapter import AgentAdapter, AgentRole
from scenario.types import AgentInput, AgentReturnTypes

logger = structlog.get_logger(__name__)


class DebatePosition(Enum):
    """Debate positions for CoD agents"""
    PRO = "pro"
    CON = "con"
    MODERATOR = "moderator"
    NEUTRAL = "neutral"


@dataclass
class DebateContext:
    """Context for debate scenarios"""
    round_number: int
    position: DebatePosition
    previous_arguments: List[Dict[str, Any]]
    debate_topic: str
    evidence_required: bool = True
    max_argument_length: int = 500


class CoDAgentAdapter(AgentAdapter):
    """Adapter to integrate UltraMCP CoD agents with Scenario framework"""
    
    role = AgentRole.AGENT
    
    def __init__(
        self,
        agent_id: str,
        position: DebatePosition,
        cod_service_url: str = "http://localhost:8001",
        local_models_url: str = "http://localhost:8012",
        config: Optional[Dict[str, Any]] = None
    ):
        self.agent_id = agent_id
        self.position = position
        self.cod_service_url = cod_service_url
        self.local_models_url = local_models_url
        self.config = config or {}
        
        logger.info(
            "Initialized CoD agent adapter",
            agent_id=agent_id,
            position=position.value
        )
    
    async def call(self, input: AgentInput) -> AgentReturnTypes:
        """Execute CoD agent call through Scenario framework"""
        try:
            # Extract debate context from scenario state
            debate_context = self.extract_debate_context(input.scenario_state)
            
            # Prepare CoD request
            cod_request = {
                "task_id": f"scenario-test-{input.scenario_state.run_id}",
                "topic": debate_context.debate_topic,
                "participants": [self.agent_id],
                "position": self.position.value,
                "context": {
                    "round": debate_context.round_number,
                    "previous_arguments": debate_context.previous_arguments,
                    "evidence_required": debate_context.evidence_required,
                    "max_length": debate_context.max_argument_length
                },
                "messages": [
                    {"role": msg.role, "content": msg.content}
                    for msg in input.messages
                ]
            }
            
            # Call CoD service
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.cod_service_url}/debate",
                    json=cod_request
                )
                response.raise_for_status()
                
                result = response.json()
                
                logger.info(
                    "CoD agent response received",
                    agent_id=self.agent_id,
                    response_length=len(result.get("response", ""))
                )
                
                return result.get("response", "")
                
        except Exception as e:
            logger.error(
                "CoD agent call failed",
                agent_id=self.agent_id,
                error=str(e)
            )
            # Fallback to local models if CoD service fails
            return await self.fallback_to_local_models(input, debate_context)
    
    def extract_debate_context(self, scenario_state) -> DebateContext:
        """Extract debate context from scenario state"""
        messages = scenario_state.messages
        
        # Extract debate topic from first user message
        debate_topic = "General debate"
        for msg in messages:
            if msg.role == "user" and len(msg.content) > 10:
                debate_topic = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                break
        
        # Count rounds based on agent messages
        round_number = len([msg for msg in messages if msg.role == "assistant"]) + 1
        
        # Extract previous arguments
        previous_arguments = []
        for msg in messages:
            if msg.role == "assistant":
                previous_arguments.append({
                    "content": msg.content,
                    "role": msg.role,
                    "timestamp": getattr(msg, "timestamp", None)
                })
        
        return DebateContext(
            round_number=round_number,
            position=self.position,
            previous_arguments=previous_arguments,
            debate_topic=debate_topic,
            evidence_required=self.config.get("evidence_required", True),
            max_argument_length=self.config.get("max_argument_length", 500)
        )
    
    async def fallback_to_local_models(self, input: AgentInput, context: DebateContext) -> str:
        """Fallback to local models if CoD service is unavailable"""
        try:
            # Construct prompt for local model
            position_prompt = f"You are taking the {self.position.value} position in this debate."
            topic_prompt = f"Topic: {context.debate_topic}"
            
            if context.previous_arguments:
                prev_args = "\n".join([
                    f"Previous argument: {arg['content'][:200]}..."
                    for arg in context.previous_arguments[-2:]  # Last 2 arguments
                ])
                context_prompt = f"Previous arguments:\n{prev_args}\n\nYour response:"
            else:
                context_prompt = "Please provide your opening argument:"
            
            full_prompt = f"{position_prompt}\n{topic_prompt}\n{context_prompt}"
            
            # Call local models orchestrator
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    f"{self.local_models_url}/generate",
                    json={
                        "prompt": full_prompt,
                        "task_type": "reasoning",
                        "max_tokens": context.max_argument_length
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get("content", "I apologize, but I cannot provide a response at this time.")
                
        except Exception as e:
            logger.error(
                "Local models fallback failed",
                agent_id=self.agent_id,
                error=str(e)
            )
            return f"Error: Unable to generate response for {self.position.value} position."


class CoDModeratorAdapter(CoDAgentAdapter):
    """Specialized adapter for moderator agents"""
    
    def __init__(self, **kwargs):
        super().__init__(position=DebatePosition.MODERATOR, **kwargs)
    
    async def call(self, input: AgentInput) -> AgentReturnTypes:
        """Moderator-specific logic for managing debate flow"""
        context = self.extract_debate_context(input.scenario_state)
        
        # Check if synthesis is needed
        if context.round_number > 3 and len(context.previous_arguments) >= 4:
            return await self.generate_synthesis(input, context)
        else:
            return await super().call(input)
    
    async def generate_synthesis(self, input: AgentInput, context: DebateContext) -> str:
        """Generate synthesis of debate positions"""
        try:
            synthesis_prompt = f"""
As a debate moderator, synthesize the following arguments on: {context.debate_topic}

Previous arguments:
{chr(10).join([f"- {arg['content'][:150]}..." for arg in context.previous_arguments])}

Provide a balanced synthesis that:
1. Identifies common ground
2. Highlights key disagreements
3. Suggests potential compromise solutions
4. Maintains neutrality
"""
            
            async with httpx.AsyncClient(timeout=25.0) as client:
                response = await client.post(
                    f"{self.local_models_url}/generate",
                    json={
                        "prompt": synthesis_prompt,
                        "task_type": "reasoning",
                        "max_tokens": 400
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                return f"[MODERATOR SYNTHESIS] {result.get('content', '')}"
                
        except Exception as e:
            logger.error("Moderator synthesis failed", error=str(e))
            return "[MODERATOR] I apologize, but I cannot provide a synthesis at this time."


class CoDUserSimulator(AgentAdapter):
    """User simulator for generating realistic debate prompts"""
    
    role = AgentRole.USER
    
    def __init__(self, topics: List[str] = None, local_models_url: str = "http://localhost:8012"):
        self.topics = topics or [
            "climate change policy effectiveness",
            "universal basic income implementation",
            "artificial intelligence regulation",
            "renewable energy transition strategies",
            "healthcare system reform approaches"
        ]
        self.local_models_url = local_models_url
    
    async def call(self, input: AgentInput) -> AgentReturnTypes:
        """Generate realistic user inputs for debate scenarios"""
        try:
            context = input.scenario_state
            
            # If this is the first message, start a debate
            if len(context.messages) == 0:
                import random
                topic = random.choice(self.topics)
                return f"I'd like to have a structured debate about {topic}. Please present your arguments for and against this topic."
            
            # Generate follow-up questions or prompts
            last_messages = context.messages[-2:] if len(context.messages) >= 2 else context.messages
            
            prompt = f"""
Based on this recent debate exchange, generate a thoughtful follow-up question or prompt from a user:

Recent messages:
{chr(10).join([f"{msg.role}: {msg.content[:100]}..." for msg in last_messages])}

Generate a user prompt that:
1. Asks for clarification on specific points
2. Requests evidence for claims made
3. Asks agents to address counterarguments
4. Seeks synthesis or compromise solutions

Keep it under 100 words and make it engaging.
"""
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.local_models_url}/generate",
                    json={
                        "prompt": prompt,
                        "task_type": "general",
                        "max_tokens": 100
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get("content", "Can you elaborate on that point?")
                
        except Exception as e:
            logger.error("User simulation failed", error=str(e))
            return "Can you provide more details about your position?"