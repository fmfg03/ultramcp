# Complete MCP Agent with LangGraph Integration
# Advanced agent with full MCP capabilities and structured reasoning

from typing import Dict, List, Any, Optional, Union
from langgraph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import asyncio
import json
import logging
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class MCPAgentState:
    """State management for MCP Agent"""
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

class CompleteMCPAgent:
    """
    Complete MCP Agent with advanced reasoning, tool integration,
    and LangGraph-based execution flow
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.llm = self._initialize_llm()
        self.tools = {}
        self.graph = self._build_execution_graph()
        self.logger = logging.getLogger(__name__)
        self.memory_analyzer = None  # Will be connected to Sam's Memory Analyzer
        
    def _initialize_llm(self) -> Union[ChatOpenAI, ChatAnthropic]:
        """Initialize the language model"""
        provider = self.config.get('llm_provider', 'openai')
        
        if provider == 'openai':
            return ChatOpenAI(
                model=self.config.get('model', 'gpt-4'),
                temperature=self.config.get('temperature', 0.1),
                max_tokens=self.config.get('max_tokens', 4000)
            )
        elif provider == 'anthropic':
            return ChatAnthropic(
                model=self.config.get('model', 'claude-3-sonnet-20240229'),
                temperature=self.config.get('temperature', 0.1),
                max_tokens=self.config.get('max_tokens', 4000)
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def _build_execution_graph(self) -> StateGraph:
        """Build the LangGraph execution flow"""
        graph = StateGraph(MCPAgentState)
        
        # Add nodes
        graph.add_node("analyzer", self._analyze_task)
        graph.add_node("planner", self._plan_execution)
        graph.add_node("executor", self._execute_plan)
        graph.add_node("validator", self._validate_results)
        graph.add_node("optimizer", self._optimize_approach)
        graph.add_node("memory_updater", self._update_memory)
        graph.add_node("error_handler", self._handle_errors)
        
        # Define edges
        graph.add_edge("analyzer", "planner")
        graph.add_edge("planner", "executor")
        graph.add_edge("executor", "validator")
        
        # Conditional edges
        graph.add_conditional_edges(
            "validator",
            self._should_retry,
            {
                "retry": "error_handler",
                "optimize": "optimizer", 
                "complete": "memory_updater"
            }
        )
        
        graph.add_edge("error_handler", "planner")
        graph.add_edge("optimizer", "executor")
        graph.add_edge("memory_updater", END)
        
        # Set entry point
        graph.set_entry_point("analyzer")
        
        return graph.compile()
    
    async def _analyze_task(self, state: MCPAgentState) -> MCPAgentState:
        """Analyze the incoming task and context"""
        try:
            # Extract task from messages
            if state.messages:
                latest_message = state.messages[-1]
                if isinstance(latest_message, HumanMessage):
                    state.current_task = latest_message.content
            
            # Analyze task complexity and requirements
            analysis_prompt = f"""
            Analyze this task and provide structured analysis:
            Task: {state.current_task}
            
            Provide analysis in JSON format:
            {{
                "task_type": "code|research|analysis|creative|other",
                "complexity": "low|medium|high",
                "required_tools": ["tool1", "tool2"],
                "estimated_steps": 3,
                "confidence_assessment": 0.8,
                "potential_challenges": ["challenge1", "challenge2"]
            }}
            """
            
            response = await self.llm.ainvoke([SystemMessage(content=analysis_prompt)])
            analysis = json.loads(response.content)
            
            # Update state
            state.execution_context.update(analysis)
            state.tools_available = list(self.tools.keys())
            state.confidence_score = analysis.get('confidence_assessment', 0.5)
            
            # Add to reasoning chain
            state.reasoning_chain.append({
                "step": "analysis",
                "timestamp": datetime.now().isoformat(),
                "analysis": analysis,
                "confidence": state.confidence_score
            })
            
            self.logger.info(f"Task analyzed: {analysis['task_type']} complexity: {analysis['complexity']}")
            
        except Exception as e:
            self.logger.error(f"Error in task analysis: {e}")
            state.error_count += 1
            
        return state
    
    async def _plan_execution(self, state: MCPAgentState) -> MCPAgentState:
        """Create detailed execution plan"""
        try:
            analysis = state.execution_context
            
            planning_prompt = f"""
            Create a detailed execution plan for this task:
            Task: {state.current_task}
            Analysis: {json.dumps(analysis, indent=2)}
            Available Tools: {state.tools_available}
            
            Provide plan in JSON format:
            {{
                "steps": [
                    {{
                        "id": 1,
                        "action": "specific action to take",
                        "tool": "tool_name or null",
                        "expected_output": "what we expect",
                        "success_criteria": "how to validate success"
                    }}
                ],
                "fallback_strategies": ["strategy1", "strategy2"],
                "quality_checks": ["check1", "check2"]
            }}
            """
            
            response = await self.llm.ainvoke([SystemMessage(content=planning_prompt)])
            plan = json.loads(response.content)
            
            # Update state
            state.execution_context['execution_plan'] = plan
            
            # Add to reasoning chain
            state.reasoning_chain.append({
                "step": "planning",
                "timestamp": datetime.now().isoformat(),
                "plan": plan,
                "step_count": len(plan['steps'])
            })
            
            self.logger.info(f"Execution plan created with {len(plan['steps'])} steps")
            
        except Exception as e:
            self.logger.error(f"Error in execution planning: {e}")
            state.error_count += 1
            
        return state
    
    async def _execute_plan(self, state: MCPAgentState) -> MCPAgentState:
        """Execute the planned steps"""
        try:
            plan = state.execution_context.get('execution_plan', {})
            steps = plan.get('steps', [])
            results = []
            
            for step in steps:
                step_result = await self._execute_step(step, state)
                results.append(step_result)
                
                # Check if step failed
                if not step_result.get('success', False):
                    self.logger.warning(f"Step {step['id']} failed: {step_result.get('error')}")
                    break
            
            # Update state with results
            state.execution_context['execution_results'] = results
            
            # Calculate overall success
            successful_steps = sum(1 for r in results if r.get('success', False))
            success_rate = successful_steps / len(steps) if steps else 0
            state.confidence_score = success_rate
            
            # Add to reasoning chain
            state.reasoning_chain.append({
                "step": "execution",
                "timestamp": datetime.now().isoformat(),
                "results": results,
                "success_rate": success_rate
            })
            
            self.logger.info(f"Execution completed: {successful_steps}/{len(steps)} steps successful")
            
        except Exception as e:
            self.logger.error(f"Error in execution: {e}")
            state.error_count += 1
            
        return state
    
    async def _execute_step(self, step: Dict, state: MCPAgentState) -> Dict:
        """Execute individual step"""
        try:
            tool_name = step.get('tool')
            action = step.get('action')
            
            if tool_name and tool_name in self.tools:
                # Use tool
                tool = self.tools[tool_name]
                result = await tool.ainvoke(action)
                
                return {
                    "step_id": step['id'],
                    "success": True,
                    "result": result,
                    "tool_used": tool_name
                }
            else:
                # Use LLM for reasoning/analysis
                response = await self.llm.ainvoke([
                    SystemMessage(content=f"Execute this action: {action}")
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
    
    async def _validate_results(self, state: MCPAgentState) -> MCPAgentState:
        """Validate execution results"""
        try:
            results = state.execution_context.get('execution_results', [])
            plan = state.execution_context.get('execution_plan', {})
            
            validation_prompt = f"""
            Validate these execution results against the original task:
            Task: {state.current_task}
            Results: {json.dumps(results, indent=2)}
            Quality Checks: {plan.get('quality_checks', [])}
            
            Provide validation in JSON format:
            {{
                "overall_success": true/false,
                "quality_score": 0.8,
                "issues_found": ["issue1", "issue2"],
                "recommendations": ["rec1", "rec2"],
                "needs_retry": true/false,
                "needs_optimization": true/false
            }}
            """
            
            response = await self.llm.ainvoke([SystemMessage(content=validation_prompt)])
            validation = json.loads(response.content)
            
            # Update state
            state.execution_context['validation'] = validation
            state.confidence_score = validation.get('quality_score', state.confidence_score)
            
            # Add to reasoning chain
            state.reasoning_chain.append({
                "step": "validation",
                "timestamp": datetime.now().isoformat(),
                "validation": validation
            })
            
            self.logger.info(f"Validation completed: success={validation['overall_success']}")
            
        except Exception as e:
            self.logger.error(f"Error in validation: {e}")
            state.error_count += 1
            
        return state
    
    def _should_retry(self, state: MCPAgentState) -> str:
        """Determine next action based on validation"""
        validation = state.execution_context.get('validation', {})
        
        if state.error_count >= state.max_retries:
            return "complete"
        
        if validation.get('needs_retry', False):
            return "retry"
        elif validation.get('needs_optimization', False):
            return "optimize"
        else:
            return "complete"
    
    async def _handle_errors(self, state: MCPAgentState) -> MCPAgentState:
        """Handle errors and prepare for retry"""
        try:
            validation = state.execution_context.get('validation', {})
            issues = validation.get('issues_found', [])
            
            error_analysis_prompt = f"""
            Analyze these issues and provide error handling strategy:
            Issues: {issues}
            Error Count: {state.error_count}
            Max Retries: {state.max_retries}
            
            Provide strategy in JSON format:
            {{
                "root_cause": "description",
                "corrective_actions": ["action1", "action2"],
                "plan_modifications": {{"key": "value"}},
                "confidence_adjustment": -0.1
            }}
            """
            
            response = await self.llm.ainvoke([SystemMessage(content=error_analysis_prompt)])
            error_strategy = json.loads(response.content)
            
            # Apply corrections
            state.execution_context.update(error_strategy.get('plan_modifications', {}))
            state.confidence_score += error_strategy.get('confidence_adjustment', 0)
            state.confidence_score = max(0, min(1, state.confidence_score))
            
            # Add to reasoning chain
            state.reasoning_chain.append({
                "step": "error_handling",
                "timestamp": datetime.now().isoformat(),
                "strategy": error_strategy
            })
            
            self.logger.info(f"Error handling applied: {error_strategy['root_cause']}")
            
        except Exception as e:
            self.logger.error(f"Error in error handling: {e}")
            
        return state
    
    async def _optimize_approach(self, state: MCPAgentState) -> MCPAgentState:
        """Optimize the approach based on results"""
        try:
            validation = state.execution_context.get('validation', {})
            recommendations = validation.get('recommendations', [])
            
            optimization_prompt = f"""
            Optimize the execution approach:
            Current Results: {state.execution_context.get('execution_results', [])}
            Recommendations: {recommendations}
            
            Provide optimizations in JSON format:
            {{
                "optimized_steps": [
                    {{
                        "id": 1,
                        "action": "optimized action",
                        "tool": "tool_name",
                        "optimization_reason": "why this is better"
                    }}
                ],
                "expected_improvement": 0.2
            }}
            """
            
            response = await self.llm.ainvoke([SystemMessage(content=optimization_prompt)])
            optimization = json.loads(response.content)
            
            # Update execution plan
            state.execution_context['execution_plan']['steps'] = optimization['optimized_steps']
            
            # Add to reasoning chain
            state.reasoning_chain.append({
                "step": "optimization",
                "timestamp": datetime.now().isoformat(),
                "optimization": optimization
            })
            
            self.logger.info("Approach optimized for better results")
            
        except Exception as e:
            self.logger.error(f"Error in optimization: {e}")
            
        return state
    
    async def _update_memory(self, state: MCPAgentState) -> MCPAgentState:
        """Update memory with learned experiences"""
        try:
            # Prepare memory entry
            memory_entry = {
                "task": state.current_task,
                "approach": state.execution_context.get('execution_plan'),
                "results": state.execution_context.get('execution_results'),
                "validation": state.execution_context.get('validation'),
                "reasoning_chain": state.reasoning_chain,
                "final_confidence": state.confidence_score,
                "timestamp": datetime.now().isoformat(),
                "performance_metrics": {
                    "steps_executed": len(state.execution_context.get('execution_results', [])),
                    "error_count": state.error_count,
                    "success_rate": state.confidence_score
                }
            }
            
            # Store in memory (would connect to Sam's Memory Analyzer)
            state.memory_context['latest_experience'] = memory_entry
            
            # Add final reasoning step
            state.reasoning_chain.append({
                "step": "memory_update",
                "timestamp": datetime.now().isoformat(),
                "memory_stored": True
            })
            
            self.logger.info("Memory updated with execution experience")
            
        except Exception as e:
            self.logger.error(f"Error updating memory: {e}")
            
        return state
    
    def add_tool(self, name: str, tool: BaseTool):
        """Add a tool to the agent's toolkit"""
        self.tools[name] = tool
        self.logger.info(f"Tool added: {name}")
    
    async def execute_task(self, task: str, context: Dict = None) -> Dict:
        """Main execution method"""
        try:
            # Initialize state
            initial_state = MCPAgentState(
                messages=[HumanMessage(content=task)],
                execution_context=context or {}
            )
            
            # Run the graph
            final_state = await self.graph.ainvoke(initial_state)
            
            # Prepare response
            return {
                "success": final_state.confidence_score > 0.5,
                "confidence": final_state.confidence_score,
                "results": final_state.execution_context.get('execution_results'),
                "reasoning": final_state.reasoning_chain,
                "memory": final_state.memory_context
            }
            
        except Exception as e:
            self.logger.error(f"Error in task execution: {e}")
            return {
                "success": False,
                "error": str(e),
                "confidence": 0.0
            }

# Example usage and configuration
if __name__ == "__main__":
    # Initialize agent
    agent = CompleteMCPAgent({
        'llm_provider': 'openai',
        'model': 'gpt-4',
        'temperature': 0.1
    })
    
    # Add tools (examples)
    # agent.add_tool("code_interpreter", CodeInterpreterTool())
    # agent.add_tool("github_tool", GitHubTool())
    # agent.add_tool("search_tool", SearchTool())
    
    # Execute task
    async def main():
        result = await agent.execute_task(
            "Create a simple web application with user authentication",
            {"project_type": "web_app", "framework": "react"}
        )
        print(json.dumps(result, indent=2))
    
    # Run example
    # asyncio.run(main())

