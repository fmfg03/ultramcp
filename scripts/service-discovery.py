#!/usr/bin/env python3
"""
UltraMCP Service Discovery with Manual Registration Fallback
Handles service discovery failures with multiple fallback mechanisms
"""

import json
import time
import threading
import requests
import socket
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import subprocess
import os

@dataclass
class ServiceConfig:
    """Service configuration structure"""
    name: str
    endpoint: str
    health_check: str
    port: int
    protocol: str = "http"
    timeout: int = 5
    retry_count: int = 3
    tags: List[str] = None
    metadata: Dict[str, Any] = None

@dataclass 
class ServiceStatus:
    """Service health status"""
    name: str
    endpoint: str
    status: str  # 'healthy', 'unhealthy', 'unknown'
    last_check: datetime
    response_time: float
    error_message: Optional[str] = None

class ManualServiceRegistry:
    """Manual service registry as fallback for service discovery"""
    
    def __init__(self, registry_file: str = "data/fallback/service_registry.json"):
        self.registry_file = Path(registry_file)
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        self.services: Dict[str, ServiceConfig] = {}
        self.service_status: Dict[str, ServiceStatus] = {}
        self.lock = threading.RLock()
        self.load_registry()
        
        # Start health check thread
        self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self.health_check_thread.start()
    
    def load_registry(self):
        """Load service registry from file"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                    
                for service_data in data.get('services', []):
                    service = ServiceConfig(**service_data)
                    self.services[service.name] = service
                    
                logging.info(f"Loaded {len(self.services)} services from registry")
            except Exception as e:
                logging.error(f"Failed to load service registry: {e}")
    
    def save_registry(self):
        """Save service registry to file"""
        with self.lock:
            try:
                data = {
                    "version": "1.0",
                    "updated_at": datetime.now().isoformat(),
                    "services": [asdict(service) for service in self.services.values()]
                }
                
                with open(self.registry_file, 'w') as f:
                    json.dump(data, f, indent=2)
                    
            except Exception as e:
                logging.error(f"Failed to save service registry: {e}")
    
    def register_service(self, service: ServiceConfig) -> bool:
        """Register a service manually"""
        with self.lock:
            try:
                self.services[service.name] = service
                self.save_registry()
                
                # Initialize health status
                self.service_status[service.name] = ServiceStatus(
                    name=service.name,
                    endpoint=service.endpoint,
                    status="unknown",
                    last_check=datetime.now(),
                    response_time=0.0
                )
                
                logging.info(f"Registered service: {service.name} at {service.endpoint}")
                return True
                
            except Exception as e:
                logging.error(f"Failed to register service {service.name}: {e}")
                return False
    
    def unregister_service(self, service_name: str) -> bool:
        """Unregister a service"""
        with self.lock:
            try:
                if service_name in self.services:
                    del self.services[service_name]
                    if service_name in self.service_status:
                        del self.service_status[service_name]
                    self.save_registry()
                    logging.info(f"Unregistered service: {service_name}")
                    return True
                return False
            except Exception as e:
                logging.error(f"Failed to unregister service {service_name}: {e}")
                return False
    
    def discover_service(self, service_name: str) -> Optional[ServiceConfig]:
        """Discover a service by name"""
        with self.lock:
            return self.services.get(service_name)
    
    def discover_services_by_tag(self, tag: str) -> List[ServiceConfig]:
        """Discover services by tag"""
        with self.lock:
            services = []
            for service in self.services.values():
                if service.tags and tag in service.tags:
                    services.append(service)
            return services
    
    def get_healthy_services(self) -> List[ServiceConfig]:
        """Get all healthy services"""
        with self.lock:
            healthy_services = []
            for service_name, service in self.services.items():
                status = self.service_status.get(service_name)
                if status and status.status == "healthy":
                    healthy_services.append(service)
            return healthy_services
    
    def check_service_health(self, service: ServiceConfig) -> ServiceStatus:
        """Check health of a single service"""
        start_time = time.time()
        
        try:
            # Try health check endpoint
            response = requests.get(
                service.health_check,
                timeout=service.timeout,
                headers={"User-Agent": "UltraMCP-HealthCheck/1.0"}
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                status = ServiceStatus(
                    name=service.name,
                    endpoint=service.endpoint,
                    status="healthy",
                    last_check=datetime.now(),
                    response_time=response_time
                )
            else:
                status = ServiceStatus(
                    name=service.name,
                    endpoint=service.endpoint,
                    status="unhealthy",
                    last_check=datetime.now(),
                    response_time=response_time,
                    error_message=f"HTTP {response.status_code}"
                )
                
        except requests.exceptions.Timeout:
            status = ServiceStatus(
                name=service.name,
                endpoint=service.endpoint,
                status="unhealthy",
                last_check=datetime.now(),
                response_time=service.timeout,
                error_message="Timeout"
            )
            
        except requests.exceptions.ConnectionError:
            status = ServiceStatus(
                name=service.name,
                endpoint=service.endpoint,
                status="unhealthy",
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                error_message="Connection failed"
            )
            
        except Exception as e:
            status = ServiceStatus(
                name=service.name,
                endpoint=service.endpoint,
                status="unhealthy",
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                error_message=str(e)
            )
        
        return status
    
    def _health_check_loop(self):
        """Background health check loop"""
        while True:
            try:
                with self.lock:
                    services_to_check = list(self.services.values())
                
                for service in services_to_check:
                    try:
                        status = self.check_service_health(service)
                        with self.lock:
                            self.service_status[service.name] = status
                    except Exception as e:
                        logging.error(f"Health check failed for {service.name}: {e}")
                
                # Sleep for 30 seconds between health checks
                time.sleep(30)
                
            except Exception as e:
                logging.error(f"Health check loop error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def get_service_status(self, service_name: str) -> Optional[ServiceStatus]:
        """Get current status of a service"""
        with self.lock:
            return self.service_status.get(service_name)
    
    def get_all_service_status(self) -> Dict[str, ServiceStatus]:
        """Get status of all services"""
        with self.lock:
            return dict(self.service_status)

class ServiceDiscoveryManager:
    """Main service discovery manager with multiple fallback mechanisms"""
    
    def __init__(self):
        self.manual_registry = ManualServiceRegistry()
        self.discovery_methods = [
            self._discover_via_manual_registry,
            self._discover_via_docker_compose,
            self._discover_via_environment_variables,
            self._discover_via_network_scan
        ]
    
    def register_core_services(self):
        """Register core UltraMCP services"""
        core_services = [
            ServiceConfig(
                name="cod-protocol",
                endpoint="http://localhost:8001",
                health_check="http://localhost:8001/health",
                port=8001,
                tags=["core", "orchestration"],
                metadata={"description": "Chain-of-Debate Protocol Service"}
            ),
            ServiceConfig(
                name="postgres",
                endpoint="postgresql://localhost:5432/ultramcp",
                health_check="http://localhost:5432",  # This will fail, but we handle it
                port=5432,
                protocol="postgresql",
                tags=["database", "core"],
                metadata={"description": "PostgreSQL Database"}
            ),
            ServiceConfig(
                name="redis",
                endpoint="redis://localhost:6379",
                health_check="http://localhost:6379",  # This will fail, but we handle it
                port=6379,
                protocol="redis",
                tags=["cache", "core"],
                metadata={"description": "Redis Cache"}
            ),
            ServiceConfig(
                name="web-dashboard",
                endpoint="http://localhost:3000",
                health_check="http://localhost:3000/health",
                port=3000,
                tags=["web", "optional"],
                metadata={"description": "Web Dashboard"}
            )
        ]
        
        for service in core_services:
            self.manual_registry.register_service(service)
    
    def _discover_via_manual_registry(self, service_name: str) -> Optional[ServiceConfig]:
        """Discover service via manual registry"""
        return self.manual_registry.discover_service(service_name)
    
    def _discover_via_docker_compose(self, service_name: str) -> Optional[ServiceConfig]:
        """Discover service via Docker Compose"""
        try:
            # Try to get service info from docker-compose
            result = subprocess.run(
                ["docker-compose", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                services_data = json.loads(result.stdout)
                for service_data in services_data:
                    if service_name in service_data.get("Service", ""):
                        # Extract port information
                        ports = service_data.get("Ports", "")
                        if ports:
                            # Parse port mapping (e.g., "0.0.0.0:8001->8001/tcp")
                            port_parts = ports.split("->")
                            if len(port_parts) == 2:
                                external_port = port_parts[0].split(":")[-1]
                                return ServiceConfig(
                                    name=service_name,
                                    endpoint=f"http://localhost:{external_port}",
                                    health_check=f"http://localhost:{external_port}/health",
                                    port=int(external_port),
                                    tags=["docker-compose"],
                                    metadata={"source": "docker-compose"}
                                )
        except Exception as e:
            logging.debug(f"Docker Compose discovery failed: {e}")
        
        return None
    
    def _discover_via_environment_variables(self, service_name: str) -> Optional[ServiceConfig]:
        """Discover service via environment variables"""
        # Check for environment variables like SERVICE_NAME_URL
        env_var_patterns = [
            f"{service_name.upper()}_URL",
            f"{service_name.upper()}_ENDPOINT",
            f"{service_name.replace('-', '_').upper()}_URL"
        ]
        
        for env_var in env_var_patterns:
            endpoint = os.getenv(env_var)
            if endpoint:
                # Extract port from URL
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(endpoint)
                    port = parsed.port or (80 if parsed.scheme == "http" else 443)
                    
                    return ServiceConfig(
                        name=service_name,
                        endpoint=endpoint,
                        health_check=f"{endpoint}/health",
                        port=port,
                        tags=["environment"],
                        metadata={"source": "environment", "env_var": env_var}
                    )
                except Exception:
                    pass
        
        return None
    
    def _discover_via_network_scan(self, service_name: str) -> Optional[ServiceConfig]:
        """Discover service via network scanning (last resort)"""
        # Define common ports for different services
        service_ports = {
            "cod-protocol": [8001],
            "postgres": [5432],
            "redis": [6379],
            "web-dashboard": [3000, 8080],
            "api": [8000, 8080, 3000],
        }
        
        ports_to_scan = service_ports.get(service_name, [])
        
        for port in ports_to_scan:
            if self._is_port_open("localhost", port):
                endpoint = f"http://localhost:{port}"
                return ServiceConfig(
                    name=service_name,
                    endpoint=endpoint,
                    health_check=f"{endpoint}/health",
                    port=port,
                    tags=["network-scan"],
                    metadata={"source": "network-scan", "detected": True}
                )
        
        return None
    
    def _is_port_open(self, host: str, port: int, timeout: int = 2) -> bool:
        """Check if a port is open"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                result = sock.connect_ex((host, port))
                return result == 0
        except Exception:
            return False
    
    def discover_service(self, service_name: str) -> Optional[ServiceConfig]:
        """Discover service using all available methods"""
        for method in self.discovery_methods:
            try:
                service = method(service_name)
                if service:
                    logging.info(f"Discovered service {service_name} via {method.__name__}")
                    # Register discovered service in manual registry
                    self.manual_registry.register_service(service)
                    return service
            except Exception as e:
                logging.debug(f"Discovery method {method.__name__} failed for {service_name}: {e}")
        
        logging.warning(f"Could not discover service: {service_name}")
        return None
    
    def get_service_status_report(self) -> Dict[str, Any]:
        """Get comprehensive service status report"""
        all_status = self.manual_registry.get_all_service_status()
        
        healthy_count = sum(1 for status in all_status.values() if status.status == "healthy")
        unhealthy_count = sum(1 for status in all_status.values() if status.status == "unhealthy")
        unknown_count = sum(1 for status in all_status.values() if status.status == "unknown")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "services": {
                "total": len(all_status),
                "healthy": healthy_count,
                "unhealthy": unhealthy_count,
                "unknown": unknown_count
            },
            "service_details": {
                name: {
                    "status": status.status,
                    "endpoint": status.endpoint,
                    "last_check": status.last_check.isoformat(),
                    "response_time": status.response_time,
                    "error": status.error_message
                }
                for name, status in all_status.items()
            },
            "discovery_methods": [
                "manual_registry",
                "docker_compose",
                "environment_variables", 
                "network_scan"
            ]
        }

# Global service discovery manager
service_discovery = ServiceDiscoveryManager()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="UltraMCP Service Discovery")
    parser.add_argument("--register-core", action="store_true", help="Register core services")
    parser.add_argument("--discover", type=str, help="Discover specific service")
    parser.add_argument("--status", action="store_true", help="Show service status report")
    parser.add_argument("--list", action="store_true", help="List all registered services")
    
    args = parser.parse_args()
    
    if args.register_core:
        service_discovery.register_core_services()
        print("Core services registered")
    
    if args.discover:
        service = service_discovery.discover_service(args.discover)
        if service:
            print(f"Found service: {json.dumps(asdict(service), indent=2)}")
        else:
            print(f"Service not found: {args.discover}")
    
    if args.status:
        report = service_discovery.get_service_status_report()
        print(json.dumps(report, indent=2))
    
    if args.list:
        services = service_discovery.manual_registry.services
        print("Registered services:")
        for name, service in services.items():
            print(f"  {name}: {service.endpoint}")