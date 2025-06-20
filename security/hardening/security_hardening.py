# Security Hardening and Production Readiness for MCP System
# Enterprise-grade security implementation with comprehensive protection

import asyncio
import hashlib
import hmac
import jwt
import bcrypt
import secrets
import time
import logging
import re
import json
import ssl
import ipaddress
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import aioredis
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from functools import wraps
import asyncpg
import sqlalchemy
from sqlalchemy.sql import text

class SecurityLevel(Enum):
    """Security levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ThreatType(Enum):
    """Types of security threats"""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    BRUTE_FORCE = "brute_force"
    DDoS = "ddos"
    DATA_BREACH = "data_breach"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    MALWARE = "malware"

class AuthenticationMethod(Enum):
    """Authentication methods"""
    PASSWORD = "password"
    JWT = "jwt"
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    CERTIFICATE = "certificate"
    BIOMETRIC = "biometric"
    MFA = "mfa"

@dataclass
class SecurityConfig:
    """Security configuration"""
    encryption_key: str
    jwt_secret: str
    password_policy: Dict[str, Any] = field(default_factory=dict)
    rate_limiting: Dict[str, Any] = field(default_factory=dict)
    cors_settings: Dict[str, Any] = field(default_factory=dict)
    ssl_settings: Dict[str, Any] = field(default_factory=dict)
    audit_settings: Dict[str, Any] = field(default_factory=dict)
    threat_detection: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SecurityEvent:
    """Security event for logging and monitoring"""
    event_id: str
    timestamp: datetime
    event_type: ThreatType
    severity: SecurityLevel
    source_ip: str
    user_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    action_taken: Optional[str] = None

class EncryptionManager:
    """Handle encryption and decryption operations"""
    
    def __init__(self, master_key: str):
        self.master_key = master_key.encode()
        self.fernet = self._create_fernet()
        self.logger = logging.getLogger(__name__)
    
    def _create_fernet(self) -> Fernet:
        """Create Fernet encryption instance"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'mcp_system_salt',  # In production, use random salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        return Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise
    
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure token"""
        return secrets.token_urlsafe(length)

class InputSanitizer:
    """Sanitize and validate user inputs"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # SQL injection patterns
        self.sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(--|#|/\*|\*/)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+['\"].*['\"])",
            r"(;|\||&)"
        ]
        
        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>.*?</iframe>",
            r"<object[^>]*>.*?</object>",
            r"<embed[^>]*>.*?</embed>"
        ]
        
        # Command injection patterns
        self.command_patterns = [
            r"[;&|`$(){}[\]<>]",
            r"\b(cat|ls|pwd|whoami|id|uname|ps|netstat|ifconfig)\b",
            r"(\.\.\/|\.\.\\)",
            r"(/etc/passwd|/etc/shadow)"
        ]
    
    def sanitize_sql(self, input_string: str) -> str:
        """Sanitize SQL input"""
        if not isinstance(input_string, str):
            return str(input_string)
        
        # Check for SQL injection patterns
        for pattern in self.sql_patterns:
            if re.search(pattern, input_string, re.IGNORECASE):
                self.logger.warning(f"Potential SQL injection detected: {input_string[:100]}")
                raise ValueError("Invalid input detected")
        
        # Escape special characters
        sanitized = input_string.replace("'", "''")
        sanitized = sanitized.replace('"', '""')
        
        return sanitized
    
    def sanitize_html(self, input_string: str) -> str:
        """Sanitize HTML input to prevent XSS"""
        if not isinstance(input_string, str):
            return str(input_string)
        
        # Check for XSS patterns
        for pattern in self.xss_patterns:
            if re.search(pattern, input_string, re.IGNORECASE):
                self.logger.warning(f"Potential XSS detected: {input_string[:100]}")
                raise ValueError("Invalid input detected")
        
        # HTML entity encoding
        sanitized = input_string.replace("&", "&amp;")
        sanitized = sanitized.replace("<", "&lt;")
        sanitized = sanitized.replace(">", "&gt;")
        sanitized = sanitized.replace('"', "&quot;")
        sanitized = sanitized.replace("'", "&#x27;")
        
        return sanitized
    
    def sanitize_command(self, input_string: str) -> str:
        """Sanitize command input to prevent injection"""
        if not isinstance(input_string, str):
            return str(input_string)
        
        # Check for command injection patterns
        for pattern in self.command_patterns:
            if re.search(pattern, input_string, re.IGNORECASE):
                self.logger.warning(f"Potential command injection detected: {input_string[:100]}")
                raise ValueError("Invalid input detected")
        
        return input_string
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def validate_ip_address(self, ip: str) -> bool:
        """Validate IP address"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def validate_url(self, url: str) -> bool:
        """Validate URL format"""
        pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
        return bool(re.match(pattern, url))

class RateLimiter:
    """Advanced rate limiting with multiple strategies"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.logger = logging.getLogger(__name__)
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int,
        strategy: str = "sliding_window"
    ) -> Dict[str, Any]:
        """Check if request is within rate limit"""
        try:
            if strategy == "sliding_window":
                return await self._sliding_window_check(key, limit, window)
            elif strategy == "token_bucket":
                return await self._token_bucket_check(key, limit, window)
            elif strategy == "fixed_window":
                return await self._fixed_window_check(key, limit, window)
            else:
                raise ValueError(f"Unknown rate limiting strategy: {strategy}")
        
        except Exception as e:
            self.logger.error(f"Rate limiting error: {e}")
            # Fail open - allow request if rate limiter fails
            return {"allowed": True, "remaining": limit, "reset_time": time.time() + window}
    
    async def _sliding_window_check(self, key: str, limit: int, window: int) -> Dict[str, Any]:
        """Sliding window rate limiting"""
        now = time.time()
        pipeline = self.redis.pipeline()
        
        # Remove old entries
        pipeline.zremrangebyscore(key, 0, now - window)
        
        # Count current requests
        pipeline.zcard(key)
        
        # Add current request
        pipeline.zadd(key, {str(now): now})
        
        # Set expiration
        pipeline.expire(key, window)
        
        results = await pipeline.execute()
        current_count = results[1]
        
        if current_count >= limit:
            # Remove the request we just added since it's over limit
            await self.redis.zrem(key, str(now))
            
            # Get oldest request time for reset calculation
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            reset_time = oldest[0][1] + window if oldest else now + window
            
            return {
                "allowed": False,
                "remaining": 0,
                "reset_time": reset_time,
                "current_count": current_count
            }
        
        return {
            "allowed": True,
            "remaining": limit - current_count - 1,
            "reset_time": now + window,
            "current_count": current_count + 1
        }
    
    async def _token_bucket_check(self, key: str, limit: int, window: int) -> Dict[str, Any]:
        """Token bucket rate limiting"""
        now = time.time()
        bucket_key = f"bucket:{key}"
        
        # Get current bucket state
        bucket_data = await self.redis.hmget(bucket_key, "tokens", "last_refill")
        tokens = float(bucket_data[0] or limit)
        last_refill = float(bucket_data[1] or now)
        
        # Calculate tokens to add based on time elapsed
        time_elapsed = now - last_refill
        tokens_to_add = (time_elapsed / window) * limit
        tokens = min(limit, tokens + tokens_to_add)
        
        if tokens >= 1:
            # Consume one token
            tokens -= 1
            
            # Update bucket state
            await self.redis.hmset(bucket_key, {
                "tokens": tokens,
                "last_refill": now
            })
            await self.redis.expire(bucket_key, window * 2)
            
            return {
                "allowed": True,
                "remaining": int(tokens),
                "reset_time": now + (limit - tokens) * (window / limit)
            }
        else:
            return {
                "allowed": False,
                "remaining": 0,
                "reset_time": now + (1 - tokens) * (window / limit)
            }
    
    async def _fixed_window_check(self, key: str, limit: int, window: int) -> Dict[str, Any]:
        """Fixed window rate limiting"""
        now = time.time()
        window_start = int(now // window) * window
        window_key = f"{key}:{window_start}"
        
        current_count = await self.redis.incr(window_key)
        
        if current_count == 1:
            await self.redis.expire(window_key, window)
        
        if current_count > limit:
            return {
                "allowed": False,
                "remaining": 0,
                "reset_time": window_start + window,
                "current_count": current_count
            }
        
        return {
            "allowed": True,
            "remaining": limit - current_count,
            "reset_time": window_start + window,
            "current_count": current_count
        }

class AuthenticationManager:
    """Handle authentication and authorization"""
    
    def __init__(self, config: SecurityConfig, encryption_manager: EncryptionManager):
        self.config = config
        self.encryption = encryption_manager
        self.logger = logging.getLogger(__name__)
    
    def generate_jwt_token(
        self,
        user_id: str,
        permissions: List[str],
        expires_in: int = 3600
    ) -> str:
        """Generate JWT token"""
        payload = {
            'user_id': user_id,
            'permissions': permissions,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iss': 'mcp-system',
            'aud': 'mcp-api'
        }
        
        return jwt.encode(payload, self.config.jwt_secret, algorithm='HS256')
    
    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=['HS256'],
                audience='mcp-api',
                issuer='mcp-system'
            )
            return {'valid': True, 'payload': payload}
        
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'error': 'Token expired'}
        except jwt.InvalidTokenError as e:
            return {'valid': False, 'error': str(e)}
    
    def generate_api_key(self, user_id: str, permissions: List[str]) -> str:
        """Generate API key"""
        key_data = {
            'user_id': user_id,
            'permissions': permissions,
            'created_at': datetime.utcnow().isoformat(),
            'key_id': self.encryption.generate_secure_token(16)
        }
        
        # Encrypt the key data
        encrypted_data = self.encryption.encrypt(json.dumps(key_data))
        
        # Create API key format: mcp_<key_id>_<encrypted_data>
        return f"mcp_{key_data['key_id']}_{encrypted_data}"
    
    def verify_api_key(self, api_key: str) -> Dict[str, Any]:
        """Verify API key"""
        try:
            if not api_key.startswith('mcp_'):
                return {'valid': False, 'error': 'Invalid API key format'}
            
            parts = api_key.split('_', 2)
            if len(parts) != 3:
                return {'valid': False, 'error': 'Invalid API key format'}
            
            key_id, encrypted_data = parts[1], parts[2]
            
            # Decrypt key data
            decrypted_data = self.encryption.decrypt(encrypted_data)
            key_data = json.loads(decrypted_data)
            
            # Verify key ID matches
            if key_data['key_id'] != key_id:
                return {'valid': False, 'error': 'Invalid API key'}
            
            return {'valid': True, 'data': key_data}
        
        except Exception as e:
            self.logger.error(f"API key verification failed: {e}")
            return {'valid': False, 'error': 'Invalid API key'}
    
    def check_permissions(self, user_permissions: List[str], required_permission: str) -> bool:
        """Check if user has required permission"""
        # Admin permission grants all access
        if 'admin' in user_permissions:
            return True
        
        # Check for specific permission
        if required_permission in user_permissions:
            return True
        
        # Check for wildcard permissions
        for permission in user_permissions:
            if permission.endswith('*'):
                prefix = permission[:-1]
                if required_permission.startswith(prefix):
                    return True
        
        return False

class ThreatDetector:
    """Detect and respond to security threats"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.logger = logging.getLogger(__name__)
        
        # Threat detection rules
        self.rules = {
            'brute_force': {
                'failed_attempts_threshold': 5,
                'time_window': 300,  # 5 minutes
                'block_duration': 3600  # 1 hour
            },
            'suspicious_activity': {
                'requests_threshold': 100,
                'time_window': 60,  # 1 minute
                'investigation_duration': 1800  # 30 minutes
            },
            'data_exfiltration': {
                'data_volume_threshold': 100 * 1024 * 1024,  # 100MB
                'time_window': 300,  # 5 minutes
                'alert_threshold': 3
            }
        }
    
    async def detect_brute_force(self, ip_address: str, user_id: str = None) -> Dict[str, Any]:
        """Detect brute force attacks"""
        key = f"failed_attempts:{ip_address}"
        if user_id:
            key += f":{user_id}"
        
        # Increment failed attempts
        attempts = await self.redis.incr(key)
        
        if attempts == 1:
            # Set expiration for the key
            await self.redis.expire(key, self.rules['brute_force']['time_window'])
        
        if attempts >= self.rules['brute_force']['failed_attempts_threshold']:
            # Block the IP/user
            block_key = f"blocked:{ip_address}"
            await self.redis.setex(
                block_key,
                self.rules['brute_force']['block_duration'],
                "brute_force"
            )
            
            # Log security event
            event = SecurityEvent(
                event_id=self.encryption.generate_secure_token(16),
                timestamp=datetime.utcnow(),
                event_type=ThreatType.BRUTE_FORCE,
                severity=SecurityLevel.HIGH,
                source_ip=ip_address,
                user_id=user_id,
                details={'failed_attempts': attempts},
                action_taken='ip_blocked'
            )
            
            await self._log_security_event(event)
            
            return {
                'threat_detected': True,
                'threat_type': 'brute_force',
                'action': 'blocked',
                'duration': self.rules['brute_force']['block_duration']
            }
        
        return {'threat_detected': False}
    
    async def detect_suspicious_activity(self, ip_address: str, request_size: int = 0) -> Dict[str, Any]:
        """Detect suspicious activity patterns"""
        # Track request frequency
        freq_key = f"request_freq:{ip_address}"
        requests = await self.redis.incr(freq_key)
        
        if requests == 1:
            await self.redis.expire(freq_key, self.rules['suspicious_activity']['time_window'])
        
        # Track data volume
        volume_key = f"data_volume:{ip_address}"
        total_volume = await self.redis.incrby(volume_key, request_size)
        
        if total_volume == request_size:  # First request in window
            await self.redis.expire(volume_key, self.rules['data_exfiltration']['time_window'])
        
        threats = []
        
        # Check request frequency
        if requests >= self.rules['suspicious_activity']['requests_threshold']:
            threats.append({
                'type': 'high_frequency_requests',
                'severity': SecurityLevel.MEDIUM,
                'details': {'requests_per_minute': requests}
            })
        
        # Check data volume
        if total_volume >= self.rules['data_exfiltration']['data_volume_threshold']:
            threats.append({
                'type': 'data_exfiltration',
                'severity': SecurityLevel.HIGH,
                'details': {'data_volume_mb': total_volume / (1024 * 1024)}
            })
        
        if threats:
            # Log security events
            for threat in threats:
                event = SecurityEvent(
                    event_id=self.encryption.generate_secure_token(16),
                    timestamp=datetime.utcnow(),
                    event_type=ThreatType.DDoS if threat['type'] == 'high_frequency_requests' else ThreatType.DATA_BREACH,
                    severity=threat['severity'],
                    source_ip=ip_address,
                    details=threat['details']
                )
                await self._log_security_event(event)
            
            return {
                'threat_detected': True,
                'threats': threats,
                'action': 'monitoring'
            }
        
        return {'threat_detected': False}
    
    async def is_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked"""
        block_key = f"blocked:{ip_address}"
        return await self.redis.exists(block_key)
    
    async def _log_security_event(self, event: SecurityEvent):
        """Log security event"""
        event_data = {
            'event_id': event.event_id,
            'timestamp': event.timestamp.isoformat(),
            'event_type': event.event_type.value,
            'severity': event.severity.value,
            'source_ip': event.source_ip,
            'user_id': event.user_id,
            'details': json.dumps(event.details),
            'action_taken': event.action_taken
        }
        
        # Store in Redis for real-time monitoring
        await self.redis.lpush('security_events', json.dumps(event_data))
        await self.redis.ltrim('security_events', 0, 9999)  # Keep last 10k events
        
        # Log to file
        self.logger.warning(f"Security event: {event.event_type.value} from {event.source_ip}")

class SecurityMiddleware:
    """Security middleware for web applications"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.encryption = EncryptionManager(config.encryption_key)
        self.sanitizer = InputSanitizer()
        self.auth_manager = AuthenticationManager(config, self.encryption)
        self.logger = logging.getLogger(__name__)
    
    async def security_headers_middleware(self, request, handler):
        """Add security headers to responses"""
        response = await handler(request)
        
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response
    
    async def input_validation_middleware(self, request, handler):
        """Validate and sanitize inputs"""
        try:
            # Get request data
            if request.content_type == 'application/json':
                data = await request.json()
                sanitized_data = self._sanitize_dict(data)
                # Replace request data with sanitized version
                request._json = sanitized_data
            
            elif request.content_type == 'application/x-www-form-urlencoded':
                data = await request.post()
                sanitized_data = {k: self.sanitizer.sanitize_html(v) for k, v in data.items()}
                request._post = sanitized_data
            
            return await handler(request)
        
        except ValueError as e:
            self.logger.warning(f"Input validation failed: {e}")
            return aiohttp.web.json_response(
                {'error': 'Invalid input'},
                status=400
            )
    
    def _sanitize_dict(self, data: Dict) -> Dict:
        """Recursively sanitize dictionary data"""
        if isinstance(data, dict):
            return {k: self._sanitize_dict(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_dict(item) for item in data]
        elif isinstance(data, str):
            return self.sanitizer.sanitize_html(data)
        else:
            return data
    
    async def authentication_middleware(self, request, handler):
        """Handle authentication"""
        # Skip authentication for public endpoints
        public_endpoints = ['/health', '/docs', '/openapi.json']
        if request.path in public_endpoints:
            return await handler(request)
        
        # Get authentication token
        auth_header = request.headers.get('Authorization', '')
        api_key = request.headers.get('X-API-Key', '')
        
        user_data = None
        
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            result = self.auth_manager.verify_jwt_token(token)
            if result['valid']:
                user_data = result['payload']
        
        elif api_key:
            result = self.auth_manager.verify_api_key(api_key)
            if result['valid']:
                user_data = result['data']
        
        if not user_data:
            return aiohttp.web.json_response(
                {'error': 'Authentication required'},
                status=401
            )
        
        # Add user data to request
        request['user'] = user_data
        
        return await handler(request)

class SecurityAuditor:
    """Perform security audits and compliance checks"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def audit_database_security(self, db_connection) -> Dict[str, Any]:
        """Audit database security configuration"""
        audit_results = {
            'encryption_at_rest': False,
            'encryption_in_transit': False,
            'access_controls': False,
            'audit_logging': False,
            'backup_encryption': False,
            'recommendations': []
        }
        
        try:
            # Check for encryption settings
            if hasattr(db_connection, 'get_server_version'):
                # PostgreSQL checks
                result = await db_connection.fetch("SHOW ssl")
                if result and result[0]['ssl'] == 'on':
                    audit_results['encryption_in_transit'] = True
                else:
                    audit_results['recommendations'].append("Enable SSL/TLS for database connections")
            
            # Check for audit logging
            try:
                result = await db_connection.fetch("SHOW log_statement")
                if result and result[0]['log_statement'] != 'none':
                    audit_results['audit_logging'] = True
                else:
                    audit_results['recommendations'].append("Enable database audit logging")
            except:
                audit_results['recommendations'].append("Configure database audit logging")
            
        except Exception as e:
            self.logger.error(f"Database security audit failed: {e}")
            audit_results['recommendations'].append("Unable to complete database security audit")
        
        return audit_results
    
    async def audit_api_security(self, app_config: Dict) -> Dict[str, Any]:
        """Audit API security configuration"""
        audit_results = {
            'https_enforced': False,
            'rate_limiting': False,
            'input_validation': False,
            'authentication': False,
            'authorization': False,
            'security_headers': False,
            'recommendations': []
        }
        
        # Check HTTPS enforcement
        if app_config.get('ssl_context'):
            audit_results['https_enforced'] = True
        else:
            audit_results['recommendations'].append("Enforce HTTPS for all API endpoints")
        
        # Check rate limiting
        if app_config.get('rate_limiting'):
            audit_results['rate_limiting'] = True
        else:
            audit_results['recommendations'].append("Implement rate limiting to prevent abuse")
        
        # Check authentication
        if app_config.get('authentication_required'):
            audit_results['authentication'] = True
        else:
            audit_results['recommendations'].append("Implement authentication for API access")
        
        return audit_results
    
    async def generate_security_report(self, audit_results: List[Dict]) -> str:
        """Generate comprehensive security report"""
        report = []
        report.append("# MCP System Security Audit Report")
        report.append(f"Generated: {datetime.utcnow().isoformat()}")
        report.append("")
        
        overall_score = 0
        total_checks = 0
        
        for audit in audit_results:
            report.append(f"## {audit['component']}")
            
            passed_checks = sum(1 for k, v in audit['results'].items() 
                              if k != 'recommendations' and v)
            total_component_checks = len([k for k in audit['results'].keys() 
                                        if k != 'recommendations'])
            
            if total_component_checks > 0:
                component_score = (passed_checks / total_component_checks) * 100
                report.append(f"Security Score: {component_score:.1f}%")
                
                overall_score += component_score
                total_checks += 1
            
            report.append("")
            report.append("### Passed Checks:")
            for check, passed in audit['results'].items():
                if check != 'recommendations' and passed:
                    report.append(f"- ✅ {check.replace('_', ' ').title()}")
            
            report.append("")
            report.append("### Failed Checks:")
            for check, passed in audit['results'].items():
                if check != 'recommendations' and not passed:
                    report.append(f"- ❌ {check.replace('_', ' ').title()}")
            
            if audit['results'].get('recommendations'):
                report.append("")
                report.append("### Recommendations:")
                for rec in audit['results']['recommendations']:
                    report.append(f"- {rec}")
            
            report.append("")
        
        if total_checks > 0:
            overall_score = overall_score / total_checks
            report.insert(2, f"Overall Security Score: {overall_score:.1f}%")
            report.insert(3, "")
        
        return "\n".join(report)

# Production readiness checkers
class ProductionReadinessChecker:
    """Check if system is ready for production deployment"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def check_environment_variables(self, required_vars: List[str]) -> Dict[str, Any]:
        """Check if all required environment variables are set"""
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        return {
            'passed': len(missing_vars) == 0,
            'missing_variables': missing_vars,
            'recommendations': [
                f"Set environment variable: {var}" for var in missing_vars
            ] if missing_vars else []
        }
    
    async def check_ssl_configuration(self, ssl_config: Dict) -> Dict[str, Any]:
        """Check SSL/TLS configuration"""
        issues = []
        
        if not ssl_config.get('cert_file'):
            issues.append("SSL certificate file not configured")
        
        if not ssl_config.get('key_file'):
            issues.append("SSL private key file not configured")
        
        if ssl_config.get('ssl_version', '').lower() in ['sslv2', 'sslv3', 'tlsv1', 'tlsv1.1']:
            issues.append("Insecure SSL/TLS version configured")
        
        return {
            'passed': len(issues) == 0,
            'issues': issues,
            'recommendations': [
                "Use TLS 1.2 or higher",
                "Ensure certificate is from trusted CA",
                "Configure proper cipher suites"
            ] if issues else []
        }
    
    async def check_database_configuration(self, db_config: Dict) -> Dict[str, Any]:
        """Check database configuration for production"""
        issues = []
        
        if db_config.get('host') in ['localhost', '127.0.0.1']:
            issues.append("Database host should not be localhost in production")
        
        if not db_config.get('ssl_mode') or db_config['ssl_mode'] == 'disable':
            issues.append("Database SSL should be enabled")
        
        if not db_config.get('backup_enabled'):
            issues.append("Database backups should be enabled")
        
        return {
            'passed': len(issues) == 0,
            'issues': issues,
            'recommendations': [
                "Use managed database service",
                "Enable automated backups",
                "Configure connection pooling",
                "Set up monitoring and alerting"
            ] if issues else []
        }

# Example usage and configuration
async def setup_security():
    """Setup comprehensive security for MCP System"""
    
    # Security configuration
    config = SecurityConfig(
        encryption_key=os.getenv('ENCRYPTION_KEY', 'default-key-change-in-production'),
        jwt_secret=os.getenv('JWT_SECRET', 'default-secret-change-in-production'),
        password_policy={
            'min_length': 12,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_numbers': True,
            'require_special_chars': True,
            'max_age_days': 90
        },
        rate_limiting={
            'default_limit': 100,
            'default_window': 3600,
            'strategy': 'sliding_window'
        },
        cors_settings={
            'allowed_origins': ['https://yourdomain.com'],
            'allowed_methods': ['GET', 'POST', 'PUT', 'DELETE'],
            'allowed_headers': ['Content-Type', 'Authorization'],
            'max_age': 3600
        }
    )
    
    # Initialize security components
    encryption_manager = EncryptionManager(config.encryption_key)
    input_sanitizer = InputSanitizer()
    auth_manager = AuthenticationManager(config, encryption_manager)
    
    # Redis for rate limiting and threat detection
    redis_client = await aioredis.from_url('redis://localhost:6379')
    rate_limiter = RateLimiter(redis_client)
    threat_detector = ThreatDetector(redis_client)
    
    # Security middleware
    security_middleware = SecurityMiddleware(config)
    
    return {
        'config': config,
        'encryption': encryption_manager,
        'sanitizer': input_sanitizer,
        'auth': auth_manager,
        'rate_limiter': rate_limiter,
        'threat_detector': threat_detector,
        'middleware': security_middleware
    }

if __name__ == "__main__":
    async def main():
        # Setup security
        security = await setup_security()
        
        # Example: Generate API key
        api_key = security['auth'].generate_api_key('user123', ['read', 'write'])
        print(f"Generated API key: {api_key[:50]}...")
        
        # Example: Verify API key
        result = security['auth'].verify_api_key(api_key)
        print(f"API key valid: {result['valid']}")
        
        # Example: Check rate limit
        rate_result = await security['rate_limiter'].check_rate_limit(
            'user123', limit=10, window=60
        )
        print(f"Rate limit check: {rate_result}")
        
        # Example: Security audit
        auditor = SecurityAuditor()
        api_audit = await auditor.audit_api_security({
            'ssl_context': True,
            'rate_limiting': True,
            'authentication_required': True
        })
        print(f"API security audit: {api_audit}")
    
    asyncio.run(main())

