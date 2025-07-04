"""
UltraMCP Supreme Stack - Human Escalation Workflows
Advanced escalation patterns and human intervention workflows

Features:
- Multi-level escalation chains
- Role-based approval workflows
- Timeout and fallback handling
- Decision audit trails
- Learning from human decisions
- Integration with ticketing system
"""

import asyncio
import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from enum import Enum
from dataclasses import dataclass, asdict, field
from pydantic import BaseModel

# Internal imports
from core.orchestrator.eventBus import EventBus
from .action_request_adapter import ActionRequestAdapter, ActionRiskLevel, ActionType
from .ticketing_system import TicketingSystem, TicketPriority, TicketCategory


class EscalationTrigger(Enum):
    """Escalation trigger types"""
    TIMEOUT = "timeout"
    COMPLEXITY = "complexity"
    RISK_LEVEL = "risk_level"
    USER_REQUEST = "user_request"
    SAFETY_CONCERN = "safety_concern"
    LEGAL_REQUIREMENT = "legal_requirement"
    ETHICAL_CONCERN = "ethical_concern"
    TECHNICAL_LIMITATION = "technical_limitation"
    INSUFFICIENT_CONFIDENCE = "insufficient_confidence"


class EscalationLevel(Enum):
    """Escalation hierarchy levels"""
    L1_TEAM_LEAD = "l1_team_lead"
    L2_DEPARTMENT_HEAD = "l2_department_head"
    L3_DIRECTOR = "l3_director"
    L4_EXECUTIVE = "l4_executive"
    L5_BOARD = "l5_board"
    EXTERNAL_EXPERT = "external_expert"


class ApprovalWorkflowType(Enum):
    """Types of approval workflows"""
    SINGLE_APPROVER = "single_approver"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    MAJORITY_VOTE = "majority_vote"
    CONSENSUS = "consensus"
    HIERARCHICAL = "hierarchical"


@dataclass
class EscalationRule:
    """Escalation rule definition"""
    trigger: EscalationTrigger
    condition: Dict[str, Any]  # Condition parameters
    target_level: EscalationLevel
    timeout_minutes: int = 60
    auto_approve_threshold: float = 0.0
    requires_justification: bool = True
    notification_channels: List[str] = field(default_factory=lambda: ["email", "telegram"])


@dataclass
class ApprovalWorkflow:
    """Approval workflow definition"""
    id: str
    name: str
    workflow_type: ApprovalWorkflowType
    approvers: List[str]
    escalation_chain: List[EscalationLevel]
    timeout_minutes: int = 120
    auto_approve_conditions: Dict[str, Any] = field(default_factory=dict)
    parallel_approval_threshold: float = 0.5  # For majority vote
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EscalationContext:
    """Context for escalation decisions"""
    escalation_id: str
    original_request_id: str
    trigger: EscalationTrigger
    current_level: EscalationLevel
    escalation_path: List[EscalationLevel]
    created_at: datetime
    escalated_from: str
    escalated_to: str
    timeout_at: datetime
    context_data: Dict[str, Any]
    decision_history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class HumanEscalationWorkflows:
    """
    Advanced human escalation workflow manager
    
    Manages complex escalation patterns including:
    - Multi-level approval chains
    - Role-based decision routing
    - Timeout and fallback handling
    - Decision learning and optimization
    - Integration with external systems
    """
    
    def __init__(self, event_bus: EventBus, action_adapter: ActionRequestAdapter, 
                 ticketing_system: TicketingSystem):
        self.event_bus = event_bus
        self.action_adapter = action_adapter
        self.ticketing_system = ticketing_system
        self.logger = logging.getLogger(f"{__name__}.HumanEscalationWorkflows")
        
        # Active escalations
        self.active_escalations: Dict[str, EscalationContext] = {}
        self.approval_workflows: Dict[str, ApprovalWorkflow] = {}
        
        # Configuration
        self.config = {
            "max_escalation_levels": 5,
            "default_timeout_minutes": 120,
            "enable_learning": True,
            "auto_approve_threshold": 0.9,
            "parallel_decision_timeout": 60,
            "escalation_cooldown_minutes": 30
        }
        
        # Predefined escalation rules
        self.escalation_rules = self._initialize_escalation_rules()
        
        # Predefined approval workflows
        self.approval_workflows = self._initialize_approval_workflows()
        
        # Role mappings
        self.role_mappings = {
            "ai_specialist": {"level": EscalationLevel.L1_TEAM_LEAD, "expertise": ["ai", "ml", "nlp"]},
            "security_analyst": {"level": EscalationLevel.L1_TEAM_LEAD, "expertise": ["security", "compliance"]},
            "devops_engineer": {"level": EscalationLevel.L1_TEAM_LEAD, "expertise": ["infrastructure", "deployment"]},
            "team_lead": {"level": EscalationLevel.L1_TEAM_LEAD, "expertise": ["general", "team_management"]},
            "department_head": {"level": EscalationLevel.L2_DEPARTMENT_HEAD, "expertise": ["strategic", "budget"]},
            "technical_director": {"level": EscalationLevel.L3_DIRECTOR, "expertise": ["architecture", "technology"]},
            "cto": {"level": EscalationLevel.L4_EXECUTIVE, "expertise": ["technology", "strategy"]},
            "ceo": {"level": EscalationLevel.L4_EXECUTIVE, "expertise": ["business", "strategic"]},
            "external_expert": {"level": EscalationLevel.EXTERNAL_EXPERT, "expertise": ["domain_specific"]}
        }
        
        # Decision learning data
        self.decision_patterns = {}
        self.success_metrics = {}
        
        # Setup event listeners
        self._setup_event_listeners()
        
        # Start background tasks
        asyncio.create_task(self._start_background_tasks())
        
        self.logger.info("HumanEscalationWorkflows initialized")

    def _initialize_escalation_rules(self) -> List[EscalationRule]:
        """Initialize predefined escalation rules"""
        return [
            # Timeout-based escalations
            EscalationRule(
                trigger=EscalationTrigger.TIMEOUT,
                condition={"timeout_minutes": 30},
                target_level=EscalationLevel.L1_TEAM_LEAD,
                timeout_minutes=60
            ),
            EscalationRule(
                trigger=EscalationTrigger.TIMEOUT,
                condition={"timeout_minutes": 120},
                target_level=EscalationLevel.L2_DEPARTMENT_HEAD,
                timeout_minutes=90
            ),
            
            # Risk-based escalations
            EscalationRule(
                trigger=EscalationTrigger.RISK_LEVEL,
                condition={"risk_level": "high"},
                target_level=EscalationLevel.L2_DEPARTMENT_HEAD,
                timeout_minutes=60,
                requires_justification=True
            ),
            EscalationRule(
                trigger=EscalationTrigger.RISK_LEVEL,
                condition={"risk_level": "critical"},
                target_level=EscalationLevel.L3_DIRECTOR,
                timeout_minutes=30,
                requires_justification=True
            ),
            
            # Complexity-based escalations
            EscalationRule(
                trigger=EscalationTrigger.COMPLEXITY,
                condition={"complexity_score": 0.8},
                target_level=EscalationLevel.L2_DEPARTMENT_HEAD,
                timeout_minutes=90
            ),
            
            # Safety and legal escalations
            EscalationRule(
                trigger=EscalationTrigger.SAFETY_CONCERN,
                condition={},
                target_level=EscalationLevel.L3_DIRECTOR,
                timeout_minutes=15,
                requires_justification=True,
                notification_channels=["email", "telegram", "sms"]
            ),
            EscalationRule(
                trigger=EscalationTrigger.LEGAL_REQUIREMENT,
                condition={},
                target_level=EscalationLevel.EXTERNAL_EXPERT,
                timeout_minutes=240,
                requires_justification=True
            )
        ]

    def _initialize_approval_workflows(self) -> Dict[str, ApprovalWorkflow]:
        """Initialize predefined approval workflows"""
        workflows = {}
        
        # Single approver workflow
        workflows["single_approver"] = ApprovalWorkflow(
            id="single_approver",
            name="Single Approver",
            workflow_type=ApprovalWorkflowType.SINGLE_APPROVER,
            approvers=["team_lead"],
            escalation_chain=[EscalationLevel.L1_TEAM_LEAD],
            timeout_minutes=60
        )
        
        # Sequential approval workflow
        workflows["sequential_approval"] = ApprovalWorkflow(
            id="sequential_approval",
            name="Sequential Approval",
            workflow_type=ApprovalWorkflowType.SEQUENTIAL,
            approvers=["team_lead", "department_head", "director"],
            escalation_chain=[
                EscalationLevel.L1_TEAM_LEAD,
                EscalationLevel.L2_DEPARTMENT_HEAD,
                EscalationLevel.L3_DIRECTOR
            ],
            timeout_minutes=180
        )
        
        # Parallel approval workflow
        workflows["parallel_approval"] = ApprovalWorkflow(
            id="parallel_approval",
            name="Parallel Approval",
            workflow_type=ApprovalWorkflowType.PARALLEL,
            approvers=["technical_lead", "security_lead", "compliance_lead"],
            escalation_chain=[EscalationLevel.L1_TEAM_LEAD],
            timeout_minutes=120,
            parallel_approval_threshold=0.67  # 2 out of 3
        )
        
        # Majority vote workflow
        workflows["majority_vote"] = ApprovalWorkflow(
            id="majority_vote",
            name="Majority Vote",
            workflow_type=ApprovalWorkflowType.MAJORITY_VOTE,
            approvers=["engineer_1", "engineer_2", "engineer_3", "engineer_4", "engineer_5"],
            escalation_chain=[EscalationLevel.L1_TEAM_LEAD],
            timeout_minutes=90,
            parallel_approval_threshold=0.6  # 3 out of 5
        )
        
        # Hierarchical workflow
        workflows["hierarchical"] = ApprovalWorkflow(
            id="hierarchical",
            name="Hierarchical Approval",
            workflow_type=ApprovalWorkflowType.HIERARCHICAL,
            approvers=["team_lead", "department_head", "director", "cto"],
            escalation_chain=[
                EscalationLevel.L1_TEAM_LEAD,
                EscalationLevel.L2_DEPARTMENT_HEAD,
                EscalationLevel.L3_DIRECTOR,
                EscalationLevel.L4_EXECUTIVE
            ],
            timeout_minutes=300
        )
        
        return workflows

    async def trigger_escalation(self, request_id: str, trigger: EscalationTrigger, 
                                context: Dict[str, Any]) -> str:
        """Trigger an escalation workflow"""
        try:
            escalation_id = str(uuid.uuid4())
            
            # Find appropriate escalation rule
            escalation_rule = self._find_escalation_rule(trigger, context)
            if not escalation_rule:
                self.logger.warning(f"No escalation rule found for trigger {trigger}")
                return None
            
            # Determine escalation target
            escalated_to = self._determine_escalation_target(escalation_rule, context)
            
            # Create escalation context
            escalation_context = EscalationContext(
                escalation_id=escalation_id,
                original_request_id=request_id,
                trigger=trigger,
                current_level=escalation_rule.target_level,
                escalation_path=[escalation_rule.target_level],
                created_at=datetime.now(),
                escalated_from=context.get("escalated_from", "system"),
                escalated_to=escalated_to,
                timeout_at=datetime.now() + timedelta(minutes=escalation_rule.timeout_minutes),
                context_data=context
            )
            
            # Store active escalation
            self.active_escalations[escalation_id] = escalation_context
            
            # Create ticket for escalation
            ticket_id = await self._create_escalation_ticket(escalation_context, escalation_rule)
            escalation_context.metadata["ticket_id"] = ticket_id
            
            # Emit escalation event
            self.event_bus.emit('escalation.triggered', {
                'escalation_id': escalation_id,
                'request_id': request_id,
                'trigger': trigger.value,
                'escalated_to': escalated_to,
                'timeout_at': escalation_context.timeout_at.isoformat()
            })
            
            # Send notifications
            await self._send_escalation_notifications(escalation_context, escalation_rule)
            
            self.logger.info(f"Escalation {escalation_id} triggered for request {request_id}")
            return escalation_id
            
        except Exception as e:
            self.logger.error(f"Failed to trigger escalation: {str(e)}")
            raise

    async def execute_approval_workflow(self, workflow_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific approval workflow"""
        try:
            workflow = self.approval_workflows.get(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            execution_id = str(uuid.uuid4())
            
            self.logger.info(f"Starting approval workflow {workflow_id} (execution: {execution_id})")
            
            if workflow.workflow_type == ApprovalWorkflowType.SINGLE_APPROVER:
                return await self._execute_single_approver(workflow, request_data, execution_id)
            elif workflow.workflow_type == ApprovalWorkflowType.SEQUENTIAL:
                return await self._execute_sequential_approval(workflow, request_data, execution_id)
            elif workflow.workflow_type == ApprovalWorkflowType.PARALLEL:
                return await self._execute_parallel_approval(workflow, request_data, execution_id)
            elif workflow.workflow_type == ApprovalWorkflowType.MAJORITY_VOTE:
                return await self._execute_majority_vote(workflow, request_data, execution_id)
            elif workflow.workflow_type == ApprovalWorkflowType.HIERARCHICAL:
                return await self._execute_hierarchical_approval(workflow, request_data, execution_id)
            else:
                raise ValueError(f"Unsupported workflow type: {workflow.workflow_type}")
                
        except Exception as e:
            self.logger.error(f"Failed to execute approval workflow {workflow_id}: {str(e)}")
            raise

    async def _execute_single_approver(self, workflow: ApprovalWorkflow, 
                                     request_data: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute single approver workflow"""
        approver = workflow.approvers[0]
        
        # Check for auto-approval conditions
        if self._check_auto_approval(workflow, request_data):
            return {
                "status": "auto_approved",
                "execution_id": execution_id,
                "approved_by": "auto_approval_system",
                "approval_time": datetime.now().isoformat(),
                "workflow_type": workflow.workflow_type.value
            }
        
        # Request human approval
        approval_request_id = await self.action_adapter.executeAction("request_human_approval", {
            "action_type": "approval_request",
            "title": f"Approval Required: {request_data.get('title', 'Action Approval')}",
            "description": request_data.get('description', ''),
            "context": {
                "workflow_id": workflow.id,
                "execution_id": execution_id,
                "approver": approver,
                **request_data.get('context', {})
            }
        })
        
        # Wait for approval with timeout
        try:
            decision = await self.event_bus.wait_for_input({
                "event_pattern": f"approval.decision.{approval_request_id['request_id']}",
                "timeout_seconds": workflow.timeout_minutes * 60,
                "default_response": {
                    "status": "timeout",
                    "reason": "No approval received within timeout"
                }
            })
            
            return {
                "status": decision.get("status"),
                "execution_id": execution_id,
                "approved_by": approver,
                "approval_time": datetime.now().isoformat(),
                "decision_reason": decision.get("reason"),
                "workflow_type": workflow.workflow_type.value
            }
            
        except Exception as e:
            return {
                "status": "error",
                "execution_id": execution_id,
                "error": str(e),
                "workflow_type": workflow.workflow_type.value
            }

    async def _execute_sequential_approval(self, workflow: ApprovalWorkflow, 
                                         request_data: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute sequential approval workflow"""
        approvals = []
        
        for i, approver in enumerate(workflow.approvers):
            # Check if previous approvals allow skipping
            if i > 0 and self._can_skip_approval(workflow, approvals, i):
                approvals.append({
                    "approver": approver,
                    "status": "skipped",
                    "reason": "Previous approvals sufficient"
                })
                continue
            
            # Request approval from current approver
            approval_request_id = await self.action_adapter.executeAction("request_human_approval", {
                "action_type": "sequential_approval",
                "title": f"Sequential Approval ({i+1}/{len(workflow.approvers)}): {request_data.get('title', '')}",
                "description": request_data.get('description', ''),
                "context": {
                    "workflow_id": workflow.id,
                    "execution_id": execution_id,
                    "approver": approver,
                    "step": i + 1,
                    "total_steps": len(workflow.approvers),
                    "previous_approvals": approvals,
                    **request_data.get('context', {})
                }
            })
            
            # Wait for approval
            try:
                decision = await self.event_bus.wait_for_input({
                    "event_pattern": f"approval.decision.{approval_request_id['request_id']}",
                    "timeout_seconds": workflow.timeout_minutes * 60,
                    "default_response": {
                        "status": "timeout",
                        "reason": "No approval received within timeout"
                    }
                })
                
                approval = {
                    "approver": approver,
                    "status": decision.get("status"),
                    "reason": decision.get("reason"),
                    "timestamp": datetime.now().isoformat()
                }
                approvals.append(approval)
                
                # If rejected, stop the workflow
                if decision.get("status") == "rejected":
                    return {
                        "status": "rejected",
                        "execution_id": execution_id,
                        "rejected_by": approver,
                        "rejection_reason": decision.get("reason"),
                        "approvals": approvals,
                        "workflow_type": workflow.workflow_type.value
                    }
                
                # If timeout, escalate or fail
                if decision.get("status") == "timeout":
                    escalation_id = await self.trigger_escalation(
                        approval_request_id['request_id'],
                        EscalationTrigger.TIMEOUT,
                        {
                            "workflow_id": workflow.id,
                            "execution_id": execution_id,
                            "step": i + 1,
                            "approver": approver
                        }
                    )
                    
                    approval["escalation_id"] = escalation_id
                    
            except Exception as e:
                approvals.append({
                    "approver": approver,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Determine final status
        final_status = "approved" if all(a.get("status") == "approved" for a in approvals) else "failed"
        
        return {
            "status": final_status,
            "execution_id": execution_id,
            "approvals": approvals,
            "completed_at": datetime.now().isoformat(),
            "workflow_type": workflow.workflow_type.value
        }

    async def _execute_parallel_approval(self, workflow: ApprovalWorkflow, 
                                       request_data: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute parallel approval workflow"""
        approval_tasks = []
        
        # Start all approval requests in parallel
        for approver in workflow.approvers:
            task = asyncio.create_task(self._request_single_approval(
                approver, workflow, request_data, execution_id
            ))
            approval_tasks.append(task)
        
        # Wait for approvals with timeout
        try:
            approvals = await asyncio.wait_for(
                asyncio.gather(*approval_tasks, return_exceptions=True),
                timeout=workflow.timeout_minutes * 60
            )
            
            # Process results
            approval_results = []
            approved_count = 0
            
            for i, result in enumerate(approvals):
                if isinstance(result, Exception):
                    approval_results.append({
                        "approver": workflow.approvers[i],
                        "status": "error",
                        "error": str(result)
                    })
                else:
                    approval_results.append(result)
                    if result.get("status") == "approved":
                        approved_count += 1
            
            # Check if threshold met
            required_approvals = int(len(workflow.approvers) * workflow.parallel_approval_threshold)
            final_status = "approved" if approved_count >= required_approvals else "rejected"
            
            return {
                "status": final_status,
                "execution_id": execution_id,
                "approvals": approval_results,
                "approved_count": approved_count,
                "required_approvals": required_approvals,
                "threshold": workflow.parallel_approval_threshold,
                "completed_at": datetime.now().isoformat(),
                "workflow_type": workflow.workflow_type.value
            }
            
        except asyncio.TimeoutError:
            # Cancel remaining tasks
            for task in approval_tasks:
                if not task.done():
                    task.cancel()
            
            return {
                "status": "timeout",
                "execution_id": execution_id,
                "timeout_minutes": workflow.timeout_minutes,
                "workflow_type": workflow.workflow_type.value
            }

    async def _execute_majority_vote(self, workflow: ApprovalWorkflow, 
                                   request_data: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute majority vote workflow"""
        # Similar to parallel approval but with different threshold logic
        return await self._execute_parallel_approval(workflow, request_data, execution_id)

    async def _execute_hierarchical_approval(self, workflow: ApprovalWorkflow, 
                                           request_data: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute hierarchical approval workflow"""
        # Hierarchical is like sequential but with escalation at each level
        approvals = []
        
        for i, (approver, escalation_level) in enumerate(zip(workflow.approvers, workflow.escalation_chain)):
            # Request approval
            approval_request_id = await self.action_adapter.executeAction("request_human_approval", {
                "action_type": "hierarchical_approval",
                "title": f"Hierarchical Approval ({escalation_level.value}): {request_data.get('title', '')}",
                "description": request_data.get('description', ''),
                "context": {
                    "workflow_id": workflow.id,
                    "execution_id": execution_id,
                    "approver": approver,
                    "escalation_level": escalation_level.value,
                    "step": i + 1,
                    "total_steps": len(workflow.approvers),
                    **request_data.get('context', {})
                }
            })
            
            # Wait for approval with escalation
            try:
                decision = await self.event_bus.wait_for_input_with_escalation({
                    "event_pattern": f"approval.decision.{approval_request_id['request_id']}",
                    "timeout_seconds": workflow.timeout_minutes * 60 // len(workflow.approvers),
                    "enable_escalation": True,
                    "escalation_chain": workflow.approvers[i+1:] if i+1 < len(workflow.approvers) else [],
                    "escalation_data": {
                        "current_approver": approver,
                        "escalation_level": escalation_level.value
                    }
                })
                
                approval = {
                    "approver": approver,
                    "escalation_level": escalation_level.value,
                    "status": decision.get("status"),
                    "reason": decision.get("reason"),
                    "timestamp": datetime.now().isoformat()
                }
                approvals.append(approval)
                
                # For hierarchical, any approval at appropriate level is sufficient
                if decision.get("status") == "approved":
                    return {
                        "status": "approved",
                        "execution_id": execution_id,
                        "approved_by": approver,
                        "approval_level": escalation_level.value,
                        "approvals": approvals,
                        "workflow_type": workflow.workflow_type.value
                    }
                
                # If rejected at this level, continue to next level
                
            except Exception as e:
                approvals.append({
                    "approver": approver,
                    "escalation_level": escalation_level.value,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # If we reach here, no approval was obtained
        return {
            "status": "rejected",
            "execution_id": execution_id,
            "reason": "No approval obtained at any level",
            "approvals": approvals,
            "workflow_type": workflow.workflow_type.value
        }

    async def _request_single_approval(self, approver: str, workflow: ApprovalWorkflow, 
                                     request_data: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Request approval from a single approver (for parallel workflows)"""
        approval_request_id = await self.action_adapter.executeAction("request_human_approval", {
            "action_type": "parallel_approval",
            "title": f"Parallel Approval ({approver}): {request_data.get('title', '')}",
            "description": request_data.get('description', ''),
            "context": {
                "workflow_id": workflow.id,
                "execution_id": execution_id,
                "approver": approver,
                **request_data.get('context', {})
            }
        })
        
        decision = await self.event_bus.wait_for_input({
            "event_pattern": f"approval.decision.{approval_request_id['request_id']}",
            "timeout_seconds": workflow.timeout_minutes * 60,
            "default_response": {
                "status": "timeout",
                "reason": "No approval received within timeout"
            }
        })
        
        return {
            "approver": approver,
            "status": decision.get("status"),
            "reason": decision.get("reason"),
            "timestamp": datetime.now().isoformat()
        }

    # Helper methods

    def _find_escalation_rule(self, trigger: EscalationTrigger, context: Dict[str, Any]) -> Optional[EscalationRule]:
        """Find appropriate escalation rule for trigger and context"""
        for rule in self.escalation_rules:
            if rule.trigger == trigger:
                if self._matches_condition(rule.condition, context):
                    return rule
        return None

    def _matches_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if context matches escalation condition"""
        for key, value in condition.items():
            if key not in context:
                continue
            
            context_value = context[key]
            
            # Handle different comparison types
            if isinstance(value, (int, float)) and isinstance(context_value, (int, float)):
                if context_value < value:
                    return False
            elif isinstance(value, str) and isinstance(context_value, str):
                if context_value != value:
                    return False
            elif isinstance(value, list):
                if context_value not in value:
                    return False
        
        return True

    def _determine_escalation_target(self, escalation_rule: EscalationRule, context: Dict[str, Any]) -> str:
        """Determine who should handle the escalation"""
        # Find appropriate person based on escalation level and expertise
        for role, role_info in self.role_mappings.items():
            if role_info["level"] == escalation_rule.target_level:
                # Check if expertise matches if specified
                required_expertise = context.get("required_expertise")
                if required_expertise:
                    if required_expertise in role_info["expertise"]:
                        return role
                else:
                    return role
        
        # Fallback based on level
        level_fallbacks = {
            EscalationLevel.L1_TEAM_LEAD: "team_lead",
            EscalationLevel.L2_DEPARTMENT_HEAD: "department_head", 
            EscalationLevel.L3_DIRECTOR: "director",
            EscalationLevel.L4_EXECUTIVE: "cto",
            EscalationLevel.EXTERNAL_EXPERT: "external_expert"
        }
        
        return level_fallbacks.get(escalation_rule.target_level, "team_lead")

    def _check_auto_approval(self, workflow: ApprovalWorkflow, request_data: Dict[str, Any]) -> bool:
        """Check if request qualifies for auto-approval"""
        if not workflow.auto_approve_conditions:
            return False
        
        # Check confidence threshold
        confidence = request_data.get("confidence_score", 0.0)
        if confidence >= workflow.auto_approve_conditions.get("min_confidence", 1.0):
            return True
        
        # Check other auto-approval conditions
        # (Can be extended based on specific requirements)
        
        return False

    def _can_skip_approval(self, workflow: ApprovalWorkflow, approvals: List[Dict[str, Any]], 
                          current_step: int) -> bool:
        """Check if current approval step can be skipped"""
        # Logic to determine if sufficient approvals already received
        # This is workflow-specific and can be customized
        return False

    async def _create_escalation_ticket(self, escalation_context: EscalationContext, 
                                      escalation_rule: EscalationRule) -> str:
        """Create ticket for escalation"""
        ticket_data = {
            "title": f"Escalation: {escalation_context.trigger.value}",
            "description": f"Escalation triggered for request {escalation_context.original_request_id}",
            "category": "escalation",
            "priority": self._escalation_to_priority(escalation_context.current_level),
            "created_by": escalation_context.escalated_from,
            "metadata": {
                "escalation_id": escalation_context.escalation_id,
                "original_request_id": escalation_context.original_request_id,
                "trigger": escalation_context.trigger.value,
                "escalation_level": escalation_context.current_level.value,
                "timeout_at": escalation_context.timeout_at.isoformat(),
                "context_data": escalation_context.context_data
            }
        }
        
        ticket = await self.ticketing_system.create_ticket(ticket_data)
        return ticket.id

    def _escalation_to_priority(self, level: EscalationLevel) -> str:
        """Convert escalation level to ticket priority"""
        mapping = {
            EscalationLevel.L1_TEAM_LEAD: "medium",
            EscalationLevel.L2_DEPARTMENT_HEAD: "high", 
            EscalationLevel.L3_DIRECTOR: "high",
            EscalationLevel.L4_EXECUTIVE: "critical",
            EscalationLevel.L5_BOARD: "critical",
            EscalationLevel.EXTERNAL_EXPERT: "high"
        }
        return mapping.get(level, "medium")

    async def _send_escalation_notifications(self, escalation_context: EscalationContext, 
                                           escalation_rule: EscalationRule):
        """Send notifications for escalation"""
        notification_data = {
            "escalation_id": escalation_context.escalation_id,
            "trigger": escalation_context.trigger.value,
            "escalated_to": escalation_context.escalated_to,
            "timeout_at": escalation_context.timeout_at.isoformat(),
            "context": escalation_context.context_data
        }
        
        for channel in escalation_rule.notification_channels:
            self.event_bus.emit(f'notification.{channel}', {
                "type": "escalation",
                "data": notification_data
            })

    def _setup_event_listeners(self):
        """Setup event listeners"""
        # Listen for escalation responses
        self.event_bus.on('escalation.response', self._handle_escalation_response)
        
        # Listen for approval decisions
        self.event_bus.on('approval.decision.*', self._handle_approval_decision)
        
        # Listen for timeout events
        self.event_bus.on('escalation.timeout', self._handle_escalation_timeout)

    async def _start_background_tasks(self):
        """Start background monitoring tasks"""
        asyncio.create_task(self._monitor_escalation_timeouts())
        
        if self.config["enable_learning"]:
            asyncio.create_task(self._decision_learning_task())

    async def _monitor_escalation_timeouts(self):
        """Monitor for escalation timeouts"""
        while True:
            try:
                current_time = datetime.now()
                
                # Check for timed-out escalations
                timeout_escalations = []
                for escalation_id, context in self.active_escalations.items():
                    if context.timeout_at <= current_time:
                        timeout_escalations.append(escalation_id)
                
                # Handle timeouts
                for escalation_id in timeout_escalations:
                    await self._handle_escalation_timeout_internal(escalation_id)
                
                # Wait 1 minute before next check
                await asyncio.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Error in escalation timeout monitor: {str(e)}")
                await asyncio.sleep(30)

    async def _decision_learning_task(self):
        """Learn from human decisions to improve auto-approval"""
        while True:
            try:
                # Analyze recent decisions and update patterns
                # This would implement ML-based learning from human decisions
                await asyncio.sleep(3600)  # Run hourly
                
            except Exception as e:
                self.logger.error(f"Error in decision learning task: {str(e)}")
                await asyncio.sleep(1800)

    async def _handle_escalation_response(self, event_data):
        """Handle escalation responses"""
        escalation_id = event_data.get("escalation_id")
        if escalation_id in self.active_escalations:
            # Process escalation response
            self.logger.info(f"Received response for escalation {escalation_id}")

    async def _handle_approval_decision(self, event_data):
        """Handle approval decisions"""
        # Process approval decisions for workflow tracking
        self.logger.info(f"Approval decision received: {event_data}")

    async def _handle_escalation_timeout_internal(self, escalation_id: str):
        """Handle internal escalation timeout"""
        if escalation_id not in self.active_escalations:
            return
        
        context = self.active_escalations[escalation_id]
        
        # Emit timeout event
        self.event_bus.emit('escalation.timeout', {
            'escalation_id': escalation_id,
            'original_request_id': context.original_request_id,
            'escalated_to': context.escalated_to
        })
        
        # Remove from active escalations
        del self.active_escalations[escalation_id]
        
        self.logger.warning(f"Escalation {escalation_id} timed out")

    # Public API methods

    async def get_active_escalations(self) -> List[Dict[str, Any]]:
        """Get list of active escalations"""
        return [asdict(context) for context in self.active_escalations.values()]

    async def respond_to_escalation(self, escalation_id: str, response: Dict[str, Any]) -> bool:
        """Respond to an escalation"""
        if escalation_id not in self.active_escalations:
            return False
        
        context = self.active_escalations[escalation_id]
        context.decision_history.append({
            "timestamp": datetime.now().isoformat(),
            "response": response
        })
        
        # Emit response event
        self.event_bus.emit('escalation.response', {
            'escalation_id': escalation_id,
            'response': response
        })
        
        return True

    async def get_escalation_statistics(self) -> Dict[str, Any]:
        """Get escalation statistics"""
        return {
            "active_escalations": len(self.active_escalations),
            "escalation_triggers": {trigger.value: 0 for trigger in EscalationTrigger},
            "escalation_levels": {level.value: 0 for level in EscalationLevel},
            "average_resolution_time": 0,  # Would calculate from historical data
            "escalation_success_rate": 0   # Would calculate from historical data
        }