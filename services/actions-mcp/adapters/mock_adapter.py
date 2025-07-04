"""
Mock Adapter - Simulates external system integrations for development and testing
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class MockAdapter:
    """Mock adapter that simulates external system interactions"""
    
    def __init__(self, adapter_name: str):
        self.adapter_name = adapter_name
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize mock adapter"""
        await asyncio.sleep(0.1)  # Simulate initialization time
        self.is_initialized = True
        logger.info(f"✅ Mock adapter {self.adapter_name} initialized")
    
    async def execute(self, action_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute mock action"""
        
        if not self.is_initialized:
            raise Exception(f"Mock adapter {self.adapter_name} not initialized")
        
        # Simulate processing time
        await asyncio.sleep(0.2)
        
        # Generate mock responses based on action type
        if action_name == "escalate_to_human":
            return await self._mock_escalate_to_human(input_data)
        elif action_name == "request_approval":
            return await self._mock_request_approval(input_data)
        elif action_name == "send_email":
            return await self._mock_send_email(input_data)
        elif action_name == "send_slack_message":
            return await self._mock_send_slack_message(input_data)
        elif action_name == "trigger_workflow":
            return await self._mock_trigger_workflow(input_data)
        elif action_name == "stop_workflow":
            return await self._mock_stop_workflow(input_data)
        elif action_name == "create_jira_ticket":
            return await self._mock_create_jira_ticket(input_data)
        elif action_name == "create_github_issue":
            return await self._mock_create_github_issue(input_data)
        elif action_name == "update_documentation":
            return await self._mock_update_documentation(input_data)
        elif action_name == "create_alert":
            return await self._mock_create_alert(input_data)
        elif action_name == "trigger_security_scan":
            return await self._mock_trigger_security_scan(input_data)
        else:
            return await self._mock_generic_action(action_name, input_data)
    
    async def _mock_escalate_to_human(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock human escalation"""
        escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
        
        stakeholders = input_data.get("stakeholders", [])
        urgency = input_data.get("urgency", "medium")
        channels = input_data.get("notification_channels", ["email"])
        
        # Simulate notification sending
        notified_stakeholders = []
        for stakeholder in stakeholders:
            for channel in channels:
                notified_stakeholders.append(f"{stakeholder}@{channel}")
                await asyncio.sleep(0.05)  # Simulate notification delay
        
        # Calculate estimated response time based on urgency
        response_times = {
            "low": "4-8 hours",
            "medium": "2-4 hours", 
            "high": "30-60 minutes",
            "critical": "5-15 minutes"
        }
        
        return {
            "escalation_id": escalation_id,
            "status": "escalated",
            "notified_stakeholders": notified_stakeholders,
            "estimated_response_time": response_times.get(urgency, "2-4 hours"),
            "tracking_url": f"https://escalation.company.com/track/{escalation_id}",
            "created_at": datetime.utcnow().isoformat(),
            "urgency": urgency,
            "context": input_data.get("context", "")
        }
    
    async def _mock_request_approval(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock approval request"""
        approval_id = f"APR-{uuid.uuid4().hex[:8].upper()}"
        
        approvers = input_data.get("approvers", [])
        approval_type = input_data.get("approval_type", "single")
        
        # Simulate approval notification
        approvers_notified = []
        for approver in approvers:
            approvers_notified.append(f"{approver}@approval-system")
            await asyncio.sleep(0.03)
        
        return {
            "approval_id": approval_id,
            "status": "pending_approval",
            "approvers_notified": approvers_notified,
            "approval_url": f"https://approval.company.com/request/{approval_id}",
            "approval_type": approval_type,
            "action_description": input_data.get("action_description", ""),
            "deadline": input_data.get("deadline"),
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def _mock_send_email(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock email sending"""
        message_id = f"MSG-{uuid.uuid4().hex[:12]}"
        
        recipients = input_data.get("recipients", [])
        subject = input_data.get("subject", "No Subject")
        
        # Simulate email delivery
        delivery_status = {}
        for recipient in recipients:
            await asyncio.sleep(0.02)  # Simulate delivery time
            delivery_status[recipient] = "delivered"
        
        return {
            "message_id": message_id,
            "status": "sent",
            "delivery_status": delivery_status,
            "subject": subject,
            "recipient_count": len(recipients),
            "sent_at": datetime.utcnow().isoformat()
        }
    
    async def _mock_send_slack_message(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock Slack message sending"""
        message_ts = str(int(datetime.utcnow().timestamp() * 1000000))
        
        channel = input_data.get("channel", "#general")
        message = input_data.get("message", "")
        
        return {
            "message_ts": message_ts,
            "channel": channel,
            "status": "sent",
            "message": message[:100] + "..." if len(message) > 100 else message,
            "sent_at": datetime.utcnow().isoformat()
        }
    
    async def _mock_trigger_workflow(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock workflow triggering"""
        workflow_id = f"WF-{uuid.uuid4().hex[:10].upper()}"
        
        workflow_type = input_data.get("workflow_type", "custom")
        environment = input_data.get("environment", "development")
        
        # Simulate workflow startup time
        await asyncio.sleep(0.1)
        
        # Estimate duration based on workflow type
        duration_estimates = {
            "deployment": 15,
            "testing": 30,
            "security_scan": 45,
            "backup": 20,
            "custom": 10
        }
        
        return {
            "workflow_id": workflow_id,
            "status": "running",
            "estimated_duration": duration_estimates.get(workflow_type, 10),
            "monitoring_url": f"https://workflows.company.com/monitor/{workflow_id}",
            "workflow_type": workflow_type,
            "environment": environment,
            "started_at": datetime.utcnow().isoformat()
        }
    
    async def _mock_stop_workflow(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock workflow stopping"""
        workflow_id = input_data.get("workflow_id", "WF-UNKNOWN")
        reason = input_data.get("reason", "User request")
        force = input_data.get("force", False)
        
        # Simulate stop time
        await asyncio.sleep(0.05 if force else 0.2)
        
        return {
            "workflow_id": workflow_id,
            "status": "stopped",
            "stop_time": datetime.utcnow().isoformat(),
            "reason": reason,
            "force_stopped": force
        }
    
    async def _mock_create_jira_ticket(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock Jira ticket creation"""
        ticket_number = f"PROJ-{1000 + hash(str(input_data)) % 9000}"
        
        project = input_data.get("project", "PROJ")
        issue_type = input_data.get("issue_type", "Task")
        summary = input_data.get("summary", "New Issue")
        
        return {
            "ticket_id": ticket_number,
            "ticket_url": f"https://company.atlassian.net/browse/{ticket_number}",
            "status": "created",
            "project": project,
            "issue_type": issue_type,
            "summary": summary,
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def _mock_create_github_issue(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock GitHub issue creation"""
        issue_number = 1000 + hash(str(input_data)) % 9000
        repository = input_data.get("repository", "owner/repo")
        title = input_data.get("title", "New Issue")
        
        return {
            "issue_id": issue_number,
            "issue_url": f"https://github.com/{repository}/issues/{issue_number}",
            "issue_number": issue_number,
            "repository": repository,
            "title": title,
            "status": "open",
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def _mock_update_documentation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock documentation update"""
        page_id = f"PAGE-{uuid.uuid4().hex[:8].upper()}"
        
        service = input_data.get("service", "confluence")
        title = input_data.get("title", "Updated Page")
        
        return {
            "page_id": page_id,
            "page_url": f"https://{service}.company.com/pages/{page_id}",
            "version": "v2.0",
            "status": "updated",
            "service": service,
            "title": title,
            "updated_at": datetime.utcnow().isoformat()
        }
    
    async def _mock_create_alert(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock alert creation"""
        alert_id = f"ALERT-{uuid.uuid4().hex[:8].upper()}"
        
        service = input_data.get("service", "datadog")
        alert_name = input_data.get("alert_name", "New Alert")
        severity = input_data.get("severity", "warning")
        
        return {
            "alert_id": alert_id,
            "alert_url": f"https://{service}.company.com/alerts/{alert_id}",
            "status": "active",
            "alert_name": alert_name,
            "severity": severity,
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def _mock_trigger_security_scan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock security scan triggering"""
        scan_id = f"SCAN-{uuid.uuid4().hex[:8].upper()}"
        
        scan_type = input_data.get("scan_type", "vulnerability")
        target = input_data.get("target", "unknown")
        scope = input_data.get("scope", "full")
        
        # Estimate completion time based on scan type and scope
        base_times = {
            "vulnerability": 30,
            "compliance": 45,
            "penetration": 120,
            "code_analysis": 60
        }
        
        scope_multipliers = {
            "full": 1.0,
            "incremental": 0.3,
            "critical_only": 0.5
        }
        
        estimated_minutes = int(base_times.get(scan_type, 30) * scope_multipliers.get(scope, 1.0))
        estimated_completion = datetime.fromtimestamp(
            datetime.utcnow().timestamp() + (estimated_minutes * 60)
        ).isoformat()
        
        return {
            "scan_id": scan_id,
            "status": "initiated",
            "estimated_completion": estimated_completion,
            "results_url": f"https://security.company.com/scans/{scan_id}",
            "scan_type": scan_type,
            "target": target,
            "scope": scope,
            "started_at": datetime.utcnow().isoformat()
        }
    
    async def _mock_generic_action(self, action_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock generic action execution"""
        execution_id = f"EXEC-{uuid.uuid4().hex[:8].upper()}"
        
        return {
            "execution_id": execution_id,
            "action_name": action_name,
            "status": "completed",
            "result": "mock_success",
            "input_summary": f"{len(input_data)} parameters provided",
            "executed_at": datetime.utcnow().isoformat()
        }
    
    async def cleanup(self):
        """Cleanup mock adapter"""
        self.is_initialized = False
        logger.info(f"✅ Mock adapter {self.adapter_name} cleaned up")