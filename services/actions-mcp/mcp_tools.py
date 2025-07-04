"""
MCP tools for actions-mcp service integration
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
import logging

logger = logging.getLogger(__name__)


class ActionsMCPTools:
    """MCP tools for external action execution"""
    
    def __init__(self, base_url: str = "http://localhost:8010"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to actions service"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.base_url}{endpoint}"
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    async def list_actions(self) -> Dict[str, Any]:
        """List all available external actions"""
        try:
            result = await self._make_request("GET", "/actions/")
            return {
                "success": True,
                "actions": result.get("actions", []),
                "total": result.get("total", 0)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_action(self, action_id: str, parameters: Dict[str, Any], user_id: str = "system") -> Dict[str, Any]:
        """Execute an external action"""
        try:
            payload = {
                "parameters": parameters
            }
            headers = {
                "Content-Type": "application/json"
            }
            
            result = await self._make_request(
                "POST", 
                f"/actions/{action_id}/execute",
                json=payload,
                headers=headers
            )
            
            return {
                "success": result.get("success", False),
                "execution_id": result.get("execution_id"),
                "result": result.get("result"),
                "error": result.get("error"),
                "timestamp": result.get("timestamp")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def escalate_to_human(self, 
                               priority: str = "medium",
                               message: str = "",
                               context: Dict[str, Any] = None,
                               approvers: List[str] = None) -> Dict[str, Any]:
        """Escalate issue to human for approval or intervention"""
        parameters = {
            "priority": priority,
            "message": message,
            "context": context or {},
            "approvers": approvers or []
        }
        
        return await self.execute_action("escalate_to_human", parameters)
    
    async def send_notification(self, 
                               channel: str = "email",
                               recipient: str = "",
                               subject: str = "",
                               message: str = "",
                               priority: str = "normal") -> Dict[str, Any]:
        """Send notification via email or Slack"""
        parameters = {
            "channel": channel,
            "recipient": recipient,
            "subject": subject,
            "message": message,
            "priority": priority
        }
        
        action_id = "send_email" if channel == "email" else "send_slack_message"
        return await self.execute_action(action_id, parameters)
    
    async def trigger_workflow(self, 
                              workflow_type: str = "jenkins",
                              job_name: str = "",
                              parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Trigger external workflow (Jenkins, GitHub Actions, etc.)"""
        workflow_params = {
            "workflow_type": workflow_type,
            "job_name": job_name,
            "parameters": parameters or {}
        }
        
        return await self.execute_action("trigger_workflow", workflow_params)
    
    async def create_ticket(self, 
                           system: str = "jira",
                           title: str = "",
                           description: str = "",
                           priority: str = "medium",
                           assignee: str = "") -> Dict[str, Any]:
        """Create ticket in external system (Jira, GitHub Issues)"""
        parameters = {
            "system": system,
            "title": title,
            "description": description,
            "priority": priority,
            "assignee": assignee
        }
        
        action_id = "create_jira_ticket" if system == "jira" else "create_github_issue"
        return await self.execute_action(action_id, parameters)
    
    async def update_documentation(self, 
                                  platform: str = "confluence",
                                  page_id: str = "",
                                  content: str = "",
                                  title: str = "") -> Dict[str, Any]:
        """Update documentation in external platform"""
        parameters = {
            "platform": platform,
            "page_id": page_id,
            "content": content,
            "title": title
        }
        
        return await self.execute_action("update_documentation", parameters)
    
    async def run_security_scan(self, 
                               scan_type: str = "vulnerability",
                               target: str = "",
                               tool: str = "sonarqube") -> Dict[str, Any]:
        """Run security scan using external tools"""
        parameters = {
            "scan_type": scan_type,
            "target": target,
            "tool": tool
        }
        
        return await self.execute_action("run_security_scan", parameters)
    
    async def send_alert(self, 
                        system: str = "datadog",
                        alert_type: str = "warning",
                        message: str = "",
                        tags: List[str] = None) -> Dict[str, Any]:
        """Send monitoring alert"""
        parameters = {
            "system": system,
            "alert_type": alert_type,
            "message": message,
            "tags": tags or []
        }
        
        return await self.execute_action("send_monitoring_alert", parameters)
    
    async def validate_action_parameters(self, action_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters for an action without executing it"""
        try:
            payload = {
                "parameters": parameters
            }
            headers = {
                "Content-Type": "application/json"
            }
            
            result = await self._make_request(
                "POST", 
                f"/actions/{action_id}/validate",
                json=payload,
                headers=headers
            )
            
            return {
                "valid": result.get("valid", False),
                "errors": result.get("errors", []),
                "warnings": result.get("warnings", [])
            }
        except Exception as e:
            return {
                "valid": False,
                "errors": [str(e)]
            }
    
    async def get_action_history(self, action_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get execution history for an action"""
        try:
            result = await self._make_request(
                "GET", 
                f"/actions/{action_id}/history?limit={limit}"
            )
            
            return {
                "success": True,
                "history": result.get("history", []),
                "total": result.get("total", 0)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_action_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        try:
            result = await self._make_request("GET", "/actions/stats/summary")
            return {
                "success": True,
                "stats": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# MCP tool definitions for registration
MCP_TOOLS = {
    "actions_list": {
        "name": "actions_list",
        "description": "List all available external actions",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "actions_execute": {
        "name": "actions_execute",
        "description": "Execute an external action with parameters",
        "parameters": {
            "type": "object",
            "properties": {
                "action_id": {
                    "type": "string",
                    "description": "ID of the action to execute"
                },
                "parameters": {
                    "type": "object",
                    "description": "Parameters for the action"
                },
                "user_id": {
                    "type": "string",
                    "description": "User ID for authorization",
                    "default": "system"
                }
            },
            "required": ["action_id", "parameters"]
        }
    },
    "actions_escalate_human": {
        "name": "actions_escalate_human",
        "description": "Escalate issue to human for approval or intervention",
        "parameters": {
            "type": "object",
            "properties": {
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "default": "medium"
                },
                "message": {
                    "type": "string",
                    "description": "Escalation message"
                },
                "context": {
                    "type": "object",
                    "description": "Additional context"
                },
                "approvers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of approver IDs"
                }
            },
            "required": ["message"]
        }
    },
    "actions_send_notification": {
        "name": "actions_send_notification",
        "description": "Send notification via email or Slack",
        "parameters": {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "enum": ["email", "slack"],
                    "default": "email"
                },
                "recipient": {
                    "type": "string",
                    "description": "Email address or Slack user/channel"
                },
                "subject": {
                    "type": "string",
                    "description": "Message subject"
                },
                "message": {
                    "type": "string",
                    "description": "Message content"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "normal", "high"],
                    "default": "normal"
                }
            },
            "required": ["recipient", "message"]
        }
    },
    "actions_trigger_workflow": {
        "name": "actions_trigger_workflow",
        "description": "Trigger external workflow (Jenkins, GitHub Actions, etc.)",
        "parameters": {
            "type": "object",
            "properties": {
                "workflow_type": {
                    "type": "string",
                    "enum": ["jenkins", "github_actions", "gitlab_ci"],
                    "default": "jenkins"
                },
                "job_name": {
                    "type": "string",
                    "description": "Job or workflow name"
                },
                "parameters": {
                    "type": "object",
                    "description": "Workflow parameters"
                }
            },
            "required": ["job_name"]
        }
    },
    "actions_create_ticket": {
        "name": "actions_create_ticket",
        "description": "Create ticket in external system (Jira, GitHub Issues)",
        "parameters": {
            "type": "object",
            "properties": {
                "system": {
                    "type": "string",
                    "enum": ["jira", "github"],
                    "default": "jira"
                },
                "title": {
                    "type": "string",
                    "description": "Ticket title"
                },
                "description": {
                    "type": "string",
                    "description": "Ticket description"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "default": "medium"
                },
                "assignee": {
                    "type": "string",
                    "description": "Assignee username"
                }
            },
            "required": ["title", "description"]
        }
    },
    "actions_security_scan": {
        "name": "actions_security_scan",
        "description": "Run security scan using external tools",
        "parameters": {
            "type": "object",
            "properties": {
                "scan_type": {
                    "type": "string",
                    "enum": ["vulnerability", "code_analysis", "dependency"],
                    "default": "vulnerability"
                },
                "target": {
                    "type": "string",
                    "description": "Scan target (path, URL, etc.)"
                },
                "tool": {
                    "type": "string",
                    "enum": ["sonarqube", "snyk", "veracode"],
                    "default": "sonarqube"
                }
            },
            "required": ["target"]
        }
    },
    "actions_validate_parameters": {
        "name": "actions_validate_parameters",
        "description": "Validate parameters for an action without executing it",
        "parameters": {
            "type": "object",
            "properties": {
                "action_id": {
                    "type": "string",
                    "description": "ID of the action to validate"
                },
                "parameters": {
                    "type": "object",
                    "description": "Parameters to validate"
                }
            },
            "required": ["action_id", "parameters"]
        }
    },
    "actions_get_stats": {
        "name": "actions_get_stats",
        "description": "Get execution statistics for actions",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}


# Tool execution functions
async def execute_actions_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute actions MCP tool"""
    async with ActionsMCPTools() as actions:
        if tool_name == "actions_list":
            return await actions.list_actions()
        
        elif tool_name == "actions_execute":
            return await actions.execute_action(
                arguments["action_id"],
                arguments["parameters"],
                arguments.get("user_id", "system")
            )
        
        elif tool_name == "actions_escalate_human":
            return await actions.escalate_to_human(
                priority=arguments.get("priority", "medium"),
                message=arguments["message"],
                context=arguments.get("context", {}),
                approvers=arguments.get("approvers", [])
            )
        
        elif tool_name == "actions_send_notification":
            return await actions.send_notification(
                channel=arguments.get("channel", "email"),
                recipient=arguments["recipient"],
                subject=arguments.get("subject", ""),
                message=arguments["message"],
                priority=arguments.get("priority", "normal")
            )
        
        elif tool_name == "actions_trigger_workflow":
            return await actions.trigger_workflow(
                workflow_type=arguments.get("workflow_type", "jenkins"),
                job_name=arguments["job_name"],
                parameters=arguments.get("parameters", {})
            )
        
        elif tool_name == "actions_create_ticket":
            return await actions.create_ticket(
                system=arguments.get("system", "jira"),
                title=arguments["title"],
                description=arguments["description"],
                priority=arguments.get("priority", "medium"),
                assignee=arguments.get("assignee", "")
            )
        
        elif tool_name == "actions_security_scan":
            return await actions.run_security_scan(
                scan_type=arguments.get("scan_type", "vulnerability"),
                target=arguments["target"],
                tool=arguments.get("tool", "sonarqube")
            )
        
        elif tool_name == "actions_validate_parameters":
            return await actions.validate_action_parameters(
                arguments["action_id"],
                arguments["parameters"]
            )
        
        elif tool_name == "actions_get_stats":
            return await actions.get_action_stats()
        
        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }