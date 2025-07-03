"""
UltraMCP Client for Claude Code Memory Service
"""
import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
import argparse
import sys

logger = logging.getLogger(__name__)

@dataclass
class MemorySearchResult:
    """Result from memory search"""
    id: str
    score: float
    content: str
    file_path: str
    element_type: str
    element_name: str
    start_line: int
    end_line: int
    language: str
    context: str

@dataclass
class IndexingResult:
    """Result from project indexing"""
    project_name: str
    total_files: int
    indexed_files: int
    total_elements: int
    processing_time: float
    success: bool
    errors: List[str]

@dataclass
class PatternAnalysisResult:
    """Result from pattern analysis"""
    file_path: str
    patterns: List[Dict[str, Any]]
    quality_score: float
    recommendations: List[str]
    analysis_time: float

class ClaudeCodeMemoryClient:
    """Client for Claude Code Memory Service"""
    
    def __init__(self, base_url: str = "http://localhost:8009"):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to memory service"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
        
        except aiohttp.ClientError as e:
            raise Exception(f"Request failed: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        return await self._make_request("GET", "/health")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get service status and statistics"""
        return await self._make_request("GET", "/status")
    
    # Project Management
    async def index_project(self, 
                           project_path: str, 
                           project_name: str,
                           force_reindex: bool = False,
                           include_patterns: Optional[List[str]] = None,
                           exclude_patterns: Optional[List[str]] = None) -> IndexingResult:
        """Index a project for semantic search"""
        data = {
            "project_path": project_path,
            "project_name": project_name,
            "force_reindex": force_reindex
        }
        
        if include_patterns:
            data["include_patterns"] = include_patterns
        if exclude_patterns:
            data["exclude_patterns"] = exclude_patterns
        
        result = await self._make_request("POST", "/projects/index", json=data)
        
        return IndexingResult(
            project_name=result["project_name"],
            total_files=result["total_files"],
            indexed_files=result["indexed_files"],
            total_elements=result["total_elements"],
            processing_time=result["processing_time"],
            success=result["success"],
            errors=result.get("errors", [])
        )
    
    async def list_projects(self) -> List[Dict[str, Any]]:
        """List all indexed projects"""
        result = await self._make_request("GET", "/projects")
        return result["projects"]
    
    async def get_project_info(self, project_name: str) -> Dict[str, Any]:
        """Get information about a specific project"""
        return await self._make_request("GET", f"/projects/{project_name}")
    
    async def delete_project(self, project_name: str) -> bool:
        """Delete a project from memory"""
        result = await self._make_request("DELETE", f"/projects/{project_name}")
        return result["success"]
    
    # Semantic Search
    async def search_code(self, 
                         query: str, 
                         project_name: Optional[str] = None,
                         language: Optional[str] = None,
                         element_type: Optional[str] = None,
                         limit: int = 10,
                         score_threshold: float = 0.7) -> List[MemorySearchResult]:
        """Search for code using semantic similarity"""
        params = {
            "query": query,
            "limit": limit,
            "score_threshold": score_threshold
        }
        
        if project_name:
            params["project_name"] = project_name
        if language:
            params["language"] = language
        if element_type:
            params["element_type"] = element_type
        
        result = await self._make_request("GET", "/search", params=params)
        
        return [
            MemorySearchResult(
                id=item["id"],
                score=item["score"],
                content=item["content"],
                file_path=item["file_path"],
                element_type=item["element_type"],
                element_name=item["element_name"],
                start_line=item["start_line"],
                end_line=item["end_line"],
                language=item["language"],
                context=item.get("context", "")
            )
            for item in result["results"]
        ]
    
    async def search_similar_code(self, 
                                 code_snippet: str,
                                 language: Optional[str] = None,
                                 project_name: Optional[str] = None,
                                 limit: int = 5) -> List[MemorySearchResult]:
        """Find similar code snippets"""
        data = {
            "code_snippet": code_snippet,
            "limit": limit
        }
        
        if language:
            data["language"] = language
        if project_name:
            data["project_name"] = project_name
        
        result = await self._make_request("POST", "/search/similar", json=data)
        
        return [
            MemorySearchResult(
                id=item["id"],
                score=item["score"],
                content=item["content"],
                file_path=item["file_path"],
                element_type=item["element_type"],
                element_name=item["element_name"],
                start_line=item["start_line"],
                end_line=item["end_line"],
                language=item["language"],
                context=item.get("context", "")
            )
            for item in result["results"]
        ]
    
    # Pattern Analysis
    async def analyze_patterns(self, 
                              file_path: str,
                              project_name: Optional[str] = None) -> PatternAnalysisResult:
        """Analyze code patterns in a file"""
        data = {"file_path": file_path}
        if project_name:
            data["project_name"] = project_name
        
        result = await self._make_request("POST", "/patterns/analyze", json=data)
        
        return PatternAnalysisResult(
            file_path=result["file_path"],
            patterns=result["patterns"],
            quality_score=result.get("quality_score", 0.0),
            recommendations=result.get("recommendations", []),
            analysis_time=result["analysis_time"]
        )
    
    async def get_pattern_summary(self, project_name: str) -> Dict[str, Any]:
        """Get pattern analysis summary for a project"""
        return await self._make_request("GET", f"/patterns/summary/{project_name}")
    
    # Memory Operations
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        return await self._make_request("GET", "/memory/stats")
    
    async def clear_memory(self, 
                          project_name: Optional[str] = None,
                          confirm: bool = False) -> bool:
        """Clear memory (with confirmation)"""
        if not confirm:
            raise ValueError("Must set confirm=True to clear memory")
        
        data = {"confirm": True}
        if project_name:
            data["project_name"] = project_name
        
        result = await self._make_request("POST", "/memory/clear", json=data)
        return result["success"]
    
    # Code Intelligence
    async def get_code_context(self, 
                              file_path: str, 
                              line_number: int,
                              project_name: Optional[str] = None) -> Dict[str, Any]:
        """Get code context around a specific line"""
        params = {
            "file_path": file_path,
            "line_number": line_number
        }
        
        if project_name:
            params["project_name"] = project_name
        
        return await self._make_request("GET", "/code/context", params=params)
    
    async def suggest_improvements(self, 
                                  file_path: str,
                                  project_name: Optional[str] = None) -> Dict[str, Any]:
        """Get improvement suggestions for a file"""
        data = {"file_path": file_path}
        if project_name:
            data["project_name"] = project_name
        
        return await self._make_request("POST", "/code/suggestions", json=data)
    
    async def find_usage(self, 
                        symbol_name: str,
                        project_name: Optional[str] = None,
                        language: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find usage of a symbol across the codebase"""
        params = {"symbol_name": symbol_name}
        
        if project_name:
            params["project_name"] = project_name
        if language:
            params["language"] = language
        
        result = await self._make_request("GET", "/code/usage", params=params)
        return result["usages"]

# CLI Interface
class ClaudeCLI:
    """Command line interface for Claude Code Memory"""
    
    def __init__(self):
        self.client = ClaudeCodeMemoryClient()
    
    async def run_command(self, args):
        """Run CLI command"""
        async with self.client:
            if args.command == "index":
                await self._index_command(args)
            elif args.command == "search":
                await self._search_command(args)
            elif args.command == "analyze":
                await self._analyze_command(args)
            elif args.command == "status":
                await self._status_command(args)
            elif args.command == "projects":
                await self._projects_command(args)
            else:
                print(f"Unknown command: {args.command}")
    
    async def _index_command(self, args):
        """Handle index command"""
        try:
            print(f"Indexing project: {args.path}")
            result = await self.client.index_project(
                project_path=args.path,
                project_name=args.name,
                force_reindex=args.force
            )
            
            if result.success:
                print(f"✅ Indexing completed successfully!")
                print(f"   Files processed: {result.indexed_files}/{result.total_files}")
                print(f"   Elements indexed: {result.total_elements}")
                print(f"   Processing time: {result.processing_time:.2f}s")
            else:
                print(f"❌ Indexing failed!")
                for error in result.errors:
                    print(f"   Error: {error}")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def _search_command(self, args):
        """Handle search command"""
        try:
            print(f"Searching for: {args.query}")
            results = await self.client.search_code(
                query=args.query,
                project_name=args.project,
                language=args.language,
                limit=args.limit
            )
            
            if results:
                print(f"Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. {result.element_name} ({result.element_type})")
                    print(f"   File: {result.file_path}:{result.start_line}")
                    print(f"   Score: {result.score:.3f}")
                    print(f"   Language: {result.language}")
                    if args.show_content:
                        content_preview = result.content[:200] + "..." if len(result.content) > 200 else result.content
                        print(f"   Content: {content_preview}")
            else:
                print("No results found.")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def _analyze_command(self, args):
        """Handle analyze command"""
        try:
            print(f"Analyzing patterns in: {args.file}")
            result = await self.client.analyze_patterns(
                file_path=args.file,
                project_name=args.project
            )
            
            print(f"Analysis completed in {result.analysis_time:.2f}s")
            print(f"Quality score: {result.quality_score:.1f}/100")
            
            if result.patterns:
                print(f"\nFound {len(result.patterns)} patterns:")
                for pattern in result.patterns:
                    print(f"  • {pattern['name']} ({pattern['type']}) - {pattern['severity']}")
                    print(f"    Confidence: {pattern['confidence']:.2f}")
                    print(f"    {pattern['description']}")
            
            if result.recommendations:
                print(f"\nRecommendations:")
                for rec in result.recommendations:
                    print(f"  • {rec}")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def _status_command(self, args):
        """Handle status command"""
        try:
            health = await self.client.health_check()
            status = await self.client.get_status()
            stats = await self.client.get_memory_stats()
            
            print("🔍 Claude Code Memory Status")
            print(f"Service: {'✅ Healthy' if health.get('status') == 'healthy' else '❌ Unhealthy'}")
            print(f"Memory Usage: {stats.get('memory_usage', {}).get('total_mb', 0):.1f}MB")
            print(f"Indexed Projects: {status.get('total_projects', 0)}")
            print(f"Total Elements: {status.get('total_elements', 0)}")
            print(f"Vector Database: {'✅ Connected' if stats.get('vector_db', {}).get('connected') else '❌ Disconnected'}")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def _projects_command(self, args):
        """Handle projects command"""
        try:
            projects = await self.client.list_projects()
            
            if projects:
                print(f"📁 Indexed Projects ({len(projects)}):")
                for project in projects:
                    print(f"  • {project['name']}")
                    print(f"    Path: {project['path']}")
                    print(f"    Files: {project['file_count']}")
                    print(f"    Elements: {project['element_count']}")
                    print(f"    Last updated: {project['last_updated']}")
                    print()
            else:
                print("No indexed projects found.")
        
        except Exception as e:
            print(f"❌ Error: {e}")

def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(description="Claude Code Memory Client")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Index command
    index_parser = subparsers.add_parser("index", help="Index a project")
    index_parser.add_argument("path", help="Project path to index")
    index_parser.add_argument("name", help="Project name")
    index_parser.add_argument("--force", action="store_true", help="Force reindexing")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search code")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--project", help="Project name to search in")
    search_parser.add_argument("--language", help="Programming language filter")
    search_parser.add_argument("--limit", type=int, default=10, help="Maximum results")
    search_parser.add_argument("--show-content", action="store_true", help="Show code content")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze code patterns")
    analyze_parser.add_argument("file", help="File path to analyze")
    analyze_parser.add_argument("--project", help="Project name")
    
    # Status command
    subparsers.add_parser("status", help="Show service status")
    
    # Projects command
    subparsers.add_parser("projects", help="List indexed projects")
    
    return parser

async def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = ClaudeCLI()
    await cli.run_command(args)

if __name__ == "__main__":
    asyncio.run(main())