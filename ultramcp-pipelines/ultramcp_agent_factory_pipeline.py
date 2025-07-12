"""
UltraMCP Agent Factory Pipeline for Open WebUI
Enables users to create, manage, and deploy AI agents directly from the WebUI

Features:
- Create agents from templates (UltraMCP, LangChain, CrewAI, AutoGen)
- Real-time agent quality validation
- Agent deployment and management
- Agent conversation routing
- Template customization
"""

import os
import json
import asyncio
import httpx
from typing import List, Dict, Any, Optional, Iterator
from pydantic import BaseModel

class Pipeline:
    """UltraMCP Agent Factory Pipeline"""
    
    class Valves(BaseModel):
        """Pipeline configuration"""
        ultramcp_agent_factory_url: str = "http://ultramcp-agent-factory:8014"
        enable_agent_creation: bool = True
        enable_agent_chat: bool = True
        default_framework: str = "ultramcp"
        available_frameworks: List[str] = ["ultramcp", "langchain", "crewai", "autogen"]
        agent_creation_commands: List[str] = ["/create-agent", "/agent", "/new-agent"]
        agent_chat_commands: List[str] = ["/chat-agent", "/agent-chat", "/talk-to"]
        enable_quality_validation: bool = True
        auto_deploy_agents: bool = False
        timeout_seconds: int = 300
        
    def __init__(self):
        self.name = "UltraMCP Agent Factory"
        self.valves = self.Valves(
            **{k: os.getenv(k.upper(), v) for k, v in self.Valves().dict().items()}
        )
        self.active_agents_cache = {}
        
    async def on_startup(self):
        """Initialize pipeline"""
        print(f"🤖 UltraMCP Agent Factory Pipeline initialized")
        print(f"🏭 Factory URL: {self.valves.ultramcp_agent_factory_url}")
        await self._load_active_agents()
        
    async def on_shutdown(self):
        """Cleanup"""
        print("🤖 UltraMCP Agent Factory Pipeline shutting down")
        
    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process incoming requests"""
        
        if "metadata" not in body:
            body["metadata"] = {}
            
        # Add Agent Factory metadata
        body["metadata"]["agent_factory_available"] = True
        body["metadata"]["available_frameworks"] = self.valves.available_frameworks
        body["metadata"]["active_agents"] = list(self.active_agents_cache.keys())
        
        # Check for agent commands
        messages = body.get("messages", [])
        if messages:
            last_message = messages[-1].get("content", "").lower()
            
            # Detect agent creation commands
            is_creation_command = any(cmd in last_message for cmd in self.valves.agent_creation_commands)
            is_chat_command = any(cmd in last_message for cmd in self.valves.agent_chat_commands)
            
            body["metadata"]["is_agent_creation"] = is_creation_command
            body["metadata"]["is_agent_chat"] = is_chat_command
            
        return body
        
    async def pipe(self, user_message: str, model_id: str, messages: List[dict], body: dict) -> Iterator[str]:
        """Main pipeline processing"""
        
        try:
            metadata = body.get("metadata", {})
            
            if metadata.get("is_agent_creation", False):
                async for chunk in self._handle_agent_creation(user_message):
                    yield chunk
                    
            elif metadata.get("is_agent_chat", False):
                async for chunk in self._handle_agent_chat(user_message, messages):
                    yield chunk
                    
            else:
                # Check if user is trying to chat with a specific agent
                agent_name = self._extract_agent_name(user_message)
                if agent_name and agent_name in self.active_agents_cache:
                    async for chunk in self._chat_with_agent(agent_name, user_message):
                        yield chunk
                else:
                    # Pass through to normal model
                    yield f"💡 **Tip:** Use `/create-agent` to create custom agents or `/chat-agent <name>` to talk to existing agents.\n\n"
                    yield f"Available agents: {', '.join(self.active_agents_cache.keys()) if self.active_agents_cache else 'None'}\n\n"
                    yield "---\n\n"
                    
        except Exception as e:
            yield f"❌ **Agent Factory Error:** {str(e)}\n\n"
            
    async def _handle_agent_creation(self, user_message: str) -> Iterator[str]:
        """Handle agent creation requests"""
        
        yield "🏭 **UltraMCP Agent Factory - Creating Custom Agent**\n\n"
        
        # Parse creation parameters
        params = self._parse_creation_params(user_message)
        
        if not params.get("agent_type"):
            yield "Please specify an agent type. Available types:\n"
            yield "- `customer-support` - Customer service agent\n"
            yield "- `research-analyst` - Research and analysis agent\n"
            yield "- `code-reviewer` - Code review and security agent\n"
            yield "- `creative` - Creative writing and content agent\n"
            yield "- `business` - Business strategy and analysis agent\n\n"
            yield "**Example:** `/create-agent customer-support name=MySupport framework=ultramcp`\n"
            return
            
        yield f"**Agent Type:** {params['agent_type']}\n"
        yield f"**Framework:** {params.get('framework', self.valves.default_framework)}\n"
        yield f"**Name:** {params.get('name', f'agent-{params['agent_type'][:8]}')}\n\n"
        
        try:
            async with httpx.AsyncClient(timeout=self.valves.timeout_seconds) as client:
                # Create agent request
                creation_request = {
                    "agent_type": params["agent_type"],
                    "framework": params.get("framework", self.valves.default_framework),
                    "name": params.get("name"),
                    "deploy_immediately": self.valves.auto_deploy_agents,
                    "run_tests": self.valves.enable_quality_validation,
                    "customization": params.get("customization", {})
                }
                
                yield "🔨 **Creating agent...**\n\n"
                
                response = await client.post(
                    f"{self.valves.ultramcp_agent_factory_url}/agents/create",
                    json=creation_request
                )
                
                if response.status_code == 200:
                    result = response.json()
                    agent_id = result.get("agent_id")
                    
                    yield f"✅ **Agent created successfully!**\n"
                    yield f"**Agent ID:** `{agent_id}`\n\n"
                    
                    if self.valves.enable_quality_validation:
                        yield "🧪 **Running quality validation...**\n\n"
                        await asyncio.sleep(2)  # Allow time for validation
                        
                        # Check validation results
                        validation_response = await client.get(
                            f"{self.valves.ultramcp_agent_factory_url}/agents/{agent_id}/validation"
                        )
                        
                        if validation_response.status_code == 200:
                            validation_data = validation_response.json()
                            report = validation_data.get("validation_report", {})
                            
                            score = report.get("overall_score", 0)
                            certification = report.get("certification", "unknown")
                            
                            yield f"**Quality Score:** {score:.2f}/1.00\n"
                            yield f"**Certification:** {certification.upper()}\n\n"
                            
                            if score >= 0.8:
                                yield "🏆 **High quality agent ready for deployment!**\n\n"
                            elif score >= 0.6:
                                yield "⚠️ **Agent meets minimum standards but could be improved**\n\n"
                            else:
                                yield "❌ **Agent needs improvement before deployment**\n\n"
                                
                    # Update cache
                    await self._load_active_agents()
                    
                    yield f"**Usage:** Type `/chat-agent {params.get('name', agent_id[:8])}` to start chatting with your agent.\n"
                    
                else:
                    yield f"❌ **Agent creation failed:** HTTP {response.status_code}\n"
                    yield f"Error: {response.text}\n"
                    
        except Exception as e:
            yield f"❌ **Creation error:** {str(e)}\n"
            
    async def _handle_agent_chat(self, user_message: str, messages: List[dict]) -> Iterator[str]:
        """Handle agent chat requests"""
        
        # Extract agent name and message
        parts = user_message.split(" ", 2)
        if len(parts) < 2:
            yield "❌ **Please specify agent name:** `/chat-agent <agent-name> <message>`\n"
            yield f"Available agents: {', '.join(self.active_agents_cache.keys())}\n"
            return
            
        agent_name = parts[1]
        message = parts[2] if len(parts) > 2 else "Hello"
        
        await self._chat_with_agent(agent_name, message)
        
    async def _chat_with_agent(self, agent_name: str, message: str) -> Iterator[str]:
        """Chat with a specific agent"""
        
        if agent_name not in self.active_agents_cache:
            yield f"❌ **Agent '{agent_name}' not found.**\n"
            yield f"Available agents: {', '.join(self.active_agents_cache.keys())}\n"
            return
            
        agent_info = self.active_agents_cache[agent_name]
        agent_id = agent_info["agent_id"]
        
        yield f"🤖 **Chatting with {agent_name}** (ID: {agent_id[:8]}...)\n\n"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Get agent config for enhanced chat
                config_response = await client.get(
                    f"{self.valves.ultramcp_agent_factory_url}/agents/{agent_id}"
                )
                
                if config_response.status_code == 200:
                    agent_data = config_response.json()
                    
                    # Send message to agent (simulate agent chat)
                    # In a real implementation, this would route to the deployed agent
                    yield f"**{agent_name}:** {self._simulate_agent_response(message, agent_data)}\n\n"
                    
                    yield f"*Agent Type: {agent_data.get('type', 'Unknown')}*\n"
                    yield f"*Framework: {agent_data.get('framework', 'Unknown')}*\n"
                    
                else:
                    yield f"❌ **Could not retrieve agent information**\n"
                    
        except Exception as e:
            yield f"❌ **Chat error:** {str(e)}\n"
            
    async def _load_active_agents(self):
        """Load active agents from the factory"""
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.valves.ultramcp_agent_factory_url}/agents"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    agents = data.get("agents", [])
                    
                    self.active_agents_cache = {}
                    for agent in agents:
                        name = agent.get("name", agent.get("agent_id", "unknown"))
                        self.active_agents_cache[name] = agent
                        
        except Exception as e:
            print(f"Failed to load active agents: {e}")
            
    def _parse_creation_params(self, message: str) -> Dict[str, Any]:
        """Parse agent creation parameters from message"""
        
        params = {}
        
        # Extract agent type (first parameter after command)
        parts = message.split()
        if len(parts) > 1:
            params["agent_type"] = parts[1]
            
        # Extract named parameters
        import re
        
        # name=value pattern
        name_match = re.search(r"name=(\S+)", message)
        if name_match:
            params["name"] = name_match.group(1)
            
        # framework=value pattern
        framework_match = re.search(r"framework=(\S+)", message)
        if framework_match:
            params["framework"] = framework_match.group(1)
            
        return params
        
    def _extract_agent_name(self, message: str) -> Optional[str]:
        """Extract agent name from message"""
        
        # Look for @agent_name pattern
        import re
        at_match = re.search(r"@(\w+)", message)
        if at_match:
            return at_match.group(1)
            
        return None
        
    def _simulate_agent_response(self, message: str, agent_data: Dict[str, Any]) -> str:
        """Simulate agent response based on agent type"""
        
        agent_type = agent_data.get("type", "generic")
        
        if "customer" in agent_type:
            return f"Thank you for contacting our support team. I understand you're asking about: {message[:50]}... How can I help you resolve this issue?"
            
        elif "research" in agent_type:
            return f"I'll analyze this research question: {message[:50]}... Let me gather relevant data and provide you with comprehensive insights."
            
        elif "code" in agent_type:
            return f"I'll review this code-related query: {message[:50]}... Let me check for best practices, security issues, and optimization opportunities."
            
        elif "creative" in agent_type:
            return f"Interesting creative challenge: {message[:50]}... Let me generate some innovative ideas and concepts for you."
            
        elif "business" in agent_type:
            return f"Analyzing this business question: {message[:50]}... I'll provide strategic insights and actionable recommendations."
            
        else:
            return f"I'm processing your request: {message[:50]}... Let me provide you with a comprehensive response."