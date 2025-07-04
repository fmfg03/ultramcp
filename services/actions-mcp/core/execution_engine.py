"""
Execution Engine - Handles secure execution of external actions
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid

from .security_manager import SecurityManager
from .audit_logger import AuditLogger

logger = logging.getLogger(__name__)

class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass
class ExecutionContext:
    """Context for action execution"""
    execution_id: str
    action_name: str
    user_id: Optional[str]
    input_data: Dict[str, Any]
    security_level: str
    timeout: int
    retry_count: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_attempts: int = 0

class ExecutionEngine:
    """Secure execution engine for external actions"""
    
    def __init__(self, security_manager: SecurityManager, audit_logger: AuditLogger):
        self.security_manager = security_manager
        self.audit_logger = audit_logger
        self.active_executions: Dict[str, ExecutionContext] = {}
        self.execution_history: List[ExecutionContext] = []
        self.adapters: Dict[str, Any] = {}
        self.rate_limits: Dict[str, List[datetime]] = {}
        
    async def initialize(self):
        """Initialize execution engine and load adapters"""
        try:
            await self._load_adapters()
            logger.info("✅ Execution engine initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize execution engine: {e}")
            raise
    
    async def _load_adapters(self):
        """Load action adapters"""
        try:
            # Import adapters dynamically
            from ..adapters.escalation_adapter import EscalationAdapter
            from ..adapters.email_adapter import EmailAdapter
            from ..adapters.slack_adapter import SlackAdapter
            from ..adapters.workflow_adapter import WorkflowAdapter
            from ..adapters.jira_adapter import JiraAdapter
            from ..adapters.github_adapter import GitHubAdapter
            from ..adapters.documentation_adapter import DocumentationAdapter
            from ..adapters.monitoring_adapter import MonitoringAdapter
            from ..adapters.security_adapter import SecurityAdapter
            
            self.adapters = {
                "EscalationAdapter": EscalationAdapter(),
                "EmailAdapter": EmailAdapter(),
                "SlackAdapter": SlackAdapter(),
                "WorkflowAdapter": WorkflowAdapter(),
                "JiraAdapter": JiraAdapter(),
                "GitHubAdapter": GitHubAdapter(),
                "DocumentationAdapter": DocumentationAdapter(),
                "MonitoringAdapter": MonitoringAdapter(),
                "SecurityAdapter": SecurityAdapter()
            }
            
            # Initialize adapters
            for name, adapter in self.adapters.items():
                await adapter.initialize()
                logger.info(f"✅ Loaded adapter: {name}")
                
        except Exception as e:
            logger.error(f"❌ Failed to load adapters: {e}")
            # Create mock adapters for development
            await self._create_mock_adapters()
    
    async def _create_mock_adapters(self):
        """Create mock adapters for development/testing"""
        from ..adapters.mock_adapter import MockAdapter
        
        adapter_names = [
            "EscalationAdapter", "EmailAdapter", "SlackAdapter", "WorkflowAdapter",
            "JiraAdapter", "GitHubAdapter", "DocumentationAdapter", 
            "MonitoringAdapter", "SecurityAdapter"
        ]
        
        for name in adapter_names:
            self.adapters[name] = MockAdapter(name)
            await self.adapters[name].initialize()
        
        logger.info("✅ Mock adapters loaded for development")
    
    async def execute_action(
        self, 
        action_name: str, 
        input_data: Dict[str, Any],
        user_id: Optional[str] = None,
        action_definition = None
    ) -> str:
        """Execute an external action"""
        
        # Create execution context
        execution_id = str(uuid.uuid4())
        context = ExecutionContext(
            execution_id=execution_id,
            action_name=action_name,
            user_id=user_id,
            input_data=input_data,
            security_level=action_definition.security_level if action_definition else "standard",
            timeout=action_definition.timeout if action_definition else 30,
            retry_count=action_definition.retry_count if action_definition else 3,
            created_at=datetime.utcnow()
        )
        
        self.active_executions[execution_id] = context
        
        try:
            # Security checks
            await self._validate_security(context, action_definition)
            
            # Rate limiting
            await self._check_rate_limit(action_name, action_definition)
            
            # Input validation
            await self._validate_input(input_data, action_definition)
            
            # Audit log start
            await self.audit_logger.log_action_start(context)
            
            # Execute action
            context.status = ExecutionStatus.RUNNING
            context.started_at = datetime.utcnow()
            
            result = await self._execute_with_timeout(context, action_definition)
            
            context.status = ExecutionStatus.COMPLETED
            context.completed_at = datetime.utcnow()
            context.result = result
            
            # Audit log completion
            await self.audit_logger.log_action_completion(context)
            
            return execution_id
            
        except Exception as e:
            context.status = ExecutionStatus.FAILED
            context.error = str(e)
            context.completed_at = datetime.utcnow()
            
            # Audit log error
            await self.audit_logger.log_action_error(context, e)
            
            # Retry logic
            if context.retry_attempts < context.retry_count:
                logger.info(f"Retrying action {action_name}, attempt {context.retry_attempts + 1}")
                context.retry_attempts += 1
                context.status = ExecutionStatus.PENDING
                await asyncio.sleep(2 ** context.retry_attempts)  # Exponential backoff
                return await self.execute_action(action_name, input_data, user_id, action_definition)
            
            raise
        finally:
            # Move to history
            if execution_id in self.active_executions:
                self.execution_history.append(self.active_executions[execution_id])
                del self.active_executions[execution_id]
    
    async def _validate_security(self, context: ExecutionContext, action_definition):
        """Validate security requirements for action execution"""
        
        # Check user permissions
        if context.user_id:
            has_permission = await self.security_manager.check_permission(
                context.user_id, 
                context.action_name, 
                context.security_level
            )
            if not has_permission:
                raise PermissionError(f"User {context.user_id} lacks permission for {context.action_name}")
        
        # Check if approval is required
        if action_definition and action_definition.requires_approval:
            approval_status = await self.security_manager.check_approval_status(
                context.action_name,
                context.input_data
            )
            if not approval_status:
                raise PermissionError(f"Action {context.action_name} requires approval")
        
        # Additional security validations
        await self.security_manager.validate_action_security(context)
    
    async def _check_rate_limit(self, action_name: str, action_definition):
        """Check rate limiting for action"""
        if not action_definition:
            return
        
        now = datetime.utcnow()
        rate_limit = action_definition.rate_limit
        
        # Clean old entries
        if action_name in self.rate_limits:
            self.rate_limits[action_name] = [
                timestamp for timestamp in self.rate_limits[action_name]
                if now - timestamp < timedelta(minutes=1)
            ]
        else:
            self.rate_limits[action_name] = []
        
        # Check limit
        if len(self.rate_limits[action_name]) >= rate_limit:
            raise Exception(f"Rate limit exceeded for {action_name}: {rate_limit} requests per minute")
        
        # Add current request
        self.rate_limits[action_name].append(now)
    
    async def _validate_input(self, input_data: Dict[str, Any], action_definition):
        """Validate input data against schema"""
        if not action_definition:
            return
        
        # TODO: Implement JSON schema validation
        # For now, basic validation
        schema = action_definition.input_schema
        required_fields = schema.get("required", [])
        
        for field in required_fields:
            if field not in input_data:
                raise ValueError(f"Required field '{field}' missing from input")
    
    async def _execute_with_timeout(self, context: ExecutionContext, action_definition) -> Dict[str, Any]:
        """Execute action with timeout"""
        
        adapter_class = action_definition.adapter_class if action_definition else "MockAdapter"
        adapter = self.adapters.get(adapter_class)
        
        if not adapter:
            raise Exception(f"Adapter {adapter_class} not found")
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                adapter.execute(context.action_name, context.input_data),
                timeout=context.timeout
            )
            return result
            
        except asyncio.TimeoutError:
            context.status = ExecutionStatus.TIMEOUT
            raise Exception(f"Action {context.action_name} timed out after {context.timeout} seconds")
    
    async def get_execution_status(self, execution_id: str) -> Optional[ExecutionContext]:
        """Get status of execution"""
        
        # Check active executions
        if execution_id in self.active_executions:
            return self.active_executions[execution_id]
        
        # Check history
        for execution in self.execution_history:
            if execution.execution_id == execution_id:
                return execution
        
        return None
    
    async def cancel_execution(self, execution_id: str, user_id: Optional[str] = None) -> bool:
        """Cancel running execution"""
        
        if execution_id not in self.active_executions:
            return False
        
        context = self.active_executions[execution_id]
        
        # Security check for cancellation
        if user_id and context.user_id != user_id:
            can_cancel = await self.security_manager.check_permission(
                user_id, "cancel_execution", "elevated"
            )
            if not can_cancel:
                raise PermissionError("Insufficient permissions to cancel execution")
        
        context.status = ExecutionStatus.CANCELLED
        context.completed_at = datetime.utcnow()
        
        # Audit log cancellation
        await self.audit_logger.log_action_cancellation(context, user_id)
        
        return True
    
    async def get_active_executions(self) -> List[ExecutionContext]:
        """Get all active executions"""
        return list(self.active_executions.values())
    
    async def get_execution_history(self, limit: int = 100) -> List[ExecutionContext]:
        """Get execution history"""
        return self.execution_history[-limit:]
    
    async def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        
        total_executions = len(self.execution_history)
        successful_executions = len([e for e in self.execution_history if e.status == ExecutionStatus.COMPLETED])
        failed_executions = len([e for e in self.execution_history if e.status == ExecutionStatus.FAILED])
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate": (successful_executions / total_executions * 100) if total_executions > 0 else 0,
            "active_executions": len(self.active_executions),
            "average_execution_time": self._calculate_average_execution_time(),
            "most_used_actions": self._get_most_used_actions()
        }
    
    def _calculate_average_execution_time(self) -> float:
        """Calculate average execution time"""
        completed_executions = [
            e for e in self.execution_history 
            if e.status == ExecutionStatus.COMPLETED and e.started_at and e.completed_at
        ]
        
        if not completed_executions:
            return 0.0
        
        total_time = sum([
            (e.completed_at - e.started_at).total_seconds()
            for e in completed_executions
        ])
        
        return total_time / len(completed_executions)
    
    def _get_most_used_actions(self) -> List[Dict[str, Any]]:
        """Get most frequently used actions"""
        action_counts = {}
        for execution in self.execution_history:
            action_counts[execution.action_name] = action_counts.get(execution.action_name, 0) + 1
        
        sorted_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"action": action, "count": count} for action, count in sorted_actions[:10]]
    
    async def cleanup(self):
        """Cleanup execution engine"""
        # Cancel active executions
        for execution_id in list(self.active_executions.keys()):
            await self.cancel_execution(execution_id)
        
        # Cleanup adapters
        for adapter in self.adapters.values():
            if hasattr(adapter, 'cleanup'):
                await adapter.cleanup()
        
        logger.info("✅ Execution engine cleaned up")