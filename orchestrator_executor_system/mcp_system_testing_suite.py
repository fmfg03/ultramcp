#!/usr/bin/env python3
"""
Comprehensive Testing Suite for MCP Orchestrator-Executor System
Suite completa de testing y validación para el sistema Manus-SAM
"""

import asyncio
import json
import time
import uuid
import pytest
import aiohttp
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import os

# Importar módulos del sistema
from mcp_payload_schemas import (
    PayloadValidator, PayloadType,
    create_task_execution_payload,
    create_notification_payload,
    create_agent_end_task_payload
)
from sam_manus_notification_protocol import (
    NotificationManager, SAMNotificationSender,
    NotificationType, TaskStatus
)
from manus_webhook_receiver import ManusWebhookReceiver
from complete_webhook_agent_end_task_system import (
    WebhookManager, AgentEndTaskManager,
    WebhookEventType, AgentEndTaskReason
)

class TestEnvironment:
    """
    Entorno de testing para el sistema MCP
    """
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test.db")
        self.mock_servers = {}
        self.test_data = {}
        
    async def setup(self):
        """Configurar entorno de testing"""
        # Configurar logging para testing
        logging.basicConfig(level=logging.DEBUG)
        
        # Inicializar componentes con base de datos temporal
        self.notification_manager = NotificationManager(self.test_db_path)
        self.webhook_manager = WebhookManager(self.test_db_path)
        self.webhook_receiver = ManusWebhookReceiver(self.test_db_path)
        self.agent_end_task_manager = AgentEndTaskManager(self.webhook_manager)
        
        # Configurar datos de prueba
        self.test_data = {
            "task_id": "test_task_001",
            "agent_id": "test_sam_001",
            "webhook_id": "test_webhook_001",
            "endpoint_url": "http://sam.chat:8999/webhook/test"
        }
    
    async def teardown(self):
        """Limpiar entorno de testing"""
        # Cerrar conexiones y limpiar archivos temporales
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

class PayloadValidationTests:
    """
    Tests para validación de payloads
    """
    
    def __init__(self, test_env: TestEnvironment):
        self.test_env = test_env
        self.validator = PayloadValidator()
    
    def test_task_execution_payload_validation(self):
        """Test validación de payload de ejecución de tarea"""
        # Payload válido
        valid_payload = create_task_execution_payload(
            task_id="test_001",
            task_type="code_generation",
            description="Generate a Python function",
            orchestrator_agent_id="manus_001",
            priority="normal"
        )
        
        result = self.validator.validate_payload(valid_payload, PayloadType.TASK_EXECUTION)
        assert result["valid"] == True
        
        # Payload inválido - falta campo requerido
        invalid_payload = valid_payload.copy()
        del invalid_payload["task_id"]
        
        result = self.validator.validate_payload(invalid_payload, PayloadType.TASK_EXECUTION)
        assert result["valid"] == False
        assert "task_id" in result["error"]
        
        # Payload inválido - tipo de tarea incorrecto
        invalid_payload = valid_payload.copy()
        invalid_payload["task_type"] = "invalid_type"
        
        result = self.validator.validate_payload(invalid_payload, PayloadType.TASK_EXECUTION)
        assert result["valid"] == False
        
        print("✅ Task execution payload validation tests passed")
    
    def test_notification_payload_validation(self):
        """Test validación de payload de notificación"""
        # Payload válido
        valid_payload = create_notification_payload(
            notification_type="task_completed",
            task_id="test_001",
            agent_id="sam_001",
            status="completed",
            data={
                "result": {"output": "success"},
                "execution_summary": "Task completed successfully"
            }
        )
        
        result = self.validator.validate_payload(valid_payload, PayloadType.NOTIFICATION)
        assert result["valid"] == True
        
        # Payload inválido - tipo de notificación incorrecto
        invalid_payload = valid_payload.copy()
        invalid_payload["notification_type"] = "invalid_notification"
        
        result = self.validator.validate_payload(invalid_payload, PayloadType.NOTIFICATION)
        assert result["valid"] == False
        
        print("✅ Notification payload validation tests passed")
    
    def test_agent_end_task_payload_validation(self):
        """Test validación de payload agent_end_task"""
        # Payload válido
        valid_payload = create_agent_end_task_payload(
            task_id="test_001",
            agent_id="sam_001",
            completion_status="success",
            result_data={"output": "Task completed"},
            execution_metrics={
                "duration_seconds": 45.2,
                "tokens_consumed": 1250
            }
        )
        
        result = self.validator.validate_payload(valid_payload, PayloadType.AGENT_END_TASK)
        assert result["valid"] == True
        
        # Payload inválido - estado de completación incorrecto
        invalid_payload = valid_payload.copy()
        invalid_payload["completion_status"] = "invalid_status"
        
        result = self.validator.validate_payload(invalid_payload, PayloadType.AGENT_END_TASK)
        assert result["valid"] == False
        
        print("✅ Agent end task payload validation tests passed")

class NotificationSystemTests:
    """
    Tests para sistema de notificaciones
    """
    
    def __init__(self, test_env: TestEnvironment):
        self.test_env = test_env
    
    async def test_notification_sending(self):
        """Test envío de notificaciones"""
        # Configurar webhook de prueba
        webhook_config = {
            "url": self.test_env.test_data["endpoint_url"],
            "secret": "test_secret",
            "timeout": 30,
            "active": True
        }
        
        self.test_env.notification_manager.register_webhook(
            self.test_env.test_data["webhook_id"],
            webhook_config
        )
        
        # Crear notificación de prueba
        sam_notifier = SAMNotificationSender(self.test_env.test_data["agent_id"])
        
        # Test notificación de inicio de tarea
        sam_notifier.notify_task_started(
            self.test_env.test_data["task_id"],
            {
                "task_type": "code_generation",
                "description": "Test task",
                "complexity": "medium"
            }
        )
        
        # Esperar procesamiento
        await asyncio.sleep(1)
        
        # Verificar que la notificación fue enviada
        status = self.test_env.notification_manager.get_notification_status(
            self.test_env.test_data["task_id"]
        )
        
        assert status is not None
        print("✅ Notification sending test passed")
    
    async def test_notification_retry_mechanism(self):
        """Test mecanismo de reintentos de notificaciones"""
        # Configurar webhook con URL inválida para forzar fallo
        webhook_config = {
            "url": "http://invalid-url:9999/webhook",
            "secret": "test_secret",
            "timeout": 5,
            "active": True
        }
        
        self.test_env.notification_manager.register_webhook(
            "test_webhook_fail",
            webhook_config
        )
        
        # Enviar notificación que debería fallar
        sam_notifier = SAMNotificationSender(self.test_env.test_data["agent_id"])
        
        sam_notifier.notify_task_failed(
            self.test_env.test_data["task_id"],
            {
                "error_type": "test_error",
                "error_message": "Test error message"
            }
        )
        
        # Esperar intentos de reintento
        await asyncio.sleep(5)
        
        # Verificar que se registraron intentos fallidos
        stats = self.test_env.notification_manager.get_delivery_stats(1)
        assert stats["pending_notifications"] > 0
        
        print("✅ Notification retry mechanism test passed")

class WebhookSystemTests:
    """
    Tests para sistema de webhooks
    """
    
    def __init__(self, test_env: TestEnvironment):
        self.test_env = test_env
    
    async def test_webhook_registration(self):
        """Test registro de webhooks"""
        # Registrar webhook
        success = self.test_env.webhook_manager.register_webhook(
            self.test_env.test_data["webhook_id"],
            self.test_env.test_data["endpoint_url"],
            ["task_lifecycle", "agent_status"],
            "test_secret"
        )
        
        assert success == True
        
        # Verificar que el webhook está registrado
        stats = self.test_env.webhook_manager.get_webhook_stats(
            self.test_env.test_data["webhook_id"]
        )
        
        assert stats is not None
        assert stats["endpoint_url"] == self.test_env.test_data["endpoint_url"]
        
        print("✅ Webhook registration test passed")
    
    async def test_webhook_delivery(self):
        """Test entrega de webhooks"""
        # Registrar webhook
        self.test_env.webhook_manager.register_webhook(
            self.test_env.test_data["webhook_id"],
            self.test_env.test_data["endpoint_url"],
            ["task_lifecycle"],
            "test_secret"
        )
        
        # Crear payload de prueba
        test_payload = {
            "event_type": "task_completed",
            "task_id": self.test_env.test_data["task_id"],
            "timestamp": datetime.now().isoformat(),
            "data": {"result": "success"}
        }
        
        # Enviar webhook
        await self.test_env.webhook_manager.send_webhook(
            WebhookEventType.TASK_LIFECYCLE,
            test_payload
        )
        
        # Esperar procesamiento
        await asyncio.sleep(2)
        
        # Verificar estadísticas de entrega
        stats = self.test_env.webhook_manager.get_webhook_stats(
            self.test_env.test_data["webhook_id"]
        )
        
        assert stats["total_deliveries"] > 0
        
        print("✅ Webhook delivery test passed")

class AgentEndTaskTests:
    """
    Tests para mecanismo agent_end_task
    """
    
    def __init__(self, test_env: TestEnvironment):
        self.test_env = test_env
    
    async def test_successful_task_completion(self):
        """Test finalización exitosa de tarea"""
        # Finalizar tarea con éxito
        result = await self.test_env.agent_end_task_manager.end_task(
            task_id=self.test_env.test_data["task_id"],
            agent_id=self.test_env.test_data["agent_id"],
            reason=AgentEndTaskReason.SUCCESS,
            execution_summary={
                "output": "Task completed successfully",
                "files_created": ["output.py"],
                "quality_score": 0.95
            },
            cleanup_actions=["remove_temp_files", "close_connections"],
            next_steps=["notify_user", "archive_results"],
            metadata={
                "execution_time": 45.2,
                "tokens_used": 1250,
                "cost": 0.025
            }
        )
        
        assert result["status"] == "task_ended"
        assert result["reason"] == "success"
        assert result["cleanup_results"]["cleanup_successful"] == True
        
        print("✅ Successful task completion test passed")
    
    async def test_failed_task_completion(self):
        """Test finalización fallida de tarea"""
        # Finalizar tarea con fallo
        result = await self.test_env.agent_end_task_manager.end_task(
            task_id=self.test_env.test_data["task_id"] + "_fail",
            agent_id=self.test_env.test_data["agent_id"],
            reason=AgentEndTaskReason.FAILURE,
            execution_summary={
                "error": "Task failed due to timeout",
                "partial_results": {"progress": 0.3}
            },
            cleanup_actions=["cleanup_partial_results"],
            next_steps=["escalate_to_human", "retry_with_different_approach"],
            metadata={
                "execution_time": 120.0,
                "error_code": "TIMEOUT_ERROR"
            }
        )
        
        assert result["status"] == "task_ended"
        assert result["reason"] == "failure"
        
        print("✅ Failed task completion test passed")

class IntegrationTests:
    """
    Tests de integración end-to-end
    """
    
    def __init__(self, test_env: TestEnvironment):
        self.test_env = test_env
    
    async def test_complete_task_lifecycle(self):
        """Test ciclo completo de vida de tarea"""
        task_id = f"integration_test_{int(time.time())}"
        
        # 1. Registrar webhook para recibir notificaciones
        self.test_env.webhook_manager.register_webhook(
            "integration_webhook",
            "http://sam.chat:8999/webhook/integration",
            ["task_lifecycle"],
            "integration_secret"
        )
        
        # 2. Crear y validar payload de tarea
        task_payload = create_task_execution_payload(
            task_id=task_id,
            task_type="code_generation",
            description="Integration test task",
            orchestrator_agent_id="manus_integration",
            priority="normal"
        )
        
        validator = PayloadValidator()
        validation_result = validator.validate_payload(task_payload, PayloadType.TASK_EXECUTION)
        assert validation_result["valid"] == True
        
        # 3. Simular inicio de tarea
        sam_notifier = SAMNotificationSender("sam_integration")
        sam_notifier.notify_task_started(task_id, {
            "task_type": "code_generation",
            "description": "Integration test task",
            "estimated_duration": 60
        })
        
        # 4. Simular progreso de tarea
        sam_notifier.notify_task_progress(task_id, {
            "progress": 50,
            "current_step": "Generating code",
            "steps_completed": 2,
            "total_steps": 4
        })
        
        # 5. Finalizar tarea
        result = await self.test_env.agent_end_task_manager.end_task(
            task_id=task_id,
            agent_id="sam_integration",
            reason=AgentEndTaskReason.SUCCESS,
            execution_summary={
                "output": "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
                "files_created": ["fibonacci.py"],
                "quality_score": 0.92
            },
            cleanup_actions=["save_results", "cleanup_temp"],
            next_steps=["deliver_to_user"],
            metadata={
                "execution_time": 58.3,
                "tokens_used": 1150,
                "cost": 0.023
            }
        )
        
        assert result["status"] == "task_ended"
        assert result["reason"] == "success"
        
        # 6. Verificar que se enviaron todas las notificaciones
        await asyncio.sleep(2)
        
        stats = self.test_env.webhook_manager.get_webhook_stats("integration_webhook")
        assert stats["total_deliveries"] >= 3  # start, progress, end
        
        print("✅ Complete task lifecycle integration test passed")
    
    async def test_error_handling_and_recovery(self):
        """Test manejo de errores y recuperación"""
        task_id = f"error_test_{int(time.time())}"
        
        # 1. Simular tarea que falla
        sam_notifier = SAMNotificationSender("sam_error_test")
        
        # Notificar inicio
        sam_notifier.notify_task_started(task_id, {
            "task_type": "complex_analysis",
            "description": "Error handling test task"
        })
        
        # Notificar fallo
        sam_notifier.notify_task_failed(task_id, {
            "error_type": "RESOURCE_EXHAUSTED",
            "error_message": "Insufficient memory to complete task",
            "partial_results": {"analysis_progress": 0.7},
            "recovery_suggestions": ["increase_memory_limit", "split_task"]
        })
        
        # 2. Finalizar tarea con escalación
        result = await self.test_env.agent_end_task_manager.end_task(
            task_id=task_id,
            agent_id="sam_error_test",
            reason=AgentEndTaskReason.ESCALATED,
            execution_summary={
                "error": "Resource exhaustion during analysis",
                "partial_results": {"progress": 0.7}
            },
            cleanup_actions=["save_partial_results", "free_resources"],
            next_steps=["human_intervention_required", "resource_optimization"],
            metadata={
                "execution_time": 180.0,
                "error_code": "RESOURCE_EXHAUSTED",
                "escalation_reason": "automatic_escalation_on_resource_limit"
            }
        )
        
        assert result["status"] == "task_ended"
        assert result["reason"] == "escalated"
        
        print("✅ Error handling and recovery test passed")

class PerformanceTests:
    """
    Tests de performance y carga
    """
    
    def __init__(self, test_env: TestEnvironment):
        self.test_env = test_env
    
    async def test_high_volume_notifications(self):
        """Test volumen alto de notificaciones"""
        start_time = time.time()
        
        # Registrar webhook
        self.test_env.webhook_manager.register_webhook(
            "performance_webhook",
            "http://sam.chat:8999/webhook/performance",
            ["task_lifecycle"],
            "performance_secret"
        )
        
        # Enviar múltiples notificaciones
        sam_notifier = SAMNotificationSender("sam_performance")
        
        tasks = []
        for i in range(100):
            task_id = f"perf_task_{i}"
            
            # Crear tarea asíncrona para cada notificación
            task = asyncio.create_task(self._send_notification_sequence(sam_notifier, task_id))
            tasks.append(task)
        
        # Esperar que todas las notificaciones se procesen
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verificar performance
        assert duration < 30  # Debería completarse en menos de 30 segundos
        
        # Verificar estadísticas
        stats = self.test_env.webhook_manager.get_webhook_stats("performance_webhook")
        assert stats["total_deliveries"] >= 300  # 3 notificaciones por tarea * 100 tareas
        
        print(f"✅ High volume notifications test passed ({duration:.2f}s for 300 notifications)")
    
    async def _send_notification_sequence(self, notifier: SAMNotificationSender, task_id: str):
        """Enviar secuencia de notificaciones para una tarea"""
        # Inicio
        notifier.notify_task_started(task_id, {
            "task_type": "performance_test",
            "description": f"Performance test task {task_id}"
        })
        
        # Progreso
        notifier.notify_task_progress(task_id, {
            "progress": 50,
            "current_step": "Processing"
        })
        
        # Completación
        notifier.notify_task_completed(task_id, {
            "result": {"status": "success"},
            "execution_summary": "Performance test completed"
        })
    
    async def test_webhook_delivery_performance(self):
        """Test performance de entrega de webhooks"""
        # Registrar múltiples webhooks
        for i in range(10):
            self.test_env.webhook_manager.register_webhook(
                f"perf_webhook_{i}",
                f"http://sam.chat:899{i}/webhook",
                ["task_lifecycle"],
                f"secret_{i}"
            )
        
        start_time = time.time()
        
        # Enviar webhook a todos los endpoints
        test_payload = {
            "event_type": "performance_test",
            "timestamp": datetime.now().isoformat(),
            "data": {"test": True}
        }
        
        await self.test_env.webhook_manager.send_webhook(
            WebhookEventType.TASK_LIFECYCLE,
            test_payload
        )
        
        # Esperar procesamiento
        await asyncio.sleep(5)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verificar que se procesó rápidamente
        assert duration < 10  # Debería completarse en menos de 10 segundos
        
        print(f"✅ Webhook delivery performance test passed ({duration:.2f}s)")

class SecurityTests:
    """
    Tests de seguridad
    """
    
    def __init__(self, test_env: TestEnvironment):
        self.test_env = test_env
    
    def test_payload_injection_protection(self):
        """Test protección contra inyección en payloads"""
        # Intentar inyección SQL en task_id
        malicious_payload = create_task_execution_payload(
            task_id="'; DROP TABLE tasks; --",
            task_type="code_generation",
            description="Malicious task",
            orchestrator_agent_id="manus_001"
        )
        
        validator = PayloadValidator()
        result = validator.validate_payload(malicious_payload, PayloadType.TASK_EXECUTION)
        
        # Debería fallar la validación por formato inválido de task_id
        assert result["valid"] == False
        
        print("✅ Payload injection protection test passed")
    
    def test_webhook_signature_verification(self):
        """Test verificación de firmas de webhook"""
        # Crear payload de prueba
        test_payload = {
            "notification_id": "test_001",
            "task_id": "test_task",
            "agent_id": "test_agent",
            "notification_type": "task_completed",
            "status": "completed",
            "data": {"result": "success"}
        }
        
        # Firma válida
        import hmac
        import hashlib
        
        secret = "test_secret"
        payload_str = json.dumps(test_payload, sort_keys=True)
        valid_signature = "sha256=" + hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Test verificación exitosa
        result = self.test_env.webhook_receiver.verify_webhook_signature(
            payload_str, valid_signature
        )
        assert result == True
        
        # Test firma inválida
        invalid_signature = "sha256=invalid_signature"
        result = self.test_env.webhook_receiver.verify_webhook_signature(
            payload_str, invalid_signature
        )
        assert result == False
        
        print("✅ Webhook signature verification test passed")

async def run_all_tests():
    """
    Ejecutar toda la suite de tests
    """
    print("🚀 Starting MCP Orchestrator-Executor System Tests")
    print("=" * 60)
    
    # Configurar entorno de testing
    test_env = TestEnvironment()
    await test_env.setup()
    
    try:
        # Tests de validación de payloads
        print("\n📋 Running Payload Validation Tests...")
        payload_tests = PayloadValidationTests(test_env)
        payload_tests.test_task_execution_payload_validation()
        payload_tests.test_notification_payload_validation()
        payload_tests.test_agent_end_task_payload_validation()
        
        # Tests de sistema de notificaciones
        print("\n📢 Running Notification System Tests...")
        notification_tests = NotificationSystemTests(test_env)
        await notification_tests.test_notification_sending()
        await notification_tests.test_notification_retry_mechanism()
        
        # Tests de sistema de webhooks
        print("\n🔗 Running Webhook System Tests...")
        webhook_tests = WebhookSystemTests(test_env)
        await webhook_tests.test_webhook_registration()
        await webhook_tests.test_webhook_delivery()
        
        # Tests de agent_end_task
        print("\n🏁 Running Agent End Task Tests...")
        end_task_tests = AgentEndTaskTests(test_env)
        await end_task_tests.test_successful_task_completion()
        await end_task_tests.test_failed_task_completion()
        
        # Tests de integración
        print("\n🔄 Running Integration Tests...")
        integration_tests = IntegrationTests(test_env)
        await integration_tests.test_complete_task_lifecycle()
        await integration_tests.test_error_handling_and_recovery()
        
        # Tests de performance
        print("\n⚡ Running Performance Tests...")
        performance_tests = PerformanceTests(test_env)
        await performance_tests.test_high_volume_notifications()
        await performance_tests.test_webhook_delivery_performance()
        
        # Tests de seguridad
        print("\n🔒 Running Security Tests...")
        security_tests = SecurityTests(test_env)
        security_tests.test_payload_injection_protection()
        security_tests.test_webhook_signature_verification()
        
        print("\n" + "=" * 60)
        print("🎉 All tests passed successfully!")
        print("✅ MCP Orchestrator-Executor System is ready for production")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        raise
    
    finally:
        await test_env.teardown()

if __name__ == "__main__":
    # Ejecutar tests
    asyncio.run(run_all_tests())

