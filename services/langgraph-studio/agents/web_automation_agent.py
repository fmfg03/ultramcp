"""
Web Automation Agent for UltraMCP LangGraph Studio
Specialized agent for complex web automation workflows using Playwright-MCP
"""

import json
import logging
from typing import Dict, List, Any, Optional, TypedDict
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebAutomationState(TypedDict):
    """State for web automation workflows"""
    messages: List[Any]
    task: str
    url: str
    steps: List[Dict[str, Any]]
    current_step: int
    screenshots: List[str]
    extracted_data: Dict[str, Any]
    errors: List[str]
    session_id: str
    completed: bool
    final_result: Dict[str, Any]

class WebAutomationAgent:
    """
    Advanced Web Automation Agent with step-by-step execution
    """
    
    def __init__(self, mcp_base_url: str = "http://localhost:3000"):
        self.mcp_base_url = mcp_base_url
        self.session_id = None
        self.current_url = None
        
    def _call_playwright_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call Playwright-MCP tool via UltraMCP API"""
        try:
            response = requests.post(
                f"{self.mcp_base_url}/api/mcp/execute",
                json={
                    "toolId": f"playwright-mcp/{tool_name}",
                    "params": params
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error calling Playwright tool {tool_name}: {e}")
            raise

    @tool
    def navigate_to_url(self, url: str, wait_for: str = "load") -> str:
        """Navigate to a specific URL"""
        try:
            result = self._call_playwright_tool("navigate", {
                "url": url,
                "waitFor": wait_for
            })
            self.current_url = url
            return f"Successfully navigated to {url}"
        except Exception as e:
            return f"Failed to navigate to {url}: {str(e)}"

    @tool
    def take_screenshot(self, selector: Optional[str] = None, full_page: bool = True) -> str:
        """Take a screenshot of the current page or specific element"""
        try:
            params = {"fullPage": full_page, "quality": 90}
            if selector:
                params["selector"] = selector
                
            result = self._call_playwright_tool("screenshot", params)
            return f"Screenshot taken successfully: {result.get('path', 'unknown')}"
        except Exception as e:
            return f"Failed to take screenshot: {str(e)}"

    @tool
    def click_element(self, selector: str, description: str = "") -> str:
        """Click on an element by selector"""
        try:
            result = self._call_playwright_tool("click", {
                "selector": selector,
                "options": {"timeout": 30000}
            })
            return f"Successfully clicked element: {selector} ({description})"
        except Exception as e:
            return f"Failed to click element {selector}: {str(e)}"

    @tool
    def type_text(self, selector: str, text: str, clear: bool = True) -> str:
        """Type text into an input field"""
        try:
            result = self._call_playwright_tool("type", {
                "selector": selector,
                "text": text,
                "clear": clear
            })
            return f"Successfully typed text into {selector}"
        except Exception as e:
            return f"Failed to type text into {selector}: {str(e)}"

    @tool
    def extract_data(self, schema: Dict[str, Any], selector: Optional[str] = None) -> str:
        """Extract structured data from the page"""
        try:
            params = {"schema": schema}
            if selector:
                params["selector"] = selector
                
            result = self._call_playwright_tool("extract", params)
            return f"Data extracted successfully: {json.dumps(result, indent=2)}"
        except Exception as e:
            return f"Failed to extract data: {str(e)}"

    @tool
    def wait_for_element(self, selector: str, state: str = "visible", timeout: int = 30000) -> str:
        """Wait for an element to appear or change state"""
        try:
            result = self._call_playwright_tool("wait_for", {
                "selector": selector,
                "state": state,
                "timeout": timeout
            })
            return f"Element {selector} is now {state}"
        except Exception as e:
            return f"Failed to wait for element {selector}: {str(e)}"

    def get_tools(self) -> List[Any]:
        """Get all available tools for this agent"""
        return [
            self.navigate_to_url,
            self.take_screenshot, 
            self.click_element,
            self.type_text,
            self.extract_data,
            self.wait_for_element
        ]

def create_web_automation_workflow() -> StateGraph:
    """
    Create a comprehensive web automation workflow using LangGraph
    """
    
    # Initialize the agent
    agent = WebAutomationAgent()
    tools = agent.get_tools()
    tool_node = ToolNode(tools)
    
    def analyze_task(state: WebAutomationState) -> WebAutomationState:
        """Analyze the web automation task and create execution plan"""
        logger.info(f"Analyzing web automation task: {state['task']}")
        
        # Create a comprehensive execution plan
        analysis_prompt = f"""
        Analyze this web automation task and create a detailed step-by-step execution plan:
        
        Task: {state['task']}
        Target URL: {state.get('url', 'Not specified')}
        
        Create a plan with these considerations:
        1. Navigation and page loading
        2. Element interaction and form filling
        3. Data extraction requirements
        4. Error handling and validation
        5. Screenshots for verification
        
        Format as a JSON list of steps with: action, description, params, validation
        """
        
        # In a real implementation, you'd call an LLM here
        # For demo purposes, creating a basic plan structure
        basic_steps = [
            {
                "action": "navigate",
                "description": f"Navigate to {state.get('url', 'target URL')}",
                "params": {"url": state.get('url'), "wait_for": "networkidle"},
                "validation": "page_loaded"
            },
            {
                "action": "screenshot",
                "description": "Take initial screenshot for verification",
                "params": {"full_page": True},
                "validation": "screenshot_taken"
            }
        ]
        
        state["steps"] = basic_steps
        state["current_step"] = 0
        state["screenshots"] = []
        state["extracted_data"] = {}
        state["errors"] = []
        
        return state
    
    def execute_step(state: WebAutomationState) -> WebAutomationState:
        """Execute the current step in the automation plan"""
        if state["current_step"] >= len(state["steps"]):
            state["completed"] = True
            return state
            
        current_step = state["steps"][state["current_step"]]
        logger.info(f"Executing step {state['current_step']}: {current_step['description']}")
        
        try:
            action = current_step["action"]
            params = current_step["params"]
            
            # Execute the appropriate tool based on action
            result = None
            if action == "navigate":
                result = agent.navigate_to_url(params["url"], params.get("wait_for", "load"))
            elif action == "screenshot":
                result = agent.take_screenshot(
                    selector=params.get("selector"),
                    full_page=params.get("full_page", True)
                )
                state["screenshots"].append(result)
            elif action == "click":
                result = agent.click_element(params["selector"], params.get("description", ""))
            elif action == "type":
                result = agent.type_text(params["selector"], params["text"], params.get("clear", True))
            elif action == "extract":
                result = agent.extract_data(params["schema"], params.get("selector"))
                # Parse and store extracted data
                try:
                    extracted = json.loads(result.split(": ", 1)[1])
                    state["extracted_data"].update(extracted)
                except:
                    state["extracted_data"]["raw_result"] = result
            elif action == "wait":
                result = agent.wait_for_element(
                    params["selector"], 
                    params.get("state", "visible"),
                    params.get("timeout", 30000)
                )
            
            # Log the result
            logger.info(f"Step {state['current_step']} result: {result}")
            
            # Move to next step
            state["current_step"] += 1
            
        except Exception as e:
            error_msg = f"Error in step {state['current_step']}: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            state["current_step"] += 1  # Continue to next step despite error
            
        return state
    
    def validate_result(state: WebAutomationState) -> WebAutomationState:
        """Validate the final result and prepare summary"""
        logger.info("Validating web automation results")
        
        # Compile final result
        state["final_result"] = {
            "task": state["task"],
            "completed": state["current_step"] >= len(state["steps"]),
            "steps_executed": state["current_step"],
            "total_steps": len(state["steps"]),
            "screenshots_taken": len(state["screenshots"]),
            "data_extracted": state["extracted_data"],
            "errors": state["errors"],
            "session_id": state["session_id"],
            "timestamp": datetime.now().isoformat()
        }
        
        state["completed"] = True
        return state
    
    def should_continue(state: WebAutomationState) -> str:
        """Determine if workflow should continue"""
        if state["completed"] or state["current_step"] >= len(state["steps"]):
            return "validate"
        return "execute"
    
    # Build the workflow graph
    workflow = StateGraph(WebAutomationState)
    
    # Add nodes
    workflow.add_node("analyze", analyze_task)
    workflow.add_node("execute", execute_step)
    workflow.add_node("validate", validate_result)
    
    # Define edges
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "execute")
    workflow.add_conditional_edges(
        "execute",
        should_continue,
        {
            "execute": "execute",
            "validate": "validate"
        }
    )
    workflow.add_edge("validate", END)
    
    return workflow.compile()

# Web Automation Workflow Templates

WEB_AUTOMATION_TEMPLATES = {
    "ecommerce_product_search": {
        "name": "E-commerce Product Search",
        "description": "Search for products on e-commerce sites and extract details",
        "steps": [
            {"action": "navigate", "params": {"url": "{site_url}", "wait_for": "networkidle"}},
            {"action": "screenshot", "params": {"full_page": True}},
            {"action": "type", "params": {"selector": "{search_selector}", "text": "{search_term}"}},
            {"action": "click", "params": {"selector": "{search_button}"}},
            {"action": "wait", "params": {"selector": "{results_selector}", "state": "visible"}},
            {"action": "extract", "params": {
                "schema": {
                    "products": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "price": {"type": "string"},
                                "rating": {"type": "string"},
                                "url": {"type": "string"}
                            }
                        }
                    }
                }
            }}
        ]
    },
    
    "form_submission": {
        "name": "Automated Form Submission",
        "description": "Fill and submit web forms automatically",
        "steps": [
            {"action": "navigate", "params": {"url": "{form_url}", "wait_for": "load"}},
            {"action": "screenshot", "params": {"full_page": True}},
            {"action": "type", "params": {"selector": "{field_selectors[name]}", "text": "{form_data[name]}"}},
            {"action": "type", "params": {"selector": "{field_selectors[email]}", "text": "{form_data[email]}"}},
            {"action": "click", "params": {"selector": "{submit_button}"}},
            {"action": "wait", "params": {"selector": "{success_indicator}", "state": "visible"}},
            {"action": "screenshot", "params": {"full_page": True}}
        ]
    },
    
    "data_monitoring": {
        "name": "Website Data Monitoring",
        "description": "Monitor specific data on websites for changes",
        "steps": [
            {"action": "navigate", "params": {"url": "{target_url}", "wait_for": "networkidle"}},
            {"action": "extract", "params": {
                "schema": "{monitoring_schema}",
                "selector": "{data_container}"
            }},
            {"action": "screenshot", "params": {"selector": "{data_container}"}}
        ]
    },
    
    "social_media_automation": {
        "name": "Social Media Content Automation",
        "description": "Automate social media posting and interaction",
        "steps": [
            {"action": "navigate", "params": {"url": "{platform_url}", "wait_for": "networkidle"}},
            {"action": "click", "params": {"selector": "{compose_button}"}},
            {"action": "type", "params": {"selector": "{content_field}", "text": "{post_content}"}},
            {"action": "click", "params": {"selector": "{publish_button}"}},
            {"action": "wait", "params": {"selector": "{success_indicator}", "state": "visible"}},
            {"action": "screenshot", "params": {"full_page": True}}
        ]
    }
}

def create_workflow_from_template(template_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a workflow configuration from a template
    """
    if template_name not in WEB_AUTOMATION_TEMPLATES:
        raise ValueError(f"Unknown template: {template_name}")
    
    template = WEB_AUTOMATION_TEMPLATES[template_name].copy()
    
    # Replace template variables with actual values
    def replace_variables(obj, params):
        if isinstance(obj, dict):
            return {k: replace_variables(v, params) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_variables(item, params) for item in obj]
        elif isinstance(obj, str):
            try:
                return obj.format(**params)
            except KeyError:
                return obj  # Return as-is if template variable not found
        return obj
    
    template["steps"] = replace_variables(template["steps"], params)
    return template

# Example usage and testing
if __name__ == "__main__":
    # Test workflow creation
    workflow = create_web_automation_workflow()
    
    # Example state for testing
    test_state = WebAutomationState(
        messages=[],
        task="Navigate to Google and take a screenshot",
        url="https://www.google.com",
        steps=[],
        current_step=0,
        screenshots=[],
        extracted_data={},
        errors=[],
        session_id="test-session-001",
        completed=False,
        final_result={}
    )
    
    print("Web Automation Agent initialized successfully!")
    print(f"Available templates: {list(WEB_AUTOMATION_TEMPLATES.keys())}")