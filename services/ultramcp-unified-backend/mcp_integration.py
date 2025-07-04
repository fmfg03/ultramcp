"""
FastAPI MCP Integration for UltraMCP Unified Backend
Exposes all endpoints as native MCP tools
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from fastapi import FastAPI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

@dataclass
class MCPTool:
    """MCP Tool definition"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    endpoint: str
    method: str
    privacy_level: str = "PUBLIC"
    intelligence_level: str = "ENHANCED"
    examples: List[Dict[str, Any]] = None

class UltraMCPToolRegistry:
    """Registry for all UltraMCP MCP tools"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.tools: Dict[str, MCPTool] = {}
        self.tool_categories = {
            "debate": "Chain of Debate Protocol",
            "memory": "Claude Code Memory Intelligence", 
            "voyage": "VoyageAI Enhanced Search",
            "ref": "Documentation Intelligence",
            "docs": "Unified Documentation Orchestration",
            "actions": "External Actions Execution"
        }
    
    async def initialize(self):
        """Initialize all MCP tools"""
        try:
            self._register_cod_tools()
            self._register_memory_tools()
            self._register_voyage_tools()
            self._register_ref_tools()
            self._register_docs_tools()
            self._register_actions_tools()
            
            # Add MCP endpoints
            self._add_mcp_endpoints()
            
            logger.info(f"✅ Registered {len(self.tools)} MCP tools")
            
        except Exception as e:
            logger.error(f"❌ MCP tool registration failed: {e}")
            raise
    
    def _register_cod_tools(self):
        """Register Chain of Debate MCP tools"""
        
        # Enhanced Chain of Debate
        self.tools["cod_enhanced_debate"] = MCPTool(
            name="cod_enhanced_debate",
            description="Start enhanced multi-LLM debate with local and API models",
            input_schema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Debate topic"},
                    "participants": {"type": "integer", "default": 3, "description": "Number of participants"},
                    "rounds": {"type": "integer", "default": 3, "description": "Number of debate rounds"},
                    "privacy_level": {"type": "string", "enum": ["PUBLIC", "INTERNAL", "CONFIDENTIAL"], "default": "INTERNAL"},
                    "include_local_models": {"type": "boolean", "default": True},
                    "context": {"type": "string", "description": "Additional context for debate"}
                },
                "required": ["topic"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "debate_id": {"type": "string"},
                    "participants": {"type": "array"},
                    "rounds": {"type": "array"},
                    "consensus": {"type": "string"},
                    "confidence_score": {"type": "number"},
                    "processing_time": {"type": "number"}
                }
            },
            endpoint="/cod/enhanced-debate",
            method="POST",
            privacy_level="CONFIGURABLE",
            intelligence_level="SUPREME",
            examples=[
                {
                    "input": {
                        "topic": "Should we implement microservices architecture for our new platform?",
                        "participants": 3,
                        "privacy_level": "INTERNAL"
                    },
                    "description": "Enterprise architecture decision making"
                }
            ]
        )
        
        # Local-only Chain of Debate
        self.tools["cod_local_debate"] = MCPTool(
            name="cod_local_debate",
            description="Privacy-first local debate with offline models only",
            input_schema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Debate topic"},
                    "participants": {"type": "integer", "default": 3},
                    "rounds": {"type": "integer", "default": 2},
                    "context": {"type": "string", "description": "Additional context"}
                },
                "required": ["topic"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "debate_id": {"type": "string"},
                    "consensus": {"type": "string"},
                    "local_processing": {"type": "boolean", "const": True},
                    "cost": {"type": "number", "const": 0.0}
                }
            },
            endpoint="/cod/local-debate",
            method="POST",
            privacy_level="CONFIDENTIAL",
            intelligence_level="BASIC"
        )
    
    def _register_memory_tools(self):
        """Register Claude Code Memory MCP tools"""
        
        # Enhanced semantic search
        self.tools["memory_enhanced_search"] = MCPTool(
            name="memory_enhanced_search",
            description="Enhanced semantic code search with VoyageAI integration",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "project_name": {"type": "string", "description": "Project context"},
                    "limit": {"type": "integer", "default": 10, "maximum": 50},
                    "privacy_level": {"type": "string", "enum": ["PUBLIC", "INTERNAL", "CONFIDENTIAL"], "default": "INTERNAL"},
                    "search_mode": {"type": "string", "enum": ["AUTO", "HYBRID", "LOCAL_ONLY"], "default": "AUTO"},
                    "enable_reranking": {"type": "boolean", "default": True}
                },
                "required": ["query"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "results": {"type": "array"},
                    "total_results": {"type": "integer"},
                    "search_mode": {"type": "string"},
                    "model_used": {"type": "string"},
                    "processing_time": {"type": "number"},
                    "cost": {"type": "number"}
                }
            },
            endpoint="/memory/search/enhanced",
            method="POST",
            privacy_level="CONFIGURABLE",
            intelligence_level="ENHANCED"
        )
        
        # Project indexing
        self.tools["memory_index_project"] = MCPTool(
            name="memory_index_project",
            description="Index project codebase for semantic memory",
            input_schema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "description": "Path to project"},
                    "project_name": {"type": "string", "description": "Project identifier"},
                    "include_patterns": {"type": "array", "items": {"type": "string"}},
                    "exclude_patterns": {"type": "array", "items": {"type": "string"}},
                    "privacy_level": {"type": "string", "enum": ["INTERNAL", "CONFIDENTIAL"], "default": "INTERNAL"}
                },
                "required": ["project_path", "project_name"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "indexed_files": {"type": "integer"},
                    "processing_time": {"type": "number"},
                    "project_id": {"type": "string"}
                }
            },
            endpoint="/memory/projects/index",
            method="POST",
            privacy_level="CONFIDENTIAL",
            intelligence_level="ENHANCED"
        )
    
    def _register_voyage_tools(self):
        """Register VoyageAI MCP tools"""
        
        # Enhanced semantic search
        self.tools["voyage_enhanced_search"] = MCPTool(
            name="voyage_enhanced_search",
            description="Premium semantic search with VoyageAI embeddings",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "privacy_level": {"type": "string", "enum": ["PUBLIC", "INTERNAL", "CONFIDENTIAL"], "default": "PUBLIC"},
                    "domain": {"type": "string", "enum": ["CODE", "FINANCE", "HEALTHCARE", "LEGAL", "GENERAL"]},
                    "search_mode": {"type": "string", "enum": ["AUTO", "HYBRID", "VOYAGE_ONLY"], "default": "AUTO"},
                    "limit": {"type": "integer", "default": 10, "maximum": 50}
                },
                "required": ["query"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "results": {"type": "array"},
                    "model_used": {"type": "string"},
                    "privacy_compliant": {"type": "boolean"},
                    "cost": {"type": "number"},
                    "processing_time": {"type": "number"}
                }
            },
            endpoint="/voyage/search/enhanced",
            method="POST",
            privacy_level="CONFIGURABLE",
            intelligence_level="ENHANCED"
        )
        
        # Domain-specific search
        self.tools["voyage_domain_search"] = MCPTool(
            name="voyage_domain_search",
            description="Domain-specialized search (finance, healthcare, legal, code)",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "domain": {"type": "string", "enum": ["CODE", "FINANCE", "HEALTHCARE", "LEGAL"], "description": "Specialized domain"},
                    "privacy_level": {"type": "string", "enum": ["PUBLIC", "CONFIDENTIAL"], "default": "PUBLIC"},
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["query", "domain"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "results": {"type": "array"},
                    "domain": {"type": "string"},
                    "model_used": {"type": "string"},
                    "privacy_compliant": {"type": "boolean"}
                }
            },
            endpoint="/voyage/search/domain",
            method="POST",
            privacy_level="CONFIGURABLE",
            intelligence_level="COGNITIVE"
        )
    
    def _register_ref_tools(self):
        """Register Ref Tools MCP tools"""
        
        # Documentation search
        self.tools["ref_search_documentation"] = MCPTool(
            name="ref_search_documentation",
            description="Search internal and external documentation sources",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Documentation search query"},
                    "source_type": {"type": "string", "enum": ["AUTO", "INTERNAL", "EXTERNAL", "HYBRID"], "default": "AUTO"},
                    "privacy_level": {"type": "string", "enum": ["PUBLIC", "INTERNAL", "CONFIDENTIAL"], "default": "INTERNAL"},
                    "include_code_examples": {"type": "boolean", "default": True},
                    "max_results": {"type": "integer", "default": 10},
                    "organization": {"type": "string", "description": "Organization context"},
                    "project_context": {"type": "string", "description": "Project context"}
                },
                "required": ["query"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "results": {"type": "array"},
                    "source_used": {"type": "string"},
                    "privacy_level": {"type": "string"},
                    "search_time": {"type": "number"}
                }
            },
            endpoint="/ref/search",
            method="POST",
            privacy_level="CONFIGURABLE",
            intelligence_level="ENHANCED"
        )
        
        # URL content reading
        self.tools["ref_read_url"] = MCPTool(
            name="ref_read_url",
            description="Extract and process content from documentation URLs",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "format": "uri", "description": "URL to read"},
                    "extract_code": {"type": "boolean", "default": True, "description": "Extract code examples"}
                },
                "required": ["url"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "code_examples": {"type": "array"},
                    "word_count": {"type": "integer"},
                    "status": {"type": "string"}
                }
            },
            endpoint="/ref/read-url",
            method="POST",
            privacy_level="PUBLIC",
            intelligence_level="BASIC"
        )
    
    def _register_docs_tools(self):
        """Register Unified Documentation MCP tools"""
        
        # Supreme unified search
        self.tools["docs_unified_search"] = MCPTool(
            name="docs_unified_search",
            description="Supreme documentation intelligence across all sources (Context7 + Ref + Memory + VoyageAI)",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "documentation_type": {"type": "string", "enum": ["HYBRID", "CODE_SNIPPETS", "FULL_DOCS", "SEMANTIC_CODE"], "default": "HYBRID"},
                    "intelligence_level": {"type": "string", "enum": ["BASIC", "ENHANCED", "COGNITIVE", "SUPREME"], "default": "ENHANCED"},
                    "privacy_level": {"type": "string", "enum": ["PUBLIC", "INTERNAL", "CONFIDENTIAL"], "default": "INTERNAL"},
                    "include_code": {"type": "boolean", "default": True},
                    "max_results_per_source": {"type": "integer", "default": 5},
                    "project_context": {"type": "string"},
                    "organization": {"type": "string"}
                },
                "required": ["query"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "results": {"type": "array"},
                    "sources_used": {"type": "array"},
                    "intelligence_level": {"type": "string"},
                    "privacy_compliant": {"type": "boolean"},
                    "cost_analysis": {"type": "object"}
                }
            },
            endpoint="/docs/unified-search",
            method="POST",
            privacy_level="CONFIGURABLE",
            intelligence_level="SUPREME"
        )
    
    def _register_actions_tools(self):
        """Register Actions MCP tools"""
        
        # List available actions
        self.tools["actions_list"] = MCPTool(
            name="actions_list",
            description="List all available external actions",
            input_schema={
                "type": "object",
                "properties": {},
                "required": []
            },
            output_schema={
                "type": "object",
                "properties": {
                    "actions": {"type": "array"},
                    "total": {"type": "integer"},
                    "timestamp": {"type": "string"}
                }
            },
            endpoint="/actions/list",
            method="GET",
            privacy_level="PUBLIC",
            intelligence_level="BASIC"
        )
        
        # Execute external action
        self.tools["actions_execute"] = MCPTool(
            name="actions_execute",
            description="Execute external action with parameters",
            input_schema={
                "type": "object",
                "properties": {
                    "action_id": {"type": "string", "description": "Action ID to execute"},
                    "parameters": {"type": "object", "description": "Action parameters"},
                    "user_id": {"type": "string", "description": "User ID for authorization", "default": "system"}
                },
                "required": ["action_id", "parameters"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "execution_id": {"type": "string"},
                    "result": {"type": "object"},
                    "error": {"type": "string"}
                }
            },
            endpoint="/actions/execute",
            method="POST",
            privacy_level="CONFIGURABLE",
            intelligence_level="ENHANCED"
        )
        
        # Escalate to human
        self.tools["actions_escalate_human"] = MCPTool(
            name="actions_escalate_human",
            description="Escalate issue to human for approval or intervention",
            input_schema={
                "type": "object",
                "properties": {
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"], "default": "medium"},
                    "message": {"type": "string", "description": "Escalation message"},
                    "context": {"type": "object", "description": "Additional context"},
                    "approvers": {"type": "array", "items": {"type": "string"}, "description": "Approver IDs"}
                },
                "required": ["message"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "escalation_id": {"type": "string"},
                    "approval_url": {"type": "string"}
                }
            },
            endpoint="/actions/escalate",
            method="POST",
            privacy_level="INTERNAL",
            intelligence_level="BASIC"
        )
        
        # Send notification
        self.tools["actions_send_notification"] = MCPTool(
            name="actions_send_notification",
            description="Send notification via email or Slack",
            input_schema={
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "enum": ["email", "slack"], "default": "email"},
                    "recipient": {"type": "string", "description": "Recipient address/ID"},
                    "subject": {"type": "string", "description": "Message subject"},
                    "message": {"type": "string", "description": "Message content"},
                    "priority": {"type": "string", "enum": ["low", "normal", "high"], "default": "normal"}
                },
                "required": ["recipient", "message"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message_id": {"type": "string"},
                    "delivery_status": {"type": "string"}
                }
            },
            endpoint="/actions/notify",
            method="POST",
            privacy_level="INTERNAL",
            intelligence_level="BASIC"
        )
        
        # Trigger external workflow
        self.tools["actions_trigger_workflow"] = MCPTool(
            name="actions_trigger_workflow",
            description="Trigger external workflow (Jenkins, GitHub Actions, etc.)",
            input_schema={
                "type": "object",
                "properties": {
                    "workflow_type": {"type": "string", "enum": ["jenkins", "github_actions", "gitlab_ci"], "default": "jenkins"},
                    "job_name": {"type": "string", "description": "Job/workflow name"},
                    "parameters": {"type": "object", "description": "Workflow parameters"}
                },
                "required": ["job_name"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "workflow_id": {"type": "string"},
                    "execution_url": {"type": "string"}
                }
            },
            endpoint="/actions/workflow",
            method="POST",
            privacy_level="INTERNAL",
            intelligence_level="BASIC"
        )
        
        # Create external ticket
        self.tools["actions_create_ticket"] = MCPTool(
            name="actions_create_ticket",
            description="Create ticket in external system (Jira, GitHub Issues)",
            input_schema={
                "type": "object",
                "properties": {
                    "system": {"type": "string", "enum": ["jira", "github"], "default": "jira"},
                    "title": {"type": "string", "description": "Ticket title"},
                    "description": {"type": "string", "description": "Ticket description"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"},
                    "assignee": {"type": "string", "description": "Assignee username"}
                },
                "required": ["title", "description"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "ticket_id": {"type": "string"},
                    "ticket_url": {"type": "string"}
                }
            },
            endpoint="/actions/ticket",
            method="POST",
            privacy_level="INTERNAL",
            intelligence_level="BASIC"
        )
        
        # Run security scan
        self.tools["actions_security_scan"] = MCPTool(
            name="actions_security_scan",
            description="Run security scan using external tools",
            input_schema={
                "type": "object",
                "properties": {
                    "scan_type": {"type": "string", "enum": ["vulnerability", "code_analysis", "dependency"], "default": "vulnerability"},
                    "target": {"type": "string", "description": "Scan target"},
                    "tool": {"type": "string", "enum": ["sonarqube", "snyk", "veracode"], "default": "sonarqube"}
                },
                "required": ["target"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "scan_id": {"type": "string"},
                    "findings": {"type": "array"},
                    "report_url": {"type": "string"}
                }
            },
            endpoint="/actions/security",
            method="POST",
            privacy_level="INTERNAL",
            intelligence_level="ENHANCED"
        )
    
    def _add_mcp_endpoints(self):
        """Add MCP protocol endpoints to FastAPI app"""
        
        @self.app.get("/mcp/tools", tags=["MCP"])
        async def list_mcp_tools():
            """List all available MCP tools"""
            return {
                "tools": [asdict(tool) for tool in self.tools.values()],
                "total_tools": len(self.tools),
                "categories": self.tool_categories,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.get("/mcp/tools/{tool_name}", tags=["MCP"])
        async def get_mcp_tool(tool_name: str):
            """Get specific MCP tool definition"""
            if tool_name not in self.tools:
                raise HTTPException(status_code=404, detail=f"MCP tool '{tool_name}' not found")
            
            return {
                "tool": asdict(self.tools[tool_name]),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.get("/mcp/schema", tags=["MCP"])
        async def get_mcp_schema():
            """Get complete MCP schema for all tools"""
            schema = {
                "version": "2024-11-05",
                "protocol": "mcp",
                "tools": {},
                "server_info": {
                    "name": "ultramcp-unified-backend",
                    "version": "2.0.0",
                    "description": "UltraMCP Unified Backend with native MCP protocol support"
                }
            }
            
            for tool_name, tool in self.tools.items():
                schema["tools"][tool_name] = {
                    "description": tool.description,
                    "inputSchema": tool.input_schema,
                    "outputSchema": tool.output_schema
                }
            
            return schema
        
        @self.app.post("/mcp/execute/{tool_name}", tags=["MCP"])
        async def execute_mcp_tool(tool_name: str, arguments: Dict[str, Any]):
            """Execute MCP tool with given arguments"""
            if tool_name not in self.tools:
                raise HTTPException(status_code=404, detail=f"MCP tool '{tool_name}' not found")
            
            tool = self.tools[tool_name]
            
            # Forward to appropriate endpoint
            import httpx
            
            async with httpx.AsyncClient() as client:
                if tool.method == "POST":
                    response = await client.post(
                        f"http://sam.chat:8000{tool.endpoint}",
                        json=arguments
                    )
                else:
                    response = await client.get(
                        f"http://sam.chat:8000{tool.endpoint}",
                        params=arguments
                    )
                
                if response.status_code == 200:
                    return {
                        "result": response.json(),
                        "tool_name": tool_name,
                        "execution_time": datetime.utcnow().isoformat()
                    }
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Tool execution failed: {response.text}"
                    )
        
        @self.app.get("/mcp/capabilities", tags=["MCP"])
        async def get_mcp_capabilities():
            """Get MCP server capabilities"""
            return {
                "capabilities": {
                    "tools": True,
                    "resources": False,
                    "prompts": True,
                    "experimental": {
                        "enhanced_intelligence": True,
                        "privacy_aware_processing": True,
                        "domain_specialization": True,
                        "cost_optimization": True
                    }
                },
                "server_info": {
                    "name": "ultramcp-unified-backend",
                    "version": "2.0.0",
                    "protocol_version": "2024-11-05"
                },
                "features": [
                    "chain_of_debate",
                    "semantic_code_search",
                    "voyage_ai_embeddings", 
                    "documentation_intelligence",
                    "unified_orchestration",
                    "privacy_first_processing",
                    "enterprise_grade_security"
                ]
            }
    
    def get_tool(self, name: str) -> Optional[MCPTool]:
        """Get MCP tool by name"""
        return self.tools.get(name)
    
    def list_tools(self) -> Dict[str, MCPTool]:
        """List all registered MCP tools"""
        return self.tools.copy()
    
    def get_tools_by_category(self, category: str) -> Dict[str, MCPTool]:
        """Get tools by category"""
        return {
            name: tool for name, tool in self.tools.items()
            if name.startswith(category)
        }