"""
Actions service routes for unified backend
Proxies requests to actions-mcp service
"""

from fastapi import APIRouter, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List
import httpx
import logging

router = APIRouter()
security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)

ACTIONS_SERVICE_URL = "http://localhost:8010"


async def proxy_to_actions_service(endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
    """Proxy request to actions-mcp service"""
    url = f"{ACTIONS_SERVICE_URL}{endpoint}"
    
    try:
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, **kwargs)
            elif method == "POST":
                response = await client.post(url, **kwargs)
            elif method == "PUT":
                response = await client.put(url, **kwargs)
            elif method == "DELETE":
                response = await client.delete(url, **kwargs)
            else:
                raise HTTPException(status_code=405, detail=f"Method {method} not allowed")
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Actions service error: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to actions service: {e}")
        raise HTTPException(
            status_code=503,
            detail="Actions service unavailable"
        )


@router.get("/list")
async def list_actions(credentials: HTTPAuthorizationCredentials = Security(security)):
    """List all available external actions"""
    return await proxy_to_actions_service("/actions/")


@router.get("/{action_id}")
async def get_action(
    action_id: str,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Get details of a specific action"""
    return await proxy_to_actions_service(f"/actions/{action_id}")


@router.post("/execute")
async def execute_action(
    action_id: str,
    parameters: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Execute an external action"""
    return await proxy_to_actions_service(
        f"/actions/{action_id}/execute",
        method="POST",
        json={"parameters": parameters}
    )


@router.post("/escalate")
async def escalate_to_human(
    priority: str = "medium",
    message: str = "",
    context: Dict[str, Any] = None,
    approvers: List[str] = None,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Escalate issue to human for approval or intervention"""
    parameters = {
        "priority": priority,
        "message": message,
        "context": context or {},
        "approvers": approvers or []
    }
    
    return await proxy_to_actions_service(
        "/actions/escalate_to_human/execute",
        method="POST",
        json={"parameters": parameters}
    )


@router.post("/notify")
async def send_notification(
    channel: str = "email",
    recipient: str = "",
    subject: str = "",
    message: str = "",
    priority: str = "normal",
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Send notification via email or Slack"""
    parameters = {
        "channel": channel,
        "recipient": recipient,
        "subject": subject,
        "message": message,
        "priority": priority
    }
    
    action_id = "send_email" if channel == "email" else "send_slack_message"
    return await proxy_to_actions_service(
        f"/actions/{action_id}/execute",
        method="POST",
        json={"parameters": parameters}
    )


@router.post("/workflow")
async def trigger_workflow(
    workflow_type: str = "jenkins",
    job_name: str = "",
    parameters: Dict[str, Any] = None,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Trigger external workflow"""
    workflow_params = {
        "workflow_type": workflow_type,
        "job_name": job_name,
        "parameters": parameters or {}
    }
    
    return await proxy_to_actions_service(
        "/actions/trigger_workflow/execute",
        method="POST",
        json={"parameters": workflow_params}
    )


@router.post("/ticket")
async def create_ticket(
    system: str = "jira",
    title: str = "",
    description: str = "",
    priority: str = "medium",
    assignee: str = "",
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Create ticket in external system"""
    parameters = {
        "system": system,
        "title": title,
        "description": description,
        "priority": priority,
        "assignee": assignee
    }
    
    action_id = "create_jira_ticket" if system == "jira" else "create_github_issue"
    return await proxy_to_actions_service(
        f"/actions/{action_id}/execute",
        method="POST",
        json={"parameters": parameters}
    )


@router.post("/security")
async def run_security_scan(
    scan_type: str = "vulnerability",
    target: str = "",
    tool: str = "sonarqube",
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Run security scan using external tools"""
    parameters = {
        "scan_type": scan_type,
        "target": target,
        "tool": tool
    }
    
    return await proxy_to_actions_service(
        "/actions/run_security_scan/execute",
        method="POST",
        json={"parameters": parameters}
    )


@router.post("/validate")
async def validate_action_parameters(
    action_id: str,
    parameters: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Validate parameters for an action without executing it"""
    return await proxy_to_actions_service(
        f"/actions/{action_id}/validate",
        method="POST",
        json={"parameters": parameters}
    )


@router.get("/{action_id}/history")
async def get_action_history(
    action_id: str,
    limit: int = 10,
    offset: int = 0,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Get execution history for an action"""
    return await proxy_to_actions_service(
        f"/actions/{action_id}/history",
        params={"limit": limit, "offset": offset}
    )


@router.post("/batch")
async def execute_batch_actions(
    actions: List[Dict[str, Any]],
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Execute multiple actions in batch"""
    return await proxy_to_actions_service(
        "/actions/batch",
        method="POST",
        json={"actions": actions}
    )


@router.get("/stats/summary")
async def get_action_stats(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Get execution statistics"""
    return await proxy_to_actions_service("/actions/stats/summary")


@router.get("/health")
async def actions_health():
    """Check actions service health"""
    return await proxy_to_actions_service("/health/")