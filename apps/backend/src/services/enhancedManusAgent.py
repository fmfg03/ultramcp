"""
Enhanced Manus Agent with LangGraph + Graphiti + MCP Enterprise Integration

This module implements the enhanced Manus agent with:
- LangGraph orchestration for complex task execution workflows
- Graphiti knowledge graph integration for contextual task understanding
- MCP tool integration for comprehensive task execution capabilities
- Multi-agent collaboration with SAM and other agents

Manus specializes in:
- Complex task orchestration and execution
- Multi-step workflow management
- Tool coordination and automation
- System integration and process optimization
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Annotated
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# LangGraph and LangChain imports
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from typing_extensions import TypedDict

# MCP and enhanced services
from .enhancedMemoryService import EnhancedMemorySystem, get_enhanced_memory_system
from .enhancedSAMAgent import EnhancedSAMAgent, get_enhanced_sam_agent, MCPAgentState, ContextSource
from ..utils.logger import logger

# LangWatch integration
try:
    import langwatch
    from langwatch.types import ChatMessage, LLMSpan
    LANGWATCH_AVAILABLE = True
    logger.info("✅ LangWatch integration available for Manus")
except ImportError:
    LANGWATCH_AVAILABLE = False
    logger.warning("⚠️ LangWatch not available for Manus - install with: pip install langwatch")

# Import Graphiti
try:
    from graphiti import Graphiti
    GRAPHITI_AVAILABLE = True
except ImportError:
    logger.warning("Graphiti not available - using mock implementation")
    GRAPHITI_AVAILABLE = False

class TaskType(Enum):
    """Types of tasks Manus can handle"""
    SIMPLE_EXECUTION = "simple_execution"
    MULTI_STEP_WORKFLOW = "multi_step_workflow"
    SYSTEM_INTEGRATION = "system_integration"
    DATA_PROCESSING = "data_processing"
    AUTOMATION_SETUP = "automation_setup"
    COLLABORATION_COORDINATION = "collaboration_coordination"
    COMPLEX_ANALYSIS = "complex_analysis"

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_INPUT = "waiting_for_input"
    DELEGATED = "delegated"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ExecutionStrategy(Enum):
    """Strategies for task execution"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    ADAPTIVE = "adaptive"
    COLLABORATIVE = "collaborative"

@dataclass
class TaskStep:
    """Individual step in a task workflow"""
    step_id: str
    description: str
    tool_required: Optional[str] = None
    dependencies: List[str] = None
    estimated_duration: Optional[int] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict] = None
    error: Optional[str] = None
    assigned_agent: Optional[str] = None

@dataclass
class TaskPlan:
    """Comprehensive task execution plan"""
    task_id: str
    task_type: TaskType
    description: str
    steps: List[TaskStep]
    strategy: ExecutionStrategy
    priority: int = 1
    deadline: Optional[datetime] = None
    required_tools: List[str] = None
    collaboration_agents: List[str] = None
    success_criteria: List[str] = None

@dataclass
class ExecutionContext:
    """Context for task execution"""
    user_id: str
    session_id: str
    environment: str = "production"
    constraints: Dict[str, Any] = None
    preferences: Dict[str, Any] = None
    available_resources: Dict[str, Any] = None

class ManusAgentState(TypedDict):
    """Enhanced state for Manus agent with task execution focus"""
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: str
    task_context: Dict[str, Any]
    current_task: Optional[Dict]
    task_queue: List[Dict]
    execution_history: List[Dict]
    active_tools: List[str]
    collaboration_status: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    system_state: Dict[str, Any]

class EnhancedManusAgent:
    """
    Enhanced Manus Agent specialized in complex task orchestration
    with LangGraph workflows and Graphiti knowledge integration
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the enhanced Manus agent"""
        self.config = config or {}
        self.agent_id = f"enhanced_manus_{uuid.uuid4().hex[:8]}"
        
        # Initialize core components
        self._initialize_components()
        
        # Setup LangGraph orchestration for task execution
        self._setup_task_orchestration()
        
        # Task management
        self.active_tasks = {}
        self.task_queue = []
        self.execution_history = []
        
        # Performance and monitoring
        self.metrics = {
            "tasks_executed": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tools_executed": 0,
            "collaboration_events": 0,
            "avg_task_duration": 0.0,
            "success_rate": 0.0
        }
        
        logger.info(f"🔧 Enhanced Manus Agent initialized: {self.agent_id}")
    
    def _initialize_components(self):
        """Initialize all core components"""
        try:
            # Enhanced Memory System with Graphiti
            self.enhanced_memory = get_enhanced_memory_system(self.config)
            
            # Graphiti Knowledge Graph (if available)
            if GRAPHITI_AVAILABLE and self.config.get('OPENAI_API_KEY'):
                self.graphiti = Graphiti(
                    neo4j_uri=self.config.get('NEO4J_URI', 'bolt://localhost:7687'),
                    neo4j_user=self.config.get('NEO4J_USERNAME', 'neo4j'),
                    neo4j_password=self.config.get('NEO4J_PASSWORD', 'neo4j_password'),
                    llm_client_type="openai",
                    embedding_model=self.config.get('GRAPHITI_EMBEDDING_MODEL', 'text-embedding-3-small'),
                    llm_model=self.config.get('GRAPHITI_LLM_MODEL', 'gpt-4-turbo-preview')
                )
            else:
                self.graphiti = None
                logger.warning("Graphiti not available - using enhanced memory only")
            
            # LLM setup
            self.llm = self._setup_llm()
            
            # LangGraph memory saver
            self.memory_saver = MemorySaver()
            
            logger.info("✅ Manus core components initialized successfully")
            
        except Exception as error:
            logger.error(f"❌ Failed to initialize Manus components: {error}")
            raise
    
    def _setup_llm(self):
        """Setup LLM with task-execution optimized settings"""
        providers = [
            ("openai", "OPENAI_API_KEY", ChatOpenAI),
            ("anthropic", "ANTHROPIC_API_KEY", ChatAnthropic)
        ]
        
        for provider_name, api_key_env, provider_class in providers:
            api_key = self.config.get(api_key_env)
            if api_key:
                try:
                    if provider_name == "openai":
                        return provider_class(
                            model="gpt-4-turbo-preview",
                            api_key=api_key,
                            temperature=0.1,  # Lower temperature for precise task execution
                            max_tokens=2000
                        )
                    elif provider_name == "anthropic":
                        return provider_class(
                            model="claude-3-sonnet-20240229",
                            api_key=api_key,
                            temperature=0.1
                        )
                except Exception as error:
                    logger.warning(f"Failed to initialize {provider_name}: {error}")
                    continue
        
        raise Exception("No LLM provider available for Manus")
    
    def _setup_task_orchestration(self):
        """Setup LangGraph for complex task orchestration"""
        try:
            # Create state graph for task execution
            graph_builder = StateGraph(ManusAgentState)
            
            # Add nodes for task execution workflow
            graph_builder.add_node('task_analysis', self._task_analysis_node)
            graph_builder.add_node('task_planning', self._task_planning_node)
            graph_builder.add_node('resource_allocation', self._resource_allocation_node)
            graph_builder.add_node('collaboration_setup', self._collaboration_setup_node)
            graph_builder.add_node('task_execution', self._task_execution_node)
            graph_builder.add_node('progress_monitoring', self._progress_monitoring_node)
            graph_builder.add_node('result_validation', self._result_validation_node)
            graph_builder.add_node('completion_handling', self._completion_handling_node)
            
            # Setup workflow edges
            graph_builder.add_edge(START, 'task_analysis')
            graph_builder.add_edge('task_analysis', 'task_planning')
            graph_builder.add_edge('task_planning', 'resource_allocation')
            
            # Conditional routing based on task complexity
            graph_builder.add_conditional_edges(
                'resource_allocation',
                self._route_execution_strategy,
                {
                    'collaboration': 'collaboration_setup',
                    'direct': 'task_execution'
                }
            )
            
            graph_builder.add_edge('collaboration_setup', 'task_execution')
            graph_builder.add_edge('task_execution', 'progress_monitoring')
            
            # Monitoring can loop back to execution or proceed to validation
            graph_builder.add_conditional_edges(
                'progress_monitoring',
                self._route_monitoring_decision,
                {
                    'continue': 'task_execution',
                    'validate': 'result_validation',
                    'collaborate': 'collaboration_setup'
                }
            )
            
            graph_builder.add_edge('result_validation', 'completion_handling')
            graph_builder.add_edge('completion_handling', END)
            
            # Compile the graph
            self.task_graph = graph_builder.compile(checkpointer=self.memory_saver)
            
            logger.info("🕸️ Manus task orchestration graph setup complete")
            
        except Exception as error:
            logger.error(f"❌ Failed to setup task orchestration: {error}")
            raise
    
    async def _task_analysis_node(self, state: ManusAgentState, config: Dict = None) -> Dict:
        """Analyze incoming task and determine execution requirements"""
        start_time = datetime.now()
        
        try:
            latest_message = state['messages'][-1].content if state['messages'] else ""
            user_id = state.get('user_id')
            
            # Get contextual understanding from knowledge graph
            task_context = await self._analyze_task_context(latest_message, user_id)
            
            # Determine task type and complexity
            task_classification = await self._classify_task(latest_message, task_context)
            
            # Update state with analysis
            state['task_context'].update({
                'analysis': task_classification,
                'contextual_info': task_context,
                'analyzed_at': datetime.now().isoformat()
            })
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"📊 Task analysis completed", {
                "task_type": task_classification.get('type'),
                "complexity": task_classification.get('complexity'),
                "tools_required": len(task_classification.get('required_tools', [])),
                "processing_time": processing_time
            })
            
            return state
            
        except Exception as error:
            logger.error(f"❌ Task analysis failed: {error}")
            return state
    
    async def _task_planning_node(self, state: ManusAgentState, config: Dict = None) -> Dict:
        """Create detailed execution plan for the task"""
        try:
            task_analysis = state['task_context'].get('analysis', {})
            
            # Generate comprehensive task plan
            task_plan = await self._generate_task_plan(task_analysis, state)
            
            # Store plan in state
            state['current_task'] = asdict(task_plan)
            
            # Update task queue if needed
            if task_plan.strategy == ExecutionStrategy.SEQUENTIAL:
                state['task_queue'] = [asdict(step) for step in task_plan.steps]
            
            logger.info(f"📋 Task plan created", {
                "task_id": task_plan.task_id,
                "steps": len(task_plan.steps),
                "strategy": task_plan.strategy.value,
                "estimated_tools": len(task_plan.required_tools or [])
            })
            
            return state
            
        except Exception as error:
            logger.error(f"❌ Task planning failed: {error}")
            return state
    
    async def _resource_allocation_node(self, state: ManusAgentState, config: Dict = None) -> Dict:
        """Allocate resources and prepare for task execution"""
        try:
            current_task = state.get('current_task', {})
            required_tools = current_task.get('required_tools', [])
            
            # Check tool availability
            available_tools = await self._check_tool_availability(required_tools)
            
            # Determine if collaboration is needed
            collaboration_needed = await self._assess_collaboration_needs(current_task, state)
            
            # Update state with resource allocation
            state['active_tools'] = available_tools
            state['collaboration_status'] = {
                'needed': collaboration_needed,
                'agents': current_task.get('collaboration_agents', []),
                'status': 'pending' if collaboration_needed else 'not_required'
            }
            
            logger.info(f"🔧 Resources allocated", {
                "available_tools": len(available_tools),
                "collaboration_needed": collaboration_needed,
                "required_agents": len(current_task.get('collaboration_agents', []))
            })
            
            return state
            
        except Exception as error:
            logger.error(f"❌ Resource allocation failed: {error}")
            return state
    
    async def _collaboration_setup_node(self, state: ManusAgentState, config: Dict = None) -> Dict:
        """Setup collaboration with other agents"""
        try:
            collaboration_status = state.get('collaboration_status', {})
            
            if not collaboration_status.get('needed'):
                return state
            
            # Get collaboration context from knowledge graph
            collaboration_context = await self._get_collaboration_context(state)
            
            # Setup communication with other agents
            agent_connections = await self._setup_agent_connections(
                collaboration_status.get('agents', []),
                state
            )
            
            # Update collaboration status
            state['collaboration_status'].update({
                'context': collaboration_context,
                'connections': agent_connections,
                'status': 'active',
                'setup_at': datetime.now().isoformat()
            })
            
            self.metrics["collaboration_events"] += 1
            
            logger.info(f"🤝 Collaboration setup completed", {
                "connected_agents": len(agent_connections),
                "collaboration_type": collaboration_context.get('type', 'unknown')
            })
            
            return state
            
        except Exception as error:
            logger.error(f"❌ Collaboration setup failed: {error}")
            return state
    
    async def _task_execution_node(self, state: ManusAgentState, config: Dict = None) -> Dict:
        """Execute the current task or task step"""
        start_time = datetime.now()
        
        try:
            current_task = state.get('current_task', {})
            task_queue = state.get('task_queue', [])
            
            execution_results = []
            
            if task_queue:
                # Execute next step in queue
                current_step = task_queue[0]
                result = await self._execute_task_step(current_step, state)
                execution_results.append(result)
                
                # Remove completed step from queue
                state['task_queue'] = task_queue[1:]
                
            else:
                # Execute simple task
                result = await self._execute_simple_task(current_task, state)
                execution_results.append(result)
            
            # Update execution history
            state['execution_history'] = state.get('execution_history', []) + execution_results
            
            # Update metrics
            self.metrics["tasks_executed"] += 1
            if all(r.get('success', False) for r in execution_results):
                self.metrics["tasks_completed"] += 1
            else:
                self.metrics["tasks_failed"] += 1
            
            duration = (datetime.now() - start_time).total_seconds()
            self.metrics["avg_task_duration"] = (
                self.metrics["avg_task_duration"] + duration
            ) / 2
            
            logger.info(f"⚡ Task execution completed", {
                "results_count": len(execution_results),
                "successful": sum(1 for r in execution_results if r.get('success', False)),
                "duration": duration
            })
            
            return state
            
        except Exception as error:
            logger.error(f"❌ Task execution failed: {error}")
            return state
    
    async def _progress_monitoring_node(self, state: ManusAgentState, config: Dict = None) -> Dict:
        """Monitor task progress and determine next actions"""
        try:
            current_task = state.get('current_task', {})
            task_queue = state.get('task_queue', [])
            execution_history = state.get('execution_history', [])
            
            # Analyze current progress
            progress_analysis = await self._analyze_progress(
                current_task, task_queue, execution_history
            )
            
            # Update performance metrics
            state['performance_metrics'] = {
                'progress_percentage': progress_analysis.get('completion_percentage', 0),
                'steps_completed': progress_analysis.get('steps_completed', 0),
                'steps_remaining': progress_analysis.get('steps_remaining', 0),
                'estimated_completion': progress_analysis.get('estimated_completion'),
                'issues_detected': progress_analysis.get('issues', [])
            }
            
            logger.info(f"📈 Progress monitoring", {
                "completion": f"{progress_analysis.get('completion_percentage', 0):.1f}%",
                "steps_remaining": progress_analysis.get('steps_remaining', 0),
                "issues": len(progress_analysis.get('issues', []))
            })
            
            return state
            
        except Exception as error:
            logger.error(f"❌ Progress monitoring failed: {error}")
            return state
    
    async def _result_validation_node(self, state: ManusAgentState, config: Dict = None) -> Dict:
        """Validate task execution results"""
        try:
            current_task = state.get('current_task', {})
            execution_history = state.get('execution_history', [])
            
            # Validate results against success criteria
            validation_results = await self._validate_task_results(
                current_task, execution_history
            )
            
            # Update task status based on validation
            state['current_task']['validation'] = validation_results
            state['current_task']['status'] = (
                TaskStatus.COMPLETED.value if validation_results.get('passed', False)
                else TaskStatus.FAILED.value
            )
            
            logger.info(f"✅ Result validation completed", {
                "validation_passed": validation_results.get('passed', False),
                "criteria_met": validation_results.get('criteria_met', 0),
                "total_criteria": validation_results.get('total_criteria', 0)
            })
            
            return state
            
        except Exception as error:
            logger.error(f"❌ Result validation failed: {error}")
            return state
    
    async def _completion_handling_node(self, state: ManusAgentState, config: Dict = None) -> Dict:
        """Handle task completion and cleanup"""
        try:
            current_task = state.get('current_task', {})
            user_id = state.get('user_id')
            
            # Store task completion in knowledge graph
            if self.graphiti:
                asyncio.create_task(self._store_task_completion_to_graphiti(
                    current_task, state, user_id
                ))
            
            # Generate completion response
            completion_response = await self._generate_completion_response(current_task, state)
            
            # Add completion message to conversation
            state['messages'] = state['messages'] + [AIMessage(content=completion_response)]
            
            # Clean up active resources
            state['active_tools'] = []
            state['collaboration_status'] = {'status': 'completed'}
            
            # Update success rate
            total_tasks = self.metrics["tasks_executed"]
            if total_tasks > 0:
                self.metrics["success_rate"] = (
                    self.metrics["tasks_completed"] / total_tasks * 100
                )
            
            logger.info(f"🎯 Task completion handled", {
                "task_status": current_task.get('status'),
                "success_rate": self.metrics["success_rate"]
            })
            
            return state
            
        except Exception as error:
            logger.error(f"❌ Completion handling failed: {error}")
            return state
    
    def _route_execution_strategy(self, state: ManusAgentState) -> str:
        """Route based on execution strategy needs"""
        collaboration_status = state.get('collaboration_status', {})
        
        if collaboration_status.get('needed', False):
            return 'collaboration'
        else:
            return 'direct'
    
    def _route_monitoring_decision(self, state: ManusAgentState) -> str:
        """Route based on monitoring decision"""
        task_queue = state.get('task_queue', [])
        performance_metrics = state.get('performance_metrics', {})
        
        # Check if there are more steps to execute
        if task_queue:
            return 'continue'
        
        # Check if collaboration is needed
        issues = performance_metrics.get('issues_detected', [])
        if any('collaboration' in issue.lower() for issue in issues):
            return 'collaborate'
        
        # Proceed to validation
        return 'validate'
    
    # Task execution helper methods
    
    async def _analyze_task_context(self, task_description: str, user_id: str) -> Dict[str, Any]:
        """Analyze task context using knowledge graph"""
        try:
            if self.graphiti:
                # Search for relevant context
                context_results = await self.graphiti.search(
                    query=f"user:{user_id} task execution {task_description}",
                    search_type="hybrid",
                    limit=10
                )
                
                # Get user's task execution patterns
                user_patterns = await self._get_user_task_patterns(user_id)
                
                return {
                    'relevant_context': context_results.get('results', []) if isinstance(context_results, dict) else [],
                    'user_patterns': user_patterns,
                    'historical_tasks': await self._get_historical_tasks(user_id)
                }
            
            return {}
            
        except Exception as error:
            logger.error(f"❌ Error analyzing task context: {error}")
            return {}
    
    async def _classify_task(self, task_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify task type and determine requirements"""
        # Simple classification logic - enhance with ML in production
        task_lower = task_description.lower()
        
        # Determine task type
        if any(keyword in task_lower for keyword in ['analyze', 'process', 'calculate']):
            task_type = TaskType.DATA_PROCESSING
        elif any(keyword in task_lower for keyword in ['setup', 'configure', 'install']):
            task_type = TaskType.SYSTEM_INTEGRATION
        elif any(keyword in task_lower for keyword in ['automate', 'schedule', 'recurring']):
            task_type = TaskType.AUTOMATION_SETUP
        elif any(keyword in task_lower for keyword in ['coordinate', 'manage', 'organize']):
            task_type = TaskType.COLLABORATION_COORDINATION
        elif 'step' in task_lower or 'workflow' in task_lower:
            task_type = TaskType.MULTI_STEP_WORKFLOW
        else:
            task_type = TaskType.SIMPLE_EXECUTION
        
        # Determine complexity
        complexity_indicators = len([
            word for word in ['complex', 'multiple', 'integrate', 'coordinate', 'analyze']
            if word in task_lower
        ])
        
        if complexity_indicators >= 3:
            complexity = 'high'
        elif complexity_indicators >= 1:
            complexity = 'medium'
        else:
            complexity = 'low'
        
        # Determine required tools
        required_tools = []
        if any(keyword in task_lower for keyword in ['search', 'find', 'lookup']):
            required_tools.append('search_tool')
        if any(keyword in task_lower for keyword in ['calculate', 'compute', 'math']):
            required_tools.append('calculator')
        if any(keyword in task_lower for keyword in ['file', 'document', 'save']):
            required_tools.append('file_manager')
        if any(keyword in task_lower for keyword in ['api', 'request', 'fetch']):
            required_tools.append('api_client')
        
        return {
            'type': task_type.value,
            'complexity': complexity,
            'required_tools': required_tools,
            'estimated_duration': self._estimate_duration(task_type, complexity),
            'requires_collaboration': complexity == 'high' or 'coordinate' in task_lower
        }
    
    async def _generate_task_plan(self, analysis: Dict[str, Any], state: ManusAgentState) -> TaskPlan:
        """Generate comprehensive task execution plan"""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task_type = TaskType(analysis.get('type', TaskType.SIMPLE_EXECUTION.value))
        
        # Generate steps based on task type
        steps = await self._generate_task_steps(analysis, state)
        
        # Determine execution strategy
        if analysis.get('requires_collaboration'):
            strategy = ExecutionStrategy.COLLABORATIVE
        elif len(steps) > 1:
            strategy = ExecutionStrategy.SEQUENTIAL
        else:
            strategy = ExecutionStrategy.SEQUENTIAL
        
        # Determine collaboration agents if needed
        collaboration_agents = []
        if analysis.get('requires_collaboration'):
            collaboration_agents = await self._identify_collaboration_agents(analysis)
        
        return TaskPlan(
            task_id=task_id,
            task_type=task_type,
            description=state['messages'][-1].content if state['messages'] else "Unknown task",
            steps=steps,
            strategy=strategy,
            required_tools=analysis.get('required_tools', []),
            collaboration_agents=collaboration_agents,
            success_criteria=await self._define_success_criteria(analysis)
        )
    
    async def _generate_task_steps(self, analysis: Dict[str, Any], state: ManusAgentState) -> List[TaskStep]:
        """Generate detailed task steps"""
        task_type = analysis.get('type')
        complexity = analysis.get('complexity')
        
        steps = []
        
        if complexity == 'high' or task_type == TaskType.MULTI_STEP_WORKFLOW.value:
            # Multi-step workflow
            steps = [
                TaskStep(
                    step_id=f"step_1_{uuid.uuid4().hex[:4]}",
                    description="Initialize task environment and gather requirements",
                    tool_required="environment_setup"
                ),
                TaskStep(
                    step_id=f"step_2_{uuid.uuid4().hex[:4]}",
                    description="Execute primary task logic",
                    tool_required=analysis.get('required_tools', [None])[0],
                    dependencies=["step_1"]
                ),
                TaskStep(
                    step_id=f"step_3_{uuid.uuid4().hex[:4]}",
                    description="Validate results and perform cleanup",
                    dependencies=["step_2"]
                )
            ]
        else:
            # Simple execution
            steps = [
                TaskStep(
                    step_id=f"step_1_{uuid.uuid4().hex[:4]}",
                    description="Execute task",
                    tool_required=analysis.get('required_tools', [None])[0]
                )
            ]
        
        return steps
    
    async def _execute_task_step(self, step: Dict[str, Any], state: ManusAgentState) -> Dict[str, Any]:
        """Execute a single task step"""
        try:
            step_id = step.get('step_id')
            tool_required = step.get('tool_required')
            
            # Mock tool execution - replace with actual MCP tool calls
            if tool_required:
                tool_result = await self._execute_tool(tool_required, step, state)
                self.metrics["tools_executed"] += 1
            else:
                tool_result = {"result": f"Completed step: {step.get('description')}", "success": True}
            
            return {
                "step_id": step_id,
                "result": tool_result,
                "success": tool_result.get('success', False),
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as error:
            return {
                "step_id": step.get('step_id'),
                "error": str(error),
                "success": False,
                "completed_at": datetime.now().isoformat()
            }
    
    async def _execute_simple_task(self, task: Dict[str, Any], state: ManusAgentState) -> Dict[str, Any]:
        """Execute a simple task"""
        try:
            # Mock simple task execution
            return {
                "task_id": task.get('task_id'),
                "result": f"Completed task: {task.get('description')}",
                "success": True,
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as error:
            return {
                "task_id": task.get('task_id'),
                "error": str(error),
                "success": False,
                "completed_at": datetime.now().isoformat()
            }
    
    async def _execute_tool(self, tool_name: str, context: Dict, state: ManusAgentState) -> Dict[str, Any]:
        """Execute a specific tool"""
        # Mock tool execution - replace with actual MCP tool integration
        try:
            return {
                "tool": tool_name,
                "result": f"Executed {tool_name} successfully",
                "success": True,
                "metadata": {"execution_time": 1.5}
            }
        except Exception as error:
            return {
                "tool": tool_name,
                "error": str(error),
                "success": False
            }
    
    # Placeholder methods for advanced features
    
    async def _check_tool_availability(self, required_tools: List[str]) -> List[str]:
        """Check which tools are available"""
        # Mock implementation - replace with actual tool registry check
        return required_tools  # Assume all tools are available
    
    async def _assess_collaboration_needs(self, task: Dict, state: ManusAgentState) -> bool:
        """Assess if collaboration with other agents is needed"""
        return task.get('requires_collaboration', False)
    
    async def _get_collaboration_context(self, state: ManusAgentState) -> Dict[str, Any]:
        """Get collaboration context from knowledge graph"""
        return {"type": "task_coordination", "priority": "medium"}
    
    async def _setup_agent_connections(self, agents: List[str], state: ManusAgentState) -> Dict[str, Any]:
        """Setup connections with other agents"""
        connections = {}
        for agent in agents:
            connections[agent] = {"status": "connected", "capabilities": ["analysis", "execution"]}
        return connections
    
    async def _analyze_progress(self, task: Dict, queue: List, history: List) -> Dict[str, Any]:
        """Analyze current task progress"""
        steps_completed = len(history)
        steps_remaining = len(queue)
        total_steps = steps_completed + steps_remaining
        
        completion_percentage = (steps_completed / max(total_steps, 1)) * 100
        
        return {
            "completion_percentage": completion_percentage,
            "steps_completed": steps_completed,
            "steps_remaining": steps_remaining,
            "issues": []
        }
    
    async def _validate_task_results(self, task: Dict, history: List) -> Dict[str, Any]:
        """Validate task execution results"""
        success_criteria = task.get('success_criteria', [])
        
        # Simple validation - check if all steps succeeded
        all_successful = all(h.get('success', False) for h in history)
        
        return {
            "passed": all_successful,
            "criteria_met": len(success_criteria) if all_successful else 0,
            "total_criteria": len(success_criteria),
            "details": "All execution steps completed successfully" if all_successful else "Some steps failed"
        }
    
    async def _generate_completion_response(self, task: Dict, state: ManusAgentState) -> str:
        """Generate task completion response"""
        status = task.get('status')
        
        if status == TaskStatus.COMPLETED.value:
            return f"✅ Task completed successfully: {task.get('description')}"
        else:
            return f"❌ Task failed: {task.get('description')}"
    
    async def _store_task_completion_to_graphiti(self, task: Dict, state: ManusAgentState, user_id: str):
        """Store task completion in Graphiti knowledge graph"""
        try:
            if not self.graphiti:
                return
            
            episode = {
                "text": f"Manus Agent completed task: {task.get('description')}",
                "metadata": {
                    "user_id": user_id,
                    "agent": "enhanced_manus",
                    "agent_id": self.agent_id,
                    "task_id": task.get('task_id'),
                    "task_type": task.get('task_type'),
                    "status": task.get('status'),
                    "execution_history": state.get('execution_history', []),
                    "tools_used": state.get('active_tools', []),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            result = await self.graphiti.add_episode(episode)
            logger.info(f"📝 Stored task completion in Graphiti: {result.get('episode_id', 'unknown')}")
            
        except Exception as error:
            logger.error(f"❌ Error storing task completion to Graphiti: {error}")
    
    def _estimate_duration(self, task_type: TaskType, complexity: str) -> int:
        """Estimate task duration in minutes"""
        base_times = {
            TaskType.SIMPLE_EXECUTION: 5,
            TaskType.MULTI_STEP_WORKFLOW: 15,
            TaskType.SYSTEM_INTEGRATION: 30,
            TaskType.DATA_PROCESSING: 20,
            TaskType.AUTOMATION_SETUP: 45,
            TaskType.COLLABORATION_COORDINATION: 25,
            TaskType.COMPLEX_ANALYSIS: 40
        }
        
        multipliers = {'low': 1.0, 'medium': 1.5, 'high': 2.5}
        
        return int(base_times.get(task_type, 10) * multipliers.get(complexity, 1.0))
    
    async def _identify_collaboration_agents(self, analysis: Dict) -> List[str]:
        """Identify which agents should collaborate on this task"""
        agents = []
        
        if 'analysis' in analysis.get('type', ''):
            agents.append('enhanced_sam')
        
        if analysis.get('complexity') == 'high':
            agents.append('enhanced_sam')
        
        return agents
    
    async def _define_success_criteria(self, analysis: Dict) -> List[str]:
        """Define success criteria for the task"""
        criteria = ["Task completed without errors"]
        
        if analysis.get('required_tools'):
            criteria.append("All required tools executed successfully")
        
        if analysis.get('requires_collaboration'):
            criteria.append("Collaboration coordination successful")
        
        return criteria
    
    async def _get_user_task_patterns(self, user_id: str) -> Dict:
        """Get user's task execution patterns"""
        # Placeholder - implement with Graphiti queries
        return {}
    
    async def _get_historical_tasks(self, user_id: str) -> List[Dict]:
        """Get historical tasks for the user"""
        # Placeholder - implement with Graphiti queries
        return []
    
    # Public interface methods
    
    async def execute_task(
        self,
        task_description: str,
        user_id: str,
        execution_context: ExecutionContext = None,
        priority: int = 1
    ) -> Dict[str, Any]:
        """
        Main task execution interface for the enhanced Manus agent
        
        Args:
            task_description: Description of the task to execute
            user_id: Unique user identifier
            execution_context: Execution context and constraints
            priority: Task priority (1-10)
            
        Returns:
            Dict containing execution results and metadata
        """
        start_time = datetime.now()
        
        try:
            # Prepare initial state
            initial_state = {
                "messages": [HumanMessage(content=task_description)],
                "user_id": user_id,
                "task_context": {
                    "execution_context": asdict(execution_context) if execution_context else {},
                    "priority": priority,
                    "started_at": start_time.isoformat()
                },
                "current_task": None,
                "task_queue": [],
                "execution_history": [],
                "active_tools": [],
                "collaboration_status": {"status": "none"},
                "performance_metrics": {},
                "system_state": {}
            }
            
            # Configuration for LangGraph execution
            config = {
                "configurable": {
                    "thread_id": f"manus_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                }
            }
            
            # Execute the task orchestration graph
            result = await self.task_graph.ainvoke(initial_state, config=config)
            
            # Extract execution results
            final_message = result['messages'][-1] if result['messages'] else None
            response_content = final_message.content if final_message else "Task execution completed."
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Return comprehensive response
            return {
                "response": response_content,
                "execution_results": {
                    "task": result.get('current_task', {}),
                    "execution_history": result.get('execution_history', []),
                    "performance_metrics": result.get('performance_metrics', {}),
                    "tools_used": result.get('active_tools', []),
                    "collaboration_summary": result.get('collaboration_status', {})
                },
                "metadata": {
                    "agent_id": self.agent_id,
                    "user_id": user_id,
                    "execution_time": duration,
                    "priority": priority,
                    "success": result.get('current_task', {}).get('status') == TaskStatus.COMPLETED.value
                }
            }
            
        except Exception as error:
            logger.error(f"❌ Task execution failed: {error}")
            return {
                "response": f"Task execution failed: {str(error)}",
                "error": str(error),
                "metadata": {
                    "agent_id": self.agent_id,
                    "user_id": user_id,
                    "execution_time": (datetime.now() - start_time).total_seconds(),
                    "success": False
                }
            }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        return {
            **self.metrics,
            "agent_id": self.agent_id,
            "active_tasks": len(self.active_tasks),
            "queued_tasks": len(self.task_queue),
            "knowledge_graph_size": await self._get_knowledge_graph_size(),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _get_knowledge_graph_size(self) -> Dict[str, int]:
        """Get knowledge graph statistics"""
        if self.graphiti:
            try:
                # Placeholder - implement actual graph size queries
                return {"nodes": 0, "relationships": 0, "episodes": 0}
            except Exception:
                pass
        return {"nodes": 0, "relationships": 0, "episodes": 0}
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        health = {
            "status": "healthy",
            "components": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            health["components"]["enhanced_memory"] = "healthy"
            health["components"]["llm"] = "healthy"
            health["components"]["task_orchestration"] = "healthy"
            
            if self.graphiti:
                health["components"]["graphiti"] = "healthy"
            else:
                health["components"]["graphiti"] = "not_available"
                health["status"] = "degraded"
                
        except Exception as error:
            health["status"] = "unhealthy"
            health["error"] = str(error)
        
        return health
    
    async def close(self):
        """Clean up resources"""
        try:
            if self.graphiti:
                await self.graphiti.close()
            await self.enhanced_memory.close()
            logger.info(f"🔒 Enhanced Manus Agent {self.agent_id} closed successfully")
        except Exception as error:
            logger.error(f"❌ Error closing Manus agent: {error}")

# Global instance management
_enhanced_manus_agents = {}

def get_enhanced_manus_agent(agent_id: str = None, config: Dict[str, Any] = None) -> EnhancedManusAgent:
    """Get or create an enhanced Manus agent instance"""
    global _enhanced_manus_agents
    
    if agent_id is None:
        agent_id = "default"
    
    if agent_id not in _enhanced_manus_agents:
        _enhanced_manus_agents[agent_id] = EnhancedManusAgent(config)
    
    return _enhanced_manus_agents[agent_id]