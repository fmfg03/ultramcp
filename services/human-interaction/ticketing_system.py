"""
UltraMCP Supreme Stack - Integrated Ticketing System
Handles ticket creation, management, and integration with external ticketing systems

Features:
- Internal ticket management
- External system integration (Jira, ServiceNow, etc.)
- Priority-based routing
- SLA tracking
- Human escalation workflows
- Real-time notifications
"""

import asyncio
import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from enum import Enum
from dataclasses import dataclass, asdict, field
from pydantic import BaseModel, Field
import sqlite3
import aiofiles
import httpx

# Internal imports
from core.orchestrator.eventBus import EventBus


class TicketPriority(Enum):
    """Ticket priority levels"""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class TicketStatus(Enum):
    """Ticket status values"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_CUSTOMER = "waiting_for_customer"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class TicketCategory(Enum):
    """Ticket categories"""
    AGENT_ESCALATION = "agent_escalation"
    SYSTEM_ERROR = "system_error"
    APPROVAL_REQUEST = "approval_request"
    INFORMATION_REQUEST = "information_request"
    EXPERT_CONSULTATION = "expert_consultation"
    INVESTIGATION_REQUEST = "investigation_request"
    SECURITY_INCIDENT = "security_incident"
    PERFORMANCE_ISSUE = "performance_issue"
    FEATURE_REQUEST = "feature_request"
    USER_SUPPORT = "user_support"


class SLALevel(Enum):
    """SLA levels with response times"""
    STANDARD = "standard"    # 4 hours
    EXPEDITED = "expedited"  # 2 hours
    URGENT = "urgent"        # 1 hour
    CRITICAL = "critical"    # 30 minutes
    EMERGENCY = "emergency"  # 15 minutes


@dataclass
class Ticket:
    """Core ticket data structure"""
    id: str
    title: str
    description: str
    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    created_at: datetime
    created_by: str
    assigned_to: Optional[str] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    sla_level: SLALevel = SLALevel.STANDARD
    due_date: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    external_id: Optional[str] = None  # ID in external system
    external_system: Optional[str] = None  # External system name
    escalation_level: int = 0
    escalation_chain: List[str] = field(default_factory=list)
    parent_ticket_id: Optional[str] = None
    child_ticket_ids: List[str] = field(default_factory=list)
    watchers: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    comments: List[Dict[str, Any]] = field(default_factory=list)
    resolution_notes: Optional[str] = None
    customer_satisfaction: Optional[int] = None  # 1-5 rating


@dataclass
class TicketComment:
    """Ticket comment structure"""
    id: str
    ticket_id: str
    author: str
    content: str
    created_at: datetime
    is_internal: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class TicketingSystem:
    """
    Comprehensive ticketing system for UltraMCP
    
    Features:
    - Internal ticket management with SQLite persistence
    - External system integration (Jira, ServiceNow, etc.)
    - SLA management and escalation
    - Real-time notifications via EventBus
    - Priority-based routing and assignment
    - Analytics and reporting
    """
    
    def __init__(self, event_bus: EventBus, config: Dict[str, Any] = None):
        self.event_bus = event_bus
        self.logger = logging.getLogger(f"{__name__}.TicketingSystem")
        
        # Configuration
        self.config = {
            "database_path": "data/tickets.db",
            "enable_external_sync": True,
            "auto_escalation": True,
            "sla_monitoring": True,
            "notification_channels": ["email", "telegram", "webhook"],
            "default_assignee": "support_team",
            "escalation_timeout_minutes": 30,
            "max_escalation_level": 3,
            **(config or {})
        }
        
        # SLA definitions (in minutes)
        self.sla_definitions = {
            SLALevel.STANDARD: {"response": 240, "resolution": 1440},      # 4h/24h
            SLALevel.EXPEDITED: {"response": 120, "resolution": 720},      # 2h/12h
            SLALevel.URGENT: {"response": 60, "resolution": 360},          # 1h/6h
            SLALevel.CRITICAL: {"response": 30, "resolution": 120},        # 30m/2h
            SLALevel.EMERGENCY: {"response": 15, "resolution": 60}         # 15m/1h
        }
        
        # Priority to SLA mapping
        self.priority_to_sla = {
            TicketPriority.LOW: SLALevel.STANDARD,
            TicketPriority.MEDIUM: SLALevel.EXPEDITED,
            TicketPriority.HIGH: SLALevel.URGENT,
            TicketPriority.CRITICAL: SLALevel.CRITICAL,
            TicketPriority.EMERGENCY: SLALevel.EMERGENCY
        }
        
        # Assignment rules
        self.assignment_rules = {
            TicketCategory.AGENT_ESCALATION: "ai_specialist",
            TicketCategory.SYSTEM_ERROR: "devops_team",
            TicketCategory.SECURITY_INCIDENT: "security_team",
            TicketCategory.EXPERT_CONSULTATION: "subject_matter_expert",
            TicketCategory.APPROVAL_REQUEST: "approval_manager"
        }
        
        # External system configurations
        self.external_systems = {}
        
        # Initialize database
        asyncio.create_task(self._initialize_database())
        
        # Setup event listeners
        self._setup_event_listeners()
        
        # Start background tasks
        asyncio.create_task(self._start_background_tasks())
        
        self.logger.info("TicketingSystem initialized")

    async def _initialize_database(self):
        """Initialize SQLite database for ticket storage"""
        try:
            conn = sqlite3.connect(self.config["database_path"])
            cursor = conn.cursor()
            
            # Create tickets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    assigned_to TEXT,
                    updated_at TEXT,
                    resolved_at TEXT,
                    closed_at TEXT,
                    sla_level TEXT NOT NULL,
                    due_date TEXT,
                    tags TEXT,
                    metadata TEXT,
                    external_id TEXT,
                    external_system TEXT,
                    escalation_level INTEGER DEFAULT 0,
                    escalation_chain TEXT,
                    parent_ticket_id TEXT,
                    child_ticket_ids TEXT,
                    watchers TEXT,
                    attachments TEXT,
                    resolution_notes TEXT,
                    customer_satisfaction INTEGER,
                    FOREIGN KEY (parent_ticket_id) REFERENCES tickets (id)
                )
            """)
            
            # Create comments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ticket_comments (
                    id TEXT PRIMARY KEY,
                    ticket_id TEXT NOT NULL,
                    author TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_internal BOOLEAN DEFAULT FALSE,
                    metadata TEXT,
                    FOREIGN KEY (ticket_id) REFERENCES tickets (id)
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_assigned_to ON tickets(assigned_to)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_ticket_id ON ticket_comments(ticket_id)")
            
            conn.commit()
            conn.close()
            
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {str(e)}")

    def _setup_event_listeners(self):
        """Setup event listeners for automatic ticket creation"""
        
        # Listen for escalation events
        self.event_bus.on('escalation.created', self._handle_escalation_event)
        
        # Listen for action approval requests
        self.event_bus.on('action.approval_requested', self._handle_approval_request)
        
        # Listen for expert consultation requests
        self.event_bus.on('expert.consultation_requested', self._handle_consultation_request)
        
        # Listen for information requests
        self.event_bus.on('information.requested', self._handle_information_request)
        
        # Listen for investigation suggestions
        self.event_bus.on('investigation.suggested', self._handle_investigation_request)
        
        # Listen for system errors
        self.event_bus.on('system.error', self._handle_system_error)
        
        # Listen for security incidents
        self.event_bus.on('security.incident', self._handle_security_incident)

    async def _start_background_tasks(self):
        """Start background monitoring tasks"""
        if self.config["sla_monitoring"]:
            asyncio.create_task(self._sla_monitor())
        
        if self.config["auto_escalation"]:
            asyncio.create_task(self._escalation_monitor())
        
        if self.config["enable_external_sync"]:
            asyncio.create_task(self._external_sync_monitor())

    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Ticket:
        """Create a new ticket"""
        try:
            # Generate unique ID
            ticket_id = str(uuid.uuid4())
            
            # Determine SLA level from priority
            priority = TicketPriority(ticket_data.get("priority", "medium"))
            sla_level = self.priority_to_sla.get(priority, SLALevel.STANDARD)
            
            # Calculate due date based on SLA
            response_time = self.sla_definitions[sla_level]["response"]
            due_date = datetime.now() + timedelta(minutes=response_time)
            
            # Auto-assign based on category
            category = TicketCategory(ticket_data.get("category", "user_support"))
            assigned_to = self.assignment_rules.get(category, self.config["default_assignee"])
            
            # Create ticket object
            ticket = Ticket(
                id=ticket_id,
                title=ticket_data["title"],
                description=ticket_data["description"],
                category=category,
                priority=priority,
                status=TicketStatus.OPEN,
                created_at=datetime.now(),
                created_by=ticket_data.get("created_by", "system"),
                assigned_to=assigned_to,
                updated_at=datetime.now(),
                sla_level=sla_level,
                due_date=due_date,
                tags=ticket_data.get("tags", []),
                metadata=ticket_data.get("metadata", {}),
                escalation_chain=ticket_data.get("escalation_chain", []),
                watchers=ticket_data.get("watchers", [])
            )
            
            # Save to database
            await self._save_ticket(ticket)
            
            # Create in external system if configured
            if self.config["enable_external_sync"]:
                await self._create_external_ticket(ticket)
            
            # Emit ticket creation event
            self.event_bus.emit('ticket.created', {
                'ticket_id': ticket.id,
                'title': ticket.title,
                'category': ticket.category.value,
                'priority': ticket.priority.value,
                'assigned_to': ticket.assigned_to,
                'due_date': ticket.due_date.isoformat() if ticket.due_date else None
            })
            
            # Send notifications
            await self._send_ticket_notifications(ticket, "created")
            
            self.logger.info(f"Created ticket {ticket.id}: {ticket.title}")
            return ticket
            
        except Exception as e:
            self.logger.error(f"Failed to create ticket: {str(e)}")
            raise

    async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> Optional[Ticket]:
        """Update an existing ticket"""
        try:
            ticket = await self.get_ticket(ticket_id)
            if not ticket:
                return None
            
            # Track what changed for notifications
            changes = {}
            
            # Apply updates
            for field, value in updates.items():
                if hasattr(ticket, field):
                    old_value = getattr(ticket, field)
                    if old_value != value:
                        changes[field] = {"from": old_value, "to": value}
                        setattr(ticket, field, value)
            
            # Update timestamp
            ticket.updated_at = datetime.now()
            
            # Handle status changes
            if "status" in changes:
                new_status = TicketStatus(changes["status"]["to"])
                if new_status == TicketStatus.RESOLVED:
                    ticket.resolved_at = datetime.now()
                elif new_status == TicketStatus.CLOSED:
                    ticket.closed_at = datetime.now()
            
            # Save to database
            await self._save_ticket(ticket)
            
            # Update external system
            if self.config["enable_external_sync"] and ticket.external_id:
                await self._update_external_ticket(ticket, changes)
            
            # Emit update event
            self.event_bus.emit('ticket.updated', {
                'ticket_id': ticket.id,
                'changes': changes,
                'updated_by': updates.get('updated_by', 'system')
            })
            
            # Send notifications for significant changes
            if self._is_significant_change(changes):
                await self._send_ticket_notifications(ticket, "updated", changes)
            
            return ticket
            
        except Exception as e:
            self.logger.error(f"Failed to update ticket {ticket_id}: {str(e)}")
            raise

    async def add_comment(self, ticket_id: str, comment_data: Dict[str, Any]) -> TicketComment:
        """Add a comment to a ticket"""
        try:
            comment = TicketComment(
                id=str(uuid.uuid4()),
                ticket_id=ticket_id,
                author=comment_data["author"],
                content=comment_data["content"],
                created_at=datetime.now(),
                is_internal=comment_data.get("is_internal", False),
                metadata=comment_data.get("metadata", {})
            )
            
            # Save to database
            await self._save_comment(comment)
            
            # Update ticket's updated_at timestamp
            await self.update_ticket(ticket_id, {"updated_at": datetime.now()})
            
            # Emit comment event
            self.event_bus.emit('ticket.comment_added', {
                'ticket_id': ticket_id,
                'comment_id': comment.id,
                'author': comment.author,
                'is_internal': comment.is_internal
            })
            
            # Send notifications
            await self._send_comment_notifications(ticket_id, comment)
            
            return comment
            
        except Exception as e:
            self.logger.error(f"Failed to add comment to ticket {ticket_id}: {str(e)}")
            raise

    async def escalate_ticket(self, ticket_id: str, escalation_reason: str, escalated_by: str) -> Optional[Ticket]:
        """Escalate a ticket to the next level"""
        try:
            ticket = await self.get_ticket(ticket_id)
            if not ticket:
                return None
            
            # Check if escalation is possible
            if ticket.escalation_level >= self.config["max_escalation_level"]:
                self.logger.warning(f"Ticket {ticket_id} already at maximum escalation level")
                return ticket
            
            # Determine next escalation target
            if ticket.escalation_chain and len(ticket.escalation_chain) > ticket.escalation_level:
                next_assignee = ticket.escalation_chain[ticket.escalation_level]
            else:
                # Use default escalation chain based on category
                default_chain = self._get_default_escalation_chain(ticket.category)
                if len(default_chain) > ticket.escalation_level:
                    next_assignee = default_chain[ticket.escalation_level]
                else:
                    next_assignee = "executive_team"  # Final escalation
            
            # Update ticket
            updates = {
                "escalation_level": ticket.escalation_level + 1,
                "assigned_to": next_assignee,
                "status": TicketStatus.ESCALATED,
                "priority": self._escalate_priority(ticket.priority),
                "updated_by": escalated_by
            }
            
            ticket = await self.update_ticket(ticket_id, updates)
            
            # Add escalation comment
            await self.add_comment(ticket_id, {
                "author": "system",
                "content": f"Ticket escalated to {next_assignee}. Reason: {escalation_reason}",
                "is_internal": True,
                "metadata": {
                    "escalation_level": ticket.escalation_level,
                    "escalated_by": escalated_by,
                    "escalation_reason": escalation_reason
                }
            })
            
            # Emit escalation event
            self.event_bus.emit('ticket.escalated', {
                'ticket_id': ticket_id,
                'escalation_level': ticket.escalation_level,
                'assigned_to': next_assignee,
                'escalated_by': escalated_by,
                'escalation_reason': escalation_reason
            })
            
            return ticket
            
        except Exception as e:
            self.logger.error(f"Failed to escalate ticket {ticket_id}: {str(e)}")
            raise

    async def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Retrieve a ticket by ID"""
        try:
            conn = sqlite3.connect(self.config["database_path"])
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
            row = cursor.fetchone()
            
            if row:
                # Convert row to dict
                columns = [desc[0] for desc in cursor.description]
                ticket_dict = dict(zip(columns, row))
                
                # Convert to Ticket object
                ticket = self._dict_to_ticket(ticket_dict)
                
                # Load comments
                cursor.execute("SELECT * FROM ticket_comments WHERE ticket_id = ? ORDER BY created_at", (ticket_id,))
                comment_rows = cursor.fetchall()
                
                comment_columns = [desc[0] for desc in cursor.description]
                for comment_row in comment_rows:
                    comment_dict = dict(zip(comment_columns, comment_row))
                    comment = self._dict_to_comment(comment_dict)
                    ticket.comments.append(asdict(comment))
                
                conn.close()
                return ticket
            
            conn.close()
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get ticket {ticket_id}: {str(e)}")
            return None

    async def search_tickets(self, filters: Dict[str, Any] = None, limit: int = 100) -> List[Ticket]:
        """Search tickets with filters"""
        try:
            conn = sqlite3.connect(self.config["database_path"])
            cursor = conn.cursor()
            
            query = "SELECT * FROM tickets"
            params = []
            conditions = []
            
            if filters:
                if "status" in filters:
                    conditions.append("status = ?")
                    params.append(filters["status"])
                
                if "priority" in filters:
                    conditions.append("priority = ?")
                    params.append(filters["priority"])
                
                if "category" in filters:
                    conditions.append("category = ?")
                    params.append(filters["category"])
                
                if "assigned_to" in filters:
                    conditions.append("assigned_to = ?")
                    params.append(filters["assigned_to"])
                
                if "created_by" in filters:
                    conditions.append("created_by = ?")
                    params.append(filters["created_by"])
                
                if "created_after" in filters:
                    conditions.append("created_at >= ?")
                    params.append(filters["created_after"])
                
                if "created_before" in filters:
                    conditions.append("created_at <= ?")
                    params.append(filters["created_before"])
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            columns = [desc[0] for desc in cursor.description]
            tickets = []
            
            for row in rows:
                ticket_dict = dict(zip(columns, row))
                ticket = self._dict_to_ticket(ticket_dict)
                tickets.append(ticket)
            
            conn.close()
            return tickets
            
        except Exception as e:
            self.logger.error(f"Failed to search tickets: {str(e)}")
            return []

    async def get_ticket_statistics(self) -> Dict[str, Any]:
        """Get ticket statistics and metrics"""
        try:
            conn = sqlite3.connect(self.config["database_path"])
            cursor = conn.cursor()
            
            # Total tickets
            cursor.execute("SELECT COUNT(*) FROM tickets")
            total_tickets = cursor.fetchone()[0]
            
            # Tickets by status
            cursor.execute("SELECT status, COUNT(*) FROM tickets GROUP BY status")
            status_counts = dict(cursor.fetchall())
            
            # Tickets by priority
            cursor.execute("SELECT priority, COUNT(*) FROM tickets GROUP BY priority")
            priority_counts = dict(cursor.fetchall())
            
            # Tickets by category
            cursor.execute("SELECT category, COUNT(*) FROM tickets GROUP BY category")
            category_counts = dict(cursor.fetchall())
            
            # Average resolution time (in hours)
            cursor.execute("""
                SELECT AVG(
                    (julianday(resolved_at) - julianday(created_at)) * 24
                ) FROM tickets WHERE resolved_at IS NOT NULL
            """)
            avg_resolution_time = cursor.fetchone()[0] or 0
            
            # SLA compliance rate
            cursor.execute("""
                SELECT COUNT(*) FROM tickets 
                WHERE resolved_at IS NOT NULL 
                AND resolved_at <= due_date
            """)
            sla_compliant = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tickets WHERE resolved_at IS NOT NULL")
            total_resolved = cursor.fetchone()[0]
            
            sla_compliance_rate = (sla_compliant / total_resolved * 100) if total_resolved > 0 else 0
            
            # Overdue tickets
            cursor.execute("""
                SELECT COUNT(*) FROM tickets 
                WHERE status NOT IN ('resolved', 'closed') 
                AND due_date < datetime('now')
            """)
            overdue_tickets = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_tickets": total_tickets,
                "status_distribution": status_counts,
                "priority_distribution": priority_counts,
                "category_distribution": category_counts,
                "average_resolution_time_hours": round(avg_resolution_time, 2),
                "sla_compliance_rate": round(sla_compliance_rate, 2),
                "overdue_tickets": overdue_tickets,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get ticket statistics: {str(e)}")
            return {}

    # Event handlers for automatic ticket creation

    async def _handle_escalation_event(self, event_data):
        """Handle escalation events from action requests"""
        await self.create_ticket({
            "title": f"Agent Escalation: {event_data.get('summary', 'Issue requires human attention')}",
            "description": event_data.get('details', 'No details provided'),
            "category": "agent_escalation",
            "priority": event_data.get('priority', 'medium'),
            "created_by": "ultramcp_agent",
            "metadata": {
                "request_id": event_data.get('request_id'),
                "escalation_reason": event_data.get('escalation_reason'),
                "suggested_actions": event_data.get('suggested_actions', [])
            }
        })

    async def _handle_approval_request(self, event_data):
        """Handle approval request events"""
        await self.create_ticket({
            "title": f"Approval Required: {event_data.get('title', 'Action Approval')}",
            "description": event_data.get('description', 'Action requires human approval'),
            "category": "approval_request",
            "priority": self._risk_to_priority(event_data.get('risk_level', 'medium')),
            "created_by": "approval_system",
            "metadata": {
                "request_id": event_data.get('request_id'),
                "action_type": event_data.get('action_type'),
                "risk_level": event_data.get('risk_level'),
                "approval_chain": event_data.get('approval_chain', [])
            }
        })

    async def _handle_consultation_request(self, event_data):
        """Handle expert consultation requests"""
        await self.create_ticket({
            "title": f"Expert Consultation: {event_data.get('domain', 'Unknown Domain')}",
            "description": event_data.get('question', 'Consultation requested'),
            "category": "expert_consultation",
            "priority": event_data.get('urgency', 'medium'),
            "created_by": "consultation_system",
            "metadata": {
                "request_id": event_data.get('request_id'),
                "domain": event_data.get('domain'),
                "question": event_data.get('question')
            }
        })

    async def _handle_information_request(self, event_data):
        """Handle information requests"""
        await self.create_ticket({
            "title": f"Information Request: {event_data.get('information_type', 'Additional Info')}",
            "description": f"Questions: {', '.join(event_data.get('questions', []))}",
            "category": "information_request",
            "priority": "medium",
            "created_by": "information_system",
            "metadata": {
                "request_id": event_data.get('request_id'),
                "information_type": event_data.get('information_type'),
                "questions": event_data.get('questions', []),
                "source": event_data.get('source', 'user')
            }
        })

    async def _handle_investigation_request(self, event_data):
        """Handle investigation suggestions"""
        await self.create_ticket({
            "title": f"Investigation Suggested: {event_data.get('investigation_type', 'Study Required')}",
            "description": event_data.get('rationale', 'Investigation recommended'),
            "category": "investigation_request",
            "priority": "medium",
            "created_by": "investigation_system",
            "metadata": {
                "request_id": event_data.get('request_id'),
                "investigation_type": event_data.get('investigation_type'),
                "rationale": event_data.get('rationale'),
                "expected_outcomes": event_data.get('expected_outcomes', []),
                "estimated_time": event_data.get('estimated_time'),
                "estimated_cost": event_data.get('estimated_cost')
            }
        })

    async def _handle_system_error(self, event_data):
        """Handle system error events"""
        await self.create_ticket({
            "title": f"System Error: {event_data.get('error_type', 'Unknown Error')}",
            "description": event_data.get('error_message', 'System error occurred'),
            "category": "system_error",
            "priority": event_data.get('severity', 'high'),
            "created_by": "system_monitor",
            "metadata": {
                "error_type": event_data.get('error_type'),
                "error_message": event_data.get('error_message'),
                "stack_trace": event_data.get('stack_trace'),
                "component": event_data.get('component'),
                "timestamp": event_data.get('timestamp')
            }
        })

    async def _handle_security_incident(self, event_data):
        """Handle security incident events"""
        await self.create_ticket({
            "title": f"Security Incident: {event_data.get('incident_type', 'Security Alert')}",
            "description": event_data.get('description', 'Security incident detected'),
            "category": "security_incident",
            "priority": "critical",
            "created_by": "security_monitor",
            "metadata": {
                "incident_type": event_data.get('incident_type'),
                "severity": event_data.get('severity'),
                "affected_systems": event_data.get('affected_systems', []),
                "detection_time": event_data.get('detection_time'),
                "indicators": event_data.get('indicators', [])
            }
        })

    # Helper methods

    def _risk_to_priority(self, risk_level: str) -> str:
        """Convert risk level to ticket priority"""
        mapping = {
            "low": "low",
            "medium": "medium",
            "high": "high",
            "critical": "critical"
        }
        return mapping.get(risk_level, "medium")

    def _escalate_priority(self, current_priority: TicketPriority) -> TicketPriority:
        """Escalate ticket priority"""
        escalation_map = {
            TicketPriority.LOW: TicketPriority.MEDIUM,
            TicketPriority.MEDIUM: TicketPriority.HIGH,
            TicketPriority.HIGH: TicketPriority.CRITICAL,
            TicketPriority.CRITICAL: TicketPriority.EMERGENCY,
            TicketPriority.EMERGENCY: TicketPriority.EMERGENCY  # Already at max
        }
        return escalation_map.get(current_priority, current_priority)

    def _get_default_escalation_chain(self, category: TicketCategory) -> List[str]:
        """Get default escalation chain for category"""
        chains = {
            TicketCategory.AGENT_ESCALATION: ["ai_specialist", "senior_engineer", "technical_director"],
            TicketCategory.SYSTEM_ERROR: ["devops_engineer", "infrastructure_lead", "cto"],
            TicketCategory.SECURITY_INCIDENT: ["security_analyst", "security_manager", "ciso"],
            TicketCategory.APPROVAL_REQUEST: ["team_lead", "department_manager", "director"],
            TicketCategory.EXPERT_CONSULTATION: ["subject_matter_expert", "senior_consultant", "external_expert"]
        }
        return chains.get(category, ["team_lead", "manager", "director"])

    def _is_significant_change(self, changes: Dict[str, Any]) -> bool:
        """Determine if changes warrant notifications"""
        significant_fields = {"status", "priority", "assigned_to", "escalation_level"}
        return bool(set(changes.keys()) & significant_fields)

    # Database helper methods

    async def _save_ticket(self, ticket: Ticket):
        """Save ticket to database"""
        conn = sqlite3.connect(self.config["database_path"])
        cursor = conn.cursor()
        
        # Convert ticket to database format
        ticket_dict = asdict(ticket)
        
        # Convert complex fields to JSON
        ticket_dict["tags"] = json.dumps(ticket.tags)
        ticket_dict["metadata"] = json.dumps(ticket.metadata)
        ticket_dict["escalation_chain"] = json.dumps(ticket.escalation_chain)
        ticket_dict["child_ticket_ids"] = json.dumps(ticket.child_ticket_ids)
        ticket_dict["watchers"] = json.dumps(ticket.watchers)
        ticket_dict["attachments"] = json.dumps(ticket.attachments)
        
        # Convert datetime objects to ISO strings
        for field in ["created_at", "updated_at", "resolved_at", "closed_at", "due_date"]:
            value = ticket_dict[field]
            if value:
                ticket_dict[field] = value.isoformat() if isinstance(value, datetime) else value
        
        # Convert enums to strings
        ticket_dict["category"] = ticket.category.value
        ticket_dict["priority"] = ticket.priority.value
        ticket_dict["status"] = ticket.status.value
        ticket_dict["sla_level"] = ticket.sla_level.value
        
        # Remove comments field (stored separately)
        ticket_dict.pop("comments", None)
        
        # Upsert ticket
        columns = list(ticket_dict.keys())
        placeholders = ", ".join(["?" for _ in columns])
        update_clause = ", ".join([f"{col} = ?" for col in columns if col != "id"])
        
        cursor.execute(f"""
            INSERT OR REPLACE INTO tickets ({", ".join(columns)})
            VALUES ({placeholders})
        """, list(ticket_dict.values()))
        
        conn.commit()
        conn.close()

    async def _save_comment(self, comment: TicketComment):
        """Save comment to database"""
        conn = sqlite3.connect(self.config["database_path"])
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO ticket_comments 
            (id, ticket_id, author, content, created_at, is_internal, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            comment.id,
            comment.ticket_id,
            comment.author,
            comment.content,
            comment.created_at.isoformat(),
            comment.is_internal,
            json.dumps(comment.metadata)
        ))
        
        conn.commit()
        conn.close()

    def _dict_to_ticket(self, ticket_dict: Dict[str, Any]) -> Ticket:
        """Convert database dict to Ticket object"""
        # Convert JSON fields
        ticket_dict["tags"] = json.loads(ticket_dict["tags"] or "[]")
        ticket_dict["metadata"] = json.loads(ticket_dict["metadata"] or "{}")
        ticket_dict["escalation_chain"] = json.loads(ticket_dict["escalation_chain"] or "[]")
        ticket_dict["child_ticket_ids"] = json.loads(ticket_dict["child_ticket_ids"] or "[]")
        ticket_dict["watchers"] = json.loads(ticket_dict["watchers"] or "[]")
        ticket_dict["attachments"] = json.loads(ticket_dict["attachments"] or "[]")
        
        # Convert datetime strings
        for field in ["created_at", "updated_at", "resolved_at", "closed_at", "due_date"]:
            if ticket_dict[field]:
                ticket_dict[field] = datetime.fromisoformat(ticket_dict[field])
        
        # Convert enums
        ticket_dict["category"] = TicketCategory(ticket_dict["category"])
        ticket_dict["priority"] = TicketPriority(ticket_dict["priority"])
        ticket_dict["status"] = TicketStatus(ticket_dict["status"])
        ticket_dict["sla_level"] = SLALevel(ticket_dict["sla_level"])
        
        # Add empty comments list (loaded separately)
        ticket_dict["comments"] = []
        
        return Ticket(**ticket_dict)

    def _dict_to_comment(self, comment_dict: Dict[str, Any]) -> TicketComment:
        """Convert database dict to TicketComment object"""
        comment_dict["created_at"] = datetime.fromisoformat(comment_dict["created_at"])
        comment_dict["metadata"] = json.loads(comment_dict["metadata"] or "{}")
        return TicketComment(**comment_dict)

    # Background monitoring tasks

    async def _sla_monitor(self):
        """Monitor SLA compliance and send alerts"""
        while True:
            try:
                # Check for tickets approaching SLA breach
                current_time = datetime.now()
                
                open_tickets = await self.search_tickets({
                    "status": "open"
                })
                
                for ticket in open_tickets:
                    if ticket.due_date and ticket.due_date <= current_time:
                        # SLA breach
                        self.event_bus.emit('ticket.sla_breach', {
                            'ticket_id': ticket.id,
                            'title': ticket.title,
                            'assigned_to': ticket.assigned_to,
                            'overdue_by_minutes': int((current_time - ticket.due_date).total_seconds() / 60)
                        })
                    elif ticket.due_date and (ticket.due_date - current_time).total_seconds() < 3600:  # 1 hour warning
                        # SLA warning
                        self.event_bus.emit('ticket.sla_warning', {
                            'ticket_id': ticket.id,
                            'title': ticket.title,
                            'assigned_to': ticket.assigned_to,
                            'minutes_remaining': int((ticket.due_date - current_time).total_seconds() / 60)
                        })
                
                # Wait 5 minutes before next check
                await asyncio.sleep(300)
                
            except Exception as e:
                self.logger.error(f"Error in SLA monitor: {str(e)}")
                await asyncio.sleep(60)

    async def _escalation_monitor(self):
        """Monitor tickets for auto-escalation"""
        while True:
            try:
                escalation_timeout = timedelta(minutes=self.config["escalation_timeout_minutes"])
                current_time = datetime.now()
                
                # Find tickets that should be escalated
                stale_tickets = await self.search_tickets({
                    "status": "open"
                })
                
                for ticket in stale_tickets:
                    time_since_update = current_time - (ticket.updated_at or ticket.created_at)
                    
                    if time_since_update >= escalation_timeout:
                        await self.escalate_ticket(
                            ticket.id,
                            f"Auto-escalation: No update for {escalation_timeout}",
                            "auto_escalation_system"
                        )
                
                # Wait 10 minutes before next check
                await asyncio.sleep(600)
                
            except Exception as e:
                self.logger.error(f"Error in escalation monitor: {str(e)}")
                await asyncio.sleep(60)

    async def _external_sync_monitor(self):
        """Sync with external ticketing systems"""
        while True:
            try:
                # Sync updates from external systems
                for system_name, system_config in self.external_systems.items():
                    await self._sync_from_external_system(system_name, system_config)
                
                # Wait 15 minutes before next sync
                await asyncio.sleep(900)
                
            except Exception as e:
                self.logger.error(f"Error in external sync monitor: {str(e)}")
                await asyncio.sleep(300)

    # External system integration methods

    async def _create_external_ticket(self, ticket: Ticket):
        """Create ticket in external system"""
        # Implementation would depend on specific external system
        # This is a placeholder for Jira, ServiceNow, etc. integration
        pass

    async def _update_external_ticket(self, ticket: Ticket, changes: Dict[str, Any]):
        """Update ticket in external system"""
        # Implementation would depend on specific external system
        pass

    async def _sync_from_external_system(self, system_name: str, system_config: Dict[str, Any]):
        """Sync updates from external system"""
        # Implementation would depend on specific external system
        pass

    # Notification methods

    async def _send_ticket_notifications(self, ticket: Ticket, event_type: str, changes: Dict[str, Any] = None):
        """Send notifications for ticket events"""
        notification_data = {
            "event_type": event_type,
            "ticket_id": ticket.id,
            "title": ticket.title,
            "priority": ticket.priority.value,
            "status": ticket.status.value,
            "assigned_to": ticket.assigned_to,
            "changes": changes
        }
        
        # Email notifications
        if "email" in self.config["notification_channels"]:
            self.event_bus.emit('notification.email', {
                "to": ticket.assigned_to,
                "subject": f"Ticket {event_type}: {ticket.title}",
                "body": self._format_ticket_email(ticket, event_type, changes),
                "metadata": notification_data
            })
        
        # Telegram notifications
        if "telegram" in self.config["notification_channels"]:
            self.event_bus.emit('notification.telegram', {
                "message": self._format_ticket_telegram(ticket, event_type, changes),
                "metadata": notification_data
            })
        
        # Webhook notifications
        if "webhook" in self.config["notification_channels"]:
            self.event_bus.emit('notification.webhook', {
                "event": f"ticket.{event_type}",
                "data": notification_data
            })

    async def _send_comment_notifications(self, ticket_id: str, comment: TicketComment):
        """Send notifications for new comments"""
        ticket = await self.get_ticket(ticket_id)
        if not ticket:
            return
        
        notification_data = {
            "event_type": "comment_added",
            "ticket_id": ticket.id,
            "comment_id": comment.id,
            "author": comment.author,
            "content": comment.content[:200] + "..." if len(comment.content) > 200 else comment.content,
            "is_internal": comment.is_internal
        }
        
        # Send notifications to watchers and assigned user
        recipients = set([ticket.assigned_to] + ticket.watchers)
        recipients.discard(comment.author)  # Don't notify the comment author
        
        for recipient in recipients:
            if not comment.is_internal or self._user_can_see_internal_comments(recipient):
                # Send appropriate notifications
                pass

    def _format_ticket_email(self, ticket: Ticket, event_type: str, changes: Dict[str, Any] = None) -> str:
        """Format ticket notification email"""
        return f"""
Ticket {event_type.upper()}: {ticket.title}

ID: {ticket.id}
Priority: {ticket.priority.value}
Status: {ticket.status.value}
Assigned to: {ticket.assigned_to}
Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M:%S')}

Description:
{ticket.description}

{f"Changes: {changes}" if changes else ""}

View ticket: [Link to ticket system]
        """.strip()

    def _format_ticket_telegram(self, ticket: Ticket, event_type: str, changes: Dict[str, Any] = None) -> str:
        """Format ticket notification for Telegram"""
        priority_emoji = {
            "low": "🟢",
            "medium": "🟡", 
            "high": "🟠",
            "critical": "🔴",
            "emergency": "🚨"
        }
        
        emoji = priority_emoji.get(ticket.priority.value, "🎫")
        
        message = f"{emoji} *Ticket {event_type.upper()}*\n\n"
        message += f"*{ticket.title}*\n"
        message += f"ID: `{ticket.id}`\n"
        message += f"Priority: {ticket.priority.value}\n"
        message += f"Status: {ticket.status.value}\n"
        message += f"Assigned: {ticket.assigned_to}\n"
        
        if changes:
            message += f"\nChanges: {changes}"
        
        return message

    def _user_can_see_internal_comments(self, user: str) -> bool:
        """Check if user can see internal comments"""
        # Implementation would check user permissions
        return True  # Placeholder