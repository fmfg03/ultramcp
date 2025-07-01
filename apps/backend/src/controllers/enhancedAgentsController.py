"""
Enhanced Agents Controller - Unified REST API for Enhanced SAM and Manus Agents

This controller provides a unified interface for interacting with the enhanced
agents that integrate LangGraph orchestration, Graphiti knowledge graphs,
and comprehensive MCP enterprise capabilities.

Features:
- Unified agent communication interface
- Multi-agent collaboration coordination
- Cross-agent knowledge sharing
- Performance monitoring and analytics
- Enterprise-grade error handling and logging
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import asdict

from fastapi import HTTPException
from pydantic import BaseModel, Field

from ..services.enhancedSAMAgent import (
    EnhancedSAMAgent, 
    get_enhanced_sam_agent,
    AgentMode,
    cleanup_all_agents as cleanup_sam_agents
)
from ..services.enhancedManusAgent import (
    EnhancedManusAgent,
    get_enhanced_manus_agent,
    ExecutionContext,
    TaskType
)
from ..utils.logger import logger

# Request/Response Models

class ChatRequest(BaseModel):
    """Request model for agent chat"""
    message: str = Field(..., description="User message")
    user_id: str = Field(..., description="Unique user identifier")
    agent_type: str = Field("sam", description="Agent type: 'sam' or 'manus'")
    task_context: Optional[Dict[str, Any]] = Field(None, description="Additional task context")
    mode: Optional[str] = Field("chat", description="Agent operation mode")
    session_id: Optional[str] = Field(None, description="Session identifier for continuity")

class TaskExecutionRequest(BaseModel):
    """Request model for task execution via Manus"""
    task_description: str = Field(..., description="Description of task to execute")
    user_id: str = Field(..., description="Unique user identifier")
    priority: int = Field(1, ge=1, le=10, description="Task priority (1-10)")
    execution_context: Optional[Dict[str, Any]] = Field(None, description="Execution context")
    deadline: Optional[datetime] = Field(None, description="Task deadline")
    required_tools: Optional[List[str]] = Field(None, description="Required tools for execution")

class CollaborationRequest(BaseModel):
    """Request model for multi-agent collaboration"""
    primary_agent: str = Field(..., description="Primary agent (sam/manus)")
    task_description: str = Field(..., description="Collaborative task description")
    user_id: str = Field(..., description="User identifier")
    collaboration_type: str = Field("analysis_execution", description="Type of collaboration")
    context: Optional[Dict[str, Any]] = Field(None, description="Collaboration context")

class KnowledgeShareRequest(BaseModel):
    """Request model for knowledge sharing between agents"""
    source_agent: str = Field(..., description="Source agent identifier")
    target_agent: str = Field(..., description="Target agent identifier")
    knowledge_type: str = Field(..., description="Type of knowledge to share")
    user_id: str = Field(..., description="User identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Sharing context")

# Response Models

class AgentResponse(BaseModel):
    """Response model for agent interactions"""
    success: bool
    response: str
    agent_id: str
    agent_type: str
    metadata: Dict[str, Any]
    conversation_state: Optional[Dict[str, Any]] = None

class TaskExecutionResponse(BaseModel):
    """Response model for task execution"""
    success: bool
    response: str
    execution_results: Dict[str, Any]
    metadata: Dict[str, Any]

class CollaborationResponse(BaseModel):
    """Response model for multi-agent collaboration"""
    success: bool
    result: str
    collaboration_summary: Dict[str, Any]
    agents_involved: List[str]
    execution_time: float

class SystemStatusResponse(BaseModel):
    """Response model for system status"""
    overall_status: str
    agents: Dict[str, Dict[str, Any]]
    metrics: Dict[str, Any]
    timestamp: str

class EnhancedAgentsController:
    """
    Unified controller for enhanced agents with LangGraph + Graphiti integration
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the enhanced agents controller"""
        self.config = config or {}
        self.request_count = 0
        self.error_count = 0
        self.collaboration_count = 0
        
        # Agent instances will be created on-demand
        self._sam_agents = {}
        self._manus_agents = {}
        
        # Performance tracking
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "collaboration_events": 0,
            "knowledge_sharing_events": 0
        }
        
        logger.info("🤖 Enhanced Agents Controller initialized")
    
    async def chat_with_agent(self, request: ChatRequest) -> AgentResponse:
        """
        Chat with SAM agent using enhanced capabilities
        POST /api/agents/enhanced/chat
        """
        try:
            self.request_count += 1
            self.performance_metrics["total_requests"] += 1
            start_time = datetime.now()
            
            # Get or create SAM agent
            agent = self._get_sam_agent(request.user_id)
            
            # Determine agent mode
            mode = AgentMode.CHAT
            if request.mode:
                try:
                    mode = AgentMode(request.mode)
                except ValueError:
                    mode = AgentMode.CHAT
            
            # Execute chat
            result = await agent.chat(
                message=request.message,
                user_id=request.user_id,
                task_context=request.task_context,
                mode=mode
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(processing_time, True)
            
            response = AgentResponse(
                success=True,
                response=result["response"],
                agent_id=result["metadata"]["agent_id"],
                agent_type="sam",
                metadata={
                    **result["metadata"],
                    "processing_time": processing_time,
                    "session_id": request.session_id
                },
                conversation_state=result.get("conversation_state")
            )
            
            logger.info("💬 SAM chat completed", {
                "user_id": request.user_id,
                "agent_id": result["metadata"]["agent_id"],
                "processing_time": processing_time,
                "mode": request.mode
            })
            
            return response
            
        except Exception as error:
            self.error_count += 1
            self.performance_metrics["failed_requests"] += 1
            logger.error(f"❌ SAM chat failed: {error}")
            raise HTTPException(status_code=500, detail=str(error))
    
    async def execute_task_with_manus(self, request: TaskExecutionRequest) -> TaskExecutionResponse:
        """
        Execute task with Manus agent using enhanced orchestration
        POST /api/agents/enhanced/execute
        """
        try:
            self.request_count += 1
            self.performance_metrics["total_requests"] += 1
            start_time = datetime.now()
            
            # Get or create Manus agent
            agent = self._get_manus_agent(request.user_id)
            
            # Prepare execution context
            execution_context = None
            if request.execution_context:
                execution_context = ExecutionContext(
                    user_id=request.user_id,
                    session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    environment=request.execution_context.get('environment', 'production'),
                    constraints=request.execution_context.get('constraints'),
                    preferences=request.execution_context.get('preferences'),
                    available_resources=request.execution_context.get('available_resources')
                )
            
            # Execute task
            result = await agent.execute_task(
                task_description=request.task_description,
                user_id=request.user_id,
                execution_context=execution_context,
                priority=request.priority
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(processing_time, result["metadata"]["success"])
            
            response = TaskExecutionResponse(
                success=result["metadata"]["success"],
                response=result["response"],
                execution_results=result["execution_results"],
                metadata={
                    **result["metadata"],
                    "processing_time": processing_time,
                    "deadline": request.deadline.isoformat() if request.deadline else None
                }
            )
            
            logger.info("⚡ Manus task execution completed", {
                "user_id": request.user_id,
                "success": result["metadata"]["success"],
                "processing_time": processing_time,
                "priority": request.priority
            })
            
            return response
            
        except Exception as error:
            self.error_count += 1
            self.performance_metrics["failed_requests"] += 1
            logger.error(f"❌ Manus task execution failed: {error}")
            raise HTTPException(status_code=500, detail=str(error))
    
    async def coordinate_collaboration(self, request: CollaborationRequest) -> CollaborationResponse:
        """
        Coordinate collaboration between SAM and Manus agents
        POST /api/agents/enhanced/collaborate
        """
        try:
            self.collaboration_count += 1
            self.performance_metrics["collaboration_events"] += 1
            start_time = datetime.now()
            
            # Get both agents
            sam_agent = self._get_sam_agent(request.user_id)
            manus_agent = self._get_manus_agent(request.user_id)
            
            # Execute collaborative workflow
            collaboration_result = await self._execute_collaboration(
                sam_agent=sam_agent,
                manus_agent=manus_agent,
                request=request
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(processing_time, True)
            
            response = CollaborationResponse(
                success=True,
                result=collaboration_result["response"],
                collaboration_summary=collaboration_result["summary"],
                agents_involved=collaboration_result["agents_involved"],
                execution_time=processing_time
            )
            
            logger.info("🤝 Agent collaboration completed", {
                "user_id": request.user_id,
                "collaboration_type": request.collaboration_type,
                "agents_involved": len(collaboration_result["agents_involved"]),
                "processing_time": processing_time
            })
            
            return response
            
        except Exception as error:
            self.error_count += 1
            self.performance_metrics["failed_requests"] += 1
            logger.error(f"❌ Agent collaboration failed: {error}")
            raise HTTPException(status_code=500, detail=str(error))
    
    async def share_knowledge_between_agents(self, request: KnowledgeShareRequest) -> Dict[str, Any]:
        """
        Share knowledge between agents via Graphiti knowledge graph
        POST /api/agents/enhanced/knowledge-share
        """
        try:
            self.performance_metrics["knowledge_sharing_events"] += 1
            start_time = datetime.now()
            
            # Get source and target agents
            source_agent = self._get_agent_by_type_and_user(request.source_agent, request.user_id)
            target_agent = self._get_agent_by_type_and_user(request.target_agent, request.user_id)
            
            # Execute knowledge sharing via Graphiti
            sharing_result = await self._execute_knowledge_sharing(
                source_agent=source_agent,
                target_agent=target_agent,
                request=request
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            response = {
                "success": True,
                "knowledge_shared": sharing_result["knowledge_shared"],
                "sharing_summary": sharing_result["summary"],
                "agents_involved": [request.source_agent, request.target_agent],
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("🧠 Knowledge sharing completed", {
                "source_agent": request.source_agent,
                "target_agent": request.target_agent,
                "knowledge_type": request.knowledge_type,
                "processing_time": processing_time
            })
            
            return response
            
        except Exception as error:
            self.error_count += 1
            logger.error(f"❌ Knowledge sharing failed: {error}")
            raise HTTPException(status_code=500, detail=str(error))
    
    async def get_agent_metrics(self, agent_type: str = None, user_id: str = None) -> Dict[str, Any]:
        """
        Get comprehensive metrics for agents
        GET /api/agents/enhanced/metrics
        """
        try:
            metrics = {
                "controller_metrics": self.performance_metrics.copy(),
                "agents": {},
                "timestamp": datetime.now().isoformat()
            }
            
            # Get SAM agent metrics
            if agent_type is None or agent_type == "sam":
                sam_metrics = {}
                for user, agent in self._sam_agents.items():
                    if user_id is None or user == user_id:
                        agent_metrics = await agent.get_metrics()
                        sam_metrics[user] = agent_metrics
                metrics["agents"]["sam"] = sam_metrics
            
            # Get Manus agent metrics
            if agent_type is None or agent_type == "manus":
                manus_metrics = {}
                for user, agent in self._manus_agents.items():
                    if user_id is None or user == user_id:
                        agent_metrics = await agent.get_metrics()
                        manus_metrics[user] = agent_metrics
                metrics["agents"]["manus"] = manus_metrics
            
            # Add summary statistics
            metrics["summary"] = {
                "total_sam_agents": len(self._sam_agents),
                "total_manus_agents": len(self._manus_agents),
                "total_requests": self.request_count,
                "error_rate": (self.error_count / max(self.request_count, 1)) * 100,
                "collaboration_rate": (self.collaboration_count / max(self.request_count, 1)) * 100
            }
            
            return metrics
            
        except Exception as error:
            logger.error(f"❌ Failed to get agent metrics: {error}")
            raise HTTPException(status_code=500, detail=str(error))
    
    async def get_system_status(self) -> SystemStatusResponse:
        """
        Get comprehensive system status
        GET /api/agents/enhanced/status
        """
        try:
            # Check agent health
            agents_status = {}
            
            # Check SAM agents
            sam_status = {}
            for user_id, agent in self._sam_agents.items():
                health = await agent.health_check()
                sam_status[user_id] = health
            agents_status["sam"] = sam_status
            
            # Check Manus agents
            manus_status = {}
            for user_id, agent in self._manus_agents.items():
                health = await agent.health_check()
                manus_status[user_id] = health
            agents_status["manus"] = manus_status
            
            # Determine overall status
            all_statuses = []
            for agent_type in agents_status.values():
                for agent_health in agent_type.values():
                    all_statuses.append(agent_health.get("status", "unknown"))
            
            if all_statuses:
                if all(status == "healthy" for status in all_statuses):
                    overall_status = "healthy"
                elif any(status == "unhealthy" for status in all_statuses):
                    overall_status = "unhealthy"
                else:
                    overall_status = "degraded"
            else:
                overall_status = "no_agents"
            
            response = SystemStatusResponse(
                overall_status=overall_status,
                agents=agents_status,
                metrics=self.performance_metrics.copy(),
                timestamp=datetime.now().isoformat()
            )
            
            return response
            
        except Exception as error:
            logger.error(f"❌ System status check failed: {error}")
            raise HTTPException(status_code=500, detail=str(error))
    
    async def reset_agent_state(self, agent_type: str, user_id: str) -> Dict[str, Any]:
        """
        Reset agent state for a specific user
        POST /api/agents/enhanced/reset
        """
        try:
            if agent_type == "sam" and user_id in self._sam_agents:
                await self._sam_agents[user_id].close()
                del self._sam_agents[user_id]
                
            elif agent_type == "manus" and user_id in self._manus_agents:
                await self._manus_agents[user_id].close()
                del self._manus_agents[user_id]
                
            elif agent_type == "all":
                if user_id in self._sam_agents:
                    await self._sam_agents[user_id].close()
                    del self._sam_agents[user_id]
                if user_id in self._manus_agents:
                    await self._manus_agents[user_id].close()
                    del self._manus_agents[user_id]
            
            logger.info(f"🔄 Agent state reset", {
                "agent_type": agent_type,
                "user_id": user_id
            })
            
            return {
                "success": True,
                "message": f"Agent state reset for {agent_type} agent(s) for user {user_id}",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as error:
            logger.error(f"❌ Agent state reset failed: {error}")
            raise HTTPException(status_code=500, detail=str(error))
    
    # Private helper methods
    
    def _get_sam_agent(self, user_id: str) -> EnhancedSAMAgent:
        """Get or create SAM agent for user"""
        if user_id not in self._sam_agents:
            self._sam_agents[user_id] = get_enhanced_sam_agent(
                agent_id=f"sam_{user_id}",
                config=self.config
            )
        return self._sam_agents[user_id]
    
    def _get_manus_agent(self, user_id: str) -> EnhancedManusAgent:
        """Get or create Manus agent for user"""
        if user_id not in self._manus_agents:
            self._manus_agents[user_id] = get_enhanced_manus_agent(
                agent_id=f"manus_{user_id}",
                config=self.config
            )
        return self._manus_agents[user_id]
    
    def _get_agent_by_type_and_user(self, agent_type: str, user_id: str):
        """Get agent by type and user ID"""
        if agent_type == "sam":
            return self._get_sam_agent(user_id)
        elif agent_type == "manus":
            return self._get_manus_agent(user_id)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
    
    async def _execute_collaboration(
        self,
        sam_agent: EnhancedSAMAgent,
        manus_agent: EnhancedManusAgent,
        request: CollaborationRequest
    ) -> Dict[str, Any]:
        """Execute collaboration between SAM and Manus agents"""
        
        if request.collaboration_type == "analysis_execution":
            # SAM analyzes, Manus executes
            
            # Step 1: SAM analyzes the task
            analysis_result = await sam_agent.chat(
                message=f"Analyze this task for execution planning: {request.task_description}",
                user_id=request.user_id,
                task_context=request.context,
                mode=AgentMode.ANALYSIS
            )
            
            # Step 2: Manus executes based on analysis
            execution_result = await manus_agent.execute_task(
                task_description=f"Execute based on analysis: {analysis_result['response']}",
                user_id=request.user_id,
                priority=2
            )
            
            return {
                "response": f"Analysis: {analysis_result['response']}\n\nExecution: {execution_result['response']}",
                "summary": {
                    "analysis_phase": analysis_result["metadata"],
                    "execution_phase": execution_result["metadata"],
                    "collaboration_type": request.collaboration_type
                },
                "agents_involved": ["sam", "manus"]
            }
        
        elif request.collaboration_type == "knowledge_synthesis":
            # Both agents contribute knowledge and synthesize
            
            # Both agents analyze the task
            sam_perspective = await sam_agent.chat(
                message=f"Provide your perspective on: {request.task_description}",
                user_id=request.user_id,
                task_context=request.context
            )
            
            manus_perspective = await manus_agent.execute_task(
                task_description=f"Provide execution perspective on: {request.task_description}",
                user_id=request.user_id,
                priority=1
            )
            
            # Synthesize perspectives
            synthesis = f"Combined insights:\nSAM (Analysis): {sam_perspective['response']}\nManus (Execution): {manus_perspective['response']}"
            
            return {
                "response": synthesis,
                "summary": {
                    "sam_contribution": sam_perspective["metadata"],
                    "manus_contribution": manus_perspective["metadata"],
                    "collaboration_type": request.collaboration_type
                },
                "agents_involved": ["sam", "manus"]
            }
        
        else:
            # Default collaboration
            return {
                "response": f"Collaboration completed for: {request.task_description}",
                "summary": {"collaboration_type": request.collaboration_type},
                "agents_involved": ["sam", "manus"]
            }
    
    async def _execute_knowledge_sharing(
        self,
        source_agent: Union[EnhancedSAMAgent, EnhancedManusAgent],
        target_agent: Union[EnhancedSAMAgent, EnhancedManusAgent],
        request: KnowledgeShareRequest
    ) -> Dict[str, Any]:
        """Execute knowledge sharing between agents via Graphiti"""
        
        # This would use Graphiti to share knowledge between agents
        # For now, return mock implementation
        
        return {
            "knowledge_shared": {
                "type": request.knowledge_type,
                "items_shared": 5,
                "relationships_created": 3
            },
            "summary": {
                "source_agent": request.source_agent,
                "target_agent": request.target_agent,
                "knowledge_type": request.knowledge_type,
                "sharing_method": "graphiti_knowledge_graph"
            }
        }
    
    def _update_performance_metrics(self, processing_time: float, success: bool):
        """Update performance metrics"""
        if success:
            self.performance_metrics["successful_requests"] += 1
        else:
            self.performance_metrics["failed_requests"] += 1
        
        # Update average response time
        current_avg = self.performance_metrics["avg_response_time"]
        total_requests = self.performance_metrics["total_requests"]
        self.performance_metrics["avg_response_time"] = (
            (current_avg * (total_requests - 1) + processing_time) / total_requests
        )
    
    async def close_all_agents(self):
        """Close all agent instances"""
        try:
            # Close SAM agents
            for agent in self._sam_agents.values():
                await agent.close()
            self._sam_agents.clear()
            
            # Close Manus agents
            for agent in self._manus_agents.values():
                await agent.close()
            self._manus_agents.clear()
            
            logger.info("🔒 All enhanced agents closed successfully")
            
        except Exception as error:
            logger.error(f"❌ Error closing agents: {error}")

# Global controller instance
_enhanced_agents_controller = None

def get_enhanced_agents_controller(config: Dict[str, Any] = None) -> EnhancedAgentsController:
    """Get or create the global enhanced agents controller instance"""
    global _enhanced_agents_controller
    
    if _enhanced_agents_controller is None:
        _enhanced_agents_controller = EnhancedAgentsController(config)
    
    return _enhanced_agents_controller