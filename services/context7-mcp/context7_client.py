#!/usr/bin/env python3

"""
UltraMCP Context7 Client
Python client for Context7 MCP service integration
"""

import asyncio
import aiohttp
import json
import logging
import re
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DocumentationRequest:
    """Documentation request structure"""
    library: str
    version: Optional[str] = None
    query: Optional[str] = None
    type: str = 'api'  # api, examples, guides, reference
    format: str = 'markdown'  # markdown, json, text

@dataclass
class DocumentationResponse:
    """Documentation response structure"""
    success: bool
    library: str
    version: str
    documentation: str
    examples: List[Dict[str, str]]
    timestamp: str
    source: str
    cached: bool = False
    error: Optional[str] = None

class Context7Client:
    """
    Client for Context7 MCP service
    
    Provides high-level interface for retrieving real-time documentation
    """
    
    def __init__(self, base_url: str = "http://localhost:8003", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = None
        self.logger = logging.getLogger(f"{__name__}.Context7Client")
        
        # Library detection patterns
        self.library_patterns = [
            r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'require\([\'"]([^\'"]+)[\'"]\)',
            r'from\s+[\'"]([^\'"]+)[\'"]',
            r'@([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)',
            r'npm\s+install\s+([a-zA-Z0-9_-]+)',
            r'yarn\s+add\s+([a-zA-Z0-9_-]+)',
            r'pip\s+install\s+([a-zA-Z0-9_-]+)',
            r'poetry\s+add\s+([a-zA-Z0-9_-]+)'
        ]
        
        # Popular libraries for quick detection
        self.popular_libraries = [
            'react', 'vue', 'angular', 'express', 'fastify', 'next',
            'nuxt', 'svelte', 'typescript', 'lodash', 'moment', 'axios',
            'prisma', 'mongoose', 'sequelize', 'tailwind', 'bootstrap',
            'material-ui', 'chakra-ui', 'framer-motion', 'three', 'd3',
            'flask', 'django', 'fastapi', 'pandas', 'numpy', 'tensorflow',
            'pytorch', 'scikit-learn', 'requests', 'beautifulsoup4'
        ]

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to Context7 service"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.content_type == 'application/json':
                    data = await response.json()
                else:
                    text = await response.text()
                    data = {"text": text}
                
                if response.status >= 400:
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=data.get('error', 'Unknown error')
                    )
                
                return data
        
        except aiohttp.ClientError as e:
            self.logger.error(f"Request failed: {e}")
            raise

    async def get_documentation(self, request: DocumentationRequest) -> DocumentationResponse:
        """
        Get documentation for a single library
        
        Args:
            request: Documentation request object
            
        Returns:
            DocumentationResponse object
        """
        try:
            data = await self._make_request(
                'POST',
                '/api/documentation',
                json=asdict(request)
            )
            
            if data['success']:
                doc_data = data['data']
                return DocumentationResponse(
                    success=True,
                    library=doc_data['library'],
                    version=doc_data['version'],
                    documentation=doc_data['documentation'],
                    examples=doc_data.get('examples', []),
                    timestamp=doc_data['timestamp'],
                    source=doc_data['source'],
                    cached=doc_data.get('cached', False)
                )
            else:
                return DocumentationResponse(
                    success=False,
                    library=request.library,
                    version=request.version or 'unknown',
                    documentation='',
                    examples=[],
                    timestamp=datetime.now().isoformat(),
                    source='error',
                    error=data.get('error', 'Unknown error')
                )
        
        except Exception as e:
            self.logger.error(f"Failed to get documentation for {request.library}: {e}")
            return DocumentationResponse(
                success=False,
                library=request.library,
                version=request.version or 'unknown',
                documentation='',
                examples=[],
                timestamp=datetime.now().isoformat(),
                source='error',
                error=str(e)
            )

    async def get_batch_documentation(self, requests: List[DocumentationRequest]) -> List[DocumentationResponse]:
        """
        Get documentation for multiple libraries in batch
        
        Args:
            requests: List of documentation request objects
            
        Returns:
            List of DocumentationResponse objects
        """
        try:
            data = await self._make_request(
                'POST',
                '/api/documentation/batch',
                json={'requests': [asdict(req) for req in requests]}
            )
            
            responses = []
            for result in data['data']:
                if result['success']:
                    doc_data = result['data']
                    responses.append(DocumentationResponse(
                        success=True,
                        library=doc_data['library'],
                        version=doc_data['version'],
                        documentation=doc_data['documentation'],
                        examples=doc_data.get('examples', []),
                        timestamp=doc_data['timestamp'],
                        source=doc_data['source'],
                        cached=doc_data.get('cached', False)
                    ))
                else:
                    req = result['request']
                    responses.append(DocumentationResponse(
                        success=False,
                        library=req['library'],
                        version=req.get('version', 'unknown'),
                        documentation='',
                        examples=[],
                        timestamp=datetime.now().isoformat(),
                        source='error',
                        error=result.get('error', 'Unknown error')
                    ))
            
            return responses
        
        except Exception as e:
            self.logger.error(f"Failed to get batch documentation: {e}")
            # Return error responses for all requests
            return [
                DocumentationResponse(
                    success=False,
                    library=req.library,
                    version=req.version or 'unknown',
                    documentation='',
                    examples=[],
                    timestamp=datetime.now().isoformat(),
                    source='error',
                    error=str(e)
                )
                for req in requests
            ]

    async def search_documentation(self, library: str, query: str) -> DocumentationResponse:
        """
        Search documentation for specific content
        
        Args:
            library: Library name
            query: Search query
            
        Returns:
            DocumentationResponse object
        """
        try:
            data = await self._make_request(
                'GET',
                '/api/documentation/search',
                params={'library': library, 'query': query}
            )
            
            if data['success']:
                doc_data = data['data']
                return DocumentationResponse(
                    success=True,
                    library=doc_data['library'],
                    version=doc_data['version'],
                    documentation=doc_data['documentation'],
                    examples=doc_data.get('examples', []),
                    timestamp=doc_data['timestamp'],
                    source=doc_data['source'],
                    cached=doc_data.get('cached', False)
                )
            else:
                return DocumentationResponse(
                    success=False,
                    library=library,
                    version='unknown',
                    documentation='',
                    examples=[],
                    timestamp=datetime.now().isoformat(),
                    source='error',
                    error=data.get('error', 'Unknown error')
                )
        
        except Exception as e:
            self.logger.error(f"Failed to search documentation for {library}: {e}")
            return DocumentationResponse(
                success=False,
                library=library,
                version='unknown',
                documentation='',
                examples=[],
                timestamp=datetime.now().isoformat(),
                source='error',
                error=str(e)
            )

    def detect_libraries_in_text(self, text: str) -> List[str]:
        """
        Detect library names mentioned in text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected library names
        """
        detected = set()
        text_lower = text.lower()
        
        # Check for popular libraries by name
        for lib in self.popular_libraries:
            if lib in text_lower:
                detected.add(lib)
        
        # Use regex patterns to detect imports/requires
        for pattern in self.library_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Clean up the match
                lib_name = match.strip()
                if lib_name and not lib_name.startswith('.') and '/' not in lib_name:
                    detected.add(lib_name)
        
        return sorted(list(detected))

    async def enhance_prompt_with_context(self, prompt: str, libraries: Optional[List[str]] = None, auto_detect: bool = True) -> Dict[str, Any]:
        """
        Enhance a prompt with Context7 documentation
        
        Args:
            prompt: Original prompt text
            libraries: Specific libraries to include (optional)
            auto_detect: Whether to auto-detect libraries from prompt
            
        Returns:
            Dictionary with enhanced prompt and metadata
        """
        try:
            data = await self._make_request(
                'POST',
                '/api/claude/context',
                json={
                    'prompt': prompt,
                    'libraries': libraries or [],
                    'autoDetect': auto_detect
                }
            )
            
            return data['data']
        
        except Exception as e:
            self.logger.error(f"Failed to enhance prompt: {e}")
            return {
                'prompt': prompt,
                'libraries': libraries or [],
                'documentation': [],
                'enhancedPrompt': prompt,
                'error': str(e)
            }

    async def get_service_health(self) -> Dict[str, Any]:
        """
        Get Context7 service health status
        
        Returns:
            Health status dictionary
        """
        try:
            return await self._make_request('GET', '/health')
        except Exception as e:
            self.logger.error(f"Failed to get service health: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    async def get_service_stats(self) -> Dict[str, Any]:
        """
        Get Context7 service statistics
        
        Returns:
            Statistics dictionary
        """
        try:
            data = await self._make_request('GET', '/api/stats')
            return data.get('data', {})
        except Exception as e:
            self.logger.error(f"Failed to get service stats: {e}")
            return {'error': str(e)}

    async def clear_cache(self, pattern: Optional[str] = None) -> Dict[str, Any]:
        """
        Clear documentation cache
        
        Args:
            pattern: Optional pattern to match for selective clearing
            
        Returns:
            Clear operation result
        """
        try:
            params = {'pattern': pattern} if pattern else {}
            return await self._make_request('DELETE', '/api/cache', params=params)
        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Convenience functions for common operations

async def get_documentation_for_library(library: str, version: Optional[str] = None) -> DocumentationResponse:
    """Get documentation for a single library"""
    async with Context7Client() as client:
        request = DocumentationRequest(library=library, version=version)
        return await client.get_documentation(request)

async def enhance_claude_prompt(prompt: str) -> str:
    """Enhance a Claude prompt with Context7 documentation"""
    async with Context7Client() as client:
        result = await client.enhance_prompt_with_context(prompt)
        return result.get('enhancedPrompt', prompt)

async def detect_and_fetch_docs(code_text: str) -> List[DocumentationResponse]:
    """Detect libraries in code and fetch their documentation"""
    async with Context7Client() as client:
        libraries = client.detect_libraries_in_text(code_text)
        if not libraries:
            return []
        
        requests = [DocumentationRequest(library=lib) for lib in libraries]
        return await client.get_batch_documentation(requests)

# CLI interface
if __name__ == '__main__':
    import argparse
    import sys

    async def main():
        parser = argparse.ArgumentParser(description='Context7 MCP Client')
        subparsers = parser.add_subparsers(dest='command', help='Available commands')

        # Get documentation command
        doc_parser = subparsers.add_parser('get', help='Get documentation for a library')
        doc_parser.add_argument('library', help='Library name')
        doc_parser.add_argument('--version', help='Library version')
        doc_parser.add_argument('--type', choices=['api', 'examples', 'guides', 'reference'], default='api')

        # Search command
        search_parser = subparsers.add_parser('search', help='Search documentation')
        search_parser.add_argument('library', help='Library name')
        search_parser.add_argument('query', help='Search query')

        # Enhance prompt command
        enhance_parser = subparsers.add_parser('enhance', help='Enhance prompt with context')
        enhance_parser.add_argument('prompt', help='Prompt text')
        enhance_parser.add_argument('--libraries', nargs='*', help='Specific libraries to include')

        # Detect libraries command
        detect_parser = subparsers.add_parser('detect', help='Detect libraries in text')
        detect_parser.add_argument('text', help='Text to analyze')

        # Health check command
        subparsers.add_parser('health', help='Check service health')

        # Stats command
        subparsers.add_parser('stats', help='Get service statistics')

        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            return

        async with Context7Client() as client:
            if args.command == 'get':
                request = DocumentationRequest(
                    library=args.library,
                    version=args.version,
                    type=args.type
                )
                response = await client.get_documentation(request)
                print(json.dumps(asdict(response), indent=2))

            elif args.command == 'search':
                response = await client.search_documentation(args.library, args.query)
                print(json.dumps(asdict(response), indent=2))

            elif args.command == 'enhance':
                result = await client.enhance_prompt_with_context(
                    args.prompt,
                    libraries=args.libraries
                )
                print(result['enhancedPrompt'])

            elif args.command == 'detect':
                libraries = client.detect_libraries_in_text(args.text)
                print(json.dumps(libraries, indent=2))

            elif args.command == 'health':
                health = await client.get_service_health()
                print(json.dumps(health, indent=2))

            elif args.command == 'stats':
                stats = await client.get_service_stats()
                print(json.dumps(stats, indent=2))

    asyncio.run(main())