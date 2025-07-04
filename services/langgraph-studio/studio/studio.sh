#!/bin/bash
# LangGraph Studio Launcher
# Script para iniciar LangGraph Studio con diferentes configuraciones

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuración por defecto
DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT="8123"
DEFAULT_DEBUG_PORT="8124"

# Función para mostrar banner
show_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🎯 LangGraph Studio                       ║"
    echo "║              Visual Debugging for Agentius MCP              ║"
    echo "║                                                              ║"
    echo "║  🔍 Real-time debugging    📊 Visual analytics              ║"
    echo "║  🎨 Graph visualization    🔥 Contradiction analysis        ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Función para mostrar ayuda
show_help() {
    echo -e "${CYAN}Usage: $0 [COMMAND] [OPTIONS]${NC}"
    echo ""
    echo -e "${YELLOW}Commands:${NC}"
    echo "  start       Start LangGraph Studio server"
    echo "  dev         Start in development mode with hot reload"
    echo "  debug       Start with enhanced debugging"
    echo "  tunnel      Start with public tunnel (ngrok-like)"
    echo "  export      Export all graphs and documentation"
    echo "  health      Check system health"
    echo "  stop        Stop running servers"
    echo "  help        Show this help message"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo "  --host HOST         Host to bind to (default: $DEFAULT_HOST)"
    echo "  --port PORT         Port to bind to (default: $DEFAULT_PORT)"
    echo "  --debug-port PORT   Debug WebSocket port (default: $DEFAULT_DEBUG_PORT)"
    echo "  --no-browser        Don't open browser automatically"
    echo "  --verbose           Enable verbose logging"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0 start                    # Start with defaults"
    echo "  $0 dev --port 8080          # Development mode on port 8080"
    echo "  $0 debug --verbose          # Debug mode with verbose logging"
    echo "  $0 tunnel                   # Start with public access"
}

# Función para verificar dependencias
check_dependencies() {
    echo -e "${BLUE}🔍 Checking dependencies...${NC}"
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 not found${NC}"
        exit 1
    fi
    
    # Verificar pip packages
    local packages=("fastapi" "uvicorn" "websockets" "langgraph")
    for package in "${packages[@]}"; do
        if ! python3 -c "import $package" &> /dev/null; then
            echo -e "${YELLOW}⚠️  Installing missing package: $package${NC}"
            pip3 install "$package"
        fi
    done
    
    echo -e "${GREEN}✅ Dependencies OK${NC}"
}

# Función para verificar puertos
check_ports() {
    local host=$1
    local port=$2
    local debug_port=$3
    
    echo -e "${BLUE}🔍 Checking ports...${NC}"
    
    # Verificar puerto principal
    if lsof -i:$port &> /dev/null; then
        echo -e "${YELLOW}⚠️  Port $port is already in use${NC}"
        echo -e "${CYAN}Do you want to kill the process? (y/N)${NC}"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            lsof -ti:$port | xargs kill -9
            echo -e "${GREEN}✅ Port $port freed${NC}"
        else
            echo -e "${RED}❌ Cannot start on port $port${NC}"
            exit 1
        fi
    fi
    
    # Verificar puerto de debug
    if lsof -i:$debug_port &> /dev/null; then
        echo -e "${YELLOW}⚠️  Debug port $debug_port is already in use${NC}"
        lsof -ti:$debug_port | xargs kill -9
        echo -e "${GREEN}✅ Debug port $debug_port freed${NC}"
    fi
    
    echo -e "${GREEN}✅ Ports available${NC}"
}

# Función para exportar grafos
export_graphs() {
    echo -e "${BLUE}📊 Exporting graphs and documentation...${NC}"
    
    cd "$(dirname "$0")"
    python3 -c "
from export_manager import export_manager
from studio_config import studio_config

# Exportar sistema completo
exports = export_manager.export_complete_system_graph()
print('✅ Graphs exported:')
for format_type, path in exports.items():
    print(f'  {format_type}: {path}')

# Crear configuración de dashboard
dashboard_config = export_manager.create_studio_dashboard_config()
print(f'✅ Dashboard config: {dashboard_config}')

# Generar README
readme_content = '''# LangGraph Studio - MCP System

## 🎯 Overview
This directory contains LangGraph Studio configuration and exported visualizations for the MCP system.

## 📊 Available Graphs
- Complete MCP Agent with full orchestration flow
- Reasoning Agent with contradiction analysis
- Builder Agent for content/code generation

## 🔧 Studio Configuration
- Development Server: ./langgraph_system/studio/studio.sh start
- Local Access: http://sam.chat:8123
- Debug Port: 8124

## 📈 Monitoring & Analytics
- Langwatch Integration: Active
- Session Tracking: Enabled
- Performance Metrics: Real-time

Generated by LangGraph Studio Export Manager
'''
readme_path = 'langgraph_system/studio/studio_exports/README.md'
with open(readme_path, 'w') as f:
    f.write(readme_content)
print(f'✅ README generated: {readme_path}')
"
    
    echo -e "${GREEN}✅ Export completed${NC}"
}

# Función para verificar salud del sistema
check_health() {
    echo -e "${BLUE}❤️  Checking system health...${NC}"
    
    # Verificar si el servidor está corriendo
    local port=${1:-$DEFAULT_PORT}
    if curl -s "http://sam.chat:$port/health" &> /dev/null; then
        echo -e "${GREEN}✅ Studio server is running${NC}"
        curl -s "http://sam.chat:$port/health" | python3 -m json.tool
    else
        echo -e "${YELLOW}⚠️  Studio server is not running${NC}"
    fi
    
    # Verificar archivos del sistema
    local project_root="$(dirname "$(dirname "$(dirname "$0")")")"
    local required_files=(
        "langgraph.json"
        "langgraph_system/agents/complete_mcp_agent.py"
        "langgraph_system/studio/studio_config.py"
    )
    
    for file in "${required_files[@]}"; do
        if [[ -f "$project_root/$file" ]]; then
            echo -e "${GREEN}✅ $file${NC}"
        else
            echo -e "${RED}❌ $file missing${NC}"
        fi
    done
}

# Función para detener servidores
stop_servers() {
    echo -e "${BLUE}🛑 Stopping servers...${NC}"
    
    # Detener por puertos conocidos
    local ports=("8123" "8124" "8125")
    for port in "${ports[@]}"; do
        if lsof -i:$port &> /dev/null; then
            echo -e "${YELLOW}Stopping process on port $port${NC}"
            lsof -ti:$port | xargs kill -9
        fi
    done
    
    # Detener por nombre de proceso
    pkill -f "studio_server.py" || true
    pkill -f "langgraph dev" || true
    
    echo -e "${GREEN}✅ Servers stopped${NC}"
}

# Función para abrir navegador
open_browser() {
    local url=$1
    local no_browser=$2
    
    if [[ "$no_browser" != "true" ]]; then
        echo -e "${CYAN}🌐 Opening browser at $url${NC}"
        if command -v xdg-open &> /dev/null; then
            xdg-open "$url" &> /dev/null &
        elif command -v open &> /dev/null; then
            open "$url" &> /dev/null &
        else
            echo -e "${YELLOW}⚠️  Cannot open browser automatically${NC}"
            echo -e "${CYAN}Please open: $url${NC}"
        fi
    fi
}

# Función principal para iniciar servidor
start_server() {
    local mode=$1
    local host=$2
    local port=$3
    local debug_port=$4
    local no_browser=$5
    local verbose=$6
    
    echo -e "${BLUE}🚀 Starting LangGraph Studio in $mode mode...${NC}"
    
    # Configurar logging
    local log_level="info"
    if [[ "$verbose" == "true" ]]; then
        log_level="debug"
    fi
    
    # Cambiar al directorio del proyecto
    local project_root="$(dirname "$(dirname "$(dirname "$0")")")"
    cd "$project_root"
    
    # Exportar grafos antes de iniciar
    export_graphs
    
    # Configurar variables de entorno
    export LANGWATCH_API_KEY="${LANGWATCH_API_KEY:-sk-lw-Phst1zhb5LdSlPad1Q6KYSYHvR1L4OgTTs4HBcvJSa3DR9fu}"
    export STUDIO_HOST="$host"
    export STUDIO_PORT="$port"
    export DEBUG_PORT="$debug_port"
    
    # Mostrar información de inicio
    echo -e "${GREEN}✅ Configuration:${NC}"
    echo -e "  Host: $host"
    echo -e "  Port: $port"
    echo -e "  Debug Port: $debug_port"
    echo -e "  Mode: $mode"
    echo -e "  Log Level: $log_level"
    echo ""
    
    # URLs de acceso
    local studio_url="http://$host:$port"
    local debug_url="ws://$host:$debug_port"
    
    echo -e "${CYAN}🌐 Access URLs:${NC}"
    echo -e "  Studio: $studio_url"
    echo -e "  Debug WebSocket: $debug_url"
    echo -e "  API Docs: $studio_url/docs"
    echo -e "  Health Check: $studio_url/health"
    echo ""
    
    # Abrir navegador
    open_browser "$studio_url" "$no_browser"
    
    # Iniciar servidor según el modo
    case $mode in
        "dev")
            echo -e "${YELLOW}🔥 Development mode with hot reload${NC}"
            python3 langgraph_system/studio/studio_server.py \
                --host "$host" \
                --port "$port" \
                --debug
            ;;
        "debug")
            echo -e "${YELLOW}🐛 Enhanced debugging mode${NC}"
            python3 langgraph_system/studio/studio_server.py \
                --host "$host" \
                --port "$port" \
                --debug
            ;;
        "tunnel")
            echo -e "${YELLOW}🌍 Public tunnel mode${NC}"
            # Usar langgraph dev con tunnel
            langgraph dev \
                --host "$host" \
                --port "$port" \
                --tunnel \
                --no-browser
            ;;
        *)
            echo -e "${YELLOW}🎯 Standard mode${NC}"
            python3 langgraph_system/studio/studio_server.py \
                --host "$host" \
                --port "$port"
            ;;
    esac
}

# Parsear argumentos
COMMAND=""
HOST="$DEFAULT_HOST"
PORT="$DEFAULT_PORT"
DEBUG_PORT="$DEFAULT_DEBUG_PORT"
NO_BROWSER="false"
VERBOSE="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        start|dev|debug|tunnel|export|health|stop|help)
            COMMAND="$1"
            shift
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --debug-port)
            DEBUG_PORT="$2"
            shift 2
            ;;
        --no-browser)
            NO_BROWSER="true"
            shift
            ;;
        --verbose)
            VERBOSE="true"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Mostrar banner
show_banner

# Ejecutar comando
case $COMMAND in
    "start")
        check_dependencies
        check_ports "$HOST" "$PORT" "$DEBUG_PORT"
        start_server "standard" "$HOST" "$PORT" "$DEBUG_PORT" "$NO_BROWSER" "$VERBOSE"
        ;;
    "dev")
        check_dependencies
        check_ports "$HOST" "$PORT" "$DEBUG_PORT"
        start_server "dev" "$HOST" "$PORT" "$DEBUG_PORT" "$NO_BROWSER" "$VERBOSE"
        ;;
    "debug")
        check_dependencies
        check_ports "$HOST" "$PORT" "$DEBUG_PORT"
        start_server "debug" "$HOST" "$PORT" "$DEBUG_PORT" "$NO_BROWSER" "$VERBOSE"
        ;;
    "tunnel")
        check_dependencies
        check_ports "$HOST" "$PORT" "$DEBUG_PORT"
        start_server "tunnel" "$HOST" "$PORT" "$DEBUG_PORT" "$NO_BROWSER" "$VERBOSE"
        ;;
    "export")
        export_graphs
        ;;
    "health")
        check_health "$PORT"
        ;;
    "stop")
        stop_servers
        ;;
    "help"|"")
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        show_help
        exit 1
        ;;
esac

