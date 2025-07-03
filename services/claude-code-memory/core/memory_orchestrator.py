#!/usr/bin/env python3

"""
Unified Memory Orchestrator
Combines Claude Code Memory, Context7, Sam Memory, and Blockoli into unified interface
"""

import asyncio
import logging
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from .code_parser import TreeSitterCodeParser
from .semantic_search import SemanticCodeSearch
from .pattern_analyzer import CodePatternAnalyzer
from .qdrant_manager import QdrantMemoryManager
from ..utils.project_scanner import ProjectScanner
from ..utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)

@dataclass
class IndexingTask:
    """Represents an indexing task"""
    task_id: str
    project_name: str
    project_path: str
    status: str  # pending, running, completed, failed
    progress: float
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    files_processed: int
    total_files: int

@dataclass
class MemoryContext:
    """Context for memory-enhanced operations"""
    similar_implementations: List[Dict]
    project_patterns: List[Dict]
    documentation_context: List[Dict]
    experience_memory: List[Dict]

class UnifiedMemoryOrchestrator:
    """
    Unified orchestrator that combines multiple memory systems:
    - Claude Code Memory (Tree-sitter + Qdrant)
    - Context7 (Real-time documentation)
    - Sam Memory (Experience patterns)
    - Blockoli (Semantic search)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.UnifiedMemoryOrchestrator")
        
        # Core components
        self.code_parser: Optional[TreeSitterCodeParser] = None
        self.semantic_search: Optional[SemanticCodeSearch] = None
        self.pattern_analyzer: Optional[CodePatternAnalyzer] = None
        self.qdrant_manager: Optional[QdrantMemoryManager] = None
        self.project_scanner: Optional[ProjectScanner] = None
        self.cache_manager: Optional[CacheManager] = None
        
        # Task management
        self.active_tasks: Dict[str, IndexingTask] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Configuration
        self.config = {
            "qdrant_url": os.getenv("QDRANT_URL", "http://localhost:6333"),
            "collection_name": os.getenv("MEMORY_COLLECTION", "ultramcp_code_memory"),
            "embedding_model": os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
            "max_file_size": int(os.getenv("MAX_FILE_SIZE", 1024 * 1024)),  # 1MB
            "supported_languages": ["python", "javascript", "typescript", "rust", "go", "java", "cpp", "c"],
            "cache_ttl": int(os.getenv("CACHE_TTL", 3600)),  # 1 hour
        }
        
        # Statistics
        self.stats = {
            "projects_indexed": 0,
            "files_processed": 0,
            "entities_extracted": 0,
            "search_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "indexing_time_total": 0.0,
            "search_time_total": 0.0,
        }

    async def initialize(self):
        """Initialize all memory components"""
        try:
            self.logger.info("🚀 Initializing Unified Memory Orchestrator...")
            
            # Initialize core components
            self.code_parser = TreeSitterCodeParser()
            await self.code_parser.initialize()
            
            self.qdrant_manager = QdrantMemoryManager(
                url=self.config["qdrant_url"],
                collection_name=self.config["collection_name"]
            )
            await self.qdrant_manager.initialize()
            
            self.semantic_search = SemanticCodeSearch(
                qdrant_manager=self.qdrant_manager,
                embedding_model=self.config["embedding_model"]
            )
            await self.semantic_search.initialize()
            
            self.pattern_analyzer = CodePatternAnalyzer(
                code_parser=self.code_parser
            )
            await self.pattern_analyzer.initialize()
            
            self.project_scanner = ProjectScanner(
                max_file_size=self.config["max_file_size"],
                supported_languages=self.config["supported_languages"]
            )
            
            self.cache_manager = CacheManager(ttl=self.config["cache_ttl"])
            
            # Initialize integration with existing UltraMCP systems
            await self._initialize_ultramcp_integrations()
            
            self.logger.info("✅ Unified Memory Orchestrator initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize memory orchestrator: {e}")
            raise

    async def _initialize_ultramcp_integrations(self):
        """Initialize integrations with existing UltraMCP systems"""
        try:
            # Context7 integration
            self.context7_available = await self._check_service_availability("http://localhost:8003/health")
            if self.context7_available:
                self.logger.info("✅ Context7 integration available")
            
            # Sam Memory integration
            self.sam_memory_available = await self._check_service_availability("http://localhost:8001/api/memory/health")
            if self.sam_memory_available:
                self.logger.info("✅ Sam Memory integration available")
            
            # Blockoli integration
            self.blockoli_available = await self._check_service_availability("http://localhost:8080/health")
            if self.blockoli_available:
                self.logger.info("✅ Blockoli integration available")
                
        except Exception as e:
            self.logger.warning(f"Some UltraMCP integrations unavailable: {e}")

    async def _check_service_availability(self, health_url: str) -> bool:
        """Check if a service is available"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(health_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    return response.status == 200
        except:
            return False

    async def start_indexing_task(
        self,
        project_path: str,
        project_name: str,
        include_patterns: List[str],
        exclude_patterns: List[str],
        indexing_mode: str = "full",
        force_reindex: bool = False
    ) -> str:
        """Start a project indexing task"""
        try:
            task_id = str(uuid.uuid4())
            
            # Create indexing task
            task = IndexingTask(
                task_id=task_id,
                project_name=project_name,
                project_path=project_path,
                status="pending",
                progress=0.0,
                started_at=None,
                completed_at=None,
                error_message=None,
                files_processed=0,
                total_files=0
            )
            
            self.active_tasks[task_id] = task
            
            # Start indexing in background
            asyncio.create_task(self._run_indexing_task(task, include_patterns, exclude_patterns, indexing_mode, force_reindex))
            
            self.logger.info(f"📋 Created indexing task {task_id} for project {project_name}")
            return task_id
            
        except Exception as e:
            self.logger.error(f"Error creating indexing task: {e}")
            raise

    async def _run_indexing_task(
        self,
        task: IndexingTask,
        include_patterns: List[str],
        exclude_patterns: List[str],
        indexing_mode: str,
        force_reindex: bool
    ):
        """Run the actual indexing task"""
        try:
            task.status = "running"
            task.started_at = datetime.now()
            
            self.logger.info(f"🔍 Starting indexing for {task.project_name}")
            
            # Scan project files
            files = await self.project_scanner.scan_project(
                Path(task.project_path),
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns
            )
            
            task.total_files = len(files)
            self.logger.info(f"📁 Found {len(files)} files to process")
            
            # Check if project already indexed
            if not force_reindex:
                existing_project = await self.qdrant_manager.get_project_info(task.project_name)
                if existing_project and indexing_mode == "incremental":
                    files = await self._filter_changed_files(files, existing_project)
                    self.logger.info(f"📄 Incremental update: {len(files)} changed files")
            
            # Process files in batches
            batch_size = 10
            processed_entities = []
            
            for i in range(0, len(files), batch_size):
                batch = files[i:i + batch_size]
                
                # Process batch
                batch_entities = await self._process_file_batch(batch, task.project_name)
                processed_entities.extend(batch_entities)
                
                # Update progress
                task.files_processed = min(i + batch_size, len(files))
                task.progress = task.files_processed / task.total_files
                
                self.logger.info(f"📊 Progress: {task.progress:.1%} ({task.files_processed}/{task.total_files})")
            
            # Store entities in Qdrant
            if processed_entities:
                await self.qdrant_manager.store_entities(processed_entities, task.project_name)
                self.logger.info(f"💾 Stored {len(processed_entities)} entities for {task.project_name}")
            
            # Update project metadata
            await self.qdrant_manager.update_project_metadata(
                task.project_name,
                {
                    "path": task.project_path,
                    "files_count": len(files),
                    "entities_count": len(processed_entities),
                    "indexed_at": datetime.now().isoformat(),
                    "indexing_mode": indexing_mode
                }
            )
            
            # Complete task
            task.status = "completed"
            task.completed_at = datetime.now()
            task.progress = 1.0
            
            # Update statistics
            self.stats["projects_indexed"] += 1
            self.stats["files_processed"] += len(files)
            self.stats["entities_extracted"] += len(processed_entities)
            
            indexing_time = (task.completed_at - task.started_at).total_seconds()
            self.stats["indexing_time_total"] += indexing_time
            
            self.logger.info(f"✅ Completed indexing {task.project_name} in {indexing_time:.2f}s")
            
        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = datetime.now()
            
            self.logger.error(f"❌ Indexing failed for {task.project_name}: {e}")

    async def _process_file_batch(self, files: List[Path], project_name: str) -> List[Dict]:
        """Process a batch of files and extract code entities"""
        entities = []
        
        for file_path in files:
            try:
                # Read file content
                content = await self._read_file_safely(file_path)
                if not content:
                    continue
                
                # Parse with Tree-sitter
                file_entities = await self.code_parser.parse_file(file_path, content)
                
                # Add project context
                for entity in file_entities:
                    entity["project_name"] = project_name
                    entity["indexed_at"] = datetime.now().isoformat()
                
                entities.extend(file_entities)
                
            except Exception as e:
                self.logger.warning(f"Failed to process {file_path}: {e}")
        
        return entities

    async def _read_file_safely(self, file_path: Path) -> Optional[str]:
        """Safely read file content with encoding detection"""
        try:
            # Check file size
            if file_path.stat().st_size > self.config["max_file_size"]:
                self.logger.warning(f"File too large, skipping: {file_path}")
                return None
            
            # Try different encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'ascii']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            
            self.logger.warning(f"Could not decode file: {file_path}")
            return None
            
        except Exception as e:
            self.logger.warning(f"Error reading file {file_path}: {e}")
            return None

    async def search_code(
        self,
        query: str,
        project_name: Optional[str] = None,
        entity_types: List[str] = None,
        languages: List[str] = None,
        search_mode: str = "hybrid",
        max_results: int = 10,
        min_similarity: float = 0.5
    ) -> List[Dict]:
        """Search for code using various strategies"""
        try:
            start_time = datetime.now()
            
            # Check cache first
            cache_key = f"search:{hash(query)}:{project_name}:{search_mode}"
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                self.stats["cache_hits"] += 1
                return cached_result
            
            self.stats["cache_misses"] += 1
            
            # Perform search
            results = await self.semantic_search.search(
                query=query,
                project_name=project_name,
                entity_types=entity_types,
                languages=languages,
                search_mode=search_mode,
                max_results=max_results,
                min_similarity=min_similarity
            )
            
            # Cache results
            await self.cache_manager.set(cache_key, results)
            
            # Update statistics
            self.stats["search_queries"] += 1
            search_time = (datetime.now() - start_time).total_seconds()
            self.stats["search_time_total"] += search_time
            
            self.logger.info(f"🔍 Search completed in {search_time:.3f}s, found {len(results)} results")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching code: {e}")
            raise

    async def find_similar_code(
        self,
        code_snippet: str,
        language: Optional[str] = None,
        entity_type: Optional[str] = None,
        project_name: Optional[str] = None,
        max_results: int = 5
    ) -> List[Dict]:
        """Find similar code implementations"""
        try:
            # Parse the code snippet first
            parsed_snippet = await self.code_parser.parse_snippet(code_snippet, language)
            
            # Extract semantic features
            query_embedding = await self.semantic_search.get_embedding(code_snippet)
            
            # Search for similar code
            results = await self.semantic_search.find_similar(
                embedding=query_embedding,
                entity_type=entity_type,
                project_name=project_name,
                max_results=max_results
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error finding similar code: {e}")
            raise

    async def analyze_code_patterns(
        self,
        pattern_type: str,
        project_name: str,
        scope: str = "all"
    ) -> Dict:
        """Analyze code patterns in a project"""
        try:
            return await self.pattern_analyzer.analyze_patterns(
                pattern_type=pattern_type,
                project_name=project_name,
                scope=scope
            )
        except Exception as e:
            self.logger.error(f"Error analyzing patterns: {e}")
            raise

    async def memory_enhanced_chat(
        self,
        prompt: str,
        project_context: Optional[str] = None,
        include_patterns: bool = True,
        include_documentation: bool = True,
        max_context_items: int = 5
    ) -> Dict:
        """Generate memory-enhanced chat response"""
        try:
            self.logger.info(f"💬 Generating memory-enhanced response for: {prompt[:50]}...")
            
            # Build memory context
            context = await self._build_memory_context(
                prompt=prompt,
                project_context=project_context,
                include_patterns=include_patterns,
                include_documentation=include_documentation,
                max_context_items=max_context_items
            )
            
            # Generate enhanced prompt
            enhanced_prompt = await self._create_enhanced_prompt(prompt, context)
            
            return {
                "original_prompt": prompt,
                "enhanced_prompt": enhanced_prompt,
                "memory_context": asdict(context),
                "context_sources": self._get_context_sources(context),
                "suggestions": await self._generate_suggestions(prompt, context)
            }
            
        except Exception as e:
            self.logger.error(f"Error in memory-enhanced chat: {e}")
            raise

    async def _build_memory_context(
        self,
        prompt: str,
        project_context: Optional[str],
        include_patterns: bool,
        include_documentation: bool,
        max_context_items: int
    ) -> MemoryContext:
        """Build comprehensive memory context"""
        
        context = MemoryContext(
            similar_implementations=[],
            project_patterns=[],
            documentation_context=[],
            experience_memory=[]
        )
        
        try:
            # 1. Find similar code implementations
            if project_context:
                similar_code = await self.search_code(
                    query=prompt,
                    project_name=project_context,
                    max_results=max_context_items
                )
                context.similar_implementations = similar_code
            
            # 2. Get project patterns if requested
            if include_patterns and project_context:
                patterns = await self.analyze_code_patterns(
                    pattern_type="architecture",
                    project_name=project_context
                )
                context.project_patterns = [patterns]
            
            # 3. Get documentation context (Context7 integration)
            if include_documentation and self.context7_available:
                doc_context = await self._get_context7_documentation(prompt)
                context.documentation_context = doc_context
            
            # 4. Get experience memory (Sam Memory integration)
            if self.sam_memory_available:
                experience = await self._get_sam_memory_context(prompt)
                context.experience_memory = experience
            
        except Exception as e:
            self.logger.warning(f"Error building memory context: {e}")
        
        return context

    async def _create_enhanced_prompt(self, original_prompt: str, context: MemoryContext) -> str:
        """Create enhanced prompt with memory context"""
        
        enhanced_parts = [original_prompt]
        
        if context.similar_implementations:
            enhanced_parts.append("\n--- Similar Implementations Found ---")
            for impl in context.similar_implementations[:3]:
                enhanced_parts.append(f"• {impl.get('name', 'Unknown')}: {impl.get('signature', '')}")
        
        if context.project_patterns:
            enhanced_parts.append("\n--- Project Patterns ---")
            for pattern in context.project_patterns:
                enhanced_parts.append(f"• Architecture: {pattern.get('summary', 'N/A')}")
        
        if context.documentation_context:
            enhanced_parts.append("\n--- Relevant Documentation ---")
            for doc in context.documentation_context[:2]:
                enhanced_parts.append(f"• {doc.get('title', 'Documentation')}")
        
        if context.experience_memory:
            enhanced_parts.append("\n--- Past Experience ---")
            for exp in context.experience_memory[:2]:
                enhanced_parts.append(f"• {exp.get('summary', 'Experience')}")
        
        return "\n".join(enhanced_parts)

    async def get_project_status(self, project_name: str) -> Dict:
        """Get indexing status for a project"""
        # Check active tasks
        for task in self.active_tasks.values():
            if task.project_name == project_name:
                return {
                    "status": task.status,
                    "progress": task.progress,
                    "files_processed": task.files_processed,
                    "total_files": task.total_files,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "error": task.error_message
                }
        
        # Check if project exists in Qdrant
        project_info = await self.qdrant_manager.get_project_info(project_name)
        if project_info:
            return {
                "status": "completed",
                "progress": 1.0,
                "project_info": project_info
            }
        
        return {"status": "not_found"}

    async def list_projects(self) -> List[Dict]:
        """List all indexed projects"""
        return await self.qdrant_manager.list_projects()

    async def get_memory_stats(self) -> Dict:
        """Get memory system statistics"""
        qdrant_stats = await self.qdrant_manager.get_collection_stats()
        
        return {
            **self.stats,
            "qdrant_stats": qdrant_stats,
            "active_tasks": len(self.active_tasks),
            "cache_stats": await self.cache_manager.get_stats()
        }

    async def delete_project(self, project_name: str):
        """Delete a project from memory"""
        await self.qdrant_manager.delete_project(project_name)

    async def refresh_project(self, project_name: str) -> str:
        """Refresh/update project index"""
        project_info = await self.qdrant_manager.get_project_info(project_name)
        if not project_info:
            raise ValueError(f"Project {project_name} not found")
        
        return await self.start_indexing_task(
            project_path=project_info["path"],
            project_name=project_name,
            include_patterns=["**/*"],
            exclude_patterns=["**/node_modules/**", "**/.git/**"],
            indexing_mode="incremental",
            force_reindex=False
        )

    async def background_maintenance(self):
        """Background maintenance tasks"""
        try:
            # Clean up completed tasks older than 1 hour
            current_time = datetime.now()
            tasks_to_remove = []
            
            for task_id, task in self.active_tasks.items():
                if (task.status in ["completed", "failed"] and 
                    task.completed_at and 
                    (current_time - task.completed_at).total_seconds() > 3600):
                    tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self.active_tasks[task_id]
            
            if tasks_to_remove:
                self.logger.info(f"🧹 Cleaned up {len(tasks_to_remove)} old tasks")
                
        except Exception as e:
            self.logger.error(f"Error in background maintenance: {e}")

    async def cleanup_stale_data(self):
        """Clean up stale data"""
        try:
            await self.cache_manager.cleanup_expired()
            await self.qdrant_manager.cleanup_old_points()
            self.logger.info("🧹 Cleaned up stale data")
        except Exception as e:
            self.logger.error(f"Error cleaning up stale data: {e}")

    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.qdrant_manager:
                await self.qdrant_manager.close()
            if self.cache_manager:
                await self.cache_manager.close()
            if self.executor:
                self.executor.shutdown(wait=True)
                
            self.logger.info("🛑 Memory orchestrator cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    # Integration methods for existing UltraMCP systems

    async def _get_context7_documentation(self, prompt: str) -> List[Dict]:
        """Get documentation context from Context7"""
        try:
            if not self.context7_available:
                return []
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8003/api/claude/context",
                    json={"prompt": prompt, "autoDetect": True},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", {}).get("documentation", [])
        except Exception as e:
            self.logger.warning(f"Context7 integration error: {e}")
        
        return []

    async def _get_sam_memory_context(self, prompt: str) -> List[Dict]:
        """Get experience context from Sam Memory"""
        try:
            if not self.sam_memory_available:
                return []
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8001/api/memory/search",
                    json={"query": prompt, "max_results": 3},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("memories", [])
        except Exception as e:
            self.logger.warning(f"Sam Memory integration error: {e}")
        
        return []

    def _get_context_sources(self, context: MemoryContext) -> List[str]:
        """Get list of context sources used"""
        sources = []
        
        if context.similar_implementations:
            sources.append("similar_code")
        if context.project_patterns:
            sources.append("project_patterns")
        if context.documentation_context:
            sources.append("documentation")
        if context.experience_memory:
            sources.append("experience_memory")
        
        return sources

    async def _generate_suggestions(self, prompt: str, context: MemoryContext) -> List[str]:
        """Generate suggestions based on memory context"""
        suggestions = []
        
        if context.similar_implementations:
            suggestions.append("Consider reviewing similar implementations in your codebase")
        
        if context.project_patterns:
            suggestions.append("Follow established project architecture patterns")
        
        if context.documentation_context:
            suggestions.append("Refer to the latest documentation for accurate implementation")
        
        return suggestions

    async def _filter_changed_files(self, files: List[Path], existing_project: Dict) -> List[Path]:
        """Filter files that have changed since last indexing"""
        # For now, return all files - in production, would check modification times
        return files