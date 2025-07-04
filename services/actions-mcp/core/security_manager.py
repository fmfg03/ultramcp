"""
Security Manager - Handles authentication, authorization, and security controls
"""

import logging
import hashlib
import os
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SecurityPolicy:
    """Security policy definition"""
    action_name: str
    required_role: str
    security_level: str
    ip_whitelist: Optional[List[str]] = None
    time_restrictions: Optional[Dict[str, Any]] = None
    approval_required: bool = False
    max_executions_per_hour: int = 100

@dataclass
class UserPermission:
    """User permission definition"""
    user_id: str
    roles: Set[str]
    security_clearance: str
    restrictions: Dict[str, Any]
    expires_at: Optional[datetime] = None

class SecurityManager:
    """Manages security controls for action execution"""
    
    def __init__(self):
        self.security_policies: Dict[str, SecurityPolicy] = {}
        self.user_permissions: Dict[str, UserPermission] = {}
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
        self.security_events: List[Dict[str, Any]] = []
        self.blocked_ips: Set[str] = set()
        self.rate_limit_violations: Dict[str, List[datetime]] = {}
        
    async def initialize(self):
        """Initialize security manager"""
        try:
            await self._load_security_policies()
            await self._load_user_permissions()
            await self._load_security_config()
            logger.info("✅ Security manager initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize security manager: {e}")
            raise
    
    async def _load_security_policies(self):
        """Load security policies for actions"""
        
        # Default security policies
        default_policies = {
            "escalate_to_human": SecurityPolicy(
                action_name="escalate_to_human",
                required_role="user",
                security_level="elevated",
                approval_required=False,
                max_executions_per_hour=10
            ),
            "request_approval": SecurityPolicy(
                action_name="request_approval",
                required_role="user",
                security_level="elevated",
                approval_required=False,
                max_executions_per_hour=5
            ),
            "send_email": SecurityPolicy(
                action_name="send_email",
                required_role="user",
                security_level="standard",
                approval_required=False,
                max_executions_per_hour=50
            ),
            "send_slack_message": SecurityPolicy(
                action_name="send_slack_message",
                required_role="user",
                security_level="standard",
                approval_required=False,
                max_executions_per_hour=100
            ),
            "trigger_workflow": SecurityPolicy(
                action_name="trigger_workflow",
                required_role="developer",
                security_level="elevated",
                approval_required=True,
                max_executions_per_hour=20
            ),
            "stop_workflow": SecurityPolicy(
                action_name="stop_workflow",
                required_role="admin",
                security_level="elevated",
                approval_required=True,
                max_executions_per_hour=10
            ),
            "create_jira_ticket": SecurityPolicy(
                action_name="create_jira_ticket",
                required_role="user",
                security_level="standard",
                approval_required=False,
                max_executions_per_hour=30
            ),
            "create_github_issue": SecurityPolicy(
                action_name="create_github_issue",
                required_role="developer",
                security_level="standard",
                approval_required=False,
                max_executions_per_hour=25
            ),
            "update_documentation": SecurityPolicy(
                action_name="update_documentation",
                required_role="developer",
                security_level="elevated",
                approval_required=False,
                max_executions_per_hour=15
            ),
            "create_alert": SecurityPolicy(
                action_name="create_alert",
                required_role="admin",
                security_level="elevated",
                approval_required=True,
                max_executions_per_hour=10
            ),
            "trigger_security_scan": SecurityPolicy(
                action_name="trigger_security_scan",
                required_role="security_admin",
                security_level="admin",
                approval_required=True,
                max_executions_per_hour=5
            )
        }
        
        self.security_policies.update(default_policies)
        logger.info(f"✅ Loaded {len(self.security_policies)} security policies")
    
    async def _load_user_permissions(self):
        """Load user permissions"""
        
        # Default user permissions for development
        default_users = {
            "system": UserPermission(
                user_id="system",
                roles={"system", "admin", "security_admin", "developer", "user"},
                security_clearance="admin",
                restrictions={}
            ),
            "admin": UserPermission(
                user_id="admin",
                roles={"admin", "developer", "user"},
                security_clearance="elevated",
                restrictions={}
            ),
            "developer": UserPermission(
                user_id="developer",
                roles={"developer", "user"},
                security_clearance="elevated",
                restrictions={}
            ),
            "user": UserPermission(
                user_id="user",
                roles={"user"},
                security_clearance="standard",
                restrictions={}
            )
        }
        
        self.user_permissions.update(default_users)
        logger.info(f"✅ Loaded {len(self.user_permissions)} user permissions")
    
    async def _load_security_config(self):
        """Load security configuration"""
        
        # Load from environment variables
        self.security_config = {
            "encryption_key": os.getenv("ACTIONS_ENCRYPTION_KEY", "default-dev-key"),
            "session_timeout": int(os.getenv("ACTIONS_SESSION_TIMEOUT", "3600")),
            "max_failed_attempts": int(os.getenv("ACTIONS_MAX_FAILED_ATTEMPTS", "5")),
            "ip_whitelist_enabled": os.getenv("ACTIONS_IP_WHITELIST_ENABLED", "false").lower() == "true",
            "audit_all_actions": os.getenv("ACTIONS_AUDIT_ALL", "true").lower() == "true",
            "require_mfa": os.getenv("ACTIONS_REQUIRE_MFA", "false").lower() == "true"
        }
        
        logger.info("✅ Security configuration loaded")
    
    async def check_permission(self, user_id: str, action_name: str, security_level: str) -> bool:
        """Check if user has permission to execute action"""
        
        try:
            # Get user permissions
            user_permission = self.user_permissions.get(user_id)
            if not user_permission:
                logger.warning(f"🔒 User {user_id} not found")
                return False
            
            # Check if permission expired
            if user_permission.expires_at and user_permission.expires_at < datetime.utcnow():
                logger.warning(f"🔒 User {user_id} permission expired")
                return False
            
            # Get security policy
            policy = self.security_policies.get(action_name)
            if not policy:
                logger.warning(f"🔒 No security policy found for {action_name}")
                return False
            
            # Check role requirement
            if policy.required_role not in user_permission.roles:
                logger.warning(f"🔒 User {user_id} lacks required role {policy.required_role} for {action_name}")
                return False
            
            # Check security clearance
            clearance_levels = {"standard": 0, "elevated": 1, "admin": 2}
            required_level = clearance_levels.get(security_level, 0)
            user_level = clearance_levels.get(user_permission.security_clearance, 0)
            
            if user_level < required_level:
                logger.warning(f"🔒 User {user_id} lacks security clearance for {action_name}")
                return False
            
            # Check rate limiting
            if not await self._check_user_rate_limit(user_id, action_name, policy):
                logger.warning(f"🔒 User {user_id} exceeded rate limit for {action_name}")
                return False
            
            # Log security event
            await self._log_security_event("permission_check", {
                "user_id": user_id,
                "action_name": action_name,
                "result": "allowed"
            })
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Permission check failed: {e}")
            await self._log_security_event("permission_error", {
                "user_id": user_id,
                "action_name": action_name,
                "error": str(e)
            })
            return False
    
    async def _check_user_rate_limit(self, user_id: str, action_name: str, policy: SecurityPolicy) -> bool:
        """Check user-specific rate limiting"""
        
        rate_key = f"{user_id}:{action_name}"
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        
        # Clean old entries
        if rate_key in self.rate_limit_violations:
            self.rate_limit_violations[rate_key] = [
                timestamp for timestamp in self.rate_limit_violations[rate_key]
                if timestamp > hour_ago
            ]
        else:
            self.rate_limit_violations[rate_key] = []
        
        # Check limit
        current_count = len(self.rate_limit_violations[rate_key])
        if current_count >= policy.max_executions_per_hour:
            return False
        
        # Add current attempt
        self.rate_limit_violations[rate_key].append(now)
        return True
    
    async def check_approval_status(self, action_name: str, input_data: Dict[str, Any]) -> bool:
        """Check if action has required approval"""
        
        # Generate approval key based on action and critical parameters
        approval_key = self._generate_approval_key(action_name, input_data)
        
        # Check if approval exists and is valid
        if approval_key in self.pending_approvals:
            approval = self.pending_approvals[approval_key]
            if approval["status"] == "approved" and approval["expires_at"] > datetime.utcnow():
                return True
        
        return False
    
    def _generate_approval_key(self, action_name: str, input_data: Dict[str, Any]) -> str:
        """Generate unique approval key"""
        
        # Create deterministic key based on action and critical parameters
        key_data = f"{action_name}:{str(sorted(input_data.items()))}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]
    
    async def request_approval(self, action_name: str, input_data: Dict[str, Any], 
                             requester_id: str, approvers: List[str]) -> str:
        """Request approval for action execution"""
        
        approval_key = self._generate_approval_key(action_name, input_data)
        
        approval_request = {
            "approval_id": approval_key,
            "action_name": action_name,
            "input_data": input_data,
            "requester_id": requester_id,
            "approvers": approvers,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24),
            "approvals_received": [],
            "approvals_required": len(approvers)
        }
        
        self.pending_approvals[approval_key] = approval_request
        
        # Log approval request
        await self._log_security_event("approval_requested", {
            "approval_id": approval_key,
            "action_name": action_name,
            "requester_id": requester_id,
            "approvers": approvers
        })
        
        return approval_key
    
    async def grant_approval(self, approval_id: str, approver_id: str) -> bool:
        """Grant approval for action"""
        
        if approval_id not in self.pending_approvals:
            return False
        
        approval = self.pending_approvals[approval_id]
        
        # Check if approver is authorized
        if approver_id not in approval["approvers"]:
            return False
        
        # Check if already approved by this user
        if approver_id in approval["approvals_received"]:
            return False
        
        # Add approval
        approval["approvals_received"].append(approver_id)
        
        # Check if all approvals received
        if len(approval["approvals_received"]) >= approval["approvals_required"]:
            approval["status"] = "approved"
            approval["approved_at"] = datetime.utcnow()
        
        # Log approval
        await self._log_security_event("approval_granted", {
            "approval_id": approval_id,
            "approver_id": approver_id,
            "status": approval["status"]
        })
        
        return True
    
    async def validate_action_security(self, execution_context) -> bool:
        """Validate security requirements for action execution"""
        
        # IP whitelist check
        if self.security_config.get("ip_whitelist_enabled"):
            # TODO: Implement IP validation from request context
            pass
        
        # Time-based restrictions
        policy = self.security_policies.get(execution_context.action_name)
        if policy and policy.time_restrictions:
            current_hour = datetime.utcnow().hour
            allowed_hours = policy.time_restrictions.get("allowed_hours", list(range(24)))
            if current_hour not in allowed_hours:
                raise PermissionError(f"Action {execution_context.action_name} not allowed at this time")
        
        # Input sanitization
        await self._sanitize_input_data(execution_context.input_data)
        
        return True
    
    async def _sanitize_input_data(self, input_data: Dict[str, Any]):
        """Sanitize input data for security"""
        
        # Check for potentially dangerous patterns
        dangerous_patterns = [
            "eval(",
            "exec(",
            "__import__",
            "subprocess",
            "<script",
            "javascript:",
            "data:text/html"
        ]
        
        def check_value(value):
            if isinstance(value, str):
                for pattern in dangerous_patterns:
                    if pattern.lower() in value.lower():
                        raise ValueError(f"Potentially dangerous input detected: {pattern}")
            elif isinstance(value, dict):
                for v in value.values():
                    check_value(v)
            elif isinstance(value, list):
                for v in value:
                    check_value(v)
        
        check_value(input_data)
    
    async def _log_security_event(self, event_type: str, data: Dict[str, Any]):
        """Log security event"""
        
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "data": data
        }
        
        self.security_events.append(event)
        
        # Keep only last 1000 events
        if len(self.security_events) > 1000:
            self.security_events = self.security_events[-1000:]
        
        logger.info(f"🔒 Security event: {event_type}")
    
    async def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics"""
        
        total_events = len(self.security_events)
        recent_events = [
            e for e in self.security_events 
            if datetime.fromisoformat(e["timestamp"]) > datetime.utcnow() - timedelta(hours=24)
        ]
        
        return {
            "total_security_events": total_events,
            "recent_events_24h": len(recent_events),
            "pending_approvals": len(self.pending_approvals),
            "blocked_ips": len(self.blocked_ips),
            "active_users": len(self.user_permissions),
            "security_policies": len(self.security_policies),
            "rate_limit_violations": len(self.rate_limit_violations)
        }
    
    async def get_pending_approvals(self, user_id: str) -> List[Dict[str, Any]]:
        """Get pending approvals for user"""
        
        user_approvals = []
        for approval in self.pending_approvals.values():
            if user_id in approval["approvers"] and approval["status"] == "pending":
                user_approvals.append({
                    "approval_id": approval["approval_id"],
                    "action_name": approval["action_name"],
                    "requester_id": approval["requester_id"],
                    "created_at": approval["created_at"].isoformat(),
                    "expires_at": approval["expires_at"].isoformat()
                })
        
        return user_approvals
    
    async def cleanup(self):
        """Cleanup security manager"""
        
        # Clean expired approvals
        now = datetime.utcnow()
        expired_approvals = [
            approval_id for approval_id, approval in self.pending_approvals.items()
            if approval["expires_at"] < now
        ]
        
        for approval_id in expired_approvals:
            del self.pending_approvals[approval_id]
        
        logger.info(f"✅ Security manager cleaned up, removed {len(expired_approvals)} expired approvals")