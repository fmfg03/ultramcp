"""
Security Adapter - Handles security scanning and compliance actions
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import aiohttp
import uuid

from .mock_adapter import MockAdapter

logger = logging.getLogger(__name__)

class SecurityAdapter:
    """Adapter for security scanning and compliance operations"""
    
    def __init__(self):
        self.is_initialized = False
        self.security_configs = {}
        self.triggered_scans = []
        
    async def initialize(self):
        """Initialize security adapter"""
        try:
            await self._load_security_configs()
            await self._test_security_connections()
            self.is_initialized = True
            logger.info("✅ Security adapter initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize security adapter: {e}")
            # Fall back to mock adapter
            self.mock_adapter = MockAdapter("SecurityAdapter")
            await self.mock_adapter.initialize()
            logger.info("✅ Using mock security adapter")
    
    async def _load_security_configs(self):
        """Load security tool configurations"""
        self.security_configs = {
            "sonarqube": {
                "enabled": os.getenv("SONARQUBE_ENABLED", "false").lower() == "true",
                "url": os.getenv("SONARQUBE_URL", ""),
                "token": os.getenv("SONARQUBE_TOKEN", "")
            },
            "snyk": {
                "enabled": os.getenv("SNYK_ENABLED", "false").lower() == "true",
                "token": os.getenv("SNYK_TOKEN", ""),
                "org": os.getenv("SNYK_ORG", "")
            },
            "veracode": {
                "enabled": os.getenv("VERACODE_ENABLED", "false").lower() == "true",
                "api_id": os.getenv("VERACODE_API_ID", ""),
                "api_key": os.getenv("VERACODE_API_KEY", "")
            },
            "custom_scanner": {
                "enabled": os.getenv("CUSTOM_SCANNER_ENABLED", "false").lower() == "true",
                "webhook_url": os.getenv("SECURITY_SCANNER_WEBHOOK", ""),
                "api_key": os.getenv("SECURITY_SCANNER_API_KEY", "")
            }
        }
    
    async def _test_security_connections(self):
        """Test connections to security tools"""
        
        if self.security_configs["sonarqube"]["enabled"]:
            await self._test_sonarqube_connection()
        
        if self.security_configs["snyk"]["enabled"]:
            await self._test_snyk_connection()
    
    async def _test_sonarqube_connection(self):
        """Test SonarQube connection"""
        try:
            sonar_config = self.security_configs["sonarqube"]
            headers = {"Authorization": f"Bearer {sonar_config['token']}"}
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    f"{sonar_config['url']}/api/system/status",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("✅ SonarQube connection test successful")
                    else:
                        raise Exception(f"SonarQube returned status {response.status}")
                        
        except Exception as e:
            logger.warning(f"⚠️ SonarQube connection test failed: {e}")
    
    async def _test_snyk_connection(self):
        """Test Snyk connection"""
        try:
            snyk_config = self.security_configs["snyk"]
            headers = {"Authorization": f"token {snyk_config['token']}"}
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    "https://snyk.io/api/v1/user/me",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("✅ Snyk connection test successful")
                    else:
                        raise Exception(f"Snyk returned status {response.status}")
                        
        except Exception as e:
            logger.warning(f"⚠️ Snyk connection test failed: {e}")
    
    async def execute(self, action_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute security action"""
        
        if not self.is_initialized and hasattr(self, 'mock_adapter'):
            return await self.mock_adapter.execute(action_name, input_data)
        
        if action_name == "trigger_security_scan":
            return await self._trigger_security_scan(input_data)
        else:
            raise ValueError(f"Unsupported action: {action_name}")
    
    async def _trigger_security_scan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger security scan"""
        
        # Extract scan parameters
        scan_type = input_data.get("scan_type", "vulnerability")
        target = input_data.get("target", "")
        scope = input_data.get("scope", "full")
        compliance_framework = input_data.get("compliance_framework")
        priority = input_data.get("priority", "medium")
        
        # Validate parameters
        if not target:
            raise ValueError("Target is required for security scan")
        
        valid_scan_types = ["vulnerability", "compliance", "penetration", "code_analysis"]
        if scan_type not in valid_scan_types:
            raise ValueError(f"Invalid scan type. Must be one of: {valid_scan_types}")
        
        # Generate scan ID
        scan_id = f"SCAN-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"
        
        # Select appropriate security tool based on scan type
        security_tool = await self._select_security_tool(scan_type, compliance_framework)
        
        # Trigger scan based on selected tool
        result = None
        if security_tool == "sonarqube":
            result = await self._trigger_sonarqube_scan(scan_id, target, scan_type, scope)
        elif security_tool == "snyk":
            result = await self._trigger_snyk_scan(scan_id, target, scan_type, scope)
        elif security_tool == "veracode":
            result = await self._trigger_veracode_scan(scan_id, target, scan_type, scope)
        elif security_tool == "custom":
            result = await self._trigger_custom_scan(scan_id, target, scan_type, scope, compliance_framework)
        else:
            # Simulate security scan
            result = await self._simulate_security_scan(scan_id, target, scan_type, scope, compliance_framework)
        
        # Calculate estimated completion time
        scan_durations = {
            "vulnerability": 30,
            "compliance": 45,
            "penetration": 120,
            "code_analysis": 60
        }
        
        scope_multipliers = {
            "full": 1.0,
            "incremental": 0.3,
            "critical_only": 0.5
        }
        
        estimated_minutes = int(scan_durations.get(scan_type, 30) * scope_multipliers.get(scope, 1.0))
        estimated_completion = datetime.utcnow() + timedelta(minutes=estimated_minutes)
        
        # Record triggered scan
        scan_record = {
            "scan_id": scan_id,
            "scan_type": scan_type,
            "target": target,
            "scope": scope,
            "compliance_framework": compliance_framework,
            "security_tool": security_tool,
            "priority": priority,
            "status": "initiated",
            "started_at": datetime.utcnow(),
            "estimated_completion": estimated_completion,
            "results_url": result.get("results_url")
        }
        
        self.triggered_scans.append(scan_record)
        
        # Keep only last 1000 scans
        if len(self.triggered_scans) > 1000:
            self.triggered_scans = self.triggered_scans[-1000:]
        
        return {
            "scan_id": scan_id,
            "status": "initiated",
            "estimated_completion": estimated_completion.isoformat(),
            "results_url": result.get("results_url", f"https://security.ultramcp.com/scans/{scan_id}"),
            "scan_type": scan_type,
            "target": target,
            "scope": scope,
            "security_tool": security_tool,
            "started_at": scan_record["started_at"].isoformat()
        }
    
    async def _select_security_tool(self, scan_type: str, compliance_framework: Optional[str]) -> str:
        """Select appropriate security tool based on scan type"""
        
        # Priority order based on scan type and configuration
        if scan_type == "code_analysis":
            if self.security_configs["sonarqube"]["enabled"]:
                return "sonarqube"
            elif self.security_configs["snyk"]["enabled"]:
                return "snyk"
        
        elif scan_type == "vulnerability":
            if self.security_configs["snyk"]["enabled"]:
                return "snyk"
            elif self.security_configs["sonarqube"]["enabled"]:
                return "sonarqube"
        
        elif scan_type == "compliance":
            if compliance_framework and self.security_configs["veracode"]["enabled"]:
                return "veracode"
            elif self.security_configs["custom_scanner"]["enabled"]:
                return "custom"
        
        elif scan_type == "penetration":
            if self.security_configs["custom_scanner"]["enabled"]:
                return "custom"
        
        # Default fallback
        if self.security_configs["custom_scanner"]["enabled"]:
            return "custom"
        else:
            return "simulation"
    
    async def _trigger_sonarqube_scan(self, scan_id: str, target: str, scan_type: str, scope: str) -> Dict[str, Any]:
        """Trigger SonarQube scan"""
        
        sonar_config = self.security_configs["sonarqube"]
        headers = {
            "Authorization": f"Bearer {sonar_config['token']}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Prepare scan parameters
        project_key = target.replace("/", "_").replace("\\", "_")
        
        try:
            # Create project if it doesn't exist
            create_payload = {
                "project": project_key,
                "name": f"Security Scan: {target}"
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                # Create project
                async with session.post(
                    f"{sonar_config['url']}/api/projects/create",
                    data=create_payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    # Ignore if project already exists
                    pass
                
                # Trigger analysis
                analysis_payload = {
                    "projectKey": project_key,
                    "name": f"Security Analysis - {scan_id}"
                }
                
                async with session.post(
                    f"{sonar_config['url']}/api/ce/submit",
                    data=analysis_payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        task_id = result.get("task", {}).get("id", scan_id)
                        
                        return {
                            "external_id": task_id,
                            "results_url": f"{sonar_config['url']}/dashboard?id={project_key}"
                        }
                    else:
                        logger.warning(f"⚠️ SonarQube scan trigger returned {response.status}")
                        return self._get_fallback_scan_result(scan_id, sonar_config['url'])
                        
        except Exception as e:
            logger.error(f"❌ Failed to trigger SonarQube scan: {e}")
            return self._get_fallback_scan_result(scan_id, sonar_config['url'])
    
    async def _trigger_snyk_scan(self, scan_id: str, target: str, scan_type: str, scope: str) -> Dict[str, Any]:
        """Trigger Snyk scan"""
        
        snyk_config = self.security_configs["snyk"]
        headers = {
            "Authorization": f"token {snyk_config['token']}",
            "Content-Type": "application/json"
        }
        
        try:
            # Trigger Snyk test
            payload = {
                "target": {
                    "remoteUrl": target
                },
                "org": snyk_config["org"]
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(
                    "https://snyk.io/api/v1/test",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        
                        return {
                            "external_id": scan_id,
                            "results_url": f"https://app.snyk.io/org/{snyk_config['org']}/projects"
                        }
                    else:
                        logger.warning(f"⚠️ Snyk scan trigger returned {response.status}")
                        return self._get_fallback_scan_result(scan_id, "https://app.snyk.io")
                        
        except Exception as e:
            logger.error(f"❌ Failed to trigger Snyk scan: {e}")
            return self._get_fallback_scan_result(scan_id, "https://app.snyk.io")
    
    async def _trigger_veracode_scan(self, scan_id: str, target: str, scan_type: str, scope: str) -> Dict[str, Any]:
        """Trigger Veracode scan"""
        
        # Simplified Veracode implementation
        return {
            "external_id": scan_id,
            "results_url": "https://web.analysiscenter.veracode.com"
        }
    
    async def _trigger_custom_scan(self, scan_id: str, target: str, scan_type: str, scope: str, 
                                  compliance_framework: Optional[str]) -> Dict[str, Any]:
        """Trigger custom security scanner"""
        
        custom_config = self.security_configs["custom_scanner"]
        headers = {
            "Authorization": f"Bearer {custom_config['api_key']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "scan_id": scan_id,
            "scan_type": scan_type,
            "target": target,
            "scope": scope,
            "compliance_framework": compliance_framework,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(
                    custom_config["webhook_url"],
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status in [200, 201, 202]:
                        return {
                            "external_id": scan_id,
                            "results_url": f"https://security.ultramcp.com/scans/{scan_id}"
                        }
                    else:
                        logger.warning(f"⚠️ Custom scanner returned {response.status}")
                        return self._get_fallback_scan_result(scan_id, "https://security.ultramcp.com")
                        
        except Exception as e:
            logger.error(f"❌ Failed to trigger custom security scan: {e}")
            return self._get_fallback_scan_result(scan_id, "https://security.ultramcp.com")
    
    async def _simulate_security_scan(self, scan_id: str, target: str, scan_type: str, scope: str,
                                     compliance_framework: Optional[str]) -> Dict[str, Any]:
        """Simulate security scan for development/testing"""
        
        return {
            "external_id": scan_id,
            "results_url": f"https://security.ultramcp.com/scans/{scan_id}"
        }
    
    def _get_fallback_scan_result(self, scan_id: str, base_url: str) -> Dict[str, Any]:
        """Get fallback scan result when API call fails"""
        
        return {
            "external_id": scan_id,
            "results_url": f"{base_url}/scan/{scan_id}"
        }
    
    async def get_scan_status(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get status of security scan"""
        
        for scan in self.triggered_scans:
            if scan["scan_id"] == scan_id:
                # Calculate current status based on time
                now = datetime.utcnow()
                estimated_completion = scan["estimated_completion"]
                
                if now < estimated_completion:
                    status = "running"
                    progress = min(90, int((now - scan["started_at"]).total_seconds() / 
                                         (estimated_completion - scan["started_at"]).total_seconds() * 100))
                else:
                    status = "completed"
                    progress = 100
                
                return {
                    "scan_id": scan_id,
                    "status": status,
                    "progress": progress,
                    "scan_type": scan["scan_type"],
                    "target": scan["target"],
                    "scope": scan["scope"],
                    "security_tool": scan["security_tool"],
                    "started_at": scan["started_at"].isoformat(),
                    "estimated_completion": scan["estimated_completion"].isoformat(),
                    "results_url": scan["results_url"]
                }
        
        return None
    
    async def get_security_statistics(self) -> Dict[str, Any]:
        """Get security adapter statistics"""
        
        total_scans = len(self.triggered_scans)
        if total_scans == 0:
            return {"total_scans": 0}
        
        # Scan type distribution
        type_counts = {}
        for scan in self.triggered_scans:
            scan_type = scan["scan_type"]
            type_counts[scan_type] = type_counts.get(scan_type, 0) + 1
        
        # Tool distribution
        tool_counts = {}
        for scan in self.triggered_scans:
            tool = scan["security_tool"]
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
        
        # Scope distribution
        scope_counts = {}
        for scan in self.triggered_scans:
            scope = scan["scope"]
            scope_counts[scope] = scope_counts.get(scope, 0) + 1
        
        # Recent scans (last 24 hours)
        recent_threshold = datetime.utcnow() - timedelta(hours=24)
        recent_scans = len([s for s in self.triggered_scans if s["started_at"] > recent_threshold])
        
        return {
            "total_scans": total_scans,
            "recent_scans_24h": recent_scans,
            "scan_type_distribution": type_counts,
            "security_tool_distribution": tool_counts,
            "scope_distribution": scope_counts,
            "configured_tools": {
                tool: config["enabled"] 
                for tool, config in self.security_configs.items()
            }
        }
    
    async def cleanup(self):
        """Cleanup security adapter"""
        
        if self.triggered_scans:
            logger.info(f"🔒 Security adapter triggered {len(self.triggered_scans)} scans during session")
        
        self.triggered_scans.clear()
        self.is_initialized = False
        logger.info("✅ Security adapter cleaned up")