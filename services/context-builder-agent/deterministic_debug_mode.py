#!/usr/bin/env python3
"""
UltraMCP ContextBuilderAgent 2.0 - DeterministicDebugMode
Reproducible debugging and testing framework for semantic coherence systems
"""

import asyncio
import json
import yaml
import hashlib
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import copy
import pickle
import threading
import queue
from contextlib import contextmanager
from semantic_coherence_bus import get_semantic_bus, SemanticMessage

# Configure logging for debug mode
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DebugLevel(str, Enum):
    """Debug verbosity levels"""
    MINIMAL = "minimal"        # Only major operations
    STANDARD = "standard"      # Standard debugging info
    VERBOSE = "verbose"        # Detailed operation logs
    EXHAUSTIVE = "exhaustive"  # Complete state tracking

class ReproducibilityMode(str, Enum):
    """Reproducibility guarantee levels"""
    STRICT = "strict"          # Bit-for-bit reproducibility
    SEMANTIC = "semantic"      # Semantically equivalent results
    FUNCTIONAL = "functional"  # Functionally equivalent outputs
    LOOSE = "loose"           # Best-effort reproducibility

@dataclass
class DebugSnapshot:
    """Complete system state snapshot"""
    snapshot_id: str
    timestamp: str
    system_state: Dict[str, Any]
    knowledge_tree: Dict[str, Any]
    active_mutations: List[Dict[str, Any]]
    service_states: Dict[str, Dict[str, Any]]
    metrics: Dict[str, Any]
    context_fragments: Dict[str, Any]
    
@dataclass
class OperationTrace:
    """Trace of a single operation"""
    operation_id: str
    operation_type: str
    timestamp: str
    input_parameters: Dict[str, Any]
    system_state_before: str  # Snapshot ID
    system_state_after: str   # Snapshot ID
    output_result: Dict[str, Any]
    duration_ms: float
    service_calls: List[Dict[str, Any]]
    randomness_seeds: Dict[str, Any]
    errors: List[Dict[str, Any]]

@dataclass
class TestCase:
    """Deterministic test case definition"""
    test_id: str
    name: str
    description: str
    initial_state: Dict[str, Any]
    operations: List[Dict[str, Any]]
    expected_outcomes: Dict[str, Any]
    reproducibility_mode: ReproducibilityMode
    created_at: str
    
class DebugSessionRequest(BaseModel):
    """Request to start debug session"""
    session_name: str
    debug_level: DebugLevel = DebugLevel.STANDARD
    reproducibility_mode: ReproducibilityMode = ReproducibilityMode.SEMANTIC
    capture_interval_seconds: int = 30
    enable_state_snapshots: bool = True
    enable_operation_tracing: bool = True
    random_seed: Optional[int] = None

class ReplayRequest(BaseModel):
    """Request to replay operations"""
    session_id: str
    operation_ids: List[str] = Field(default_factory=list)
    target_snapshot_id: Optional[str] = None
    verify_reproducibility: bool = True
    
class TestCaseRequest(BaseModel):
    """Request to create test case"""
    name: str
    description: str
    base_session_id: Optional[str] = None
    operations_to_include: List[str] = Field(default_factory=list)
    expected_outcomes: Dict[str, Any] = Field(default_factory=dict)

class DeterministicDebugMode:
    """
    Deterministic debugging and reproducibility framework
    Provides complete system state tracking, operation replay, and test case generation
    """
    
    def __init__(self):
        self.app = FastAPI(title="DeterministicDebugMode", version="2.0.0")
        self.semantic_bus = None
        
        # Debug session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.snapshots: Dict[str, DebugSnapshot] = {}
        self.operation_traces: Dict[str, OperationTrace] = {}
        self.test_cases: Dict[str, TestCase] = {}
        
        # State management
        self.deterministic_mode = False
        self.current_session_id: Optional[str] = None
        self.random_seed = 42
        self.snapshot_counter = 0
        self.operation_counter = 0
        
        # Reproducibility tracking
        self.state_hash_history: List[Tuple[str, str]] = []  # (timestamp, hash)
        self.randomness_log: List[Dict[str, Any]] = []
        self.external_call_log: List[Dict[str, Any]] = []
        
        # Service endpoints for state collection
        self.service_endpoints = {
            "orchestrator": "http://localhost:8025",
            "drift_detector": "http://localhost:8020",
            "contradiction_resolver": "http://localhost:8021",
            "belief_reviser": "http://localhost:8022",
            "utility_predictor": "http://localhost:8023",
            "memory_tuner": "http://localhost:8026",
            "prompt_assembler": "http://localhost:8027",
            "observatory": "http://localhost:8028"
        }
        
        # Context paths
        self.context_dir = "/root/ultramcp/.context"
        self.debug_data_dir = f"{self.context_dir}/debug"
        
        # Performance metrics
        self.performance_metrics = {
            "sessions_created": 0,
            "snapshots_captured": 0,
            "operations_traced": 0,
            "replays_performed": 0,
            "test_cases_generated": 0,
            "reproducibility_verifications": 0
        }
        
        # Setup routes and initialize
        self._setup_routes()
        
        # Add startup event handler
        @self.app.on_event("startup")
        async def startup_event():
            await self._initialize_system()
    
    def _setup_routes(self):
        """Setup FastAPI routes for debug mode"""
        
        @self.app.post("/start_debug_session")
        async def start_debug_session(request: DebugSessionRequest):
            """Start a new deterministic debug session"""
            try:
                result = await self._start_debug_session(
                    request.session_name,
                    request.debug_level,
                    request.reproducibility_mode,
                    request.capture_interval_seconds,
                    request.enable_state_snapshots,
                    request.enable_operation_tracing,
                    request.random_seed
                )
                return result
            except Exception as e:
                logger.error(f"Failed to start debug session: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/stop_debug_session/{session_id}")
        async def stop_debug_session(session_id: str):
            """Stop an active debug session"""
            try:
                result = await self._stop_debug_session(session_id)
                return result
            except Exception as e:
                logger.error(f"Failed to stop debug session: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/debug_sessions")
        async def get_debug_sessions():
            """Get all debug sessions"""
            return {
                "active_sessions": {
                    session_id: {
                        "name": session["name"],
                        "debug_level": session["debug_level"],
                        "started_at": session["started_at"],
                        "snapshots_count": len([s for s in self.snapshots.values() if s.snapshot_id.startswith(session_id)]),
                        "operations_count": len([o for o in self.operation_traces.values() if o.operation_id.startswith(session_id)])
                    }
                    for session_id, session in self.active_sessions.items()
                },
                "total_snapshots": len(self.snapshots),
                "total_operations": len(self.operation_traces),
                "total_test_cases": len(self.test_cases),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        @self.app.post("/capture_snapshot")
        async def capture_snapshot(session_id: Optional[str] = None):
            """Manually capture system state snapshot"""
            try:
                target_session = session_id or self.current_session_id
                if not target_session:
                    raise HTTPException(status_code=400, detail="No active session")
                
                result = await self._capture_system_snapshot(target_session)
                return result
            except Exception as e:
                logger.error(f"Failed to capture snapshot: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/snapshots/{session_id}")
        async def get_snapshots(session_id: str):
            """Get all snapshots for a session"""
            session_snapshots = [
                {
                    "snapshot_id": snapshot.snapshot_id,
                    "timestamp": snapshot.timestamp,
                    "system_state_hash": hashlib.md5(json.dumps(snapshot.system_state, sort_keys=True).encode()).hexdigest()[:8],
                    "knowledge_tree_hash": hashlib.md5(json.dumps(snapshot.knowledge_tree, sort_keys=True).encode()).hexdigest()[:8],
                    "active_mutations_count": len(snapshot.active_mutations),
                    "services_count": len(snapshot.service_states)
                }
                for snapshot in self.snapshots.values()
                if snapshot.snapshot_id.startswith(session_id)
            ]
            
            return {
                "session_id": session_id,
                "snapshots": session_snapshots,
                "count": len(session_snapshots),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        @self.app.get("/snapshot/{snapshot_id}")
        async def get_snapshot_details(snapshot_id: str):
            """Get detailed snapshot data"""
            if snapshot_id in self.snapshots:
                snapshot = self.snapshots[snapshot_id]
                return {
                    "snapshot": asdict(snapshot),
                    "size_bytes": len(json.dumps(asdict(snapshot)).encode()),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            else:
                raise HTTPException(status_code=404, detail="Snapshot not found")
        
        @self.app.post("/trace_operation")
        async def trace_operation(operation_data: Dict[str, Any]):
            """Trace a specific operation"""
            try:
                if not self.current_session_id:
                    raise HTTPException(status_code=400, detail="No active debug session")
                
                result = await self._trace_operation(
                    operation_data.get("operation_type", "unknown"),
                    operation_data.get("input_parameters", {}),
                    operation_data.get("target_service", "orchestrator")
                )
                return result
            except Exception as e:
                logger.error(f"Failed to trace operation: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/operations/{session_id}")
        async def get_operations(session_id: str):
            """Get all traced operations for a session"""
            session_operations = [
                {
                    "operation_id": op.operation_id,
                    "operation_type": op.operation_type,
                    "timestamp": op.timestamp,
                    "duration_ms": op.duration_ms,
                    "service_calls_count": len(op.service_calls),
                    "errors_count": len(op.errors),
                    "state_before": op.system_state_before,
                    "state_after": op.system_state_after
                }
                for op in self.operation_traces.values()
                if op.operation_id.startswith(session_id)
            ]
            
            return {
                "session_id": session_id,
                "operations": session_operations,
                "count": len(session_operations),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        @self.app.post("/replay_operations")
        async def replay_operations(request: ReplayRequest):
            """Replay operations for reproducibility testing"""
            try:
                result = await self._replay_operations(
                    request.session_id,
                    request.operation_ids,
                    request.target_snapshot_id,
                    request.verify_reproducibility
                )
                return result
            except Exception as e:
                logger.error(f"Failed to replay operations: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/create_test_case")
        async def create_test_case(request: TestCaseRequest):
            """Create a deterministic test case"""
            try:
                result = await self._create_test_case(
                    request.name,
                    request.description,
                    request.base_session_id,
                    request.operations_to_include,
                    request.expected_outcomes
                )
                return result
            except Exception as e:
                logger.error(f"Failed to create test case: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/test_cases")
        async def get_test_cases():
            """Get all test cases"""
            return {
                "test_cases": [asdict(test_case) for test_case in self.test_cases.values()],
                "count": len(self.test_cases),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        @self.app.post("/run_test_case/{test_id}")
        async def run_test_case(test_id: str):
            """Run a specific test case"""
            try:
                result = await self._run_test_case(test_id)
                return result
            except Exception as e:
                logger.error(f"Failed to run test case: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/reproducibility_report/{session_id}")
        async def get_reproducibility_report(session_id: str):
            """Generate reproducibility analysis report"""
            try:
                result = await self._generate_reproducibility_report(session_id)
                return result
            except Exception as e:
                logger.error(f"Failed to generate reproducibility report: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/debug_analytics")
        async def get_debug_analytics():
            """Get debug session analytics"""
            try:
                result = await self._generate_debug_analytics()
                return result
            except Exception as e:
                logger.error(f"Failed to generate debug analytics: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health")
        async def health_check():
            """Debug mode health check"""
            try:
                return {
                    "status": "healthy",
                    "service": "DeterministicDebugMode",
                    "version": "2.0.0",
                    "deterministic_mode": self.deterministic_mode,
                    "current_session": self.current_session_id,
                    "active_sessions_count": len(self.active_sessions),
                    "snapshots_count": len(self.snapshots),
                    "operations_count": len(self.operation_traces),
                    "performance_metrics": self.performance_metrics,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
    
    async def _initialize_system(self):
        """Initialize the DeterministicDebugMode system"""
        try:
            # Initialize semantic bus connection
            self.semantic_bus = await get_semantic_bus()
            
            # Create debug data directories
            import os
            os.makedirs(self.debug_data_dir, exist_ok=True)
            os.makedirs(f"{self.debug_data_dir}/sessions", exist_ok=True)
            os.makedirs(f"{self.debug_data_dir}/snapshots", exist_ok=True)
            os.makedirs(f"{self.debug_data_dir}/test_cases", exist_ok=True)
            
            # Load existing test cases
            await self._load_test_cases()
            
            logger.info("DeterministicDebugMode initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize DeterministicDebugMode: {e}")
    
    async def _start_debug_session(self, session_name: str, debug_level: DebugLevel,
                                  reproducibility_mode: ReproducibilityMode, 
                                  capture_interval_seconds: int, enable_state_snapshots: bool,
                                  enable_operation_tracing: bool, random_seed: Optional[int]) -> Dict[str, Any]:
        """Start a new deterministic debug session"""
        
        try:
            session_id = f"debug_{int(datetime.utcnow().timestamp())}"
            
            # Set random seed for reproducibility
            if random_seed is not None:
                self.random_seed = random_seed
                import random
                import numpy as np
                random.seed(random_seed)
                np.random.seed(random_seed)
            
            # Create session configuration
            session_config = {
                "session_id": session_id,
                "name": session_name,
                "debug_level": debug_level,
                "reproducibility_mode": reproducibility_mode,
                "capture_interval_seconds": capture_interval_seconds,
                "enable_state_snapshots": enable_state_snapshots,
                "enable_operation_tracing": enable_operation_tracing,
                "random_seed": self.random_seed,
                "started_at": datetime.utcnow().isoformat() + "Z",
                "status": "active"
            }
            
            self.active_sessions[session_id] = session_config
            self.current_session_id = session_id
            self.deterministic_mode = True
            
            # Capture initial state snapshot
            if enable_state_snapshots:
                initial_snapshot = await self._capture_system_snapshot(session_id)
                session_config["initial_snapshot_id"] = initial_snapshot["snapshot_id"]
            
            # Start periodic snapshot capture if enabled
            if enable_state_snapshots and capture_interval_seconds > 0:
                asyncio.create_task(self._periodic_snapshot_capture(session_id, capture_interval_seconds))
            
            # Update metrics
            self.performance_metrics["sessions_created"] += 1
            
            # Log session start
            logger.info(f"Debug session started: {session_id} - {session_name}")
            
            return {
                "success": True,
                "session_id": session_id,
                "session_config": session_config,
                "message": f"Debug session '{session_name}' started successfully",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error(f"Failed to start debug session: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _stop_debug_session(self, session_id: str) -> Dict[str, Any]:
        """Stop an active debug session"""
        
        try:
            if session_id not in self.active_sessions:
                return {
                    "success": False,
                    "error": f"Session {session_id} not found or already stopped",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            
            session = self.active_sessions[session_id]
            
            # Capture final snapshot
            if session.get("enable_state_snapshots"):
                final_snapshot = await self._capture_system_snapshot(session_id)
                session["final_snapshot_id"] = final_snapshot["snapshot_id"]
            
            # Update session status
            session["status"] = "stopped"
            session["stopped_at"] = datetime.utcnow().isoformat() + "Z"
            
            # Calculate session statistics
            session_operations = [op for op in self.operation_traces.values() if op.operation_id.startswith(session_id)]
            session_snapshots = [snap for snap in self.snapshots.values() if snap.snapshot_id.startswith(session_id)]
            
            session_stats = {
                "operations_traced": len(session_operations),
                "snapshots_captured": len(session_snapshots),
                "duration_seconds": (
                    datetime.fromisoformat(session["stopped_at"].replace('Z', '+00:00')) -
                    datetime.fromisoformat(session["started_at"].replace('Z', '+00:00'))
                ).total_seconds(),
                "avg_operation_duration": (
                    sum(op.duration_ms for op in session_operations) / len(session_operations)
                    if session_operations else 0
                )
            }
            
            session["statistics"] = session_stats
            
            # Save session data to file
            await self._save_session_data(session_id, session)
            
            # Clear current session if it's the one being stopped
            if self.current_session_id == session_id:
                self.current_session_id = None
                self.deterministic_mode = bool(self.active_sessions)
            
            logger.info(f"Debug session stopped: {session_id}")
            
            return {
                "success": True,
                "session_id": session_id,
                "session_statistics": session_stats,
                "message": f"Debug session stopped successfully",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error(f"Failed to stop debug session: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _capture_system_snapshot(self, session_id: str) -> Dict[str, Any]:
        """Capture complete system state snapshot"""
        
        try:
            snapshot_id = f"{session_id}_snapshot_{self.snapshot_counter}"
            self.snapshot_counter += 1
            
            # Collect system state from all services
            system_state = {}
            service_states = {}
            
            for service_name, endpoint in self.service_endpoints.items():
                try:
                    async with aiohttp.ClientSession() as session:
                        # Get service health and metrics
                        async with session.get(f"{endpoint}/health", timeout=10) as response:
                            if response.status == 200:
                                health_data = await response.json()
                                service_states[service_name] = {
                                    "health": health_data,
                                    "endpoint": endpoint,
                                    "timestamp": datetime.utcnow().isoformat() + "Z"
                                }
                        
                        # Get service-specific state if available
                        try:
                            async with session.get(f"{endpoint}/metrics", timeout=10) as response:
                                if response.status == 200:
                                    metrics_data = await response.json()
                                    service_states[service_name]["metrics"] = metrics_data
                        except:
                            pass  # Metrics endpoint might not exist
                            
                except Exception as e:
                    service_states[service_name] = {
                        "error": str(e),
                        "endpoint": endpoint,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
            
            # Load knowledge tree
            knowledge_tree = {}
            try:
                knowledge_tree_path = f"{self.context_dir}/core/knowledge_tree.yaml"
                with open(knowledge_tree_path, 'r', encoding='utf-8') as f:
                    knowledge_tree = yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"Failed to load knowledge tree: {e}")
            
            # Get active mutations (simplified)
            active_mutations = []
            try:
                mutations_dir = f"{self.context_dir}/mutations"
                import os
                if os.path.exists(mutations_dir):
                    for file in os.listdir(mutations_dir):
                        if file.endswith('.json'):
                            with open(os.path.join(mutations_dir, file), 'r') as f:
                                mutation_data = json.load(f)
                                active_mutations.append(mutation_data)
            except Exception as e:
                logger.warning(f"Failed to load mutations: {e}")
            
            # Get context fragments
            context_fragments = {}
            try:
                fragments_dir = f"{self.context_dir}/fragments"
                import os
                if os.path.exists(fragments_dir):
                    for root, dirs, files in os.walk(fragments_dir):
                        for file in files:
                            if file.endswith(('.yaml', '.json')):
                                file_path = os.path.join(root, file)
                                rel_path = os.path.relpath(file_path, fragments_dir)
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        if file.endswith('.yaml'):
                                            context_fragments[rel_path] = yaml.safe_load(f)
                                        else:
                                            context_fragments[rel_path] = json.load(f)
                                except Exception as e:
                                    context_fragments[rel_path] = {"error": str(e)}
            except Exception as e:
                logger.warning(f"Failed to load context fragments: {e}")
            
            # Create comprehensive snapshot
            snapshot = DebugSnapshot(
                snapshot_id=snapshot_id,
                timestamp=datetime.utcnow().isoformat() + "Z",
                system_state=system_state,
                knowledge_tree=knowledge_tree,
                active_mutations=active_mutations,
                service_states=service_states,
                metrics={
                    "total_services": len(service_states),
                    "healthy_services": len([s for s in service_states.values() if s.get("health", {}).get("status") == "healthy"]),
                    "active_mutations_count": len(active_mutations),
                    "context_fragments_count": len(context_fragments)
                },
                context_fragments=context_fragments
            )
            
            # Store snapshot
            self.snapshots[snapshot_id] = snapshot
            
            # Calculate and store state hash for reproducibility tracking
            state_data = {
                "knowledge_tree": knowledge_tree,
                "active_mutations": active_mutations,
                "context_fragments": context_fragments
            }
            state_hash = hashlib.sha256(json.dumps(state_data, sort_keys=True).encode()).hexdigest()
            self.state_hash_history.append((snapshot.timestamp, state_hash))
            
            # Save snapshot to file
            await self._save_snapshot_data(snapshot_id, snapshot)
            
            # Update metrics
            self.performance_metrics["snapshots_captured"] += 1
            
            logger.debug(f"System snapshot captured: {snapshot_id}")
            
            return {
                "success": True,
                "snapshot_id": snapshot_id,
                "timestamp": snapshot.timestamp,
                "services_captured": len(service_states),
                "state_hash": state_hash[:16],  # First 16 chars for identification
                "size_estimate": len(json.dumps(asdict(snapshot)).encode())
            }
            
        except Exception as e:
            logger.error(f"Failed to capture system snapshot: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _trace_operation(self, operation_type: str, input_parameters: Dict[str, Any],
                              target_service: str) -> Dict[str, Any]:
        """Trace a specific operation for reproducibility"""
        
        try:
            if not self.current_session_id:
                return {"success": False, "error": "No active debug session"}
            
            operation_id = f"{self.current_session_id}_op_{self.operation_counter}"
            self.operation_counter += 1
            
            start_time = datetime.utcnow()
            
            # Capture system state before operation
            before_snapshot = await self._capture_system_snapshot(self.current_session_id)
            before_snapshot_id = before_snapshot.get("snapshot_id", "unknown")
            
            # Record randomness seeds
            randomness_seeds = {
                "python_random_state": str(getattr(__import__('random'), 'getstate', lambda: None)()),
                "numpy_random_state": str(getattr(__import__('numpy.random'), 'get_state', lambda: None)()),
                "operation_seed": self.random_seed,
                "timestamp_seed": int(start_time.timestamp())
            }
            
            # Execute operation and track service calls
            service_calls = []
            errors = []
            output_result = {}
            
            try:
                # Simulate operation execution (in real implementation, this would intercept actual calls)
                if target_service in self.service_endpoints:
                    endpoint = self.service_endpoints[target_service]
                    
                    async with aiohttp.ClientSession() as session:
                        # Log the service call
                        service_call = {
                            "service": target_service,
                            "endpoint": endpoint,
                            "operation_type": operation_type,
                            "input_parameters": copy.deepcopy(input_parameters),
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                        
                        # Make actual service call based on operation type
                        if operation_type == "health_check":
                            async with session.get(f"{endpoint}/health", timeout=30) as response:
                                service_call["response_status"] = response.status
                                if response.status == 200:
                                    output_result = await response.json()
                                    service_call["response_data"] = output_result
                                else:
                                    error = {"type": "http_error", "status": response.status, "url": f"{endpoint}/health"}
                                    errors.append(error)
                        
                        elif operation_type == "validate_coherence":
                            async with session.post(f"{endpoint}/validate_coherence", 
                                                   json=input_parameters, timeout=30) as response:
                                service_call["response_status"] = response.status
                                if response.status == 200:
                                    output_result = await response.json()
                                    service_call["response_data"] = output_result
                                else:
                                    error = {"type": "http_error", "status": response.status, "url": f"{endpoint}/validate_coherence"}
                                    errors.append(error)
                        
                        # Add more operation types as needed
                        
                        service_calls.append(service_call)
                        
                else:
                    error = {"type": "unknown_service", "service": target_service}
                    errors.append(error)
                    
            except Exception as e:
                error = {"type": "execution_error", "message": str(e)}
                errors.append(error)
            
            # Capture system state after operation
            after_snapshot = await self._capture_system_snapshot(self.current_session_id)
            after_snapshot_id = after_snapshot.get("snapshot_id", "unknown")
            
            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            # Create operation trace
            operation_trace = OperationTrace(
                operation_id=operation_id,
                operation_type=operation_type,
                timestamp=start_time.isoformat() + "Z",
                input_parameters=copy.deepcopy(input_parameters),
                system_state_before=before_snapshot_id,
                system_state_after=after_snapshot_id,
                output_result=copy.deepcopy(output_result),
                duration_ms=duration_ms,
                service_calls=service_calls,
                randomness_seeds=randomness_seeds,
                errors=errors
            )
            
            # Store operation trace
            self.operation_traces[operation_id] = operation_trace
            
            # Log operation for external analysis
            self.external_call_log.append({
                "operation_id": operation_id,
                "timestamp": operation_trace.timestamp,
                "target_service": target_service,
                "operation_type": operation_type,
                "duration_ms": duration_ms,
                "success": len(errors) == 0
            })
            
            # Update metrics
            self.performance_metrics["operations_traced"] += 1
            
            logger.debug(f"Operation traced: {operation_id} - {operation_type}")
            
            return {
                "success": True,
                "operation_id": operation_id,
                "operation_trace": asdict(operation_trace),
                "duration_ms": duration_ms,
                "errors_count": len(errors),
                "service_calls_count": len(service_calls),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error(f"Failed to trace operation: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _periodic_snapshot_capture(self, session_id: str, interval_seconds: int):
        """Periodically capture system snapshots"""
        
        while session_id in self.active_sessions and self.active_sessions[session_id]["status"] == "active":
            try:
                await asyncio.sleep(interval_seconds)
                if session_id in self.active_sessions and self.active_sessions[session_id]["status"] == "active":
                    await self._capture_system_snapshot(session_id)
            except Exception as e:
                logger.error(f"Periodic snapshot capture failed: {e}")
    
    async def _save_session_data(self, session_id: str, session_data: Dict[str, Any]):
        """Save session data to file"""
        try:
            session_file = f"{self.debug_data_dir}/sessions/{session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save session data: {e}")
    
    async def _save_snapshot_data(self, snapshot_id: str, snapshot: DebugSnapshot):
        """Save snapshot data to file"""
        try:
            snapshot_file = f"{self.debug_data_dir}/snapshots/{snapshot_id}.json"
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(snapshot), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save snapshot data: {e}")
    
    async def _load_test_cases(self):
        """Load existing test cases from files"""
        try:
            import os
            test_cases_dir = f"{self.debug_data_dir}/test_cases"
            if os.path.exists(test_cases_dir):
                for file in os.listdir(test_cases_dir):
                    if file.endswith('.json'):
                        test_case_path = os.path.join(test_cases_dir, file)
                        with open(test_case_path, 'r', encoding='utf-8') as f:
                            test_case_data = json.load(f)
                            test_case = TestCase(**test_case_data)
                            self.test_cases[test_case.test_id] = test_case
                logger.info(f"Loaded {len(self.test_cases)} test cases")
        except Exception as e:
            logger.error(f"Failed to load test cases: {e}")
    
    # Placeholder methods for complex functionality (to be implemented)
    async def _replay_operations(self, session_id: str, operation_ids: List[str], 
                                target_snapshot_id: Optional[str], verify_reproducibility: bool): 
        return {"status": "not_implemented", "message": "Operation replay functionality pending implementation"}
    
    async def _create_test_case(self, name: str, description: str, base_session_id: Optional[str],
                               operations_to_include: List[str], expected_outcomes: Dict[str, Any]):
        return {"status": "not_implemented", "message": "Test case creation functionality pending implementation"}
    
    async def _run_test_case(self, test_id: str):
        return {"status": "not_implemented", "message": "Test case execution functionality pending implementation"}
    
    async def _generate_reproducibility_report(self, session_id: str):
        return {"status": "not_implemented", "message": "Reproducibility reporting functionality pending implementation"}
    
    async def _generate_debug_analytics(self):
        return {
            "performance_metrics": self.performance_metrics,
            "active_sessions": len(self.active_sessions),
            "total_snapshots": len(self.snapshots),
            "total_operations": len(self.operation_traces),
            "deterministic_mode": self.deterministic_mode,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

# Global instance
deterministic_debug = DeterministicDebugMode()

# FastAPI app instance for uvicorn
app = deterministic_debug.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8029)