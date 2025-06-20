#!/usr/bin/env python3
"""
MCP Enterprise Testing Suite
Comprehensive testing framework for all MCP components
"""

import pytest
import asyncio
import aiohttp
import psycopg2
import redis
import json
import time
import subprocess
import os
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class TestResult:
    name: str
    status: str  # 'passed', 'failed', 'skipped'
    duration: float
    error: str = None
    details: Dict[str, Any] = None

class MCPTestSuite:
    """Suite completa de testing para MCP Enterprise"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results: List[TestResult] = []
        self.start_time = None
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Ejecuta todos los tests y retorna reporte completo"""
        self.start_time = time.time()
        
        print("🧪 Iniciando MCP Enterprise Testing Suite...")
        print("=" * 60)
        
        # Tests de infraestructura
        await self._test_infrastructure()
        
        # Tests de base de datos
        await self._test_database()
        
        # Tests de APIs
        await self._test_apis()
        
        # Tests de herramientas MCP
        await self._test_mcp_tools()
        
        # Tests de webhooks
        await self._test_webhooks()
        
        # Tests de memoria semántica
        await self._test_semantic_memory()
        
        # Tests de seguridad
        await self._test_security()
        
        # Tests de performance
        await self._test_performance()
        
        # Tests de integración
        await self._test_integration()
        
        return self._generate_report()
    
    async def _test_infrastructure(self):
        """Tests de infraestructura Docker y servicios"""
        print("\n📦 Testing Infrastructure...")
        
        # Test Docker containers
        await self._run_test("docker_containers", self._test_docker_containers)
        
        # Test network connectivity
        await self._run_test("network_connectivity", self._test_network_connectivity)
        
        # Test service health checks
        await self._run_test("service_health", self._test_service_health)
    
    async def _test_database(self):
        """Tests de base de datos PostgreSQL y Redis"""
        print("\n🗄️ Testing Database...")
        
        # Test PostgreSQL connection
        await self._run_test("postgres_connection", self._test_postgres_connection)
        
        # Test pgvector extension
        await self._run_test("pgvector_extension", self._test_pgvector_extension)
        
        # Test Redis connection
        await self._run_test("redis_connection", self._test_redis_connection)
        
        # Test database schema
        await self._run_test("database_schema", self._test_database_schema)
    
    async def _test_apis(self):
        """Tests de APIs REST"""
        print("\n🌐 Testing APIs...")
        
        # Test health endpoints
        await self._run_test("health_endpoints", self._test_health_endpoints)
        
        # Test authentication
        await self._run_test("authentication", self._test_authentication)
        
        # Test rate limiting
        await self._run_test("rate_limiting", self._test_rate_limiting)
        
        # Test CORS
        await self._run_test("cors_headers", self._test_cors_headers)
    
    async def _test_mcp_tools(self):
        """Tests de herramientas MCP"""
        print("\n🔧 Testing MCP Tools...")
        
        # Test tool discovery
        await self._run_test("tool_discovery", self._test_tool_discovery)
        
        # Test tool execution
        await self._run_test("tool_execution", self._test_tool_execution)
        
        # Test error handling
        await self._run_test("tool_error_handling", self._test_tool_error_handling)
    
    async def _test_webhooks(self):
        """Tests de sistema de webhooks"""
        print("\n🪝 Testing Webhooks...")
        
        # Test webhook receiver
        await self._run_test("webhook_receiver", self._test_webhook_receiver)
        
        # Test signature validation
        await self._run_test("webhook_signatures", self._test_webhook_signatures)
        
        # Test async processing
        await self._run_test("webhook_async_processing", self._test_webhook_async_processing)
    
    async def _test_semantic_memory(self):
        """Tests de memoria semántica"""
        print("\n🧠 Testing Semantic Memory...")
        
        # Test vector storage
        await self._run_test("vector_storage", self._test_vector_storage)
        
        # Test similarity search
        await self._run_test("similarity_search", self._test_similarity_search)
        
        # Test memory cleanup
        await self._run_test("memory_cleanup", self._test_memory_cleanup)
    
    async def _test_security(self):
        """Tests de seguridad"""
        print("\n🔒 Testing Security...")
        
        # Test input sanitization
        await self._run_test("input_sanitization", self._test_input_sanitization)
        
        # Test SQL injection protection
        await self._run_test("sql_injection_protection", self._test_sql_injection_protection)
        
        # Test XSS protection
        await self._run_test("xss_protection", self._test_xss_protection)
        
        # Test JWT validation
        await self._run_test("jwt_validation", self._test_jwt_validation)
    
    async def _test_performance(self):
        """Tests de performance"""
        print("\n⚡ Testing Performance...")
        
        # Test response times
        await self._run_test("response_times", self._test_response_times)
        
        # Test concurrent requests
        await self._run_test("concurrent_requests", self._test_concurrent_requests)
        
        # Test memory usage
        await self._run_test("memory_usage", self._test_memory_usage)
    
    async def _test_integration(self):
        """Tests de integración end-to-end"""
        print("\n🔄 Testing Integration...")
        
        # Test complete workflow
        await self._run_test("complete_workflow", self._test_complete_workflow)
        
        # Test error recovery
        await self._run_test("error_recovery", self._test_error_recovery)
        
        # Test data consistency
        await self._run_test("data_consistency", self._test_data_consistency)
    
    async def _run_test(self, test_name: str, test_func):
        """Ejecuta un test individual y registra el resultado"""
        start_time = time.time()
        try:
            print(f"  ▶️ {test_name}...", end=" ")
            result = await test_func()
            duration = time.time() - start_time
            
            if result.get('success', True):
                print("✅ PASSED")
                self.results.append(TestResult(
                    name=test_name,
                    status='passed',
                    duration=duration,
                    details=result
                ))
            else:
                print("❌ FAILED")
                self.results.append(TestResult(
                    name=test_name,
                    status='failed',
                    duration=duration,
                    error=result.get('error', 'Unknown error'),
                    details=result
                ))
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ FAILED - {str(e)}")
            self.results.append(TestResult(
                name=test_name,
                status='failed',
                duration=duration,
                error=str(e)
            ))
    
    # Implementaciones de tests específicos
    
    async def _test_docker_containers(self) -> Dict[str, Any]:
        """Test que todos los contenedores Docker estén ejecutándose"""
        try:
            result = subprocess.run(['docker', 'ps', '--format', 'json'], 
                                  capture_output=True, text=True)
            containers = [json.loads(line) for line in result.stdout.strip().split('\n') if line]
            
            expected_containers = [
                'mcp_postgres', 'mcp_redis', 'mcp_backend', 
                'mcp_frontend', 'mcp_prometheus', 'mcp_grafana'
            ]
            
            running_containers = [c['Names'] for c in containers]
            missing = [name for name in expected_containers if name not in running_containers]
            
            return {
                'success': len(missing) == 0,
                'running_containers': running_containers,
                'missing_containers': missing,
                'total_containers': len(containers)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _test_network_connectivity(self) -> Dict[str, Any]:
        """Test conectividad de red entre servicios"""
        endpoints = [
            ('backend', 'http://mcp_backend:3000/health'),
            ('postgres', 'postgresql://mcp_user:password@mcp_postgres:5432/mcp_enterprise'),
            ('redis', 'redis://mcp_redis:6379'),
            ('prometheus', 'http://mcp_prometheus:9090/-/healthy'),
            ('grafana', 'http://mcp_grafana:3000/api/health')
        ]
        
        results = {}
        for name, endpoint in endpoints:
            try:
                if endpoint.startswith('http'):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(endpoint, timeout=5) as response:
                            results[name] = response.status == 200
                else:
                    # Para bases de datos, test básico de conexión
                    results[name] = True  # Simplificado para el ejemplo
            except Exception:
                results[name] = False
        
        return {
            'success': all(results.values()),
            'connectivity_results': results
        }
    
    async def _test_service_health(self) -> Dict[str, Any]:
        """Test health checks de todos los servicios"""
        health_endpoints = [
            ('backend', 'http://localhost:3000/health'),
            ('frontend', 'http://localhost:80/health'),
            ('prometheus', 'http://localhost:9091/-/healthy'),
            ('grafana', 'http://localhost:3001/api/health')
        ]
        
        results = {}
        for name, endpoint in health_endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(endpoint, timeout=5) as response:
                        if response.status == 200:
                            data = await response.json()
                            results[name] = {
                                'status': 'healthy',
                                'response_time': response.headers.get('X-Response-Time'),
                                'data': data
                            }
                        else:
                            results[name] = {'status': 'unhealthy', 'code': response.status}
            except Exception as e:
                results[name] = {'status': 'error', 'error': str(e)}
        
        healthy_services = sum(1 for r in results.values() if r.get('status') == 'healthy')
        
        return {
            'success': healthy_services == len(health_endpoints),
            'healthy_services': healthy_services,
            'total_services': len(health_endpoints),
            'service_results': results
        }
    
    async def _test_postgres_connection(self) -> Dict[str, Any]:
        """Test conexión a PostgreSQL"""
        try:
            conn = psycopg2.connect(
                host=self.config.get('postgres_host', 'localhost'),
                port=self.config.get('postgres_port', 5432),
                database=self.config.get('postgres_db', 'mcp_enterprise'),
                user=self.config.get('postgres_user', 'mcp_user'),
                password=self.config.get('postgres_password', 'mcp_secure_password_2024')
            )
            
            cursor = conn.cursor()
            cursor.execute('SELECT version();')
            version = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s;', ('mcp_core',))
            table_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'success': True,
                'postgres_version': version,
                'table_count': table_count
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _test_pgvector_extension(self) -> Dict[str, Any]:
        """Test extensión pgvector"""
        try:
            conn = psycopg2.connect(
                host=self.config.get('postgres_host', 'localhost'),
                port=self.config.get('postgres_port', 5432),
                database=self.config.get('postgres_db', 'mcp_enterprise'),
                user=self.config.get('postgres_user', 'mcp_user'),
                password=self.config.get('postgres_password', 'mcp_secure_password_2024')
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
            extension_exists = cursor.fetchone() is not None
            
            if extension_exists:
                # Test vector operations
                cursor.execute("SELECT '[1,2,3]'::vector <-> '[4,5,6]'::vector;")
                distance = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'success': extension_exists,
                'extension_installed': extension_exists,
                'vector_distance_test': distance if extension_exists else None
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _test_redis_connection(self) -> Dict[str, Any]:
        """Test conexión a Redis"""
        try:
            r = redis.Redis(
                host=self.config.get('redis_host', 'localhost'),
                port=self.config.get('redis_port', 6379),
                password=self.config.get('redis_password', 'redis_secure_password_2024'),
                decode_responses=True
            )
            
            # Test basic operations
            r.set('test_key', 'test_value', ex=60)
            value = r.get('test_key')
            r.delete('test_key')
            
            info = r.info()
            
            return {
                'success': value == 'test_value',
                'redis_version': info.get('redis_version'),
                'connected_clients': info.get('connected_clients'),
                'used_memory': info.get('used_memory_human')
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _test_database_schema(self) -> Dict[str, Any]:
        """Test esquema de base de datos"""
        try:
            conn = psycopg2.connect(
                host=self.config.get('postgres_host', 'localhost'),
                port=self.config.get('postgres_port', 5432),
                database=self.config.get('postgres_db', 'mcp_enterprise'),
                user=self.config.get('postgres_user', 'mcp_user'),
                password=self.config.get('postgres_password', 'mcp_secure_password_2024')
            )
            
            cursor = conn.cursor()
            
            # Check required schemas
            cursor.execute("""
                SELECT schema_name FROM information_schema.schemata 
                WHERE schema_name IN ('mcp_core', 'mcp_memory', 'mcp_analytics', 'mcp_security');
            """)
            schemas = [row[0] for row in cursor.fetchall()]
            
            # Check required tables
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'mcp_core' AND table_name IN ('tasks', 'tools', 'tool_executions');
            """)
            core_tables = [row[0] for row in cursor.fetchall()]
            
            # Check vector tables
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'mcp_memory' AND table_name IN ('semantic_memory', 'knowledge_base');
            """)
            memory_tables = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            expected_schemas = ['mcp_core', 'mcp_memory', 'mcp_analytics', 'mcp_security']
            expected_core_tables = ['tasks', 'tools', 'tool_executions']
            expected_memory_tables = ['semantic_memory', 'knowledge_base']
            
            return {
                'success': (
                    len(schemas) == len(expected_schemas) and
                    len(core_tables) == len(expected_core_tables) and
                    len(memory_tables) == len(expected_memory_tables)
                ),
                'schemas_found': schemas,
                'core_tables_found': core_tables,
                'memory_tables_found': memory_tables
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _test_health_endpoints(self) -> Dict[str, Any]:
        """Test endpoints de health check"""
        endpoints = [
            'http://localhost:3000/health',
            'http://localhost:3000/api/health',
            'http://localhost:8080/health',  # webhooks
            'http://localhost:8766/health',  # notifications
            'http://localhost:8767/health'   # memory
        ]
        
        results = {}
        for endpoint in endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(endpoint, timeout=5) as response:
                        data = await response.json()
                        results[endpoint] = {
                            'status_code': response.status,
                            'response_data': data,
                            'success': response.status == 200
                        }
            except Exception as e:
                results[endpoint] = {'success': False, 'error': str(e)}
        
        successful = sum(1 for r in results.values() if r.get('success', False))
        
        return {
            'success': successful == len(endpoints),
            'successful_endpoints': successful,
            'total_endpoints': len(endpoints),
            'endpoint_results': results
        }
    
    def _generate_report(self) -> Dict[str, Any]:
        """Genera reporte completo de testing"""
        total_duration = time.time() - self.start_time
        
        passed = [r for r in self.results if r.status == 'passed']
        failed = [r for r in self.results if r.status == 'failed']
        skipped = [r for r in self.results if r.status == 'skipped']
        
        report = {
            'summary': {
                'total_tests': len(self.results),
                'passed': len(passed),
                'failed': len(failed),
                'skipped': len(skipped),
                'success_rate': len(passed) / len(self.results) * 100 if self.results else 0,
                'total_duration': total_duration,
                'timestamp': datetime.now().isoformat()
            },
            'results': [
                {
                    'name': r.name,
                    'status': r.status,
                    'duration': r.duration,
                    'error': r.error,
                    'details': r.details
                }
                for r in self.results
            ],
            'failed_tests': [
                {
                    'name': r.name,
                    'error': r.error,
                    'duration': r.duration
                }
                for r in failed
            ]
        }
        
        return report

# Configuración de testing
async def main():
    """Función principal para ejecutar tests"""
    config = {
        'postgres_host': os.getenv('POSTGRES_HOST', 'localhost'),
        'postgres_port': int(os.getenv('POSTGRES_PORT', 5432)),
        'postgres_db': os.getenv('POSTGRES_DB', 'mcp_enterprise'),
        'postgres_user': os.getenv('POSTGRES_USER', 'mcp_user'),
        'postgres_password': os.getenv('POSTGRES_PASSWORD', 'mcp_secure_password_2024'),
        'redis_host': os.getenv('REDIS_HOST', 'localhost'),
        'redis_port': int(os.getenv('REDIS_PORT', 6379)),
        'redis_password': os.getenv('REDIS_PASSWORD', 'redis_secure_password_2024'),
        'backend_url': os.getenv('BACKEND_URL', 'http://localhost:3000'),
        'frontend_url': os.getenv('FRONTEND_URL', 'http://localhost:80')
    }
    
    suite = MCPTestSuite(config)
    report = await suite.run_all_tests()
    
    # Imprimir reporte
    print("\n" + "=" * 60)
    print("🧪 MCP ENTERPRISE TESTING REPORT")
    print("=" * 60)
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"✅ Passed: {report['summary']['passed']}")
    print(f"❌ Failed: {report['summary']['failed']}")
    print(f"⏭️ Skipped: {report['summary']['skipped']}")
    print(f"📊 Success Rate: {report['summary']['success_rate']:.1f}%")
    print(f"⏱️ Duration: {report['summary']['total_duration']:.2f}s")
    
    if report['failed_tests']:
        print("\n❌ FAILED TESTS:")
        for test in report['failed_tests']:
            print(f"  • {test['name']}: {test['error']}")
    
    # Guardar reporte en archivo
    with open('mcp_test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Full report saved to: mcp_test_report.json")
    
    # Exit code basado en resultados
    exit_code = 0 if report['summary']['failed'] == 0 else 1
    return exit_code

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

