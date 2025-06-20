# Advanced Integrations and APIs for MCP System
# Third-party service integrations and external API connectors

import asyncio
import aiohttp
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
from abc import ABC, abstractmethod
import hashlib
import hmac
import base64
from urllib.parse import urlencode, quote

class IntegrationType(Enum):
    """Types of integrations"""
    WEBHOOK = "webhook"
    REST_API = "rest_api"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"
    DATABASE = "database"
    MESSAGE_QUEUE = "message_queue"
    FILE_STORAGE = "file_storage"
    AUTHENTICATION = "authentication"

class IntegrationStatus(Enum):
    """Integration status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"
    RATE_LIMITED = "rate_limited"

@dataclass
class IntegrationConfig:
    """Configuration for an integration"""
    id: str
    name: str
    type: IntegrationType
    endpoint: str
    auth_config: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    rate_limit: Optional[int] = None  # requests per minute
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    webhook_secret: Optional[str] = None
    custom_config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class APIResponse:
    """Standardized API response"""
    success: bool
    status_code: int
    data: Any = None
    error: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    response_time: float = 0.0
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))

class BaseIntegration(ABC):
    """Base class for all integrations"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.status = IntegrationStatus.INACTIVE
        self.logger = logging.getLogger(f"{__name__}.{config.name}")
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = RateLimiter(config.rate_limit) if config.rate_limit else None
        
        # Metrics
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'last_request_time': None,
            'rate_limit_hits': 0
        }
    
    async def initialize(self):
        """Initialize the integration"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                headers=self.config.headers
            )
            await self._authenticate()
            self.status = IntegrationStatus.ACTIVE
            self.logger.info(f"Integration {self.config.name} initialized successfully")
        except Exception as e:
            self.status = IntegrationStatus.ERROR
            self.logger.error(f"Failed to initialize integration {self.config.name}: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        self.status = IntegrationStatus.INACTIVE
    
    @abstractmethod
    async def _authenticate(self):
        """Authenticate with the service"""
        pass
    
    async def make_request(
        self,
        method: str,
        endpoint: str,
        data: Any = None,
        params: Dict = None,
        headers: Dict = None
    ) -> APIResponse:
        """Make an authenticated request"""
        if not self.session:
            raise RuntimeError("Integration not initialized")
        
        # Rate limiting
        if self.rate_limiter:
            await self.rate_limiter.acquire()
        
        start_time = time.time()
        request_headers = {**self.config.headers}
        if headers:
            request_headers.update(headers)
        
        try:
            # Prepare request
            url = f"{self.config.endpoint.rstrip('/')}/{endpoint.lstrip('/')}"
            
            # Make request with retries
            for attempt in range(self.config.retry_attempts):
                try:
                    async with self.session.request(
                        method=method,
                        url=url,
                        json=data if method.upper() in ['POST', 'PUT', 'PATCH'] else None,
                        params=params,
                        headers=request_headers
                    ) as response:
                        response_time = time.time() - start_time
                        response_data = await self._parse_response(response)
                        
                        # Update metrics
                        self._update_metrics(response.status, response_time)
                        
                        return APIResponse(
                            success=response.status < 400,
                            status_code=response.status,
                            data=response_data,
                            headers=dict(response.headers),
                            response_time=response_time
                        )
                
                except asyncio.TimeoutError:
                    if attempt == self.config.retry_attempts - 1:
                        raise
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                
                except aiohttp.ClientError as e:
                    if attempt == self.config.retry_attempts - 1:
                        raise
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
        
        except Exception as e:
            response_time = time.time() - start_time
            self._update_metrics(500, response_time, failed=True)
            
            return APIResponse(
                success=False,
                status_code=500,
                error=str(e),
                response_time=response_time
            )
    
    async def _parse_response(self, response: aiohttp.ClientResponse) -> Any:
        """Parse response based on content type"""
        content_type = response.headers.get('content-type', '').lower()
        
        if 'application/json' in content_type:
            return await response.json()
        elif 'text/' in content_type:
            return await response.text()
        else:
            return await response.read()
    
    def _update_metrics(self, status_code: int, response_time: float, failed: bool = False):
        """Update integration metrics"""
        self.metrics['total_requests'] += 1
        self.metrics['last_request_time'] = datetime.now()
        
        if failed or status_code >= 400:
            self.metrics['failed_requests'] += 1
        else:
            self.metrics['successful_requests'] += 1
        
        # Update average response time
        total_requests = self.metrics['total_requests']
        current_avg = self.metrics['average_response_time']
        self.metrics['average_response_time'] = (
            (current_avg * (total_requests - 1) + response_time) / total_requests
        )
        
        if status_code == 429:  # Rate limited
            self.metrics['rate_limit_hits'] += 1

class RateLimiter:
    """Simple rate limiter"""
    
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make a request"""
        async with self.lock:
            now = time.time()
            # Remove requests older than 1 minute
            self.requests = [req_time for req_time in self.requests if now - req_time < 60]
            
            if len(self.requests) >= self.requests_per_minute:
                # Wait until we can make a request
                sleep_time = 60 - (now - self.requests[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    return await self.acquire()
            
            self.requests.append(now)

# Specific Integrations

class SlackIntegration(BaseIntegration):
    """Slack integration for notifications and communication"""
    
    async def _authenticate(self):
        """Authenticate with Slack"""
        token = self.config.auth_config.get('bot_token')
        if not token:
            raise ValueError("Slack bot token required")
        
        self.config.headers['Authorization'] = f"Bearer {token}"
        
        # Test authentication
        response = await self.make_request('GET', 'auth.test')
        if not response.success:
            raise RuntimeError(f"Slack authentication failed: {response.error}")
    
    async def send_message(self, channel: str, text: str, blocks: List = None) -> APIResponse:
        """Send message to Slack channel"""
        data = {
            'channel': channel,
            'text': text
        }
        if blocks:
            data['blocks'] = blocks
        
        return await self.make_request('POST', 'chat.postMessage', data=data)
    
    async def create_channel(self, name: str, is_private: bool = False) -> APIResponse:
        """Create a new Slack channel"""
        data = {
            'name': name,
            'is_private': is_private
        }
        return await self.make_request('POST', 'conversations.create', data=data)

class DiscordIntegration(BaseIntegration):
    """Discord integration for community management"""
    
    async def _authenticate(self):
        """Authenticate with Discord"""
        token = self.config.auth_config.get('bot_token')
        if not token:
            raise ValueError("Discord bot token required")
        
        self.config.headers['Authorization'] = f"Bot {token}"
    
    async def send_message(self, channel_id: str, content: str, embeds: List = None) -> APIResponse:
        """Send message to Discord channel"""
        data = {'content': content}
        if embeds:
            data['embeds'] = embeds
        
        return await self.make_request('POST', f'channels/{channel_id}/messages', data=data)
    
    async def create_webhook(self, channel_id: str, name: str) -> APIResponse:
        """Create a webhook for a channel"""
        data = {'name': name}
        return await self.make_request('POST', f'channels/{channel_id}/webhooks', data=data)

class JiraIntegration(BaseIntegration):
    """Jira integration for issue tracking"""
    
    async def _authenticate(self):
        """Authenticate with Jira"""
        email = self.config.auth_config.get('email')
        api_token = self.config.auth_config.get('api_token')
        
        if not email or not api_token:
            raise ValueError("Jira email and API token required")
        
        credentials = base64.b64encode(f"{email}:{api_token}".encode()).decode()
        self.config.headers['Authorization'] = f"Basic {credentials}"
    
    async def create_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task"
    ) -> APIResponse:
        """Create a new Jira issue"""
        data = {
            'fields': {
                'project': {'key': project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type}
            }
        }
        return await self.make_request('POST', 'issue', data=data)
    
    async def update_issue(self, issue_key: str, fields: Dict) -> APIResponse:
        """Update a Jira issue"""
        data = {'fields': fields}
        return await self.make_request('PUT', f'issue/{issue_key}', data=data)
    
    async def search_issues(self, jql: str, max_results: int = 50) -> APIResponse:
        """Search for issues using JQL"""
        params = {
            'jql': jql,
            'maxResults': max_results
        }
        return await self.make_request('GET', 'search', params=params)

class ZendeskIntegration(BaseIntegration):
    """Zendesk integration for customer support"""
    
    async def _authenticate(self):
        """Authenticate with Zendesk"""
        email = self.config.auth_config.get('email')
        api_token = self.config.auth_config.get('api_token')
        
        if not email or not api_token:
            raise ValueError("Zendesk email and API token required")
        
        credentials = base64.b64encode(f"{email}/token:{api_token}".encode()).decode()
        self.config.headers['Authorization'] = f"Basic {credentials}"
    
    async def create_ticket(
        self,
        subject: str,
        description: str,
        requester_email: str,
        priority: str = "normal"
    ) -> APIResponse:
        """Create a new support ticket"""
        data = {
            'ticket': {
                'subject': subject,
                'comment': {'body': description},
                'requester': {'email': requester_email},
                'priority': priority
            }
        }
        return await self.make_request('POST', 'tickets.json', data=data)
    
    async def update_ticket(self, ticket_id: int, comment: str, status: str = None) -> APIResponse:
        """Update a support ticket"""
        data = {
            'ticket': {
                'comment': {'body': comment}
            }
        }
        if status:
            data['ticket']['status'] = status
        
        return await self.make_request('PUT', f'tickets/{ticket_id}.json', data=data)

class SendGridIntegration(BaseIntegration):
    """SendGrid integration for email notifications"""
    
    async def _authenticate(self):
        """Authenticate with SendGrid"""
        api_key = self.config.auth_config.get('api_key')
        if not api_key:
            raise ValueError("SendGrid API key required")
        
        self.config.headers['Authorization'] = f"Bearer {api_key}"
    
    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        content: str,
        from_email: str = None,
        template_id: str = None
    ) -> APIResponse:
        """Send email via SendGrid"""
        data = {
            'personalizations': [{
                'to': [{'email': email} for email in to_emails],
                'subject': subject
            }],
            'from': {'email': from_email or self.config.custom_config.get('default_from_email')},
            'content': [{
                'type': 'text/html',
                'value': content
            }]
        }
        
        if template_id:
            data['template_id'] = template_id
        
        return await self.make_request('POST', 'mail/send', data=data)

class StripeIntegration(BaseIntegration):
    """Stripe integration for payment processing"""
    
    async def _authenticate(self):
        """Authenticate with Stripe"""
        secret_key = self.config.auth_config.get('secret_key')
        if not secret_key:
            raise ValueError("Stripe secret key required")
        
        self.config.headers['Authorization'] = f"Bearer {secret_key}"
    
    async def create_payment_intent(
        self,
        amount: int,
        currency: str = "usd",
        metadata: Dict = None
    ) -> APIResponse:
        """Create a payment intent"""
        data = {
            'amount': amount,
            'currency': currency
        }
        if metadata:
            data['metadata'] = metadata
        
        return await self.make_request('POST', 'payment_intents', data=data)
    
    async def retrieve_customer(self, customer_id: str) -> APIResponse:
        """Retrieve customer information"""
        return await self.make_request('GET', f'customers/{customer_id}')

class WebhookHandler:
    """Handle incoming webhooks from various services"""
    
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_handler(self, service: str, handler: Callable):
        """Register a webhook handler for a service"""
        self.handlers[service] = handler
    
    async def handle_webhook(
        self,
        service: str,
        payload: Dict,
        headers: Dict,
        secret: str = None
    ) -> Dict[str, Any]:
        """Handle incoming webhook"""
        try:
            # Verify webhook signature if secret provided
            if secret:
                if not self._verify_signature(payload, headers, secret, service):
                    return {'error': 'Invalid signature', 'status': 401}
            
            # Get handler for service
            handler = self.handlers.get(service)
            if not handler:
                return {'error': f'No handler for service: {service}', 'status': 404}
            
            # Process webhook
            result = await handler(payload, headers)
            
            self.logger.info(f"Webhook processed for {service}")
            return {'status': 200, 'result': result}
            
        except Exception as e:
            self.logger.error(f"Webhook processing error for {service}: {e}")
            return {'error': str(e), 'status': 500}
    
    def _verify_signature(self, payload: Dict, headers: Dict, secret: str, service: str) -> bool:
        """Verify webhook signature"""
        if service == 'github':
            signature = headers.get('X-Hub-Signature-256', '')
            expected = 'sha256=' + hmac.new(
                secret.encode(),
                json.dumps(payload).encode(),
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, expected)
        
        elif service == 'slack':
            timestamp = headers.get('X-Slack-Request-Timestamp', '')
            signature = headers.get('X-Slack-Signature', '')
            
            if not timestamp or not signature:
                return False
            
            # Check timestamp (prevent replay attacks)
            if abs(time.time() - int(timestamp)) > 300:  # 5 minutes
                return False
            
            sig_basestring = f"v0:{timestamp}:{json.dumps(payload)}"
            expected = 'v0=' + hmac.new(
                secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected)
        
        # Add more signature verification methods as needed
        return True

class IntegrationManager:
    """Manage all integrations"""
    
    def __init__(self):
        self.integrations: Dict[str, BaseIntegration] = {}
        self.webhook_handler = WebhookHandler()
        self.logger = logging.getLogger(__name__)
    
    async def add_integration(self, config: IntegrationConfig) -> bool:
        """Add and initialize an integration"""
        try:
            # Create integration instance based on type
            integration = self._create_integration(config)
            
            # Initialize integration
            await integration.initialize()
            
            # Store integration
            self.integrations[config.id] = integration
            
            self.logger.info(f"Integration {config.name} added successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add integration {config.name}: {e}")
            return False
    
    def _create_integration(self, config: IntegrationConfig) -> BaseIntegration:
        """Create integration instance based on configuration"""
        integration_map = {
            'slack': SlackIntegration,
            'discord': DiscordIntegration,
            'jira': JiraIntegration,
            'zendesk': ZendeskIntegration,
            'sendgrid': SendGridIntegration,
            'stripe': StripeIntegration
        }
        
        integration_class = integration_map.get(config.name.lower())
        if not integration_class:
            raise ValueError(f"Unknown integration type: {config.name}")
        
        return integration_class(config)
    
    async def remove_integration(self, integration_id: str) -> bool:
        """Remove an integration"""
        try:
            integration = self.integrations.get(integration_id)
            if integration:
                await integration.cleanup()
                del self.integrations[integration_id]
                self.logger.info(f"Integration {integration_id} removed")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to remove integration {integration_id}: {e}")
            return False
    
    def get_integration(self, integration_id: str) -> Optional[BaseIntegration]:
        """Get integration by ID"""
        return self.integrations.get(integration_id)
    
    def list_integrations(self) -> List[Dict[str, Any]]:
        """List all integrations with their status"""
        return [
            {
                'id': integration.config.id,
                'name': integration.config.name,
                'type': integration.config.type.value,
                'status': integration.status.value,
                'metrics': integration.metrics
            }
            for integration in self.integrations.values()
        ]
    
    async def test_integration(self, integration_id: str) -> Dict[str, Any]:
        """Test an integration"""
        integration = self.integrations.get(integration_id)
        if not integration:
            return {'success': False, 'error': 'Integration not found'}
        
        try:
            # Simple health check
            response = await integration.make_request('GET', '')
            return {
                'success': response.success,
                'status_code': response.status_code,
                'response_time': response.response_time
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def cleanup_all(self):
        """Cleanup all integrations"""
        for integration in self.integrations.values():
            try:
                await integration.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up integration: {e}")
        
        self.integrations.clear()

# Example usage and configuration
async def setup_integrations():
    """Example setup of integrations"""
    manager = IntegrationManager()
    
    # Slack integration
    slack_config = IntegrationConfig(
        id="slack_main",
        name="slack",
        type=IntegrationType.REST_API,
        endpoint="https://slack.com/api",
        auth_config={
            'bot_token': 'xoxb-your-bot-token'
        },
        rate_limit=50  # 50 requests per minute
    )
    
    # Discord integration
    discord_config = IntegrationConfig(
        id="discord_main",
        name="discord",
        type=IntegrationType.REST_API,
        endpoint="https://discord.com/api/v10",
        auth_config={
            'bot_token': 'your-discord-bot-token'
        },
        rate_limit=30
    )
    
    # Jira integration
    jira_config = IntegrationConfig(
        id="jira_main",
        name="jira",
        type=IntegrationType.REST_API,
        endpoint="https://your-domain.atlassian.net/rest/api/3",
        auth_config={
            'email': 'your-email@domain.com',
            'api_token': 'your-jira-api-token'
        },
        rate_limit=100
    )
    
    # Add integrations
    await manager.add_integration(slack_config)
    await manager.add_integration(discord_config)
    await manager.add_integration(jira_config)
    
    return manager

if __name__ == "__main__":
    async def main():
        # Setup integrations
        manager = await setup_integrations()
        
        # Test Slack integration
        slack = manager.get_integration("slack_main")
        if slack:
            response = await slack.send_message(
                channel="#general",
                text="Hello from MCP System! 🚀"
            )
            print(f"Slack message sent: {response.success}")
        
        # List all integrations
        integrations = manager.list_integrations()
        print(f"Active integrations: {len(integrations)}")
        
        # Cleanup
        await manager.cleanup_all()
    
    asyncio.run(main())

