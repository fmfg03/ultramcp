#!/usr/bin/env python3
"""
UltraMCP ContextBuilderAgent 2.0 - Belief Reviser
Updates beliefs in knowledge graph with git-like versioning
"""

import asyncio
import asyncpg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import json
import hashlib
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BeliefRevisionRequest(BaseModel):
    domain: str
    field: str
    new_value: Any
    confidence_delta: float
    trust_signal: float
    source: str
    reason: str

class BeliefRevisionResponse(BaseModel):
    revision_applied: bool
    new_version: str
    confidence_change: float
    knowledge_graph_updated: bool
    rollback_available: bool
    timestamp: str

class BeliefReviser:
    """
    Updates beliefs in the knowledge graph with incremental versioning
    Provides git-like version control for context evolution
    """
    
    def __init__(self):
        self.app = FastAPI(title="Belief Reviser", version="1.0.0")
        self.db_pool = None
        self.knowledge_tree_path = "/root/ultramcp/.context/core/knowledge_tree.yaml"
        self.versions_path = "/root/ultramcp/.context/versions"
        self.performance_metrics = {
            "revisions_processed": 0,
            "revisions_applied": 0,
            "rollbacks_performed": 0,
            "avg_confidence_delta": 0.0
        }
        
        # Initialize FastAPI routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.post("/revise_belief", response_model=BeliefRevisionResponse)
        async def revise_belief(request: BeliefRevisionRequest):
            """Revise belief in knowledge graph"""
            try:
                start_time = datetime.utcnow()
                
                result = await self._revise_belief(
                    request.domain,
                    request.field,
                    request.new_value,
                    request.confidence_delta,
                    request.trust_signal,
                    request.source,
                    request.reason
                )
                
                # Update metrics
                self.performance_metrics["revisions_processed"] += 1
                if result["revision_applied"]:
                    self.performance_metrics["revisions_applied"] += 1
                
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.info(f"Belief revision completed in {processing_time:.2f}ms")
                
                return BeliefRevisionResponse(**result)
                
            except Exception as e:
                logger.error(f"Error in belief revision: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/rollback_version")
        async def rollback_version(version: str):
            """Rollback to specific version"""
            try:
                result = await self._rollback_to_version(version)
                self.performance_metrics["rollbacks_performed"] += 1
                return result
            except Exception as e:
                logger.error(f"Error in rollback: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/versions")
        async def get_versions():
            """Get version history"""
            try:
                return await self._get_version_history()
            except Exception as e:
                logger.error(f"Error getting versions: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/current_knowledge_tree")
        async def get_current_knowledge_tree():
            """Get current knowledge tree"""
            try:
                return await self._load_knowledge_tree()
            except Exception as e:
                logger.error(f"Error loading knowledge tree: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            try:
                # Test database connection
                db_healthy = self.db_pool is not None
                
                # Test file system access
                import os
                fs_healthy = os.path.exists(self.knowledge_tree_path)
                
                return {
                    "status": "healthy" if db_healthy and fs_healthy else "degraded",
                    "database_connected": db_healthy,
                    "filesystem_accessible": fs_healthy,
                    "metrics": self.performance_metrics,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
        
        @self.app.get("/metrics")
        async def get_metrics():
            """Get performance metrics"""
            success_rate = 0
            if self.performance_metrics["revisions_processed"] > 0:
                success_rate = self.performance_metrics["revisions_applied"] / self.performance_metrics["revisions_processed"]
            
            return {
                **self.performance_metrics,
                "success_rate": success_rate,
                "knowledge_tree_path": self.knowledge_tree_path,
                "versions_path": self.versions_path,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def initialize_database(self):
        """Initialize database connection"""
        try:
            self.db_pool = await asyncpg.create_pool(
                host="mcp-database",
                port=5432,
                database="mcp_system",
                user="mcp_user",
                password="mcp_password",  # Should come from environment
                min_size=1,
                max_size=10
            )
            
            # Create tables if they don't exist
            await self._create_tables()
            logger.info("Database connection established")
            
        except Exception as e:
            logger.warning(f"Database connection failed: {e}")
            self.db_pool = None
    
    async def _create_tables(self):
        """Create necessary database tables"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS belief_revisions (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(50) NOT NULL,
                    domain VARCHAR(100) NOT NULL,
                    field VARCHAR(100) NOT NULL,
                    old_value JSONB,
                    new_value JSONB,
                    confidence_delta FLOAT,
                    trust_signal FLOAT,
                    source VARCHAR(200),
                    reason TEXT,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    rollback_data JSONB
                );
                
                CREATE INDEX IF NOT EXISTS idx_belief_revisions_version 
                ON belief_revisions(version);
                
                CREATE INDEX IF NOT EXISTS idx_belief_revisions_domain 
                ON belief_revisions(domain);
                
                CREATE TABLE IF NOT EXISTS knowledge_versions (
                    version VARCHAR(50) PRIMARY KEY,
                    knowledge_tree JSONB NOT NULL,
                    context_hash VARCHAR(64) NOT NULL,
                    coherence_score FLOAT,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    parent_version VARCHAR(50),
                    commit_message TEXT
                );
            """)
    
    async def _load_knowledge_tree(self) -> Dict[str, Any]:
        """Load current knowledge tree from file"""
        try:
            with open(self.knowledge_tree_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load knowledge tree: {e}")
            raise
    
    async def _save_knowledge_tree(self, knowledge_tree: Dict[str, Any]):
        """Save knowledge tree to file"""
        try:
            with open(self.knowledge_tree_path, 'w', encoding='utf-8') as f:
                yaml.dump(knowledge_tree, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            logger.error(f"Failed to save knowledge tree: {e}")
            raise
    
    def _calculate_context_hash(self, knowledge_tree: Dict[str, Any]) -> str:
        """Calculate hash of knowledge tree for versioning"""
        # Remove timestamp and hash fields for consistent hashing
        tree_copy = json.loads(json.dumps(knowledge_tree))
        if 'last_updated' in tree_copy:
            del tree_copy['last_updated']
        if 'context_hash' in tree_copy:
            del tree_copy['context_hash']
        
        content = json.dumps(tree_copy, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _generate_version(self, current_version: str) -> str:
        """Generate new version number"""
        try:
            parts = current_version.split('.')
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
            
            # Increment patch version for belief revisions
            patch += 1
            
            return f"{major}.{minor}.{patch}"
        except:
            # Fallback to timestamp-based version
            return f"1.0.{int(datetime.utcnow().timestamp())}"
    
    async def _revise_belief(self, domain: str, field: str, new_value: Any,
                           confidence_delta: float, trust_signal: float,
                           source: str, reason: str) -> Dict[str, Any]:
        """Core belief revision logic"""
        
        # Load current knowledge tree
        knowledge_tree = await self._load_knowledge_tree()
        
        # Check if domain and field exist
        if domain not in knowledge_tree.get("domains", {}):
            return {
                "revision_applied": False,
                "new_version": knowledge_tree.get("version", "1.0.0"),
                "confidence_change": 0.0,
                "knowledge_graph_updated": False,
                "rollback_available": False,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "error": f"Domain {domain} not found"
            }
        
        domain_data = knowledge_tree["domains"][domain]
        if "fields" not in domain_data or field not in domain_data["fields"]:
            return {
                "revision_applied": False,
                "new_version": knowledge_tree.get("version", "1.0.0"),
                "confidence_change": 0.0,
                "knowledge_graph_updated": False,
                "rollback_available": False,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "error": f"Field {field} not found in domain {domain}"
            }
        
        # Store old value for rollback
        field_data = domain_data["fields"][field]
        old_value = field_data.get("value")
        old_confidence = field_data.get("confidence", 0.0)
        
        # Calculate new confidence
        new_confidence = min(max(old_confidence + confidence_delta, 0.0), 1.0)
        
        # Determine if revision should be applied based on trust signal
        apply_revision = trust_signal > 0.5 and confidence_delta != 0
        
        if apply_revision:
            # Create backup version
            current_version = knowledge_tree.get("version", "1.0.0")
            new_version = self._generate_version(current_version)
            
            # Store current version in database
            if self.db_pool:
                await self._store_version_in_db(current_version, knowledge_tree, f"Before revision: {reason}")
            
            # Apply revision
            field_data["value"] = new_value
            field_data["confidence"] = new_confidence
            field_data["source"] = source
            field_data["timestamp"] = datetime.utcnow().isoformat() + "Z"
            
            # Update knowledge tree metadata
            knowledge_tree["version"] = new_version
            knowledge_tree["last_updated"] = datetime.utcnow().isoformat() + "Z"
            knowledge_tree["context_hash"] = self._calculate_context_hash(knowledge_tree)
            
            # Update average confidence in metadata
            if "metadata" in knowledge_tree:
                await self._update_metadata_confidence(knowledge_tree)
            
            # Save updated knowledge tree
            await self._save_knowledge_tree(knowledge_tree)
            
            # Store revision in database
            if self.db_pool:
                await self._store_revision_in_db(
                    new_version, domain, field, old_value, new_value,
                    confidence_delta, trust_signal, source, reason,
                    {"old_confidence": old_confidence, "new_confidence": new_confidence}
                )
            
            logger.info(f"Belief revision applied: {domain}.{field} -> {new_value} (confidence: {new_confidence})")
            
            return {
                "revision_applied": True,
                "new_version": new_version,
                "confidence_change": confidence_delta,
                "knowledge_graph_updated": True,
                "rollback_available": True,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        else:
            return {
                "revision_applied": False,
                "new_version": knowledge_tree.get("version", "1.0.0"),
                "confidence_change": 0.0,
                "knowledge_graph_updated": False,
                "rollback_available": False,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "reason": f"Trust signal too low ({trust_signal}) or no confidence change"
            }
    
    async def _update_metadata_confidence(self, knowledge_tree: Dict[str, Any]):
        """Update average confidence in metadata"""
        total_confidence = 0
        field_count = 0
        
        for domain_data in knowledge_tree.get("domains", {}).values():
            for field_data in domain_data.get("fields", {}).values():
                if isinstance(field_data, dict) and "confidence" in field_data:
                    total_confidence += field_data["confidence"]
                    field_count += 1
        
        if field_count > 0:
            avg_confidence = total_confidence / field_count
            if "metadata" not in knowledge_tree:
                knowledge_tree["metadata"] = {}
            knowledge_tree["metadata"]["avg_confidence"] = round(avg_confidence, 3)
    
    async def _store_version_in_db(self, version: str, knowledge_tree: Dict[str, Any], 
                                  commit_message: str):
        """Store version in database"""
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO knowledge_versions 
                    (version, knowledge_tree, context_hash, coherence_score, commit_message)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (version) DO UPDATE SET
                    knowledge_tree = EXCLUDED.knowledge_tree,
                    context_hash = EXCLUDED.context_hash,
                    coherence_score = EXCLUDED.coherence_score,
                    commit_message = EXCLUDED.commit_message
                """, version, json.dumps(knowledge_tree), 
                knowledge_tree.get("context_hash", ""), 
                knowledge_tree.get("coherence_score", 1.0),
                commit_message)
        except Exception as e:
            logger.error(f"Failed to store version in database: {e}")
    
    async def _store_revision_in_db(self, version: str, domain: str, field: str,
                                   old_value: Any, new_value: Any, confidence_delta: float,
                                   trust_signal: float, source: str, reason: str,
                                   rollback_data: Dict[str, Any]):
        """Store revision in database"""
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO belief_revisions 
                    (version, domain, field, old_value, new_value, confidence_delta,
                     trust_signal, source, reason, rollback_data)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """, version, domain, field, json.dumps(old_value), 
                json.dumps(new_value), confidence_delta, trust_signal, 
                source, reason, json.dumps(rollback_data))
        except Exception as e:
            logger.error(f"Failed to store revision in database: {e}")
    
    async def _rollback_to_version(self, target_version: str) -> Dict[str, Any]:
        """Rollback to specific version"""
        if not self.db_pool:
            return {"success": False, "error": "Database not available"}
        
        try:
            async with self.db_pool.acquire() as conn:
                # Get target version
                row = await conn.fetchrow("""
                    SELECT knowledge_tree, context_hash, timestamp
                    FROM knowledge_versions
                    WHERE version = $1
                """, target_version)
                
                if not row:
                    return {"success": False, "error": f"Version {target_version} not found"}
                
                # Restore knowledge tree
                knowledge_tree = row["knowledge_tree"]
                knowledge_tree["version"] = self._generate_version(target_version)
                knowledge_tree["last_updated"] = datetime.utcnow().isoformat() + "Z"
                
                # Save restored tree
                await self._save_knowledge_tree(knowledge_tree)
                
                logger.info(f"Successfully rolled back to version {target_version}")
                
                return {
                    "success": True,
                    "restored_version": target_version,
                    "new_version": knowledge_tree["version"],
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_version_history(self) -> Dict[str, Any]:
        """Get version history"""
        if not self.db_pool:
            return {"versions": [], "error": "Database not available"}
        
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT version, context_hash, coherence_score, timestamp, commit_message
                    FROM knowledge_versions
                    ORDER BY timestamp DESC
                    LIMIT 50
                """)
                
                versions = []
                for row in rows:
                    versions.append({
                        "version": row["version"],
                        "context_hash": row["context_hash"],
                        "coherence_score": row["coherence_score"],
                        "timestamp": row["timestamp"].isoformat() + "Z",
                        "commit_message": row["commit_message"]
                    })
                
                return {"versions": versions}
                
        except Exception as e:
            logger.error(f"Failed to get version history: {e}")
            return {"versions": [], "error": str(e)}

# Global instance
reviser = BeliefReviser()

# FastAPI app instance for uvicorn
app = reviser.app

if __name__ == "__main__":
    import uvicorn
    
    # Initialize database on startup
    async def startup():
        await reviser.initialize_database()
    
    asyncio.create_task(startup())
    uvicorn.run(app, host="0.0.0.0", port=8022)