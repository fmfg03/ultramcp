#!/usr/bin/env python3
"""
UltraMCP Claudia Integration - Agent Service with MCP Protocol
Enhanced agent management with native UltraMCP service integration and MCP protocol support
"""

import asyncio
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import aiohttp
import logging
from dataclasses import dataclass, asdict
from enum import Enum

# Import MCP protocol components
try:
    from mcp_protocol import MCPServer, MCPTool, MCPResource, MCPPrompt, UltraMCPToolRegistry
    from ultramcp_service_adapters import UltraMCPServiceAdapters
    MCP_AVAILABLE = True
except ImportError as e:
    logging.warning(f"MCP protocol components not available: {e}")
    MCP_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentModel(Enum):
    OPUS = "opus"
    SONNET = "sonnet" 
    HAIKU = "haiku"

class AgentStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class UltraMCPAgent:
    """Enhanced agent with UltraMCP service integration"""
    id: Optional[str] = None
    name: str = ""
    icon: str = "bot"
    system_prompt: str = ""
    default_task: str = ""
    model: str = "sonnet"
    capabilities: Dict[str, Any] = None
    ultramcp_services: List[str] = None
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = {
                "file_read": True,
                "file_write": True,
                "network": True,
                "ultramcp_integration": True
            }
        if self.ultramcp_services is None:
            self.ultramcp_services = []
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()

@dataclass
class AgentExecution:
    """Agent execution tracking with metrics"""
    id: Optional[str] = None
    agent_id: str = ""
    agent_name: str = ""
    task: str = ""
    project_path: str = ""
    session_id: str = ""
    status: str = "pending"
    pid: Optional[int] = None
    services_used: List[str] = None
    metrics: Dict[str, Any] = None
    created_at: str = ""
    completed_at: Optional[str] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.services_used is None:
            self.services_used = []
        if self.metrics is None:
            self.metrics = {}
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

class UltraMCPAgentService:
    """Enhanced agent service with UltraMCP integration"""
    
    def __init__(self, db_path: str = "/root/ultramcp/data/claudia_agents.db"):
        self.db_path = db_path
        self.services = {
            'cod': 'http://sam.chat:8001',
            'asterisk': 'http://sam.chat:8002', 
            'blockoli': 'http://sam.chat:8080',
            'voice': 'http://sam.chat:8004',
            'deepclaude': 'http://sam.chat:8006',
            'control_tower': 'http://sam.chat:8007',
            'memory': 'http://sam.chat:8009',
            'voyage': 'http://sam.chat:8010',
            'ref_tools': 'http://sam.chat:8011'
        }
        self.running_executions: Dict[str, AgentExecution] = {}
        self._init_database()
        self._load_templates()
    
    def _init_database(self):
        """Initialize SQLite database for agent storage"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    icon TEXT NOT NULL,
                    system_prompt TEXT NOT NULL,
                    default_task TEXT,
                    model TEXT NOT NULL,
                    capabilities TEXT NOT NULL,
                    ultramcp_services TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_executions (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    task TEXT NOT NULL,
                    project_path TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    pid INTEGER,
                    services_used TEXT,
                    metrics TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    FOREIGN KEY (agent_id) REFERENCES agents (id)
                )
            """)
            
            conn.commit()
    
    def _load_templates(self):
        """Load pre-built agent templates"""
        self.templates = {
            "ultramcp_security_scanner": UltraMCPAgent(
                name="UltraMCP Security Scanner",
                icon="shield",
                model="opus",
                system_prompt="""You are an advanced security scanner integrated with UltraMCP's Asterisk Security Service.

Your capabilities:
1. Comprehensive vulnerability scanning using OWASP Top 10 and CWE standards
2. Static Application Security Testing (SAST) with AI-powered analysis
3. Integration with Blockoli for code intelligence and pattern recognition
4. Automated threat modeling using STRIDE methodology
5. Real-time security compliance checking (SOC2, HIPAA, GDPR)

When scanning:
- Use Asterisk Security Service for comprehensive vulnerability detection
- Leverage Blockoli Intelligence for code pattern analysis
- Generate detailed security reports with remediation steps
- Prioritize findings by severity and exploitability
- Provide specific code fixes and security improvements

Always provide actionable, specific recommendations.""",
                default_task="Perform comprehensive security scan of the codebase",
                ultramcp_services=["asterisk", "blockoli"],
                capabilities={
                    "file_read": True,
                    "file_write": True,
                    "network": True,
                    "ultramcp_integration": True,
                    "security_scanning": True
                }
            ),
            
            "code_intelligence_analyst": UltraMCPAgent(
                name="Code Intelligence Analyst", 
                icon="code",
                model="sonnet",
                system_prompt="""You are a code intelligence analyst powered by UltraMCP's Blockoli and Memory services.

Your capabilities:
1. Advanced semantic code search and pattern recognition
2. Architecture analysis and technical debt assessment
3. Code quality evaluation and improvement suggestions
4. Integration with Claude Code Memory for context-aware analysis
5. Cross-repository pattern detection and best practices

When analyzing code:
- Use Blockoli Intelligence for semantic understanding
- Leverage Memory Service for historical context and patterns
- Provide architecture insights and improvement recommendations
- Identify code smells, anti-patterns, and technical debt
- Suggest refactoring opportunities and modernization paths
- Generate comprehensive code quality reports

Focus on actionable insights that improve code maintainability and performance.""",
                default_task="Analyze codebase architecture and provide improvement recommendations",
                ultramcp_services=["blockoli", "memory"],
                capabilities={
                    "file_read": True,
                    "file_write": True,
                    "code_analysis": True,
                    "ultramcp_integration": True
                }
            ),
            
            "debate_orchestrator": UltraMCPAgent(
                name="Multi-LLM Debate Orchestrator",
                icon="bot", 
                model="sonnet",
                system_prompt="""You are a debate orchestrator for UltraMCP's Chain-of-Debate Protocol.

Your capabilities:
1. Intelligent multi-LLM debate coordination and facilitation
2. Strategic decision analysis using diverse AI perspectives
3. Consensus building and conflict resolution
4. Integration with local models for cost-effective analysis
5. Real-time debate monitoring and quality assessment

When orchestrating debates:
- Use Chain-of-Debate Service for multi-LLM coordination
- Facilitate productive discussions between different AI models
- Ensure balanced participation and diverse perspectives
- Guide debates toward actionable consensus
- Provide comprehensive analysis of different viewpoints
- Generate executive summaries with clear recommendations

Focus on extracting maximum value from AI collaboration while maintaining debate quality and relevance.""",
                default_task="Orchestrate intelligent debate on strategic decision",
                ultramcp_services=["cod", "memory"],
                capabilities={
                    "debate_orchestration": True,
                    "multi_llm_coordination": True,
                    "ultramcp_integration": True
                }
            ),
            
            "voice_powered_assistant": UltraMCPAgent(
                name="Voice-Powered AI Assistant",
                icon="database",
                model="sonnet", 
                system_prompt="""You are a voice-powered AI assistant integrated with UltraMCP's Voice System.

Your capabilities:
1. Real-time voice interaction and natural conversation
2. Audio transcription and analysis
3. Voice-guided development workflows
4. Integration with all UltraMCP services via voice commands
5. Hands-free coding and project management

When providing voice assistance:
- Use Voice System for natural conversation flow
- Transcribe and understand voice commands accurately
- Execute complex tasks through voice interaction
- Provide audio feedback and confirmations
- Maintain context across voice sessions
- Support multilingual voice interaction

Focus on creating intuitive, hands-free development experiences.""",
                default_task="Provide voice-powered assistance for development tasks",
                ultramcp_services=["voice", "memory", "control_tower"],
                capabilities={
                    "voice_interaction": True,
                    "audio_processing": True,
                    "hands_free_operation": True,
                    "ultramcp_integration": True
                }
            )
        }
    
    async def create_agent(self, agent: UltraMCPAgent) -> UltraMCPAgent:
        """Create a new agent"""
        if not agent.id:
            agent.id = str(uuid.uuid4())
        
        agent.created_at = datetime.utcnow().isoformat()
        agent.updated_at = agent.created_at
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO agents (id, name, icon, system_prompt, default_task, model, 
                                  capabilities, ultramcp_services, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent.id, agent.name, agent.icon, agent.system_prompt,
                agent.default_task, agent.model,
                json.dumps(agent.capabilities),
                json.dumps(agent.ultramcp_services),
                agent.created_at, agent.updated_at
            ))
            conn.commit()
        
        logger.info(f"Created agent: {agent.name} ({agent.id})")
        return agent
    
    async def list_agents(self) -> List[UltraMCPAgent]:
        """List all agents"""
        agents = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, name, icon, system_prompt, default_task, model,
                       capabilities, ultramcp_services, created_at, updated_at
                FROM agents ORDER BY created_at DESC
            """)
            
            for row in cursor.fetchall():
                agent = UltraMCPAgent(
                    id=row[0], name=row[1], icon=row[2], system_prompt=row[3],
                    default_task=row[4], model=row[5],
                    capabilities=json.loads(row[6]) if row[6] else {},
                    ultramcp_services=json.loads(row[7]) if row[7] else [],
                    created_at=row[8], updated_at=row[9]
                )
                agents.append(agent)
        
        return agents
    
    async def get_agent(self, agent_id: str) -> Optional[UltraMCPAgent]:
        """Get agent by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, name, icon, system_prompt, default_task, model,
                       capabilities, ultramcp_services, created_at, updated_at
                FROM agents WHERE id = ?
            """, (agent_id,))
            
            row = cursor.fetchone()
            if row:
                return UltraMCPAgent(
                    id=row[0], name=row[1], icon=row[2], system_prompt=row[3],
                    default_task=row[4], model=row[5],
                    capabilities=json.loads(row[6]) if row[6] else {},
                    ultramcp_services=json.loads(row[7]) if row[7] else [],
                    created_at=row[8], updated_at=row[9]
                )
        return None
    
    async def execute_agent(self, agent_id: str, task: str, project_path: str) -> AgentExecution:
        """Execute an agent with enhanced UltraMCP integration"""
        agent = await self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        execution = AgentExecution(
            agent_id=agent_id,
            agent_name=agent.name,
            task=task,
            project_path=project_path,
            session_id=str(uuid.uuid4()),
            status=AgentStatus.PENDING.value,
            services_used=agent.ultramcp_services.copy()
        )
        
        # Store execution
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO agent_executions 
                (id, agent_id, agent_name, task, project_path, session_id, 
                 status, services_used, metrics, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                execution.id, execution.agent_id, execution.agent_name,
                execution.task, execution.project_path, execution.session_id,
                execution.status, json.dumps(execution.services_used),
                json.dumps(execution.metrics), execution.created_at
            ))
            conn.commit()
        
        # Track running execution
        self.running_executions[execution.id] = execution
        
        # Start execution asynchronously
        asyncio.create_task(self._execute_agent_async(agent, execution))
        
        return execution
    
    async def _execute_agent_async(self, agent: UltraMCPAgent, execution: AgentExecution):
        """Async agent execution with service integration"""
        try:
            execution.status = AgentStatus.RUNNING.value
            await self._update_execution_status(execution)
            
            # Pre-execution: Initialize required services
            await self._initialize_services(agent.ultramcp_services)
            
            # Build enhanced system prompt with service context
            enhanced_prompt = await self._build_enhanced_prompt(agent, execution)
            
            # Execute with service integration
            result = await self._execute_with_services(
                agent, execution, enhanced_prompt
            )
            
            execution.status = AgentStatus.COMPLETED.value
            execution.completed_at = datetime.utcnow().isoformat()
            execution.metrics.update(result.get('metrics', {}))
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            execution.status = AgentStatus.FAILED.value
            execution.completed_at = datetime.utcnow().isoformat()
            execution.metrics['error'] = str(e)
        
        finally:
            await self._update_execution_status(execution)
            if execution.id in self.running_executions:
                del self.running_executions[execution.id]
    
    async def _initialize_services(self, service_names: List[str]):
        """Initialize required UltraMCP services"""
        for service_name in service_names:
            if service_name in self.services:
                try:
                    url = f"{self.services[service_name]}/health"
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=5) as response:
                            if response.status == 200:
                                logger.info(f"Service {service_name} is healthy")
                            else:
                                logger.warning(f"Service {service_name} returned {response.status}")
                except Exception as e:
                    logger.error(f"Failed to check service {service_name}: {e}")
    
    async def _build_enhanced_prompt(self, agent: UltraMCPAgent, execution: AgentExecution) -> str:
        """Build enhanced system prompt with service context"""
        prompt = agent.system_prompt
        
        # Add service availability context
        if agent.ultramcp_services:
            prompt += f"\n\nAvailable UltraMCP Services:\n"
            for service in agent.ultramcp_services:
                if service in self.services:
                    prompt += f"- {service.title()}: {self.services[service]}\n"
        
        # Add project context
        prompt += f"\nProject Context:\n"
        prompt += f"- Project Path: {execution.project_path}\n"
        prompt += f"- Task: {execution.task}\n"
        prompt += f"- Session ID: {execution.session_id}\n"
        
        return prompt
    
    async def _execute_with_services(self, agent: UltraMCPAgent, execution: AgentExecution, prompt: str) -> Dict[str, Any]:
        """Execute agent with enhanced service integration"""
        # This would integrate with Claude Code execution
        # For now, simulate execution with service calls
        
        results = {
            'metrics': {
                'execution_time_ms': 1000,
                'services_called': len(agent.ultramcp_services),
                'success': True
            }
        }
        
        # Simulate service-specific execution
        for service in agent.ultramcp_services:
            if service == 'asterisk':
                # Security scanning
                results['security_scan'] = await self._call_security_service(execution.project_path)
            elif service == 'blockoli':
                # Code intelligence
                results['code_analysis'] = await self._call_code_intelligence(execution.project_path)
            elif service == 'cod':
                # Chain-of-Debate
                results['debate_result'] = await self._call_cod_service(execution.task)
        
        return results
    
    async def _call_security_service(self, project_path: str) -> Dict[str, Any]:
        """Call Asterisk Security Service"""
        try:
            url = f"{self.services['asterisk']}/scan"
            payload = {
                "path": project_path,
                "scan_type": "comprehensive"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=30) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"Security service returned {response.status}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def _call_code_intelligence(self, project_path: str) -> Dict[str, Any]:
        """Call Blockoli Code Intelligence Service"""
        try:
            url = f"{self.services['blockoli']}/analyze"
            payload = {
                "project_path": project_path,
                "analysis_type": "comprehensive"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=30) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"Code intelligence service returned {response.status}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def _call_cod_service(self, topic: str) -> Dict[str, Any]:
        """Call Chain-of-Debate Service"""
        try:
            url = f"{self.services['cod']}/debate"
            payload = {
                "topic": topic,
                "mode": "local",
                "participants": 3
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=60) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"CoD service returned {response.status}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def _update_execution_status(self, execution: AgentExecution):
        """Update execution status in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE agent_executions 
                SET status = ?, metrics = ?, completed_at = ?
                WHERE id = ?
            """, (
                execution.status,
                json.dumps(execution.metrics),
                execution.completed_at,
                execution.id
            ))
            conn.commit()
    
    async def get_agent_templates(self) -> Dict[str, UltraMCPAgent]:
        """Get pre-built agent templates"""
        return self.templates
    
    async def install_template(self, template_name: str) -> UltraMCPAgent:
        """Install a pre-built template as a new agent"""
        if template_name not in self.templates:
            raise ValueError(f"Template {template_name} not found")
        
        template = self.templates[template_name]
        # Create new agent from template
        new_agent = UltraMCPAgent(**asdict(template))
        new_agent.id = None  # Reset ID to create new
        
        return await self.create_agent(new_agent)
    
    async def list_executions(self, limit: int = 50) -> List[AgentExecution]:
        """List recent agent executions"""
        executions = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, agent_id, agent_name, task, project_path, session_id,
                       status, pid, services_used, metrics, created_at, completed_at
                FROM agent_executions 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            for row in cursor.fetchall():
                execution = AgentExecution(
                    id=row[0], agent_id=row[1], agent_name=row[2],
                    task=row[3], project_path=row[4], session_id=row[5],
                    status=row[6], pid=row[7],
                    services_used=json.loads(row[8]) if row[8] else [],
                    metrics=json.loads(row[9]) if row[9] else {},
                    created_at=row[10], completed_at=row[11]
                )
                executions.append(execution)
        
        return executions
    
    async def get_execution_metrics(self) -> Dict[str, Any]:
        """Get execution analytics and metrics"""
        with sqlite3.connect(self.db_path) as conn:
            # Total executions
            cursor = conn.execute("SELECT COUNT(*) FROM agent_executions")
            total_executions = cursor.fetchone()[0]
            
            # Status breakdown
            cursor = conn.execute("""
                SELECT status, COUNT(*) 
                FROM agent_executions 
                GROUP BY status
            """)
            status_breakdown = dict(cursor.fetchall())
            
            # Service usage
            cursor = conn.execute("""
                SELECT services_used, COUNT(*) 
                FROM agent_executions 
                WHERE services_used IS NOT NULL
                GROUP BY services_used
            """)
            service_usage = {}
            for services_json, count in cursor.fetchall():
                services = json.loads(services_json)
                for service in services:
                    service_usage[service] = service_usage.get(service, 0) + count
            
            return {
                'total_executions': total_executions,
                'status_breakdown': status_breakdown,
                'service_usage': service_usage,
                'running_executions': len(self.running_executions)
            }

# FastAPI integration
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(title="UltraMCP Claudia Integration Service")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    agent_service = UltraMCPAgentService()
    
    # Initialize MCP components if available
    mcp_state = {"server": None, "adapters": None}
    
    async def initialize_mcp():
        if MCP_AVAILABLE:
            try:
                mcp_state["server"] = MCPServer()
                mcp_state["adapters"] = UltraMCPServiceAdapters()
                
                # Initialize MCP tools from UltraMCP services
                registry = UltraMCPToolRegistry()
                tools = await registry.create_mcp_tools()
                
                for tool in tools:
                    # Create async handler for each tool
                    def create_handler(tool_name):
                        async def handler(arguments):
                            if tool_name == "ultramcp_security_scan":
                                return await mcp_state["adapters"].execute_security_scan(arguments)
                            elif tool_name == "ultramcp_code_analysis":
                                return await mcp_state["adapters"].execute_code_analysis(arguments)
                            elif tool_name == "ultramcp_ai_debate":
                                return await mcp_state["adapters"].execute_ai_debate(arguments)
                            elif tool_name == "ultramcp_voice_assist":
                                return await mcp_state["adapters"].execute_voice_assist(arguments)
                            else:
                                return {"error": f"Unknown tool: {tool_name}"}
                        return handler
                    
                    tool_handler = create_handler(tool.name)
                    mcp_state["server"].register_tool(tool, tool_handler)
                
                logger.info(f"Initialized MCP server with {len(tools)} tools")
                
            except Exception as e:
                logger.error(f"Failed to initialize MCP components: {e}")
                mcp_state["server"] = None
    
    # Initialize MCP on startup
    @app.on_event("startup")
    async def startup_event():
        await initialize_mcp()
    
    @app.get("/health")
    async def health_check():
        health_status = {"status": "healthy", "service": "claudia-integration"}
        if mcp_state["server"]:
            health_status["mcp_protocol"] = "enabled"
            health_status["mcp_tools"] = len(mcp_state["server"].tools)
        return health_status
    
    @app.post("/agents", response_model=dict)
    async def create_agent(agent_data: dict):
        agent = UltraMCPAgent(**agent_data)
        created_agent = await agent_service.create_agent(agent)
        return asdict(created_agent)
    
    @app.get("/agents")
    async def list_agents():
        agents = await agent_service.list_agents()
        return [asdict(agent) for agent in agents]
    
    @app.get("/agents/templates")
    async def get_templates():
        templates = await agent_service.get_agent_templates()
        return {name: asdict(template) for name, template in templates.items()}
    
    @app.post("/agents/templates/{template_name}/install")
    async def install_template(template_name: str):
        try:
            agent = await agent_service.install_template(template_name)
            return asdict(agent)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    
    @app.post("/agents/{agent_id}/execute")
    async def execute_agent(agent_id: str, execution_data: dict):
        try:
            execution = await agent_service.execute_agent(
                agent_id, 
                execution_data.get("task", ""),
                execution_data.get("project_path", "/root/ultramcp")
            )
            return asdict(execution)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    
    @app.get("/executions")
    async def list_executions(limit: int = 50):
        executions = await agent_service.list_executions(limit)
        return [asdict(execution) for execution in executions]
    
    @app.get("/metrics")
    async def get_metrics():
        return await agent_service.get_execution_metrics()
    
    # MCP Protocol Endpoints
    def get_mcp_server():
        return mcp_state["server"]
    
    @app.get("/mcp/tools")
    async def list_mcp_tools():
        """List all available MCP tools"""
        mcp_server = get_mcp_server()
        if not mcp_server:
            raise HTTPException(status_code=503, detail="MCP protocol not available")
        
        tools_list = []
        for tool in mcp_server.tools.values():
            tools_list.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            })
        return {"tools": tools_list}
        @app.get("/mcp/tools")
        async def list_mcp_tools():
            """List all available MCP tools"""
            tools_list = []
            for tool in mcp_server.tools.values():
                tools_list.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                })
            return {"tools": tools_list}
        
        @app.post("/mcp/tools/{tool_name}/call")
        async def call_mcp_tool(tool_name: str, arguments: dict = None):
            """Call an MCP tool directly via REST API"""
            if tool_name not in mcp_server.tool_handlers:
                raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
            
            try:
                handler = mcp_server.tool_handlers[tool_name]
                result = await handler(arguments or {})
                return {
                    "tool": tool_name,
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")
        
        @app.get("/mcp/resources")
        async def list_mcp_resources():
            """List all available MCP resources"""
            resources_list = []
            for resource in mcp_server.resources.values():
                resources_list.append({
                    "uri": resource.uri,
                    "name": resource.name,
                    "description": resource.description,
                    "mimeType": resource.mimeType
                })
            return {"resources": resources_list}
        
        @app.get("/mcp/resources/read")
        async def read_mcp_resource(uri: str):
            """Read an MCP resource"""
            if uri not in mcp_server.resources:
                raise HTTPException(status_code=404, detail=f"Resource not found: {uri}")
            
            # Handle different resource types
            if uri == "ultramcp://services/status":
                # Return UltraMCP services status
                status_data = {}
                for service_name, service_url in agent_service.services.items():
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(f"{service_url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                                if response.status == 200:
                                    status_data[service_name] = {"status": "healthy", "url": service_url}
                                else:
                                    status_data[service_name] = {"status": "unhealthy", "url": service_url}
                    except:
                        status_data[service_name] = {"status": "unreachable", "url": service_url}
                
                return {
                    "uri": uri,
                    "mimeType": "application/json",
                    "content": status_data
                }
            
            elif uri == "ultramcp://logs/recent":
                # Return recent logs (simplified)
                return {
                    "uri": uri,
                    "mimeType": "text/plain",
                    "content": "Recent UltraMCP system logs would be displayed here"
                }
            
            else:
                return {
                    "uri": uri,
                    "mimeType": "text/plain",
                    "content": f"Resource content for: {uri}"
                }
        
        @app.get("/mcp/prompts")
        async def list_mcp_prompts():
            """List all available MCP prompts"""
            prompts_list = []
            for prompt in mcp_server.prompts.values():
                prompts_list.append({
                    "name": prompt.name,
                    "description": prompt.description,
                    "arguments": prompt.arguments
                })
            return {"prompts": prompts_list}
        
        @app.post("/mcp/prompts/{prompt_name}/get")
        async def get_mcp_prompt(prompt_name: str, arguments: dict = None):
            """Get an MCP prompt with arguments"""
            if prompt_name not in mcp_server.prompts:
                raise HTTPException(status_code=404, detail=f"Prompt not found: {prompt_name}")
            
            prompt = mcp_server.prompts[prompt_name]
            args = arguments or {}
            
            # Generate prompt based on template
            if prompt_name == "security_analysis":
                project_path = args.get("project_path", "/unknown")
                focus_areas = args.get("focus_areas", "general security")
                prompt_text = f"""
Perform a comprehensive security analysis of the project at: {project_path}

Focus areas: {focus_areas}

Please analyze the following aspects:
1. Code vulnerabilities and security issues
2. Dependencies and known CVEs
3. Configuration security
4. Authentication and authorization
5. Data protection and encryption
6. Input validation and sanitization

Provide specific recommendations for remediation.
"""
            elif prompt_name == "code_review":
                language = args.get("language", "unknown")
                file_path = args.get("file_path", "/unknown")
                review_type = args.get("review_type", "general")
                prompt_text = f"""
Perform a {review_type} code review for the {language} file: {file_path}

Focus on:
- Code quality and best practices
- Performance considerations
- Security implications
- Maintainability
- Documentation

Provide specific suggestions for improvement.
"""
            else:
                prompt_text = f"Prompt: {prompt.description}\nArguments: {args}"
            
            return {
                "prompt": prompt_name,
                "description": prompt.description,
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": prompt_text
                        }
                    }
                ]
            }
        
        @app.websocket("/mcp/ws")
        async def mcp_websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for MCP protocol communication"""
            await websocket.accept()
            
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Handle MCP message
                    response = await mcp_server.handle_message(message, websocket)
                    
                    if response:
                        await websocket.send_text(json.dumps(response.to_dict()))
                        
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.close()
    
    uvicorn.run(app, host="0.0.0.0", port=8013)