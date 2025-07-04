#!/usr/bin/env python3
"""
UltraMCP ContextBuilderAgent 2.0 - Main Orchestrator
Coordinates all ContextBuilderAgent components for semantic coherence
"""

import asyncio
import aiohttp
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import json
import yaml
from semantic_coherence_bus import get_semantic_bus, ContextMutation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContextBuilderRequest(BaseModel):
    context_data: Dict[str, Any]
    operation: str  # "validate", "mutate", "optimize", "analyze"
    parameters: Optional[Dict[str, Any]] = None

class ContextBuilderResponse(BaseModel):
    success: bool
    operation: str
    results: Dict[str, Any]
    timestamp: str
    processing_time_ms: float

class SessionInsightRequest(BaseModel):
    meeting_transcript: str
    context_domain: str = "general"
    analysis_depth: str = "standard"  # "basic", "standard", "deep"

class SessionInsightResponse(BaseModel):
    session_insights: Dict[str, Any]
    proposed_mutations: List[Dict[str, Any]]
    coherence_score: float
    timestamp: str

class ContextBuilderOrchestrator:
    """
    Main orchestrator for ContextBuilderAgent 2.0
    Coordinates semantic coherence across all microservices
    """
    
    def __init__(self):
        self.app = FastAPI(title="ContextBuilderAgent Orchestrator", version="2.0.0")
        self.semantic_bus = None
        self.service_endpoints = {
            "drift_detector": "http://localhost:8020",
            "contradiction_resolver": "http://localhost:8021", 
            "belief_reviser": "http://localhost:8022",
            "utility_predictor": "http://localhost:8023",
            "memory_tuner": "http://localhost:8026"
        }
        self.knowledge_tree_path = "/root/ultramcp/.context/core/knowledge_tree.yaml"
        self.performance_metrics = {
            "operations_processed": 0,
            "mutations_applied": 0,
            "coherence_validations": 0,
            "avg_processing_time_ms": 0.0,
            "last_operation": None
        }
        
        # Initialize FastAPI routes
        self._setup_routes()
        
        # Add startup event handler
        @self.app.on_event("startup")
        async def startup_event():
            await self._initialize_system()
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.post("/process_context", response_model=ContextBuilderResponse)
        async def process_context(request: ContextBuilderRequest, background_tasks: BackgroundTasks):
            """Main entry point for context processing"""
            try:
                start_time = datetime.utcnow()
                
                result = await self._process_context_operation(
                    request.context_data,
                    request.operation,
                    request.parameters or {}
                )
                
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Update metrics
                self.performance_metrics["operations_processed"] += 1
                self.performance_metrics["avg_processing_time_ms"] = (
                    (self.performance_metrics["avg_processing_time_ms"] * (self.performance_metrics["operations_processed"] - 1) + processing_time) /
                    self.performance_metrics["operations_processed"]
                )
                self.performance_metrics["last_operation"] = datetime.utcnow().isoformat() + "Z"
                
                return ContextBuilderResponse(
                    success=result["success"],
                    operation=request.operation,
                    results=result,
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    processing_time_ms=processing_time
                )
                
            except Exception as e:
                logger.error(f"Error processing context operation: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/analyze_session", response_model=SessionInsightResponse)
        async def analyze_session(request: SessionInsightRequest):
            """Analyze meeting transcript and generate session insights"""
            try:
                result = await self._analyze_session_transcript(
                    request.meeting_transcript,
                    request.context_domain,
                    request.analysis_depth
                )
                
                return SessionInsightResponse(**result)
                
            except Exception as e:
                logger.error(f"Error analyzing session: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/apply_mutation")
        async def apply_mutation(mutation_data: Dict[str, Any]):
            """Apply a context mutation"""
            try:
                result = await self._apply_context_mutation(mutation_data)
                
                if result["success"]:
                    self.performance_metrics["mutations_applied"] += 1
                
                return result
            except Exception as e:
                logger.error(f"Error applying mutation: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/validate_coherence")
        async def validate_coherence():
            """Validate semantic coherence across all contexts"""
            try:
                result = await self._validate_semantic_coherence()
                self.performance_metrics["coherence_validations"] += 1
                return result
            except Exception as e:
                logger.error(f"Error validating coherence: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/system_status")
        async def get_system_status():
            """Get complete system status"""
            try:
                return await self._get_system_status()
            except Exception as e:
                logger.error(f"Error getting system status: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/knowledge_tree")
        async def get_knowledge_tree():
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
                services_healthy = await self._check_all_services_health()
                semantic_bus_healthy = self.semantic_bus is not None
                
                return {
                    "status": "healthy" if services_healthy and semantic_bus_healthy else "degraded",
                    "services_healthy": services_healthy,
                    "semantic_bus_connected": semantic_bus_healthy,
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
            return {
                **self.performance_metrics,
                "service_endpoints": self.service_endpoints,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _initialize_system(self):
        """Initialize the ContextBuilderAgent system"""
        try:
            # Initialize semantic coherence bus
            self.semantic_bus = await get_semantic_bus()
            
            # Wait for services to be ready
            await self._wait_for_services()
            
            logger.info("ContextBuilderAgent Orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ContextBuilderAgent: {e}")
    
    async def _wait_for_services(self, max_wait_time: int = 60):
        """Wait for all services to be ready"""
        start_time = datetime.utcnow()
        
        while (datetime.utcnow() - start_time).total_seconds() < max_wait_time:
            all_healthy = True
            
            for service_name, endpoint in self.service_endpoints.items():
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{endpoint}/health", timeout=5) as response:
                            if response.status != 200:
                                all_healthy = False
                                break
                except:
                    all_healthy = False
                    break
            
            if all_healthy:
                logger.info("All services are ready")
                return
            
            await asyncio.sleep(5)
        
        logger.warning("Some services may not be ready after waiting")
    
    async def _process_context_operation(self, context_data: Dict[str, Any], 
                                       operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process context operation based on type"""
        
        if operation == "validate":
            return await self._validate_context(context_data, parameters)
        elif operation == "mutate":
            return await self._mutate_context(context_data, parameters)
        elif operation == "optimize":
            return await self._optimize_context(context_data, parameters)
        elif operation == "analyze":
            return await self._analyze_context(context_data, parameters)
        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _validate_context(self, context_data: Dict[str, Any], 
                               parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate context for semantic coherence"""
        try:
            validation_results = {}
            
            # Load current knowledge tree for comparison
            current_knowledge = await self._load_knowledge_tree()
            
            # Check for drift
            drift_result = await self._call_service(
                "drift_detector", 
                "/detect_drift",
                {
                    "current_context": context_data,
                    "previous_context": current_knowledge,
                    "domain": parameters.get("domain", "ORGANIZACION"),
                    "confidence_threshold": parameters.get("threshold", 0.78)
                }
            )
            validation_results["drift_detection"] = drift_result
            
            # Check for contradictions if any are found
            if drift_result and drift_result.get("drift_detected"):
                contradiction_check = await self._check_contradictions(context_data, current_knowledge)
                validation_results["contradiction_analysis"] = contradiction_check
            
            # Calculate overall coherence score
            coherence_score = self._calculate_coherence_score(validation_results)
            
            return {
                "success": True,
                "coherence_score": coherence_score,
                "validation_results": validation_results,
                "requires_attention": coherence_score < 0.8,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error(f"Context validation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _mutate_context(self, context_data: Dict[str, Any], 
                             parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply context mutation with validation"""
        try:
            # Predict utility of mutation
            utility_result = await self._call_service(
                "utility_predictor",
                "/predict_utility",
                {
                    "mutation_data": context_data,
                    "context_state": await self._load_knowledge_tree(),
                    "historical_success_rate": parameters.get("success_rate", 0.7)
                }
            )
            
            # Check if utility is high enough
            if utility_result and utility_result.get("utility_score", 0) < parameters.get("min_utility", 0.6):
                return {
                    "success": False,
                    "reason": "Utility score too low",
                    "utility_result": utility_result,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            
            # Apply mutation via belief reviser
            revision_result = await self._call_service(
                "belief_reviser",
                "/revise_belief",
                {
                    "domain": parameters.get("domain", "ORGANIZACION"),
                    "field": parameters.get("field", "nombre_empresa"),
                    "new_value": context_data.get("new_value"),
                    "confidence_delta": parameters.get("confidence_delta", 0.1),
                    "trust_signal": utility_result.get("confidence", 0.8),
                    "source": parameters.get("source", "orchestrator"),
                    "reason": parameters.get("reason", "Automated mutation")
                }
            )
            
            # Publish mutation to semantic bus if successful
            if revision_result and revision_result.get("revision_applied"):
                mutation = ContextMutation(
                    mutation_id=f"mutation_{int(datetime.utcnow().timestamp())}",
                    mutation_type="UPDATE_FIELD",
                    target_domain=f"{parameters.get('domain', 'ORGANIZACION')}.{parameters.get('field', 'nombre_empresa')}",
                    new_value=context_data.get("new_value"),
                    previous_value=context_data.get("previous_value"),
                    confidence=utility_result.get("confidence", 0.8),
                    requires_cod_validation=utility_result.get("confidence", 0.8) < 0.3,
                    source=parameters.get("source", "orchestrator"),
                    timestamp=datetime.utcnow().isoformat() + "Z"
                )
                
                await self.semantic_bus.publish_context_mutation(mutation)
            
            return {
                "success": revision_result.get("revision_applied", False),
                "utility_result": utility_result,
                "revision_result": revision_result,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error(f"Context mutation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _optimize_context(self, context_data: Dict[str, Any], 
                               parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize context thresholds and parameters"""
        try:
            optimization_results = {}
            
            # Optimize thresholds via memory tuner
            for metric in ["context_overlap_ratio", "embedding_similarity", "belief_consistency_index"]:
                optimization_result = await self._call_service(
                    "memory_tuner",
                    "/optimize_threshold",
                    {
                        "metric_name": metric,
                        "current_value": parameters.get(f"current_{metric}", 0.8),
                        "target_performance": parameters.get("target_performance", 0.85),
                        "optimization_window_hours": parameters.get("window_hours", 24)
                    }
                )
                optimization_results[metric] = optimization_result
            
            # Apply optimizations if they show improvement
            applied_optimizations = []
            for metric, result in optimization_results.items():
                if (result and result.get("expected_improvement", 0) > 0.05 and 
                    result.get("confidence", 0) > 0.6):
                    
                    apply_result = await self._call_service(
                        "memory_tuner",
                        "/apply_threshold_adjustment",
                        {
                            "metric_name": metric,
                            "new_value": result["optimized_threshold"],
                            "reason": f"Optimization: {result['adaptation_reason']}"
                        }
                    )
                    applied_optimizations.append({
                        "metric": metric,
                        "result": apply_result
                    })
            
            return {
                "success": True,
                "optimization_results": optimization_results,
                "applied_optimizations": applied_optimizations,
                "total_optimizations": len(applied_optimizations),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error(f"Context optimization failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _analyze_context(self, context_data: Dict[str, Any], 
                              parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze context for patterns and insights"""
        try:
            analysis_results = {}
            
            # Pattern analysis via memory tuner
            pattern_result = await self._call_service(
                "memory_tuner",
                "/analyze_patterns",
                {
                    "context_history": parameters.get("context_history", [context_data]),
                    "analysis_window_hours": parameters.get("window_hours", 48)
                }
            )
            analysis_results["pattern_analysis"] = pattern_result
            
            # Performance trends
            trends_result = await self._call_service(
                "memory_tuner",
                "/performance_trends"
            )
            analysis_results["performance_trends"] = trends_result
            
            return {
                "success": True,
                "analysis_results": analysis_results,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error(f"Context analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _analyze_session_transcript(self, transcript: str, domain: str, 
                                        depth: str) -> Dict[str, Any]:
        """Analyze meeting transcript and generate session insights"""
        try:
            # Simple transcript analysis (in production, would use LLM)
            insights = {
                "pain_points_explicit": [],
                "objetivos_declarados": [],
                "senales_oportunidad": [],
                "banderas_contradiccion": [],
                "insights_implicitos": []
            }
            
            # Basic keyword analysis
            pain_keywords = ["problema", "dificultad", "falla", "error", "issue", "challenge"]
            goal_keywords = ["objetivo", "meta", "target", "goal", "quiero", "necesito"]
            
            sentences = transcript.lower().split('.')
            
            for sentence in sentences:
                if any(keyword in sentence for keyword in pain_keywords):
                    insights["pain_points_explicit"].append({
                        "content": sentence.strip(),
                        "confidence": 0.8,
                        "source": "transcript_analysis",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    })
                
                if any(keyword in sentence for keyword in goal_keywords):
                    insights["objetivos_declarados"].append({
                        "content": sentence.strip(),
                        "confidence": 0.7,
                        "source": "transcript_analysis",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    })
            
            # Generate proposed mutations
            proposed_mutations = []
            
            for pain_point in insights["pain_points_explicit"]:
                proposed_mutations.append({
                    "mutation_id": f"add_pain_point_{int(datetime.utcnow().timestamp())}",
                    "type": "ADD_INSIGHT",
                    "target_domain": "PAIN_POINTS.problemas_actuales",
                    "confidence": pain_point["confidence"],
                    "requires_cod_validation": False,
                    "new_value": pain_point["content"],
                    "source": "session_analysis"
                })
            
            # Calculate coherence score
            coherence_score = min(1.0, 0.8 + (len(insights["objetivos_declarados"]) * 0.05))
            
            return {
                "session_insights": insights,
                "proposed_mutations": proposed_mutations,
                "coherence_score": coherence_score,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error(f"Session analysis failed: {e}")
            return {
                "session_insights": {},
                "proposed_mutations": [],
                "coherence_score": 0.0,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _call_service(self, service_name: str, endpoint: str, 
                           data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Call a specific service endpoint"""
        try:
            service_url = self.service_endpoints.get(service_name)
            if not service_url:
                logger.error(f"Unknown service: {service_name}")
                return None
            
            url = f"{service_url}{endpoint}"
            
            async with aiohttp.ClientSession() as session:
                if data:
                    async with session.post(url, json=data, timeout=30) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            logger.error(f"Service {service_name} returned {response.status}")
                            return None
                else:
                    async with session.get(url, timeout=30) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            logger.error(f"Service {service_name} returned {response.status}")
                            return None
                            
        except Exception as e:
            logger.error(f"Error calling service {service_name}: {e}")
            return None
    
    async def _check_contradictions(self, context1: Dict[str, Any], 
                                   context2: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for contradictions between contexts"""
        conflicting_statements = [
            {"content": str(context1), "source": "new_context", "confidence": 0.8},
            {"content": str(context2), "source": "existing_context", "confidence": 0.9}
        ]
        
        return await self._call_service(
            "contradiction_resolver",
            "/resolve_contradiction",
            {
                "conflicting_statements": conflicting_statements,
                "context_domain": "general",
                "confidence_threshold": 0.85
            }
        )
    
    def _calculate_coherence_score(self, validation_results: Dict[str, Any]) -> float:
        """Calculate overall coherence score from validation results"""
        base_score = 0.8
        
        # Penalize for drift
        if validation_results.get("drift_detection", {}).get("drift_detected"):
            similarity = validation_results["drift_detection"].get("similarity_score", 0.8)
            base_score *= similarity
        
        # Penalize for contradictions
        if validation_results.get("contradiction_analysis", {}).get("resolution_found") is False:
            base_score *= 0.7
        
        return max(0.0, min(1.0, base_score))
    
    async def _load_knowledge_tree(self) -> Dict[str, Any]:
        """Load current knowledge tree"""
        try:
            with open(self.knowledge_tree_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load knowledge tree: {e}")
            return {}
    
    async def _check_all_services_health(self) -> bool:
        """Check health of all services"""
        try:
            for service_name, endpoint in self.service_endpoints.items():
                health_result = await self._call_service(service_name, "/health")
                if not health_result or health_result.get("status") not in ["healthy", "degraded"]:
                    return False
            return True
        except:
            return False
    
    async def _get_system_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        status = {
            "orchestrator": {
                "status": "healthy",
                "metrics": self.performance_metrics
            },
            "services": {},
            "semantic_bus": {
                "connected": self.semantic_bus is not None,
                "metrics": await self.semantic_bus.get_performance_metrics() if self.semantic_bus else {}
            }
        }
        
        # Get status from each service
        for service_name, endpoint in self.service_endpoints.items():
            service_status = await self._call_service(service_name, "/health")
            service_metrics = await self._call_service(service_name, "/metrics")
            
            status["services"][service_name] = {
                "status": service_status.get("status", "unknown") if service_status else "unreachable",
                "metrics": service_metrics or {}
            }
        
        return status
    
    async def _apply_context_mutation(self, mutation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a context mutation"""
        try:
            return await self._mutate_context(
                mutation_data,
                {
                    "domain": mutation_data.get("target_domain", "ORGANIZACION").split(".")[0],
                    "field": mutation_data.get("target_domain", "ORGANIZACION").split(".")[-1],
                    "source": mutation_data.get("source", "manual"),
                    "reason": mutation_data.get("reason", "Manual mutation"),
                    "confidence_delta": 0.1
                }
            )
        except Exception as e:
            logger.error(f"Failed to apply mutation: {e}")
            return {"success": False, "error": str(e)}
    
    async def _validate_semantic_coherence(self) -> Dict[str, Any]:
        """Validate semantic coherence across all contexts"""
        try:
            knowledge_tree = await self._load_knowledge_tree()
            
            validation_result = await self._validate_context(
                knowledge_tree,
                {"domain": "ALL", "threshold": 0.78}
            )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Coherence validation failed: {e}")
            return {"success": False, "error": str(e)}

# Global instance
orchestrator = ContextBuilderOrchestrator()

# FastAPI app instance for uvicorn
app = orchestrator.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8025)