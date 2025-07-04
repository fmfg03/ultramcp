#!/usr/bin/env python3
"""
UltraMCP ContextBuilderAgent 2.0 - Custom Metrics Collector
Advanced metrics collection for Prometheus monitoring
"""

import time
import logging
import threading
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

import redis
import psycopg2
import requests
from prometheus_client import start_http_server, Gauge, Counter, Histogram, Info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContextBuilderMetricsCollector:
    """Custom metrics collector for ContextBuilderAgent 2.0"""
    
    def __init__(self):
        # Configuration
        self.redis_url = os.getenv('REDIS_URL', 'redis://sam.chat:6379')
        self.postgres_url = os.getenv('POSTGRES_URL', 'postgresql://contextbuilder:contextbuilder_secure_2024@sam.chat:5432/contextbuilder')
        self.prometheus_port = int(os.getenv('PROMETHEUS_PORT', '8000'))
        self.collection_interval = int(os.getenv('COLLECTION_INTERVAL', '30'))
        
        # Service endpoints
        self.services = {
            'contextbuilder_core': 'http://host.docker.internal:8020',
            'belief_reviser': 'http://host.docker.internal:8022',
            'contradiction_resolver': 'http://host.docker.internal:8024',
            'utility_predictor': 'http://host.docker.internal:8025',
            'context_drift_detector': 'http://host.docker.internal:8026',
            'prompt_assembler': 'http://host.docker.internal:8027',
            'context_observatory': 'http://host.docker.internal:8028',
            'deterministic_debug': 'http://host.docker.internal:8029',
            'context_memory_tuner': 'http://host.docker.internal:8030',
        }
        
        # Initialize connections
        self.redis_client = None
        self.postgres_conn = None
        
        # Prometheus metrics
        self.setup_metrics()
        
        # Collection thread
        self.running = False
        self.collection_thread = None
        
    def setup_metrics(self):
        """Setup Prometheus metrics"""
        
        # System Information
        self.system_info = Info('contextbuilder_system_info', 'System information')
        
        # Service Health Metrics
        self.service_health = Gauge('contextbuilder_service_health', 
                                  'Service health status (1=healthy, 0=unhealthy)', 
                                  ['service'])
        
        self.service_response_time = Histogram('contextbuilder_service_response_time_seconds',
                                             'Service response time in seconds',
                                             ['service'])
        
        # Business Logic Metrics
        self.coherence_score = Gauge('contextbuilder_coherence_score_average',
                                   'Average coherence score')
        
        self.validation_total = Counter('contextbuilder_validation_total',
                                      'Total number of validations',
                                      ['validation_type'])
        
        self.validation_failures = Counter('contextbuilder_validation_failures_total',
                                         'Total number of validation failures',
                                         ['validation_type'])
        
        self.belief_revisions = Counter('contextbuilder_belief_revisions_total',
                                      'Total number of belief revisions',
                                      ['revision_type'])
        
        self.context_drift_magnitude = Gauge('contextbuilder_context_drift_magnitude',
                                           'Current context drift magnitude')
        
        self.utility_prediction_accuracy = Gauge('contextbuilder_utility_prediction_accuracy',
                                                'Current utility prediction accuracy')
        
        # Performance Metrics
        self.processing_time = Histogram('contextbuilder_processing_time_seconds',
                                       'Processing time in seconds',
                                       ['operation_type'])
        
        self.queue_depth = Gauge('contextbuilder_queue_depth',
                               'Current queue depth',
                               ['queue_type'])
        
        # Database Metrics
        self.database_connections = Gauge('contextbuilder_database_connections',
                                        'Number of database connections')
        
        self.redis_memory_usage = Gauge('contextbuilder_redis_memory_usage_bytes',
                                      'Redis memory usage in bytes')
        
        # Observatory Metrics
        self.observatory_alerts = Gauge('contextbuilder_observatory_alert_count',
                                      'Number of active alerts from Observatory',
                                      ['severity'])
        
        self.observatory_health_checks = Counter('contextbuilder_observatory_health_check_failures',
                                                'Number of health check failures')
        
        # Stream Metrics (Redis Streams)
        self.stream_length = Gauge('contextbuilder_stream_length',
                                 'Length of Redis streams',
                                 ['stream_name'])
        
        # ML/AI Metrics
        self.ml_model_performance = Gauge('contextbuilder_ml_model_performance',
                                        'ML model performance score',
                                        ['model_name', 'metric_type'])
        
    def connect_redis(self) -> bool:
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Connected to Redis successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
            return False
            
    def connect_postgres(self) -> bool:
        """Connect to PostgreSQL"""
        try:
            self.postgres_conn = psycopg2.connect(self.postgres_url)
            logger.info("Connected to PostgreSQL successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            self.postgres_conn = None
            return False
            
    def collect_service_health(self):
        """Collect service health metrics"""
        for service_name, base_url in self.services.items():
            try:
                start_time = time.time()
                response = requests.get(f"{base_url}/health", timeout=5)
                response_time = time.time() - start_time
                
                # Record response time
                self.service_response_time.labels(service=service_name).observe(response_time)
                
                # Record health status
                if response.status_code == 200:
                    self.service_health.labels(service=service_name).set(1)
                    logger.debug(f"Service {service_name} is healthy")
                else:
                    self.service_health.labels(service=service_name).set(0)
                    logger.warning(f"Service {service_name} returned status {response.status_code}")
                    
            except Exception as e:
                self.service_health.labels(service=service_name).set(0)
                logger.error(f"Failed to check health of {service_name}: {e}")
                
    def collect_database_metrics(self):
        """Collect database-related metrics"""
        
        # PostgreSQL metrics
        if self.postgres_conn:
            try:
                with self.postgres_conn.cursor() as cursor:
                    # Count active connections
                    cursor.execute("SELECT count(*) FROM pg_stat_activity;")
                    connections = cursor.fetchone()[0]
                    self.database_connections.set(connections)
                    
                    # Coherence score from context_validations
                    cursor.execute("""
                        SELECT AVG(coherence_score) 
                        FROM context_validations 
                        WHERE created_at > NOW() - INTERVAL '1 hour';
                    """)
                    result = cursor.fetchone()[0]
                    if result:
                        self.coherence_score.set(float(result))
                    
                    # Validation metrics
                    cursor.execute("""
                        SELECT validation_type, COUNT(*) 
                        FROM context_validations 
                        WHERE created_at > NOW() - INTERVAL '1 hour'
                        GROUP BY validation_type;
                    """)
                    for validation_type, count in cursor.fetchall():
                        self.validation_total.labels(validation_type=validation_type)._value._value = count
                    
                    # Belief revision metrics
                    cursor.execute("""
                        SELECT revision_type, COUNT(*) 
                        FROM belief_revisions 
                        WHERE created_at > NOW() - INTERVAL '1 hour'
                        GROUP BY revision_type;
                    """)
                    for revision_type, count in cursor.fetchall():
                        self.belief_revisions.labels(revision_type=revision_type)._value._value = count
                    
                    # Context drift metrics
                    cursor.execute("""
                        SELECT AVG(drift_magnitude) 
                        FROM context_drift_events 
                        WHERE detected_at > NOW() - INTERVAL '15 minutes';
                    """)
                    result = cursor.fetchone()[0]
                    if result:
                        self.context_drift_magnitude.set(float(result))
                    
                    # Utility prediction accuracy
                    cursor.execute("""
                        SELECT AVG(prediction_accuracy) 
                        FROM utility_predictions 
                        WHERE evaluated_at > NOW() - INTERVAL '1 hour'
                        AND prediction_accuracy IS NOT NULL;
                    """)
                    result = cursor.fetchone()[0]
                    if result:
                        self.utility_prediction_accuracy.set(float(result))
                        
            except Exception as e:
                logger.error(f"Failed to collect PostgreSQL metrics: {e}")
                self.connect_postgres()  # Reconnect
                
        # Redis metrics
        if self.redis_client:
            try:
                # Memory usage
                info = self.redis_client.info('memory')
                self.redis_memory_usage.set(info['used_memory'])
                
                # Stream lengths
                streams = ['coherence_stream', 'context_events', 'validation_stream']
                for stream_name in streams:
                    try:
                        length = self.redis_client.xlen(stream_name)
                        self.stream_length.labels(stream_name=stream_name).set(length)
                    except:
                        # Stream doesn't exist
                        self.stream_length.labels(stream_name=stream_name).set(0)
                        
            except Exception as e:
                logger.error(f"Failed to collect Redis metrics: {e}")
                self.connect_redis()  # Reconnect
                
    def collect_observatory_metrics(self):
        """Collect Observatory-specific metrics"""
        try:
            response = requests.get(f"{self.services['context_observatory']}/api/observatory/alerts", timeout=5)
            if response.status_code == 200:
                alerts_data = response.json()
                
                # Count alerts by severity
                severity_counts = {'critical': 0, 'warning': 0, 'info': 0, 'low': 0}
                for alert in alerts_data.get('alerts', []):
                    severity = alert.get('severity', 'info')
                    severity_counts[severity] += 1
                
                for severity, count in severity_counts.items():
                    self.observatory_alerts.labels(severity=severity).set(count)
                    
        except Exception as e:
            logger.error(f"Failed to collect Observatory metrics: {e}")
            
    def collect_ml_metrics(self):
        """Collect ML/AI model performance metrics"""
        try:
            # Prompt Assembler ML metrics
            response = requests.get(f"{self.services['prompt_assembler']}/api/prompt/analytics", timeout=5)
            if response.status_code == 200:
                analytics = response.json()
                
                if 'model_performance' in analytics:
                    for model_name, metrics in analytics['model_performance'].items():
                        for metric_type, value in metrics.items():
                            self.ml_model_performance.labels(
                                model_name=model_name, 
                                metric_type=metric_type
                            ).set(float(value))
                            
        except Exception as e:
            logger.error(f"Failed to collect ML metrics: {e}")
            
    def collect_all_metrics(self):
        """Collect all metrics"""
        logger.info("Starting metrics collection cycle")
        
        # Update system info
        self.system_info.info({
            'version': '2.0',
            'environment': 'production',
            'collected_at': datetime.now().isoformat()
        })
        
        # Collect different metric categories
        self.collect_service_health()
        self.collect_database_metrics()
        self.collect_observatory_metrics()
        self.collect_ml_metrics()
        
        logger.info("Metrics collection cycle completed")
        
    def collection_loop(self):
        """Main collection loop"""
        logger.info("Starting metrics collection loop")
        
        while self.running:
            try:
                self.collect_all_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                time.sleep(self.collection_interval)
                
        logger.info("Metrics collection loop stopped")
        
    def start(self):
        """Start the metrics collector"""
        logger.info("Starting ContextBuilderAgent Metrics Collector")
        
        # Connect to databases
        self.connect_redis()
        self.connect_postgres()
        
        # Start Prometheus HTTP server
        start_http_server(self.prometheus_port)
        logger.info(f"Prometheus metrics server started on port {self.prometheus_port}")
        
        # Start collection thread
        self.running = True
        self.collection_thread = threading.Thread(target=self.collection_loop)
        self.collection_thread.daemon = True
        self.collection_thread.start()
        
        logger.info("Metrics collector started successfully")
        
    def stop(self):
        """Stop the metrics collector"""
        logger.info("Stopping metrics collector")
        self.running = False
        
        if self.collection_thread:
            self.collection_thread.join(timeout=10)
            
        if self.postgres_conn:
            self.postgres_conn.close()
            
        logger.info("Metrics collector stopped")


def main():
    """Main function"""
    collector = ContextBuilderMetricsCollector()
    
    try:
        collector.start()
        
        # Keep the main thread alive
        while True:
            time.sleep(60)
            logger.debug("Metrics collector running...")
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        collector.stop()


if __name__ == '__main__':
    main()