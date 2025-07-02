#!/usr/bin/env python3
"""
UltraMCP Database Fallback System
Handles Supabase connectivity issues with local database fallback
"""

import json
import sqlite3
import os
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
import uuid

@dataclass
class DatabaseConfig:
    """Database configuration structure"""
    type: str  # 'supabase', 'postgresql', 'sqlite'
    host: Optional[str] = None
    port: Optional[int] = None
    database: str = "ultramcp"
    username: Optional[str] = None
    password: Optional[str] = None
    url: Optional[str] = None
    file_path: Optional[str] = None

class LocalSQLiteManager:
    """Local SQLite database manager for fallback operations"""
    
    def __init__(self, db_path: str = "data/fallback/ultramcp_local.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        with self.lock:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for better concurrency
            
            # Create main tables
            tables = [
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT,
                    level TEXT,
                    service TEXT,
                    message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data TEXT
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    channel TEXT NOT NULL,
                    event_type TEXT,
                    payload TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS system_state (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS service_registry (
                    service_name TEXT PRIMARY KEY,
                    endpoint TEXT,
                    health_check TEXT,
                    status TEXT DEFAULT 'active',
                    metadata TEXT,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            ]
            
            for table_sql in tables:
                conn.execute(table_sql)
            
            # Create indexes for performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
                "CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(type)",
                "CREATE INDEX IF NOT EXISTS idx_logs_task_id ON logs(task_id)",
                "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_events_channel ON events(channel)",
                "CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at)"
            ]
            
            for index_sql in indexes:
                conn.execute(index_sql)
            
            conn.commit()
            conn.close()
    
    def execute_query(self, query: str, params: tuple = (), fetch: bool = False) -> Union[List[tuple], int]:
        """Execute SQL query with proper error handling"""
        with self.lock:
            try:
                conn = sqlite3.connect(str(self.db_path))
                conn.row_factory = sqlite3.Row  # Enable column access by name
                cursor = conn.cursor()
                
                cursor.execute(query, params)
                
                if fetch:
                    result = [dict(row) for row in cursor.fetchall()]
                    conn.close()
                    return result
                else:
                    affected_rows = cursor.rowcount
                    conn.commit()
                    conn.close()
                    return affected_rows
                    
            except Exception as e:
                logging.error(f"SQLite query error: {e}")
                if 'conn' in locals():
                    conn.close()
                raise
    
    def create_task(self, task_id: str, task_type: str, data: Dict[str, Any]) -> bool:
        """Create a new task in local database"""
        query = """
            INSERT OR REPLACE INTO tasks (id, type, data, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """
        try:
            self.execute_query(query, (task_id, task_type, json.dumps(data)))
            return True
        except Exception as e:
            logging.error(f"Failed to create task {task_id}: {e}")
            return False
    
    def update_task_status(self, task_id: str, status: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """Update task status in local database"""
        if data:
            query = """
                UPDATE tasks 
                SET status = ?, data = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            params = (status, json.dumps(data), task_id)
        else:
            query = """
                UPDATE tasks 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            params = (status, task_id)
        
        try:
            affected = self.execute_query(query, params)
            return affected > 0
        except Exception as e:
            logging.error(f"Failed to update task {task_id}: {e}")
            return False
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task from local database"""
        query = "SELECT * FROM tasks WHERE id = ?"
        try:
            results = self.execute_query(query, (task_id,), fetch=True)
            if results:
                task = results[0]
                if task['data']:
                    task['data'] = json.loads(task['data'])
                return task
            return None
        except Exception as e:
            logging.error(f"Failed to get task {task_id}: {e}")
            return None
    
    def get_tasks_by_status(self, status: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get tasks by status from local database"""
        query = """
            SELECT * FROM tasks 
            WHERE status = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """
        try:
            results = self.execute_query(query, (status, limit), fetch=True)
            for task in results:
                if task['data']:
                    task['data'] = json.loads(task['data'])
            return results
        except Exception as e:
            logging.error(f"Failed to get tasks with status {status}: {e}")
            return []
    
    def log_event(self, task_id: str, level: str, service: str, message: str, data: Optional[Dict] = None):
        """Log event to local database"""
        query = """
            INSERT INTO logs (task_id, level, service, message, data)
            VALUES (?, ?, ?, ?, ?)
        """
        try:
            self.execute_query(query, (
                task_id, level, service, message, 
                json.dumps(data) if data else None
            ))
        except Exception as e:
            logging.error(f"Failed to log event: {e}")
    
    def publish_event(self, channel: str, event_type: str, payload: Dict[str, Any], ttl_hours: int = 24) -> str:
        """Publish event to local database"""
        event_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(hours=ttl_hours)
        
        query = """
            INSERT INTO events (id, channel, event_type, payload, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """
        try:
            self.execute_query(query, (
                event_id, channel, event_type, 
                json.dumps(payload), expires_at.isoformat()
            ))
            return event_id
        except Exception as e:
            logging.error(f"Failed to publish event: {e}")
            return ""
    
    def get_events(self, channel: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get events from channel"""
        query = """
            SELECT * FROM events 
            WHERE channel = ? AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            ORDER BY created_at DESC 
            LIMIT ?
        """
        try:
            results = self.execute_query(query, (channel, limit), fetch=True)
            for event in results:
                if event['payload']:
                    event['payload'] = json.loads(event['payload'])
            return results
        except Exception as e:
            logging.error(f"Failed to get events for channel {channel}: {e}")
            return []
    
    def register_service(self, service_name: str, endpoint: str, health_check: str, metadata: Optional[Dict] = None):
        """Register service in local database"""
        query = """
            INSERT OR REPLACE INTO service_registry 
            (service_name, endpoint, health_check, metadata, last_seen)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        try:
            self.execute_query(query, (
                service_name, endpoint, health_check,
                json.dumps(metadata) if metadata else None
            ))
        except Exception as e:
            logging.error(f"Failed to register service {service_name}: {e}")
    
    def get_services(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get registered services"""
        if active_only:
            query = "SELECT * FROM service_registry WHERE status = 'active'"
        else:
            query = "SELECT * FROM service_registry"
        
        try:
            results = self.execute_query(query, fetch=True)
            for service in results:
                if service['metadata']:
                    service['metadata'] = json.loads(service['metadata'])
            return results
        except Exception as e:
            logging.error(f"Failed to get services: {e}")
            return []
    
    def cleanup_expired_data(self):
        """Clean up expired data"""
        queries = [
            "DELETE FROM events WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP",
            "DELETE FROM logs WHERE timestamp < datetime('now', '-7 days')",  # Keep logs for 7 days
        ]
        
        for query in queries:
            try:
                self.execute_query(query)
            except Exception as e:
                logging.error(f"Cleanup query failed: {e}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}
        
        stat_queries = {
            "tasks_total": "SELECT COUNT(*) as count FROM tasks",
            "tasks_pending": "SELECT COUNT(*) as count FROM tasks WHERE status = 'pending'",
            "tasks_completed": "SELECT COUNT(*) as count FROM tasks WHERE status = 'completed'",
            "logs_total": "SELECT COUNT(*) as count FROM logs",
            "events_total": "SELECT COUNT(*) as count FROM events",
            "services_active": "SELECT COUNT(*) as count FROM service_registry WHERE status = 'active'",
        }
        
        for stat_name, query in stat_queries.items():
            try:
                result = self.execute_query(query, fetch=True)
                stats[stat_name] = result[0]['count'] if result else 0
            except Exception as e:
                logging.error(f"Failed to get stat {stat_name}: {e}")
                stats[stat_name] = 0
        
        # Database file size
        try:
            stats["db_size_mb"] = round(self.db_path.stat().st_size / (1024 * 1024), 2)
        except:
            stats["db_size_mb"] = 0
            
        return stats

class DatabaseFallbackManager:
    """Manages database connections with fallback capabilities"""
    
    def __init__(self):
        self.primary_db = None
        self.fallback_db = LocalSQLiteManager()
        self.current_mode = "fallback"  # Start in fallback mode
        self.connection_attempts = 0
        self.max_connection_attempts = 3
    
    def check_primary_database(self, config: DatabaseConfig) -> bool:
        """Check if primary database is available"""
        try:
            if config.type == "postgresql":
                import psycopg2
                conn = psycopg2.connect(
                    host=config.host,
                    port=config.port,
                    database=config.database,
                    user=config.username,
                    password=config.password,
                    connect_timeout=5
                )
                conn.close()
                return True
            elif config.type == "supabase":
                # Implement Supabase connection check
                from supabase import create_client
                supabase = create_client(config.url, config.password)  # Using password as API key
                # Try a simple query
                result = supabase.table("_ultramcp_health_check").select("*").limit(1).execute()
                return True
        except Exception as e:
            logging.warning(f"Primary database check failed: {e}")
            self.connection_attempts += 1
            return False
    
    def switch_to_primary(self, config: DatabaseConfig):
        """Switch to primary database"""
        if self.check_primary_database(config):
            self.current_mode = "primary"
            self.connection_attempts = 0
            logging.info(f"Switched to primary database: {config.type}")
        else:
            logging.warning("Failed to switch to primary database, staying in fallback mode")
    
    def switch_to_fallback(self):
        """Switch to fallback database"""
        self.current_mode = "fallback"
        logging.warning("Switched to fallback database (SQLite)")
    
    def is_fallback_mode(self) -> bool:
        """Check if currently in fallback mode"""
        return self.current_mode == "fallback"
    
    def create_task(self, task_id: str, task_type: str, data: Dict[str, Any]) -> bool:
        """Create task with fallback support"""
        if self.current_mode == "fallback":
            return self.fallback_db.create_task(task_id, task_type, data)
        else:
            # Implement primary database task creation
            try:
                # Primary database logic here
                return True
            except Exception:
                self.switch_to_fallback()
                return self.fallback_db.create_task(task_id, task_type, data)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            "database_mode": self.current_mode,
            "connection_attempts": self.connection_attempts,
            "fallback_stats": self.fallback_db.get_database_stats(),
            "timestamp": datetime.now().isoformat()
        }
        
        if self.current_mode == "fallback":
            status["primary_database"] = "unavailable"
            status["fallback_database"] = "active"
        else:
            status["primary_database"] = "active"
            status["fallback_database"] = "standby"
        
        return status

# Global database manager instance
db_fallback_manager = DatabaseFallbackManager()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="UltraMCP Database Fallback Manager")
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--test", action="store_true", help="Run database tests")
    parser.add_argument("--cleanup", action="store_true", help="Clean up expired data")
    
    args = parser.parse_args()
    
    if args.status:
        status = db_fallback_manager.get_system_status()
        print(json.dumps(status, indent=2))
    
    if args.test:
        # Test database operations
        test_task_id = f"test_{int(datetime.now().timestamp())}"
        
        success = db_fallback_manager.create_task(
            test_task_id, 
            "test", 
            {"message": "Database test"}
        )
        
        print(f"Database test {'passed' if success else 'failed'}")
    
    if args.cleanup:
        db_fallback_manager.fallback_db.cleanup_expired_data()
        print("Database cleanup completed")