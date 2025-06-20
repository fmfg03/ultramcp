#!/usr/bin/env python3
"""
SAM Enterprise Authentication and Security System
Sistema avanzado de autenticación y seguridad enterprise para SAM
"""

import asyncio
import jwt
import bcrypt
import secrets
import hashlib
import hmac
import time
import uuid
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import sqlite3
import aiohttp
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import base64
import os
from functools import wraps
import ipaddress
from urllib.parse import urlparse
import threading
from collections import defaultdict, deque

class AuthenticationMethod(Enum):
    """Métodos de autenticación soportados"""
    API_KEY = "api_key"
    JWT_TOKEN = "jwt_token"
    OAUTH2 = "oauth2"
    HMAC_SIGNATURE = "hmac_signature"
    MUTUAL_TLS = "mutual_tls"
    BEARER_TOKEN = "bearer_token"

class UserRole(Enum):
    """Roles de usuario en el sistema"""
    ADMIN = "admin"
    OPERATOR = "operator"
    AGENT = "agent"
    SERVICE = "service"
    READONLY = "readonly"
    GUEST = "guest"

class PermissionLevel(Enum):
    """Niveles de permisos"""
    FULL_ACCESS = "full_access"
    READ_WRITE = "read_write"
    READ_ONLY = "read_only"
    EXECUTE_ONLY = "execute_only"
    NO_ACCESS = "no_access"

class SecurityEvent(Enum):
    """Tipos de eventos de seguridad"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    TOKEN_ISSUED = "token_issued"
    TOKEN_EXPIRED = "token_expired"
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SECURITY_VIOLATION = "security_violation"

@dataclass
class User:
    """Usuario del sistema"""
    user_id: str
    username: str
    email: str
    password_hash: str
    role: UserRole
    permissions: List[str]
    api_keys: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_login: Optional[str] = None
    failed_login_attempts: int = 0
    locked_until: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class APIKey:
    """Clave API"""
    key_id: str
    user_id: str
    key_hash: str
    name: str
    permissions: List[str]
    expires_at: Optional[str] = None
    last_used: Optional[str] = None
    usage_count: int = 0
    rate_limit: int = 1000  # requests per hour
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class JWTClaims:
    """Claims del JWT"""
    user_id: str
    username: str
    role: str
    permissions: List[str]
    issued_at: int
    expires_at: int
    issuer: str = "sam_enterprise"
    audience: str = "mcp_system"

@dataclass
class SecurityAuditLog:
    """Log de auditoría de seguridad"""
    log_id: str
    event_type: SecurityEvent
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    endpoint: str
    success: bool
    details: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class RateLimiter:
    """Rate limiter avanzado"""
    
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()
    
    def is_allowed(self, 
                   identifier: str, 
                   limit: int, 
                   window: int = 3600) -> Tuple[bool, Dict[str, Any]]:
        """Verificar si la request está permitida"""
        with self.lock:
            now = time.time()
            window_start = now - window
            
            # Limpiar requests antiguas
            while self.requests[identifier] and self.requests[identifier][0] < window_start:
                self.requests[identifier].popleft()
            
            current_count = len(self.requests[identifier])
            
            if current_count >= limit:
                # Calcular tiempo hasta que se permita la siguiente request
                oldest_request = self.requests[identifier][0]
                reset_time = oldest_request + window
                
                return False, {
                    "allowed": False,
                    "current_count": current_count,
                    "limit": limit,
                    "window": window,
                    "reset_time": reset_time,
                    "retry_after": int(reset_time - now)
                }
            
            # Registrar nueva request
            self.requests[identifier].append(now)
            
            return True, {
                "allowed": True,
                "current_count": current_count + 1,
                "limit": limit,
                "window": window,
                "remaining": limit - current_count - 1
            }

class PasswordManager:
    """Gestor de contraseñas seguro"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash de contraseña con bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verificar contraseña"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """Generar contraseña segura"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
        """Validar fortaleza de contraseña"""
        issues = []
        
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            issues.append("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Password must contain at least one special character")
        
        return len(issues) == 0, issues

class CryptographyManager:
    """Gestor de criptografía"""
    
    def __init__(self, master_key: Optional[bytes] = None):
        if master_key:
            self.fernet = Fernet(master_key)
        else:
            # Generar clave maestra
            key = Fernet.generate_key()
            self.fernet = Fernet(key)
            
        # Generar par de claves RSA para firmas
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
    
    def encrypt_data(self, data: str) -> str:
        """Encriptar datos"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Desencriptar datos"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    def sign_data(self, data: str) -> str:
        """Firmar datos con clave privada"""
        signature = self.private_key.sign(
            data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode()
    
    def verify_signature(self, data: str, signature: str) -> bool:
        """Verificar firma con clave pública"""
        try:
            signature_bytes = base64.b64decode(signature.encode())
            self.public_key.verify(
                signature_bytes,
                data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
    
    def generate_hmac(self, data: str, secret: str) -> str:
        """Generar HMAC"""
        return hmac.new(
            secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify_hmac(self, data: str, signature: str, secret: str) -> bool:
        """Verificar HMAC"""
        expected = self.generate_hmac(data, secret)
        return hmac.compare_digest(expected, signature)

class JWTManager:
    """Gestor de tokens JWT"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.default_expiry = 3600  # 1 hora
    
    def create_token(self, 
                    user: User, 
                    expires_in: Optional[int] = None) -> str:
        """Crear token JWT"""
        now = int(time.time())
        expires_in = expires_in or self.default_expiry
        
        claims = JWTClaims(
            user_id=user.user_id,
            username=user.username,
            role=user.role.value,
            permissions=user.permissions,
            issued_at=now,
            expires_at=now + expires_in
        )
        
        payload = asdict(claims)
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[JWTClaims]:
        """Verificar y decodificar token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return JWTClaims(**payload)
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def refresh_token(self, token: str) -> Optional[str]:
        """Refrescar token JWT"""
        claims = self.verify_token(token)
        if not claims:
            return None
        
        # Crear nuevo token con mismos claims pero nueva expiración
        now = int(time.time())
        claims.issued_at = now
        claims.expires_at = now + self.default_expiry
        
        payload = asdict(claims)
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

class SecurityAuditor:
    """Auditor de seguridad"""
    
    def __init__(self, db_path: str = "/tmp/sam_security_audit.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Inicializar base de datos de auditoría"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS security_audit_logs (
                    log_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    user_id TEXT,
                    ip_address TEXT NOT NULL,
                    user_agent TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    details TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            
            # Índices para consultas eficientes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON security_audit_logs(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON security_audit_logs(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON security_audit_logs(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ip_address ON security_audit_logs(ip_address)")
    
    def log_security_event(self, 
                          event_type: SecurityEvent,
                          ip_address: str,
                          user_agent: str,
                          endpoint: str,
                          success: bool,
                          user_id: Optional[str] = None,
                          details: Optional[Dict[str, Any]] = None):
        """Registrar evento de seguridad"""
        try:
            audit_log = SecurityAuditLog(
                log_id=str(uuid.uuid4()),
                event_type=event_type,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                endpoint=endpoint,
                success=success,
                details=details or {}
            )
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO security_audit_logs 
                    (log_id, event_type, user_id, ip_address, user_agent, 
                     endpoint, success, details, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    audit_log.log_id,
                    audit_log.event_type.value,
                    audit_log.user_id,
                    audit_log.ip_address,
                    audit_log.user_agent,
                    audit_log.endpoint,
                    audit_log.success,
                    json.dumps(audit_log.details),
                    audit_log.timestamp
                ))
            
            # Log crítico para eventos de seguridad importantes
            if event_type in [SecurityEvent.SECURITY_VIOLATION, SecurityEvent.SUSPICIOUS_ACTIVITY]:
                self.logger.critical(f"Security event: {event_type.value} from {ip_address}")
                
        except Exception as e:
            self.logger.error(f"Error logging security event: {e}")
    
    def get_security_events(self,
                           event_type: Optional[SecurityEvent] = None,
                           user_id: Optional[str] = None,
                           start_time: Optional[str] = None,
                           end_time: Optional[str] = None,
                           limit: int = 100) -> List[SecurityAuditLog]:
        """Obtener eventos de seguridad"""
        try:
            query = "SELECT * FROM security_audit_logs WHERE 1=1"
            params = []
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type.value)
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, params)
                
                events = []
                for row in cursor.fetchall():
                    event = SecurityAuditLog(
                        log_id=row[0],
                        event_type=SecurityEvent(row[1]),
                        user_id=row[2],
                        ip_address=row[3],
                        user_agent=row[4],
                        endpoint=row[5],
                        success=bool(row[6]),
                        details=json.loads(row[7]),
                        timestamp=row[8]
                    )
                    events.append(event)
                
                return events
                
        except Exception as e:
            self.logger.error(f"Error getting security events: {e}")
            return []
    
    def detect_suspicious_activity(self, ip_address: str, time_window: int = 300) -> bool:
        """Detectar actividad sospechosa"""
        try:
            # Buscar múltiples fallos de login en ventana de tiempo
            start_time = (datetime.now() - timedelta(seconds=time_window)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM security_audit_logs 
                    WHERE ip_address = ? AND event_type = ? AND success = FALSE 
                    AND timestamp >= ?
                """, (ip_address, SecurityEvent.LOGIN_FAILURE.value, start_time))
                
                failure_count = cursor.fetchone()[0]
                
                # Más de 5 fallos en 5 minutos es sospechoso
                if failure_count > 5:
                    self.log_security_event(
                        SecurityEvent.SUSPICIOUS_ACTIVITY,
                        ip_address,
                        "system",
                        "security_monitor",
                        True,
                        details={"failure_count": failure_count, "time_window": time_window}
                    )
                    return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"Error detecting suspicious activity: {e}")
            return False

class AuthenticationManager:
    """Gestor principal de autenticación"""
    
    def __init__(self, 
                 db_path: str = "/tmp/sam_auth.db",
                 jwt_secret: Optional[str] = None):
        
        self.db_path = db_path
        self.jwt_secret = jwt_secret or secrets.token_urlsafe(32)
        
        # Componentes de seguridad
        self.password_manager = PasswordManager()
        self.crypto_manager = CryptographyManager()
        self.jwt_manager = JWTManager(self.jwt_secret)
        self.rate_limiter = RateLimiter()
        self.security_auditor = SecurityAuditor()
        
        self.logger = logging.getLogger(__name__)
        self._init_database()
        
        # Configuración de seguridad
        self.max_login_attempts = 5
        self.lockout_duration = 900  # 15 minutos
        self.session_timeout = 3600  # 1 hora
        
        # IPs permitidas (whitelist)
        self.allowed_ips: List[str] = []
        
        # IPs bloqueadas (blacklist)
        self.blocked_ips: List[str] = []
    
    def _init_database(self):
        """Inicializar base de datos de autenticación"""
        with sqlite3.connect(self.db_path) as conn:
            # Tabla de usuarios
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    permissions TEXT NOT NULL,
                    api_keys TEXT DEFAULT '[]',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TEXT NOT NULL,
                    last_login TEXT,
                    failed_login_attempts INTEGER DEFAULT 0,
                    locked_until TEXT,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Tabla de claves API
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    key_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    key_hash TEXT NOT NULL,
                    name TEXT NOT NULL,
                    permissions TEXT NOT NULL,
                    expires_at TEXT,
                    last_used TEXT,
                    usage_count INTEGER DEFAULT 0,
                    rate_limit INTEGER DEFAULT 1000,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Tabla de sesiones activas
            conn.execute("""
                CREATE TABLE IF NOT EXISTS active_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token_hash TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    user_agent TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    last_activity TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Índices
            conn.execute("CREATE INDEX IF NOT EXISTS idx_username ON users(username)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_email ON users(email)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_api_key_hash ON api_keys(key_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session_token ON active_sessions(token_hash)")
    
    async def create_user(self,
                         username: str,
                         email: str,
                         password: str,
                         role: UserRole,
                         permissions: List[str]) -> Optional[User]:
        """Crear nuevo usuario"""
        try:
            # Validar fortaleza de contraseña
            is_strong, issues = self.password_manager.validate_password_strength(password)
            if not is_strong:
                raise ValueError(f"Password validation failed: {', '.join(issues)}")
            
            # Hash de contraseña
            password_hash = self.password_manager.hash_password(password)
            
            # Crear usuario
            user = User(
                user_id=str(uuid.uuid4()),
                username=username,
                email=email,
                password_hash=password_hash,
                role=role,
                permissions=permissions
            )
            
            # Persistir en base de datos
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO users 
                    (user_id, username, email, password_hash, role, permissions,
                     api_keys, is_active, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user.user_id,
                    user.username,
                    user.email,
                    user.password_hash,
                    user.role.value,
                    json.dumps(user.permissions),
                    json.dumps(user.api_keys),
                    user.is_active,
                    user.created_at,
                    json.dumps(user.metadata)
                ))
            
            self.logger.info(f"User created: {username}")
            return user
            
        except Exception as e:
            self.logger.error(f"Error creating user {username}: {e}")
            return None
    
    async def authenticate_user(self,
                               username: str,
                               password: str,
                               ip_address: str,
                               user_agent: str) -> Optional[str]:
        """Autenticar usuario y devolver token JWT"""
        try:
            # Verificar IP bloqueada
            if self._is_ip_blocked(ip_address):
                self.security_auditor.log_security_event(
                    SecurityEvent.LOGIN_FAILURE,
                    ip_address,
                    user_agent,
                    "/auth/login",
                    False,
                    details={"reason": "IP blocked"}
                )
                return None
            
            # Detectar actividad sospechosa
            if self.security_auditor.detect_suspicious_activity(ip_address):
                self._block_ip(ip_address)
                return None
            
            # Buscar usuario
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT user_id, username, email, password_hash, role, permissions,
                           is_active, failed_login_attempts, locked_until
                    FROM users WHERE username = ?
                """, (username,))
                
                row = cursor.fetchone()
                if not row:
                    self.security_auditor.log_security_event(
                        SecurityEvent.LOGIN_FAILURE,
                        ip_address,
                        user_agent,
                        "/auth/login",
                        False,
                        details={"reason": "User not found"}
                    )
                    return None
                
                user_id, username, email, password_hash, role, permissions, is_active, failed_attempts, locked_until = row
                
                # Verificar si el usuario está activo
                if not is_active:
                    self.security_auditor.log_security_event(
                        SecurityEvent.LOGIN_FAILURE,
                        ip_address,
                        user_agent,
                        "/auth/login",
                        False,
                        user_id=user_id,
                        details={"reason": "User inactive"}
                    )
                    return None
                
                # Verificar si el usuario está bloqueado
                if locked_until:
                    locked_until_dt = datetime.fromisoformat(locked_until)
                    if datetime.now() < locked_until_dt:
                        self.security_auditor.log_security_event(
                            SecurityEvent.LOGIN_FAILURE,
                            ip_address,
                            user_agent,
                            "/auth/login",
                            False,
                            user_id=user_id,
                            details={"reason": "User locked"}
                        )
                        return None
                    else:
                        # Desbloquear usuario
                        conn.execute("""
                            UPDATE users SET locked_until = NULL, failed_login_attempts = 0
                            WHERE user_id = ?
                        """, (user_id,))
                
                # Verificar contraseña
                if not self.password_manager.verify_password(password, password_hash):
                    # Incrementar intentos fallidos
                    failed_attempts += 1
                    
                    # Bloquear usuario si excede intentos máximos
                    locked_until_new = None
                    if failed_attempts >= self.max_login_attempts:
                        locked_until_new = (datetime.now() + timedelta(seconds=self.lockout_duration)).isoformat()
                    
                    conn.execute("""
                        UPDATE users SET failed_login_attempts = ?, locked_until = ?
                        WHERE user_id = ?
                    """, (failed_attempts, locked_until_new, user_id))
                    
                    self.security_auditor.log_security_event(
                        SecurityEvent.LOGIN_FAILURE,
                        ip_address,
                        user_agent,
                        "/auth/login",
                        False,
                        user_id=user_id,
                        details={"reason": "Invalid password", "failed_attempts": failed_attempts}
                    )
                    return None
                
                # Login exitoso
                user = User(
                    user_id=user_id,
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    role=UserRole(role),
                    permissions=json.loads(permissions)
                )
                
                # Resetear intentos fallidos y actualizar último login
                conn.execute("""
                    UPDATE users SET failed_login_attempts = 0, locked_until = NULL, last_login = ?
                    WHERE user_id = ?
                """, (datetime.now().isoformat(), user_id))
                
                # Crear token JWT
                token = self.jwt_manager.create_token(user)
                
                # Registrar sesión activa
                session_id = str(uuid.uuid4())
                token_hash = hashlib.sha256(token.encode()).hexdigest()
                expires_at = (datetime.now() + timedelta(seconds=self.session_timeout)).isoformat()
                
                conn.execute("""
                    INSERT INTO active_sessions 
                    (session_id, user_id, token_hash, ip_address, user_agent,
                     created_at, expires_at, last_activity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    user_id,
                    token_hash,
                    ip_address,
                    user_agent,
                    datetime.now().isoformat(),
                    expires_at,
                    datetime.now().isoformat()
                ))
                
                # Log de éxito
                self.security_auditor.log_security_event(
                    SecurityEvent.LOGIN_SUCCESS,
                    ip_address,
                    user_agent,
                    "/auth/login",
                    True,
                    user_id=user_id
                )
                
                self.security_auditor.log_security_event(
                    SecurityEvent.TOKEN_ISSUED,
                    ip_address,
                    user_agent,
                    "/auth/login",
                    True,
                    user_id=user_id,
                    details={"session_id": session_id}
                )
                
                return token
                
        except Exception as e:
            self.logger.error(f"Error authenticating user {username}: {e}")
            return None
    
    async def verify_token(self, token: str) -> Optional[JWTClaims]:
        """Verificar token JWT"""
        try:
            claims = self.jwt_manager.verify_token(token)
            if not claims:
                return None
            
            # Verificar que la sesión esté activa
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT session_id, expires_at FROM active_sessions 
                    WHERE token_hash = ?
                """, (token_hash,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                session_id, expires_at = row
                
                # Verificar expiración de sesión
                if datetime.now() > datetime.fromisoformat(expires_at):
                    # Eliminar sesión expirada
                    conn.execute("DELETE FROM active_sessions WHERE session_id = ?", (session_id,))
                    return None
                
                # Actualizar última actividad
                conn.execute("""
                    UPDATE active_sessions SET last_activity = ?
                    WHERE session_id = ?
                """, (datetime.now().isoformat(), session_id))
            
            return claims
            
        except Exception as e:
            self.logger.error(f"Error verifying token: {e}")
            return None
    
    async def create_api_key(self,
                            user_id: str,
                            name: str,
                            permissions: List[str],
                            expires_in: Optional[int] = None,
                            rate_limit: int = 1000) -> Optional[Tuple[str, APIKey]]:
        """Crear clave API"""
        try:
            # Generar clave API
            api_key = f"sam_{secrets.token_urlsafe(32)}"
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Calcular expiración
            expires_at = None
            if expires_in:
                expires_at = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
            
            # Crear objeto APIKey
            api_key_obj = APIKey(
                key_id=str(uuid.uuid4()),
                user_id=user_id,
                key_hash=key_hash,
                name=name,
                permissions=permissions,
                expires_at=expires_at,
                rate_limit=rate_limit
            )
            
            # Persistir en base de datos
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO api_keys 
                    (key_id, user_id, key_hash, name, permissions, expires_at,
                     rate_limit, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    api_key_obj.key_id,
                    api_key_obj.user_id,
                    api_key_obj.key_hash,
                    api_key_obj.name,
                    json.dumps(api_key_obj.permissions),
                    api_key_obj.expires_at,
                    api_key_obj.rate_limit,
                    api_key_obj.is_active,
                    api_key_obj.created_at
                ))
            
            self.logger.info(f"API key created for user {user_id}: {name}")
            return api_key, api_key_obj
            
        except Exception as e:
            self.logger.error(f"Error creating API key: {e}")
            return None
    
    async def verify_api_key(self, api_key: str, ip_address: str) -> Optional[APIKey]:
        """Verificar clave API"""
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT key_id, user_id, name, permissions, expires_at,
                           last_used, usage_count, rate_limit, is_active
                    FROM api_keys WHERE key_hash = ?
                """, (key_hash,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                key_id, user_id, name, permissions, expires_at, last_used, usage_count, rate_limit, is_active = row
                
                # Verificar si está activa
                if not is_active:
                    return None
                
                # Verificar expiración
                if expires_at and datetime.now() > datetime.fromisoformat(expires_at):
                    return None
                
                # Verificar rate limit
                allowed, rate_info = self.rate_limiter.is_allowed(f"api_key_{key_id}", rate_limit)
                if not allowed:
                    return None
                
                # Actualizar estadísticas de uso
                conn.execute("""
                    UPDATE api_keys SET last_used = ?, usage_count = usage_count + 1
                    WHERE key_id = ?
                """, (datetime.now().isoformat(), key_id))
                
                return APIKey(
                    key_id=key_id,
                    user_id=user_id,
                    key_hash=key_hash,
                    name=name,
                    permissions=json.loads(permissions),
                    expires_at=expires_at,
                    last_used=datetime.now().isoformat(),
                    usage_count=usage_count + 1,
                    rate_limit=rate_limit,
                    is_active=is_active
                )
                
        except Exception as e:
            self.logger.error(f"Error verifying API key: {e}")
            return None
    
    def _is_ip_blocked(self, ip_address: str) -> bool:
        """Verificar si IP está bloqueada"""
        return ip_address in self.blocked_ips
    
    def _block_ip(self, ip_address: str):
        """Bloquear IP"""
        if ip_address not in self.blocked_ips:
            self.blocked_ips.append(ip_address)
            self.logger.warning(f"IP blocked: {ip_address}")
    
    def _unblock_ip(self, ip_address: str):
        """Desbloquear IP"""
        if ip_address in self.blocked_ips:
            self.blocked_ips.remove(ip_address)
            self.logger.info(f"IP unblocked: {ip_address}")
    
    def check_permission(self, user_permissions: List[str], required_permission: str) -> bool:
        """Verificar permisos"""
        return required_permission in user_permissions or "admin" in user_permissions
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de seguridad"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Estadísticas de usuarios
                cursor = conn.execute("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
                active_users = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM users WHERE locked_until IS NOT NULL")
                locked_users = cursor.fetchone()[0]
                
                # Estadísticas de sesiones
                cursor = conn.execute("SELECT COUNT(*) FROM active_sessions WHERE expires_at > ?", 
                                    (datetime.now().isoformat(),))
                active_sessions = cursor.fetchone()[0]
                
                # Estadísticas de API keys
                cursor = conn.execute("SELECT COUNT(*) FROM api_keys WHERE is_active = TRUE")
                active_api_keys = cursor.fetchone()[0]
                
                return {
                    "active_users": active_users,
                    "locked_users": locked_users,
                    "active_sessions": active_sessions,
                    "active_api_keys": active_api_keys,
                    "blocked_ips": len(self.blocked_ips),
                    "allowed_ips": len(self.allowed_ips)
                }
                
        except Exception as e:
            self.logger.error(f"Error getting security stats: {e}")
            return {}

# Instancia global del gestor de autenticación
auth_manager = AuthenticationManager()

# Decorador para autenticación
def require_auth(permission: Optional[str] = None):
    """Decorador para requerir autenticación"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extraer token del header Authorization
            # En implementación real, esto vendría del framework web
            token = kwargs.get('auth_token')
            if not token:
                raise PermissionError("Authentication required")
            
            # Verificar token
            claims = await auth_manager.verify_token(token)
            if not claims:
                raise PermissionError("Invalid or expired token")
            
            # Verificar permisos si se especifican
            if permission and not auth_manager.check_permission(claims.permissions, permission):
                raise PermissionError(f"Permission '{permission}' required")
            
            # Añadir claims al contexto
            kwargs['user_claims'] = claims
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ejemplo de uso
    async def demo():
        # Crear usuario administrador
        admin_user = await auth_manager.create_user(
            username="admin",
            email="admin@sam-enterprise.com",
            password="SecurePassword123!",
            role=UserRole.ADMIN,
            permissions=["admin", "read", "write", "execute"]
        )
        
        if admin_user:
            print(f"Admin user created: {admin_user.username}")
            
            # Autenticar usuario
            token = await auth_manager.authenticate_user(
                username="admin",
                password="SecurePassword123!",
                ip_address="127.0.0.1",
                user_agent="SAM-Client/1.0"
            )
            
            if token:
                print(f"Authentication successful, token: {token[:50]}...")
                
                # Verificar token
                claims = await auth_manager.verify_token(token)
                if claims:
                    print(f"Token verified for user: {claims.username}")
                
                # Crear API key
                api_key_result = await auth_manager.create_api_key(
                    user_id=admin_user.user_id,
                    name="Test API Key",
                    permissions=["read", "write"],
                    expires_in=86400  # 24 horas
                )
                
                if api_key_result:
                    api_key, api_key_obj = api_key_result
                    print(f"API key created: {api_key[:20]}...")
                    
                    # Verificar API key
                    verified_key = await auth_manager.verify_api_key(api_key, "127.0.0.1")
                    if verified_key:
                        print(f"API key verified: {verified_key.name}")
        
        # Mostrar estadísticas de seguridad
        stats = auth_manager.get_security_stats()
        print(f"Security stats: {json.dumps(stats, indent=2)}")
    
    # Ejecutar demo
    asyncio.run(demo())

