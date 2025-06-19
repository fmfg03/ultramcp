# Web Client Híbrido - MCP DevTool

## Objetivo
Desarrollar un cockpit tipo DevTool para operar el sistema MCP con las siguientes funcionalidades:

## Fase 1: Configurar proyecto React con Tailwind y ShadCN ⏳
- [ ] Crear proyecto React con Vite
- [ ] Instalar y configurar Tailwind CSS
- [ ] Instalar y configurar ShadCN/UI
- [ ] Configurar WebSocket client
- [ ] Estructura base de directorios

## Fase 2: Implementar componentes base y layout principal ✅
- [x] Layout principal con sidebar y header
- [x] Componentes base de ShadCN
- [x] Sistema de routing
- [x] Tema dark/light
- [x] Responsive design
- [x] Contextos WebSocket y MCP
- [x] Dashboard principal funcional
## Fase 3: Crear panel de ejecución de agentes MCP ✅
- [x] Input de prompt con editor avanzado
- [x] Selector de agente (builder, reasoning, etc.)
- [x] Live response streaming simulado
- [x] Configuración de parámetros (temperature, tokens)
- [x] Estados de ejecución dinámicos
- [x] Historial de ejecuciones
- [x] Controles de copy/download
- [x] Indicadores visuales de estadoar visualización de grafo LangGraph
- [ ] Diagrama del flujo actual
- [ ] Estado de cada nodo (tick/skip/error)
- [ ] Navegación interactiva del grafo
- [ ] Zoom y pan del diagrama
- [ ] Detalles de nodos en hover

## Fase 5: Desarrollar panel Langwatch y debugger
- [ ] Logs en tiempo real
- [ ] Contradicciones detectadas
- [ ] Métricas de uso (tokens, duración, modelo)
- [ ] Playback de sesiones
- [ ] Reinyección de input corregido
- [ ] Análisis de fallos

## Fase 6: Integrar CLI in-browser y WebSocket
- [ ] Terminal in-browser funcional
- [ ] Comandos: run-agent, trace-session, analyze-error
- [ ] WebSocket para streaming en tiempo real
- [ ] Autocompletado de comandos
- [ ] Historial de comandos

## Fase 7: Probar y documentar Web Client
- [ ] Pruebas de integración
- [ ] Documentación de uso
- [ ] Guías para developers
- [ ] Optimización de rendimiento

## Funcionalidades Clave
1. **Ejecución de agentes MCP**: Input, selección, live response
2. **Visualización LangGraph**: Diagrama, estado de nodos
3. **Panel Langwatch**: Logs, contradicciones, métricas
4. **Debugger interactivo**: Playback, reinyección, análisis
5. **CLI integrado**: Terminal, comandos especializados

## Stack Tecnológico
- **Frontend**: React + Vite
- **Styling**: Tailwind CSS
- **Components**: ShadCN/UI
- **Real-time**: WebSocket
- **Visualización**: Mermaid.js / D3.js
- **Terminal**: Xterm.js

## Estado Actual
- ⏳ Configurando proyecto React con Tailwind y ShadCN

