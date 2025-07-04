#!/usr/bin/env python3
"""
UltraMCP ContextBuilderAgent 2.0 - Semantic Coherence Bus
High-performance messaging system for semantic coherence across microservices
"""

import asyncio
import redis.asyncio as redis
import json
import logging
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib
import uuid
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SemanticMessage:
    """Represents a message in the semantic coherence bus"""
    message_id: str
    channel: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: str
    source_service: str
    correlation_id: Optional[str] = None
    priority: int = 0
    ttl: int = 3600  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SemanticMessage':
        return cls(**data)

@dataclass
class ContextMutation:
    """Represents a context mutation message"""
    mutation_id: str
    mutation_type: str
    target_domain: str
    new_value: Any
    previous_value: Any
    confidence: float
    requires_cod_validation: bool
    source: str
    timestamp: str
    
class CircuitBreaker:
    """Circuit breaker for semantic coherence protection"""
    
    def __init__(self, failure_threshold: int = 3, recovery_threshold: int = 5, 
                 timeout_window: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_threshold = recovery_threshold
        self.timeout_window = timeout_window
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout_window:
                self.state = "HALF_OPEN"
                return True
            return False
        elif self.state == "HALF_OPEN":
            return True
        return False
    
    def record_success(self):
        """Record successful operation"""
        if self.state == "HALF_OPEN":
            self.success_count += 1
            if self.success_count >= self.recovery_threshold:
                self.state = "CLOSED"
                self.failure_count = 0
                self.success_count = 0
        elif self.state == "CLOSED":
            self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.success_count = 0

class SemanticCoherenceBus:
    """
    High-performance semantic coherence bus using Redis Streams
    Provides pub/sub messaging for context mutations and validation
    """
    
    def __init__(self, redis_url: str = "redis://mcp-redis:6379/0"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.subscribers: Dict[str, List[Callable]] = {}
        self.circuit_breaker = CircuitBreaker()
        self.performance_metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "latency_sum": 0,
            "latency_count": 0
        }
        
        # Channel configurations
        self.channels = {
            "context_mutations": {"max_len": 10000, "retention": "7d"},
            "semantic_validation": {"max_len": 5000, "retention": "3d"},
            "coherence_alerts": {"max_len": 1000, "retention": "30d"},
            "fragment_updates": {"max_len": 20000, "retention": "14d"}
        }
        
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Connected to Redis for Semantic Coherence Bus")
            
            # Initialize streams if they don't exist
            for channel, config in self.channels.items():
                try:
                    await self.redis_client.xgroup_create(
                        channel, "coherence_group", id="0", mkstream=True
                    )
                except redis.exceptions.ResponseError as e:
                    if "BUSYGROUP" not in str(e):
                        logger.warning(f"Failed to create group for {channel}: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
    
    @asynccontextmanager
    async def performance_tracking(self, operation: str):
        """Context manager for performance tracking"""
        start_time = time.time()
        try:
            yield
            self.circuit_breaker.record_success()
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error(f"Operation {operation} failed: {e}")
            raise
        finally:
            latency = (time.time() - start_time) * 1000  # ms
            self.performance_metrics["latency_sum"] += latency
            self.performance_metrics["latency_count"] += 1
            
            if latency > 50:  # P95 target
                logger.warning(f"High latency detected: {latency:.2f}ms for {operation}")
    
    async def publish_context_mutation(self, mutation: ContextMutation) -> str:
        """Publish a context mutation to the semantic bus"""
        if not self.circuit_breaker.can_execute():
            raise Exception("Circuit breaker is OPEN - semantic bus unavailable")
        
        async with self.performance_tracking("publish_context_mutation"):
            message = SemanticMessage(
                message_id=str(uuid.uuid4()),
                channel="context_mutations",
                message_type="context_mutation",
                payload=asdict(mutation),
                timestamp=datetime.utcnow().isoformat() + "Z",
                source_service="context_builder_agent",
                priority=1 if mutation.requires_cod_validation else 0
            )
            
            stream_data = message.to_dict()
            result = await self.redis_client.xadd(
                "context_mutations",
                stream_data,
                maxlen=self.channels["context_mutations"]["max_len"]
            )
            
            self.performance_metrics["messages_sent"] += 1
            logger.info(f"Published context mutation {mutation.mutation_id} to stream: {result}")
            return result
    
    async def publish_semantic_validation(self, validation_result: Dict[str, Any]) -> str:
        """Publish semantic validation results"""
        if not self.circuit_breaker.can_execute():
            raise Exception("Circuit breaker is OPEN - semantic bus unavailable")
        
        async with self.performance_tracking("publish_semantic_validation"):
            message = SemanticMessage(
                message_id=str(uuid.uuid4()),
                channel="semantic_validation",
                message_type="validation_result",
                payload=validation_result,
                timestamp=datetime.utcnow().isoformat() + "Z",
                source_service="coherence_validator"
            )
            
            result = await self.redis_client.xadd(
                "semantic_validation",
                message.to_dict(),
                maxlen=self.channels["semantic_validation"]["max_len"]
            )
            
            self.performance_metrics["messages_sent"] += 1
            return result
    
    async def publish_coherence_alert(self, alert: Dict[str, Any]) -> str:
        """Publish coherence alert"""
        if not self.circuit_breaker.can_execute():
            raise Exception("Circuit breaker is OPEN - semantic bus unavailable")
        
        async with self.performance_tracking("publish_coherence_alert"):
            message = SemanticMessage(
                message_id=str(uuid.uuid4()),
                channel="coherence_alerts",
                message_type="coherence_alert",
                payload=alert,
                timestamp=datetime.utcnow().isoformat() + "Z",
                source_service="coherence_validator",
                priority=2  # High priority for alerts
            )
            
            result = await self.redis_client.xadd(
                "coherence_alerts",
                message.to_dict(),
                maxlen=self.channels["coherence_alerts"]["max_len"]
            )
            
            self.performance_metrics["messages_sent"] += 1
            logger.warning(f"Published coherence alert: {alert.get('alert_type', 'unknown')}")
            return result
    
    async def publish_fragment_update(self, fragment_data: Dict[str, Any]) -> str:
        """Publish fragment update"""
        if not self.circuit_breaker.can_execute():
            raise Exception("Circuit breaker is OPEN - semantic bus unavailable")
        
        async with self.performance_tracking("publish_fragment_update"):
            message = SemanticMessage(
                message_id=str(uuid.uuid4()),
                channel="fragment_updates",
                message_type="fragment_update",
                payload=fragment_data,
                timestamp=datetime.utcnow().isoformat() + "Z",
                source_service="fragment_manager"
            )
            
            result = await self.redis_client.xadd(
                "fragment_updates",
                message.to_dict(),
                maxlen=self.channels["fragment_updates"]["max_len"]
            )
            
            self.performance_metrics["messages_sent"] += 1
            return result
    
    async def subscribe_to_mutations(self, callback: Callable[[ContextMutation], None]):
        """Subscribe to context mutations"""
        await self._subscribe_to_channel("context_mutations", callback)
    
    async def subscribe_to_validations(self, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to semantic validations"""
        await self._subscribe_to_channel("semantic_validation", callback)
    
    async def subscribe_to_alerts(self, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to coherence alerts"""
        await self._subscribe_to_channel("coherence_alerts", callback)
    
    async def subscribe_to_fragments(self, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to fragment updates"""
        await self._subscribe_to_channel("fragment_updates", callback)
    
    async def _subscribe_to_channel(self, channel: str, callback: Callable):
        """Internal method to subscribe to a specific channel"""
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        self.subscribers[channel].append(callback)
        
        # Start consumer if not already running
        asyncio.create_task(self._consume_channel(channel))
    
    async def _consume_channel(self, channel: str):
        """Consume messages from a specific channel"""
        consumer_name = f"consumer_{channel}_{uuid.uuid4().hex[:8]}"
        
        try:
            while True:
                if not self.circuit_breaker.can_execute():
                    logger.warning(f"Circuit breaker OPEN - pausing consumption of {channel}")
                    await asyncio.sleep(5)
                    continue
                
                async with self.performance_tracking(f"consume_{channel}"):
                    messages = await self.redis_client.xreadgroup(
                        "coherence_group",
                        consumer_name,
                        {channel: ">"},
                        count=10,
                        block=1000
                    )
                    
                    for stream, stream_messages in messages:
                        for message_id, fields in stream_messages:
                            try:
                                # Process message
                                message_data = {k.decode(): v.decode() for k, v in fields.items()}
                                
                                # Parse payload if it's JSON
                                if 'payload' in message_data:
                                    try:
                                        message_data['payload'] = json.loads(message_data['payload'])
                                    except json.JSONDecodeError:
                                        pass
                                
                                # Call callbacks
                                for callback in self.subscribers.get(channel, []):
                                    try:
                                        if channel == "context_mutations":
                                            mutation_data = message_data['payload']
                                            mutation = ContextMutation(**mutation_data)
                                            await callback(mutation)
                                        else:
                                            await callback(message_data['payload'])
                                    except Exception as e:
                                        logger.error(f"Callback error for {channel}: {e}")
                                
                                # Acknowledge message
                                await self.redis_client.xack("coherence_group", channel, message_id)
                                self.performance_metrics["messages_received"] += 1
                                
                            except Exception as e:
                                logger.error(f"Error processing message {message_id}: {e}")
                
        except Exception as e:
            logger.error(f"Error in channel consumer {channel}: {e}")
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        avg_latency = 0
        if self.performance_metrics["latency_count"] > 0:
            avg_latency = self.performance_metrics["latency_sum"] / self.performance_metrics["latency_count"]
        
        return {
            "messages_sent": self.performance_metrics["messages_sent"],
            "messages_received": self.performance_metrics["messages_received"],
            "avg_latency_ms": round(avg_latency, 2),
            "circuit_breaker_state": self.circuit_breaker.state,
            "circuit_breaker_failures": self.circuit_breaker.failure_count,
            "throughput_target": 10000,  # msg/s
            "latency_p95_target": 50,    # ms
            "availability_target": 99.9   # %
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Check Redis connection
            await self.redis_client.ping()
            
            # Check circuit breaker state
            cb_healthy = self.circuit_breaker.state != "OPEN"
            
            # Check performance metrics
            metrics = await self.get_performance_metrics()
            latency_healthy = metrics["avg_latency_ms"] < 100  # Allow some buffer
            
            return {
                "healthy": cb_healthy and latency_healthy,
                "redis_connected": True,
                "circuit_breaker_state": self.circuit_breaker.state,
                "average_latency_ms": metrics["avg_latency_ms"],
                "messages_processed": metrics["messages_sent"] + metrics["messages_received"],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

# Singleton instance
semantic_bus = None

async def get_semantic_bus() -> SemanticCoherenceBus:
    """Get singleton instance of semantic coherence bus"""
    global semantic_bus
    if semantic_bus is None:
        semantic_bus = SemanticCoherenceBus()
        await semantic_bus.connect()
    return semantic_bus

# Convenience functions for common operations
async def publish_mutation(mutation: ContextMutation) -> str:
    """Convenience function to publish context mutation"""
    bus = await get_semantic_bus()
    return await bus.publish_context_mutation(mutation)

async def publish_validation(result: Dict[str, Any]) -> str:
    """Convenience function to publish validation result"""
    bus = await get_semantic_bus()
    return await bus.publish_semantic_validation(result)

async def publish_alert(alert: Dict[str, Any]) -> str:
    """Convenience function to publish coherence alert"""
    bus = await get_semantic_bus()
    return await bus.publish_coherence_alert(alert)

async def publish_fragment(fragment_data: Dict[str, Any]) -> str:
    """Convenience function to publish fragment update"""
    bus = await get_semantic_bus()
    return await bus.publish_fragment_update(fragment_data)

if __name__ == "__main__":
    async def test_semantic_bus():
        """Test the semantic coherence bus"""
        bus = SemanticCoherenceBus()
        await bus.connect()
        
        # Test context mutation
        mutation = ContextMutation(
            mutation_id="test_mutation_1",
            mutation_type="ADD_INSIGHT",
            target_domain="PAIN_POINTS.problemas_actuales",
            new_value="Test insight",
            previous_value=None,
            confidence=0.85,
            requires_cod_validation=False,
            source="test_system",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
        await bus.publish_context_mutation(mutation)
        
        # Test health check
        health = await bus.health_check()
        print(f"Health check: {health}")
        
        # Test metrics
        metrics = await bus.get_performance_metrics()
        print(f"Performance metrics: {metrics}")
        
        await bus.disconnect()
    
    asyncio.run(test_semantic_bus())