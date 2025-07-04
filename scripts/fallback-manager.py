#!/usr/bin/env python3
"""
UltraMCP Fallback Manager
Handles Redis, Database, and Service Discovery fallbacks
"""

import json
import time
import threading
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import queue
import logging

@dataclass
class Event:
    """In-memory event structure"""
    id: str
    type: str
    data: Dict[str, Any]
    timestamp: datetime
    ttl: Optional[datetime] = None

class InMemoryEventStore:
    """Fallback event store when Redis is unavailable"""
    
    def __init__(self, max_events: int = 10000, cleanup_interval: int = 300):
        self.events: Dict[str, Event] = {}
        self.subscribers: Dict[str, List[queue.Queue]] = {}
        self.max_events = max_events
        self.cleanup_interval = cleanup_interval
        self.lock = threading.RLock()
        self._start_cleanup_thread()
        
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup():
            while True:
                try:
                    time.sleep(self.cleanup_interval)
                    self._cleanup_expired_events()
                except Exception as e:
                    logging.error(f"Cleanup thread error: {e}")
                    
        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()
        
    def _cleanup_expired_events(self):
        """Remove expired events"""
        with self.lock:
            current_time = datetime.now()
            expired_keys = [
                key for key, event in self.events.items()
                if event.ttl and current_time > event.ttl
            ]
            
            for key in expired_keys:
                del self.events[key]
                
            # Limit total events
            if len(self.events) > self.max_events:
                # Remove oldest events
                sorted_events = sorted(
                    self.events.items(),
                    key=lambda x: x[1].timestamp
                )
                for key, _ in sorted_events[:len(self.events) - self.max_events]:
                    del self.events[key]
    
    def publish(self, channel: str, event_data: Dict[str, Any], ttl_seconds: int = 3600):
        """Publish event to in-memory store"""
        with self.lock:
            event_id = f"{channel}_{int(time.time() * 1000)}"
            ttl = datetime.now() + timedelta(seconds=ttl_seconds) if ttl_seconds > 0 else None
            
            event = Event(
                id=event_id,
                type=channel,
                data=event_data,
                timestamp=datetime.now(),
                ttl=ttl
            )
            
            self.events[event_id] = event
            
            # Notify subscribers
            if channel in self.subscribers:
                for sub_queue in self.subscribers[channel]:
                    try:
                        sub_queue.put_nowait(event)
                    except queue.Full:
                        pass  # Drop event if queue is full
                        
            return event_id
    
    def subscribe(self, channel: str) -> queue.Queue:
        """Subscribe to events on a channel"""
        with self.lock:
            if channel not in self.subscribers:
                self.subscribers[channel] = []
                
            event_queue = queue.Queue(maxsize=1000)
            self.subscribers[channel].append(event_queue)
            return event_queue
    
    def get_events(self, channel: str, limit: int = 100) -> List[Event]:
        """Get recent events from a channel"""
        with self.lock:
            channel_events = [
                event for event in self.events.values()
                if event.type == channel
            ]
            
            # Sort by timestamp, newest first
            channel_events.sort(key=lambda x: x.timestamp, reverse=True)
            return channel_events[:limit]

class FallbackManager:
    """Manages all fallback mechanisms"""
    
    def __init__(self):
        self.redis_available = False
        self.postgres_available = False
        self.supabase_available = False
        self.event_store = InMemoryEventStore()
        self.service_registry = {}
        self.local_data = {}
        
    def check_redis_health(self) -> bool:
        """Check Redis connectivity"""
        try:
            import redis
            r = redis.Redis(host='sam.chat', port=6379, socket_timeout=2)
            r.ping()
            self.redis_available = True
            return True
        except Exception:
            self.redis_available = False
            return False
    
    def check_postgres_health(self) -> bool:
        """Check PostgreSQL connectivity"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host="sam.chat",
                port=5432,
                database="ultramcp",
                user="ultramcp",
                password=os.getenv("POSTGRES_PASSWORD", ""),
                connect_timeout=3
            )
            conn.close()
            self.postgres_available = True
            return True
        except Exception:
            self.postgres_available = False
            return False
    
    def check_supabase_health(self) -> bool:
        """Check Supabase connectivity"""
        try:
            # Implement Supabase health check
            # For now, assume it's available if we have the URL
            supabase_url = os.getenv("SUPABASE_URL")
            if supabase_url:
                self.supabase_available = True
                return True
            return False
        except Exception:
            self.supabase_available = False
            return False
    
    def publish_event(self, channel: str, data: Dict[str, Any]) -> str:
        """Publish event with fallback logic"""
        if self.redis_available:
            try:
                import redis
                r = redis.Redis(host='sam.chat', port=6379)
                return r.publish(channel, json.dumps(data))
            except Exception:
                self.redis_available = False
        
        # Fallback to in-memory store
        return self.event_store.publish(channel, data)
    
    def subscribe_events(self, channel: str):
        """Subscribe to events with fallback logic"""
        if self.redis_available:
            try:
                import redis
                r = redis.Redis(host='sam.chat', port=6379)
                pubsub = r.pubsub()
                pubsub.subscribe(channel)
                return pubsub
            except Exception:
                self.redis_available = False
        
        # Fallback to in-memory store
        return self.event_store.subscribe(channel)
    
    def store_data(self, key: str, data: Any, table: str = "default"):
        """Store data with database fallback"""
        if self.postgres_available:
            try:
                # Store in PostgreSQL
                import psycopg2
                conn = psycopg2.connect(
                    host="sam.chat",
                    port=5432,
                    database="ultramcp",
                    user="ultramcp",
                    password=os.getenv("POSTGRES_PASSWORD", "")
                )
                cur = conn.cursor()
                
                # Create table if not exists
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table}_fallback (
                        key VARCHAR PRIMARY KEY,
                        data JSONB,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                # Insert or update data
                cur.execute(f"""
                    INSERT INTO {table}_fallback (key, data)
                    VALUES (%s, %s)
                    ON CONFLICT (key) DO UPDATE SET
                        data = EXCLUDED.data,
                        created_at = NOW()
                """, (key, json.dumps(data)))
                
                conn.commit()
                conn.close()
                return True
            except Exception:
                self.postgres_available = False
        
        # Fallback to local file storage
        self._store_locally(table, key, data)
        return True
    
    def _store_locally(self, table: str, key: str, data: Any):
        """Store data locally as fallback"""
        os.makedirs("data/fallback", exist_ok=True)
        file_path = f"data/fallback/{table}.json"
        
        # Load existing data
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                local_data = json.load(f)
        else:
            local_data = {}
        
        # Update data
        local_data[key] = {
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save data
        with open(file_path, 'w') as f:
            json.dump(local_data, f, indent=2)
    
    def get_data(self, key: str, table: str = "default") -> Optional[Any]:
        """Retrieve data with fallback logic"""
        if self.postgres_available:
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host="sam.chat",
                    port=5432,
                    database="ultramcp",
                    user="ultramcp",
                    password=os.getenv("POSTGRES_PASSWORD", "")
                )
                cur = conn.cursor()
                cur.execute(f"SELECT data FROM {table}_fallback WHERE key = %s", (key,))
                result = cur.fetchone()
                conn.close()
                
                if result:
                    return json.loads(result[0])
            except Exception:
                self.postgres_available = False
        
        # Fallback to local storage
        return self._get_locally(table, key)
    
    def _get_locally(self, table: str, key: str) -> Optional[Any]:
        """Get data from local storage"""
        file_path = f"data/fallback/{table}.json"
        
        if not os.path.exists(file_path):
            return None
            
        try:
            with open(file_path, 'r') as f:
                local_data = json.load(f)
                
            if key in local_data:
                return local_data[key]["data"]
        except Exception:
            pass
            
        return None
    
    def register_service(self, service_name: str, endpoint: str, health_check: str):
        """Register service manually as fallback"""
        self.service_registry[service_name] = {
            "endpoint": endpoint,
            "health_check": health_check,
            "registered_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        # Persist to storage
        self.store_data(service_name, self.service_registry[service_name], "services")
    
    def discover_service(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Discover service with fallback"""
        # Check local registry first
        if service_name in self.service_registry:
            return self.service_registry[service_name]
        
        # Check persistent storage
        service_data = self.get_data(service_name, "services")
        if service_data:
            self.service_registry[service_name] = service_data
            return service_data
        
        return None
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        return {
            "timestamp": datetime.now().isoformat(),
            "redis": {
                "available": self.check_redis_health(),
                "fallback": "in-memory events" if not self.redis_available else None
            },
            "postgres": {
                "available": self.check_postgres_health(),
                "fallback": "local file storage" if not self.postgres_available else None
            },
            "supabase": {
                "available": self.check_supabase_health(),
                "fallback": "local database" if not self.supabase_available else None
            },
            "services": {
                "registered": len(self.service_registry),
                "active": len([s for s in self.service_registry.values() if s.get("status") == "active"])
            },
            "in_memory_events": len(self.event_store.events),
            "status": "degraded" if not all([self.redis_available, self.postgres_available]) else "healthy"
        }

# Global fallback manager instance
fallback_manager = FallbackManager()

if __name__ == "__main__":
    # Test the fallback manager
    import argparse
    
    parser = argparse.ArgumentParser(description="UltraMCP Fallback Manager")
    parser.add_argument("--health", action="store_true", help="Run health check")
    parser.add_argument("--test-events", action="store_true", help="Test event system")
    
    args = parser.parse_args()
    
    if args.health:
        health = fallback_manager.health_check()
        print(json.dumps(health, indent=2))
    
    if args.test_events:
        # Test event publishing
        event_id = fallback_manager.publish_event("test", {"message": "Hello World"})
        print(f"Published event: {event_id}")
        
        # Test data storage
        fallback_manager.store_data("test_key", {"value": 42})
        retrieved = fallback_manager.get_data("test_key")
        print(f"Retrieved data: {retrieved}")