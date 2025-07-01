from datetime import datetime
#!/usr/bin/env python3
"""
MCP Enterprise Secrets Management System
Sistema seguro de gestión de secretos y variables de entorno
"""

import os
import json
import base64
import hashlib
import secrets
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import boto3
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
import hvac  # HashiCorp Vault client

class SecretsManager:
    """Gestor centralizado de secretos para MCP Enterprise"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.backend = config.get('backend', 'local')  # local, aws, azure, vault
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Inicializar backend específico
        if self.backend == 'aws':
            self.aws_client = boto3.client('secretsmanager')
        elif self.backend == 'azure':
            self.azure_client = SecretClient(
                vault_url=config['azure_vault_url'],
                credential=DefaultAzureCredential()
            )
        elif self.backend == 'vault':
            self.vault_client = hvac.Client(url=config['vault_url'])
            if config.get('vault_token'):
                self.vault_client.token = config['vault_token']
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Obtiene o crea la clave de encriptación maestra"""
        key_file = self.config.get('key_file', '/etc/mcp/master.key')
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generar nueva clave
            password = self.config.get('master_password', '').encode()
            if not password:
                # Generar password aleatorio si no se proporciona
                password = secrets.token_urlsafe(32).encode()
                print(f"Generated master password: {password.decode()}")
            
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            
            # Guardar clave
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)
            
            return key
    
    def store_secret(self, name: str, value: str, metadata: Optional[Dict] = None) -> bool:
        """Almacena un secreto de forma segura"""
        try:
            if self.backend == 'local':
                return self._store_local(name, value, metadata)
            elif self.backend == 'aws':
                return self._store_aws(name, value, metadata)
            elif self.backend == 'azure':
                return self._store_azure(name, value, metadata)
            elif self.backend == 'vault':
                return self._store_vault(name, value, metadata)
            else:
                raise ValueError(f"Backend no soportado: {self.backend}")
        except Exception as e:
            print(f"Error storing secret {name}: {e}")
            return False
    
    def get_secret(self, name: str) -> Optional[str]:
        """Recupera un secreto"""
        try:
            if self.backend == 'local':
                return self._get_local(name)
            elif self.backend == 'aws':
                return self._get_aws(name)
            elif self.backend == 'azure':
                return self._get_azure(name)
            elif self.backend == 'vault':
                return self._get_vault(name)
            else:
                raise ValueError(f"Backend no soportado: {self.backend}")
        except Exception as e:
            print(f"Error retrieving secret {name}: {e}")
            return None
    
    def delete_secret(self, name: str) -> bool:
        """Elimina un secreto"""
        try:
            if self.backend == 'local':
                return self._delete_local(name)
            elif self.backend == 'aws':
                return self._delete_aws(name)
            elif self.backend == 'azure':
                return self._delete_azure(name)
            elif self.backend == 'vault':
                return self._delete_vault(name)
            else:
                raise ValueError(f"Backend no soportado: {self.backend}")
        except Exception as e:
            print(f"Error deleting secret {name}: {e}")
            return False
    
    def list_secrets(self) -> list:
        """Lista todos los secretos disponibles"""
        try:
            if self.backend == 'local':
                return self._list_local()
            elif self.backend == 'aws':
                return self._list_aws()
            elif self.backend == 'azure':
                return self._list_azure()
            elif self.backend == 'vault':
                return self._list_vault()
            else:
                raise ValueError(f"Backend no soportado: {self.backend}")
        except Exception as e:
            print(f"Error listing secrets: {e}")
            return []
    
    # Implementaciones específicas por backend
    
    def _store_local(self, name: str, value: str, metadata: Optional[Dict] = None) -> bool:
        """Almacena secreto localmente encriptado"""
        secrets_dir = self.config.get('secrets_dir', '/etc/mcp/secrets')
        os.makedirs(secrets_dir, exist_ok=True)
        
        # Encriptar valor
        encrypted_value = self.cipher.encrypt(value.encode())
        
        # Preparar datos
        secret_data = {
            'value': base64.b64encode(encrypted_value).decode(),
            'metadata': metadata or {},
            'created_at': str(datetime.now()),
            'hash': hashlib.sha256(value.encode()).hexdigest()
        }
        
        # Guardar archivo
        secret_file = os.path.join(secrets_dir, f"{name}.json")
        with open(secret_file, 'w') as f:
            json.dump(secret_data, f, indent=2)
        os.chmod(secret_file, 0o600)
        
        return True
    
    def _get_local(self, name: str) -> Optional[str]:
        """Recupera secreto local"""
        secrets_dir = self.config.get('secrets_dir', '/etc/mcp/secrets')
        secret_file = os.path.join(secrets_dir, f"{name}.json")
        
        if not os.path.exists(secret_file):
            return None
        
        with open(secret_file, 'r') as f:
            secret_data = json.load(f)
        
        # Desencriptar
        encrypted_value = base64.b64decode(secret_data['value'])
        decrypted_value = self.cipher.decrypt(encrypted_value)
        
        return decrypted_value.decode()
    
    def _delete_local(self, name: str) -> bool:
        """Elimina secreto local"""
        secrets_dir = self.config.get('secrets_dir', '/etc/mcp/secrets')
        secret_file = os.path.join(secrets_dir, f"{name}.json")
        
        if os.path.exists(secret_file):
            os.remove(secret_file)
            return True
        return False
    
    def _list_local(self) -> list:
        """Lista secretos locales"""
        secrets_dir = self.config.get('secrets_dir', '/etc/mcp/secrets')
        if not os.path.exists(secrets_dir):
            return []
        
        secrets = []
        for file in os.listdir(secrets_dir):
            if file.endswith('.json'):
                name = file[:-5]  # Remove .json extension
                secrets.append(name)
        
        return secrets
    
    def _store_aws(self, name: str, value: str, metadata: Optional[Dict] = None) -> bool:
        """Almacena secreto en AWS Secrets Manager"""
        try:
            self.aws_client.create_secret(
                Name=name,
                SecretString=value,
                Description=metadata.get('description', '') if metadata else ''
            )
            return True
        except self.aws_client.exceptions.ResourceExistsException:
            # Actualizar secreto existente
            self.aws_client.update_secret(
                SecretId=name,
                SecretString=value
            )
            return True
    
    def _get_aws(self, name: str) -> Optional[str]:
        """Recupera secreto de AWS"""
        try:
            response = self.aws_client.get_secret_value(SecretId=name)
            return response['SecretString']
        except self.aws_client.exceptions.ResourceNotFoundException:
            return None
    
    def _delete_aws(self, name: str) -> bool:
        """Elimina secreto de AWS"""
        try:
            self.aws_client.delete_secret(
                SecretId=name,
                ForceDeleteWithoutRecovery=True
            )
            return True
        except self.aws_client.exceptions.ResourceNotFoundException:
            return False
    
    def _list_aws(self) -> list:
        """Lista secretos de AWS"""
        try:
            response = self.aws_client.list_secrets()
            return [secret['Name'] for secret in response['SecretList']]
        except Exception:
            return []
    
    def _store_azure(self, name: str, value: str, metadata: Optional[Dict] = None) -> bool:
        """Almacena secreto en Azure Key Vault"""
        try:
            self.azure_client.set_secret(name, value)
            return True
        except Exception:
            return False
    
    def _get_azure(self, name: str) -> Optional[str]:
        """Recupera secreto de Azure"""
        try:
            secret = self.azure_client.get_secret(name)
            return secret.value
        except Exception:
            return None
    
    def _delete_azure(self, name: str) -> bool:
        """Elimina secreto de Azure"""
        try:
            self.azure_client.begin_delete_secret(name)
            return True
        except Exception:
            return False
    
    def _list_azure(self) -> list:
        """Lista secretos de Azure"""
        try:
            secrets = self.azure_client.list_properties_of_secrets()
            return [secret.name for secret in secrets]
        except Exception:
            return []
    
    def _store_vault(self, name: str, value: str, metadata: Optional[Dict] = None) -> bool:
        """Almacena secreto en HashiCorp Vault"""
        try:
            secret_data = {'value': value}
            if metadata:
                secret_data.update(metadata)
            
            self.vault_client.secrets.kv.v2.create_or_update_secret(
                path=name,
                secret=secret_data
            )
            return True
        except Exception:
            return False
    
    def _get_vault(self, name: str) -> Optional[str]:
        """Recupera secreto de Vault"""
        try:
            response = self.vault_client.secrets.kv.v2.read_secret_version(path=name)
            return response['data']['data']['value']
        except Exception:
            return None
    
    def _delete_vault(self, name: str) -> bool:
        """Elimina secreto de Vault"""
        try:
            self.vault_client.secrets.kv.v2.delete_metadata_and_all_versions(path=name)
            return True
        except Exception:
            return False
    
    def _list_vault(self) -> list:
        """Lista secretos de Vault"""
        try:
            response = self.vault_client.secrets.kv.v2.list_secrets(path='')
            return response['data']['keys']
        except Exception:
            return []

class EnvironmentManager:
    """Gestor de variables de entorno para diferentes ambientes"""
    
    def __init__(self, secrets_manager: SecretsManager):
        self.secrets_manager = secrets_manager
        self.environments = ['development', 'staging', 'production']
    
    def setup_environment(self, env: str) -> Dict[str, str]:
        """Configura variables de entorno para un ambiente específico"""
        if env not in self.environments:
            raise ValueError(f"Environment {env} not supported")
        
        # Variables base
        base_vars = {
            'NODE_ENV': env,
            'ENVIRONMENT': env,
            'LOG_LEVEL': 'debug' if env == 'development' else 'info',
            'API_RATE_LIMIT': '1000' if env == 'development' else '100',
            'CORS_ORIGIN': '*' if env == 'development' else 'https://mcp-enterprise.com'
        }
        
        # Variables específicas por ambiente
        if env == 'production':
            env_vars = {
                **base_vars,
                'DATABASE_URL': self.secrets_manager.get_secret('prod_database_url'),
                'REDIS_URL': self.secrets_manager.get_secret('prod_redis_url'),
                'JWT_SECRET': self.secrets_manager.get_secret('prod_jwt_secret'),
                'OPENAI_API_KEY': self.secrets_manager.get_secret('openai_api_key'),
                'GITHUB_TOKEN': self.secrets_manager.get_secret('github_token'),
                'TELEGRAM_BOT_TOKEN': self.secrets_manager.get_secret('telegram_bot_token'),
                'NOTION_API_KEY': self.secrets_manager.get_secret('notion_api_key'),
                'FIRECRAWL_API_KEY': self.secrets_manager.get_secret('firecrawl_api_key'),
                'GRAFANA_PASSWORD': self.secrets_manager.get_secret('grafana_admin_password'),
                'POSTGRES_PASSWORD': self.secrets_manager.get_secret('postgres_password'),
                'REDIS_PASSWORD': self.secrets_manager.get_secret('redis_password'),
                'SSL_EMAIL': self.secrets_manager.get_secret('ssl_email'),
                'DOMAIN': self.secrets_manager.get_secret('domain_name')
            }
        elif env == 'staging':
            env_vars = {
                **base_vars,
                'DATABASE_URL': self.secrets_manager.get_secret('staging_database_url'),
                'REDIS_URL': self.secrets_manager.get_secret('staging_redis_url'),
                'JWT_SECRET': self.secrets_manager.get_secret('staging_jwt_secret'),
                'OPENAI_API_KEY': self.secrets_manager.get_secret('openai_api_key'),
                'DOMAIN': 'staging.mcp-enterprise.com'
            }
        else:  # development
            env_vars = {
                **base_vars,
                'DATABASE_URL': 'postgresql://mcp_user:dev_password@localhost:5432/mcp_dev',
                'REDIS_URL': 'redis://localhost:6379',
                'JWT_SECRET': 'dev_jwt_secret_not_for_production',
                'DOMAIN': 'localhost'
            }
        
        return {k: v for k, v in env_vars.items() if v is not None}
    
    def generate_env_file(self, env: str, output_path: str = None) -> str:
        """Genera archivo .env para un ambiente"""
        env_vars = self.setup_environment(env)
        
        if output_path is None:
            output_path = f'.env.{env}'
        
        with open(output_path, 'w') as f:
            f.write(f"# MCP Enterprise Environment Configuration - {env.upper()}\n")
            f.write(f"# Generated on {datetime.now()}\n\n")
            
            for key, value in sorted(env_vars.items()):
                f.write(f"{key}={value}\n")
        
        # Establecer permisos seguros
        os.chmod(output_path, 0o600)
        
        return output_path

def initialize_secrets():
    """Inicializa secretos por defecto para MCP Enterprise"""
    import secrets as py_secrets
    from datetime import datetime
    
    # Configuración del gestor de secretos
    config = {
        'backend': os.getenv('SECRETS_BACKEND', 'local'),
        'secrets_dir': '/etc/mcp/secrets',
        'key_file': '/etc/mcp/master.key',
        'master_password': os.getenv('MASTER_PASSWORD', '')
    }
    
    # Configuraciones específicas por backend
    if config['backend'] == 'aws':
        config.update({
            'aws_region': os.getenv('AWS_REGION', 'us-east-1')
        })
    elif config['backend'] == 'azure':
        config.update({
            'azure_vault_url': os.getenv('AZURE_VAULT_URL')
        })
    elif config['backend'] == 'vault':
        config.update({
            'vault_url': os.getenv('VAULT_URL', 'http://localhost:8200'),
            'vault_token': os.getenv('VAULT_TOKEN')
        })
    
    secrets_manager = SecretsManager(config)
    env_manager = EnvironmentManager(secrets_manager)
    
    # Generar secretos por defecto si no existen
    default_secrets = {
        'prod_jwt_secret': py_secrets.token_urlsafe(64),
        'staging_jwt_secret': py_secrets.token_urlsafe(64),
        'postgres_password': py_secrets.token_urlsafe(32),
        'redis_password': py_secrets.token_urlsafe(32),
        'grafana_admin_password': py_secrets.token_urlsafe(16),
        'webhook_secret': py_secrets.token_urlsafe(32),
        'encryption_key': py_secrets.token_urlsafe(32)
    }
    
    print("🔐 Inicializando secretos de MCP Enterprise...")
    
    for name, value in default_secrets.items():
        if not secrets_manager.get_secret(name):
            if secrets_manager.store_secret(name, value, {
                'created_at': datetime.now().isoformat(),
                'auto_generated': True
            }):
                print(f"✅ Secreto generado: {name}")
            else:
                print(f"❌ Error generando secreto: {name}")
        else:
            print(f"⏭️ Secreto ya existe: {name}")
    
    # Generar archivos .env para cada ambiente
    print("\n📄 Generando archivos de configuración...")
    
    for env in ['development', 'staging', 'production']:
        try:
            env_file = env_manager.generate_env_file(env)
            print(f"✅ Archivo generado: {env_file}")
        except Exception as e:
            print(f"❌ Error generando {env}: {e}")
    
    print("\n🎉 Inicialización de secretos completada!")
    print("\nPróximos pasos:")
    print("1. Revisar y actualizar secretos según sea necesario")
    print("2. Configurar secretos específicos de APIs externas")
    print("3. Establecer rotación automática de secretos")
    print("4. Configurar backup de secretos")

if __name__ == "__main__":
    initialize_secrets()

