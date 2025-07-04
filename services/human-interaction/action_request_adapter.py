"""
UltraMCP Supreme Stack - Action Request Adapter
Handles external action requests requiring human intervention

This module manages:
- Action classification and risk assessment
- Human approval workflows
- External system integration (email, ticketing, studies)
- Escalation chains
- Decision audit logging
"""

import asyncio
import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from enum import Enum
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field

# Internal imports
from core.orchestrator.eventBus import EventBus
from human_feedback.hitlManager import HITLManager
from apps.backend.src.adapters.baseMCPAdapter import BaseMCPAdapter


class ActionRiskLevel(Enum):
    """Risk levels for actions requiring different approval processes"""
    LOW = "low"           # Auto-approve or basic notification
    MEDIUM = "medium"     # Single human approval required
    HIGH = "high"         # Multiple approvals or escalation
    CRITICAL = "critical" # Executive/expert approval required


class ActionType(Enum):
    """Types of external actions the system can request"""
    EMAIL_SEND = "email_send"
    HUMAN_CONSULTATION = "human_consultation"
    EXPERT_REVIEW = "expert_review"
    MEDICAL_STUDY = "medical_study"
    LEGAL_REVIEW = "legal_review"
    FINANCIAL_APPROVAL = "financial_approval"
    SYSTEM_ACCESS = "system_access"
    DATA_COLLECTION = "data_collection"
    ESCALATION = "escalation"
    TICKET_CREATION = "ticket_creation"
    EXTERNAL_API_CALL = "external_api_call"
    RESEARCH_REQUEST = "research_request"


class ActionStatus(Enum):
    """Status of action requests"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    ESCALATED = "escalated"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ActionRequest:
    """Represents a request for external action requiring human approval"""
    id: str
    action_type: ActionType
    risk_level: ActionRiskLevel
    title: str
    description: str
    context: Dict[str, Any]
    requested_by: str  # Agent/system that requested
    created_at: datetime
    expires_at: Optional[datetime] = None
    status: ActionStatus = ActionStatus.PENDING
    assigned_to: Optional[str] = None
    approval_chain: List[str] = None
    decision_reason: Optional[str] = None
    decision_at: Optional[datetime] = None
    decision_by: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.approval_chain is None:
            self.approval_chain = []
        if self.metadata is None:
            self.metadata = {}


class HumanApprovalRequest(BaseModel):
    """Pydantic model for API requests"""
    action_type: ActionType
    title: str
    description: str
    context: Dict[str, Any] = Field(default_factory=dict)
    risk_level: Optional[ActionRiskLevel] = ActionRiskLevel.MEDIUM
    expires_in_minutes: Optional[int] = 60
    approval_chain: Optional[List[str]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ActionRequestAdapter(BaseMCPAdapter):
    """
    Advanced adapter for handling external action requests with human-in-the-loop
    
    Features:
    - Intelligent action classification
    - Risk-based approval workflows
    - Multi-channel notifications
    - Escalation chains
    - Decision learning
    """
    
    def __init__(self, event_bus: EventBus, hitl_manager: HITLManager):
        super().__init__()
        self.event_bus = event_bus
        self.hitl_manager = hitl_manager
        self.logger = logging.getLogger(f"{__name__}.ActionRequestAdapter")
        
        # Active action requests
        self.pending_requests: Dict[str, ActionRequest] = {}
        self.completed_requests: Dict[str, ActionRequest] = {}
        
        # Configuration
        self.config = {
            "default_timeout_minutes": 60,
            "escalation_timeout_minutes": 30,
            "auto_approve_threshold": 0.9,
            "max_approval_chain_length": 5,
            "enable_learning": True
        }
        
        # Risk assessment rules
        self.risk_rules = {
            ActionType.EMAIL_SEND: self._assess_email_risk,
            ActionType.HUMAN_CONSULTATION: self._assess_consultation_risk,
            ActionType.MEDICAL_STUDY: self._assess_medical_study_risk,
            ActionType.FINANCIAL_APPROVAL: self._assess_financial_risk,
            ActionType.SYSTEM_ACCESS: self._assess_system_access_risk,
            ActionType.LEGAL_REVIEW: self._assess_legal_risk,
            ActionType.ESCALATION: self._assess_escalation_risk
        }
        
        # Approval chain templates
        self.approval_chains = {
            ActionRiskLevel.LOW: [],  # Auto-approve or notification only
            ActionRiskLevel.MEDIUM: ["team_lead"],
            ActionRiskLevel.HIGH: ["team_lead", "department_head"],
            ActionRiskLevel.CRITICAL: ["team_lead", "department_head", "executive"]
        }
        
        # Setup event listeners
        self._setup_event_listeners()
        
        self.logger.info("ActionRequestAdapter initialized with human-in-the-loop capabilities")

    def getId(self) -> str:
        return "action_request_adapter"

    def getTools(self) -> List[Dict[str, Any]]:
        """Return available tools for action requests"""
        return [
            {
                "name": "request_human_approval",
                "description": "Request human approval for sensitive or high-risk actions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action_type": {
                            "type": "string",
                            "enum": [t.value for t in ActionType],
                            "description": "Type of action requiring approval"
                        },
                        "title": {
                            "type": "string",
                            "description": "Brief title for the action request"
                        },
                        "description": {
                            "type": "string", 
                            "description": "Detailed description of the action and why it's needed"
                        },
                        "context": {
                            "type": "object",
                            "description": "Additional context for decision making"
                        },
                        "urgency": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                            "description": "Urgency level of the request"
                        }
                    },
                    "required": ["action_type", "title", "description"]
                }
            },
            {
                "name": "request_expert_consultation",
                "description": "Request consultation from domain expert",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "domain": {
                            "type": "string",
                            "description": "Domain of expertise needed (medical, legal, technical, etc.)"
                        },
                        "question": {
                            "type": "string",
                            "description": "Specific question or consultation needed"
                        },
                        "context": {
                            "type": "object",
                            "description": "Background context for the consultation"
                        },
                        "urgency": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"]
                        }
                    },
                    "required": ["domain", "question"]
                }
            },
            {
                "name": "request_additional_information",
                "description": "Request additional information from user or external source",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "information_type": {
                            "type": "string",
                            "description": "Type of information needed"
                        },
                        "questions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific questions to ask"
                        },
                        "source": {
                            "type": "string",
                            "enum": ["user", "expert", "external_system", "database"],
                            "description": "Where to get the information"
                        }
                    },
                    "required": ["information_type", "questions"]
                }
            },
            {
                "name": "suggest_investigation",
                "description": "Suggest further investigation or study",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "investigation_type": {
                            "type": "string",
                            "enum": ["medical_test", "market_research", "technical_analysis", "legal_research", "user_study"]
                        },
                        "rationale": {
                            "type": "string",
                            "description": "Why this investigation is recommended"
                        },
                        "expected_outcomes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "What insights the investigation might provide"
                        },
                        "estimated_time": {
                            "type": "string",
                            "description": "Estimated time to complete"
                        },
                        "estimated_cost": {
                            "type": "number",
                            "description": "Estimated cost if applicable"
                        }
                    },
                    "required": ["investigation_type", "rationale"]
                }
            },
            {
                "name": "escalate_to_human",
                "description": "Escalate issue to human operator via ticketing system",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "escalation_reason": {
                            "type": "string",
                            "enum": ["complexity", "safety", "legal", "ethical", "technical_failure", "user_request"]
                        },
                        "summary": {
                            "type": "string",
                            "description": "Brief summary of the issue"
                        },
                        "details": {
                            "type": "string",
                            "description": "Detailed description of the situation"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"]
                        },
                        "suggested_actions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Suggested next steps for human operator"
                        }
                    },
                    "required": ["escalation_reason", "summary", "details"]
                }
            }
        ]

    async def executeAction(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action request with human-in-the-loop"""
        try:
            if action == "request_human_approval":
                return await self._handle_approval_request(parameters)
            elif action == "request_expert_consultation":
                return await self._handle_expert_consultation(parameters)
            elif action == "request_additional_information":
                return await self._handle_information_request(parameters)
            elif action == "suggest_investigation":
                return await self._handle_investigation_suggestion(parameters)
            elif action == "escalate_to_human":
                return await self._handle_escalation(parameters)
            else:
                raise ValueError(f"Unknown action: {action}")
                
        except Exception as e:
            self.logger.error(f"Error executing action {action}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "action": action,
                "timestamp": datetime.now().isoformat()
            }

    async def _handle_approval_request(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle human approval request"""
        try:
            # Create approval request
            request = HumanApprovalRequest(**parameters)
            
            # Assess risk level if not provided
            if "urgency" in parameters:
                urgency_to_risk = {
                    "low": ActionRiskLevel.LOW,
                    "medium": ActionRiskLevel.MEDIUM,
                    "high": ActionRiskLevel.HIGH,
                    "critical": ActionRiskLevel.CRITICAL
                }
                request.risk_level = urgency_to_risk.get(parameters["urgency"], ActionRiskLevel.MEDIUM)
            
            # Perform intelligent risk assessment
            assessed_risk = await self._assess_action_risk(request.action_type, request.context)
            if assessed_risk:
                request.risk_level = max(request.risk_level, assessed_risk)
            
            # Create action request
            action_request = ActionRequest(
                id=str(uuid.uuid4()),
                action_type=request.action_type,
                risk_level=request.risk_level,
                title=request.title,
                description=request.description,
                context=request.context,
                requested_by="agent_system",
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(minutes=request.expires_in_minutes or 60),
                approval_chain=request.approval_chain or self.approval_chains[request.risk_level],
                metadata=request.metadata
            )
            
            # Check if auto-approval is possible
            if request.risk_level == ActionRiskLevel.LOW:
                confidence_score = await self._calculate_confidence_score(action_request)
                if confidence_score >= self.config["auto_approve_threshold"]:
                    action_request.status = ActionStatus.APPROVED
                    action_request.decision_reason = f"Auto-approved (confidence: {confidence_score:.2f})"
                    action_request.decision_at = datetime.now()
                    action_request.decision_by = "auto_approval_system"
                    
                    self.completed_requests[action_request.id] = action_request
                    
                    # Emit approval event
                    self.event_bus.emit('action.auto_approved', {
                        'request_id': action_request.id,
                        'action_type': action_request.action_type.value,
                        'confidence_score': confidence_score
                    })
                    
                    return {
                        "success": True,
                        "request_id": action_request.id,
                        "status": "auto_approved",
                        "confidence_score": confidence_score,
                        "message": "Action was automatically approved based on high confidence score"
                    }
            
            # Store pending request
            self.pending_requests[action_request.id] = action_request
            
            # Emit request event for notification system
            self.event_bus.emit('action.approval_requested', {
                'request_id': action_request.id,
                'action_type': action_request.action_type.value,
                'risk_level': action_request.risk_level.value,
                'title': action_request.title,
                'description': action_request.description,
                'approval_chain': action_request.approval_chain,
                'expires_at': action_request.expires_at.isoformat()
            })
            
            # Wait for human input
            decision = await self._wait_for_human_decision(action_request)
            
            return {
                "success": True,
                "request_id": action_request.id,
                "status": decision["status"],
                "decision": decision,
                "message": f"Human approval process completed with status: {decision['status']}"
            }
            
        except Exception as e:
            self.logger.error(f"Error handling approval request: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process approval request"
            }

    async def _handle_expert_consultation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle expert consultation request"""
        consultation_request = ActionRequest(
            id=str(uuid.uuid4()),
            action_type=ActionType.EXPERT_REVIEW,
            risk_level=ActionRiskLevel.MEDIUM,
            title=f"Expert Consultation: {parameters['domain']}",
            description=f"Question: {parameters['question']}",
            context={
                "domain": parameters["domain"],
                "question": parameters["question"],
                "consultation_context": parameters.get("context", {}),
                "urgency": parameters.get("urgency", "medium")
            },
            requested_by="agent_system",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24)  # Longer timeout for expert consultation
        )
        
        self.pending_requests[consultation_request.id] = consultation_request
        
        # Emit expert consultation event
        self.event_bus.emit('expert.consultation_requested', {
            'request_id': consultation_request.id,
            'domain': parameters['domain'],
            'question': parameters['question'],
            'urgency': parameters.get('urgency', 'medium')
        })
        
        return {
            "success": True,
            "request_id": consultation_request.id,
            "status": "consultation_requested",
            "message": f"Expert consultation requested for {parameters['domain']} domain",
            "estimated_response_time": "24 hours"
        }

    async def _handle_information_request(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle additional information request"""
        info_request = ActionRequest(
            id=str(uuid.uuid4()),
            action_type=ActionType.DATA_COLLECTION,
            risk_level=ActionRiskLevel.LOW,
            title=f"Information Request: {parameters['information_type']}",
            description=f"Questions: {', '.join(parameters['questions'])}",
            context={
                "information_type": parameters["information_type"],
                "questions": parameters["questions"],
                "source": parameters.get("source", "user")
            },
            requested_by="agent_system",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=4)
        )
        
        self.pending_requests[info_request.id] = info_request
        
        # Emit information request event
        self.event_bus.emit('information.requested', {
            'request_id': info_request.id,
            'information_type': parameters['information_type'],
            'questions': parameters['questions'],
            'source': parameters.get('source', 'user')
        })
        
        return {
            "success": True,
            "request_id": info_request.id,
            "status": "information_requested",
            "questions": parameters["questions"],
            "message": "Additional information has been requested"
        }

    async def _handle_investigation_suggestion(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle investigation/study suggestion"""
        investigation_request = ActionRequest(
            id=str(uuid.uuid4()),
            action_type=ActionType.RESEARCH_REQUEST,
            risk_level=ActionRiskLevel.MEDIUM,
            title=f"Investigation Suggestion: {parameters['investigation_type']}",
            description=parameters['rationale'],
            context={
                "investigation_type": parameters["investigation_type"],
                "rationale": parameters["rationale"],
                "expected_outcomes": parameters.get("expected_outcomes", []),
                "estimated_time": parameters.get("estimated_time"),
                "estimated_cost": parameters.get("estimated_cost")
            },
            requested_by="agent_system",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=7)  # Longer timeout for investigation planning
        )
        
        self.pending_requests[investigation_request.id] = investigation_request
        
        # Emit investigation suggestion event
        self.event_bus.emit('investigation.suggested', {
            'request_id': investigation_request.id,
            'investigation_type': parameters['investigation_type'],
            'rationale': parameters['rationale'],
            'expected_outcomes': parameters.get('expected_outcomes', []),
            'estimated_time': parameters.get('estimated_time'),
            'estimated_cost': parameters.get('estimated_cost')
        })
        
        return {
            "success": True,
            "request_id": investigation_request.id,
            "status": "investigation_suggested",
            "investigation_type": parameters["investigation_type"],
            "message": "Investigation has been suggested for human review"
        }

    async def _handle_escalation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle escalation to human operator"""
        escalation_request = ActionRequest(
            id=str(uuid.uuid4()),
            action_type=ActionType.ESCALATION,
            risk_level=ActionRiskLevel.HIGH,
            title=f"Escalation: {parameters['escalation_reason']}",
            description=parameters['details'],
            context={
                "escalation_reason": parameters["escalation_reason"],
                "summary": parameters["summary"],
                "details": parameters["details"],
                "priority": parameters.get("priority", "medium"),
                "suggested_actions": parameters.get("suggested_actions", [])
            },
            requested_by="agent_system",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=2)  # Escalations need quick response
        )
        
        self.pending_requests[escalation_request.id] = escalation_request
        
        # Emit escalation event
        self.event_bus.emit('escalation.created', {
            'request_id': escalation_request.id,
            'escalation_reason': parameters['escalation_reason'],
            'summary': parameters['summary'],
            'priority': parameters.get('priority', 'medium'),
            'suggested_actions': parameters.get('suggested_actions', [])
        })
        
        # Automatically create ticket if ticketing system is available
        await self._create_support_ticket(escalation_request)
        
        return {
            "success": True,
            "request_id": escalation_request.id,
            "status": "escalated",
            "priority": parameters.get("priority", "medium"),
            "message": "Issue has been escalated to human operator"
        }

    async def _wait_for_human_decision(self, action_request: ActionRequest) -> Dict[str, Any]:
        """Wait for human decision using EventBus wait_for_input functionality"""
        try:
            # Create wait condition
            wait_event = f"action.decision.{action_request.id}"
            timeout_seconds = (action_request.expires_at - datetime.now()).total_seconds()
            
            # Use EventBus wait_for_input (to be implemented)
            decision = await self.event_bus.wait_for_input(
                event_pattern=wait_event,
                timeout_seconds=int(timeout_seconds),
                default_response={
                    "status": "timeout",
                    "reason": "No human response within timeout period"
                }
            )
            
            # Update request with decision
            action_request.status = ActionStatus(decision.get("status", "timeout"))
            action_request.decision_reason = decision.get("reason", "")
            action_request.decision_at = datetime.now()
            action_request.decision_by = decision.get("decided_by", "unknown")
            
            # Move to completed requests
            self.completed_requests[action_request.id] = action_request
            if action_request.id in self.pending_requests:
                del self.pending_requests[action_request.id]
            
            # Emit decision event
            self.event_bus.emit('action.decision_made', {
                'request_id': action_request.id,
                'status': action_request.status.value,
                'decision_by': action_request.decision_by,
                'decision_reason': action_request.decision_reason
            })
            
            return decision
            
        except Exception as e:
            self.logger.error(f"Error waiting for human decision: {str(e)}")
            return {
                "status": "error",
                "reason": f"Error in decision process: {str(e)}"
            }

    async def _assess_action_risk(self, action_type: ActionType, context: Dict[str, Any]) -> Optional[ActionRiskLevel]:
        """Intelligent risk assessment based on action type and context"""
        if action_type in self.risk_rules:
            return await self.risk_rules[action_type](context)
        return None

    async def _assess_email_risk(self, context: Dict[str, Any]) -> ActionRiskLevel:
        """Assess risk for email sending"""
        recipients = context.get("recipients", [])
        if len(recipients) > 100:
            return ActionRiskLevel.HIGH
        elif any("@external.com" in r for r in recipients):
            return ActionRiskLevel.MEDIUM
        return ActionRiskLevel.LOW

    async def _assess_consultation_risk(self, context: Dict[str, Any]) -> ActionRiskLevel:
        """Assess risk for human consultation"""
        urgency = context.get("urgency", "medium")
        if urgency == "critical":
            return ActionRiskLevel.HIGH
        return ActionRiskLevel.MEDIUM

    async def _assess_medical_study_risk(self, context: Dict[str, Any]) -> ActionRiskLevel:
        """Assess risk for medical study requests"""
        # Medical studies always require careful human review
        return ActionRiskLevel.HIGH

    async def _assess_financial_risk(self, context: Dict[str, Any]) -> ActionRiskLevel:
        """Assess risk for financial actions"""
        amount = context.get("amount", 0)
        if amount > 10000:
            return ActionRiskLevel.CRITICAL
        elif amount > 1000:
            return ActionRiskLevel.HIGH
        return ActionRiskLevel.MEDIUM

    async def _assess_system_access_risk(self, context: Dict[str, Any]) -> ActionRiskLevel:
        """Assess risk for system access requests"""
        access_level = context.get("access_level", "read")
        if access_level in ["admin", "root"]:
            return ActionRiskLevel.CRITICAL
        elif access_level == "write":
            return ActionRiskLevel.HIGH
        return ActionRiskLevel.MEDIUM

    async def _assess_legal_risk(self, context: Dict[str, Any]) -> ActionRiskLevel:
        """Assess risk for legal reviews"""
        # Legal matters typically require careful review
        return ActionRiskLevel.HIGH

    async def _assess_escalation_risk(self, context: Dict[str, Any]) -> ActionRiskLevel:
        """Assess risk for escalations"""
        priority = context.get("priority", "medium")
        if priority == "critical":
            return ActionRiskLevel.CRITICAL
        elif priority == "high":
            return ActionRiskLevel.HIGH
        return ActionRiskLevel.MEDIUM

    async def _calculate_confidence_score(self, action_request: ActionRequest) -> float:
        """Calculate confidence score for auto-approval decisions"""
        # Base confidence on action type
        base_confidence = {
            ActionType.EMAIL_SEND: 0.8,
            ActionType.DATA_COLLECTION: 0.9,
            ActionType.RESEARCH_REQUEST: 0.7,
            ActionType.HUMAN_CONSULTATION: 0.5,
            ActionType.MEDICAL_STUDY: 0.3,
            ActionType.FINANCIAL_APPROVAL: 0.2,
            ActionType.SYSTEM_ACCESS: 0.1
        }.get(action_request.action_type, 0.5)
        
        # Adjust based on context factors
        context_factors = action_request.context
        
        # Risk level adjustment
        risk_adjustment = {
            ActionRiskLevel.LOW: 0.2,
            ActionRiskLevel.MEDIUM: 0.0,
            ActionRiskLevel.HIGH: -0.3,
            ActionRiskLevel.CRITICAL: -0.5
        }.get(action_request.risk_level, 0.0)
        
        final_confidence = max(0.0, min(1.0, base_confidence + risk_adjustment))
        return final_confidence

    async def _create_support_ticket(self, action_request: ActionRequest):
        """Create support ticket for escalated issues"""
        ticket_data = {
            "title": action_request.title,
            "description": action_request.description,
            "priority": action_request.context.get("priority", "medium"),
            "category": "agent_escalation",
            "source": "ultramcp_agent",
            "metadata": {
                "request_id": action_request.id,
                "action_type": action_request.action_type.value,
                "escalation_reason": action_request.context.get("escalation_reason"),
                "suggested_actions": action_request.context.get("suggested_actions", [])
            }
        }
        
        # Emit ticket creation event
        self.event_bus.emit('ticket.create', ticket_data)

    def _setup_event_listeners(self):
        """Setup event listeners for action processing"""
        
        # Listen for decision responses
        self.event_bus.on('action.decision_response', self._handle_decision_response)
        
        # Listen for timeout events
        self.event_bus.on('action.timeout', self._handle_timeout)
        
        # Listen for escalation responses
        self.event_bus.on('action.escalation_response', self._handle_escalation_response)

    async def _handle_decision_response(self, event_data: Dict[str, Any]):
        """Handle human decision responses"""
        request_id = event_data.get("request_id")
        if request_id in self.pending_requests:
            # Emit decision to wake up waiting process
            self.event_bus.emit(f"action.decision.{request_id}", event_data)

    async def _handle_timeout(self, event_data: Dict[str, Any]):
        """Handle action timeouts"""
        request_id = event_data.get("request_id")
        if request_id in self.pending_requests:
            action_request = self.pending_requests[request_id]
            
            # Check if escalation is needed
            if len(action_request.approval_chain) > 1:
                # Escalate to next level
                action_request.approval_chain.pop(0)  # Remove current approver
                action_request.status = ActionStatus.ESCALATED
                
                self.event_bus.emit('action.escalated', {
                    'request_id': request_id,
                    'new_approver': action_request.approval_chain[0],
                    'reason': 'timeout_escalation'
                })
            else:
                # Final timeout
                action_request.status = ActionStatus.TIMEOUT
                self.event_bus.emit(f"action.decision.{request_id}", {
                    "status": "timeout",
                    "reason": "Final timeout reached with no response"
                })

    async def _handle_escalation_response(self, event_data: Dict[str, Any]):
        """Handle escalation responses"""
        request_id = event_data.get("request_id")
        if request_id in self.pending_requests:
            # Process escalation response
            self.event_bus.emit(f"action.decision.{request_id}", event_data)

    # Public API methods for external integration

    async def get_pending_requests(self, filter_by: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get pending action requests with optional filtering"""
        requests = list(self.pending_requests.values())
        
        if filter_by:
            if "action_type" in filter_by:
                requests = [r for r in requests if r.action_type.value == filter_by["action_type"]]
            if "risk_level" in filter_by:
                requests = [r for r in requests if r.risk_level.value == filter_by["risk_level"]]
            if "assigned_to" in filter_by:
                requests = [r for r in requests if r.assigned_to == filter_by["assigned_to"]]
        
        return [asdict(r) for r in requests]

    async def respond_to_request(self, request_id: str, decision: str, reason: str, decided_by: str) -> Dict[str, Any]:
        """Respond to an action request"""
        if request_id not in self.pending_requests:
            return {"success": False, "error": "Request not found"}
        
        decision_data = {
            "request_id": request_id,
            "status": decision,
            "reason": reason,
            "decided_by": decided_by,
            "timestamp": datetime.now().isoformat()
        }
        
        self.event_bus.emit('action.decision_response', decision_data)
        
        return {"success": True, "message": "Decision recorded"}

    async def get_request_details(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific request"""
        if request_id in self.pending_requests:
            return asdict(self.pending_requests[request_id])
        elif request_id in self.completed_requests:
            return asdict(self.completed_requests[request_id])
        return None

    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            "pending_requests": len(self.pending_requests),
            "completed_requests": len(self.completed_requests),
            "requests_by_type": {
                action_type.value: len([r for r in self.pending_requests.values() 
                                     if r.action_type == action_type])
                for action_type in ActionType
            },
            "requests_by_risk": {
                risk.value: len([r for r in self.pending_requests.values() 
                               if r.risk_level == risk])
                for risk in ActionRiskLevel
            }
        }