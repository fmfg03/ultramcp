"""
LangGraph Studio Configuration and Export Manager
Configura y maneja la exportación de grafos para visualización
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class StudioConfig:
    """Configuración para LangGraph Studio"""
    
    def __init__(self, config_path: str = "langgraph_studio_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Carga la configuración desde archivo"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                return self._default_config()
        except Exception as e:
            logger.warning(f"Error loading config: {e}, using defaults")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Configuración por defecto"""
        return {
            "studio_url": "https://smith.langchain.com",
            "enable_debugging": True,
            "debug_port": 5678,
            "auto_reload": True,
            "host": "0.0.0.0",
            "port": 8123,
            "export_format": "mermaid",
            "export_path": "./langgraph_system/studio/studio_exports/",
            "enable_realtime_debugging": True,
            "langwatch_integration": True,
            "session_tracking": True,
            "performance_metrics": True,
            "hot_reload": True,
            "browser_auto_open": False,
            "tunnel_enabled": True,
            "log_level": "INFO",
            "mermaid_theme": "default",
            "include_metadata": True,
            "include_state_schemas": True,
            "include_edge_conditions": True
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene valor de configuración"""
        return self.config.get(key, default)
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Actualiza configuración"""
        self.config.update(updates)
        self._save_config()
    
    def _save_config(self) -> None:
        """Guarda configuración a archivo"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

class StudioExportManager:
    """Maneja la exportación de grafos para Studio"""
    
    def __init__(self, config: StudioConfig):
        self.config = config
        self.export_path = Path(config.get("export_path", "./studio_exports/"))
        self.export_path.mkdir(parents=True, exist_ok=True)
    
    def export_mermaid_graph(self, graph_name: str, graph_definition: str) -> str:
        """Exporta grafo en formato Mermaid"""
        try:
            mermaid_content = self._generate_mermaid_content(graph_name, graph_definition)
            
            # Guardar archivo
            filename = f"{graph_name}.mmd"
            filepath = self.export_path / filename
            
            with open(filepath, 'w') as f:
                f.write(mermaid_content)
            
            logger.info(f"Mermaid graph exported to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error exporting Mermaid graph: {e}")
            return ""
    
    def _generate_mermaid_content(self, graph_name: str, graph_definition: str) -> str:
        """Genera contenido Mermaid para el grafo"""
        
        # Header del diagrama
        mermaid_content = f"""graph TD
    %% {graph_name.upper()} - MCP System Graph
    %% Generated by LangGraph Studio Export Manager
    
    %% Styling
    classDef startEnd fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef reasoning fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef execution fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef evaluation fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef decision fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef memory fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    
    %% Nodes
    START([🚀 START]):::startEnd
    INIT[🔧 Initialize Session]:::memory
    HEALTH[❤️ Health Check]:::evaluation
    REASON[🧠 Enhanced Reasoning]:::reasoning
    SELECT[🎯 Adaptive Selection]:::decision
    EXECUTE[⚡ Execute LLM]:::execution
    EVALUATE[📊 Enhanced Reward]:::evaluation
    CONTRADICTION[🔥 Contradiction Analysis]:::decision
    RETRY[🔄 Intelligent Retry]:::decision
    FINALIZE[✅ Finalize Results]:::memory
    END([🏁 END]):::startEnd
    
    %% Flow
    START --> INIT
    INIT --> HEALTH
    HEALTH --> REASON
    REASON --> SELECT
    SELECT --> EXECUTE
    EXECUTE --> EVALUATE
    EVALUATE --> CONTRADICTION
    CONTRADICTION --> RETRY
    RETRY --> FINALIZE
    FINALIZE --> END
    
    %% Conditional Edges
    HEALTH -->|❌ Unhealthy| END
    EVALUATE -->|⭐ Score >= 0.8| FINALIZE
    CONTRADICTION -->|🔥 Apply Contradiction| REASON
    RETRY -->|🔄 Retry Needed| SELECT
    RETRY -->|✅ Max Retries| FINALIZE
    
    %% Metadata
    %% Graph: {graph_name}
    %% Nodes: 11
    %% Edges: 13
    %% Features: Reasoning, Reward, Contradiction, Retry, Memory
"""
        
        if self.config.get("include_metadata", True):
            mermaid_content += f"""
    %% Additional Metadata
    %% LangWatch Integration: {self.config.get("langwatch_integration", True)}
    %% Local LLMs: mistral-local, llama-local, deepseek-local
    %% Session Tracking: {self.config.get("session_tracking", True)}
    %% Performance Metrics: {self.config.get("performance_metrics", True)}
"""
        
        return mermaid_content
    
    def export_graph_for_pitch_deck(self, graph_name: str) -> str:
        """Exporta versión simplificada para pitch deck"""
        try:
            simplified_content = f"""graph LR
    %% {graph_name.upper()} - Simplified for Pitch Deck
    
    %% Styling
    classDef input fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    classDef process fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    classDef output fill:#e8f5e8,stroke:#388e3c,stroke-width:3px
    classDef intelligence fill:#fff3e0,stroke:#f57c00,stroke-width:3px
    
    %% Main Flow
    INPUT[📝 User Input]:::input
    REASONING[🧠 AI Reasoning<br/>+ Planning]:::process
    EXECUTION[⚡ Multi-LLM<br/>Execution]:::process
    EVALUATION[🏆 Quality<br/>Assessment]:::intelligence
    CONTRADICTION[🔥 Explicit<br/>Contradiction]:::intelligence
    OUTPUT[✨ Optimized<br/>Result]:::output
    
    %% Flow
    INPUT --> REASONING
    REASONING --> EXECUTION
    EXECUTION --> EVALUATION
    EVALUATION -->|❌ Low Score| CONTRADICTION
    CONTRADICTION --> REASONING
    EVALUATION -->|✅ High Score| OUTPUT
    
    %% Labels
    REASONING -.->|"Auto-detects best model<br/>mistral/llama/deepseek"| EXECUTION
    EVALUATION -.->|"Langwatch tracking<br/>Real-time metrics"| OUTPUT
    CONTRADICTION -.->|"Forces new approach<br/>Learns from failures"| REASONING
"""
            
            # Guardar versión para pitch deck
            filename = f"{graph_name}_pitch_deck.mmd"
            filepath = self.export_path / filename
            
            with open(filepath, 'w') as f:
                f.write(simplified_content)
            
            logger.info(f"Pitch deck graph exported to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error exporting pitch deck graph: {e}")
            return ""
    
    def generate_studio_readme(self) -> str:
        """Genera README para LangGraph Studio"""
        readme_content = f"""# LangGraph Studio - MCP System

## 🎯 Overview
This directory contains LangGraph Studio configuration and exported visualizations for the MCP (Model Context Protocol) system.

## 📊 Available Graphs

### 1. Complete MCP Agent (`mcp_complete_agent`)
- **Full orchestration flow** with all features
- **Reasoning + Reward + Contradiction + Retry**
- **Local LLMs integration** (Mistral, LLaMA, DeepSeek)
- **Langwatch monitoring** throughout

### 2. Reasoning Agent (`mcp_reasoning_agent`)
- **Specialized reasoning** with contradiction
- **Auto-model selection** based on task type
- **Enhanced prompting** with failure analysis

### 3. Builder Agent (`mcp_builder_agent`)
- **Content/code generation** specialist
- **Multiple output formats** (markdown, html, json, code)
- **Build type optimization** (website, code, document, analysis)

## 🔧 Studio Configuration

### Development Server
```bash
langgraph dev --host 0.0.0.0 --port 8123 --tunnel
```

### Studio Access
- **Local**: http://sam.chat:8123
- **Tunnel**: Auto-generated public URL
- **Studio URL**: {self.config.get("studio_url", "https://smith.langchain.com")}

### Debugging
- **Debug Port**: {self.config.get("debug_port", 5678)}
- **Hot Reload**: {self.config.get("hot_reload", True)}
- **Real-time Debugging**: {self.config.get("enable_realtime_debugging", True)}

## 📈 Monitoring & Analytics

### Langwatch Integration
- **API Key**: Configured in .env
- **Session Tracking**: {self.config.get("session_tracking", True)}
- **Performance Metrics**: {self.config.get("performance_metrics", True)}
- **Contradiction Analysis**: Automatic detection and effectiveness measurement

### Key Metrics Tracked
- **Token Usage**: Per model, per session
- **Response Time**: End-to-end latency
- **Quality Scores**: Multi-dimensional evaluation
- **Contradiction Effectiveness**: Improvement after contradiction
- **Retry Patterns**: Success rates and failure analysis

## 🎨 Exported Visualizations

### Mermaid Diagrams
- `mcp_graph.mmd` - Complete system flow
- `mcp_graph_pitch_deck.mmd` - Simplified for presentations

### Usage in Documentation
```markdown
```mermaid
{{% include "studio_exports/mcp_graph.mmd" %}}
```
```

## 🚀 Key Features Visualized

### 1. **Intelligent Routing**
- Auto-detects best LLM for task type
- Fallback mechanisms for model failures
- Load balancing across local models

### 2. **Contradiction-Driven Improvement**
- Detects stagnation and low scores
- Injects explicit contradiction prompts
- Forces new approaches and methodologies

### 3. **Comprehensive Monitoring**
- Real-time performance tracking
- Session-based analytics
- Pattern recognition in failures

### 4. **Adaptive Retry Logic**
- Multiple retry strategies
- Escalation mechanisms
- Intelligent stopping conditions

## 🔍 Debugging Tips

### Studio Debugging
1. **Set breakpoints** in graph nodes
2. **Inspect state** at each step
3. **Monitor LLM calls** in real-time
4. **Analyze contradiction triggers**

### Performance Analysis
1. **Token efficiency** per model
2. **Response time** distribution
3. **Quality score** progression
4. **Retry success** patterns

## 📝 Configuration Files

- `langgraph.json` - Graph definitions and schemas
- `langgraph_studio_config.json` - Studio-specific settings
- `.env` - Environment variables and API keys

## 🎯 Next Steps

1. **Real-time Dashboard** - Live metrics visualization
2. **A/B Testing** - Compare contradiction strategies
3. **Pattern Learning** - ML-based failure prediction
4. **Cross-session Analytics** - User behavior analysis

---

Generated by LangGraph Studio Export Manager
Configuration: {self.config.get("mermaid_theme", "default")} theme
Last updated: {self._get_timestamp()}
"""
        
        readme_path = self.export_path / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        return str(readme_path)
    
    def _get_timestamp(self) -> str:
        """Obtiene timestamp actual"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Configuración global
studio_config = StudioConfig()
export_manager = StudioExportManager(studio_config)

def get_studio_config() -> StudioConfig:
    """Obtiene configuración de Studio"""
    return studio_config

def get_export_manager() -> StudioExportManager:
    """Obtiene manager de exportación"""
    return export_manager

