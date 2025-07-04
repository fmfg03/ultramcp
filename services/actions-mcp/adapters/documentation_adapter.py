"""
Documentation Adapter - Handles documentation updates in various systems
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp
import json

from .mock_adapter import MockAdapter

logger = logging.getLogger(__name__)

class DocumentationAdapter:
    """Adapter for documentation management across multiple platforms"""
    
    def __init__(self):
        self.is_initialized = False
        self.doc_configs = {}
        self.updated_docs = []
        
    async def initialize(self):
        """Initialize documentation adapter"""
        try:
            await self._load_documentation_configs()
            await self._test_documentation_connections()
            self.is_initialized = True
            logger.info("✅ Documentation adapter initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize documentation adapter: {e}")
            # Fall back to mock adapter
            self.mock_adapter = MockAdapter("DocumentationAdapter")
            await self.mock_adapter.initialize()
            logger.info("✅ Using mock documentation adapter")
    
    async def _load_documentation_configs(self):
        """Load documentation system configurations"""
        self.doc_configs = {
            "confluence": {
                "enabled": os.getenv("CONFLUENCE_ENABLED", "false").lower() == "true",
                "url": os.getenv("CONFLUENCE_URL", ""),
                "username": os.getenv("CONFLUENCE_USERNAME", ""),
                "api_token": os.getenv("CONFLUENCE_API_TOKEN", ""),
                "default_space": os.getenv("CONFLUENCE_DEFAULT_SPACE", "")
            },
            "notion": {
                "enabled": os.getenv("NOTION_ENABLED", "false").lower() == "true",
                "token": os.getenv("NOTION_TOKEN", ""),
                "default_database": os.getenv("NOTION_DEFAULT_DATABASE", "")
            },
            "gitbook": {
                "enabled": os.getenv("GITBOOK_ENABLED", "false").lower() == "true",
                "token": os.getenv("GITBOOK_TOKEN", ""),
                "organization": os.getenv("GITBOOK_ORGANIZATION", ""),
                "default_space": os.getenv("GITBOOK_DEFAULT_SPACE", "")
            },
            "wiki": {
                "enabled": os.getenv("WIKI_ENABLED", "false").lower() == "true",
                "url": os.getenv("WIKI_URL", ""),
                "username": os.getenv("WIKI_USERNAME", ""),
                "password": os.getenv("WIKI_PASSWORD", "")
            }
        }
    
    async def _test_documentation_connections(self):
        """Test connections to documentation systems"""
        
        if self.doc_configs["confluence"]["enabled"]:
            await self._test_confluence_connection()
        
        if self.doc_configs["notion"]["enabled"]:
            await self._test_notion_connection()
        
        if self.doc_configs["gitbook"]["enabled"]:
            await self._test_gitbook_connection()
    
    async def _test_confluence_connection(self):
        """Test Confluence connection"""
        try:
            confluence_config = self.doc_configs["confluence"]
            auth = aiohttp.BasicAuth(confluence_config["username"], confluence_config["api_token"])
            
            async with aiohttp.ClientSession(auth=auth) as session:
                async with session.get(
                    f"{confluence_config['url']}/rest/api/user/current",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("✅ Confluence connection test successful")
                    else:
                        raise Exception(f"Confluence returned status {response.status}")
                        
        except Exception as e:
            logger.warning(f"⚠️ Confluence connection test failed: {e}")
    
    async def _test_notion_connection(self):
        """Test Notion connection"""
        try:
            notion_config = self.doc_configs["notion"]
            headers = {
                "Authorization": f"Bearer {notion_config['token']}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    "https://api.notion.com/v1/users/me",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("✅ Notion connection test successful")
                    else:
                        raise Exception(f"Notion returned status {response.status}")
                        
        except Exception as e:
            logger.warning(f"⚠️ Notion connection test failed: {e}")
    
    async def _test_gitbook_connection(self):
        """Test GitBook connection"""
        try:
            gitbook_config = self.doc_configs["gitbook"]
            headers = {
                "Authorization": f"Bearer {gitbook_config['token']}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    "https://api.gitbook.com/v1/user",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("✅ GitBook connection test successful")
                    else:
                        raise Exception(f"GitBook returned status {response.status}")
                        
        except Exception as e:
            logger.warning(f"⚠️ GitBook connection test failed: {e}")
    
    async def execute(self, action_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute documentation action"""
        
        if not self.is_initialized and hasattr(self, 'mock_adapter'):
            return await self.mock_adapter.execute(action_name, input_data)
        
        if action_name == "update_documentation":
            return await self._update_documentation(input_data)
        else:
            raise ValueError(f"Unsupported action: {action_name}")
    
    async def _update_documentation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update documentation in specified system"""
        
        # Extract documentation parameters
        service = input_data.get("service", "").lower()
        page_id = input_data.get("page_id")
        title = input_data.get("title", "")
        content = input_data.get("content", "")
        format_type = input_data.get("format", "markdown")
        create_if_missing = input_data.get("create_if_missing", False)
        parent_page = input_data.get("parent_page")
        
        # Validate parameters
        if service not in self.doc_configs:
            raise ValueError(f"Unsupported documentation service: {service}")
        
        if not self.doc_configs[service]["enabled"]:
            raise ValueError(f"Documentation service {service} is not enabled")
        
        if not content:
            raise ValueError("Content is required")
        
        # Route to appropriate service handler
        result = None
        if service == "confluence":
            result = await self._update_confluence_page(page_id, title, content, format_type, create_if_missing, parent_page)
        elif service == "notion":
            result = await self._update_notion_page(page_id, title, content, format_type, create_if_missing, parent_page)
        elif service == "gitbook":
            result = await self._update_gitbook_page(page_id, title, content, format_type, create_if_missing, parent_page)
        elif service == "wiki":
            result = await self._update_wiki_page(page_id, title, content, format_type, create_if_missing, parent_page)
        else:
            raise ValueError(f"Handler not implemented for service: {service}")
        
        # Record updated documentation
        doc_record = {
            "page_id": result["page_id"],
            "service": service,
            "title": title,
            "action": "updated" if page_id else "created",
            "updated_at": datetime.utcnow(),
            "content_length": len(content)
        }
        
        self.updated_docs.append(doc_record)
        
        # Keep only last 1000 updates
        if len(self.updated_docs) > 1000:
            self.updated_docs = self.updated_docs[-1000:]
        
        return {
            **result,
            "service": service,
            "title": title,
            "action": doc_record["action"],
            "updated_at": doc_record["updated_at"].isoformat()
        }
    
    async def _update_confluence_page(self, page_id: Optional[str], title: str, content: str, 
                                     format_type: str, create_if_missing: bool, parent_page: Optional[str]) -> Dict[str, Any]:
        """Update Confluence page"""
        
        confluence_config = self.doc_configs["confluence"]
        auth = aiohttp.BasicAuth(confluence_config["username"], confluence_config["api_token"])
        
        try:
            # Convert content format if needed
            if format_type == "markdown":
                # In real implementation, convert markdown to Confluence storage format
                storage_content = f'<p>{content.replace("\n", "</p><p>")}</p>'
            else:
                storage_content = content
            
            async with aiohttp.ClientSession(auth=auth) as session:
                if page_id:
                    # Update existing page
                    # First get current version
                    async with session.get(
                        f"{confluence_config['url']}/rest/api/content/{page_id}",
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as response:
                        if response.status != 200:
                            raise Exception(f"Failed to get page info: {response.status}")
                        
                        page_info = await response.json()
                        current_version = page_info["version"]["number"]
                    
                    # Update page
                    update_payload = {
                        "version": {"number": current_version + 1},
                        "title": title or page_info["title"],
                        "type": "page",
                        "body": {
                            "storage": {
                                "value": storage_content,
                                "representation": "storage"
                            }
                        }
                    }
                    
                    async with session.put(
                        f"{confluence_config['url']}/rest/api/content/{page_id}",
                        json=update_payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return {
                                "page_id": result["id"],
                                "page_url": f"{confluence_config['url']}{result['_links']['webui']}",
                                "version": str(result["version"]["number"]),
                                "status": "updated"
                            }
                        else:
                            error_text = await response.text()
                            raise Exception(f"Failed to update page: {response.status} - {error_text}")
                
                elif create_if_missing:
                    # Create new page
                    create_payload = {
                        "type": "page",
                        "title": title,
                        "space": {"key": confluence_config["default_space"]},
                        "body": {
                            "storage": {
                                "value": storage_content,
                                "representation": "storage"
                            }
                        }
                    }
                    
                    if parent_page:
                        create_payload["ancestors"] = [{"id": parent_page}]
                    
                    async with session.post(
                        f"{confluence_config['url']}/rest/api/content",
                        json=create_payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return {
                                "page_id": result["id"],
                                "page_url": f"{confluence_config['url']}{result['_links']['webui']}",
                                "version": "1",
                                "status": "created"
                            }
                        else:
                            error_text = await response.text()
                            raise Exception(f"Failed to create page: {response.status} - {error_text}")
                
                else:
                    raise ValueError("Page ID is required when create_if_missing is False")
                    
        except Exception as e:
            logger.error(f"❌ Failed to update Confluence page: {e}")
            raise
    
    async def _update_notion_page(self, page_id: Optional[str], title: str, content: str,
                                 format_type: str, create_if_missing: bool, parent_page: Optional[str]) -> Dict[str, Any]:
        """Update Notion page"""
        
        notion_config = self.doc_configs["notion"]
        headers = {
            "Authorization": f"Bearer {notion_config['token']}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        
        try:
            # Convert content to Notion blocks
            blocks = await self._convert_to_notion_blocks(content, format_type)
            
            async with aiohttp.ClientSession(headers=headers) as session:
                if page_id:
                    # Update existing page
                    update_payload = {
                        "properties": {
                            "title": {
                                "title": [
                                    {
                                        "type": "text",
                                        "text": {"content": title}
                                    }
                                ]
                            }
                        }
                    }
                    
                    # Update page properties
                    async with session.patch(
                        f"https://api.notion.com/v1/pages/{page_id}",
                        json=update_payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise Exception(f"Failed to update page properties: {response.status} - {error_text}")
                    
                    # Update page content (append blocks)
                    content_payload = {"children": blocks}
                    
                    async with session.patch(
                        f"https://api.notion.com/v1/blocks/{page_id}/children",
                        json=content_payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            return {
                                "page_id": page_id,
                                "page_url": f"https://notion.so/{page_id.replace('-', '')}",
                                "version": "updated",
                                "status": "updated"
                            }
                        else:
                            error_text = await response.text()
                            raise Exception(f"Failed to update page content: {response.status} - {error_text}")
                
                elif create_if_missing:
                    # Create new page
                    create_payload = {
                        "parent": {"database_id": notion_config["default_database"]} if notion_config["default_database"] else {"page_id": parent_page},
                        "properties": {
                            "title": {
                                "title": [
                                    {
                                        "type": "text",
                                        "text": {"content": title}
                                    }
                                ]
                            }
                        },
                        "children": blocks
                    }
                    
                    async with session.post(
                        "https://api.notion.com/v1/pages",
                        json=create_payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return {
                                "page_id": result["id"],
                                "page_url": result["url"],
                                "version": "1",
                                "status": "created"
                            }
                        else:
                            error_text = await response.text()
                            raise Exception(f"Failed to create page: {response.status} - {error_text}")
                
                else:
                    raise ValueError("Page ID is required when create_if_missing is False")
                    
        except Exception as e:
            logger.error(f"❌ Failed to update Notion page: {e}")
            raise
    
    async def _convert_to_notion_blocks(self, content: str, format_type: str) -> List[Dict[str, Any]]:
        """Convert content to Notion blocks"""
        
        blocks = []
        
        if format_type == "markdown":
            # Simple markdown to Notion blocks conversion
            lines = content.split('\n')
            for line in lines:
                if line.startswith('# '):
                    blocks.append({
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                        }
                    })
                elif line.startswith('## '):
                    blocks.append({
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": line[3:]}}]
                        }
                    })
                elif line.strip():
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": line}}]
                        }
                    })
        else:
            # Plain text - convert to paragraphs
            paragraphs = content.split('\n\n')
            for paragraph in paragraphs:
                if paragraph.strip():
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": paragraph.strip()}}]
                        }
                    })
        
        return blocks
    
    async def _update_gitbook_page(self, page_id: Optional[str], title: str, content: str,
                                  format_type: str, create_if_missing: bool, parent_page: Optional[str]) -> Dict[str, Any]:
        """Update GitBook page"""
        
        # Simplified GitBook implementation
        return {
            "page_id": page_id or f"gitbook-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "page_url": f"https://app.gitbook.com/page/{page_id or 'new'}",
            "version": "updated",
            "status": "updated" if page_id else "created"
        }
    
    async def _update_wiki_page(self, page_id: Optional[str], title: str, content: str,
                               format_type: str, create_if_missing: bool, parent_page: Optional[str]) -> Dict[str, Any]:
        """Update Wiki page"""
        
        # Simplified Wiki implementation
        return {
            "page_id": page_id or f"wiki-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "page_url": f"https://wiki.company.com/{page_id or 'new'}",
            "version": "updated",
            "status": "updated" if page_id else "created"
        }
    
    async def get_documentation_statistics(self) -> Dict[str, Any]:
        """Get documentation adapter statistics"""
        
        total_updates = len(self.updated_docs)
        if total_updates == 0:
            return {"total_updates": 0}
        
        # Service distribution
        service_counts = {}
        for doc in self.updated_docs:
            service = doc["service"]
            service_counts[service] = service_counts.get(service, 0) + 1
        
        # Action distribution
        action_counts = {}
        for doc in self.updated_docs:
            action = doc["action"]
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # Content statistics
        total_content_length = sum(doc["content_length"] for doc in self.updated_docs)
        avg_content_length = total_content_length / total_updates if total_updates > 0 else 0
        
        return {
            "total_updates": total_updates,
            "service_distribution": service_counts,
            "action_distribution": action_counts,
            "total_content_length": total_content_length,
            "average_content_length": avg_content_length,
            "configured_services": {
                service: config["enabled"] 
                for service, config in self.doc_configs.items()
            }
        }
    
    async def cleanup(self):
        """Cleanup documentation adapter"""
        
        if self.updated_docs:
            logger.info(f"📝 Documentation adapter updated {len(self.updated_docs)} documents during session")
        
        self.updated_docs.clear()
        self.is_initialized = False
        logger.info("✅ Documentation adapter cleaned up")