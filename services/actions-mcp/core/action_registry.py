"""
Action Registry - Central registry for all available external actions
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ActionDefinition:
    """Definition of an external action"""
    name: str
    description: str
    adapter_class: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    category: str
    security_level: str = "standard"  # standard, elevated, admin
    rate_limit: int = 10  # requests per minute
    timeout: int = 30     # seconds
    retry_count: int = 3
    requires_approval: bool = False
    examples: List[Dict[str, Any]] = None

class ActionRegistry:
    """Central registry for all available external actions"""
    
    def __init__(self):
        self.actions: Dict[str, ActionDefinition] = {}
        self.categories = {
            "escalation": "Human Escalation and Approval",
            "notification": "Notifications and Communications",
            "workflow": "Workflow and Pipeline Triggers",
            "integration": "External System Integration",
            "documentation": "Documentation and Knowledge Management",
            "monitoring": "Monitoring and Alerting",
            "security": "Security and Compliance Actions"
        }
        
    async def initialize(self):
        """Initialize action registry with default actions"""
        try:
            self._register_escalation_actions()
            self._register_notification_actions()
            self._register_workflow_actions()
            self._register_integration_actions()
            self._register_documentation_actions()
            self._register_monitoring_actions()
            self._register_security_actions()
            
            logger.info(f"✅ Action registry initialized with {len(self.actions)} actions")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize action registry: {e}")
            raise
    
    def _register_escalation_actions(self):
        """Register human escalation actions"""
        
        # Escalate to human
        self.actions["escalate_to_human"] = ActionDefinition(
            name="escalate_to_human",
            description="Escalate decision or issue to human stakeholder",
            adapter_class="EscalationAdapter",
            input_schema={
                "type": "object",
                "properties": {
                    "context": {"type": "string", "description": "Context and reason for escalation"},
                    "urgency": {"type": "string", "enum": ["low", "medium", "high", "critical"], "default": "medium"},
                    "stakeholders": {"type": "array", "items": {"type": "string"}, "description": "List of stakeholder roles or names"},
                    "deadline": {"type": "string", "format": "date-time", "description": "Optional deadline for response"},
                    "attachments": {"type": "array", "items": {"type": "string"}, "description": "File paths or URLs to attach"},
                    "notification_channels": {"type": "array", "items": {"type": "string", "enum": ["email", "slack", "teams", "sms"]}}
                },
                "required": ["context", "stakeholders"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "escalation_id": {"type": "string"},
                    "status": {"type": "string"},
                    "notified_stakeholders": {"type": "array"},
                    "estimated_response_time": {"type": "string"},
                    "tracking_url": {"type": "string"}
                }
            },
            category="escalation",
            security_level="elevated",
            rate_limit=5,
            examples=[
                {
                    "input": {
                        "context": "Critical security vulnerability found in production system",
                        "urgency": "critical",
                        "stakeholders": ["security_team", "tech_lead", "cto"],
                        "notification_channels": ["slack", "email", "sms"]
                    },
                    "description": "Critical security escalation"
                }
            ]
        )
        
        # Request approval
        self.actions["request_approval"] = ActionDefinition(
            name="request_approval",
            description="Request approval for an action or decision",
            adapter_class="EscalationAdapter",
            input_schema={
                "type": "object",
                "properties": {
                    "action_description": {"type": "string", "description": "What needs approval"},
                    "approvers": {"type": "array", "items": {"type": "string"}},
                    "justification": {"type": "string", "description": "Why this action is needed"},
                    "impact_assessment": {"type": "string", "description": "Potential impact if approved"},
                    "deadline": {"type": "string", "format": "date-time"},
                    "approval_type": {"type": "string", "enum": ["single", "majority", "unanimous"], "default": "single"}
                },
                "required": ["action_description", "approvers", "justification"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "approval_id": {"type": "string"},
                    "status": {"type": "string"},
                    "approvers_notified": {"type": "array"},
                    "approval_url": {"type": "string"}
                }
            },
            category="escalation",
            security_level="elevated",
            requires_approval=False  # Requesting approval doesn't need approval itself
        )
    
    def _register_notification_actions(self):
        """Register notification and communication actions"""
        
        # Send email
        self.actions["send_email"] = ActionDefinition(
            name="send_email",
            description="Send email notification",
            adapter_class="EmailAdapter",
            input_schema={
                "type": "object",
                "properties": {
                    "recipients": {"type": "array", "items": {"type": "string"}},
                    "subject": {"type": "string"},
                    "template": {"type": "string", "description": "Email template name"},
                    "data": {"type": "object", "description": "Template data"},
                    "priority": {"type": "string", "enum": ["low", "normal", "high"], "default": "normal"},
                    "attachments": {"type": "array", "items": {"type": "string"}},
                    "cc": {"type": "array", "items": {"type": "string"}},
                    "bcc": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["recipients", "subject"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "message_id": {"type": "string"},
                    "status": {"type": "string"},
                    "delivery_status": {"type": "object"}
                }
            },
            category="notification",
            rate_limit=50
        )
        
        # Send Slack message
        self.actions["send_slack_message"] = ActionDefinition(
            name="send_slack_message",
            description="Send message to Slack channel or user",
            adapter_class="SlackAdapter",
            input_schema={
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "description": "Channel name or user ID"},
                    "message": {"type": "string"},
                    "template": {"type": "string", "description": "Message template name"},
                    "data": {"type": "object", "description": "Template data"},
                    "thread_ts": {"type": "string", "description": "Thread timestamp for replies"},
                    "blocks": {"type": "array", "description": "Slack block kit elements"}
                },
                "required": ["channel", "message"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "message_ts": {"type": "string"},
                    "channel": {"type": "string"},
                    "status": {"type": "string"}
                }
            },
            category="notification",
            rate_limit=100
        )
    
    def _register_workflow_actions(self):
        """Register workflow and pipeline trigger actions"""
        
        # Trigger workflow
        self.actions["trigger_workflow"] = ActionDefinition(
            name="trigger_workflow",
            description="Trigger external workflow or pipeline",
            adapter_class="WorkflowAdapter",
            input_schema={
                "type": "object",
                "properties": {
                    "workflow_type": {"type": "string", "enum": ["deployment", "testing", "security_scan", "backup", "custom"]},
                    "environment": {"type": "string", "enum": ["development", "staging", "production"]},
                    "parameters": {"type": "object", "description": "Workflow-specific parameters"},
                    "trigger_conditions": {"type": "object", "description": "Conditions that must be met"},
                    "timeout": {"type": "integer", "description": "Workflow timeout in minutes", "default": 30},
                    "priority": {"type": "string", "enum": ["low", "normal", "high"], "default": "normal"}
                },
                "required": ["workflow_type"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string"},
                    "status": {"type": "string"},
                    "estimated_duration": {"type": "integer"},
                    "monitoring_url": {"type": "string"}
                }
            },
            category="workflow",
            security_level="elevated",
            timeout=60
        )
        
        # Stop workflow
        self.actions["stop_workflow"] = ActionDefinition(
            name="stop_workflow",
            description="Stop running workflow or pipeline",
            adapter_class="WorkflowAdapter",
            input_schema={
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string"},
                    "reason": {"type": "string", "description": "Reason for stopping"},
                    "force": {"type": "boolean", "default": False, "description": "Force stop without cleanup"}
                },
                "required": ["workflow_id", "reason"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string"},
                    "status": {"type": "string"},
                    "stop_time": {"type": "string"}
                }
            },
            category="workflow",
            security_level="elevated",
            requires_approval=True
        )
    
    def _register_integration_actions(self):
        """Register external system integration actions"""
        
        # Create Jira ticket
        self.actions["create_jira_ticket"] = ActionDefinition(
            name="create_jira_ticket",
            description="Create ticket in Jira",
            adapter_class="JiraAdapter",
            input_schema={
                "type": "object",
                "properties": {
                    "project": {"type": "string"},
                    "issue_type": {"type": "string", "enum": ["Bug", "Task", "Story", "Epic", "Incident"]},
                    "summary": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {"type": "string", "enum": ["Lowest", "Low", "Medium", "High", "Highest"]},
                    "assignee": {"type": "string"},
                    "labels": {"type": "array", "items": {"type": "string"}},
                    "components": {"type": "array", "items": {"type": "string"}},
                    "custom_fields": {"type": "object"}
                },
                "required": ["project", "issue_type", "summary"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string"},
                    "ticket_url": {"type": "string"},
                    "status": {"type": "string"}
                }
            },
            category="integration",
            rate_limit=20
        )
        
        # Create GitHub issue
        self.actions["create_github_issue"] = ActionDefinition(
            name="create_github_issue",
            description="Create issue in GitHub repository",
            adapter_class="GitHubAdapter",
            input_schema={
                "type": "object",
                "properties": {
                    "repository": {"type": "string", "description": "Repository in format owner/repo"},
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                    "labels": {"type": "array", "items": {"type": "string"}},
                    "assignees": {"type": "array", "items": {"type": "string"}},
                    "milestone": {"type": "integer"},
                    "projects": {"type": "array", "items": {"type": "integer"}}
                },
                "required": ["repository", "title"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "issue_id": {"type": "integer"},
                    "issue_url": {"type": "string"},
                    "issue_number": {"type": "integer"}
                }
            },
            category="integration",
            rate_limit=30
        )
    
    def _register_documentation_actions(self):
        """Register documentation management actions"""
        
        # Update documentation
        self.actions["update_documentation"] = ActionDefinition(
            name="update_documentation",
            description="Update documentation in external system",
            adapter_class="DocumentationAdapter",
            input_schema={
                "type": "object",
                "properties": {
                    "service": {"type": "string", "enum": ["confluence", "notion", "gitbook", "wiki"]},
                    "page_id": {"type": "string"},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "format": {"type": "string", "enum": ["markdown", "html", "plain"], "default": "markdown"},
                    "create_if_missing": {"type": "boolean", "default": False},
                    "parent_page": {"type": "string"}
                },
                "required": ["service", "content"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string"},
                    "page_url": {"type": "string"},
                    "version": {"type": "string"},
                    "status": {"type": "string"}
                }
            },
            category="documentation",
            rate_limit=15
        )
    
    def _register_monitoring_actions(self):
        """Register monitoring and alerting actions"""
        
        # Create alert
        self.actions["create_alert"] = ActionDefinition(
            name="create_alert",
            description="Create monitoring alert",
            adapter_class="MonitoringAdapter",
            input_schema={
                "type": "object",
                "properties": {
                    "service": {"type": "string", "enum": ["datadog", "newrelic", "prometheus", "grafana"]},
                    "alert_name": {"type": "string"},
                    "condition": {"type": "string"},
                    "severity": {"type": "string", "enum": ["info", "warning", "error", "critical"]},
                    "notification_channels": {"type": "array", "items": {"type": "string"}},
                    "tags": {"type": "object"}
                },
                "required": ["service", "alert_name", "condition"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "alert_id": {"type": "string"},
                    "alert_url": {"type": "string"},
                    "status": {"type": "string"}
                }
            },
            category="monitoring",
            security_level="elevated"
        )
    
    def _register_security_actions(self):
        """Register security and compliance actions"""
        
        # Trigger security scan
        self.actions["trigger_security_scan"] = ActionDefinition(
            name="trigger_security_scan",
            description="Trigger security scan on target system",
            adapter_class="SecurityAdapter",
            input_schema={
                "type": "object",
                "properties": {
                    "scan_type": {"type": "string", "enum": ["vulnerability", "compliance", "penetration", "code_analysis"]},
                    "target": {"type": "string", "description": "Target system or code repository"},
                    "scope": {"type": "string", "enum": ["full", "incremental", "critical_only"]},
                    "compliance_framework": {"type": "string", "enum": ["SOC2", "GDPR", "HIPAA", "PCI_DSS"]},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"}
                },
                "required": ["scan_type", "target"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "scan_id": {"type": "string"},
                    "status": {"type": "string"},
                    "estimated_completion": {"type": "string"},
                    "results_url": {"type": "string"}
                }
            },
            category="security",
            security_level="admin",
            requires_approval=True,
            timeout=300  # 5 minutes
        )
    
    def register_action(self, action: ActionDefinition):
        """Register a new action"""
        self.actions[action.name] = action
        logger.info(f"✅ Registered action: {action.name}")
    
    def get_action(self, name: str) -> Optional[ActionDefinition]:
        """Get action definition by name"""
        return self.actions.get(name)
    
    def get_actions_by_category(self, category: str) -> Dict[str, ActionDefinition]:
        """Get actions by category"""
        return {
            name: action for name, action in self.actions.items()
            if action.category == category
        }
    
    def get_all_actions(self) -> Dict[str, ActionDefinition]:
        """Get all registered actions"""
        return self.actions.copy()
    
    def get_action_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get action schemas for MCP integration"""
        schemas = {}
        for name, action in self.actions.items():
            schemas[name] = {
                "description": action.description,
                "inputSchema": action.input_schema,
                "outputSchema": action.output_schema,
                "category": action.category,
                "security_level": action.security_level,
                "rate_limit": action.rate_limit,
                "examples": action.examples or []
            }
        return schemas
    
    def get_categories(self) -> Dict[str, str]:
        """Get available action categories"""
        return self.categories.copy()