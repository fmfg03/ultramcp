#!/usr/bin/env python3
"""
Blockoli Code Intelligence Client for UltraMCP Integration
Provides semantic code search, pattern analysis, and intelligent code context
"""

import asyncio
import aiohttp
import json
import os
import time
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BlockoliCodeContext:
    """Client for Blockoli code intelligence engine"""
    
    def __init__(self, endpoint: str = "http://localhost:8080", api_key: Optional[str] = None):
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.session = None
        self.projects = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers=self._get_headers(),
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests"""
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers
        
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make HTTP request to Blockoli API"""
        url = f"{self.endpoint}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                async with self.session.get(url, params=data) as response:
                    response.raise_for_status()
                    return await response.json()
            else:
                async with self.session.request(method, url, json=data) as response:
                    response.raise_for_status()
                    return await response.json()
                    
        except aiohttp.ClientError as e:
            logger.error(f"Blockoli API request failed: {e}")
            raise BlockoliAPIError(f"API request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in Blockoli request: {e}")
            raise BlockoliAPIError(f"Unexpected error: {e}")
    
    async def health_check(self) -> Dict:
        """Check Blockoli service health"""
        try:
            return await self._make_request('GET', '/health')
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    async def create_project(self, project_name: str, description: str = "") -> Dict:
        """Create a new project in Blockoli"""
        data = {
            'name': project_name,
            'description': description,
            'created_at': datetime.now().isoformat()
        }
        
        result = await self._make_request('POST', '/projects', data)
        
        self.projects[project_name] = {
            'id': result.get('id'),
            'name': project_name,
            'created_at': datetime.now(),
            'indexed_files': []
        }
        
        return result
    
    async def index_codebase(self, project_name: str, project_path: str, 
                           file_patterns: List[str] = None) -> Dict:
        """Index entire codebase for semantic search"""
        
        if file_patterns is None:
            file_patterns = [
                "*.py", "*.js", "*.ts", "*.jsx", "*.tsx", 
                "*.java", "*.c", "*.cpp", "*.rs", "*.go",
                "*.php", "*.rb", "*.swift", "*.kt"
            ]
        
        # Collect files to index
        files_to_index = []
        project_path_obj = Path(project_path)
        
        for pattern in file_patterns:
            files_to_index.extend(project_path_obj.rglob(pattern))
        
        # Filter out common ignore patterns
        ignore_patterns = [
            '.git', 'node_modules', '__pycache__', '.pytest_cache',
            'venv', '.venv', 'env', '.env', 'build', 'dist',
            '.DS_Store', '*.pyc', '*.pyo'
        ]
        
        filtered_files = []
        for file_path in files_to_index:
            if not any(ignore in str(file_path) for ignore in ignore_patterns):
                filtered_files.append(file_path)
        
        # Index files in batches
        batch_size = 10
        indexed_count = 0
        
        for i in range(0, len(filtered_files), batch_size):
            batch = filtered_files[i:i + batch_size]
            
            batch_data = []
            for file_path in batch:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    batch_data.append({
                        'file_path': str(file_path.relative_to(project_path_obj)),
                        'absolute_path': str(file_path),
                        'content': content,
                        'language': self._detect_language(file_path.suffix),
                        'size': len(content)
                    })
                except (UnicodeDecodeError, IOError) as e:
                    logger.warning(f"Skipping file {file_path}: {e}")
                    continue
            
            if batch_data:
                await self._make_request('POST', f'/projects/{project_name}/index', {
                    'files': batch_data
                })
                indexed_count += len(batch_data)
                
                logger.info(f"Indexed {indexed_count}/{len(filtered_files)} files")
        
        # Update project info
        if project_name in self.projects:
            self.projects[project_name]['indexed_files'] = indexed_count
            self.projects[project_name]['last_indexed'] = datetime.now()
        
        return {
            'project_name': project_name,
            'indexed_files': indexed_count,
            'total_files_found': len(filtered_files),
            'timestamp': datetime.now().isoformat()
        }
    
    async def generate_embeddings(self, project_name: str) -> Dict:
        """Generate embeddings for indexed code"""
        return await self._make_request('POST', f'/projects/{project_name}/embeddings')
    
    async def search_similar_code(self, query: str, project_name: str, 
                                limit: int = 10, threshold: float = 0.7) -> List[Dict]:
        """Search for similar code blocks using semantic search"""
        
        data = {
            'query': query,
            'limit': limit,
            'threshold': threshold
        }
        
        result = await self._make_request('GET', f'/projects/{project_name}/search', data)
        
        return result.get('matches', [])
    
    async def search_function_blocks(self, query: str, project_name: str, 
                                   limit: int = 20) -> List[Dict]:
        """Search for function-level code blocks"""
        
        data = {
            'query': query,
            'search_type': 'functions',
            'limit': limit
        }
        
        result = await self._make_request('GET', f'/projects/{project_name}/search/functions', data)
        
        return result.get('functions', [])
    
    async def get_code_context(self, query: str, project_name: str, 
                             context_depth: str = "medium", limit: int = 10) -> Dict:
        """Get comprehensive code context for AI analysis"""
        
        # 1. Semantic search for relevant code blocks
        similar_blocks = await self.search_similar_code(query, project_name, limit)
        
        # 2. Function-level search
        function_blocks = await self.search_function_blocks(query, project_name, limit)
        
        # 3. Analyze patterns in found code
        patterns = await self.analyze_code_patterns(similar_blocks + function_blocks)
        
        # 4. Extract architectural insights
        architecture_insights = await self.extract_architecture_insights(
            similar_blocks, function_blocks
        )
        
        return {
            'query': query,
            'project': project_name,
            'context_depth': context_depth,
            'similar_code_blocks': similar_blocks,
            'related_functions': function_blocks,
            'code_patterns': patterns,
            'architecture_insights': architecture_insights,
            'total_matches': len(similar_blocks) + len(function_blocks),
            'timestamp': datetime.now().isoformat()
        }
    
    async def analyze_code_patterns(self, code_blocks: List[Dict]) -> Dict:
        """Analyze patterns in code blocks"""
        
        if not code_blocks:
            return {'patterns': [], 'analysis': 'No code blocks to analyze'}
        
        # Group by language
        language_groups = {}
        for block in code_blocks:
            lang = block.get('language', 'unknown')
            if lang not in language_groups:
                language_groups[lang] = []
            language_groups[lang].append(block)
        
        # Analyze common patterns
        patterns = []
        
        for language, blocks in language_groups.items():
            # Extract common keywords/patterns
            all_content = ' '.join([block.get('content', '') for block in blocks])
            
            # Simple pattern detection (can be enhanced with AST analysis)
            common_patterns = self._extract_simple_patterns(all_content, language)
            
            patterns.append({
                'language': language,
                'block_count': len(blocks),
                'common_patterns': common_patterns,
                'files_involved': list(set([block.get('file_path') for block in blocks]))
            })
        
        return {
            'total_blocks_analyzed': len(code_blocks),
            'languages_found': list(language_groups.keys()),
            'patterns_by_language': patterns,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    async def extract_architecture_insights(self, similar_blocks: List[Dict], 
                                          function_blocks: List[Dict]) -> Dict:
        """Extract architectural insights from code context"""
        
        all_blocks = similar_blocks + function_blocks
        
        if not all_blocks:
            return {'insights': [], 'summary': 'No code blocks available for analysis'}
        
        # Extract file relationships
        files_involved = set()
        directory_structure = {}
        
        for block in all_blocks:
            file_path = block.get('file_path', '')
            files_involved.add(file_path)
            
            # Build directory structure understanding
            parts = Path(file_path).parts
            if len(parts) > 1:
                directory = parts[0]
                if directory not in directory_structure:
                    directory_structure[directory] = set()
                directory_structure[directory].add(file_path)
        
        # Identify potential architectural patterns
        insights = []
        
        # Check for layer separation
        if any('controller' in f.lower() for f in files_involved):
            insights.append({
                'pattern': 'MVC/Controller Pattern',
                'description': 'Controllers detected, suggesting MVC architecture',
                'confidence': 0.8
            })
        
        if any('service' in f.lower() for f in files_involved):
            insights.append({
                'pattern': 'Service Layer',
                'description': 'Service layer components detected',
                'confidence': 0.7
            })
        
        if any('adapter' in f.lower() for f in files_involved):
            insights.append({
                'pattern': 'Adapter Pattern',
                'description': 'Adapter pattern implementation detected',
                'confidence': 0.8
            })
        
        return {
            'files_analyzed': len(files_involved),
            'directories_involved': list(directory_structure.keys()),
            'architectural_insights': insights,
            'coupling_analysis': {
                'files_involved': len(files_involved),
                'directories_involved': len(directory_structure),
                'estimated_coupling': 'high' if len(files_involved) > 10 else 'medium' if len(files_involved) > 5 else 'low'
            },
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _detect_language(self, file_extension: str) -> str:
        """Detect programming language from file extension"""
        
        extension_map = {
            '.py': 'python',
            '.js': 'javascript', 
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.rs': 'rust',
            '.go': 'go',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin'
        }
        
        return extension_map.get(file_extension.lower(), 'unknown')
    
    def _extract_simple_patterns(self, content: str, language: str) -> List[str]:
        """Extract simple code patterns from content"""
        
        patterns = []
        content_lower = content.lower()
        
        # Common patterns across languages
        if 'async' in content_lower or 'await' in content_lower:
            patterns.append('asynchronous_programming')
        
        if 'class' in content_lower:
            patterns.append('object_oriented_programming')
        
        if 'function' in content_lower or 'def ' in content_lower:
            patterns.append('function_definitions')
        
        if 'import' in content_lower or 'require' in content_lower:
            patterns.append('module_imports')
        
        if 'try' in content_lower and 'catch' in content_lower:
            patterns.append('error_handling')
        elif 'try:' in content_lower and 'except' in content_lower:
            patterns.append('error_handling')
        
        # Database patterns
        if any(db_term in content_lower for db_term in ['sql', 'query', 'database', 'db.']):
            patterns.append('database_operations')
        
        # API patterns
        if any(api_term in content_lower for api_term in ['api', 'endpoint', 'request', 'response']):
            patterns.append('api_operations')
        
        return patterns
    
    async def reindex_file(self, file_path: str, project_name: str) -> Dict:
        """Re-index a single file after changes"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_data = {
                'file_path': file_path,
                'content': content,
                'language': self._detect_language(Path(file_path).suffix),
                'size': len(content),
                'updated_at': datetime.now().isoformat()
            }
            
            return await self._make_request('PUT', f'/projects/{project_name}/files', file_data)
            
        except Exception as e:
            logger.error(f"Failed to reindex file {file_path}: {e}")
            raise BlockoliAPIError(f"File reindex failed: {e}")
    
    async def get_project_stats(self, project_name: str) -> Dict:
        """Get project statistics"""
        return await self._make_request('GET', f'/projects/{project_name}/stats')
    
    async def list_projects(self) -> List[Dict]:
        """List all projects"""
        result = await self._make_request('GET', '/projects')
        return result.get('projects', [])


class BlockoliAPIError(Exception):
    """Custom exception for Blockoli API errors"""
    pass


# Utility functions for integration

async def quick_code_search(query: str, project_name: str, 
                          blockoli_endpoint: str = "http://localhost:8080") -> Dict:
    """Quick code search utility function"""
    
    async with BlockoliCodeContext(blockoli_endpoint) as blockoli:
        return await blockoli.get_code_context(query, project_name)


async def index_project_quickly(project_path: str, project_name: str,
                              blockoli_endpoint: str = "http://localhost:8080") -> Dict:
    """Quick project indexing utility function"""
    
    async with BlockoliCodeContext(blockoli_endpoint) as blockoli:
        # Create project
        await blockoli.create_project(project_name)
        
        # Index codebase
        index_result = await blockoli.index_codebase(project_name, project_path)
        
        # Generate embeddings
        await blockoli.generate_embeddings(project_name)
        
        return index_result


if __name__ == "__main__":
    # CLI interface for testing
    import sys
    
    async def main():
        if len(sys.argv) < 3:
            print("Usage: python blockoli_client.py <command> <args>")
            print("Commands:")
            print("  index <project_path> <project_name> - Index a project")
            print("  search <query> <project_name> - Search for code")
            print("  health - Check service health")
            return
        
        command = sys.argv[1]
        
        async with BlockoliCodeContext() as blockoli:
            if command == "health":
                result = await blockoli.health_check()
                print(json.dumps(result, indent=2))
                
            elif command == "index" and len(sys.argv) >= 4:
                project_path = sys.argv[2]
                project_name = sys.argv[3]
                
                print(f"Creating project: {project_name}")
                await blockoli.create_project(project_name)
                
                print(f"Indexing codebase: {project_path}")
                result = await blockoli.index_codebase(project_name, project_path)
                
                print(f"Generating embeddings...")
                await blockoli.generate_embeddings(project_name)
                
                print(json.dumps(result, indent=2))
                
            elif command == "search" and len(sys.argv) >= 4:
                query = sys.argv[2]
                project_name = sys.argv[3]
                
                result = await blockoli.get_code_context(query, project_name)
                print(json.dumps(result, indent=2))
                
            else:
                print("Invalid command or arguments")
    
    asyncio.run(main())