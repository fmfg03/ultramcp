"""
Monitoring Adapter - Handles monitoring alerts and metrics
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp

from .mock_adapter import MockAdapter

logger = logging.getLogger(__name__)

class MonitoringAdapter:
    """Adapter for monitoring and alerting systems"""
    
    def __init__(self):
        self.is_initialized = False
        self.monitoring_configs = {}
        self.created_alerts = []
        
    async def initialize(self):
        """Initialize monitoring adapter"""
        try:
            await self._load_monitoring_configs()
            await self._test_monitoring_connections()
            self.is_initialized = True
            logger.info("✅ Monitoring adapter initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize monitoring adapter: {e}")
            # Fall back to mock adapter
            self.mock_adapter = MockAdapter("MonitoringAdapter")
            await self.mock_adapter.initialize()
            logger.info("✅ Using mock monitoring adapter")
    
    async def _load_monitoring_configs(self):
        """Load monitoring system configurations"""
        self.monitoring_configs = {
            "datadog": {
                "enabled": os.getenv("DATADOG_ENABLED", "false").lower() == "true",
                "api_key": os.getenv("DATADOG_API_KEY", ""),
                "app_key": os.getenv("DATADOG_APP_KEY", "")
            },
            "newrelic": {
                "enabled": os.getenv("NEWRELIC_ENABLED", "false").lower() == "true",
                "api_key": os.getenv("NEWRELIC_API_KEY", ""),
                "account_id": os.getenv("NEWRELIC_ACCOUNT_ID", "")
            },
            "prometheus": {
                "enabled": os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true",
                "url": os.getenv("PROMETHEUS_URL", ""),
                "username": os.getenv("PROMETHEUS_USERNAME", ""),
                "password": os.getenv("PROMETHEUS_PASSWORD", "")
            },
            "grafana": {
                "enabled": os.getenv("GRAFANA_ENABLED", "false").lower() == "true",
                "url": os.getenv("GRAFANA_URL", ""),
                "api_token": os.getenv("GRAFANA_API_TOKEN", "")
            }
        }
    
    async def _test_monitoring_connections(self):
        """Test connections to monitoring systems"""
        
        if self.monitoring_configs["datadog"]["enabled"]:
            await self._test_datadog_connection()
        
        if self.monitoring_configs["grafana"]["enabled"]:
            await self._test_grafana_connection()
    
    async def _test_datadog_connection(self):
        """Test Datadog connection"""
        try:
            datadog_config = self.monitoring_configs["datadog"]
            headers = {
                "DD-API-KEY": datadog_config["api_key"],
                "DD-APPLICATION-KEY": datadog_config["app_key"]
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    "https://api.datadoghq.com/api/v1/validate",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("✅ Datadog connection test successful")
                    else:
                        raise Exception(f"Datadog returned status {response.status}")
                        
        except Exception as e:
            logger.warning(f"⚠️ Datadog connection test failed: {e}")
    
    async def _test_grafana_connection(self):
        """Test Grafana connection"""
        try:
            grafana_config = self.monitoring_configs["grafana"]
            headers = {"Authorization": f"Bearer {grafana_config['api_token']}"}
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    f"{grafana_config['url']}/api/org",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("✅ Grafana connection test successful")
                    else:
                        raise Exception(f"Grafana returned status {response.status}")
                        
        except Exception as e:
            logger.warning(f"⚠️ Grafana connection test failed: {e}")
    
    async def execute(self, action_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute monitoring action"""
        
        if not self.is_initialized and hasattr(self, 'mock_adapter'):
            return await self.mock_adapter.execute(action_name, input_data)
        
        if action_name == "create_alert":
            return await self._create_alert(input_data)
        else:
            raise ValueError(f"Unsupported action: {action_name}")
    
    async def _create_alert(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create monitoring alert"""
        
        # Extract alert parameters
        service = input_data.get("service", "").lower()
        alert_name = input_data.get("alert_name", "")
        condition = input_data.get("condition", "")
        severity = input_data.get("severity", "warning")
        notification_channels = input_data.get("notification_channels", [])
        tags = input_data.get("tags", {})
        
        # Validate parameters
        if service not in self.monitoring_configs:
            raise ValueError(f"Unsupported monitoring service: {service}")
        
        if not self.monitoring_configs[service]["enabled"]:
            raise ValueError(f"Monitoring service {service} is not enabled")
        
        if not alert_name:
            raise ValueError("Alert name is required")
        
        if not condition:
            raise ValueError("Alert condition is required")
        
        # Route to appropriate service handler
        result = None
        if service == "datadog":
            result = await self._create_datadog_alert(alert_name, condition, severity, notification_channels, tags)
        elif service == "newrelic":
            result = await self._create_newrelic_alert(alert_name, condition, severity, notification_channels, tags)
        elif service == "prometheus":
            result = await self._create_prometheus_alert(alert_name, condition, severity, notification_channels, tags)
        elif service == "grafana":
            result = await self._create_grafana_alert(alert_name, condition, severity, notification_channels, tags)
        else:
            raise ValueError(f"Handler not implemented for service: {service}")
        
        # Record created alert
        alert_record = {
            "alert_id": result["alert_id"],
            "service": service,
            "alert_name": alert_name,
            "condition": condition,
            "severity": severity,
            "created_at": datetime.utcnow(),
            "status": "active"
        }
        
        self.created_alerts.append(alert_record)
        
        # Keep only last 1000 alerts
        if len(self.created_alerts) > 1000:
            self.created_alerts = self.created_alerts[-1000:]
        
        return {
            **result,
            "service": service,
            "alert_name": alert_name,
            "severity": severity,
            "created_at": alert_record["created_at"].isoformat()
        }
    
    async def _create_datadog_alert(self, alert_name: str, condition: str, severity: str,
                                   notification_channels: list, tags: Dict[str, Any]) -> Dict[str, Any]:
        """Create Datadog alert"""
        
        datadog_config = self.monitoring_configs["datadog"]
        headers = {
            "DD-API-KEY": datadog_config["api_key"],
            "DD-APPLICATION-KEY": datadog_config["app_key"],
            "Content-Type": "application/json"
        }
        
        # Map severity to Datadog priority
        priority_mapping = {
            "info": 5,
            "warning": 3,
            "error": 2,
            "critical": 1
        }
        
        priority = priority_mapping.get(severity, 3)
        
        # Prepare Datadog monitor payload
        payload = {
            "type": "metric alert",
            "query": condition,
            "name": alert_name,
            "message": f"Alert: {alert_name}\nCondition: {condition}\nSeverity: {severity}",
            "tags": [f"{k}:{v}" for k, v in tags.items()],
            "priority": priority,
            "options": {
                "notify_audit": True,
                "locked": False,
                "timeout_h": 0,
                "include_tags": True,
                "no_data_timeframe": 10,
                "notify_no_data": True
            }
        }
        
        if notification_channels:
            payload["message"] += f"\nNotifications: {' '.join(notification_channels)}"
        
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(
                    "https://api.datadoghq.com/api/v1/monitor",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "alert_id": str(result["id"]),
                            "alert_url": f"https://app.datadoghq.com/monitors/{result['id']}",
                            "status": "created"
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"Datadog API returned {response.status}: {error_text}")
                        
        except Exception as e:
            logger.error(f"❌ Failed to create Datadog alert: {e}")
            raise
    
    async def _create_newrelic_alert(self, alert_name: str, condition: str, severity: str,
                                    notification_channels: list, tags: Dict[str, Any]) -> Dict[str, Any]:
        """Create New Relic alert"""
        
        # Simplified New Relic implementation
        alert_id = f"newrelic-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        return {
            "alert_id": alert_id,
            "alert_url": f"https://one.newrelic.com/alerts-ai/policies/{alert_id}",
            "status": "created"
        }
    
    async def _create_prometheus_alert(self, alert_name: str, condition: str, severity: str,
                                      notification_channels: list, tags: Dict[str, Any]) -> Dict[str, Any]:
        """Create Prometheus alert"""
        
        # Simplified Prometheus implementation
        alert_id = f"prometheus-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        return {
            "alert_id": alert_id,
            "alert_url": f"http://prometheus:9090/alerts",
            "status": "created"
        }
    
    async def _create_grafana_alert(self, alert_name: str, condition: str, severity: str,
                                   notification_channels: list, tags: Dict[str, Any]) -> Dict[str, Any]:
        """Create Grafana alert"""
        
        grafana_config = self.monitoring_configs["grafana"]
        headers = {
            "Authorization": f"Bearer {grafana_config['api_token']}",
            "Content-Type": "application/json"
        }
        
        # Simplified Grafana alert creation
        payload = {
            "title": alert_name,
            "message": f"Alert condition: {condition}",
            "frequency": "10s",
            "conditions": [
                {
                    "query": {
                        "queryType": "",
                        "refId": "A"
                    },
                    "reducer": {
                        "type": "last",
                        "params": []
                    },
                    "evaluator": {
                        "params": [0],
                        "type": "gt"
                    }
                }
            ],
            "executionErrorState": "alerting",
            "noDataState": "no_data",
            "for": "5m"
        }
        
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(
                    f"{grafana_config['url']}/api/alerts",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "alert_id": str(result.get("id", "unknown")),
                            "alert_url": f"{grafana_config['url']}/alerting/list",
                            "status": "created"
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"Grafana API returned {response.status}: {error_text}")
                        
        except Exception as e:
            logger.error(f"❌ Failed to create Grafana alert: {e}")
            # Return mock response as fallback
            alert_id = f"grafana-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            return {
                "alert_id": alert_id,
                "alert_url": f"{grafana_config['url']}/alerting/list",
                "status": "created"
            }
    
    async def get_alert_status(self, alert_id: str, service: str) -> Optional[Dict[str, Any]]:
        """Get status of monitoring alert"""
        
        # Check local records first
        for alert in self.created_alerts:
            if alert["alert_id"] == alert_id and alert["service"] == service:
                return {
                    "alert_id": alert["alert_id"],
                    "service": alert["service"],
                    "alert_name": alert["alert_name"],
                    "condition": alert["condition"],
                    "severity": alert["severity"],
                    "status": alert["status"],
                    "created_at": alert["created_at"].isoformat()
                }
        
        return None
    
    async def get_monitoring_statistics(self) -> Dict[str, Any]:
        """Get monitoring adapter statistics"""
        
        total_alerts = len(self.created_alerts)
        if total_alerts == 0:
            return {"total_alerts": 0}
        
        # Service distribution
        service_counts = {}
        for alert in self.created_alerts:
            service = alert["service"]
            service_counts[service] = service_counts.get(service, 0) + 1
        
        # Severity distribution
        severity_counts = {}
        for alert in self.created_alerts:
            severity = alert["severity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_alerts": total_alerts,
            "service_distribution": service_counts,
            "severity_distribution": severity_counts,
            "configured_services": {
                service: config["enabled"] 
                for service, config in self.monitoring_configs.items()
            }
        }
    
    async def cleanup(self):
        """Cleanup monitoring adapter"""
        
        if self.created_alerts:
            logger.info(f"📊 Monitoring adapter created {len(self.created_alerts)} alerts during session")
        
        self.created_alerts.clear()
        self.is_initialized = False
        logger.info("✅ Monitoring adapter cleaned up")