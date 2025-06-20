#!/usr/bin/env python3
"""
Manus Webhook Receiver
Sistema de recepción y procesamiento de webhooks para Manus

Este módulo implementa un receptor robusto de webhooks que:
- Recibe webhooks de sistemas externos (GitHub, Slack, etc.)
- Valida signatures y autenticación
- Procesa eventos de manera asíncrona
- Integra con el sistema de notificaciones SAM-Manus
- Proporciona retry logic y dead letter queue
- Mantiene logs de auditoría completos
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import base64
import secrets

# Imports para servidor web
try:
    from flask import Flask, request, jsonify, abort
    from werkzeug.exceptions import BadRequest
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

try:
    from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from aiohttp import web, ClientSession
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

# Imports para persistencia y colas
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import sqlalchemy as sa
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import declarative_base, sessionmaker
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebhookSource(Enum):
    """Fuentes de webhooks soportadas"""
    GITHUB = "github"
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    STRIPE = "stripe"
    PAYPAL = "paypal"
    CUSTOM = "custom"
    MANUS = "manus"
    SAM = "sam"

class WebhookStatus(Enum):
    """Estados de procesamiento de webhooks"""
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"

@dataclass
class WebhookEvent:
    """Estructura de datos para eventos de webhook"""
    id: str
    source: WebhookSource
    event_type: str
    payload: Dict[str, Any]
    headers: Dict[str, str]
    signature: Optional[str]
    timestamp: datetime
    status: WebhookStatus = WebhookStatus.RECEIVED
    retry_count: int = 0
    last_error: Optional[str] = None
    processed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el evento a diccionario"""
        return {
            'id': self.id,
            'source': self.source.value,
            'event_type': self.event_type,
            'payload': self.payload,
            'headers': self.headers,
            'signature': self.signature,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.value,
            'retry_count': self.retry_count,
            'last_error': self.last_error,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebhookEvent':
        """Crea un evento desde diccionario"""
        return cls(
            id=data['id'],
            source=WebhookSource(data['source']),
            event_type=data['event_type'],
            payload=data['payload'],
            headers=data['headers'],
            signature=data.get('signature'),
            timestamp=datetime.fromisoformat(data['timestamp']),
            status=WebhookStatus(data.get('status', 'received')),
            retry_count=data.get('retry_count', 0),
            last_error=data.get('last_error'),
            processed_at=datetime.fromisoformat(data['processed_at']) if data.get('processed_at') else None
        )

class WebhookProcessor:
    """Procesador base para webhooks"""
    
    def __init__(self, source: WebhookSource):
        self.source = source
        self.is_active = True
    
    async def process(self, event: WebhookEvent) -> bool:
        """
        Procesa un evento de webhook
        
        Returns:
            True si se procesó exitosamente, False en caso contrario
        """
        raise NotImplementedError("Subclasses must implement process method")
    
    def can_process(self, event: WebhookEvent) -> bool:
        """Determina si este procesador puede manejar el evento"""
        return event.source == self.source
    
    def validate_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Valida la signature del webhook"""
        return True  # Implementar según el proveedor

class GitHubWebhookProcessor(WebhookProcessor):
    """Procesador específico para webhooks de GitHub"""
    
    def __init__(self, secret: Optional[str] = None):
        super().__init__(WebhookSource.GITHUB)
        self.secret = secret
    
    def validate_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Valida signature de GitHub usando HMAC-SHA256"""
        if not secret or not signature:
            return False
        
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # GitHub envía la signature como "sha256=<hash>"
        if signature.startswith('sha256='):
            signature = signature[7:]
        
        return hmac.compare_digest(expected_signature, signature)
    
    async def process(self, event: WebhookEvent) -> bool:
        """Procesa eventos de GitHub"""
        try:
            event_type = event.event_type
            payload = event.payload
            
            logger.info(f"Processing GitHub event: {event_type}")
            
            if event_type == "push":
                return await self._handle_push_event(payload)
            elif event_type == "pull_request":
                return await self._handle_pull_request_event(payload)
            elif event_type == "issues":
                return await self._handle_issues_event(payload)
            elif event_type == "release":
                return await self._handle_release_event(payload)
            else:
                logger.info(f"Unhandled GitHub event type: {event_type}")
                return True  # No es un error, simplemente no lo manejamos
            
        except Exception as e:
            logger.error(f"Error processing GitHub webhook: {e}")
            return False
    
    async def _handle_push_event(self, payload: Dict[str, Any]) -> bool:
        """Maneja eventos de push"""
        repository = payload.get('repository', {})
        commits = payload.get('commits', [])
        
        logger.info(f"Push to {repository.get('full_name')}: {len(commits)} commits")
        
        # Aquí se puede integrar con sistemas de CI/CD, notificaciones, etc.
        # Por ejemplo, triggear builds automáticos o notificar al equipo
        
        return True
    
    async def _handle_pull_request_event(self, payload: Dict[str, Any]) -> bool:
        """Maneja eventos de pull request"""
        action = payload.get('action')
        pr = payload.get('pull_request', {})
        
        logger.info(f"Pull request {action}: #{pr.get('number')} - {pr.get('title')}")
        
        # Integrar con sistemas de review, testing automático, etc.
        
        return True
    
    async def _handle_issues_event(self, payload: Dict[str, Any]) -> bool:
        """Maneja eventos de issues"""
        action = payload.get('action')
        issue = payload.get('issue', {})
        
        logger.info(f"Issue {action}: #{issue.get('number')} - {issue.get('title')}")
        
        # Integrar con sistemas de tracking, notificaciones, etc.
        
        return True
    
    async def _handle_release_event(self, payload: Dict[str, Any]) -> bool:
        """Maneja eventos de release"""
        action = payload.get('action')
        release = payload.get('release', {})
        
        logger.info(f"Release {action}: {release.get('tag_name')} - {release.get('name')}")
        
        # Integrar con sistemas de deployment, notificaciones, etc.
        
        return True

class SlackWebhookProcessor(WebhookProcessor):
    """Procesador específico para webhooks de Slack"""
    
    def __init__(self, signing_secret: Optional[str] = None):
        super().__init__(WebhookSource.SLACK)
        self.signing_secret = signing_secret
    
    def validate_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Valida signature de Slack"""
        if not secret or not signature:
            return False
        
        # Slack usa un timestamp en los headers
        timestamp = str(int(time.time()))
        
        # Crear string base para signature
        sig_basestring = f"v0:{timestamp}:{payload.decode('utf-8')}"
        
        # Calcular signature esperada
        expected_signature = 'v0=' + hmac.new(
            secret.encode('utf-8'),
            sig_basestring.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    async def process(self, event: WebhookEvent) -> bool:
        """Procesa eventos de Slack"""
        try:
            payload = event.payload
            
            # Manejar challenge de verificación de URL
            if 'challenge' in payload:
                logger.info("Slack URL verification challenge received")
                return True
            
            event_type = payload.get('type', 'unknown')
            logger.info(f"Processing Slack event: {event_type}")
            
            if event_type == "message":
                return await self._handle_message_event(payload)
            elif event_type == "app_mention":
                return await self._handle_mention_event(payload)
            else:
                logger.info(f"Unhandled Slack event type: {event_type}")
                return True
            
        except Exception as e:
            logger.error(f"Error processing Slack webhook: {e}")
            return False
    
    async def _handle_message_event(self, payload: Dict[str, Any]) -> bool:
        """Maneja eventos de mensaje"""
        event = payload.get('event', {})
        text = event.get('text', '')
        user = event.get('user', 'unknown')
        
        logger.info(f"Slack message from {user}: {text[:100]}...")
        
        # Procesar comandos, respuestas automáticas, etc.
        
        return True
    
    async def _handle_mention_event(self, payload: Dict[str, Any]) -> bool:
        """Maneja menciones del bot"""
        event = payload.get('event', {})
        text = event.get('text', '')
        user = event.get('user', 'unknown')
        
        logger.info(f"Bot mentioned by {user}: {text}")
        
        # Procesar comandos dirigidos al bot
        
        return True

class CustomWebhookProcessor(WebhookProcessor):
    """Procesador genérico para webhooks personalizados"""
    
    def __init__(self, processor_func: Optional[Callable] = None):
        super().__init__(WebhookSource.CUSTOM)
        self.processor_func = processor_func
    
    async def process(self, event: WebhookEvent) -> bool:
        """Procesa eventos personalizados"""
        try:
            if self.processor_func:
                if asyncio.iscoroutinefunction(self.processor_func):
                    return await self.processor_func(event)
                else:
                    return self.processor_func(event)
            
            # Procesamiento por defecto
            logger.info(f"Processing custom webhook: {event.event_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing custom webhook: {e}")
            return False

class WebhookStorage:
    """Sistema de almacenamiento para webhooks"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or "redis://localhost:6379"
        self.redis_client = None
    
    async def initialize(self):
        """Inicializa el sistema de almacenamiento"""
        if REDIS_AVAILABLE:
            self.redis_client = redis.from_url(self.redis_url)
            try:
                await self.redis_client.ping()
                logger.info("Connected to Redis for webhook storage")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                self.redis_client = None
    
    async def store_event(self, event: WebhookEvent):
        """Almacena un evento de webhook"""
        if self.redis_client:
            key = f"webhook:{event.id}"
            data = json.dumps(event.to_dict())
            await self.redis_client.setex(key, 86400, data)  # TTL 24 horas
    
    async def get_event(self, event_id: str) -> Optional[WebhookEvent]:
        """Recupera un evento por ID"""
        if self.redis_client:
            key = f"webhook:{event_id}"
            data = await self.redis_client.get(key)
            if data:
                return WebhookEvent.from_dict(json.loads(data))
        return None
    
    async def update_event_status(self, event_id: str, status: WebhookStatus, 
                                 error: Optional[str] = None):
        """Actualiza el estado de un evento"""
        event = await self.get_event(event_id)
        if event:
            event.status = status
            if error:
                event.last_error = error
            if status == WebhookStatus.COMPLETED:
                event.processed_at = datetime.now(timezone.utc)
            await self.store_event(event)

class ManusWebhookReceiver:
    """
    Receptor principal de webhooks para Manus
    
    Características:
    - Múltiples fuentes de webhook soportadas
    - Validación de signatures automática
    - Procesamiento asíncrono con retry logic
    - Dead letter queue para eventos fallidos
    - Métricas y monitoreo integrado
    - API REST para gestión
    """
    
    def __init__(self, 
                 host: str = "0.0.0.0",
                 port: int = 8080,
                 redis_url: Optional[str] = None):
        self.host = host
        self.port = port
        self.storage = WebhookStorage(redis_url)
        self.processors: Dict[WebhookSource, WebhookProcessor] = {}
        self.secrets: Dict[WebhookSource, str] = {}
        
        # Configuración de retry
        self.max_retries = 3
        self.retry_delays = [1, 5, 15]  # segundos
        
        # Métricas
        self.metrics = {
            'total_received': 0,
            'total_processed': 0,
            'total_failed': 0,
            'by_source': {},
            'by_event_type': {}
        }
        
        # Registrar procesadores por defecto
        self.register_processor(GitHubWebhookProcessor())
        self.register_processor(SlackWebhookProcessor())
        self.register_processor(CustomWebhookProcessor())
    
    async def initialize(self):
        """Inicializa el receptor de webhooks"""
        await self.storage.initialize()
        logger.info("Manus Webhook Receiver initialized")
    
    def register_processor(self, processor: WebhookProcessor):
        """Registra un procesador de webhooks"""
        self.processors[processor.source] = processor
        logger.info(f"Registered webhook processor for {processor.source.value}")
    
    def set_secret(self, source: WebhookSource, secret: str):
        """Configura el secret para validación de signatures"""
        self.secrets[source] = secret
        logger.info(f"Secret configured for {source.value}")
    
    async def receive_webhook(self, 
                            source: WebhookSource,
                            event_type: str,
                            payload: Dict[str, Any],
                            headers: Dict[str, str],
                            raw_payload: bytes) -> Dict[str, Any]:
        """
        Recibe y procesa un webhook
        
        Returns:
            Respuesta del procesamiento
        """
        # Crear evento
        event = WebhookEvent(
            id=str(uuid.uuid4()),
            source=source,
            event_type=event_type,
            payload=payload,
            headers=headers,
            signature=headers.get('X-Hub-Signature-256') or headers.get('X-Slack-Signature'),
            timestamp=datetime.now(timezone.utc)
        )
        
        try:
            # Validar signature si está configurada
            if source in self.secrets and event.signature:
                processor = self.processors.get(source)
                if processor and not processor.validate_signature(
                    raw_payload, event.signature, self.secrets[source]
                ):
                    logger.warning(f"Invalid signature for {source.value} webhook")
                    return {
                        'status': 'error',
                        'error': 'Invalid signature',
                        'event_id': event.id
                    }
            
            # Almacenar evento
            await self.storage.store_event(event)
            
            # Actualizar métricas
            self.metrics['total_received'] += 1
            self.metrics['by_source'][source.value] = self.metrics['by_source'].get(source.value, 0) + 1
            self.metrics['by_event_type'][event_type] = self.metrics['by_event_type'].get(event_type, 0) + 1
            
            # Procesar de manera asíncrona
            asyncio.create_task(self._process_event_with_retry(event))
            
            logger.info(f"Webhook received: {event.id} ({source.value}/{event_type})")
            
            return {
                'status': 'received',
                'event_id': event.id,
                'timestamp': event.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error receiving webhook: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'event_id': event.id
            }
    
    async def _process_event_with_retry(self, event: WebhookEvent):
        """Procesa un evento con lógica de retry"""
        processor = self.processors.get(event.source)
        if not processor:
            logger.error(f"No processor found for {event.source.value}")
            await self.storage.update_event_status(
                event.id, 
                WebhookStatus.FAILED, 
                f"No processor for {event.source.value}"
            )
            return
        
        # Actualizar estado a procesando
        await self.storage.update_event_status(event.id, WebhookStatus.PROCESSING)
        
        for attempt in range(self.max_retries + 1):
            try:
                success = await processor.process(event)
                
                if success:
                    await self.storage.update_event_status(event.id, WebhookStatus.COMPLETED)
                    self.metrics['total_processed'] += 1
                    logger.info(f"Webhook processed successfully: {event.id}")
                    return
                else:
                    raise Exception("Processor returned False")
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error processing webhook {event.id} (attempt {attempt + 1}): {error_msg}")
                
                if attempt < self.max_retries:
                    # Retry con delay exponencial
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    await self.storage.update_event_status(event.id, WebhookStatus.RETRYING, error_msg)
                    await asyncio.sleep(delay)
                else:
                    # Mover a dead letter queue
                    await self.storage.update_event_status(event.id, WebhookStatus.DEAD_LETTER, error_msg)
                    self.metrics['total_failed'] += 1
                    logger.error(f"Webhook moved to dead letter queue: {event.id}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del receptor"""
        return self.metrics.copy()
    
    async def get_event_status(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado de un evento"""
        event = await self.storage.get_event(event_id)
        if event:
            return event.to_dict()
        return None

# Implementaciones para diferentes frameworks web

class FlaskWebhookReceiver:
    """Implementación Flask del receptor de webhooks"""
    
    def __init__(self, receiver: ManusWebhookReceiver):
        if not FLASK_AVAILABLE:
            raise ImportError("Flask not available")
        
        self.receiver = receiver
        self.app = Flask(__name__)
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas de Flask"""
        
        @self.app.route('/webhook/<source>', methods=['POST'])
        def receive_webhook(source):
            try:
                webhook_source = WebhookSource(source)
            except ValueError:
                abort(400, f"Unsupported webhook source: {source}")
            
            # Extraer datos de la request
            payload = request.get_json() or {}
            headers = dict(request.headers)
            raw_payload = request.get_data()
            event_type = headers.get('X-GitHub-Event', headers.get('X-Event-Type', 'unknown'))
            
            # Procesar webhook de manera asíncrona
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    self.receiver.receive_webhook(
                        webhook_source, event_type, payload, headers, raw_payload
                    )
                )
                return jsonify(result)
            finally:
                loop.close()
        
        @self.app.route('/webhook/status/<event_id>', methods=['GET'])
        def get_event_status(event_id):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    self.receiver.get_event_status(event_id)
                )
                if result:
                    return jsonify(result)
                else:
                    abort(404, "Event not found")
            finally:
                loop.close()
        
        @self.app.route('/webhook/metrics', methods=['GET'])
        def get_metrics():
            return jsonify(self.receiver.get_metrics())
    
    def run(self, **kwargs):
        """Ejecuta el servidor Flask"""
        self.app.run(host=self.receiver.host, port=self.receiver.port, **kwargs)

class FastAPIWebhookReceiver:
    """Implementación FastAPI del receptor de webhooks"""
    
    def __init__(self, receiver: ManusWebhookReceiver):
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI not available")
        
        self.receiver = receiver
        self.app = FastAPI(title="Manus Webhook Receiver")
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas de FastAPI"""
        
        @self.app.post("/webhook/{source}")
        async def receive_webhook(source: str, request: Request, background_tasks: BackgroundTasks):
            try:
                webhook_source = WebhookSource(source)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Unsupported webhook source: {source}")
            
            # Extraer datos de la request
            payload = await request.json()
            headers = dict(request.headers)
            raw_payload = await request.body()
            event_type = headers.get('x-github-event', headers.get('x-event-type', 'unknown'))
            
            result = await self.receiver.receive_webhook(
                webhook_source, event_type, payload, headers, raw_payload
            )
            
            return JSONResponse(content=result)
        
        @self.app.get("/webhook/status/{event_id}")
        async def get_event_status(event_id: str):
            result = await self.receiver.get_event_status(event_id)
            if result:
                return JSONResponse(content=result)
            else:
                raise HTTPException(status_code=404, detail="Event not found")
        
        @self.app.get("/webhook/metrics")
        async def get_metrics():
            return JSONResponse(content=self.receiver.get_metrics())

# Funciones de utilidad

async def create_webhook_receiver(host: str = "0.0.0.0", 
                                port: int = 8080,
                                redis_url: Optional[str] = None) -> ManusWebhookReceiver:
    """Crea e inicializa un receptor de webhooks"""
    receiver = ManusWebhookReceiver(host, port, redis_url)
    await receiver.initialize()
    return receiver

def create_flask_webhook_server(receiver: ManusWebhookReceiver) -> FlaskWebhookReceiver:
    """Crea un servidor Flask para webhooks"""
    return FlaskWebhookReceiver(receiver)

def create_fastapi_webhook_server(receiver: ManusWebhookReceiver) -> FastAPIWebhookReceiver:
    """Crea un servidor FastAPI para webhooks"""
    return FastAPIWebhookReceiver(receiver)

# Ejemplo de uso
if __name__ == "__main__":
    async def main():
        # Crear receptor
        receiver = await create_webhook_receiver()
        
        # Configurar secrets para validación
        receiver.set_secret(WebhookSource.GITHUB, "your-github-webhook-secret")
        receiver.set_secret(WebhookSource.SLACK, "your-slack-signing-secret")
        
        # Crear servidor web (usar Flask o FastAPI según disponibilidad)
        if FASTAPI_AVAILABLE:
            server = create_fastapi_webhook_server(receiver)
            import uvicorn
            uvicorn.run(server.app, host=receiver.host, port=receiver.port)
        elif FLASK_AVAILABLE:
            server = create_flask_webhook_server(receiver)
            server.run(debug=True)
        else:
            logger.error("No web framework available (Flask or FastAPI required)")
    
    asyncio.run(main())

