#!/usr/bin/env python3
"""
Ref Tools MCP Service for UltraMCP Supreme Stack
Complete documentation intelligence with internal/external source management
"""

import asyncio
import logging
import os
import json
import aiohttp
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentationSource(Enum):
    """Types of documentation sources"""
    INTERNAL = "internal"           # Private organizational docs
    EXTERNAL = "external"           # Public APIs, libraries
    HYBRID = "hybrid"              # Mixed internal/external
    AUTO = "auto"                  # Intelligent source selection

class PrivacyLevel(Enum):
    """Privacy levels for documentation access"""
    PUBLIC = "public"               # External APIs, open source
    INTERNAL = "internal"           # Company documentation
    CONFIDENTIAL = "confidential"   # Sensitive internal docs
    RESTRICTED = "restricted"       # Highly sensitive documents

@dataclass
class DocumentationSearchRequest:
    """Request for documentation search"""
    query: str
    source_type: DocumentationSource = DocumentationSource.AUTO
    privacy_level: PrivacyLevel = PrivacyLevel.INTERNAL
    include_code_examples: bool = True
    max_results: int = 10
    organization: Optional[str] = None
    project_context: Optional[str] = None
    
@dataclass
class DocumentationResult:
    """Single documentation search result"""
    title: str
    url: str
    content: str
    source_type: str
    relevance_score: float
    last_updated: Optional[str]
    section: Optional[str] = None
    code_examples: List[str] = None
    privacy_compliant: bool = True

@dataclass
class SearchResponse:
    """Complete search response"""
    results: List[DocumentationResult]
    query: str
    source_used: str
    total_results: int
    search_time: float
    privacy_level: str
    cached: bool = False

class DocumentationCache:
    """Intelligent caching for documentation results"""
    
    def __init__(self, max_size: int = 5000, ttl_hours: int = 24):
        self.cache = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_hours * 3600
        
    def _generate_key(self, query: str, source_type: str, privacy_level: str) -> str:
        """Generate cache key"""
        content = f"{query}:{source_type}:{privacy_level}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, query: str, source_type: str, privacy_level: str) -> Optional[SearchResponse]:
        """Get cached result"""
        key = self._generate_key(query, source_type, privacy_level)
        if key in self.cache:
            result, timestamp = self.cache[key]
            if datetime.now().timestamp() - timestamp < self.ttl_seconds:
                result.cached = True
                return result
            else:
                del self.cache[key]
        return None
    
    def set(self, query: str, source_type: str, privacy_level: str, response: SearchResponse):
        """Cache search result"""
        if len(self.cache) >= self.max_size:
            # Simple LRU eviction
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        key = self._generate_key(query, source_type, privacy_level)
        self.cache[key] = (response, datetime.now().timestamp())

class DocumentationSourceManager:
    """Manages different documentation sources"""
    
    def __init__(self):
        self.internal_sources = []
        self.external_sources = []
        self.api_keys = {}
        self._load_configuration()
    
    def _load_configuration(self):
        """Load documentation source configuration"""
        # Internal documentation sources
        self.internal_sources = [
            {
                "name": "Internal API Docs",
                "url_pattern": os.getenv("INTERNAL_DOCS_URL", "https://docs.internal.company.com"),
                "auth_required": True,
                "privacy_level": "confidential"
            },
            {
                "name": "Team Wiki",
                "url_pattern": os.getenv("TEAM_WIKI_URL", "https://wiki.internal.company.com"),
                "auth_required": True,
                "privacy_level": "internal"
            },
            {
                "name": "Architecture Decision Records",
                "url_pattern": os.getenv("ADR_URL", "https://adr.internal.company.com"),
                "auth_required": True,
                "privacy_level": "internal"
            }
        ]
        
        # External documentation sources
        self.external_sources = [
            {
                "name": "GitHub Documentation",
                "search_url": "https://docs.github.com",
                "api_search": True
            },
            {
                "name": "FastAPI Documentation", 
                "search_url": "https://fastapi.tiangolo.com",
                "api_search": False
            },
            {
                "name": "React Documentation",
                "search_url": "https://react.dev",
                "api_search": False
            },
            {
                "name": "Python Documentation",
                "search_url": "https://docs.python.org",
                "api_search": True
            }
        ]
        
        # Load API keys
        self.api_keys = {
            "github": os.getenv("GITHUB_TOKEN"),
            "internal_docs": os.getenv("INTERNAL_DOCS_API_KEY")
        }

class RefToolsClient:
    """Client for Ref Tools MCP functionality"""
    
    def __init__(self):
        self.session = None
        self.source_manager = DocumentationSourceManager()
        self.cache = DocumentationCache()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_documentation(self, request: DocumentationSearchRequest) -> SearchResponse:
        """Search documentation using Ref Tools approach"""
        start_time = datetime.now()
        
        # Check cache first
        cached_result = self.cache.get(
            request.query, 
            request.source_type.value, 
            request.privacy_level.value
        )
        if cached_result:
            return cached_result
        
        # Determine source strategy
        sources_to_search = self._select_sources(request)
        
        # Perform search across selected sources
        all_results = []
        for source in sources_to_search:
            try:
                source_results = await self._search_source(source, request)
                all_results.extend(source_results)
            except Exception as e:
                logger.warning(f"Search failed for source {source.get('name', 'unknown')}: {e}")
        
        # Sort by relevance and limit results
        all_results.sort(key=lambda x: x.relevance_score, reverse=True)
        final_results = all_results[:request.max_results]
        
        # Create response
        search_time = (datetime.now() - start_time).total_seconds()
        response = SearchResponse(
            results=final_results,
            query=request.query,
            source_used=request.source_type.value,
            total_results=len(final_results),
            search_time=search_time,
            privacy_level=request.privacy_level.value,
            cached=False
        )
        
        # Cache the response
        self.cache.set(
            request.query,
            request.source_type.value, 
            request.privacy_level.value,
            response
        )
        
        return response
    
    def _select_sources(self, request: DocumentationSearchRequest) -> List[Dict]:
        """Select appropriate documentation sources based on request"""
        if request.source_type == DocumentationSource.INTERNAL:
            return [s for s in self.source_manager.internal_sources 
                   if self._privacy_compatible(s, request.privacy_level)]
        
        elif request.source_type == DocumentationSource.EXTERNAL:
            return self.source_manager.external_sources
        
        elif request.source_type == DocumentationSource.AUTO:
            # Intelligent source selection based on query content
            if any(keyword in request.query.lower() for keyword in 
                   ['internal', 'company', 'team', 'private', 'our api', 'internal api']):
                return [s for s in self.source_manager.internal_sources 
                       if self._privacy_compatible(s, request.privacy_level)]
            else:
                return self.source_manager.external_sources
        
        else:  # HYBRID
            sources = []
            if request.privacy_level in [PrivacyLevel.PUBLIC, PrivacyLevel.INTERNAL]:
                sources.extend(self.source_manager.external_sources)
            sources.extend([s for s in self.source_manager.internal_sources 
                           if self._privacy_compatible(s, request.privacy_level)])
            return sources
    
    def _privacy_compatible(self, source: Dict, privacy_level: PrivacyLevel) -> bool:
        """Check if source is compatible with privacy level"""
        source_privacy = source.get('privacy_level', 'public')
        
        privacy_hierarchy = {
            'public': 0,
            'internal': 1, 
            'confidential': 2,
            'restricted': 3
        }
        
        user_level = privacy_hierarchy.get(privacy_level.value, 0)
        source_level = privacy_hierarchy.get(source_privacy, 0)
        
        return user_level >= source_level
    
    async def _search_source(self, source: Dict, request: DocumentationSearchRequest) -> List[DocumentationResult]:
        """Search a specific documentation source"""
        results = []
        
        try:
            if source.get('api_search'):
                # Use API-based search if available
                results = await self._api_search(source, request)
            else:
                # Fallback to web search and content extraction
                results = await self._web_search(source, request)
                
        except Exception as e:
            logger.error(f"Source search failed for {source.get('name')}: {e}")
        
        return results
    
    async def _api_search(self, source: Dict, request: DocumentationSearchRequest) -> List[DocumentationResult]:
        """Perform API-based documentation search"""
        results = []
        
        # Implementation varies by source type
        source_name = source.get('name', '').lower()
        
        if 'github' in source_name:
            results = await self._search_github_docs(request)
        elif 'python' in source_name:
            results = await self._search_python_docs(request)
        else:
            # Generic web search fallback
            results = await self._web_search(source, request)
        
        return results
    
    async def _search_github_docs(self, request: DocumentationSearchRequest) -> List[DocumentationResult]:
        """Search GitHub documentation"""
        results = []
        
        if not self.source_manager.api_keys.get('github'):
            logger.warning("GitHub API key not configured")
            return results
        
        try:
            # GitHub API search for documentation
            headers = {
                'Authorization': f"token {self.source_manager.api_keys['github']}",
                'Accept': 'application/vnd.github.v3+json'
            }
            
            search_url = f"https://api.github.com/search/code"
            params = {
                'q': f"{request.query} in:file extension:md",
                'per_page': request.max_results
            }
            
            async with self.session.get(search_url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for item in data.get('items', []):
                        # Fetch file content
                        content = await self._fetch_github_file_content(item, headers)
                        
                        result = DocumentationResult(
                            title=item.get('name', 'GitHub Documentation'),
                            url=item.get('html_url', ''),
                            content=content[:2000],  # Truncate for efficiency
                            source_type='external',
                            relevance_score=self._calculate_relevance(content, request.query),
                            last_updated=None,
                            privacy_compliant=True
                        )
                        results.append(result)
                        
        except Exception as e:
            logger.error(f"GitHub search failed: {e}")
        
        return results
    
    async def _fetch_github_file_content(self, item: Dict, headers: Dict) -> str:
        """Fetch content of a GitHub file"""
        try:
            content_url = item.get('url', '')
            async with self.session.get(content_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    # Decode base64 content
                    import base64
                    content = base64.b64decode(data.get('content', '')).decode('utf-8')
                    return content
        except Exception as e:
            logger.warning(f"Failed to fetch GitHub file content: {e}")
        
        return ""
    
    async def _search_python_docs(self, request: DocumentationSearchRequest) -> List[DocumentationResult]:
        """Search Python documentation"""
        results = []
        
        try:
            # Use Python documentation search
            search_url = "https://docs.python.org/3/search.html"
            params = {'q': request.query}
            
            async with self.session.get(search_url, params=params) as response:
                if response.status == 200:
                    # Parse search results (simplified implementation)
                    content = await response.text()
                    
                    # Extract relevant documentation links and content
                    # This is a simplified implementation - in practice, you'd parse HTML
                    result = DocumentationResult(
                        title=f"Python Documentation: {request.query}",
                        url=f"https://docs.python.org/3/search.html?q={request.query}",
                        content=f"Python documentation search results for: {request.query}",
                        source_type='external',
                        relevance_score=0.8,
                        last_updated=None,
                        privacy_compliant=True
                    )
                    results.append(result)
                    
        except Exception as e:
            logger.error(f"Python docs search failed: {e}")
        
        return results
    
    async def _web_search(self, source: Dict, request: DocumentationSearchRequest) -> List[DocumentationResult]:
        """Perform web-based search and content extraction"""
        results = []
        
        try:
            # Construct search URL
            base_url = source.get('search_url', '')
            search_query = f"site:{base_url} {request.query}"
            
            # Use Google Search API or fallback to direct site search
            # This is a simplified implementation
            result = DocumentationResult(
                title=f"{source.get('name', 'Documentation')}: {request.query}",
                url=f"{base_url}/search?q={request.query}",
                content=f"Documentation search for {request.query} in {source.get('name')}",
                source_type='external' if 'internal' not in source.get('name', '').lower() else 'internal',
                relevance_score=0.7,
                last_updated=None,
                privacy_compliant=True
            )
            results.append(result)
            
        except Exception as e:
            logger.error(f"Web search failed for {source.get('name')}: {e}")
        
        return results
    
    def _calculate_relevance(self, content: str, query: str) -> float:
        """Calculate relevance score for content"""
        if not content or not query:
            return 0.0
        
        content_lower = content.lower()
        query_terms = query.lower().split()
        
        # Simple relevance calculation
        score = 0.0
        for term in query_terms:
            if term in content_lower:
                score += 1.0 / len(query_terms)
        
        # Boost score for exact phrase matches
        if query.lower() in content_lower:
            score += 0.2
        
        return min(score, 1.0)
    
    async def read_url(self, url: str, extract_code: bool = True) -> Dict[str, Any]:
        """Read and extract content from URL (ref_read_url functionality)"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Extract readable content and convert to markdown
                    # This is a simplified implementation - in practice, you'd use
                    # libraries like BeautifulSoup, readability, or html2text
                    
                    extracted_content = self._extract_readable_content(content)
                    code_examples = self._extract_code_examples(content) if extract_code else []
                    
                    return {
                        'url': url,
                        'title': self._extract_title(content),
                        'content': extracted_content,
                        'code_examples': code_examples,
                        'status': 'success',
                        'word_count': len(extracted_content.split())
                    }
                else:
                    return {
                        'url': url,
                        'error': f"HTTP {response.status}",
                        'status': 'error'
                    }
                    
        except Exception as e:
            logger.error(f"URL reading failed for {url}: {e}")
            return {
                'url': url,
                'error': str(e),
                'status': 'error'
            }
    
    def _extract_readable_content(self, html: str) -> str:
        """Extract readable content from HTML"""
        # Simplified implementation - remove HTML tags and clean up
        import re
        
        # Remove script and style elements
        html = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text[:5000]  # Limit content size
    
    def _extract_title(self, html: str) -> str:
        """Extract title from HTML"""
        import re
        
        title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()
        
        return "Documentation"
    
    def _extract_code_examples(self, html: str) -> List[str]:
        """Extract code examples from HTML"""
        import re
        
        # Find code blocks
        code_patterns = [
            r'<code[^>]*>(.*?)</code>',
            r'<pre[^>]*>(.*?)</pre>',
            r'```[^`]*```'
        ]
        
        code_examples = []
        for pattern in code_patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            for match in matches:
                clean_code = re.sub(r'<[^>]+>', '', match).strip()
                if len(clean_code) > 20:  # Only include substantial code examples
                    code_examples.append(clean_code[:500])  # Limit code size
        
        return code_examples[:5]  # Limit number of examples

# Global client instance
ref_client: Optional[RefToolsClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global ref_client
    
    try:
        logger.info("🔗 Initializing Ref Tools MCP Service...")
        
        ref_client = RefToolsClient()
        
        logger.info("✅ Ref Tools MCP Service initialized successfully")
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Ref Tools service: {e}")
        raise
    finally:
        logger.info("🛑 Shutting down Ref Tools MCP Service...")

# FastAPI application
app = FastAPI(
    title="UltraMCP Ref Tools Service",
    description="Complete documentation intelligence with internal/external source management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class SearchRequest(BaseModel):
    query: str = Field(..., description="Documentation search query")
    source_type: DocumentationSource = Field(DocumentationSource.AUTO, description="Source type selection")
    privacy_level: PrivacyLevel = Field(PrivacyLevel.INTERNAL, description="Privacy level for search")
    include_code_examples: bool = Field(True, description="Include code examples in results")
    max_results: int = Field(10, ge=1, le=50, description="Maximum number of results")
    organization: Optional[str] = Field(None, description="Organization context")
    project_context: Optional[str] = Field(None, description="Project context")

class URLReadRequest(BaseModel):
    url: str = Field(..., description="URL to read and extract content from")
    extract_code: bool = Field(True, description="Extract code examples")

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ref-tools-mcp",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "cache_size": len(ref_client.cache.cache) if ref_client else 0
    }

@app.post("/ref/search", response_model=Dict[str, Any])
async def search_documentation(request: SearchRequest):
    """Search documentation across internal and external sources"""
    try:
        if not ref_client:
            raise HTTPException(status_code=503, detail="Ref Tools client not initialized")
        
        search_request = DocumentationSearchRequest(
            query=request.query,
            source_type=request.source_type,
            privacy_level=request.privacy_level,
            include_code_examples=request.include_code_examples,
            max_results=request.max_results,
            organization=request.organization,
            project_context=request.project_context
        )
        
        async with ref_client as client:
            response = await client.search_documentation(search_request)
        
        return asdict(response)
        
    except Exception as e:
        logger.error(f"Documentation search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ref/read-url", response_model=Dict[str, Any])
async def read_url(request: URLReadRequest):
    """Read and extract content from URL"""
    try:
        if not ref_client:
            raise HTTPException(status_code=503, detail="Ref Tools client not initialized")
        
        async with ref_client as client:
            result = await client.read_url(request.url, request.extract_code)
        
        return result
        
    except Exception as e:
        logger.error(f"URL reading failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ref/sources")
async def list_sources():
    """List available documentation sources"""
    try:
        if not ref_client:
            raise HTTPException(status_code=503, detail="Ref Tools client not initialized")
        
        return {
            "internal_sources": ref_client.source_manager.internal_sources,
            "external_sources": ref_client.source_manager.external_sources,
            "source_types": [source.value for source in DocumentationSource],
            "privacy_levels": [level.value for level in PrivacyLevel]
        }
        
    except Exception as e:
        logger.error(f"Failed to list sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ref/stats")
async def get_statistics():
    """Get service statistics"""
    try:
        if not ref_client:
            raise HTTPException(status_code=503, detail="Ref Tools client not initialized")
        
        return {
            "cache_size": len(ref_client.cache.cache),
            "max_cache_size": ref_client.cache.max_size,
            "cache_ttl_hours": ref_client.cache.ttl_seconds / 3600,
            "internal_sources_count": len(ref_client.source_manager.internal_sources),
            "external_sources_count": len(ref_client.source_manager.external_sources),
            "api_keys_configured": {
                key: bool(value) for key, value in ref_client.source_manager.api_keys.items()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("REF_SERVICE_PORT", 8011))
    uvicorn.run(
        "ref_service:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development",
        log_level="info"
    )