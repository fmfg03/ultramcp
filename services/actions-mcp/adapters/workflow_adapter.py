"""
Workflow Adapter - Handles external workflow and pipeline triggers
"""

import asyncio
import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
import aiohttp

from .mock_adapter import MockAdapter

logger = logging.getLogger(__name__)

class WorkflowAdapter:
    """Adapter for external workflow and pipeline management"""
    
    def __init__(self):
        self.is_initialized = False
        self.workflow_config = {}
        self.active_workflows = {}
        self.workflow_history = []
        
    async def initialize(self):
        """Initialize workflow adapter"""
        try:
            await self._load_workflow_config()
            await self._test_workflow_connections()
            self.is_initialized = True
            logger.info("✅ Workflow adapter initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize workflow adapter: {e}")
            # Fall back to mock adapter
            self.mock_adapter = MockAdapter("WorkflowAdapter")
            await self.mock_adapter.initialize()
            logger.info("✅ Using mock workflow adapter")
    
    async def _load_workflow_config(self):
        """Load workflow system configurations"""
        self.workflow_config = {
            "jenkins": {
                "enabled": os.getenv("JENKINS_ENABLED", "false").lower() == "true",
                "url": os.getenv("JENKINS_URL", ""),
                "username": os.getenv("JENKINS_USERNAME", ""),
                "api_token": os.getenv("JENKINS_API_TOKEN", "")
            },
            "github_actions": {
                "enabled": os.getenv("GITHUB_ACTIONS_ENABLED", "false").lower() == "true",
                "token": os.getenv("GITHUB_TOKEN", ""),
                "default_repo": os.getenv("GITHUB_DEFAULT_REPO", "")
            },
            "gitlab_ci": {
                "enabled": os.getenv("GITLAB_CI_ENABLED", "false").lower() == "true",
                "url": os.getenv("GITLAB_URL", ""),
                "token": os.getenv("GITLAB_TOKEN", ""),
                "project_id": os.getenv("GITLAB_PROJECT_ID", "")
            },
            "custom_webhooks": {
                "enabled": os.getenv("CUSTOM_WEBHOOKS_ENABLED", "false").lower() == "true",
                "deployment_webhook": os.getenv("DEPLOYMENT_WEBHOOK_URL", ""),
                "testing_webhook": os.getenv("TESTING_WEBHOOK_URL", ""),
                "security_webhook": os.getenv("SECURITY_WEBHOOK_URL", "")
            }
        }
    
    async def _test_workflow_connections(self):
        """Test connections to workflow systems"""
        
        if self.workflow_config["jenkins"]["enabled"]:
            await self._test_jenkins_connection()
        
        if self.workflow_config["github_actions"]["enabled"]:
            await self._test_github_actions_connection()
        
        if self.workflow_config["gitlab_ci"]["enabled"]:
            await self._test_gitlab_ci_connection()
    
    async def _test_jenkins_connection(self):
        """Test Jenkins connection"""
        try:
            jenkins_config = self.workflow_config["jenkins"]
            auth = aiohttp.BasicAuth(jenkins_config["username"], jenkins_config["api_token"])
            
            async with aiohttp.ClientSession(auth=auth) as session:
                async with session.get(
                    f"{jenkins_config['url']}/api/json",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("✅ Jenkins connection test successful")
                    else:
                        raise Exception(f"Jenkins returned status {response.status}")
                        
        except Exception as e:
            logger.warning(f"⚠️ Jenkins connection test failed: {e}")
    
    async def _test_github_actions_connection(self):
        """Test GitHub Actions connection"""
        try:
            github_config = self.workflow_config["github_actions"]
            headers = {
                "Authorization": f"token {github_config['token']}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    "https://api.github.com/user",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("✅ GitHub Actions connection test successful")
                    else:
                        raise Exception(f"GitHub API returned status {response.status}")
                        
        except Exception as e:
            logger.warning(f"⚠️ GitHub Actions connection test failed: {e}")
    
    async def _test_gitlab_ci_connection(self):
        """Test GitLab CI connection"""
        try:
            gitlab_config = self.workflow_config["gitlab_ci"]
            headers = {"PRIVATE-TOKEN": gitlab_config["token"]}
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    f"{gitlab_config['url']}/api/v4/user",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("✅ GitLab CI connection test successful")
                    else:
                        raise Exception(f"GitLab API returned status {response.status}")
                        
        except Exception as e:
            logger.warning(f"⚠️ GitLab CI connection test failed: {e}")
    
    async def execute(self, action_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow action"""
        
        if not self.is_initialized and hasattr(self, 'mock_adapter'):
            return await self.mock_adapter.execute(action_name, input_data)
        
        if action_name == "trigger_workflow":
            return await self._trigger_workflow(input_data)
        elif action_name == "stop_workflow":
            return await self._stop_workflow(input_data)
        else:
            raise ValueError(f"Unsupported action: {action_name}")
    
    async def _trigger_workflow(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger external workflow"""
        
        # Extract workflow parameters
        workflow_type = input_data.get("workflow_type", "custom")
        environment = input_data.get("environment", "development")
        parameters = input_data.get("parameters", {})
        trigger_conditions = input_data.get("trigger_conditions", {})
        timeout = input_data.get("timeout", 30)
        priority = input_data.get("priority", "normal")
        
        # Generate workflow ID
        workflow_id = f"WF-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"
        
        # Check trigger conditions
        if trigger_conditions:
            conditions_met = await self._check_trigger_conditions(trigger_conditions)
            if not conditions_met:
                raise Exception("Trigger conditions not met for workflow execution")
        
        # Select workflow system based on type and configuration
        workflow_system = await self._select_workflow_system(workflow_type, environment)
        
        # Trigger workflow based on system
        result = None
        if workflow_system == "jenkins":
            result = await self._trigger_jenkins_workflow(workflow_id, workflow_type, environment, parameters)
        elif workflow_system == "github_actions":
            result = await self._trigger_github_actions_workflow(workflow_id, workflow_type, environment, parameters)
        elif workflow_system == "gitlab_ci":
            result = await self._trigger_gitlab_ci_workflow(workflow_id, workflow_type, environment, parameters)
        elif workflow_system == "webhook":
            result = await self._trigger_webhook_workflow(workflow_id, workflow_type, environment, parameters)
        else:
            # Simulate workflow execution
            result = await self._simulate_workflow_execution(workflow_id, workflow_type, environment, parameters)
        
        # Record active workflow
        workflow_record = {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type,
            "environment": environment,
            "system": workflow_system,
            "parameters": parameters,
            "status": "running",
            "started_at": datetime.utcnow(),
            "timeout_at": datetime.utcnow() + timedelta(minutes=timeout),
            "priority": priority,
            "external_id": result.get("external_id"),
            "monitoring_url": result.get("monitoring_url")
        }
        
        self.active_workflows[workflow_id] = workflow_record
        
        return {
            "workflow_id": workflow_id,
            "status": "running",
            "estimated_duration": result.get("estimated_duration", timeout),
            "monitoring_url": result.get("monitoring_url", f"https://workflows.ultramcp.com/monitor/{workflow_id}"),
            "workflow_type": workflow_type,
            "environment": environment,
            "system": workflow_system,
            "started_at": workflow_record["started_at"].isoformat()
        }
    
    async def _stop_workflow(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Stop running workflow"""
        
        workflow_id = input_data.get("workflow_id", "")
        reason = input_data.get("reason", "User request")
        force = input_data.get("force", False)
        
        if not workflow_id:
            raise ValueError("Workflow ID is required")
        
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found or not active")
        
        workflow = self.active_workflows[workflow_id]
        
        # Stop workflow based on system
        stop_result = None
        if workflow["system"] == "jenkins":
            stop_result = await self._stop_jenkins_workflow(workflow, force)
        elif workflow["system"] == "github_actions":
            stop_result = await self._stop_github_actions_workflow(workflow, force)
        elif workflow["system"] == "gitlab_ci":
            stop_result = await self._stop_gitlab_ci_workflow(workflow, force)
        elif workflow["system"] == "webhook":
            stop_result = await self._stop_webhook_workflow(workflow, force)
        else:
            # Simulate workflow stopping
            stop_result = {"status": "stopped", "stop_time": datetime.utcnow()}
        
        # Update workflow record
        workflow["status"] = "stopped"
        workflow["stopped_at"] = datetime.utcnow()
        workflow["stop_reason"] = reason
        workflow["force_stopped"] = force
        
        # Move to history
        self.workflow_history.append(workflow)
        del self.active_workflows[workflow_id]
        
        return {
            "workflow_id": workflow_id,
            "status": "stopped",
            "stop_time": workflow["stopped_at"].isoformat(),
            "reason": reason,
            "force_stopped": force,
            "duration": (workflow["stopped_at"] - workflow["started_at"]).total_seconds()
        }
    
    async def _check_trigger_conditions(self, conditions: Dict[str, Any]) -> bool:
        """Check if trigger conditions are met"""
        
        # Example conditions checking
        for condition, expected_value in conditions.items():
            if condition == "tests_passed":
                # In real implementation, check test results
                if not expected_value:
                    return False
            elif condition == "security_scan":
                # In real implementation, check security scan results
                if expected_value == "clean":
                    # Simulate security check
                    pass
            elif condition == "approval_status":
                # In real implementation, check approval status
                if expected_value == "approved":
                    # Simulate approval check
                    pass
        
        return True
    
    async def _select_workflow_system(self, workflow_type: str, environment: str) -> str:
        """Select appropriate workflow system"""
        
        # Priority order based on configuration and workflow type
        if workflow_type == "deployment":
            if self.workflow_config["jenkins"]["enabled"]:
                return "jenkins"
            elif self.workflow_config["github_actions"]["enabled"]:
                return "github_actions"
            elif self.workflow_config["custom_webhooks"]["enabled"]:
                return "webhook"
        
        elif workflow_type == "testing":
            if self.workflow_config["github_actions"]["enabled"]:
                return "github_actions"
            elif self.workflow_config["gitlab_ci"]["enabled"]:
                return "gitlab_ci"
            elif self.workflow_config["jenkins"]["enabled"]:
                return "jenkins"
        
        elif workflow_type == "security_scan":
            if self.workflow_config["custom_webhooks"]["enabled"]:
                return "webhook"
            elif self.workflow_config["jenkins"]["enabled"]:
                return "jenkins"
        
        # Default fallback
        if self.workflow_config["jenkins"]["enabled"]:
            return "jenkins"
        elif self.workflow_config["github_actions"]["enabled"]:
            return "github_actions"
        elif self.workflow_config["gitlab_ci"]["enabled"]:
            return "gitlab_ci"
        else:
            return "simulation"
    
    async def _trigger_jenkins_workflow(self, workflow_id: str, workflow_type: str, 
                                       environment: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger Jenkins workflow"""
        
        jenkins_config = self.workflow_config["jenkins"]
        auth = aiohttp.BasicAuth(jenkins_config["username"], jenkins_config["api_token"])
        
        # Map workflow type to Jenkins job
        job_mapping = {
            "deployment": f"deploy-{environment}",
            "testing": f"test-{environment}",
            "security_scan": "security-scan",
            "backup": "backup-job",
            "custom": "custom-workflow"
        }
        
        job_name = job_mapping.get(workflow_type, "custom-workflow")
        
        # Prepare Jenkins parameters
        jenkins_params = {
            "WORKFLOW_ID": workflow_id,
            "ENVIRONMENT": environment,
            **parameters
        }
        
        try:
            async with aiohttp.ClientSession(auth=auth) as session:
                # Trigger Jenkins job
                url = f"{jenkins_config['url']}/job/{job_name}/buildWithParameters"
                
                async with session.post(
                    url,
                    data=jenkins_params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status not in [200, 201]:
                        raise Exception(f"Jenkins returned status {response.status}")
                    
                    # Get build number from queue
                    queue_id = response.headers.get("Location", "").split("/")[-2]
                    
                    return {
                        "external_id": queue_id,
                        "monitoring_url": f"{jenkins_config['url']}/job/{job_name}",
                        "estimated_duration": 15
                    }
                    
        except Exception as e:
            logger.error(f"❌ Failed to trigger Jenkins workflow: {e}")
            raise
    
    async def _trigger_github_actions_workflow(self, workflow_id: str, workflow_type: str,
                                             environment: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger GitHub Actions workflow"""
        
        github_config = self.workflow_config["github_actions"]
        headers = {
            "Authorization": f"token {github_config['token']}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Map workflow type to GitHub Actions workflow file
        workflow_mapping = {
            "deployment": "deploy.yml",
            "testing": "test.yml",
            "security_scan": "security.yml",
            "backup": "backup.yml",
            "custom": "custom.yml"
        }
        
        workflow_file = workflow_mapping.get(workflow_type, "custom.yml")
        repo = parameters.get("repository", github_config["default_repo"])
        
        # Prepare workflow inputs
        inputs = {
            "workflow_id": workflow_id,
            "environment": environment,
            **{k: str(v) for k, v in parameters.items() if k != "repository"}
        }
        
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_file}/dispatches"
                
                payload = {
                    "ref": "main",
                    "inputs": inputs
                }
                
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 204:
                        error_text = await response.text()
                        raise Exception(f"GitHub Actions returned {response.status}: {error_text}")
                    
                    return {
                        "external_id": f"{repo}/{workflow_file}",
                        "monitoring_url": f"https://github.com/{repo}/actions",
                        "estimated_duration": 10
                    }
                    
        except Exception as e:
            logger.error(f"❌ Failed to trigger GitHub Actions workflow: {e}")
            raise
    
    async def _trigger_gitlab_ci_workflow(self, workflow_id: str, workflow_type: str,
                                         environment: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger GitLab CI workflow"""
        
        gitlab_config = self.workflow_config["gitlab_ci"]
        headers = {"PRIVATE-TOKEN": gitlab_config["token"]}
        
        # Prepare pipeline variables
        variables = [
            {"key": "WORKFLOW_ID", "value": workflow_id},
            {"key": "WORKFLOW_TYPE", "value": workflow_type},
            {"key": "ENVIRONMENT", "value": environment}
        ]
        
        for key, value in parameters.items():
            variables.append({"key": key.upper(), "value": str(value)})
        
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                url = f"{gitlab_config['url']}/api/v4/projects/{gitlab_config['project_id']}/pipeline"
                
                payload = {
                    "ref": "main",
                    "variables": variables
                }
                
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 201:
                        error_text = await response.text()
                        raise Exception(f"GitLab CI returned {response.status}: {error_text}")
                    
                    result = await response.json()
                    pipeline_id = result.get("id")
                    
                    return {
                        "external_id": str(pipeline_id),
                        "monitoring_url": f"{gitlab_config['url']}/pipelines/{pipeline_id}",
                        "estimated_duration": 12
                    }
                    
        except Exception as e:
            logger.error(f"❌ Failed to trigger GitLab CI workflow: {e}")
            raise
    
    async def _trigger_webhook_workflow(self, workflow_id: str, workflow_type: str,
                                       environment: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger workflow via webhook"""
        
        webhook_config = self.workflow_config["custom_webhooks"]
        
        # Select webhook URL based on workflow type
        webhook_urls = {
            "deployment": webhook_config.get("deployment_webhook"),
            "testing": webhook_config.get("testing_webhook"),
            "security_scan": webhook_config.get("security_webhook")
        }
        
        webhook_url = webhook_urls.get(workflow_type, webhook_config.get("deployment_webhook"))
        
        if not webhook_url:
            raise Exception(f"No webhook configured for workflow type: {workflow_type}")
        
        # Prepare webhook payload
        payload = {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type,
            "environment": environment,
            "parameters": parameters,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status not in [200, 201, 202]:
                        error_text = await response.text()
                        raise Exception(f"Webhook returned {response.status}: {error_text}")
                    
                    return {
                        "external_id": workflow_id,
                        "monitoring_url": f"https://workflows.ultramcp.com/monitor/{workflow_id}",
                        "estimated_duration": 20
                    }
                    
        except Exception as e:
            logger.error(f"❌ Failed to trigger webhook workflow: {e}")
            raise
    
    async def _simulate_workflow_execution(self, workflow_id: str, workflow_type: str,
                                          environment: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate workflow execution for development/testing"""
        
        # Simulate different execution times based on workflow type
        duration_mapping = {
            "deployment": 15,
            "testing": 10,
            "security_scan": 30,
            "backup": 20,
            "custom": 5
        }
        
        estimated_duration = duration_mapping.get(workflow_type, 10)
        
        return {
            "external_id": workflow_id,
            "monitoring_url": f"https://workflows.ultramcp.com/monitor/{workflow_id}",
            "estimated_duration": estimated_duration
        }
    
    async def _stop_jenkins_workflow(self, workflow: Dict[str, Any], force: bool) -> Dict[str, Any]:
        """Stop Jenkins workflow"""
        # Implementation would depend on Jenkins API for stopping builds
        return {"status": "stopped", "stop_time": datetime.utcnow()}
    
    async def _stop_github_actions_workflow(self, workflow: Dict[str, Any], force: bool) -> Dict[str, Any]:
        """Stop GitHub Actions workflow"""
        # Implementation would use GitHub API to cancel workflow runs
        return {"status": "stopped", "stop_time": datetime.utcnow()}
    
    async def _stop_gitlab_ci_workflow(self, workflow: Dict[str, Any], force: bool) -> Dict[str, Any]:
        """Stop GitLab CI workflow"""
        # Implementation would use GitLab API to cancel pipelines
        return {"status": "stopped", "stop_time": datetime.utcnow()}
    
    async def _stop_webhook_workflow(self, workflow: Dict[str, Any], force: bool) -> Dict[str, Any]:
        """Stop webhook workflow"""
        # Implementation would send stop signal to webhook endpoint
        return {"status": "stopped", "stop_time": datetime.utcnow()}
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of workflow"""
        
        # Check active workflows
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            return {
                "workflow_id": workflow_id,
                "status": workflow["status"],
                "workflow_type": workflow["workflow_type"],
                "environment": workflow["environment"],
                "started_at": workflow["started_at"].isoformat(),
                "monitoring_url": workflow.get("monitoring_url")
            }
        
        # Check history
        for workflow in self.workflow_history:
            if workflow["workflow_id"] == workflow_id:
                return {
                    "workflow_id": workflow_id,
                    "status": workflow["status"],
                    "workflow_type": workflow["workflow_type"],
                    "environment": workflow["environment"],
                    "started_at": workflow["started_at"].isoformat(),
                    "stopped_at": workflow.get("stopped_at", "").isoformat() if workflow.get("stopped_at") else None,
                    "duration": (workflow.get("stopped_at", datetime.utcnow()) - workflow["started_at"]).total_seconds()
                }
        
        return None
    
    async def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get workflow execution statistics"""
        
        total_workflows = len(self.workflow_history) + len(self.active_workflows)
        active_count = len(self.active_workflows)
        completed_count = len([w for w in self.workflow_history if w["status"] == "completed"])
        failed_count = len([w for w in self.workflow_history if w["status"] == "failed"])
        stopped_count = len([w for w in self.workflow_history if w["status"] == "stopped"])
        
        # Type statistics
        type_counts = {}
        for workflow in self.workflow_history + list(self.active_workflows.values()):
            wf_type = workflow["workflow_type"]
            type_counts[wf_type] = type_counts.get(wf_type, 0) + 1
        
        # System statistics
        system_counts = {}
        for workflow in self.workflow_history + list(self.active_workflows.values()):
            system = workflow.get("system", "unknown")
            system_counts[system] = system_counts.get(system, 0) + 1
        
        return {
            "total_workflows": total_workflows,
            "active_workflows": active_count,
            "completed_workflows": completed_count,
            "failed_workflows": failed_count,
            "stopped_workflows": stopped_count,
            "success_rate": (completed_count / total_workflows * 100) if total_workflows > 0 else 0,
            "workflow_types": type_counts,
            "workflow_systems": system_counts,
            "configured_systems": {
                "jenkins": self.workflow_config["jenkins"]["enabled"],
                "github_actions": self.workflow_config["github_actions"]["enabled"],
                "gitlab_ci": self.workflow_config["gitlab_ci"]["enabled"],
                "webhooks": self.workflow_config["custom_webhooks"]["enabled"]
            }
        }
    
    async def cleanup(self):
        """Cleanup workflow adapter"""
        
        # Stop all active workflows
        for workflow_id in list(self.active_workflows.keys()):
            try:
                await self._stop_workflow({
                    "workflow_id": workflow_id,
                    "reason": "Service shutdown",
                    "force": True
                })
            except Exception as e:
                logger.warning(f"⚠️ Failed to stop workflow {workflow_id} during cleanup: {e}")
        
        if self.workflow_history:
            logger.info(f"⚙️ Workflow adapter executed {len(self.workflow_history)} workflows during session")
        
        self.active_workflows.clear()
        self.workflow_history.clear()
        self.is_initialized = False
        logger.info("✅ Workflow adapter cleaned up")