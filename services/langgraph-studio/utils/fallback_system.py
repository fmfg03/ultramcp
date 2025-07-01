"""
Fallback & Redundancy System for MCP
Intelligent fallback mechanisms for research and LLM services
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import time
import random

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"

class FallbackStrategy(Enum):
    SEQUENTIAL = "sequential"  # Try services one by one
    PARALLEL = "parallel"      # Try multiple services simultaneously
    WEIGHTED = "weighted"      # Try based on success rates
    ADAPTIVE = "adaptive"      # Learn from failures

class FallbackManager:
    """
    Manages fallback strategies for MCP services
    """
    
    def __init__(self):
        self.services = {}
        self.service_stats = {}
        self.fallback_chains = {}
        self.circuit_breakers = {}
        self.logger = logging.getLogger(__name__)
        
    def register_service(self, service_name: str, service_instance, priority: int = 1):
        """Register a service with fallback manager"""
        self.services[service_name] = {
            'instance': service_instance,
            'priority': priority,
            'status': ServiceStatus.UNKNOWN,
            'last_check': None,
            'consecutive_failures': 0
        }
        
        self.service_stats[service_name] = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'avg_response_time': 0,
            'last_success': None,
            'last_failure': None
        }
        
        self.circuit_breakers[service_name] = {
            'state': 'closed',  # closed, open, half_open
            'failure_count': 0,
            'last_failure_time': None,
            'timeout': 60  # seconds
        }
        
    def register_fallback_chain(self, chain_name: str, services: List[str], strategy: FallbackStrategy = FallbackStrategy.SEQUENTIAL):
        """Register a fallback chain"""
        self.fallback_chains[chain_name] = {
            'services': services,
            'strategy': strategy,
            'last_used': None,
            'success_count': 0,
            'failure_count': 0
        }
        
    async def execute_with_fallback(self, chain_name: str, operation: str, *args, **kwargs) -> Dict[str, Any]:
        """Execute operation with fallback strategy"""
        chain = self.fallback_chains.get(chain_name)
        if not chain:
            raise ValueError(f"Fallback chain '{chain_name}' not found")
            
        strategy = chain['strategy']
        services = chain['services']
        
        if strategy == FallbackStrategy.SEQUENTIAL:
            return await self._execute_sequential(services, operation, *args, **kwargs)
        elif strategy == FallbackStrategy.PARALLEL:
            return await self._execute_parallel(services, operation, *args, **kwargs)
        elif strategy == FallbackStrategy.WEIGHTED:
            return await self._execute_weighted(services, operation, *args, **kwargs)
        elif strategy == FallbackStrategy.ADAPTIVE:
            return await self._execute_adaptive(services, operation, *args, **kwargs)
        else:
            raise ValueError(f"Unknown fallback strategy: {strategy}")
            
    async def _execute_sequential(self, services: List[str], operation: str, *args, **kwargs) -> Dict[str, Any]:
        """Execute services sequentially until one succeeds"""
        last_error = None
        
        for service_name in services:
            if not self._is_service_available(service_name):
                continue
                
            try:
                start_time = time.time()
                service = self.services[service_name]['instance']
                
                # Execute the operation
                if hasattr(service, operation):
                    result = await getattr(service, operation)(*args, **kwargs)
                else:
                    result = await service.execute(operation, *args, **kwargs)
                
                # Record success
                response_time = time.time() - start_time
                self._record_success(service_name, response_time)
                
                return {
                    'success': True,
                    'result': result,
                    'service_used': service_name,
                    'response_time': response_time,
                    'fallback_used': service_name != services[0]
                }
                
            except Exception as e:
                self._record_failure(service_name, str(e))
                last_error = e
                self.logger.warning(f"Service {service_name} failed: {e}")
                continue
                
        # All services failed
        return {
            'success': False,
            'error': str(last_error) if last_error else "All services failed",
            'services_tried': services,
            'fallback_exhausted': True
        }
        
    async def _execute_parallel(self, services: List[str], operation: str, *args, **kwargs) -> Dict[str, Any]:
        """Execute services in parallel, return first successful result"""
        available_services = [s for s in services if self._is_service_available(s)]
        
        if not available_services:
            return {
                'success': False,
                'error': "No services available",
                'services_tried': services
            }
            
        # Create tasks for all available services
        tasks = []
        for service_name in available_services:
            task = asyncio.create_task(
                self._execute_single_service(service_name, operation, *args, **kwargs)
            )
            tasks.append((service_name, task))
            
        # Wait for first successful result
        try:
            done, pending = await asyncio.wait(
                [task for _, task in tasks],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
                
            # Get the first completed result
            for task in done:
                try:
                    result = await task
                    if result['success']:
                        return result
                except Exception as e:
                    continue
                    
            # If no successful result, wait for all to complete
            for task in pending:
                try:
                    await task
                except:
                    pass
                    
            return {
                'success': False,
                'error': "All parallel services failed",
                'services_tried': available_services
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Parallel execution failed: {e}",
                'services_tried': available_services
            }
            
    async def _execute_weighted(self, services: List[str], operation: str, *args, **kwargs) -> Dict[str, Any]:
        """Execute services based on success rate weights"""
        # Calculate weights based on success rates
        weights = []
        for service_name in services:
            if not self._is_service_available(service_name):
                weights.append(0)
                continue
                
            stats = self.service_stats[service_name]
            if stats['total_calls'] == 0:
                weights.append(1.0)  # Default weight for new services
            else:
                success_rate = stats['successful_calls'] / stats['total_calls']
                # Boost weight for faster services
                response_time_factor = max(0.1, 1.0 / (stats['avg_response_time'] + 0.1))
                weights.append(success_rate * response_time_factor)
                
        # Sort services by weight (highest first)
        weighted_services = sorted(zip(services, weights), key=lambda x: x[1], reverse=True)
        ordered_services = [s for s, w in weighted_services if w > 0]
        
        # Execute sequentially in weighted order
        return await self._execute_sequential(ordered_services, operation, *args, **kwargs)
        
    async def _execute_adaptive(self, services: List[str], operation: str, *args, **kwargs) -> Dict[str, Any]:
        """Adaptive execution that learns from patterns"""
        # Use weighted strategy but with adaptive learning
        result = await self._execute_weighted(services, operation, *args, **kwargs)
        
        # Learn from the result
        if result['success']:
            service_used = result['service_used']
            # Boost the successful service's priority
            self.services[service_used]['priority'] += 0.1
        else:
            # Reduce priority of failed services
            for service_name in result.get('services_tried', []):
                self.services[service_name]['priority'] = max(0.1, self.services[service_name]['priority'] - 0.05)
                
        return result
        
    async def _execute_single_service(self, service_name: str, operation: str, *args, **kwargs) -> Dict[str, Any]:
        """Execute operation on a single service"""
        start_time = time.time()
        
        try:
            service = self.services[service_name]['instance']
            
            if hasattr(service, operation):
                result = await getattr(service, operation)(*args, **kwargs)
            else:
                result = await service.execute(operation, *args, **kwargs)
                
            response_time = time.time() - start_time
            self._record_success(service_name, response_time)
            
            return {
                'success': True,
                'result': result,
                'service_used': service_name,
                'response_time': response_time
            }
            
        except Exception as e:
            self._record_failure(service_name, str(e))
            return {
                'success': False,
                'error': str(e),
                'service_used': service_name
            }
            
    def _is_service_available(self, service_name: str) -> bool:
        """Check if service is available (circuit breaker logic)"""
        if service_name not in self.services:
            return False
            
        circuit_breaker = self.circuit_breakers[service_name]
        
        if circuit_breaker['state'] == 'open':
            # Check if timeout has passed
            if time.time() - circuit_breaker['last_failure_time'] > circuit_breaker['timeout']:
                circuit_breaker['state'] = 'half_open'
                return True
            return False
            
        return True
        
    def _record_success(self, service_name: str, response_time: float):
        """Record successful service call"""
        stats = self.service_stats[service_name]
        stats['total_calls'] += 1
        stats['successful_calls'] += 1
        stats['last_success'] = time.time()
        
        # Update average response time
        if stats['avg_response_time'] == 0:
            stats['avg_response_time'] = response_time
        else:
            stats['avg_response_time'] = (stats['avg_response_time'] + response_time) / 2
            
        # Reset circuit breaker
        circuit_breaker = self.circuit_breakers[service_name]
        circuit_breaker['failure_count'] = 0
        circuit_breaker['state'] = 'closed'
        
        # Update service status
        self.services[service_name]['status'] = ServiceStatus.HEALTHY
        self.services[service_name]['consecutive_failures'] = 0
        
    def _record_failure(self, service_name: str, error: str):
        """Record failed service call"""
        stats = self.service_stats[service_name]
        stats['total_calls'] += 1
        stats['failed_calls'] += 1
        stats['last_failure'] = time.time()
        
        # Update circuit breaker
        circuit_breaker = self.circuit_breakers[service_name]
        circuit_breaker['failure_count'] += 1
        circuit_breaker['last_failure_time'] = time.time()
        
        # Open circuit breaker if too many failures
        if circuit_breaker['failure_count'] >= 3:
            circuit_breaker['state'] = 'open'
            
        # Update service status
        self.services[service_name]['consecutive_failures'] += 1
        if self.services[service_name]['consecutive_failures'] >= 3:
            self.services[service_name]['status'] = ServiceStatus.FAILED
        else:
            self.services[service_name]['status'] = ServiceStatus.DEGRADED
            
    def get_service_stats(self) -> Dict[str, Any]:
        """Get statistics for all services"""
        return {
            'services': dict(self.service_stats),
            'circuit_breakers': dict(self.circuit_breakers),
            'fallback_chains': dict(self.fallback_chains)
        }

# Research Fallback Implementation
class ResearchFallbackService:
    """
    Fallback service for research operations
    Perplexity → Serper → Wikipedia
    """
    
    def __init__(self):
        self.fallback_manager = FallbackManager()
        self.setup_research_services()
        
    def setup_research_services(self):
        """Setup research service fallback chain"""
        # Register services (these would be actual service instances)
        self.fallback_manager.register_service('perplexity', MockPerplexityService(), priority=3)
        self.fallback_manager.register_service('serper', MockSerperService(), priority=2)
        self.fallback_manager.register_service('wikipedia', MockWikipediaService(), priority=1)
        
        # Register fallback chain
        self.fallback_manager.register_fallback_chain(
            'research',
            ['perplexity', 'serper', 'wikipedia'],
            FallbackStrategy.SEQUENTIAL
        )
        
    async def search_with_fallback(self, query: str, **kwargs) -> Dict[str, Any]:
        """Search with automatic fallback"""
        return await self.fallback_manager.execute_with_fallback(
            'research', 'search', query, **kwargs
        )

# LLM Fallback Implementation
class LLMFallbackService:
    """
    Fallback service for LLM operations
    DeepSeek → Mistral → Llama → OpenAI
    """
    
    def __init__(self):
        self.fallback_manager = FallbackManager()
        self.setup_llm_services()
        
    def setup_llm_services(self):
        """Setup LLM service fallback chain"""
        # Register services (these would be actual LLM service instances)
        self.fallback_manager.register_service('deepseek', MockDeepSeekService(), priority=4)
        self.fallback_manager.register_service('mistral', MockMistralService(), priority=3)
        self.fallback_manager.register_service('llama', MockLlamaService(), priority=2)
        self.fallback_manager.register_service('openai', MockOpenAIService(), priority=1)
        
        # Register fallback chains for different use cases
        self.fallback_manager.register_fallback_chain(
            'reasoning',
            ['deepseek', 'mistral', 'llama', 'openai'],
            FallbackStrategy.ADAPTIVE
        )
        
        self.fallback_manager.register_fallback_chain(
            'coding',
            ['deepseek', 'mistral', 'openai'],  # Skip Llama for coding
            FallbackStrategy.WEIGHTED
        )
        
        self.fallback_manager.register_fallback_chain(
            'creative',
            ['mistral', 'openai', 'llama'],  # Different order for creative tasks
            FallbackStrategy.SEQUENTIAL
        )
        
    async def generate_with_fallback(self, prompt: str, task_type: str = 'reasoning', **kwargs) -> Dict[str, Any]:
        """Generate with automatic LLM fallback"""
        chain_name = task_type if task_type in ['reasoning', 'coding', 'creative'] else 'reasoning'
        
        return await self.fallback_manager.execute_with_fallback(
            chain_name, 'generate', prompt, **kwargs
        )

# Mock service implementations for testing
class MockPerplexityService:
    async def search(self, query: str, **kwargs):
        # Simulate occasional failures
        if random.random() < 0.1:
            raise Exception("Perplexity API rate limit exceeded")
        await asyncio.sleep(0.5)  # Simulate API call
        return {
            'answer': f"Perplexity search result for: {query}",
            'sources': ['https://example1.com', 'https://example2.com'],
            'confidence': 0.9
        }

class MockSerperService:
    async def search(self, query: str, **kwargs):
        if random.random() < 0.05:
            raise Exception("Serper API error")
        await asyncio.sleep(0.3)
        return {
            'answer': f"Serper search result for: {query}",
            'sources': ['https://serper1.com', 'https://serper2.com'],
            'confidence': 0.8
        }

class MockWikipediaService:
    async def search(self, query: str, **kwargs):
        await asyncio.sleep(0.2)
        return {
            'answer': f"Wikipedia search result for: {query}",
            'sources': ['https://en.wikipedia.org/wiki/...'],
            'confidence': 0.7
        }

class MockDeepSeekService:
    async def generate(self, prompt: str, **kwargs):
        if random.random() < 0.15:
            raise Exception("DeepSeek model overloaded")
        await asyncio.sleep(1.0)
        return {
            'text': f"DeepSeek response to: {prompt[:50]}...",
            'model': 'deepseek-coder',
            'confidence': 0.85
        }

class MockMistralService:
    async def generate(self, prompt: str, **kwargs):
        if random.random() < 0.08:
            raise Exception("Mistral connection timeout")
        await asyncio.sleep(0.8)
        return {
            'text': f"Mistral response to: {prompt[:50]}...",
            'model': 'mistral-7b',
            'confidence': 0.8
        }

class MockLlamaService:
    async def generate(self, prompt: str, **kwargs):
        if random.random() < 0.12:
            raise Exception("Llama model not available")
        await asyncio.sleep(1.2)
        return {
            'text': f"Llama response to: {prompt[:50]}...",
            'model': 'llama-2-7b',
            'confidence': 0.75
        }

class MockOpenAIService:
    async def generate(self, prompt: str, **kwargs):
        if random.random() < 0.02:
            raise Exception("OpenAI API quota exceeded")
        await asyncio.sleep(0.6)
        return {
            'text': f"OpenAI response to: {prompt[:50]}...",
            'model': 'gpt-3.5-turbo',
            'confidence': 0.9
        }

# Global instances
research_fallback = ResearchFallbackService()
llm_fallback = LLMFallbackService()

# Example usage and testing
async def test_fallback_system():
    """Test the fallback system"""
    print("🔄 Testing Research Fallback...")
    
    # Test research fallback
    result = await research_fallback.search_with_fallback("What is artificial intelligence?")
    print(f"Research result: {result}")
    
    print("\n🔄 Testing LLM Fallback...")
    
    # Test LLM fallback
    result = await llm_fallback.generate_with_fallback(
        "Explain quantum computing", 
        task_type="reasoning"
    )
    print(f"LLM result: {result}")
    
    # Get statistics
    print("\n📊 Service Statistics:")
    research_stats = research_fallback.fallback_manager.get_service_stats()
    llm_stats = llm_fallback.fallback_manager.get_service_stats()
    
    print("Research services:", research_stats['services'])
    print("LLM services:", llm_stats['services'])

if __name__ == "__main__":
    asyncio.run(test_fallback_system())

