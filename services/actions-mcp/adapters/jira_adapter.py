"""
Jira Adapter - Handles Jira ticket creation and management
"""

import asyncio
import logging
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp
import base64

from .mock_adapter import MockAdapter

logger = logging.getLogger(__name__)

class JiraAdapter:
    """Adapter for Jira ticket management"""
    
    def __init__(self):
        self.is_initialized = False
        self.jira_config = {}
        self.created_tickets = []
        
    async def initialize(self):
        """Initialize Jira adapter"""
        try:
            await self._load_jira_config()
            await self._test_jira_connection()
            self.is_initialized = True
            logger.info("✅ Jira adapter initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Jira adapter: {e}")
            # Fall back to mock adapter
            self.mock_adapter = MockAdapter("JiraAdapter")
            await self.mock_adapter.initialize()
            logger.info("✅ Using mock Jira adapter")
    
    async def _load_jira_config(self):
        """Load Jira configuration"""
        self.jira_config = {
            "url": os.getenv("JIRA_URL", ""),
            "username": os.getenv("JIRA_USERNAME", ""),
            "api_token": os.getenv("JIRA_API_TOKEN", ""),
            "default_project": os.getenv("JIRA_DEFAULT_PROJECT", ""),
            "api_version": "3"  # Jira Cloud API version
        }
        
        if not all([self.jira_config["url"], self.jira_config["username"], self.jira_config["api_token"]]):
            raise ValueError("JIRA_URL, JIRA_USERNAME, and JIRA_API_TOKEN must be configured")
    
    async def _test_jira_connection(self):
        """Test Jira connection"""
        try:
            headers = await self._get_auth_headers()
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    f"{self.jira_config['url']}/rest/api/{self.jira_config['api_version']}/myself",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        user_info = await response.json()
                        logger.info(f"✅ Jira connection test successful (user: {user_info.get('displayName')})")
                    else:
                        raise Exception(f"Jira returned status {response.status}")
                        
        except Exception as e:
            logger.warning(f"⚠️ Jira connection test failed: {e}")
            raise
    
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Jira API"""
        auth_string = f"{self.jira_config['username']}:{self.jira_config['api_token']}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        return {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def execute(self, action_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Jira action"""
        
        if not self.is_initialized and hasattr(self, 'mock_adapter'):
            return await self.mock_adapter.execute(action_name, input_data)
        
        if action_name == "create_jira_ticket":
            return await self._create_jira_ticket(input_data)
        else:
            raise ValueError(f"Unsupported action: {action_name}")
    
    async def _create_jira_ticket(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Jira ticket"""
        
        # Extract ticket parameters
        project = input_data.get("project", self.jira_config["default_project"])
        issue_type = input_data.get("issue_type", "Task")
        summary = input_data.get("summary", "")
        description = input_data.get("description", "")
        priority = input_data.get("priority", "Medium")
        assignee = input_data.get("assignee")
        labels = input_data.get("labels", [])
        components = input_data.get("components", [])
        custom_fields = input_data.get("custom_fields", {})
        
        # Validate required fields
        if not project:
            raise ValueError("Project is required")
        if not summary:
            raise ValueError("Summary is required")
        
        try:
            # Get project info to validate
            project_info = await self._get_project_info(project)
            if not project_info:
                raise ValueError(f"Project '{project}' not found")
            
            # Get issue type ID
            issue_type_id = await self._get_issue_type_id(project, issue_type)
            
            # Prepare ticket payload
            fields = {
                "project": {"key": project},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": description
                                }
                            ]
                        }
                    ]
                },
                "issuetype": {"id": issue_type_id}
            }
            
            # Add priority if specified
            if priority:
                fields["priority"] = {"name": priority}
            
            # Add assignee if specified
            if assignee:
                fields["assignee"] = {"accountId": assignee}
            
            # Add labels if specified
            if labels:
                fields["labels"] = labels
            
            # Add components if specified
            if components:
                fields["components"] = [{"name": comp} for comp in components]
            
            # Add custom fields
            fields.update(custom_fields)
            
            payload = {"fields": fields}
            
            # Create ticket
            headers = await self._get_auth_headers()
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(
                    f"{self.jira_config['url']}/rest/api/{self.jira_config['api_version']}/issue",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        ticket_key = result["key"]
                        ticket_id = result["id"]
                        
                        # Record created ticket
                        ticket_record = {
                            "ticket_id": ticket_key,
                            "ticket_key": ticket_key,
                            "internal_id": ticket_id,
                            "project": project,
                            "issue_type": issue_type,
                            "summary": summary,
                            "created_at": datetime.utcnow(),
                            "status": "created"
                        }
                        
                        self.created_tickets.append(ticket_record)
                        
                        # Keep only last 1000 tickets
                        if len(self.created_tickets) > 1000:
                            self.created_tickets = self.created_tickets[-1000:]
                        
                        return {
                            "ticket_id": ticket_key,
                            "ticket_url": f"{self.jira_config['url']}/browse/{ticket_key}",
                            "status": "created",
                            "project": project,
                            "issue_type": issue_type,
                            "summary": summary,
                            "created_at": ticket_record["created_at"].isoformat()
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"Jira API returned {response.status}: {error_text}")
                        
        except Exception as e:
            logger.error(f"❌ Failed to create Jira ticket: {e}")
            raise
    
    async def _get_project_info(self, project_key: str) -> Optional[Dict[str, Any]]:
        """Get project information"""
        try:
            headers = await self._get_auth_headers()
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    f"{self.jira_config['url']}/rest/api/{self.jira_config['api_version']}/project/{project_key}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
                    
        except Exception as e:
            logger.warning(f"⚠️ Failed to get project info for {project_key}: {e}")
            return None
    
    async def _get_issue_type_id(self, project_key: str, issue_type_name: str) -> str:
        """Get issue type ID for project"""
        try:
            headers = await self._get_auth_headers()
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    f"{self.jira_config['url']}/rest/api/{self.jira_config['api_version']}/project/{project_key}/statuses",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        statuses = await response.json()
                        
                        for issue_type in statuses:
                            if issue_type["name"].lower() == issue_type_name.lower():
                                return issue_type["id"]
                        
                        # If not found, try default issue types
                        default_types = {"Task": "10001", "Bug": "10004", "Story": "10002"}
                        return default_types.get(issue_type_name, "10001")  # Default to Task
                    
        except Exception as e:
            logger.warning(f"⚠️ Failed to get issue type ID: {e}")
        
        # Fallback to common issue type IDs
        default_types = {"Task": "10001", "Bug": "10004", "Story": "10002", "Epic": "10000"}
        return default_types.get(issue_type_name, "10001")
    
    async def get_ticket_status(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get status of Jira ticket"""
        
        # Check local records first
        for ticket in self.created_tickets:
            if ticket["ticket_id"] == ticket_id or ticket["ticket_key"] == ticket_id:
                return {
                    "ticket_id": ticket["ticket_key"],
                    "project": ticket["project"],
                    "summary": ticket["summary"],
                    "status": ticket["status"],
                    "created_at": ticket["created_at"].isoformat()
                }
        
        # Try to fetch from Jira API
        try:
            headers = await self._get_auth_headers()
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    f"{self.jira_config['url']}/rest/api/{self.jira_config['api_version']}/issue/{ticket_id}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        issue = await response.json()
                        return {
                            "ticket_id": issue["key"],
                            "project": issue["fields"]["project"]["key"],
                            "summary": issue["fields"]["summary"],
                            "status": issue["fields"]["status"]["name"],
                            "assignee": issue["fields"].get("assignee", {}).get("displayName"),
                            "created_at": issue["fields"]["created"]
                        }
                        
        except Exception as e:
            logger.warning(f"⚠️ Failed to get ticket status for {ticket_id}: {e}")
        
        return None
    
    async def get_jira_statistics(self) -> Dict[str, Any]:
        """Get Jira adapter statistics"""
        
        total_tickets = len(self.created_tickets)
        if total_tickets == 0:
            return {"total_tickets": 0}
        
        # Project distribution
        project_counts = {}
        for ticket in self.created_tickets:
            project = ticket["project"]
            project_counts[project] = project_counts.get(project, 0) + 1
        
        # Issue type distribution
        type_counts = {}
        for ticket in self.created_tickets:
            issue_type = ticket["issue_type"]
            type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
        
        return {
            "total_tickets": total_tickets,
            "project_distribution": project_counts,
            "issue_type_distribution": type_counts,
            "jira_configured": bool(self.jira_config.get("url")),
            "default_project": self.jira_config.get("default_project")
        }
    
    async def cleanup(self):
        """Cleanup Jira adapter"""
        
        if self.created_tickets:
            logger.info(f"🎫 Jira adapter created {len(self.created_tickets)} tickets during session")
        
        self.created_tickets.clear()
        self.is_initialized = False
        logger.info("✅ Jira adapter cleaned up")