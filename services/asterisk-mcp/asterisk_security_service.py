#!/usr/bin/env python3
"""
Asterisk MCP Security Service
Enterprise-grade security scanning and analysis service
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import the existing security client
from asterisk_security_client import SecurityScanner, ComplianceChecker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Asterisk MCP Security Service",
    description="Enterprise-grade security scanning and analysis",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ScanRequest(BaseModel):
    scan_type: str  # "codebase", "snippet", "file"
    target: str     # Path or code content
    options: Dict[str, Any] = {}

class VulnerabilityAnalysisRequest(BaseModel):
    file_path: str
    context: Dict[str, Any] = {}

class ComplianceCheckRequest(BaseModel):
    standard: str   # "SOC2", "GDPR", "HIPAA", "ISO27001", "PCI_DSS"
    scope: str = "full"

class ThreatModelRequest(BaseModel):
    scope: str
    assets: List[str] = []
    attack_vectors: List[str] = []

# Initialize services
security_scanner = SecurityScanner()
compliance_checker = ComplianceChecker()

# Global state
active_scans = {}
scan_results_cache = {}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "asterisk-mcp-security",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/v1/status")
async def get_service_status():
    """Get detailed service status"""
    return {
        "service": "asterisk-mcp-security",
        "status": "running",
        "active_scans": len(active_scans),
        "cached_results": len(scan_results_cache),
        "features": [
            "vulnerability_scanning",
            "compliance_checking", 
            "threat_modeling",
            "security_analysis"
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/scan/snippet")
async def scan_code_snippet(request: ScanRequest, background_tasks: BackgroundTasks):
    """Scan a code snippet for vulnerabilities"""
    try:
        scan_id = f"snippet_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Start background scan
        background_tasks.add_task(
            run_snippet_scan,
            scan_id,
            request.target,
            request.options
        )
        
        active_scans[scan_id] = {
            "type": "snippet",
            "status": "running",
            "started_at": datetime.now().isoformat()
        }
        
        return {
            "scan_id": scan_id,
            "status": "started",
            "message": "Code snippet security scan initiated"
        }
        
    except Exception as e:
        logger.error(f"Snippet scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/scan/codebase")
async def scan_codebase(request: ScanRequest, background_tasks: BackgroundTasks):
    """Scan entire codebase for vulnerabilities"""
    try:
        scan_id = f"codebase_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Validate path
        target_path = Path(request.target)
        if not target_path.exists():
            raise HTTPException(status_code=400, detail="Target path does not exist")
        
        # Start background scan
        background_tasks.add_task(
            run_codebase_scan,
            scan_id,
            str(target_path),
            request.options
        )
        
        active_scans[scan_id] = {
            "type": "codebase",
            "status": "running",
            "target": str(target_path),
            "started_at": datetime.now().isoformat()
        }
        
        return {
            "scan_id": scan_id,
            "status": "started",
            "target": str(target_path),
            "message": "Codebase security scan initiated"
        }
        
    except Exception as e:
        logger.error(f"Codebase scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/vulnerability/analyze")
async def analyze_vulnerability(request: VulnerabilityAnalysisRequest):
    """Analyze specific file for vulnerabilities"""
    try:
        file_path = Path(request.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=400, detail="File does not exist")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Analyze with security scanner
        analysis = await security_scanner.analyze_code_snippet(
            content=content,
            file_path=str(file_path),
            context=request.context
        )
        
        return {
            "file_path": str(file_path),
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Vulnerability analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/compliance/check")
async def check_compliance(request: ComplianceCheckRequest):
    """Check compliance against security standards"""
    try:
        # Run compliance check
        compliance_result = await compliance_checker.check_compliance(
            standard=request.standard,
            scope=request.scope
        )
        
        return {
            "standard": request.standard,
            "scope": request.scope,
            "compliance_result": compliance_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Compliance check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/threat/model")
async def create_threat_model(request: ThreatModelRequest):
    """Create threat model for specified scope"""
    try:
        # Generate threat model
        threat_model = await security_scanner.generate_threat_model(
            scope=request.scope,
            assets=request.assets,
            attack_vectors=request.attack_vectors
        )
        
        return {
            "scope": request.scope,
            "threat_model": threat_model,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Threat modeling error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/scan/{scan_id}/status")
async def get_scan_status(scan_id: str):
    """Get status of a running scan"""
    if scan_id not in active_scans and scan_id not in scan_results_cache:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if scan_id in active_scans:
        return active_scans[scan_id]
    else:
        return scan_results_cache[scan_id]

@app.get("/api/v1/scan/{scan_id}/results")
async def get_scan_results(scan_id: str):
    """Get results of a completed scan"""
    if scan_id not in scan_results_cache:
        if scan_id in active_scans:
            return {"status": "running", "message": "Scan still in progress"}
        else:
            raise HTTPException(status_code=404, detail="Scan results not found")
    
    return scan_results_cache[scan_id]

@app.get("/api/v1/scans/list")
async def list_scans():
    """List all scans (active and completed)"""
    return {
        "active_scans": active_scans,
        "completed_scans": list(scan_results_cache.keys()),
        "total_active": len(active_scans),
        "total_completed": len(scan_results_cache)
    }

# Background task functions
async def run_snippet_scan(scan_id: str, code_content: str, options: Dict):
    """Run security scan on code snippet"""
    try:
        logger.info(f"Starting snippet scan {scan_id}")
        
        # Analyze code snippet
        results = await security_scanner.analyze_code_snippet(
            content=code_content,
            options=options
        )
        
        # Store results
        scan_results_cache[scan_id] = {
            "scan_id": scan_id,
            "type": "snippet",
            "status": "completed",
            "results": results,
            "completed_at": datetime.now().isoformat()
        }
        
        # Remove from active scans
        if scan_id in active_scans:
            del active_scans[scan_id]
        
        logger.info(f"Snippet scan {scan_id} completed")
        
    except Exception as e:
        logger.error(f"Snippet scan {scan_id} failed: {e}")
        scan_results_cache[scan_id] = {
            "scan_id": scan_id,
            "type": "snippet",
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        }
        if scan_id in active_scans:
            del active_scans[scan_id]

async def run_codebase_scan(scan_id: str, target_path: str, options: Dict):
    """Run security scan on entire codebase"""
    try:
        logger.info(f"Starting codebase scan {scan_id} on {target_path}")
        
        # Analyze entire codebase
        results = await security_scanner.analyze_codebase(
            path=target_path,
            options=options
        )
        
        # Store results
        scan_results_cache[scan_id] = {
            "scan_id": scan_id,
            "type": "codebase",
            "status": "completed", 
            "target": target_path,
            "results": results,
            "completed_at": datetime.now().isoformat()
        }
        
        # Remove from active scans
        if scan_id in active_scans:
            del active_scans[scan_id]
        
        logger.info(f"Codebase scan {scan_id} completed")
        
    except Exception as e:
        logger.error(f"Codebase scan {scan_id} failed: {e}")
        scan_results_cache[scan_id] = {
            "scan_id": scan_id,
            "type": "codebase",
            "status": "failed",
            "target": target_path,
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        }
        if scan_id in active_scans:
            del active_scans[scan_id]

if __name__ == "__main__":
    port = int(os.getenv("ASTERISK_SERVICE_PORT", 8002))
    
    logger.info(f"🛡️ Starting Asterisk MCP Security Service on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )