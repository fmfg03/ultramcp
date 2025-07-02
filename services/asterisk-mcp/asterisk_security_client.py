#!/usr/bin/env python3
"""
Asterisk MCP Security Client
Enterprise-grade security scanning integration for UltraMCP
"""

import asyncio
import httpx
import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional, Any, Union
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecuritySeverity(Enum):
    """Security vulnerability severity levels"""
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ComplianceStandard(Enum):
    """Supported compliance standards"""
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    NIST = "nist"

@dataclass
class SecurityVulnerability:
    """Individual security vulnerability"""
    id: str
    severity: SecuritySeverity
    title: str
    description: str
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    remediation: Optional[str] = None
    confidence: float = 0.0

@dataclass
class SecurityScanResult:
    """Security scan result with vulnerabilities and metadata"""
    scan_id: str
    timestamp: str
    scan_type: str
    risk_score: float
    vulnerabilities: List[SecurityVulnerability]
    compliance_status: Dict[str, bool]
    scan_duration: float
    lines_scanned: int
    files_scanned: int
    
    def has_vulnerabilities(self) -> bool:
        """Check if scan found any vulnerabilities"""
        return len(self.vulnerabilities) > 0
    
    def get_critical_vulnerabilities(self) -> List[SecurityVulnerability]:
        """Get only critical severity vulnerabilities"""
        return [v for v in self.vulnerabilities if v.severity == SecuritySeverity.CRITICAL]
    
    def get_high_vulnerabilities(self) -> List[SecurityVulnerability]:
        """Get high severity vulnerabilities"""
        return [v for v in self.vulnerabilities if v.severity == SecuritySeverity.HIGH]
    
    def format_findings(self) -> str:
        """Format findings for display"""
        if not self.has_vulnerabilities():
            return "✅ No vulnerabilities found"
        
        findings = []
        findings.append(f"🔍 Security Scan Results (Risk Score: {self.risk_score}/10)")
        findings.append(f"📊 Found {len(self.vulnerabilities)} vulnerabilities")
        
        # Group by severity
        severity_counts = {}
        for vuln in self.vulnerabilities:
            severity_counts[vuln.severity] = severity_counts.get(vuln.severity, 0) + 1
        
        for severity, count in severity_counts.items():
            emoji = {"critical": "🚨", "high": "⚠️", "medium": "⚡", "low": "ℹ️"}.get(severity.value, "❓")
            findings.append(f"{emoji} {severity.value.upper()}: {count}")
        
        # Top 3 vulnerabilities
        findings.append("\n🔥 Top Vulnerabilities:")
        for i, vuln in enumerate(self.vulnerabilities[:3]):
            findings.append(f"{i+1}. {vuln.title} ({vuln.severity.value})")
            if vuln.line_number:
                findings.append(f"   Line {vuln.line_number}: {vuln.description}")
        
        return "\n".join(findings)

class AsteriskSecurityClient:
    """Asterisk MCP Security Client for UltraMCP integration"""
    
    def __init__(self, api_url: str, api_key: str, timeout: int = 30):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session = httpx.AsyncClient(timeout=timeout)
        
        # Headers for authentication
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "UltraMCP-Security-Client/1.0"
        }
    
    async def scan_code_snippet(self, 
                               code: str, 
                               language: str = "python",
                               context: Optional[Dict] = None) -> SecurityScanResult:
        """Scan individual code snippet for vulnerabilities"""
        
        payload = {
            "code": code,
            "language": language,
            "scan_type": "snippet",
            "context": context or {},
            "include_remediation": True,
            "compliance_standards": ["soc2", "owasp"]
        }
        
        try:
            logger.info(f"🔍 Scanning code snippet ({len(code)} chars, {language})")
            start_time = time.time()
            
            response = await self.session.post(
                f"{self.api_url}/api/v1/scan/snippet",
                json=payload,
                headers=self.headers
            )
            
            scan_duration = time.time() - start_time
            
            if response.status_code == 200:
                result_data = response.json()
                logger.info(f"✅ Scan completed in {scan_duration:.2f}s")
                return self._parse_scan_result(result_data, scan_duration)
            else:
                logger.error(f"❌ Scan failed: {response.status_code} - {response.text}")
                raise Exception(f"Security scan failed: {response.status_code}")
                
        except httpx.TimeoutException:
            logger.error("⏱️ Security scan timed out")
            raise Exception("Security scan timed out")
        except Exception as e:
            logger.error(f"💥 Security scan error: {str(e)}")
            raise
    
    async def scan_codebase(self, 
                           file_paths: List[str],
                           scan_config: Optional[Dict] = None) -> SecurityScanResult:
        """Scan multiple files with contextual analysis"""
        
        # Read file contents
        file_contents = {}
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_contents[file_path] = f.read()
            except Exception as e:
                logger.warning(f"⚠️ Could not read {file_path}: {e}")
                continue
        
        payload = {
            "files": file_contents,
            "scan_type": "codebase",
            "include_context": True,
            "scan_config": scan_config or {
                "include_dependencies": True,
                "deep_analysis": True,
                "compliance_standards": ["soc2", "owasp", "gdpr"]
            }
        }
        
        try:
            logger.info(f"🔍 Scanning codebase ({len(file_contents)} files)")
            start_time = time.time()
            
            response = await self.session.post(
                f"{self.api_url}/api/v1/scan/codebase",
                json=payload,
                headers=self.headers
            )
            
            scan_duration = time.time() - start_time
            
            if response.status_code == 200:
                result_data = response.json()
                logger.info(f"✅ Codebase scan completed in {scan_duration:.2f}s")
                return self._parse_scan_result(result_data, scan_duration)
            else:
                logger.error(f"❌ Codebase scan failed: {response.status_code}")
                raise Exception(f"Codebase scan failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"💥 Codebase scan error: {str(e)}")
            raise
    
    async def verify_code_changes(self, 
                                 diff_content: str,
                                 base_branch: str = "main") -> SecurityScanResult:
        """Verify code changes for new vulnerabilities"""
        
        payload = {
            "diff": diff_content,
            "base_branch": base_branch,
            "scan_type": "change_verification",
            "focus_on_new_vulnerabilities": True,
            "include_security_regression_analysis": True
        }
        
        try:
            logger.info("🔍 Verifying code changes for security regressions")
            start_time = time.time()
            
            response = await self.session.post(
                f"{self.api_url}/api/v1/scan/changes",
                json=payload,
                headers=self.headers
            )
            
            scan_duration = time.time() - start_time
            
            if response.status_code == 200:
                result_data = response.json()
                logger.info(f"✅ Change verification completed in {scan_duration:.2f}s")
                return self._parse_scan_result(result_data, scan_duration)
            else:
                logger.error(f"❌ Change verification failed: {response.status_code}")
                raise Exception(f"Change verification failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"💥 Change verification error: {str(e)}")
            raise
    
    async def compliance_audit(self, 
                              code_or_process: str,
                              standard: ComplianceStandard,
                              business_context: Optional[str] = None) -> Dict[str, Any]:
        """Perform compliance audit against specific standard"""
        
        payload = {
            "content": code_or_process,
            "compliance_standard": standard.value,
            "business_context": business_context or "",
            "audit_type": "comprehensive",
            "include_remediation_roadmap": True,
            "generate_audit_report": True
        }
        
        try:
            logger.info(f"🔍 Performing {standard.value.upper()} compliance audit")
            start_time = time.time()
            
            response = await self.session.post(
                f"{self.api_url}/api/v1/compliance/audit",
                json=payload,
                headers=self.headers
            )
            
            audit_duration = time.time() - start_time
            
            if response.status_code == 200:
                result_data = response.json()
                logger.info(f"✅ Compliance audit completed in {audit_duration:.2f}s")
                return result_data
            else:
                logger.error(f"❌ Compliance audit failed: {response.status_code}")
                raise Exception(f"Compliance audit failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"💥 Compliance audit error: {str(e)}")
            raise
    
    def _parse_scan_result(self, result_data: Dict, scan_duration: float) -> SecurityScanResult:
        """Parse API response into SecurityScanResult"""
        
        vulnerabilities = []
        for vuln_data in result_data.get('vulnerabilities', []):
            vulnerability = SecurityVulnerability(
                id=vuln_data.get('id', ''),
                severity=SecuritySeverity(vuln_data.get('severity', 'info')),
                title=vuln_data.get('title', ''),
                description=vuln_data.get('description', ''),
                cwe_id=vuln_data.get('cwe_id'),
                owasp_category=vuln_data.get('owasp_category'),
                line_number=vuln_data.get('line_number'),
                code_snippet=vuln_data.get('code_snippet'),
                remediation=vuln_data.get('remediation'),
                confidence=vuln_data.get('confidence', 0.0)
            )
            vulnerabilities.append(vulnerability)
        
        return SecurityScanResult(
            scan_id=result_data.get('scan_id', ''),
            timestamp=result_data.get('timestamp', ''),
            scan_type=result_data.get('scan_type', ''),
            risk_score=result_data.get('risk_score', 0.0),
            vulnerabilities=vulnerabilities,
            compliance_status=result_data.get('compliance_status', {}),
            scan_duration=scan_duration,
            lines_scanned=result_data.get('lines_scanned', 0),
            files_scanned=result_data.get('files_scanned', 0)
        )
    
    async def get_security_health_score(self, project_path: str) -> Dict[str, Any]:
        """Get overall security health score for project"""
        
        # Scan all Python files in project
        python_files = list(Path(project_path).rglob("*.py"))
        
        if not python_files:
            return {
                "health_score": 10.0,
                "status": "healthy",
                "message": "No Python files found"
            }
        
        # Scan codebase
        scan_result = await self.scan_codebase([str(f) for f in python_files[:10]])  # Limit for demo
        
        # Calculate health score
        health_score = max(0, 10.0 - scan_result.risk_score)
        
        if health_score >= 8.0:
            status = "healthy"
        elif health_score >= 6.0:
            status = "warning"
        else:
            status = "critical"
        
        return {
            "health_score": health_score,
            "status": status,
            "risk_score": scan_result.risk_score,
            "vulnerabilities_count": len(scan_result.vulnerabilities),
            "critical_vulnerabilities": len(scan_result.get_critical_vulnerabilities()),
            "high_vulnerabilities": len(scan_result.get_high_vulnerabilities()),
            "scan_summary": scan_result.format_findings()
        }
    
    async def close(self):
        """Close HTTP session"""
        await self.session.aclose()

# Example usage and testing
async def main():
    """Example usage of Asterisk Security Client"""
    
    # Initialize client (you'll need real API credentials)
    client = AsteriskSecurityClient(
        api_url="https://api.asterisk-security.com",
        api_key="your-api-key-here"
    )
    
    try:
        # Example 1: Scan code snippet
        test_code = '''
import sqlite3

def get_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL injection vulnerability
    cursor.execute(query)
    return cursor.fetchone()
'''
        
        print("🔍 Scanning code snippet...")
        scan_result = await client.scan_code_snippet(test_code, "python")
        print(scan_result.format_findings())
        
        # Example 2: Get security health score
        print("\n🏥 Getting security health score...")
        health_score = await client.get_security_health_score(".")
        print(f"Health Score: {health_score['health_score']}/10 ({health_score['status']})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())