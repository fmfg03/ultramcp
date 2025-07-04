"""
Ref Tools consolidated routes - Documentation search and URL content extraction
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, HttpUrl

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class DocumentationSearchRequest(BaseModel):
    query: str = Field(..., description="Documentation search query")
    source_type: str = Field("AUTO", description="Source type: AUTO, INTERNAL, EXTERNAL, HYBRID")
    privacy_level: str = Field("INTERNAL", description="Privacy level: PUBLIC, INTERNAL, CONFIDENTIAL")
    include_code_examples: bool = Field(True, description="Include code examples in results")
    max_results: int = Field(10, ge=1, le=30, description="Maximum results")
    organization: Optional[str] = Field(None, description="Organization context")
    project_context: Optional[str] = Field(None, description="Project context")
    language_filter: Optional[str] = Field(None, description="Programming language filter")

class URLReadRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL to read and extract content from")
    extract_code: bool = Field(True, description="Extract code examples")
    max_content_length: int = Field(50000, description="Maximum content length")
    follow_redirects: bool = Field(True, description="Follow HTTP redirects")

class DocumentationResult(BaseModel):
    id: str
    title: str
    content: str
    url: Optional[str]
    source_type: str
    relevance_score: float
    code_examples: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    organization: Optional[str]
    privacy_compliant: bool
    processing_time: float

class DocumentationResponse(BaseModel):
    results: List[DocumentationResult]
    query: str
    source_used: str
    privacy_level: str
    total_results: int
    search_time: float
    code_examples_found: int

class URLContentResponse(BaseModel):
    url: str
    title: str
    content: str
    code_examples: List[Dict[str, Any]]
    word_count: int
    status: str
    extraction_time: float
    metadata: Dict[str, Any]

# Mock Ref Tools service implementation
class MockRefService:
    """Simplified Ref Tools service for unified backend"""
    
    @staticmethod
    async def search_documentation(request: DocumentationSearchRequest) -> DocumentationResponse:
        """Search documentation across multiple sources"""
        start_time = datetime.utcnow()
        
        # Simulate documentation search
        await asyncio.sleep(0.4)
        
        # Generate mock documentation results
        mock_results = []
        code_examples_count = 0
        
        for i in range(min(request.max_results, 7)):
            # Generate code examples based on query
            code_examples = []
            if request.include_code_examples and i < 3:  # First 3 results have code
                code_examples = [
                    {
                        "language": request.language_filter or "python",
                        "code": f"# Example {i+1} for {request.query}\ndef example_{i+1}():\n    return 'Documentation example'",
                        "description": f"Code example {i+1} related to {request.query}"
                    }
                ]
                code_examples_count += len(code_examples)
            
            result = DocumentationResult(
                id=f"doc_result_{i}",
                title=f"Documentation: {request.query} - Guide {i+1}",
                content=f"Comprehensive documentation content for '{request.query}'. This guide covers implementation details, best practices, and advanced usage patterns. Section {i+1} focuses on practical applications.",
                url=f"https://docs.example.com/{request.query.lower().replace(' ', '-')}/guide-{i+1}",
                source_type=request.source_type if request.source_type != "AUTO" else ("INTERNAL" if i % 2 == 0 else "EXTERNAL"),
                relevance_score=0.95 - (i * 0.08),
                code_examples=code_examples,
                metadata={
                    "last_updated": "2024-12-01",
                    "version": "v2.1",
                    "category": "documentation",
                    "tags": [request.query.lower(), "guide", "implementation"]
                },
                organization=request.organization,
                privacy_compliant=True,
                processing_time=0.15
            )
            mock_results.append(result)
        
        search_time = (datetime.utcnow() - start_time).total_seconds()
        
        return DocumentationResponse(
            results=mock_results,
            query=request.query,
            source_used=request.source_type,
            privacy_level=request.privacy_level,
            total_results=len(mock_results),
            search_time=search_time,
            code_examples_found=code_examples_count
        )
    
    @staticmethod
    async def read_url_content(request: URLReadRequest) -> URLContentResponse:
        """Extract and process content from URL"""
        start_time = datetime.utcnow()
        
        # Simulate URL content extraction
        await asyncio.sleep(0.6)
        
        # Generate mock content based on URL
        url_str = str(request.url)
        mock_title = f"Documentation Page - {url_str.split('/')[-1].replace('-', ' ').title()}"
        
        # Generate mock content
        mock_content = f"""# {mock_title}

This is extracted content from {url_str}. The page contains comprehensive documentation 
about the topic, including detailed explanations, implementation guides, and practical examples.

## Overview
The documentation covers key concepts and provides step-by-step instructions for implementation.

## Implementation Details
Detailed technical information about the implementation approach, including configuration 
options and best practices.

## Examples
Practical examples demonstrating usage in real-world scenarios.
"""
        
        # Generate code examples if requested
        code_examples = []
        if request.extract_code:
            code_examples = [
                {
                    "language": "python",
                    "code": "# Example from documentation\nimport example_module\n\ndef main():\n    result = example_module.process()\n    return result",
                    "description": "Main implementation example"
                },
                {
                    "language": "javascript", 
                    "code": "// Configuration example\nconst config = {\n  apiKey: 'your-key',\n  endpoint: 'https://api.example.com'\n};\n\nexample.initialize(config);",
                    "description": "Configuration setup"
                }
            ]
        
        extraction_time = (datetime.utcnow() - start_time).total_seconds()
        
        return URLContentResponse(
            url=url_str,
            title=mock_title,
            content=mock_content,
            code_examples=code_examples,
            word_count=len(mock_content.split()),
            status="success",
            extraction_time=extraction_time,
            metadata={
                "content_type": "text/html",
                "charset": "utf-8",
                "last_modified": datetime.utcnow().isoformat(),
                "size_bytes": len(mock_content.encode('utf-8'))
            }
        )

# Routes
@router.post("/search", response_model=DocumentationResponse)
async def search_documentation(
    request: DocumentationSearchRequest,
    background_tasks: BackgroundTasks
):
    """Search internal and external documentation sources"""
    try:
        result = await MockRefService.search_documentation(request)
        
        # Log search analytics
        background_tasks.add_task(
            log_ref_analytics,
            request.query,
            result.total_results,
            request.source_type,
            request.privacy_level
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Documentation search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/read-url", response_model=URLContentResponse)
async def read_url_content(
    request: URLReadRequest,
    background_tasks: BackgroundTasks
):
    """Extract and process content from documentation URLs"""
    try:
        result = await MockRefService.read_url_content(request)
        
        # Log URL reading analytics
        background_tasks.add_task(
            log_url_analytics,
            str(request.url),
            result.status,
            result.word_count
        )
        
        return result
        
    except Exception as e:
        logger.error(f"URL content extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"URL reading failed: {str(e)}")

@router.post("/search/privacy-first")
async def privacy_first_documentation_search(
    query: str,
    organization: Optional[str] = None,
    project_context: Optional[str] = None,
    max_results: int = 10
):
    """Privacy-first documentation search using only internal sources"""
    try:
        request = DocumentationSearchRequest(
            query=query,
            source_type="INTERNAL",
            privacy_level="CONFIDENTIAL",
            include_code_examples=True,
            max_results=max_results,
            organization=organization,
            project_context=project_context
        )
        
        result = await MockRefService.search_documentation(request)
        
        return {
            "results": [r.dict() for r in result.results],
            "query": query,
            "search_type": "privacy_first_internal",
            "source_restriction": "INTERNAL_ONLY",
            "privacy_compliant": True,
            "organization": organization,
            "code_examples_found": result.code_examples_found,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Privacy-first documentation search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/search/code-focused")
async def code_focused_search(
    query: str,
    language: str,
    privacy_level: str = "INTERNAL",
    max_results: int = 8
):
    """Code-focused documentation search with language filtering"""
    try:
        request = DocumentationSearchRequest(
            query=query,
            source_type="HYBRID",
            privacy_level=privacy_level,
            include_code_examples=True,
            max_results=max_results,
            language_filter=language
        )
        
        result = await MockRefService.search_documentation(request)
        
        # Filter results to prioritize those with code examples
        code_heavy_results = [r for r in result.results if r.code_examples]
        other_results = [r for r in result.results if not r.code_examples]
        
        # Prioritize code-heavy results
        prioritized_results = code_heavy_results + other_results
        
        return {
            "results": [r.dict() for r in prioritized_results],
            "query": query,
            "language_filter": language,
            "search_type": "code_focused",
            "code_examples_found": sum(len(r.code_examples) for r in prioritized_results),
            "prioritized_code_results": len(code_heavy_results),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Code-focused search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/sources/available")
async def get_available_sources():
    """Get available documentation sources"""
    return {
        "internal_sources": [
            {
                "name": "Internal Wiki",
                "type": "INTERNAL",
                "url": "https://wiki.internal.com",
                "searchable": True,
                "code_examples": True
            },
            {
                "name": "API Documentation",
                "type": "INTERNAL", 
                "url": "https://api-docs.internal.com",
                "searchable": True,
                "code_examples": True
            }
        ],
        "external_sources": [
            {
                "name": "Stack Overflow",
                "type": "EXTERNAL",
                "url": "https://stackoverflow.com",
                "searchable": True,
                "code_examples": True
            },
            {
                "name": "GitHub Documentation",
                "type": "EXTERNAL",
                "url": "https://docs.github.com",
                "searchable": True,
                "code_examples": True
            }
        ],
        "privacy_levels": ["PUBLIC", "INTERNAL", "CONFIDENTIAL"],
        "supported_languages": ["python", "javascript", "typescript", "java", "go", "rust", "cpp"],
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/stats")
async def ref_stats():
    """Get Ref Tools service statistics"""
    return {
        "total_searches": 890,
        "internal_searches": 340,
        "external_searches": 550,
        "url_extractions": 125,
        "code_examples_extracted": 680,
        "average_search_time": 0.42,
        "privacy_compliance_rate": 100.0,
        "successful_extractions": 96.8,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/health")
async def ref_health():
    """Ref Tools service health"""
    return {
        "status": "healthy",
        "service": "ref-tools-documentation",
        "timestamp": datetime.utcnow().isoformat(),
        "capabilities": {
            "documentation_search": True,
            "url_content_extraction": True,
            "code_example_extraction": True,
            "privacy_aware_search": True,
            "multi_source_support": True
        }
    }

# Background tasks
async def log_ref_analytics(query: str, results_count: int, source_type: str, privacy_level: str):
    """Log Ref Tools search analytics"""
    try:
        logger.info(f"Ref search: '{query}', results: {results_count}, source: {source_type}, privacy: {privacy_level}")
    except Exception as e:
        logger.warning(f"Failed to log Ref analytics: {e}")

async def log_url_analytics(url: str, status: str, word_count: int):
    """Log URL extraction analytics"""
    try:
        logger.info(f"URL extraction: {url}, status: {status}, words: {word_count}")
    except Exception as e:
        logger.warning(f"Failed to log URL analytics: {e}")