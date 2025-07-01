#!/usr/bin/env python3
"""
Memory Injection System for Manus-Sam Orchestration
Provides persistent context and state management for Sam agent
"""

import json
import os
import glob
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib

class MemoryInjectionSystem:
    """
    Sistema de inyección de memoria que prepara contexto completo para Sam
    """
    
    def __init__(self, project_root: str = "/root/supermcp"):
        self.project_root = project_root
        self.context_cache = {}
        self.last_update = None
        
    def get_project_state(self) -> Dict[str, Any]:
        """
        Obtiene el estado completo del proyecto para inyectar a Sam
        """
        context = {
            "timestamp": datetime.now().isoformat(),
            "project_root": self.project_root,
            "system_info": self._get_system_info(),
            "file_structure": self._get_file_structure(),
            "todo_lists": self._get_todo_lists(),
            "key_references": self._get_key_references(),
            "environment_config": self._get_environment_config(),
            "agent_status": self._get_agent_status(),
            "recent_changes": self._get_recent_changes()
        }
        
        return context
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Información del sistema y servicios activos"""
        return {
            "domain": "sam.chat",
            "api_endpoint": "https://api.sam.chat",
            "frontend_url": "https://sam.chat",
            "studio_url": "https://studio.sam.chat",
            "dev_url": "https://dev.sam.chat",
            "ollama_models": [
                "mistral:7b-instruct",
                "llama3.1:8b-instruct", 
                "deepseek-coder:6.7b-instruct",
                "qwen2.5-coder:7b-instruct",
                "qwen2.5:14b-instruct"
            ],
            "external_apis": ["openai", "claude", "perplexity", "supabase"],
            "active_ports": {
                "nginx": 80,
                "nginx_ssl": 443,
                "backend": 3000,
                "frontend": 5174,
                "studio": 8123,
                "ollama": 11434,
                "postgres": 5432,
                "redis": 6379
            }
        }
    
    def _get_file_structure(self) -> Dict[str, Any]:
        """Estructura del árbol de archivos del proyecto"""
        structure = {}
        
        # Directorios principales
        main_dirs = [
            "backend", "frontend", "mcp-frontend", "langgraph_system",
            "adapters", "config", "docs", "integrations", "src"
        ]
        
        for dir_name in main_dirs:
            dir_path = os.path.join(self.project_root, dir_name)
            if os.path.exists(dir_path):
                structure[dir_name] = self._scan_directory(dir_path, max_depth=2)
        
        # Archivos importantes en root
        important_files = [
            "README.md", "MCP_ARCHITECTURE.md", "AGENTS_CATALOG.md",
            "langgraph.json", "docker-compose.yml", ".env",
            "package.json", "todo.md"
        ]
        
        structure["root_files"] = []
        for file_name in important_files:
            file_path = os.path.join(self.project_root, file_name)
            if os.path.exists(file_path):
                structure["root_files"].append({
                    "name": file_name,
                    "size": os.path.getsize(file_path),
                    "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                })
        
        return structure
    
    def _scan_directory(self, path: str, max_depth: int = 2, current_depth: int = 0) -> Dict[str, Any]:
        """Escanea un directorio recursivamente hasta max_depth"""
        if current_depth >= max_depth:
            return {"truncated": True}
        
        result = {"files": [], "directories": {}}
        
        try:
            for item in os.listdir(path):
                if item.startswith('.'):
                    continue
                    
                item_path = os.path.join(path, item)
                
                if os.path.isfile(item_path):
                    result["files"].append({
                        "name": item,
                        "size": os.path.getsize(item_path),
                        "extension": os.path.splitext(item)[1]
                    })
                elif os.path.isdir(item_path):
                    result["directories"][item] = self._scan_directory(
                        item_path, max_depth, current_depth + 1
                    )
        except PermissionError:
            result["error"] = "Permission denied"
        
        return result
    
    def _get_todo_lists(self) -> Dict[str, List[str]]:
        """Obtiene todas las listas de tareas del proyecto"""
        todo_files = glob.glob(os.path.join(self.project_root, "*todo*.md"))
        todos = {}
        
        for todo_file in todo_files:
            try:
                with open(todo_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    todos[os.path.basename(todo_file)] = self._parse_todo_content(content)
            except Exception as e:
                todos[os.path.basename(todo_file)] = [f"Error reading file: {str(e)}"]
        
        return todos
    
    def _parse_todo_content(self, content: str) -> List[str]:
        """Parsea el contenido de un archivo todo.md"""
        lines = content.split('\n')
        todos = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('- [ ]') or line.startswith('- [x]'):
                todos.append(line)
            elif line.startswith('##') or line.startswith('###'):
                todos.append(line)
        
        return todos[:20]  # Limitar a 20 items más importantes
    
    def _get_key_references(self) -> Dict[str, str]:
        """Obtiene contenido de archivos de referencia clave"""
        key_files = [
            "README.md",
            "MCP_ARCHITECTURE.md", 
            "AGENTS_CATALOG.md",
            "SECURITY_IMPLEMENTATION.md",
            "langgraph.json"
        ]
        
        references = {}
        
        for file_name in key_files:
            file_path = os.path.join(self.project_root, file_name)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Limitar contenido para evitar overflow
                        if len(content) > 5000:
                            content = content[:5000] + "\n... [TRUNCATED]"
                        references[file_name] = content
                except Exception as e:
                    references[file_name] = f"Error reading file: {str(e)}"
        
        return references
    
    def _get_environment_config(self) -> Dict[str, Any]:
        """Obtiene configuración del entorno (sin secrets)"""
        env_config = {
            "node_version": "20.18.0",
            "python_version": "3.11.0rc1",
            "docker_available": True,
            "ssl_enabled": True,
            "domain_configured": True
        }
        
        # Leer variables de entorno públicas
        env_file = os.path.join(self.project_root, ".env")
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r') as f:
                    lines = f.readlines()
                    public_vars = {}
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, _ = line.split('=', 1)
                                # Solo incluir variables no sensibles
                                if not any(secret in key.lower() for secret in ['key', 'secret', 'password', 'token']):
                                    public_vars[key] = "[CONFIGURED]"
                                else:
                                    public_vars[key] = "[HIDDEN]"
                    env_config["environment_variables"] = public_vars
            except Exception as e:
                env_config["environment_error"] = str(e)
        
        return env_config
    
    def _get_agent_status(self) -> Dict[str, Any]:
        """Estado de los agentes y servicios"""
        return {
            "ollama_status": "active",
            "local_models": {
                "mistral": "loaded",
                "llama3.1": "loaded", 
                "deepseek-coder": "loaded",
                "qwen2.5-coder": "loaded",
                "qwen2.5": "loaded"
            },
            "external_apis": {
                "openai": "configured",
                "claude": "configured",
                "perplexity": "configured",
                "supabase": "configured"
            },
            "services": {
                "nginx": "active",
                "backend": "active",
                "frontend": "active",
                "postgres": "active",
                "redis": "active"
            }
        }
    
    def _get_recent_changes(self) -> List[Dict[str, Any]]:
        """Obtiene cambios recientes del repositorio git"""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "log", "--oneline", "-10"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                commits = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(' ', 1)
                        if len(parts) == 2:
                            commits.append({
                                "hash": parts[0],
                                "message": parts[1]
                            })
                return commits
        except Exception as e:
            return [{"error": f"Could not get git log: {str(e)}"}]
        
        return []
    
    def create_system_message(self) -> str:
        """
        Crea el system message completo para inyectar a Sam
        """
        context = self.get_project_state()
        
        system_message = f"""
# SAM AGENT - SYSTEM CONTEXT INJECTION
## Timestamp: {context['timestamp']}

You are Sam, an autonomous AI agent operating within the MCP (Model Context Protocol) system.
This is your complete project context and memory injection.

## 🏗️ PROJECT ARCHITECTURE
- **Domain**: {context['system_info']['domain']}
- **API Endpoint**: {context['system_info']['api_endpoint']}
- **Project Root**: {context['project_root']}

## 🤖 AVAILABLE MODELS (LOCAL FIRST)
Local Models (Ollama - PRIORITIZE THESE):
{chr(10).join(f"- {model}" for model in context['system_info']['ollama_models'])}

External APIs (Fallback only):
{chr(10).join(f"- {api}" for api in context['system_info']['external_apis'])}

## 📁 PROJECT STRUCTURE
Key directories and their contents are mapped in your context.
Main components: backend, frontend, langgraph_system, adapters, integrations.

## 📋 CURRENT TODO LISTS
{self._format_todos(context['todo_lists'])}

## 🔧 SYSTEM STATUS
Services: {', '.join(f"{k}:{v}" for k, v in context['system_info']['active_ports'].items())}
All services are operational and ready for your commands.

## 🧠 OPERATIONAL DIRECTIVES
1. **Local Models First**: Always try Ollama models before external APIs
2. **Autonomous Operation**: Execute tasks without asking for clarification unless truly ambiguous
3. **Context Awareness**: You have full project knowledge - use it
4. **Batch Processing**: Handle multiple related tasks in sequence
5. **Error Recovery**: If local models fail, fallback to external APIs automatically

## 📚 KEY REFERENCES LOADED
You have access to README.md, MCP_ARCHITECTURE.md, AGENTS_CATALOG.md, and other critical documentation.

Remember: You are operating with FULL CONTEXT. Act autonomously and efficiently.
"""
        
        return system_message
    
    def _format_todos(self, todos: Dict[str, List[str]]) -> str:
        """Formatea las listas de tareas para el system message"""
        formatted = []
        for file_name, items in todos.items():
            if items:
                formatted.append(f"\n### {file_name}")
                for item in items[:5]:  # Top 5 items per file
                    formatted.append(f"  {item}")
        
        return '\n'.join(formatted) if formatted else "No pending todos found."
    
    def create_payload(self) -> Dict[str, Any]:
        """
        Crea el payload completo para enviar a Sam
        """
        context = self.get_project_state()
        
        return {
            "system_message": self.create_system_message(),
            "context": context,
            "memory_hash": self._generate_context_hash(context),
            "injection_timestamp": datetime.now().isoformat()
        }
    
    def _generate_context_hash(self, context: Dict[str, Any]) -> str:
        """Genera hash del contexto para detectar cambios"""
        context_str = json.dumps(context, sort_keys=True)
        return hashlib.md5(context_str.encode()).hexdigest()

# Función de utilidad para uso directo
def inject_memory_to_sam(project_root: str = "/root/supermcp") -> Dict[str, Any]:
    """
    Función de conveniencia para inyectar memoria a Sam
    """
    memory_system = MemoryInjectionSystem(project_root)
    return memory_system.create_payload()

if __name__ == "__main__":
    # Test del sistema
    memory_system = MemoryInjectionSystem()
    payload = memory_system.create_payload()
    
    print("=== MEMORY INJECTION SYSTEM TEST ===")
    print(f"System Message Length: {len(payload['system_message'])} characters")
    print(f"Context Hash: {payload['memory_hash']}")
    print(f"Injection Timestamp: {payload['injection_timestamp']}")
    
    # Guardar ejemplo
    with open("/tmp/sam_memory_injection_example.json", "w") as f:
        json.dump(payload, f, indent=2)
    
    print("Example payload saved to /tmp/sam_memory_injection_example.json")

