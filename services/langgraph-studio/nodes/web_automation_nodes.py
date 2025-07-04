"""
Specialized LangGraph nodes for web automation workflows
Integration with UltraMCP Playwright-MCP adapter
"""

import json
import logging
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.graph.state import add_messages
import requests
from datetime import datetime
import asyncio
import time

# Configure logging
logger = logging.getLogger(__name__)

class WebAutomationState(TypedDict):
    """Enhanced state for web automation with memory and context"""
    messages: Annotated[List[Any], add_messages]
    task: str
    url: str
    workflow_plan: List[Dict[str, Any]]
    current_step: int
    step_results: List[Dict[str, Any]]
    screenshots: List[str]
    extracted_data: Dict[str, Any]
    errors: List[str]
    session_id: str
    context: Dict[str, Any]  # For cross-step context
    performance_metrics: Dict[str, Any]
    retry_count: int
    max_retries: int
    completed: bool
    final_result: Dict[str, Any]

class WebAutomationNodes:
    """
    Collection of specialized nodes for web automation workflows
    """
    
    def __init__(self, mcp_base_url: str = "http://sam.chat:3000"):
        self.mcp_base_url = mcp_base_url
        self.performance_tracker = {}
        
    def _call_playwright_mcp(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call Playwright-MCP via UltraMCP orchestration API"""
        start_time = time.time()
        try:
            response = requests.post(
                f"{self.mcp_base_url}/api/mcp/execute",
                json={
                    "toolId": f"playwright-mcp/{tool_name}",
                    "params": params,
                    "session_id": params.get("session_id")
                },
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            
            # Track performance
            execution_time = time.time() - start_time
            self.performance_tracker[tool_name] = self.performance_tracker.get(tool_name, [])
            self.performance_tracker[tool_name].append(execution_time)
            
            return result
            
        except Exception as e:
            logger.error(f"Error calling Playwright-MCP {tool_name}: {e}")
            raise

    def task_analyzer_node(self, state: WebAutomationState) -> WebAutomationState:
        """
        Advanced task analysis and workflow planning node
        Breaks down complex web automation tasks into executable steps
        """
        logger.info(f"Analyzing web automation task: {state['task']}")
        
        # Initialize performance tracking
        state["performance_metrics"] = {
            "start_time": datetime.now().isoformat(),
            "steps_planned": 0,
            "steps_executed": 0,
            "errors_encountered": 0
        }
        
        # Analyze task complexity and create detailed plan
        task = state["task"]
        url = state.get("url", "")
        
        # Enhanced task analysis using pattern recognition
        workflow_plan = self._analyze_and_plan_workflow(task, url)
        
        state["workflow_plan"] = workflow_plan
        state["current_step"] = 0
        state["step_results"] = []
        state["screenshots"] = []
        state["extracted_data"] = {}
        state["errors"] = []
        state["context"] = {"initial_task": task, "target_url": url}
        state["retry_count"] = 0
        state["max_retries"] = 3
        state["performance_metrics"]["steps_planned"] = len(workflow_plan)
        
        # Add analysis message
        state["messages"].append(AIMessage(
            content=f"Analyzed task: '{task}'. Created workflow plan with {len(workflow_plan)} steps."
        ))
        
        return state
    
    def _analyze_and_plan_workflow(self, task: str, url: str) -> List[Dict[str, Any]]:
        """
        Intelligent workflow planning based on task analysis
        """
        # Basic task pattern recognition
        task_lower = task.lower()
        plan = []
        
        # Always start with navigation if URL provided
        if url:
            plan.append({
                "step_id": "nav_001",
                "action": "navigate",
                "description": f"Navigate to {url}",
                "params": {"url": url, "waitFor": "networkidle"},
                "expected_outcome": "page_loaded",
                "timeout": 30000,
                "retry_on_failure": True
            })
        
        # Add initial screenshot for documentation
        plan.append({
            "step_id": "doc_001", 
            "action": "screenshot",
            "description": "Take initial page screenshot",
            "params": {"fullPage": True, "quality": 90},
            "expected_outcome": "screenshot_captured",
            "timeout": 10000,
            "retry_on_failure": False
        })
        
        # Pattern-based step generation
        if "search" in task_lower:
            plan.extend(self._generate_search_steps(task))
        elif "form" in task_lower or "submit" in task_lower:
            plan.extend(self._generate_form_steps(task))
        elif "extract" in task_lower or "scrape" in task_lower:
            plan.extend(self._generate_extraction_steps(task))
        elif "click" in task_lower:
            plan.extend(self._generate_click_steps(task))
        elif "login" in task_lower:
            plan.extend(self._generate_login_steps(task))
        else:
            # Generic interaction steps
            plan.extend(self._generate_generic_steps(task))
        
        # Always end with final screenshot and summary
        plan.append({
            "step_id": "doc_final",
            "action": "screenshot", 
            "description": "Take final screenshot for verification",
            "params": {"fullPage": True, "quality": 90},
            "expected_outcome": "final_screenshot_captured",
            "timeout": 10000,
            "retry_on_failure": False
        })
        
        return plan
    
    def _generate_search_steps(self, task: str) -> List[Dict[str, Any]]:
        """Generate steps for search-related tasks"""
        return [
            {
                "step_id": "search_001",
                "action": "wait_for",
                "description": "Wait for search input to be visible",
                "params": {"selector": "input[type='search'], input[name*='search'], input[placeholder*='search']", "state": "visible"},
                "expected_outcome": "search_field_ready",
                "timeout": 15000,
                "retry_on_failure": True
            },
            {
                "step_id": "search_002",
                "action": "type",
                "description": "Enter search query",
                "params": {"selector": "input[type='search'], input[name*='search'], input[placeholder*='search']", "text": "SEARCH_TERM", "clear": True},
                "expected_outcome": "search_query_entered",
                "timeout": 10000,
                "retry_on_failure": True
            },
            {
                "step_id": "search_003",
                "action": "click",
                "description": "Click search button",
                "params": {"selector": "button[type='submit'], input[type='submit'], button:contains('Search')", "options": {"timeout": 10000}},
                "expected_outcome": "search_submitted",
                "timeout": 15000,
                "retry_on_failure": True
            }
        ]
    
    def _generate_form_steps(self, task: str) -> List[Dict[str, Any]]:
        """Generate steps for form-related tasks"""
        return [
            {
                "step_id": "form_001",
                "action": "wait_for",
                "description": "Wait for form to be visible",
                "params": {"selector": "form, [role='form']", "state": "visible"},
                "expected_outcome": "form_ready",
                "timeout": 15000,
                "retry_on_failure": True
            },
            {
                "step_id": "form_002",
                "action": "extract",
                "description": "Analyze form structure",
                "params": {
                    "schema": {
                        "form_fields": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string"},
                                    "name": {"type": "string"},
                                    "placeholder": {"type": "string"},
                                    "required": {"type": "boolean"}
                                }
                            }
                        }
                    },
                    "selector": "form"
                },
                "expected_outcome": "form_analyzed",
                "timeout": 10000,
                "retry_on_failure": False
            }
        ]
    
    def _generate_extraction_steps(self, task: str) -> List[Dict[str, Any]]:
        """Generate steps for data extraction tasks"""
        return [
            {
                "step_id": "extract_001",
                "action": "wait_for",
                "description": "Wait for content to load",
                "params": {"selector": "main, [role='main'], #content, .content", "state": "visible"},
                "expected_outcome": "content_loaded",
                "timeout": 15000,
                "retry_on_failure": True
            },
            {
                "step_id": "extract_002",
                "action": "extract",
                "description": "Extract page data",
                "params": {
                    "schema": {
                        "title": {"type": "string"},
                        "content": {"type": "string"},
                        "links": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "metadata": {"type": "object"}
                    }
                },
                "expected_outcome": "data_extracted",
                "timeout": 20000,
                "retry_on_failure": True
            }
        ]
    
    def _generate_click_steps(self, task: str) -> List[Dict[str, Any]]:
        """Generate steps for click-based interactions"""
        return [
            {
                "step_id": "click_001",
                "action": "wait_for",
                "description": "Wait for target element",
                "params": {"selector": "DYNAMIC_SELECTOR", "state": "visible"},
                "expected_outcome": "element_ready",
                "timeout": 15000,
                "retry_on_failure": True
            },
            {
                "step_id": "click_002",
                "action": "click",
                "description": "Click target element",
                "params": {"selector": "DYNAMIC_SELECTOR", "options": {"timeout": 10000}},
                "expected_outcome": "element_clicked",
                "timeout": 15000,
                "retry_on_failure": True
            }
        ]
    
    def _generate_login_steps(self, task: str) -> List[Dict[str, Any]]:
        """Generate steps for login workflows"""
        return [
            {
                "step_id": "login_001",
                "action": "wait_for",
                "description": "Wait for login form",
                "params": {"selector": "input[type='email'], input[type='text'][name*='user'], input[name*='login']", "state": "visible"},
                "expected_outcome": "login_form_ready",
                "timeout": 15000,
                "retry_on_failure": True
            },
            {
                "step_id": "login_002",
                "action": "type",
                "description": "Enter username/email",
                "params": {"selector": "input[type='email'], input[type='text'][name*='user'], input[name*='login']", "text": "USERNAME", "clear": True},
                "expected_outcome": "username_entered",
                "timeout": 10000,
                "retry_on_failure": True
            },
            {
                "step_id": "login_003",
                "action": "type",
                "description": "Enter password",
                "params": {"selector": "input[type='password']", "text": "PASSWORD", "clear": True},
                "expected_outcome": "password_entered",
                "timeout": 10000,
                "retry_on_failure": True
            },
            {
                "step_id": "login_004",
                "action": "click",
                "description": "Click login button",
                "params": {"selector": "button[type='submit'], input[type='submit'], button:contains('Login')", "options": {"timeout": 10000}},
                "expected_outcome": "login_submitted",
                "timeout": 15000,
                "retry_on_failure": True
            }
        ]
    
    def _generate_generic_steps(self, task: str) -> List[Dict[str, Any]]:
        """Generate generic interaction steps"""
        return [
            {
                "step_id": "generic_001",
                "action": "extract",
                "description": "Analyze page structure",
                "params": {
                    "schema": {
                        "page_title": {"type": "string"},
                        "interactive_elements": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "tag": {"type": "string"},
                                    "text": {"type": "string"},
                                    "selector": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "expected_outcome": "page_analyzed",
                "timeout": 15000,
                "retry_on_failure": False
            }
        ]

    def step_executor_node(self, state: WebAutomationState) -> WebAutomationState:
        """
        Execute individual workflow steps with error handling and retry logic
        """
        if state["current_step"] >= len(state["workflow_plan"]):
            state["completed"] = True
            return state
        
        current_step = state["workflow_plan"][state["current_step"]]
        step_id = current_step["step_id"]
        action = current_step["action"]
        
        logger.info(f"Executing step {state['current_step']}: {step_id} ({action})")
        
        step_start_time = time.time()
        step_result = {
            "step_id": step_id,
            "action": action,
            "description": current_step["description"],
            "start_time": datetime.now().isoformat(),
            "success": False,
            "result": None,
            "error": None,
            "execution_time": 0,
            "retry_count": 0
        }
        
        try:
            # Add session context to params
            params = current_step["params"].copy()
            params["session_id"] = state["session_id"]
            
            # Execute the step
            if action == "navigate":
                result = self._call_playwright_mcp("navigate", params)
            elif action == "screenshot":
                result = self._call_playwright_mcp("screenshot", params)
                if result and "path" in result:
                    state["screenshots"].append(result["path"])
            elif action == "click":
                result = self._call_playwright_mcp("click", params)
            elif action == "type":
                result = self._call_playwright_mcp("type", params)
            elif action == "extract":
                result = self._call_playwright_mcp("extract", params)
                if result and "data" in result:
                    # Store extracted data in state context
                    step_data_key = f"step_{step_id}_data"
                    state["extracted_data"][step_data_key] = result["data"]
                    state["context"][step_data_key] = result["data"]
            elif action == "wait_for":
                result = self._call_playwright_mcp("wait_for", params)
            else:
                raise ValueError(f"Unknown action: {action}")
            
            # Mark step as successful
            step_result["success"] = True
            step_result["result"] = result
            step_result["execution_time"] = time.time() - step_start_time
            
            # Update performance metrics
            state["performance_metrics"]["steps_executed"] += 1
            
            logger.info(f"Step {step_id} completed successfully")
            
        except Exception as e:
            error_msg = f"Error in step {step_id}: {str(e)}"
            logger.error(error_msg)
            
            step_result["error"] = error_msg
            step_result["execution_time"] = time.time() - step_start_time
            
            # Handle retry logic
            if current_step.get("retry_on_failure", False) and state["retry_count"] < state["max_retries"]:
                state["retry_count"] += 1
                step_result["retry_count"] = state["retry_count"]
                logger.info(f"Retrying step {step_id} (attempt {state['retry_count']})")
                # Don't advance step, will retry
                state["step_results"].append(step_result)
                return state
            else:
                # Log error and continue
                state["errors"].append(error_msg)
                state["performance_metrics"]["errors_encountered"] += 1
        
        # Store step result
        state["step_results"].append(step_result)
        
        # Move to next step
        state["current_step"] += 1
        state["retry_count"] = 0  # Reset retry count for next step
        
        # Add step completion message
        if step_result["success"]:
            state["messages"].append(AIMessage(
                content=f"Completed step: {current_step['description']}"
            ))
        else:
            state["messages"].append(AIMessage(
                content=f"Failed step: {current_step['description']} - {step_result['error']}"
            ))
        
        return state

    def result_validator_node(self, state: WebAutomationState) -> WebAutomationState:
        """
        Validate workflow results and compile comprehensive summary
        """
        logger.info("Validating web automation workflow results")
        
        # Calculate performance metrics
        total_steps = len(state["workflow_plan"])
        successful_steps = sum(1 for result in state["step_results"] if result["success"])
        failed_steps = total_steps - successful_steps
        
        total_execution_time = sum(result["execution_time"] for result in state["step_results"])
        
        # Compile final result
        state["final_result"] = {
            "workflow_summary": {
                "task": state["task"],
                "url": state.get("url"),
                "session_id": state["session_id"],
                "completed_at": datetime.now().isoformat(),
                "total_duration": total_execution_time
            },
            "execution_metrics": {
                "total_steps": total_steps,
                "successful_steps": successful_steps,
                "failed_steps": failed_steps,
                "success_rate": (successful_steps / total_steps) * 100 if total_steps > 0 else 0,
                "total_execution_time": total_execution_time,
                "average_step_time": total_execution_time / total_steps if total_steps > 0 else 0
            },
            "outputs": {
                "screenshots_captured": len(state["screenshots"]),
                "screenshot_paths": state["screenshots"],
                "extracted_data": state["extracted_data"],
                "context_data": state["context"]
            },
            "errors_and_issues": {
                "error_count": len(state["errors"]),
                "errors": state["errors"],
                "failed_steps": [result for result in state["step_results"] if not result["success"]]
            },
            "step_details": state["step_results"],
            "performance_metrics": state["performance_metrics"]
        }
        
        # Update completion status
        state["completed"] = True
        state["performance_metrics"]["end_time"] = datetime.now().isoformat()
        
        # Add final summary message
        success_rate = state["final_result"]["execution_metrics"]["success_rate"]
        state["messages"].append(AIMessage(
            content=f"Web automation workflow completed. Success rate: {success_rate:.1f}% ({successful_steps}/{total_steps} steps)"
        ))
        
        logger.info(f"Workflow validation completed. Success rate: {success_rate:.1f}%")
        
        return state

    def error_recovery_node(self, state: WebAutomationState) -> WebAutomationState:
        """
        Handle error recovery and alternative approaches
        """
        logger.info("Initiating error recovery procedures")
        
        # Analyze recent errors
        recent_errors = state["errors"][-3:] if len(state["errors"]) >= 3 else state["errors"]
        
        # Implement recovery strategies
        recovery_actions = []
        
        if any("timeout" in error.lower() for error in recent_errors):
            recovery_actions.append("increase_timeouts")
        
        if any("element not found" in error.lower() for error in recent_errors):
            recovery_actions.append("alternative_selectors")
        
        if any("network" in error.lower() for error in recent_errors):
            recovery_actions.append("retry_navigation")
        
        # Add recovery attempt message
        state["messages"].append(AIMessage(
            content=f"Attempting error recovery with strategies: {', '.join(recovery_actions)}"
        ))
        
        # For now, just continue - in a full implementation, you'd implement specific recovery logic
        state["context"]["recovery_attempted"] = True
        state["context"]["recovery_strategies"] = recovery_actions
        
        return state

def create_enhanced_web_automation_workflow() -> StateGraph:
    """
    Create an enhanced web automation workflow with advanced error handling
    """
    nodes = WebAutomationNodes()
    
    def should_continue_execution(state: WebAutomationState) -> str:
        """Determine next step in workflow"""
        if state["completed"]:
            return "validate"
        
        # Check if too many consecutive errors
        if len(state["errors"]) >= 3 and not state["context"].get("recovery_attempted", False):
            return "recover"
        
        if state["current_step"] >= len(state["workflow_plan"]):
            return "validate"
        
        return "execute"
    
    def should_attempt_recovery(state: WebAutomationState) -> str:
        """Determine if recovery is needed"""
        if state["context"].get("recovery_attempted", False):
            return "validate"  # Already tried recovery, proceed to validation
        return "execute"
    
    # Build the enhanced workflow
    workflow = StateGraph(WebAutomationState)
    
    # Add nodes
    workflow.add_node("analyze", nodes.task_analyzer_node)
    workflow.add_node("execute", nodes.step_executor_node)
    workflow.add_node("recover", nodes.error_recovery_node)
    workflow.add_node("validate", nodes.result_validator_node)
    
    # Define workflow edges
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "execute")
    
    workflow.add_conditional_edges(
        "execute",
        should_continue_execution,
        {
            "execute": "execute",
            "recover": "recover",
            "validate": "validate"
        }
    )
    
    workflow.add_conditional_edges(
        "recover",
        should_attempt_recovery,
        {
            "execute": "execute",
            "validate": "validate"
        }
    )
    
    workflow.add_edge("validate", END)
    
    return workflow.compile()

# Example usage
if __name__ == "__main__":
    workflow = create_enhanced_web_automation_workflow()
    print("Enhanced Web Automation Workflow created successfully!")
    print("Features: Task analysis, step execution, error recovery, result validation")