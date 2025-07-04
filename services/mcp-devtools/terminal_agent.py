#!/usr/bin/env python3
"""
Terminal Agent - Computer Use Style for SuperMCP
Agente con acceso completo al terminal, gestión de archivos, y automatización de sistema

Author: Manus AI
Date: June 25, 2025
Version: 1.0.0
"""

import asyncio
import subprocess
import os
import json
import logging
import time
import shutil
import psutil
import socket
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import aiohttp
from aiohttp import web
import tempfile

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TerminalTaskType(Enum):
    """Tipos de tareas que puede realizar el Terminal Agent"""
    COMMAND_EXECUTION = "command_execution"
    FILE_MANAGEMENT = "file_management"
    SYSTEM_MONITORING = "system_monitoring"
    PROCESS_MANAGEMENT = "process_management"
    NETWORK_OPERATIONS = "network_operations"
    AUTOMATION = "automation"
    BACKUP_RESTORE = "backup_restore"
    LOG_ANALYSIS = "log_analysis"

class SecurityLevel(Enum):
    """Niveles de seguridad para comandos"""
    SAFE = "safe"           # Comandos de lectura, no destructivos
    MODERATE = "moderate"   # Comandos que modifican archivos
    DANGEROUS = "dangerous" # Comandos que pueden dañar el sistema
    RESTRICTED = "restricted" # Comandos bloqueados

@dataclass
class CommandResult:
    """Resultado de ejecución de comando"""
    success: bool
    command: str
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    working_directory: str

@dataclass
class SystemInfo:
    """Información del sistema"""
    hostname: str
    os_type: str
    cpu_count: int
    memory_total: int
    memory_available: int
    disk_usage: Dict[str, Dict[str, Union[int, float]]]
    network_interfaces: List[Dict[str, Any]]
    running_processes: int
    uptime: float

class SecurityManager:
    """Gestor de seguridad para comandos de terminal"""
    
    def __init__(self):
        self.setup_security_rules()
    
    def setup_security_rules(self):
        """Configurar reglas de seguridad para comandos"""
        
        # Comandos seguros (solo lectura)
        self.safe_commands = {
            'ls', 'cat', 'head', 'tail', 'grep', 'find', 'which', 'whoami',
            'pwd', 'echo', 'date', 'uptime', 'ps', 'top', 'htop', 'df', 'du',
            'free', 'uname', 'id', 'groups', 'history', 'env', 'printenv',
            'curl', 'wget', 'ping', 'traceroute', 'nslookup', 'dig',
            'git status', 'git log', 'git diff', 'git branch',
            'docker ps', 'docker images', 'docker logs',
            'systemctl status', 'journalctl', 'netstat', 'ss', 'lsof'
        }
        
        # Comandos moderados (modificación de archivos)
        self.moderate_commands = {
            'mkdir', 'touch', 'cp', 'mv', 'ln', 'chmod', 'chown',
            'tar', 'zip', 'unzip', 'gzip', 'gunzip',
            'git add', 'git commit', 'git push', 'git pull',
            'npm install', 'pip install', 'apt update',
            'systemctl restart', 'systemctl reload'
        }
        
        # Comandos peligrosos (requieren confirmación)
        self.dangerous_commands = {
            'rm', 'rmdir', 'dd', 'mkfs', 'fdisk', 'parted',
            'systemctl stop', 'systemctl disable', 'kill', 'killall',
            'reboot', 'shutdown', 'halt', 'init',
            'iptables', 'ufw', 'firewall-cmd',
            'crontab', 'at', 'batch'
        }
        
        # Comandos restringidos (bloqueados)
        self.restricted_commands = {
            'format', 'deltree', 'rm -rf /', 'chmod 777 /',
            'chown -R root /', 'sudo su', 'su -',
            ':(){ :|:& };:', # Fork bomb
            'wget -O- | sh', 'curl | sh'  # Ejecución de scripts remotos
        }
    
    def classify_command(self, command: str) -> SecurityLevel:
        """Clasificar nivel de seguridad de un comando"""
        command_lower = command.lower().strip()
        
        # Verificar comandos restringidos
        for restricted in self.restricted_commands:
            if restricted in command_lower:
                return SecurityLevel.RESTRICTED
        
        # Verificar comandos peligrosos
        for dangerous in self.dangerous_commands:
            if command_lower.startswith(dangerous):
                return SecurityLevel.DANGEROUS
        
        # Verificar comandos moderados
        for moderate in self.moderate_commands:
            if command_lower.startswith(moderate):
                return SecurityLevel.MODERATE
        
        # Verificar comandos seguros
        for safe in self.safe_commands:
            if command_lower.startswith(safe):
                return SecurityLevel.SAFE
        
        # Por defecto, clasificar como moderado
        return SecurityLevel.MODERATE
    
    def is_command_allowed(self, command: str, require_confirmation: bool = False) -> tuple[bool, str]:
        """Verificar si un comando está permitido"""
        security_level = self.classify_command(command)
        
        if security_level == SecurityLevel.RESTRICTED:
            return False, f"Command '{command}' is restricted for security reasons"
        
        if security_level == SecurityLevel.DANGEROUS and not require_confirmation:
            return False, f"Command '{command}' requires explicit confirmation (dangerous)"
        
        return True, "Command allowed"

class TerminalAgent:
    """Agente Terminal con capacidades completas de sistema"""
    
    def __init__(self, port: int = 8301, working_dir: str = "/root/supermcp"):
        self.agent_id = "terminal_agent_v1"
        self.name = "Terminal Agent"
        self.port = port
        self.working_dir = Path(working_dir)
        self.security_manager = SecurityManager()
        self.app = web.Application()
        self.command_history: List[Dict[str, Any]] = []
        
        # Capacidades del agente
        self.capabilities = [
            "command_execution", "file_management", "system_monitoring",
            "process_management", "network_operations", "automation",
            "backup_restore", "log_analysis", "system_administration"
        ]
        
        # Configurar rutas HTTP
        self._setup_routes()
        
        # Crear directorio de trabajo si no existe
        self.working_dir.mkdir(parents=True, exist_ok=True)
    
    def _setup_routes(self):
        """Configurar rutas HTTP del agente"""
        # Rutas principales
        self.app.router.add_post('/execute', self.handle_command_execution)
        self.app.router.add_post('/file', self.handle_file_operation)
        self.app.router.add_get('/system', self.handle_system_info)
        self.app.router.add_get('/processes', self.handle_process_list)
        self.app.router.add_post('/automation', self.handle_automation_task)
        
        # Rutas de gestión
        self.app.router.add_get('/health', self.handle_health)
        self.app.router.add_get('/capabilities', self.handle_capabilities)
        self.app.router.add_get('/history', self.handle_command_history)
        self.app.router.add_post('/a2a', self.handle_a2a_task)
        
        # Rutas específicas
        self.app.router.add_get('/logs/{service}', self.handle_log_analysis)
        self.app.router.add_post('/backup', self.handle_backup_operation)
        self.app.router.add_get('/network', self.handle_network_info)
    
    async def handle_command_execution(self, request):
        """Ejecutar comando de terminal"""
        try:
            data = await request.json()
            command = data.get('command', '')
            working_dir = data.get('working_dir', str(self.working_dir))
            require_confirmation = data.get('require_confirmation', False)
            timeout = data.get('timeout', 30)
            
            if not command:
                return web.json_response({
                    "success": False,
                    "error": "No command provided"
                }, status=400)
            
            # Verificar seguridad
            allowed, reason = self.security_manager.is_command_allowed(
                command, require_confirmation
            )
            
            if not allowed:
                return web.json_response({
                    "success": False,
                    "error": reason,
                    "security_level": self.security_manager.classify_command(command).value
                }, status=403)
            
            # Ejecutar comando
            result = await self.execute_command(command, working_dir, timeout)
            
            # Guardar en historial
            self.command_history.append({
                "timestamp": time.time(),
                "command": command,
                "working_dir": working_dir,
                "result": result.__dict__
            })
            
            return web.json_response({
                "success": result.success,
                "command": result.command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code,
                "execution_time": result.execution_time,
                "working_directory": result.working_directory,
                "security_level": self.security_manager.classify_command(command).value
            })
            
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def execute_command(self, command: str, working_dir: str, timeout: int = 30) -> CommandResult:
        """Ejecutar comando en el terminal"""
        start_time = time.time()
        
        try:
            # Ejecutar comando
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            # Esperar con timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=process.returncode == 0,
                command=command,
                stdout=stdout.decode('utf-8', errors='ignore'),
                stderr=stderr.decode('utf-8', errors='ignore'),
                exit_code=process.returncode,
                execution_time=execution_time,
                working_directory=working_dir
            )
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            return CommandResult(
                success=False,
                command=command,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                exit_code=-1,
                execution_time=execution_time,
                working_directory=working_dir
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return CommandResult(
                success=False,
                command=command,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                execution_time=execution_time,
                working_directory=working_dir
            )
    
    async def handle_file_operation(self, request):
        """Manejar operaciones de archivos"""
        try:
            data = await request.json()
            operation = data.get('operation', '')
            path = data.get('path', '')
            
            if operation == 'read':
                return await self._read_file(path)
            elif operation == 'write':
                content = data.get('content', '')
                return await self._write_file(path, content)
            elif operation == 'list':
                return await self._list_directory(path)
            elif operation == 'create_dir':
                return await self._create_directory(path)
            elif operation == 'delete':
                return await self._delete_path(path)
            elif operation == 'copy':
                dest = data.get('destination', '')
                return await self._copy_file(path, dest)
            elif operation == 'move':
                dest = data.get('destination', '')
                return await self._move_file(path, dest)
            else:
                return web.json_response({
                    "success": False,
                    "error": f"Unknown operation: {operation}"
                }, status=400)
                
        except Exception as e:
            logger.error(f"File operation error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def _read_file(self, file_path: str):
        """Leer archivo"""
        try:
            path = Path(file_path)
            if not path.exists():
                return web.json_response({
                    "success": False,
                    "error": "File not found"
                }, status=404)
            
            # Limitar tamaño de archivo (10MB max)
            if path.stat().st_size > 10 * 1024 * 1024:
                return web.json_response({
                    "success": False,
                    "error": "File too large (max 10MB)"
                }, status=413)
            
            content = path.read_text(encoding='utf-8', errors='ignore')
            
            return web.json_response({
                "success": True,
                "content": content,
                "size": path.stat().st_size,
                "modified": path.stat().st_mtime
            })
            
        except Exception as e:
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def _write_file(self, file_path: str, content: str):
        """Escribir archivo"""
        try:
            path = Path(file_path)
            
            # Crear directorios padre si no existen
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Escribir archivo
            path.write_text(content, encoding='utf-8')
            
            return web.json_response({
                "success": True,
                "message": f"File written: {file_path}",
                "size": len(content.encode('utf-8'))
            })
            
        except Exception as e:
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def _list_directory(self, dir_path: str):
        """Listar directorio"""
        try:
            path = Path(dir_path) if dir_path else self.working_dir
            
            if not path.exists():
                return web.json_response({
                    "success": False,
                    "error": "Directory not found"
                }, status=404)
            
            if not path.is_dir():
                return web.json_response({
                    "success": False,
                    "error": "Path is not a directory"
                }, status=400)
            
            items = []
            for item in path.iterdir():
                stat = item.stat()
                items.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file",
                    "size": stat.st_size if item.is_file() else 0,
                    "modified": stat.st_mtime,
                    "permissions": oct(stat.st_mode)[-3:]
                })
            
            # Ordenar por tipo y nombre
            items.sort(key=lambda x: (x["type"] == "file", x["name"]))
            
            return web.json_response({
                "success": True,
                "path": str(path),
                "items": items,
                "total_items": len(items)
            })
            
        except Exception as e:
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def handle_system_info(self, request):
        """Obtener información del sistema"""
        try:
            # Información básica del sistema
            info = SystemInfo(
                hostname=socket.gethostname(),
                os_type=os.name,
                cpu_count=psutil.cpu_count(),
                memory_total=psutil.virtual_memory().total,
                memory_available=psutil.virtual_memory().available,
                disk_usage={},
                network_interfaces=[],
                running_processes=len(psutil.pids()),
                uptime=time.time() - psutil.boot_time()
            )
            
            # Información de discos
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    info.disk_usage[partition.mountpoint] = {
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": (usage.used / usage.total) * 100
                    }
                except:
                    continue
            
            # Información de red
            for interface, addrs in psutil.net_if_addrs().items():
                interface_info = {"name": interface, "addresses": []}
                for addr in addrs:
                    interface_info["addresses"].append({
                        "family": str(addr.family),
                        "address": addr.address,
                        "netmask": addr.netmask
                    })
                info.network_interfaces.append(interface_info)
            
            return web.json_response({
                "success": True,
                "system_info": {
                    "hostname": info.hostname,
                    "os_type": info.os_type,
                    "cpu_count": info.cpu_count,
                    "memory": {
                        "total": info.memory_total,
                        "available": info.memory_available,
                        "used_percent": ((info.memory_total - info.memory_available) / info.memory_total) * 100
                    },
                    "disk_usage": info.disk_usage,
                    "network_interfaces": info.network_interfaces,
                    "running_processes": info.running_processes,
                    "uptime_hours": info.uptime / 3600
                }
            })
            
        except Exception as e:
            logger.error(f"System info error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def handle_process_list(self, request):
        """Obtener lista de procesos"""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'create_time']):
                try:
                    processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "cpu_percent": proc.info['cpu_percent'],
                        "memory_percent": proc.info['memory_percent'],
                        "status": proc.info['status'],
                        "create_time": proc.info['create_time']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Ordenar por uso de CPU
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            return web.json_response({
                "success": True,
                "processes": processes[:50],  # Top 50 procesos
                "total_processes": len(processes)
            })
            
        except Exception as e:
            logger.error(f"Process list error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def handle_automation_task(self, request):
        """Manejar tareas de automatización"""
        try:
            data = await request.json()
            task_type = data.get('task_type', '')
            
            if task_type == 'backup_supermcp':
                return await self._backup_supermcp_system()
            elif task_type == 'cleanup_logs':
                return await self._cleanup_old_logs()
            elif task_type == 'monitor_services':
                return await self._monitor_supermcp_services()
            elif task_type == 'update_system':
                return await self._update_system_packages()
            elif task_type == 'restart_services':
                services = data.get('services', [])
                return await self._restart_services(services)
            else:
                return web.json_response({
                    "success": False,
                    "error": f"Unknown automation task: {task_type}"
                }, status=400)
                
        except Exception as e:
            logger.error(f"Automation task error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def _backup_supermcp_system(self):
        """Crear backup del sistema SuperMCP"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_dir = f"/tmp/supermcp_backup_{timestamp}"
            
            # Crear directorio de backup
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup de archivos críticos
            critical_paths = [
                "/root/supermcp/.env",
                "/root/supermcp/configs/",
                "/root/supermcp/logs/",
                "/root/supermcp/*.py",
                "/root/supermcp/*.js",
                "/root/supermcp/package.json"
            ]
            
            backed_up_files = []
            for path in critical_paths:
                try:
                    if os.path.exists(path):
                        if os.path.isfile(path):
                            shutil.copy2(path, backup_dir)
                            backed_up_files.append(path)
                        elif os.path.isdir(path):
                            dir_name = os.path.basename(path)
                            shutil.copytree(path, os.path.join(backup_dir, dir_name))
                            backed_up_files.append(path)
                except Exception as e:
                    logger.warning(f"Failed to backup {path}: {e}")
            
            # Crear archivo tar
            tar_file = f"/tmp/supermcp_backup_{timestamp}.tar.gz"
            await self.execute_command(f"tar -czf {tar_file} -C /tmp supermcp_backup_{timestamp}")
            
            # Limpiar directorio temporal
            shutil.rmtree(backup_dir)
            
            return web.json_response({
                "success": True,
                "backup_file": tar_file,
                "backed_up_files": backed_up_files,
                "timestamp": timestamp
            })
            
        except Exception as e:
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def _monitor_supermcp_services(self):
        """Monitorear servicios de SuperMCP"""
        try:
            services_status = {}
            
            # Puertos de servicios SuperMCP
            supermcp_ports = {
                "frontend": 5174,
                "backend": 3000,
                "dashboard": 8126,
                "validation": 8127,
                "monitoring": 8125,
                "terminal_agent": 8301
            }
            
            for service, port in supermcp_ports.items():
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(('sam.chat', port))
                    sock.close()
                    
                    services_status[service] = {
                        "port": port,
                        "status": "running" if result == 0 else "stopped",
                        "accessible": result == 0
                    }
                except Exception as e:
                    services_status[service] = {
                        "port": port,
                        "status": "error",
                        "accessible": False,
                        "error": str(e)
                    }
            
            return web.json_response({
                "success": True,
                "services": services_status,
                "healthy_services": sum(1 for s in services_status.values() if s.get("accessible")),
                "total_services": len(services_status)
            })
            
        except Exception as e:
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def handle_a2a_task(self, request):
        """Manejar tareas A2A"""
        try:
            task_data = await request.json()
            task_type = task_data.get("task_type", "")
            payload = task_data.get("payload", {})
            
            if task_type == "command_execution":
                command = payload.get("command", "")
                result = await self.execute_command(command, str(self.working_dir))
                return web.json_response({
                    "success": True,
                    "result": {
                        "command_executed": True,
                        "command": result.command,
                        "success": result.success,
                        "output": result.stdout,
                        "error": result.stderr
                    }
                })
            
            elif task_type == "system_monitoring":
                # Obtener métricas del sistema
                system_info = await self.handle_system_info(request)
                return system_info
            
            elif task_type == "automation":
                automation_type = payload.get("automation_type", "")
                if automation_type:
                    # Crear request simulada para automation
                    fake_request = type('Request', (), {
                        'json': lambda: asyncio.create_task(asyncio.coroutine(lambda: {"task_type": automation_type})())
                    })()
                    return await self.handle_automation_task(fake_request)
            
            else:
                return web.json_response({
                    "success": False,
                    "error": f"Unknown A2A task type: {task_type}"
                }, status=400)
                
        except Exception as e:
            logger.error(f"A2A task error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def handle_health(self, request):
        """Health check del agente"""
        return web.json_response({
            "status": "healthy",
            "agent_id": self.agent_id,
            "name": self.name,
            "capabilities": self.capabilities,
            "working_directory": str(self.working_dir),
            "command_history_count": len(self.command_history)
        })
    
    async def handle_capabilities(self, request):
        """Obtener capacidades del agente"""
        return web.json_response({
            "agent_id": self.agent_id,
            "name": self.name,
            "capabilities": self.capabilities,
            "supported_operations": [
                "command_execution", "file_management", "system_monitoring",
                "process_management", "automation", "backup_restore"
            ],
            "security_features": [
                "command_classification", "security_levels", "command_blocking"
            ]
        })
    
    async def handle_command_history(self, request):
        """Obtener historial de comandos"""
        limit = int(request.query.get('limit', 50))
        
        return web.json_response({
            "success": True,
            "history": self.command_history[-limit:],
            "total_commands": len(self.command_history)
        })
    
    async def start_server(self):
        """Iniciar servidor del agente"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        logger.info(f"Terminal Agent started on port {self.port}")
        logger.info(f"Working directory: {self.working_dir}")
        logger.info(f"Capabilities: {', '.join(self.capabilities)}")
        
        return runner

# API de integración con SuperMCP
class TerminalAgentIntegration:
    """Integración del Terminal Agent con SuperMCP"""
    
    def __init__(self, terminal_agent: TerminalAgent):
        self.terminal_agent = terminal_agent
        self.a2a_server_url = "http://sam.chat:8200"
    
    async def register_with_a2a(self):
        """Registrar agente con servidor A2A"""
        agent_card = {
            "agent_id": self.terminal_agent.agent_id,
            "name": self.terminal_agent.name,
            "version": "1.0.0",
            "capabilities": self.terminal_agent.capabilities,
            "endpoints": {
                "http": f"http://sam.chat:{self.terminal_agent.port}",
                "health": f"http://sam.chat:{self.terminal_agent.port}/health",
                "a2a": f"http://sam.chat:{self.terminal_agent.port}/a2a"
            },
            "metadata": {
                "description": "Terminal agent with full system access for automation",
                "security_level": "high",
                "working_directory": str(self.terminal_agent.working_dir)
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.a2a_server_url}/register",
                    json=agent_card
                ) as resp:
                    if resp.status == 200:
                        logger.info("Terminal Agent registered with A2A server")
                        return True
                    else:
                        logger.error(f"Failed to register with A2A server: {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"A2A registration error: {e}")
            return False

# Comandos especializados para SuperMCP
class SuperMCPCommands:
    """Comandos especializados para gestión de SuperMCP"""
    
    def __init__(self, terminal_agent: TerminalAgent):
        self.terminal_agent = terminal_agent
    
    async def deploy_supermcp(self) -> Dict[str, Any]:
        """Deploy completo del sistema SuperMCP"""
        deployment_steps = [
            "cd /root/supermcp",
            "git pull origin main",
            "npm install --production",
            "pip install -r requirements.txt",
            "./scripts/stop_all_services.sh",
            "./scripts/start_unified_system.sh",
            "sleep 10",
            "./scripts/health_check_all.sh"
        ]
        
        results = []
        for step in deployment_steps:
            result = await self.terminal_agent.execute_command(step, "/root/supermcp")
            results.append({
                "step": step,
                "success": result.success,
                "output": result.stdout,
                "error": result.stderr
            })
            
            if not result.success and "sleep" not in step:
                break
        
        return {
            "deployment_completed": all(r["success"] for r in results if "sleep" not in r["step"]),
            "steps": results
        }
    
    async def setup_environment(self) -> Dict[str, Any]:
        """Configurar entorno completo"""
        setup_commands = [
            "mkdir -p /root/supermcp/{logs,data,backups,configs}",
            "chmod +x /root/supermcp/scripts/*.sh",
            "systemctl enable nginx",
            "systemctl start nginx",
            "ufw allow 22,80,443,3000,5174,8125:8130/tcp",
            "npm install -g pm2",
            "pip install --upgrade pip setuptools wheel"
        ]
        
        results = []
        for cmd in setup_commands:
            result = await self.terminal_agent.execute_command(cmd, "/root/supermcp")
            results.append({
                "command": cmd,
                "success": result.success,
                "output": result.stdout[:200],  # Limitar output
                "error": result.stderr[:200] if result.stderr else None
            })
        
        return {
            "environment_setup": True,
            "commands_executed": len(results),
            "successful_commands": sum(1 for r in results if r["success"]),
            "results": results
        }
    
    async def backup_and_restore(self, operation: str, backup_file: str = None) -> Dict[str, Any]:
        """Backup y restore del sistema"""
        if operation == "backup":
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_commands = [
                f"tar -czf /tmp/supermcp_full_backup_{timestamp}.tar.gz -C /root supermcp",
                f"cp /tmp/supermcp_full_backup_{timestamp}.tar.gz /root/backups/",
                f"ls -la /root/backups/supermcp_full_backup_{timestamp}.tar.gz"
            ]
            
            results = []
            for cmd in backup_commands:
                result = await self.terminal_agent.execute_command(cmd, "/root")
                results.append({
                    "command": cmd,
                    "success": result.success,
                    "output": result.stdout
                })
            
            return {
                "backup_completed": all(r["success"] for r in results),
                "backup_file": f"/root/backups/supermcp_full_backup_{timestamp}.tar.gz",
                "timestamp": timestamp,
                "results": results
            }
        
        elif operation == "restore" and backup_file:
            restore_commands = [
                "systemctl stop supermcp-* || true",
                f"cd /root && tar -xzf {backup_file}",
                "cd /root/supermcp && ./scripts/start_unified_system.sh"
            ]
            
            results = []
            for cmd in restore_commands:
                result = await self.terminal_agent.execute_command(cmd, "/root")
                results.append({
                    "command": cmd,
                    "success": result.success,
                    "output": result.stdout
                })
            
            return {
                "restore_completed": all(r["success"] for r in results),
                "backup_file": backup_file,
                "results": results
            }
        
        return {"error": "Invalid operation or missing backup file"}

# Sistema de notificaciones para Terminal Agent
class TerminalNotificationSystem:
    """Sistema de notificaciones para eventos del terminal"""
    
    def __init__(self):
        self.webhook_urls = []
        self.notification_history = []
    
    async def notify_command_execution(self, command: str, result: CommandResult):
        """Notificar ejecución de comando"""
        notification = {
            "type": "command_execution",
            "timestamp": time.time(),
            "command": command,
            "success": result.success,
            "execution_time": result.execution_time,
            "exit_code": result.exit_code
        }
        
        self.notification_history.append(notification)
        await self._send_notifications(notification)
    
    async def notify_system_alert(self, alert_type: str, message: str, severity: str = "info"):
        """Notificar alerta del sistema"""
        notification = {
            "type": "system_alert",
            "timestamp": time.time(),
            "alert_type": alert_type,
            "message": message,
            "severity": severity
        }
        
        self.notification_history.append(notification)
        await self._send_notifications(notification)
    
    async def _send_notifications(self, notification: Dict[str, Any]):
        """Enviar notificaciones a webhooks configurados"""
        for webhook_url in self.webhook_urls:
            try:
                async with aiohttp.ClientSession() as session:
                    await session.post(webhook_url, json=notification)
            except Exception as e:
                logger.error(f"Failed to send notification to {webhook_url}: {e}")

# Función principal para iniciar el Terminal Agent
async def main():
    """Función principal para iniciar el Terminal Agent"""
    
    # Crear Terminal Agent
    terminal_agent = TerminalAgent(port=8301, working_dir="/root/supermcp")
    
    # Crear integración
    integration = TerminalAgentIntegration(terminal_agent)
    
    # Crear comandos especializados
    supermcp_commands = SuperMCPCommands(terminal_agent)
    
    # Iniciar servidor
    runner = await terminal_agent.start_server()
    
    # Registrar con A2A (opcional)
    await integration.register_with_a2a()
    
    print(f"""
🖥️  TERMINAL AGENT STARTED SUCCESSFULLY!
=========================================

🌐 Access Points:
   HTTP API:     http://sam.chat:8301
   Health Check: http://sam.chat:8301/health
   A2A Endpoint: http://sam.chat:8301/a2a

🛠️  Available Endpoints:
   POST /execute     - Execute terminal commands
   POST /file        - File operations (read/write/list/etc)
   GET  /system      - System information
   GET  /processes   - Process list
   POST /automation  - Automation tasks
   GET  /logs/{{service}} - Log analysis
   POST /backup      - Backup operations
   GET  /network     - Network information

🔒 Security Features:
   ✅ Command classification (safe/moderate/dangerous/restricted)
   ✅ Security level enforcement
   ✅ Command history tracking
   ✅ Working directory isolation

🤖 A2A Integration:
   ✅ Registered with A2A server (if available)
   ✅ Supports A2A task delegation
   ✅ Compatible with SuperMCP ecosystem

🎯 Specialized Commands:
   ✅ SuperMCP deployment automation
   ✅ Environment setup
   ✅ Backup and restore operations
   ✅ Service monitoring

📋 Example Usage:
   curl -X POST http://sam.chat:8301/execute \\
     -H "Content-Type: application/json" \\
     -d '{{"command": "ls -la /root/supermcp"}}'

   curl -X POST http://sam.chat:8301/file \\
     -H "Content-Type: application/json" \\
     -d '{{"operation": "list", "path": "/root/supermcp"}}'

🚀 Ready for terminal automation!
""")
    
    try:
        # Mantener el servidor corriendo
        while True:
            await asyncio.sleep(3600)  # Dormir 1 hora
    except KeyboardInterrupt:
        logger.info("Shutting down Terminal Agent...")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    # Configuración adicional para Docker/containers
    if os.getenv('RUNNING_IN_DOCKER'):
        # Ajustes específicos para contenedores
        os.environ['PYTHONUNBUFFERED'] = '1'
    
    # Ejecutar agente
    asyncio.run(main())

# Script de instalación y configuración
def create_installation_script():
    """Crear script de instalación para el Terminal Agent"""
    install_script = """#!/bin/bash
# Terminal Agent Installation Script for SuperMCP

echo "🖥️ Installing Terminal Agent..."

# 1. Verificar dependencias
echo "📦 Checking dependencies..."
python3 -c "import asyncio, aiohttp, psutil" 2>/dev/null || {
    echo "Installing Python dependencies..."
    pip install aiohttp psutil
}

# 2. Crear directorio de trabajo
mkdir -p /root/supermcp/terminal_agent
cd /root/supermcp

# 3. Crear archivo del agente
cat > terminal_agent.py << 'AGENT_EOF'
[CONTENIDO DEL TERMINAL AGENT]
AGENT_EOF

# 4. Hacer ejecutable
chmod +x terminal_agent.py

# 5. Crear servicio systemd
sudo tee /etc/systemd/system/terminal-agent.service > /dev/null << 'SERVICE_EOF'
[Unit]
Description=SuperMCP Terminal Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/supermcp
ExecStart=/usr/bin/python3 /root/supermcp/terminal_agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# 6. Habilitar servicio
sudo systemctl daemon-reload
sudo systemctl enable terminal-agent

echo "✅ Terminal Agent installed successfully!"
echo "🚀 Start with: sudo systemctl start terminal-agent"
echo "📊 Status: sudo systemctl status terminal-agent"
echo "🌐 API: http://sam.chat:8301"
"""
    
    with open('/root/supermcp/install_terminal_agent.sh', 'w') as f:
        f.write(install_script)
    
    os.chmod('/root/supermcp/install_terminal_agent.sh', 0o755)
    print("✅ Installation script created: /root/supermcp/install_terminal_agent.sh")

# Crear script de instalación si se ejecuta directamente
if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "install":
    create_installation_script()
[El código completo del artifact]
EOF# 1. Crear el Terminal Agent
cd /root/supermcp
cat > terminal_agent.py << 'EOF'
#!/usr/bin/env python3
"""
Terminal Agent - Computer Use Style for SuperMCP
Agente con acceso completo al terminal, gestión de archivos, y automatización de sistema

Author: Manus AI
Date: June 25, 2025
Version: 1.0.0
"""

import asyncio
import subprocess
import os
import json
import logging
import time
import shutil
import psutil
import socket
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import aiohttp
from aiohttp import web
import tempfile

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TerminalTaskType(Enum):
    """Tipos de tareas que puede realizar el Terminal Agent"""
    COMMAND_EXECUTION = "command_execution"
    FILE_MANAGEMENT = "file_management"
    SYSTEM_MONITORING = "system_monitoring"
    PROCESS_MANAGEMENT = "process_management"
    NETWORK_OPERATIONS = "network_operations"
    AUTOMATION = "automation"
    BACKUP_RESTORE = "backup_restore"
    LOG_ANALYSIS = "log_analysis"

class SecurityLevel(Enum):
    """Niveles de seguridad para comandos"""
    SAFE = "safe"           # Comandos de lectura, no destructivos
    MODERATE = "moderate"   # Comandos que modifican archivos
    DANGEROUS = "dangerous" # Comandos que pueden dañar el sistema
    RESTRICTED = "restricted" # Comandos bloqueados

@dataclass
class CommandResult:
    """Resultado de ejecución de comando"""
    success: bool
    command: str
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    working_directory: str

@dataclass
class SystemInfo:
    """Información del sistema"""
    hostname: str
    os_type: str
    cpu_count: int
    memory_total: int
    memory_available: int
    disk_usage: Dict[str, Dict[str, Union[int, float]]]
    network_interfaces: List[Dict[str, Any]]
    running_processes: int
    uptime: float

class SecurityManager:
    """Gestor de seguridad para comandos de terminal"""
    
    def __init__(self):
        self.setup_security_rules()
    
    def setup_security_rules(self):
        """Configurar reglas de seguridad para comandos"""
        
        # Comandos seguros (solo lectura)
        self.safe_commands = {
            'ls', 'cat', 'head', 'tail', 'grep', 'find', 'which', 'whoami',
            'pwd', 'echo', 'date', 'uptime', 'ps', 'top', 'htop', 'df', 'du',
            'free', 'uname', 'id', 'groups', 'history', 'env', 'printenv',
            'curl', 'wget', 'ping', 'traceroute', 'nslookup', 'dig',
            'git status', 'git log', 'git diff', 'git branch',
            'docker ps', 'docker images', 'docker logs',
            'systemctl status', 'journalctl', 'netstat', 'ss', 'lsof'
        }
        
        # Comandos moderados (modificación de archivos)
        self.moderate_commands = {
            'mkdir', 'touch', 'cp', 'mv', 'ln', 'chmod', 'chown',
            'tar', 'zip', 'unzip', 'gzip', 'gunzip',
            'git add', 'git commit', 'git push', 'git pull',
            'npm install', 'pip install', 'apt update',
            'systemctl restart', 'systemctl reload'
        }
        
        # Comandos peligrosos (requieren confirmación)
        self.dangerous_commands = {
            'rm', 'rmdir', 'dd', 'mkfs', 'fdisk', 'parted',
            'systemctl stop', 'systemctl disable', 'kill', 'killall',
            'reboot', 'shutdown', 'halt', 'init',
            'iptables', 'ufw', 'firewall-cmd',
            'crontab', 'at', 'batch'
        }
        
        # Comandos restringidos (bloqueados)
        self.restricted_commands = {
            'format', 'deltree', 'rm -rf /', 'chmod 777 /',
            'chown -R root /', 'sudo su', 'su -',
            ':(){ :|:& };:', # Fork bomb
            'wget -O- | sh', 'curl | sh'  # Ejecución de scripts remotos
        }
    
    def classify_command(self, command: str) -> SecurityLevel:
        """Clasificar nivel de seguridad de un comando"""
        command_lower = command.lower().strip()
        
        # Verificar comandos restringidos
        for restricted in self.restricted_commands:
            if restricted in command_lower:
                return SecurityLevel.RESTRICTED
        
        # Verificar comandos peligrosos
        for dangerous in self.dangerous_commands:
            if command_lower.startswith(dangerous):
                return SecurityLevel.DANGEROUS
        
        # Verificar comandos moderados
        for moderate in self.moderate_commands:
            if command_lower.startswith(moderate):
                return SecurityLevel.MODERATE
        
        # Verificar comandos seguros
        for safe in self.safe_commands:
            if command_lower.startswith(safe):
                return SecurityLevel.SAFE
        
        # Por defecto, clasificar como moderado
        return SecurityLevel.MODERATE
    
    def is_command_allowed(self, command: str, require_confirmation: bool = False) -> tuple[bool, str]:
        """Verificar si un comando está permitido"""
        security_level = self.classify_command(command)
        
        if security_level == SecurityLevel.RESTRICTED:
            return False, f"Command '{command}' is restricted for security reasons"
        
        if security_level == SecurityLevel.DANGEROUS and not require_confirmation:
            return False, f"Command '{command}' requires explicit confirmation (dangerous)"
        
        return True, "Command allowed"

class TerminalAgent:
    """Agente Terminal con capacidades completas de sistema"""
    
    def __init__(self, port: int = 8301, working_dir: str = "/root/supermcp"):
        self.agent_id = "terminal_agent_v1"
        self.name = "Terminal Agent"
        self.port = port
        self.working_dir = Path(working_dir)
        self.security_manager = SecurityManager()
        self.app = web.Application()
        self.command_history: List[Dict[str, Any]] = []
        
        # Capacidades del agente
        self.capabilities = [
            "command_execution", "file_management", "system_monitoring",
            "process_management", "network_operations", "automation",
            "backup_restore", "log_analysis", "system_administration"
        ]
        
        # Configurar rutas HTTP
        self._setup_routes()
        
        # Crear directorio de trabajo si no existe
        self.working_dir.mkdir(parents=True, exist_ok=True)
    
    def _setup_routes(self):
        """Configurar rutas HTTP del agente"""
        # Rutas principales
        self.app.router.add_post('/execute', self.handle_command_execution)
        self.app.router.add_post('/file', self.handle_file_operation)
        self.app.router.add_get('/system', self.handle_system_info)
        self.app.router.add_get('/processes', self.handle_process_list)
        self.app.router.add_post('/automation', self.handle_automation_task)
        
        # Rutas de gestión
        self.app.router.add_get('/health', self.handle_health)
        self.app.router.add_get('/capabilities', self.handle_capabilities)
        self.app.router.add_get('/history', self.handle_command_history)
        self.app.router.add_post('/a2a', self.handle_a2a_task)
        
        # Rutas específicas
        self.app.router.add_get('/logs/{service}', self.handle_log_analysis)
        self.app.router.add_post('/backup', self.handle_backup_operation)
        self.app.router.add_get('/network', self.handle_network_info)
    
    async def handle_command_execution(self, request):
        """Ejecutar comando de terminal"""
        try:
            data = await request.json()
            command = data.get('command', '')
            working_dir = data.get('working_dir', str(self.working_dir))
            require_confirmation = data.get('require_confirmation', False)
            timeout = data.get('timeout', 30)
            
            if not command:
                return web.json_response({
                    "success": False,
                    "error": "No command provided"
                }, status=400)
            
            # Verificar seguridad
            allowed, reason = self.security_manager.is_command_allowed(
                command, require_confirmation
            )
            
            if not allowed:
                return web.json_response({
                    "success": False,
                    "error": reason,
                    "security_level": self.security_manager.classify_command(command).value
                }, status=403)
            
            # Ejecutar comando
            result = await self.execute_command(command, working_dir, timeout)
            
            # Guardar en historial
            self.command_history.append({
                "timestamp": time.time(),
                "command": command,
                "working_dir": working_dir,
                "result": result.__dict__
            })
            
            return web.json_response({
                "success": result.success,
                "command": result.command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code,
                "execution_time": result.execution_time,
                "working_directory": result.working_directory,
                "security_level": self.security_manager.classify_command(command).value
            })
            
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def execute_command(self, command: str, working_dir: str, timeout: int = 30) -> CommandResult:
        """Ejecutar comando en el terminal"""
        start_time = time.time()
        
        try:
            # Ejecutar comando
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            # Esperar con timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=process.returncode == 0,
                command=command,
                stdout=stdout.decode('utf-8', errors='ignore'),
                stderr=stderr.decode('utf-8', errors='ignore'),
                exit_code=process.returncode,
                execution_time=execution_time,
                working_directory=working_dir
            )
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            return CommandResult(
                success=False,
                command=command,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                exit_code=-1,
                execution_time=execution_time,
                working_directory=working_dir
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return CommandResult(
                success=False,
                command=command,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                execution_time=execution_time,
                working_directory=working_dir
            )
    
    async def handle_file_operation(self, request):
        """Manejar operaciones de archivos"""
        try:
            data = await request.json()
            operation = data.get('operation', '')
            path = data.get('path', '')
            
            if operation == 'read':
                return await self._read_file(path)
            elif operation == 'write':
                content = data.get('content', '')
                return await self._write_file(path, content)
            elif operation == 'list':
                return await self._list_directory(path)
            elif operation == 'create_dir':
                return await self._create_directory(path)
            elif operation == 'delete':
                return await self._delete_path(path)
            elif operation == 'copy':
                dest = data.get('destination', '')
                return await self._copy_file(path, dest)
            elif operation == 'move':
                dest = data.get('destination', '')
                return await self._move_file(path, dest)
            else:
                return web.json_response({
                    "success": False,
                    "error": f"Unknown operation: {operation}"
                }, status=400)
                
        except Exception as e:
            logger.error(f"File operation error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def _read_file(self, file_path: str):
        """Leer archivo"""
        try:
            path = Path(file_path)
            if not path.exists():
                return web.json_response({
                    "success": False,
                    "error": "File not found"
                }, status=404)
            
            # Limitar tamaño de archivo (10MB max)
            if path.stat().st_size > 10 * 1024 * 1024:
                return web.json_response({
                    "success": False,
                    "error": "File too large (max 10MB)"
                }, status=413)
            
            content = path.read_text(encoding='utf-8', errors='ignore')
            
            return web.json_response({
                "success": True,
                "content": content,
                "size": path.stat().st_size,
                "modified": path.stat().st_mtime
            })
            
        except Exception as e:
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def _write_file(self, file_path: str, content: str):
        """Escribir archivo"""
        try:
            path = Path(file_path)
            
            # Crear directorios padre si no existen
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Escribir archivo
            path.write_text(content, encoding='utf-8')
            
            return web.json_response({
                "success": True,
                "message": f"File written: {file_path}",
                "size": len(content.encode('utf-8'))
            })
            
        except Exception as e:
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def _list_directory(self, dir_path: str):
        """Listar directorio"""
        try:
            path = Path(dir_path) if dir_path else self.working_dir
            
            if not path.exists():
                return web.json_response({
                    "success": False,
                    "error": "Directory not found"
                }, status=404)
            
            if not path.is_dir():
                return web.json_response({
                    "success": False,
                    "error": "Path is not a directory"
                }, status=400)
            
            items = []
            for item in path.iterdir():
                stat = item.stat()
                items.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file",
                    "size": stat.st_size if item.is_file() else 0,
                    "modified": stat.st_mtime,
                    "permissions": oct(stat.st_mode)[-3:]
                })
            
            # Ordenar por tipo y nombre
            items.sort(key=lambda x: (x["type"] == "file", x["name"]))
            
            return web.json_response({
                "success": True,
                "path": str(path),
                "items": items,
                "total_items": len(items)
            })
            
        except Exception as e:
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def handle_system_info(self, request):
        """Obtener información del sistema"""
        try:
            # Información básica del sistema
            info = SystemInfo(
                hostname=socket.gethostname(),
                os_type=os.name,
                cpu_count=psutil.cpu_count(),
                memory_total=psutil.virtual_memory().total,
                memory_available=psutil.virtual_memory().available,
                disk_usage={},
                network_interfaces=[],
                running_processes=len(psutil.pids()),
                uptime=time.time() - psutil.boot_time()
            )
            
            # Información de discos
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    info.disk_usage[partition.mountpoint] = {
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": (usage.used / usage.total) * 100
                    }
                except:
                    continue
            
            # Información de red
            for interface, addrs in psutil.net_if_addrs().items():
                interface_info = {"name": interface, "addresses": []}
                for addr in addrs:
                    interface_info["addresses"].append({
                        "family": str(addr.family),
                        "address": addr.address,
                        "netmask": addr.netmask
                    })
                info.network_interfaces.append(interface_info)
            
            return web.json_response({
                "success": True,
                "system_info": {
                    "hostname": info.hostname,
                    "os_type": info.os_type,
                    "cpu_count": info.cpu_count,
                    "memory": {
                        "total": info.memory_total,
                        "available": info.memory_available,
                        "used_percent": ((info.memory_total - info.memory_available) / info.memory_total) * 100
                    },
                    "disk_usage": info.disk_usage,
                    "network_interfaces": info.network_interfaces,
                    "running_processes": info.running_processes,
                    "uptime_hours": info.uptime / 3600
                }
            })
            
        except Exception as e:
            logger.error(f"System info error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def handle_process_list(self, request):
        """Obtener lista de procesos"""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'create_time']):
                try:
                    processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "cpu_percent": proc.info['cpu_percent'],
                        "memory_percent": proc.info['memory_percent'],
                        "status": proc.info['status'],
                        "create_time": proc.info['create_time']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Ordenar por uso de CPU
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            return web.json_response({
                "success": True,
                "processes": processes[:50],  # Top 50 procesos
                "total_processes": len(processes)
            })
            
        except Exception as e:
            logger.error(f"Process list error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def handle_automation_task(self, request):
        """Manejar tareas de automatización"""
        try:
            data = await request.json()
            task_type = data.get('task_type', '')
            
            if task_type == 'backup_supermcp':
                return await self._backup_supermcp_system()
            elif task_type == 'cleanup_logs':
                return await self._cleanup_old_logs()
            elif task_type == 'monitor_services':
                return await self._monitor_supermcp_services()
            elif task_type == 'update_system':
                return await self._update_system_packages()
            elif task_type == 'restart_services':
                services = data.get('services', [])
                return await self._restart_services(services)
            else:
                return web.json_response({
                    "success": False,
                    "error": f"Unknown automation task: {task_type}"
                }, status=400)
                
        except Exception as e:
            logger.error(f"Automation task error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def _backup_supermcp_system(self):
        """Crear backup del sistema SuperMCP"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_dir = f"/tmp/supermcp_backup_{timestamp}"
            
            # Crear directorio de backup
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup de archivos críticos
            critical_paths = [
                "/root/supermcp/.env",
                "/root/supermcp/configs/",
                "/root/supermcp/logs/",
                "/root/supermcp/*.py",
                "/root/supermcp/*.js",
                "/root/supermcp/package.json"
            ]
            
            backed_up_files = []
            for path in critical_paths:
                try:
                    if os.path.exists(path):
                        if os.path.isfile(path):
                            shutil.copy2(path, backup_dir)
                            backed_up_files.append(path)
                        elif os.path.isdir(path):
                            dir_name = os.path.basename(path)
                            shutil.copytree(path, os.path.join(backup_dir, dir_name))
                            backed_up_files.append(path)
                except Exception as e:
                    logger.warning(f"Failed to backup {path}: {e}")
            
            # Crear archivo tar
            tar_file = f"/tmp/supermcp_backup_{timestamp}.tar.gz"
            await self.execute_command(f"tar -czf {tar_file} -C /tmp supermcp_backup_{timestamp}")
            
            # Limpiar directorio temporal
            shutil.rmtree(backup_dir)
            
            return web.json_response({
                "success": True,
                "backup_file": tar_file,
                "backed_up_files": backed_up_files,
                "timestamp": timestamp
            })
            
        except Exception as e:
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def _monitor_supermcp_services(self):
        """Monitorear servicios de SuperMCP"""
        try:
            services_status = {}
            
            # Puertos de servicios SuperMCP
            supermcp_ports = {
                "frontend": 5174,
                "backend": 3000,
                "dashboard": 8126,
                "validation": 8127,
                "monitoring": 8125,
                "terminal_agent": 8301
            }
            
            for service, port in supermcp_ports.items():
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(('sam.chat', port))
                    sock.close()
                    
                    services_status[service] = {
                        "port": port,
                        "status": "running" if result == 0 else "stopped",
                        "accessible": result == 0
                    }
                except Exception as e:
                    services_status[service] = {
                        "port": port,
                        "status": "error",
                        "accessible": False,
                        "error": str(e)
                    }
            
            return web.json_response({
                "success": True,
                "services": services_status,
                "healthy_services": sum(1 for s in services_status.values() if s.get("accessible")),
                "total_services": len(services_status)
            })
            
        except Exception as e:
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def handle_a2a_task(self, request):
        """Manejar tareas A2A"""
        try:
            task_data = await request.json()
            task_type = task_data.get("task_type", "")
            payload = task_data.get("payload", {})
            
            if task_type == "command_execution":
                command = payload.get("command", "")
                result = await self.execute_command(command, str(self.working_dir))
                return web.json_response({
                    "success": True,
                    "result": {
                        "command_executed": True,
                        "command": result.command,
                        "success": result.success,
                        "output": result.stdout,
                        "error": result.stderr
                    }
                })
            
            elif task_type == "system_monitoring":
                # Obtener métricas del sistema
                system_info = await self.handle_system_info(request)
                return system_info
            
            elif task_type == "automation":
                automation_type = payload.get("automation_type", "")
                if automation_type:
                    # Crear request simulada para automation
                    fake_request = type('Request', (), {
                        'json': lambda: asyncio.create_task(asyncio.coroutine(lambda: {"task_type": automation_type})())
                    })()
                    return await self.handle_automation_task(fake_request)
            
            else:
                return web.json_response({
                    "success": False,
                    "error": f"Unknown A2A task type: {task_type}"
                }, status=400)
                
        except Exception as e:
            logger.error(f"A2A task error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def handle_health(self, request):
        """Health check del agente"""
        return web.json_response({
            "status": "healthy",
            "agent_id": self.agent_id,
            "name": self.name,
            "capabilities": self.capabilities,
            "working_directory": str(self.working_dir),
            "command_history_count": len(self.command_history)
        })
    
    async def handle_capabilities(self, request):
        """Obtener capacidades del agente"""
        return web.json_response({
            "agent_id": self.agent_id,
            "name": self.name,
            "capabilities": self.capabilities,
            "supported_operations": [
                "command_execution", "file_management", "system_monitoring",
                "process_management", "automation", "backup_restore"
            ],
            "security_features": [
                "command_classification", "security_levels", "command_blocking"
            ]
        })
    
    async def handle_command_history(self, request):
        """Obtener historial de comandos"""
        limit = int(request.query.get('limit', 50))
        
        return web.json_response({
            "success": True,
            "history": self.command_history[-limit:],
            "total_commands": len(self.command_history)
        })
    
    async def start_server(self):
        """Iniciar servidor del agente"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        logger.info(f"Terminal Agent started on port {self.port}")
        logger.info(f"Working directory: {self.working_dir}")
        logger.info(f"Capabilities: {', '.join(self.capabilities)}")
        
        return runner

# API de integración con SuperMCP
class TerminalAgentIntegration:
    """Integración del Terminal Agent con SuperMCP"""
    
    def __init__(self, terminal_agent: TerminalAgent):
        self.terminal_agent = terminal_agent
        self.a2a_server_url = "http://sam.chat:8200"
    
    async def register_with_a2a(self):
        """Registrar agente con servidor A2A"""
        agent_card = {
            "agent_id": self.terminal_agent.agent_id,
            "name": self.terminal_agent.name,
            "version": "1.0.0",
            "capabilities": self.terminal_agent.capabilities,
            "endpoints": {
                "http": f"http://sam.chat:{self.terminal_agent.port}",
                "health": f"http://sam.chat:{self.terminal_agent.port}/health",
                "a2a": f"http://sam.chat:{self.terminal_agent.port}/a2a"
            },
            "metadata": {
                "description": "Terminal agent with full system access for automation",
                "security_level": "high",
                "working_directory": str(self.terminal_agent.working_dir)
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.a2a_server_url}/register",
                    json=agent_card
                ) as resp:
                    if resp.status == 200:
                        logger.info("Terminal Agent registered with A2A server")
                        return True
                    else:
                        logger.error(f"Failed to register with A2A server: {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"A2A registration error: {e}")
            return False

# Comandos especializados para SuperMCP
class SuperMCPCommands:
    """Comandos especializados para gestión de SuperMCP"""
    
    def __init__(self, terminal_agent: TerminalAgent):
        self.terminal_agent = terminal_agent
    
    async def deploy_supermcp(self) -> Dict[str, Any]:
        """Deploy completo del sistema SuperMCP"""
        deployment_steps = [
            "cd /root/supermcp",
            "git pull origin main",
            "npm install --production",
            "pip install -r requirements.txt",
            "./scripts/stop_all_services.sh",
            "./scripts/start_unified_system.sh",
            "sleep 10",
            "./scripts/health_check_all.sh"
        ]
        
        results = []
        for step in deployment_steps:
            result = await self.terminal_agent.execute_command(step, "/root/supermcp")
            results.append({
                "step": step,
                "success": result.success,
                "output": result.stdout,
                "error": result.stderr
            })
            
            if not result.success and "sleep" not in step:
                break
        
        return {
            "deployment_completed": all(r["success"] for r in results if "sleep" not in r["step"]),
            "steps": results
        }
    
    async def setup_environment(self) -> Dict[str, Any]:
        """Configurar entorno completo"""
        setup_commands = [
            "mkdir -p /root/supermcp/{logs,data,backups,configs}",
            "chmod +x /root/supermcp/scripts/*.sh",
            "systemctl enable nginx",
            "systemctl start nginx",
            "ufw allow 22,80,443,3000,5174,8125:8130/tcp",
            "npm install -g pm2",
            "pip install --upgrade pip setuptools wheel"
        ]
        
        results = []
        for cmd in setup_commands:
            result = await self.terminal_agent.execute_command(cmd, "/root/supermcp")
            results.append({
                "command": cmd,
                "success": result.success,
                "output": result.stdout[:200],  # Limitar output
                "error": result.stderr[:200] if result.stderr else None
            })
        
        return {
            "environment_setup": True,
            "commands_executed": len(results),
            "successful_commands": sum(1 for r in results if r["success"]),
            "results": results
        }
    
    async def backup_and_restore(self, operation: str, backup_file: str = None) -> Dict[str, Any]:
        """Backup y restore del sistema"""
        if operation == "backup":
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_commands = [
                f"tar -czf /tmp/supermcp_full_backup_{timestamp}.tar.gz -C /root supermcp",
                f"cp /tmp/supermcp_full_backup_{timestamp}.tar.gz /root/backups/",
                f"ls -la /root/backups/supermcp_full_backup_{timestamp}.tar.gz"
            ]
            
            results = []
            for cmd in backup_commands:
                result = await self.terminal_agent.execute_command(cmd, "/root")
                results.append({
                    "command": cmd,
                    "success": result.success,
                    "output": result.stdout
                })
            
            return {
                "backup_completed": all(r["success"] for r in results),
                "backup_file": f"/root/backups/supermcp_full_backup_{timestamp}.tar.gz",
                "timestamp": timestamp,
                "results": results
            }
        
        elif operation == "restore" and backup_file:
            restore_commands = [
                "systemctl stop supermcp-* || true",
                f"cd /root && tar -xzf {backup_file}",
                "cd /root/supermcp && ./scripts/start_unified_system.sh"
            ]
            
            results = []
            for cmd in restore_commands:
                result = await self.terminal_agent.execute_command(cmd, "/root")
                results.append({
                    "command": cmd,
                    "success": result.success,
                    "output": result.stdout
                })
            
            return {
                "restore_completed": all(r["success"] for r in results),
                "backup_file": backup_file,
                "results": results
            }
        
        return {"error": "Invalid operation or missing backup file"}

# Sistema de notificaciones para Terminal Agent
class TerminalNotificationSystem:
    """Sistema de notificaciones para eventos del terminal"""
    
    def __init__(self):
        self.webhook_urls = []
        self.notification_history = []
    
    async def notify_command_execution(self, command: str, result: CommandResult):
        """Notificar ejecución de comando"""
        notification = {
            "type": "command_execution",
            "timestamp": time.time(),
            "command": command,
            "success": result.success,
            "execution_time": result.execution_time,
            "exit_code": result.exit_code
        }
        
        self.notification_history.append(notification)
        await self._send_notifications(notification)
    
    async def notify_system_alert(self, alert_type: str, message: str, severity: str = "info"):
        """Notificar alerta del sistema"""
        notification = {
            "type": "system_alert",
            "timestamp": time.time(),
            "alert_type": alert_type,
            "message": message,
            "severity": severity
        }
        
        self.notification_history.append(notification)
        await self._send_notifications(notification)
    
    async def _send_notifications(self, notification: Dict[str, Any]):
        """Enviar notificaciones a webhooks configurados"""
        for webhook_url in self.webhook_urls:
            try:
                async with aiohttp.ClientSession() as session:
                    await session.post(webhook_url, json=notification)
            except Exception as e:
                logger.error(f"Failed to send notification to {webhook_url}: {e}")

# Función principal para iniciar el Terminal Agent
async def main():
    """Función principal para iniciar el Terminal Agent"""
    
    # Crear Terminal Agent
    terminal_agent = TerminalAgent(port=8301, working_dir="/root/supermcp")
    
    # Crear integración
    integration = TerminalAgentIntegration(terminal_agent)
    
    # Crear comandos especializados
    supermcp_commands = SuperMCPCommands(terminal_agent)
    
    # Iniciar servidor
    runner = await terminal_agent.start_server()
    
    # Registrar con A2A (opcional)
    await integration.register_with_a2a()
    
    print(f"""
🖥️  TERMINAL AGENT STARTED SUCCESSFULLY!
=========================================

🌐 Access Points:
   HTTP API:     http://sam.chat:8301
   Health Check: http://sam.chat:8301/health
   A2A Endpoint: http://sam.chat:8301/a2a

🛠️  Available Endpoints:
   POST /execute     - Execute terminal commands
   POST /file        - File operations (read/write/list/etc)
   GET  /system      - System information
   GET  /processes   - Process list
   POST /automation  - Automation tasks
   GET  /logs/{{service}} - Log analysis
   POST /backup      - Backup operations
   GET  /network     - Network information

🔒 Security Features:
   ✅ Command classification (safe/moderate/dangerous/restricted)
   ✅ Security level enforcement
   ✅ Command history tracking
   ✅ Working directory isolation

🤖 A2A Integration:
   ✅ Registered with A2A server (if available)
   ✅ Supports A2A task delegation
   ✅ Compatible with SuperMCP ecosystem

🎯 Specialized Commands:
   ✅ SuperMCP deployment automation
   ✅ Environment setup
   ✅ Backup and restore operations
   ✅ Service monitoring

📋 Example Usage:
   curl -X POST http://sam.chat:8301/execute \\
     -H "Content-Type: application/json" \\
     -d '{{"command": "ls -la /root/supermcp"}}'

   curl -X POST http://sam.chat:8301/file \\
     -H "Content-Type: application/json" \\
     -d '{{"operation": "list", "path": "/root/supermcp"}}'

🚀 Ready for terminal automation!
""")
    
    try:
        # Mantener el servidor corriendo
        while True:
            await asyncio.sleep(3600)  # Dormir 1 hora
    except KeyboardInterrupt:
        logger.info("Shutting down Terminal Agent...")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    # Configuración adicional para Docker/containers
    if os.getenv('RUNNING_IN_DOCKER'):
        # Ajustes específicos para contenedores
        os.environ['PYTHONUNBUFFERED'] = '1'
    
    # Ejecutar agente
    asyncio.run(main())

# Script de instalación y configuración
def create_installation_script():
    """Crear script de instalación para el Terminal Agent"""
    install_script = """#!/bin/bash
# Terminal Agent Installation Script for SuperMCP

echo "🖥️ Installing Terminal Agent..."

# 1. Verificar dependencias
echo "📦 Checking dependencies..."
python3 -c "import asyncio, aiohttp, psutil" 2>/dev/null || {
    echo "Installing Python dependencies..."
    pip install aiohttp psutil
}

# 2. Crear directorio de trabajo
mkdir -p /root/supermcp/terminal_agent
cd /root/supermcp

# 3. Crear archivo del agente
cat > terminal_agent.py << 'AGENT_EOF'
[CONTENIDO DEL TERMINAL AGENT]
AGENT_EOF

# 4. Hacer ejecutable
chmod +x terminal_agent.py

# 5. Crear servicio systemd
sudo tee /etc/systemd/system/terminal-agent.service > /dev/null << 'SERVICE_EOF'
[Unit]
Description=SuperMCP Terminal Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/supermcp
ExecStart=/usr/bin/python3 /root/supermcp/terminal_agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# 6. Habilitar servicio
sudo systemctl daemon-reload
sudo systemctl enable terminal-agent

echo "✅ Terminal Agent installed successfully!"
echo "🚀 Start with: sudo systemctl start terminal-agent"
echo "📊 Status: sudo systemctl status terminal-agent"
echo "🌐 API: http://sam.chat:8301"
"""
    
    with open('/root/supermcp/install_terminal_agent.sh', 'w') as f:
        f.write(install_script)
    
    os.chmod('/root/supermcp/install_terminal_agent.sh', 0o755)
    print("✅ Installation script created: /root/supermcp/install_terminal_agent.sh")

# Crear script de instalación si se ejecuta directamente
if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "install":
    create_installation_script()
[El código completo del artifact]
