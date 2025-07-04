"""
Audit Logger - Comprehensive logging and auditing for action execution
"""

import logging
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class AuditLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class AuditEvent:
    """Audit event record"""
    event_id: str
    timestamp: datetime
    event_type: str
    level: AuditLevel
    user_id: Optional[str]
    action_name: Optional[str]
    execution_id: Optional[str]
    data: Dict[str, Any]
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None

class AuditLogger:
    """Comprehensive audit logging system"""
    
    def __init__(self):
        self.audit_events: List[AuditEvent] = []
        self.audit_file_path = os.getenv("AUDIT_LOG_PATH", "/app/data/audit.log")
        self.max_events_in_memory = int(os.getenv("MAX_AUDIT_EVENTS", "10000"))
        self.log_to_file = os.getenv("AUDIT_LOG_TO_FILE", "true").lower() == "true"
        self.log_to_external = os.getenv("AUDIT_LOG_EXTERNAL", "false").lower() == "true"
        
    async def initialize(self):
        """Initialize audit logger"""
        try:
            # Create audit log directory if it doesn't exist
            os.makedirs(os.path.dirname(self.audit_file_path), exist_ok=True)
            
            # Test file writing
            if self.log_to_file:
                await self._test_file_logging()
            
            logger.info("✅ Audit logger initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize audit logger: {e}")
            raise
    
    async def _test_file_logging(self):
        """Test if we can write to audit log file"""
        try:
            test_event = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": "audit_logger_test",
                "message": "Audit logger initialization test"
            }
            
            with open(self.audit_file_path, 'a') as f:
                f.write(json.dumps(test_event) + '\n')
                
        except Exception as e:
            logger.warning(f"⚠️ Cannot write to audit log file: {e}")
            self.log_to_file = False
    
    async def log_action_start(self, execution_context) -> str:
        """Log action execution start"""
        
        event_data = {
            "execution_id": execution_context.execution_id,
            "action_name": execution_context.action_name,
            "user_id": execution_context.user_id,
            "input_data": execution_context.input_data,
            "security_level": execution_context.security_level,
            "timeout": execution_context.timeout,
            "phase": "start"
        }
        
        return await self._log_event(
            event_type="action_execution_start",
            level=AuditLevel.INFO,
            user_id=execution_context.user_id,
            action_name=execution_context.action_name,
            execution_id=execution_context.execution_id,
            data=event_data
        )
    
    async def log_action_completion(self, execution_context) -> str:
        """Log action execution completion"""
        
        execution_time = None
        if execution_context.started_at and execution_context.completed_at:
            execution_time = (execution_context.completed_at - execution_context.started_at).total_seconds()
        
        event_data = {
            "execution_id": execution_context.execution_id,
            "action_name": execution_context.action_name,
            "user_id": execution_context.user_id,
            "status": execution_context.status.value,
            "execution_time": execution_time,
            "retry_attempts": execution_context.retry_attempts,
            "result_summary": self._summarize_result(execution_context.result),
            "phase": "completion"
        }
        
        return await self._log_event(
            event_type="action_execution_completed",
            level=AuditLevel.INFO,
            user_id=execution_context.user_id,
            action_name=execution_context.action_name,
            execution_id=execution_context.execution_id,
            data=event_data
        )
    
    async def log_action_error(self, execution_context, error: Exception) -> str:
        """Log action execution error"""
        
        event_data = {
            "execution_id": execution_context.execution_id,
            "action_name": execution_context.action_name,
            "user_id": execution_context.user_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "status": execution_context.status.value,
            "retry_attempts": execution_context.retry_attempts,
            "phase": "error"
        }
        
        return await self._log_event(
            event_type="action_execution_error",
            level=AuditLevel.ERROR,
            user_id=execution_context.user_id,
            action_name=execution_context.action_name,
            execution_id=execution_context.execution_id,
            data=event_data
        )
    
    async def log_action_cancellation(self, execution_context, cancelled_by: Optional[str]) -> str:
        """Log action execution cancellation"""
        
        event_data = {
            "execution_id": execution_context.execution_id,
            "action_name": execution_context.action_name,
            "user_id": execution_context.user_id,
            "cancelled_by": cancelled_by,
            "cancellation_reason": "user_request",
            "status": execution_context.status.value,
            "phase": "cancellation"
        }
        
        return await self._log_event(
            event_type="action_execution_cancelled",
            level=AuditLevel.WARNING,
            user_id=execution_context.user_id,
            action_name=execution_context.action_name,
            execution_id=execution_context.execution_id,
            data=event_data
        )
    
    async def log_security_event(self, event_type: str, data: Dict[str, Any], 
                                user_id: Optional[str] = None, level: AuditLevel = AuditLevel.WARNING) -> str:
        """Log security-related event"""
        
        return await self._log_event(
            event_type=f"security_{event_type}",
            level=level,
            user_id=user_id,
            data=data
        )
    
    async def log_permission_denied(self, user_id: str, action_name: str, reason: str) -> str:
        """Log permission denied event"""
        
        event_data = {
            "user_id": user_id,
            "action_name": action_name,
            "denial_reason": reason,
            "attempted_at": datetime.utcnow().isoformat()
        }
        
        return await self._log_event(
            event_type="permission_denied",
            level=AuditLevel.WARNING,
            user_id=user_id,
            action_name=action_name,
            data=event_data
        )
    
    async def log_approval_event(self, approval_type: str, approval_data: Dict[str, Any], 
                                user_id: Optional[str] = None) -> str:
        """Log approval-related event"""
        
        return await self._log_event(
            event_type=f"approval_{approval_type}",
            level=AuditLevel.INFO,
            user_id=user_id,
            data=approval_data
        )
    
    async def log_system_event(self, event_type: str, data: Dict[str, Any], 
                              level: AuditLevel = AuditLevel.INFO) -> str:
        """Log system-level event"""
        
        return await self._log_event(
            event_type=f"system_{event_type}",
            level=level,
            user_id="system",
            data=data
        )
    
    async def log_error(self, action: str, error: str, status_code: int, path: str) -> str:
        """Log general error event"""
        
        event_data = {
            "action": action,
            "error": error,
            "status_code": status_code,
            "path": path
        }
        
        return await self._log_event(
            event_type="general_error",
            level=AuditLevel.ERROR,
            data=event_data
        )
    
    async def _log_event(self, event_type: str, level: AuditLevel, data: Dict[str, Any],
                        user_id: Optional[str] = None, action_name: Optional[str] = None,
                        execution_id: Optional[str] = None) -> str:
        """Internal method to log audit event"""
        
        # Generate event ID
        event_id = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{len(self.audit_events):06d}"
        
        # Create audit event
        audit_event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.utcnow(),
            event_type=event_type,
            level=level,
            user_id=user_id,
            action_name=action_name,
            execution_id=execution_id,
            data=data
        )
        
        # Add to in-memory store
        self.audit_events.append(audit_event)
        
        # Manage memory usage
        if len(self.audit_events) > self.max_events_in_memory:
            # Remove oldest 20% of events
            remove_count = int(self.max_events_in_memory * 0.2)
            self.audit_events = self.audit_events[remove_count:]
        
        # Log to file
        if self.log_to_file:
            await self._write_to_file(audit_event)
        
        # Log to external system
        if self.log_to_external:
            await self._send_to_external_system(audit_event)
        
        # Log critical events to application logger
        if level in [AuditLevel.ERROR, AuditLevel.CRITICAL]:
            logger.error(f"🔍 AUDIT {level.value.upper()}: {event_type} - {data}")
        elif level == AuditLevel.WARNING:
            logger.warning(f"🔍 AUDIT {level.value.upper()}: {event_type}")
        else:
            logger.info(f"🔍 AUDIT: {event_type}")
        
        return event_id
    
    async def _write_to_file(self, audit_event: AuditEvent):
        """Write audit event to file"""
        try:
            event_dict = asdict(audit_event)
            event_dict['timestamp'] = audit_event.timestamp.isoformat()
            event_dict['level'] = audit_event.level.value
            
            with open(self.audit_file_path, 'a') as f:
                f.write(json.dumps(event_dict) + '\n')
                
        except Exception as e:
            logger.error(f"❌ Failed to write audit event to file: {e}")
    
    async def _send_to_external_system(self, audit_event: AuditEvent):
        """Send audit event to external logging system"""
        try:
            # TODO: Implement external logging (e.g., Splunk, ELK, CloudWatch)
            # For now, just log that we would send it
            logger.debug(f"📤 Would send audit event {audit_event.event_id} to external system")
            
        except Exception as e:
            logger.error(f"❌ Failed to send audit event to external system: {e}")
    
    def _summarize_result(self, result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary of action result for auditing"""
        if not result:
            return {"status": "no_result"}
        
        # Create safe summary without sensitive data
        summary = {
            "has_result": True,
            "result_keys": list(result.keys()) if isinstance(result, dict) else ["non_dict_result"],
            "result_size": len(str(result))
        }
        
        # Add specific safe fields if they exist
        safe_fields = ["status", "id", "url", "count", "success", "created"]
        for field in safe_fields:
            if isinstance(result, dict) and field in result:
                summary[field] = result[field]
        
        return summary
    
    async def get_audit_events(self, 
                              start_time: Optional[datetime] = None,
                              end_time: Optional[datetime] = None,
                              event_type: Optional[str] = None,
                              user_id: Optional[str] = None,
                              action_name: Optional[str] = None,
                              level: Optional[AuditLevel] = None,
                              limit: int = 100) -> List[AuditEvent]:
        """Get audit events with filtering"""
        
        filtered_events = []
        
        for event in self.audit_events:
            # Apply filters
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue
            if event_type and event.event_type != event_type:
                continue
            if user_id and event.user_id != user_id:
                continue
            if action_name and event.action_name != action_name:
                continue
            if level and event.level != level:
                continue
            
            filtered_events.append(event)
        
        # Sort by timestamp (newest first) and limit
        filtered_events.sort(key=lambda x: x.timestamp, reverse=True)
        return filtered_events[:limit]
    
    async def get_audit_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get audit summary for specified time period"""
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        recent_events = await self.get_audit_events(start_time=start_time)
        
        # Count by event type
        event_type_counts = {}
        for event in recent_events:
            event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1
        
        # Count by level
        level_counts = {}
        for event in recent_events:
            level_counts[event.level.value] = level_counts.get(event.level.value, 0) + 1
        
        # Count by user
        user_counts = {}
        for event in recent_events:
            if event.user_id:
                user_counts[event.user_id] = user_counts.get(event.user_id, 0) + 1
        
        # Count by action
        action_counts = {}
        for event in recent_events:
            if event.action_name:
                action_counts[event.action_name] = action_counts.get(event.action_name, 0) + 1
        
        return {
            "time_period_hours": hours,
            "total_events": len(recent_events),
            "event_types": event_type_counts,
            "levels": level_counts,
            "top_users": sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "top_actions": sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "critical_events": len([e for e in recent_events if e.level == AuditLevel.CRITICAL]),
            "error_events": len([e for e in recent_events if e.level == AuditLevel.ERROR]),
            "warning_events": len([e for e in recent_events if e.level == AuditLevel.WARNING])
        }
    
    async def search_audit_logs(self, query: str, limit: int = 50) -> List[AuditEvent]:
        """Search audit logs by text query"""
        
        matching_events = []
        query_lower = query.lower()
        
        for event in self.audit_events:
            # Search in event type, user_id, action_name, and data
            searchable_text = f"{event.event_type} {event.user_id or ''} {event.action_name or ''} {str(event.data)}"
            
            if query_lower in searchable_text.lower():
                matching_events.append(event)
        
        # Sort by timestamp (newest first) and limit
        matching_events.sort(key=lambda x: x.timestamp, reverse=True)
        return matching_events[:limit]
    
    async def export_audit_logs(self, format: str = "json", 
                               start_time: Optional[datetime] = None,
                               end_time: Optional[datetime] = None) -> str:
        """Export audit logs in specified format"""
        
        events = await self.get_audit_events(start_time=start_time, end_time=end_time, limit=10000)
        
        if format == "json":
            events_data = []
            for event in events:
                event_dict = asdict(event)
                event_dict['timestamp'] = event.timestamp.isoformat()
                event_dict['level'] = event.level.value
                events_data.append(event_dict)
            
            return json.dumps(events_data, indent=2)
        
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            fieldnames = ['event_id', 'timestamp', 'event_type', 'level', 'user_id', 'action_name', 'execution_id']
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for event in events:
                writer.writerow({
                    'event_id': event.event_id,
                    'timestamp': event.timestamp.isoformat(),
                    'event_type': event.event_type,
                    'level': event.level.value,
                    'user_id': event.user_id or '',
                    'action_name': event.action_name or '',
                    'execution_id': event.execution_id or ''
                })
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    async def cleanup(self):
        """Cleanup audit logger"""
        
        # Archive old events to file before clearing
        if self.log_to_file:
            archive_file = f"{self.audit_file_path}.archive.{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            try:
                with open(archive_file, 'w') as f:
                    for event in self.audit_events:
                        event_dict = asdict(event)
                        event_dict['timestamp'] = event.timestamp.isoformat()
                        event_dict['level'] = event.level.value
                        f.write(json.dumps(event_dict) + '\n')
                
                logger.info(f"✅ Archived {len(self.audit_events)} audit events to {archive_file}")
                
            except Exception as e:
                logger.error(f"❌ Failed to archive audit events: {e}")
        
        # Clear in-memory events
        self.audit_events.clear()
        
        logger.info("✅ Audit logger cleaned up")