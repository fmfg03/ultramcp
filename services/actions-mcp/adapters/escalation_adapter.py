"""
Escalation Adapter - Handles human escalation and approval workflows
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import uuid
import json

from .mock_adapter import MockAdapter

logger = logging.getLogger(__name__)

class EscalationAdapter:
    """Adapter for human escalation and approval workflows"""
    
    def __init__(self):
        self.is_initialized = False
        self.escalations: Dict[str, Dict[str, Any]] = {}
        self.approvals: Dict[str, Dict[str, Any]] = {}
        self.notification_templates = {}
        
    async def initialize(self):
        """Initialize escalation adapter"""
        try:
            await self._load_notification_templates()
            await self._setup_notification_channels()
            self.is_initialized = True
            logger.info("✅ Escalation adapter initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize escalation adapter: {e}")
            # Fall back to mock adapter
            self.mock_adapter = MockAdapter("EscalationAdapter")
            await self.mock_adapter.initialize()
            logger.info("✅ Using mock escalation adapter")
    
    async def _load_notification_templates(self):
        """Load notification templates"""
        self.notification_templates = {
            "escalation_critical": {
                "subject": "🚨 CRITICAL: Immediate attention required - {context}",
                "body": """
                CRITICAL ESCALATION REQUIRED

                Context: {context}
                Urgency: {urgency}
                Escalated by: {escalated_by}
                Time: {timestamp}

                Action required: Please review and respond immediately.
                Tracking: {tracking_url}

                This is an automated escalation from UltraMCP Actions Service.
                """
            },
            "escalation_high": {
                "subject": "⚠️  HIGH PRIORITY: Action required - {context}",
                "body": """
                HIGH PRIORITY ESCALATION

                Context: {context}
                Urgency: {urgency}
                Escalated by: {escalated_by}
                Time: {timestamp}

                Please review and respond within the estimated timeframe.
                Tracking: {tracking_url}
                """
            },
            "approval_request": {
                "subject": "📋 Approval Required: {action_description}",
                "body": """
                APPROVAL REQUEST

                Action: {action_description}
                Requested by: {requester}
                Justification: {justification}
                Impact: {impact_assessment}
                Deadline: {deadline}

                Please review and approve/reject:
                {approval_url}

                This request expires at: {expires_at}
                """
            }
        }
        
    async def _setup_notification_channels(self):
        """Setup notification channels"""
        # In production, this would configure actual notification systems
        self.notification_channels = {
            "email": {"enabled": True, "config": {}},
            "slack": {"enabled": True, "config": {}},
            "teams": {"enabled": False, "config": {}},
            "sms": {"enabled": False, "config": {}}
        }
        
    async def execute(self, action_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute escalation action"""
        
        if not self.is_initialized and hasattr(self, 'mock_adapter'):
            return await self.mock_adapter.execute(action_name, input_data)
        
        if action_name == "escalate_to_human":
            return await self._escalate_to_human(input_data)
        elif action_name == "request_approval":
            return await self._request_approval(input_data)
        else:
            raise ValueError(f"Unsupported action: {action_name}")
    
    async def _escalate_to_human(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Escalate issue to human stakeholders"""
        
        escalation_id = f"ESC-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        # Extract escalation parameters
        context = input_data.get("context", "")
        urgency = input_data.get("urgency", "medium")
        stakeholders = input_data.get("stakeholders", [])
        deadline = input_data.get("deadline")
        attachments = input_data.get("attachments", [])
        notification_channels = input_data.get("notification_channels", ["email"])
        
        # Validate stakeholders
        if not stakeholders:
            raise ValueError("At least one stakeholder must be specified for escalation")
        
        # Create escalation record
        escalation = {
            "escalation_id": escalation_id,
            "context": context,
            "urgency": urgency,
            "stakeholders": stakeholders,
            "deadline": deadline,
            "attachments": attachments,
            "notification_channels": notification_channels,
            "status": "escalated",
            "created_at": datetime.utcnow(),
            "responses": [],
            "escalated_by": input_data.get("escalated_by", "system")
        }
        
        self.escalations[escalation_id] = escalation
        
        # Calculate estimated response time based on urgency
        response_times = {
            "low": timedelta(hours=8),
            "medium": timedelta(hours=4),
            "high": timedelta(hours=1),
            "critical": timedelta(minutes=15)
        }
        
        estimated_response = datetime.utcnow() + response_times.get(urgency, timedelta(hours=4))
        
        # Send notifications to stakeholders
        notified_stakeholders = await self._send_escalation_notifications(escalation)
        
        # Generate tracking URL
        tracking_url = f"https://escalation.ultramcp.com/track/{escalation_id}"
        
        return {
            "escalation_id": escalation_id,
            "status": "escalated",
            "notified_stakeholders": notified_stakeholders,
            "estimated_response_time": estimated_response.isoformat(),
            "tracking_url": tracking_url,
            "urgency": urgency,
            "stakeholder_count": len(stakeholders),
            "notification_channels_used": notification_channels,
            "created_at": escalation["created_at"].isoformat()
        }
    
    async def _send_escalation_notifications(self, escalation: Dict[str, Any]) -> List[str]:
        """Send notifications to stakeholders"""
        
        notified_stakeholders = []
        
        # Select template based on urgency
        if escalation["urgency"] == "critical":
            template_key = "escalation_critical"
        elif escalation["urgency"] == "high":
            template_key = "escalation_high"
        else:
            template_key = "escalation_high"  # Default template
        
        template = self.notification_templates.get(template_key)
        
        # Prepare notification data
        notification_data = {
            "context": escalation["context"],
            "urgency": escalation["urgency"],
            "escalated_by": escalation["escalated_by"],
            "timestamp": escalation["created_at"].isoformat(),
            "tracking_url": f"https://escalation.ultramcp.com/track/{escalation['escalation_id']}"
        }
        
        # Send notifications via each channel
        for channel in escalation["notification_channels"]:
            if channel in self.notification_channels and self.notification_channels[channel]["enabled"]:
                for stakeholder in escalation["stakeholders"]:
                    try:
                        await self._send_notification(channel, stakeholder, template, notification_data)
                        notified_stakeholders.append(f"{stakeholder}@{channel}")
                        await asyncio.sleep(0.1)  # Rate limiting
                    except Exception as e:
                        logger.error(f"❌ Failed to notify {stakeholder} via {channel}: {e}")
        
        return notified_stakeholders
    
    async def _request_approval(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Request approval for an action"""
        
        approval_id = f"APR-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        # Extract approval parameters
        action_description = input_data.get("action_description", "")
        approvers = input_data.get("approvers", [])
        justification = input_data.get("justification", "")
        impact_assessment = input_data.get("impact_assessment", "")
        deadline = input_data.get("deadline")
        approval_type = input_data.get("approval_type", "single")  # single, majority, unanimous
        
        # Validate approvers
        if not approvers:
            raise ValueError("At least one approver must be specified")
        
        if not action_description:
            raise ValueError("Action description is required for approval requests")
        
        # Calculate expiration time
        if deadline:
            expires_at = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
        else:
            expires_at = datetime.utcnow() + timedelta(hours=24)  # Default 24 hour expiration
        
        # Create approval record
        approval = {
            "approval_id": approval_id,
            "action_description": action_description,
            "approvers": approvers,
            "justification": justification,
            "impact_assessment": impact_assessment,
            "deadline": deadline,
            "approval_type": approval_type,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "approvals_received": [],
            "rejections_received": [],
            "requester": input_data.get("requester", "system")
        }
        
        self.approvals[approval_id] = approval
        
        # Send approval notifications
        approvers_notified = await self._send_approval_notifications(approval)
        
        # Generate approval URL
        approval_url = f"https://approval.ultramcp.com/request/{approval_id}"
        
        return {
            "approval_id": approval_id,
            "status": "pending_approval",
            "approvers_notified": approvers_notified,
            "approval_url": approval_url,
            "approval_type": approval_type,
            "expires_at": expires_at.isoformat(),
            "approvers_required": self._calculate_approvers_required(approval_type, len(approvers)),
            "created_at": approval["created_at"].isoformat()
        }
    
    async def _send_approval_notifications(self, approval: Dict[str, Any]) -> List[str]:
        """Send approval request notifications"""
        
        approvers_notified = []
        template = self.notification_templates["approval_request"]
        
        # Prepare notification data
        notification_data = {
            "action_description": approval["action_description"],
            "requester": approval["requester"],
            "justification": approval["justification"],
            "impact_assessment": approval["impact_assessment"],
            "deadline": approval["deadline"] or "None specified",
            "approval_url": f"https://approval.ultramcp.com/request/{approval['approval_id']}",
            "expires_at": approval["expires_at"].isoformat()
        }
        
        # Send notifications to approvers (default to email)
        for approver in approval["approvers"]:
            try:
                await self._send_notification("email", approver, template, notification_data)
                approvers_notified.append(f"{approver}@email")
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                logger.error(f"❌ Failed to notify approver {approver}: {e}")
        
        return approvers_notified
    
    async def _send_notification(self, channel: str, recipient: str, template: Dict[str, str], data: Dict[str, Any]):
        """Send notification via specified channel"""
        
        try:
            subject = template["subject"].format(**data)
            body = template["body"].format(**data)
            
            if channel == "email":
                await self._send_email_notification(recipient, subject, body)
            elif channel == "slack":
                await self._send_slack_notification(recipient, subject, body)
            elif channel == "teams":
                await self._send_teams_notification(recipient, subject, body)
            elif channel == "sms":
                await self._send_sms_notification(recipient, subject)
            else:
                logger.warning(f"⚠️ Unsupported notification channel: {channel}")
                
        except Exception as e:
            logger.error(f"❌ Failed to send {channel} notification to {recipient}: {e}")
            raise
    
    async def _send_email_notification(self, recipient: str, subject: str, body: str):
        """Send email notification"""
        # In production, integrate with actual email service (SendGrid, SES, etc.)
        logger.info(f"📧 EMAIL to {recipient}: {subject}")
        await asyncio.sleep(0.1)  # Simulate email sending
    
    async def _send_slack_notification(self, recipient: str, subject: str, body: str):
        """Send Slack notification"""
        # In production, integrate with Slack API
        logger.info(f"💬 SLACK to {recipient}: {subject}")
        await asyncio.sleep(0.1)  # Simulate Slack sending
    
    async def _send_teams_notification(self, recipient: str, subject: str, body: str):
        """Send Teams notification"""
        # In production, integrate with Microsoft Teams API
        logger.info(f"👥 TEAMS to {recipient}: {subject}")
        await asyncio.sleep(0.1)  # Simulate Teams sending
    
    async def _send_sms_notification(self, recipient: str, message: str):
        """Send SMS notification"""
        # In production, integrate with SMS service (Twilio, etc.)
        logger.info(f"📱 SMS to {recipient}: {message}")
        await asyncio.sleep(0.1)  # Simulate SMS sending
    
    def _calculate_approvers_required(self, approval_type: str, total_approvers: int) -> int:
        """Calculate number of approvers required based on approval type"""
        
        if approval_type == "single":
            return 1
        elif approval_type == "majority":
            return (total_approvers // 2) + 1
        elif approval_type == "unanimous":
            return total_approvers
        else:
            return 1  # Default to single
    
    async def get_escalation_status(self, escalation_id: str) -> Dict[str, Any]:
        """Get status of escalation"""
        
        if escalation_id not in self.escalations:
            raise ValueError(f"Escalation {escalation_id} not found")
        
        escalation = self.escalations[escalation_id]
        
        return {
            "escalation_id": escalation_id,
            "status": escalation["status"],
            "context": escalation["context"],
            "urgency": escalation["urgency"],
            "stakeholders": escalation["stakeholders"],
            "responses_received": len(escalation["responses"]),
            "created_at": escalation["created_at"].isoformat()
        }
    
    async def get_approval_status(self, approval_id: str) -> Dict[str, Any]:
        """Get status of approval request"""
        
        if approval_id not in self.approvals:
            raise ValueError(f"Approval {approval_id} not found")
        
        approval = self.approvals[approval_id]
        approvers_required = self._calculate_approvers_required(approval["approval_type"], len(approval["approvers"]))
        
        return {
            "approval_id": approval_id,
            "status": approval["status"],
            "action_description": approval["action_description"],
            "approvals_received": len(approval["approvals_received"]),
            "approvers_required": approvers_required,
            "approval_type": approval["approval_type"],
            "expires_at": approval["expires_at"].isoformat(),
            "created_at": approval["created_at"].isoformat()
        }
    
    async def cleanup(self):
        """Cleanup escalation adapter"""
        
        # Clean up expired approvals
        now = datetime.utcnow()
        expired_approvals = [
            approval_id for approval_id, approval in self.approvals.items()
            if approval["expires_at"] < now
        ]
        
        for approval_id in expired_approvals:
            self.approvals[approval_id]["status"] = "expired"
        
        self.is_initialized = False
        logger.info("✅ Escalation adapter cleaned up")