"""
Test Service API for Scenario-CoD Integration
Provides REST API for running debate quality tests and monitoring results
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import structlog

from test_scenarios import CoDTestSuite
from config import get_config, DEBATE_SCENARIOS, JUDGE_CRITERIA_CONFIGS

logger = structlog.get_logger(__name__)

app = FastAPI(
    title="UltraMCP Scenario-CoD Testing Service",
    description="Quality assurance and testing framework for Chain-of-Debate protocols",
    version="1.0.0"
)

# Global state
test_results_store = {}
active_tests = {}
config = get_config()


class TestRequest(BaseModel):
    """Request model for running tests"""
    test_type: str
    topic: Optional[str] = None
    agents_config: Optional[Dict[str, Any]] = None
    quality_threshold: Optional[float] = None
    max_turns: Optional[int] = None
    use_local_models: Optional[bool] = None


class TestResult(BaseModel):
    """Response model for test results"""
    test_id: str
    test_type: str
    status: str  # "running", "completed", "failed"
    success: Optional[bool] = None
    reason: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "UltraMCP Scenario-CoD Testing Framework",
        "version": "1.0.0",
        "description": "Quality assurance for Chain-of-Debate protocols",
        "endpoints": {
            "health": "/health",
            "run_test": "/test/run",
            "test_status": "/test/{test_id}",
            "test_results": "/test/{test_id}/results",
            "available_tests": "/tests/available",
            "comprehensive_suite": "/tests/comprehensive"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test connections to dependencies
        import httpx
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check CoD service
            try:
                cod_response = await client.get(f"{config.cod_service_url}/health")
                cod_healthy = cod_response.status_code == 200
            except:
                cod_healthy = False
            
            # Check local models
            try:
                local_response = await client.get(f"{config.local_models_url}/models")
                local_healthy = local_response.status_code == 200
            except:
                local_healthy = False
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(),
            "dependencies": {
                "cod_service": "healthy" if cod_healthy else "unhealthy",
                "local_models": "healthy" if local_healthy else "unhealthy"
            },
            "active_tests": len(active_tests),
            "test_results_stored": len(test_results_store)
        }
    
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now()
            }
        )


@app.get("/tests/available")
async def get_available_tests():
    """Get list of available test scenarios"""
    return {
        "scenarios": DEBATE_SCENARIOS,
        "judge_criteria": JUDGE_CRITERIA_CONFIGS,
        "config": {
            "test_mode": config.test_mode.value,
            "quality_thresholds": {
                "basic": config.basic_quality_threshold,
                "strict": config.strict_quality_threshold,
                "evidence": config.evidence_quality_threshold
            },
            "supported_topics": config.test_topics
        }
    }


@app.post("/test/run")
async def run_test(request: TestRequest, background_tasks: BackgroundTasks):
    """Run a specific test scenario"""
    
    test_id = str(uuid.uuid4())
    
    # Validate test type
    if request.test_type not in DEBATE_SCENARIOS:
        available_tests = list(DEBATE_SCENARIOS.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Invalid test type. Available: {available_tests}"
        )
    
    # Create test result entry
    test_result = TestResult(
        test_id=test_id,
        test_type=request.test_type,
        status="running",
        started_at=datetime.now()
    )
    
    test_results_store[test_id] = test_result
    active_tests[test_id] = test_result
    
    # Run test in background
    background_tasks.add_task(execute_test, test_id, request)
    
    logger.info("Test started", test_id=test_id, test_type=request.test_type)
    
    return {
        "test_id": test_id,
        "status": "started",
        "test_type": request.test_type,
        "estimated_duration": "2-5 minutes"
    }


@app.get("/test/{test_id}")
async def get_test_status(test_id: str):
    """Get test status"""
    if test_id not in test_results_store:
        raise HTTPException(status_code=404, detail="Test not found")
    
    return test_results_store[test_id]


@app.get("/test/{test_id}/results")
async def get_test_results(test_id: str):
    """Get detailed test results"""
    if test_id not in test_results_store:
        raise HTTPException(status_code=404, detail="Test not found")
    
    result = test_results_store[test_id]
    
    if result.status == "running":
        return {
            "test_id": test_id,
            "status": "running",
            "message": "Test still in progress"
        }
    
    return result


@app.post("/tests/comprehensive")
async def run_comprehensive_suite(background_tasks: BackgroundTasks):
    """Run the comprehensive test suite"""
    
    test_id = str(uuid.uuid4())
    
    test_result = TestResult(
        test_id=test_id,
        test_type="comprehensive_suite",
        status="running", 
        started_at=datetime.now()
    )
    
    test_results_store[test_id] = test_result
    active_tests[test_id] = test_result
    
    # Run comprehensive suite in background
    background_tasks.add_task(execute_comprehensive_suite, test_id)
    
    logger.info("Comprehensive test suite started", test_id=test_id)
    
    return {
        "test_id": test_id,
        "status": "started",
        "test_type": "comprehensive_suite",
        "estimated_duration": "10-20 minutes"
    }


@app.get("/tests/results")
async def get_all_test_results():
    """Get summary of all test results"""
    
    summary = {
        "total_tests": len(test_results_store),
        "active_tests": len(active_tests),
        "completed_tests": len([r for r in test_results_store.values() if r.status == "completed"]),
        "failed_tests": len([r for r in test_results_store.values() if r.status == "failed"]),
        "recent_results": list(test_results_store.values())[-10:]  # Last 10 results
    }
    
    return summary


@app.delete("/tests/results")
async def clear_test_results():
    """Clear all stored test results"""
    global test_results_store, active_tests
    
    # Don't clear active tests
    cleared_count = len(test_results_store) - len(active_tests)
    
    # Keep only active tests
    test_results_store = {k: v for k, v in test_results_store.items() if k in active_tests}
    
    return {
        "message": f"Cleared {cleared_count} test results",
        "remaining_active": len(active_tests)
    }


# Background task functions

async def execute_test(test_id: str, request: TestRequest):
    """Execute individual test scenario"""
    
    try:
        suite = CoDTestSuite(cod_service_url=config.cod_service_url)
        
        # Map test types to methods
        test_methods = {
            "basic_two_agent": suite.run_basic_debate_test,
            "moderated_debate": suite.run_moderated_debate_test,
            "evidence_intensive": suite.run_evidence_quality_test,
            "fallacy_resistance": suite.run_fallacy_resistance_test,
            "consensus_building": suite.run_consensus_building_test,
            "local_models_only": suite.run_local_models_test
        }
        
        test_method = test_methods.get(request.test_type)
        if not test_method:
            raise ValueError(f"Unknown test method for {request.test_type}")
        
        # Execute the test
        result = await test_method()
        
        # Update stored result
        test_result = test_results_store[test_id]
        test_result.status = "completed"
        test_result.success = result["success"]
        test_result.reason = result["reason"]
        test_result.metrics = result.get("metrics", {})
        test_result.completed_at = datetime.now()
        test_result.duration_seconds = (test_result.completed_at - test_result.started_at).total_seconds()
        
        # Remove from active tests
        if test_id in active_tests:
            del active_tests[test_id]
        
        logger.info(
            "Test completed",
            test_id=test_id,
            success=result["success"],
            duration=test_result.duration_seconds
        )
    
    except Exception as e:
        logger.error("Test execution failed", test_id=test_id, error=str(e))
        
        # Update stored result with error
        test_result = test_results_store[test_id]
        test_result.status = "failed"
        test_result.success = False
        test_result.reason = f"Test execution error: {str(e)}"
        test_result.completed_at = datetime.now()
        test_result.duration_seconds = (test_result.completed_at - test_result.started_at).total_seconds()
        
        # Remove from active tests
        if test_id in active_tests:
            del active_tests[test_id]


async def execute_comprehensive_suite(test_id: str):
    """Execute comprehensive test suite"""
    
    try:
        suite = CoDTestSuite(cod_service_url=config.cod_service_url)
        
        # Run comprehensive suite
        results = await suite.run_comprehensive_test_suite()
        
        # Calculate summary metrics
        total_tests = len(results)
        successful_tests = sum(1 for r in results.values() if r["success"])
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Update stored result
        test_result = test_results_store[test_id]
        test_result.status = "completed"
        test_result.success = success_rate >= 70  # 70% success rate threshold
        test_result.reason = f"Comprehensive suite: {successful_tests}/{total_tests} tests passed ({success_rate:.1f}%)"
        test_result.metrics = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": success_rate,
            "individual_results": results
        }
        test_result.completed_at = datetime.now()
        test_result.duration_seconds = (test_result.completed_at - test_result.started_at).total_seconds()
        
        # Remove from active tests
        if test_id in active_tests:
            del active_tests[test_id]
        
        logger.info(
            "Comprehensive suite completed",
            test_id=test_id,
            success_rate=success_rate,
            duration=test_result.duration_seconds
        )
    
    except Exception as e:
        logger.error("Comprehensive suite failed", test_id=test_id, error=str(e))
        
        # Update stored result with error
        test_result = test_results_store[test_id]
        test_result.status = "failed" 
        test_result.success = False
        test_result.reason = f"Suite execution error: {str(e)}"
        test_result.completed_at = datetime.now()
        test_result.duration_seconds = (test_result.completed_at - test_result.started_at).total_seconds()
        
        # Remove from active tests
        if test_id in active_tests:
            del active_tests[test_id]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8013)