# Optimized MCP Agent with Performance Enhancements
# High-performance version with caching, monitoring, and optimization

from typing import Dict, List, Any, Optional, Union, Callable
from langgraph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import asyncio
import json
import logging
import time
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from functools import wraps
import aioredis
from collections import defaultdict

@dataclass
class OptimizedMCPState:
    """Enhanced state with performance tracking"""
    messages: List[BaseMessage] = field(default_factory=list)
    current_task: Optional[str] = None
    tools_available: List[str] = field(default_factory=list)
    execution_context: Dict[str, Any] = field(default_factory=dict)
    reasoning_chain: List[Dict] = field(default_factory=list)
    error_count: int = 0
    max_retries: int = 3
    confidence_score: float = 0.0
    memory_context: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    cache_hits: int = 0
    cache_misses: int = 0
    execution_time: float = 0.0
    token_usage: Dict[str, int] = field(default_factory=dict)
    optimization_level: str = "standard"

class PerformanceMonitor:
    """Monitor and track agent performance"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.start_time = None
        
    def start_timing(self, operation: str):
        """Start timing an operation"""
        self.start_time = time.time()
        
    def end_timing(self, operation: str):
        """End timing and record"""
        if self.start_time:
            duration = time.time() - self.start_time
            self.metrics[f"{operation}_duration"].append(duration)
            self.start_time = None
            return duration
        return 0
    
    def record_metric(self, name: str, value: Any):
        """Record a metric"""
        self.metrics[name].append({
            "value": value,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_summary(self) -> Dict:
        """Get performance summary"""
        summary = {}
        for metric, values in self.metrics.items():
            if metric.endswith('_duration'):
                summary[metric] = {
                    "avg": sum(values) / len(values) if values else 0,
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0,
                    "count": len(values)
                }
            else:
                summary[metric] = values[-5:]  # Last 5 values
        return summary

class CacheManager:
    """Intelligent caching for expensive operations"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url
        self.local_cache = {}
        self.cache_ttl = 3600  # 1 hour
        self.redis_client = None
        
    async def initialize(self):
        """Initialize Redis connection if available"""
        if self.redis_url:
            try:
                self.redis_client = await aioredis.from_url(self.redis_url)
            except Exception as e:
                logging.warning(f"Redis connection failed, using local cache: {e}")
    
    def _generate_key(self, operation: str, params: Dict) -> str:
        """Generate cache key"""
        params_str = json.dumps(params, sort_keys=True)
        return f"{operation}:{hashlib.md5(params_str.encode()).hexdigest()}"
    
    async def get(self, operation: str, params: Dict) -> Optional[Any]:
        """Get from cache"""
        key = self._generate_key(operation, params)
        
        # Try Redis first
        if self.redis_client:
            try:
                cached = await self.redis_client.get(key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logging.warning(f"Redis get failed: {e}")
        
        # Fallback to local cache
        if key in self.local_cache:
            entry = self.local_cache[key]
            if datetime.now() < entry['expires']:
                return entry['data']
            else:
                del self.local_cache[key]
        
        return None
    
    async def set(self, operation: str, params: Dict, data: Any):
        """Set in cache"""
        key = self._generate_key(operation, params)
        
        # Try Redis first
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    key, 
                    self.cache_ttl, 
                    json.dumps(data)
                )
                return
            except Exception as e:
                logging.warning(f"Redis set failed: {e}")
        
        # Fallback to local cache
        self.local_cache[key] = {
            'data': data,
            'expires': datetime.now() + timedelta(seconds=self.cache_ttl)
        }

def cached_operation(cache_manager: CacheManager, operation_name: str):
    """Decorator for caching expensive operations"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from arguments
            cache_params = {
                'args': str(args),
                'kwargs': kwargs
            }
            
            # Try to get from cache
            cached_result = await cache_manager.get(operation_name, cache_params)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache_manager.set(operation_name, cache_params, result)
            
            return result
        return wrapper
    return decorator

class OptimizedMCPAgent:
    """
    High-performance MCP Agent with caching, monitoring,
    and intelligent optimization
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.llm = self._initialize_llm()
        self.tools = {}
        self.graph = self._build_execution_graph()
        self.logger = logging.getLogger(__name__)
        
        # Performance components
        self.monitor = PerformanceMonitor()
        self.cache_manager = CacheManager(self.config.get('redis_url'))
        self.optimization_strategies = self._initialize_optimizations()
        
        # Initialize async components
        asyncio.create_task(self._initialize_async_components())
    
    async def _initialize_async_components(self):
        """Initialize async components"""
        await self.cache_manager.initialize()
    
    def _initialize_llm(self) -> Union[ChatOpenAI, ChatAnthropic]:
        """Initialize optimized language model"""
        provider = self.config.get('llm_provider', 'openai')
        
        # Optimization settings
        optimized_config = {
            'temperature': self.config.get('temperature', 0.1),
            'max_tokens': self.config.get('max_tokens', 2000),  # Reduced for efficiency
            'request_timeout': 30,  # Timeout for requests
            'max_retries': 2  # Reduced retries
        }
        
        if provider == 'openai':
            return ChatOpenAI(
                model=self.config.get('model', 'gpt-4'),
                **optimized_config
            )
        elif provider == 'anthropic':
            return ChatAnthropic(
                model=self.config.get('model', 'claude-3-sonnet-20240229'),
                **optimized_config
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def _initialize_optimizations(self) -> Dict[str, Callable]:
        """Initialize optimization strategies"""
        return {
            'fast': self._fast_optimization,
            'balanced': self._balanced_optimization,
            'thorough': self._thorough_optimization
        }
    
    def _build_execution_graph(self) -> StateGraph:
        """Build optimized execution graph"""
        graph = StateGraph(OptimizedMCPState)
        
        # Core nodes with performance monitoring
        graph.add_node("analyzer", self._monitored_analyze_task)
        graph.add_node("planner", self._monitored_plan_execution)
        graph.add_node("executor", self._monitored_execute_plan)
        graph.add_node("validator", self._monitored_validate_results)
        graph.add_node("optimizer", self._monitored_optimize_approach)
        graph.add_node("memory_updater", self._monitored_update_memory)
        graph.add_node("error_handler", self._monitored_handle_errors)
        
        # Optimized edges
        graph.add_edge("analyzer", "planner")
        graph.add_edge("planner", "executor")
        graph.add_edge("executor", "validator")
        
        # Smart conditional routing
        graph.add_conditional_edges(
            "validator",
            self._intelligent_routing,
            {
                "retry": "error_handler",
                "optimize": "optimizer",
                "complete": "memory_updater",
                "fast_complete": END  # Skip memory update for simple tasks
            }
        )
        
        graph.add_edge("error_handler", "planner")
        graph.add_edge("optimizer", "executor")
        graph.add_edge("memory_updater", END)
        
        graph.set_entry_point("analyzer")
        return graph.compile()
    
    def _monitored_wrapper(self, operation_name: str):
        """Wrapper to add monitoring to operations"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(state: OptimizedMCPState):
                self.monitor.start_timing(operation_name)
                
                try:
                    result = await func(state)
                    duration = self.monitor.end_timing(operation_name)
                    
                    # Update performance metrics
                    state.performance_metrics[f"{operation_name}_duration"] = duration
                    self.monitor.record_metric(f"{operation_name}_success", True)
                    
                    return result
                    
                except Exception as e:
                    self.monitor.end_timing(operation_name)
                    self.monitor.record_metric(f"{operation_name}_error", str(e))
                    raise
                    
            return wrapper
        return decorator
    
    @cached_operation(None, "task_analysis")  # Will be set after initialization
    async def _cached_analyze_task(self, task: str, context: Dict) -> Dict:
        """Cached task analysis"""
        analysis_prompt = f"""
        Analyze this task efficiently:
        Task: {task}
        Context: {json.dumps(context)}
        
        Provide concise analysis in JSON:
        {{
            "task_type": "code|research|analysis|creative|other",
            "complexity": "low|medium|high",
            "required_tools": ["tool1"],
            "estimated_steps": 2,
            "confidence_assessment": 0.8,
            "optimization_level": "fast|balanced|thorough"
        }}
        """
        
        response = await self.llm.ainvoke([SystemMessage(content=analysis_prompt)])
        return json.loads(response.content)
    
    async def _monitored_analyze_task(self, state: OptimizedMCPState) -> OptimizedMCPState:
        """Monitored task analysis with caching"""
        self.monitor.start_timing("analysis")
        
        try:
            if state.messages:
                latest_message = state.messages[-1]
                if isinstance(latest_message, HumanMessage):
                    state.current_task = latest_message.content
            
            # Use cached analysis
            analysis = await self._cached_analyze_task(
                state.current_task, 
                state.execution_context
            )
            
            # Update state
            state.execution_context.update(analysis)
            state.tools_available = list(self.tools.keys())
            state.confidence_score = analysis.get('confidence_assessment', 0.5)
            state.optimization_level = analysis.get('optimization_level', 'balanced')
            
            # Optimized reasoning chain (less verbose)
            state.reasoning_chain.append({
                "step": "analysis",
                "timestamp": datetime.now().isoformat(),
                "complexity": analysis['complexity'],
                "confidence": state.confidence_score
            })
            
            duration = self.monitor.end_timing("analysis")
            state.performance_metrics['analysis_duration'] = duration
            
            self.logger.info(f"Task analyzed in {duration:.2f}s: {analysis['task_type']}")
            
        except Exception as e:
            self.monitor.end_timing("analysis")
            self.logger.error(f"Error in task analysis: {e}")
            state.error_count += 1
            
        return state
    
    async def _monitored_plan_execution(self, state: OptimizedMCPState) -> OptimizedMCPState:
        """Optimized execution planning"""
        self.monitor.start_timing("planning")
        
        try:
            # Use optimization strategy based on complexity
            optimization_func = self.optimization_strategies.get(
                state.optimization_level, 
                self._balanced_optimization
            )
            
            plan = await optimization_func(state)
            state.execution_context['execution_plan'] = plan
            
            duration = self.monitor.end_timing("planning")
            state.performance_metrics['planning_duration'] = duration
            
            self.logger.info(f"Plan created in {duration:.2f}s with {len(plan['steps'])} steps")
            
        except Exception as e:
            self.monitor.end_timing("planning")
            self.logger.error(f"Error in planning: {e}")
            state.error_count += 1
            
        return state
    
    async def _fast_optimization(self, state: OptimizedMCPState) -> Dict:
        """Fast optimization for simple tasks"""
        return {
            "steps": [
                {
                    "id": 1,
                    "action": "Execute task directly",
                    "tool": None,
                    "expected_output": "Quick result"
                }
            ],
            "fallback_strategies": [],
            "quality_checks": ["basic_validation"]
        }
    
    async def _balanced_optimization(self, state: OptimizedMCPState) -> Dict:
        """Balanced optimization for most tasks"""
        analysis = state.execution_context
        
        return {
            "steps": [
                {
                    "id": 1,
                    "action": "Analyze requirements",
                    "tool": None,
                    "expected_output": "Requirements understood"
                },
                {
                    "id": 2,
                    "action": "Execute main task",
                    "tool": analysis.get('required_tools', [None])[0],
                    "expected_output": "Task completed"
                }
            ],
            "fallback_strategies": ["retry_with_different_approach"],
            "quality_checks": ["result_validation", "format_check"]
        }
    
    async def _thorough_optimization(self, state: OptimizedMCPState) -> Dict:
        """Thorough optimization for complex tasks"""
        analysis = state.execution_context
        
        return {
            "steps": [
                {
                    "id": 1,
                    "action": "Deep analysis",
                    "tool": None,
                    "expected_output": "Comprehensive understanding"
                },
                {
                    "id": 2,
                    "action": "Plan detailed approach",
                    "tool": None,
                    "expected_output": "Detailed plan"
                },
                {
                    "id": 3,
                    "action": "Execute with monitoring",
                    "tool": analysis.get('required_tools', [None])[0],
                    "expected_output": "High-quality result"
                },
                {
                    "id": 4,
                    "action": "Validate and refine",
                    "tool": None,
                    "expected_output": "Validated result"
                }
            ],
            "fallback_strategies": ["retry", "alternative_approach", "escalate"],
            "quality_checks": ["comprehensive_validation", "performance_check", "accuracy_check"]
        }
    
    async def _monitored_execute_plan(self, state: OptimizedMCPState) -> OptimizedMCPState:
        """Optimized plan execution with parallel processing where possible"""
        self.monitor.start_timing("execution")
        
        try:
            plan = state.execution_context.get('execution_plan', {})
            steps = plan.get('steps', [])
            
            # Determine if steps can be parallelized
            if len(steps) > 1 and state.optimization_level == 'fast':
                results = await self._parallel_execution(steps, state)
            else:
                results = await self._sequential_execution(steps, state)
            
            state.execution_context['execution_results'] = results
            
            # Calculate performance metrics
            successful_steps = sum(1 for r in results if r.get('success', False))
            success_rate = successful_steps / len(steps) if steps else 0
            state.confidence_score = success_rate
            
            duration = self.monitor.end_timing("execution")
            state.performance_metrics['execution_duration'] = duration
            
            self.logger.info(f"Execution completed in {duration:.2f}s: {successful_steps}/{len(steps)} successful")
            
        except Exception as e:
            self.monitor.end_timing("execution")
            self.logger.error(f"Error in execution: {e}")
            state.error_count += 1
            
        return state
    
    async def _parallel_execution(self, steps: List[Dict], state: OptimizedMCPState) -> List[Dict]:
        """Execute steps in parallel where possible"""
        # Simple parallel execution for independent steps
        tasks = [self._execute_step(step, state) for step in steps]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "step_id": steps[i]['id'],
                    "success": False,
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _sequential_execution(self, steps: List[Dict], state: OptimizedMCPState) -> List[Dict]:
        """Execute steps sequentially"""
        results = []
        for step in steps:
            result = await self._execute_step(step, state)
            results.append(result)
            
            # Early termination on failure for efficiency
            if not result.get('success', False) and state.optimization_level == 'fast':
                break
        
        return results
    
    async def _execute_step(self, step: Dict, state: OptimizedMCPState) -> Dict:
        """Optimized step execution"""
        try:
            tool_name = step.get('tool')
            action = step.get('action')
            
            if tool_name and tool_name in self.tools:
                tool = self.tools[tool_name]
                result = await tool.ainvoke(action)
                
                return {
                    "step_id": step['id'],
                    "success": True,
                    "result": result,
                    "tool_used": tool_name
                }
            else:
                # Optimized LLM call with reduced context
                response = await self.llm.ainvoke([
                    SystemMessage(content=f"Execute concisely: {action}")
                ])
                
                return {
                    "step_id": step['id'],
                    "success": True,
                    "result": response.content,
                    "tool_used": "llm"
                }
                
        except Exception as e:
            return {
                "step_id": step['id'],
                "success": False,
                "error": str(e),
                "tool_used": step.get('tool', 'unknown')
            }
    
    async def _monitored_validate_results(self, state: OptimizedMCPState) -> OptimizedMCPState:
        """Optimized validation with smart checks"""
        self.monitor.start_timing("validation")
        
        try:
            # Skip detailed validation for fast optimization
            if state.optimization_level == 'fast':
                validation = {
                    "overall_success": state.confidence_score > 0.5,
                    "quality_score": state.confidence_score,
                    "needs_retry": False,
                    "needs_optimization": False
                }
            else:
                validation = await self._detailed_validation(state)
            
            state.execution_context['validation'] = validation
            state.confidence_score = validation.get('quality_score', state.confidence_score)
            
            duration = self.monitor.end_timing("validation")
            state.performance_metrics['validation_duration'] = duration
            
        except Exception as e:
            self.monitor.end_timing("validation")
            self.logger.error(f"Error in validation: {e}")
            state.error_count += 1
            
        return state
    
    async def _detailed_validation(self, state: OptimizedMCPState) -> Dict:
        """Detailed validation for complex tasks"""
        results = state.execution_context.get('execution_results', [])
        
        validation_prompt = f"""
        Validate results efficiently:
        Task: {state.current_task}
        Results: {json.dumps(results, indent=2)[:1000]}...
        
        JSON response:
        {{
            "overall_success": true/false,
            "quality_score": 0.8,
            "needs_retry": false,
            "needs_optimization": false
        }}
        """
        
        response = await self.llm.ainvoke([SystemMessage(content=validation_prompt)])
        return json.loads(response.content)
    
    def _intelligent_routing(self, state: OptimizedMCPState) -> str:
        """Intelligent routing based on performance and optimization level"""
        validation = state.execution_context.get('validation', {})
        
        # Fast path for simple successful tasks
        if (state.optimization_level == 'fast' and 
            validation.get('overall_success', False) and 
            state.error_count == 0):
            return "fast_complete"
        
        # Standard routing
        if state.error_count >= state.max_retries:
            return "complete"
        
        if validation.get('needs_retry', False):
            return "retry"
        elif validation.get('needs_optimization', False):
            return "optimize"
        else:
            return "complete"
    
    # Placeholder methods for other monitored operations
    async def _monitored_optimize_approach(self, state: OptimizedMCPState) -> OptimizedMCPState:
        """Monitored optimization"""
        # Implementation similar to base class but with monitoring
        return state
    
    async def _monitored_update_memory(self, state: OptimizedMCPState) -> OptimizedMCPState:
        """Monitored memory update"""
        # Implementation similar to base class but with monitoring
        return state
    
    async def _monitored_handle_errors(self, state: OptimizedMCPState) -> OptimizedMCPState:
        """Monitored error handling"""
        # Implementation similar to base class but with monitoring
        return state
    
    def add_tool(self, name: str, tool: BaseTool):
        """Add tool with performance tracking"""
        self.tools[name] = tool
        self.logger.info(f"Tool added: {name}")
    
    async def execute_task(self, task: str, context: Dict = None) -> Dict:
        """Optimized task execution with comprehensive monitoring"""
        start_time = time.time()
        
        try:
            # Initialize optimized state
            initial_state = OptimizedMCPState(
                messages=[HumanMessage(content=task)],
                execution_context=context or {},
                optimization_level=context.get('optimization_level', 'balanced') if context else 'balanced'
            )
            
            # Run the optimized graph
            final_state = await self.graph.ainvoke(initial_state)
            
            # Calculate total execution time
            total_time = time.time() - start_time
            final_state.execution_time = total_time
            
            # Prepare optimized response
            return {
                "success": final_state.confidence_score > 0.5,
                "confidence": final_state.confidence_score,
                "results": final_state.execution_context.get('execution_results'),
                "performance": {
                    "total_time": total_time,
                    "cache_hits": final_state.cache_hits,
                    "cache_misses": final_state.cache_misses,
                    "optimization_level": final_state.optimization_level,
                    "metrics": final_state.performance_metrics,
                    "monitor_summary": self.monitor.get_summary()
                },
                "reasoning": final_state.reasoning_chain[-3:] if len(final_state.reasoning_chain) > 3 else final_state.reasoning_chain  # Last 3 steps only
            }
            
        except Exception as e:
            total_time = time.time() - start_time
            self.logger.error(f"Error in optimized task execution: {e}")
            return {
                "success": False,
                "error": str(e),
                "confidence": 0.0,
                "performance": {
                    "total_time": total_time,
                    "error": True
                }
            }

# Example usage
if __name__ == "__main__":
    # Initialize optimized agent
    agent = OptimizedMCPAgent({
        'llm_provider': 'openai',
        'model': 'gpt-4',
        'temperature': 0.1,
        'redis_url': 'redis://localhost:6379'  # Optional
    })
    
    # Execute with optimization level
    async def main():
        result = await agent.execute_task(
            "Create a simple function to calculate fibonacci numbers",
            {"optimization_level": "fast", "project_type": "code"}
        )
        print(json.dumps(result, indent=2))
    
    # Run example
    # asyncio.run(main())

