#!/bin/bash

echo "🚀 Demo de Claudia MCP Frontend"
echo "=============================="

# 1. Ver estado del sistema
echo "1. 🏥 Estado del Sistema:"
curl -s http://localhost:8013/health | jq '.'

echo ""
echo "2. 🤖 Agentes Disponibles:"
curl -s http://localhost:8013/agents | jq '.[] | {name: .name, services: .ultramcp_services}'

echo ""
echo "3. 📊 Métricas Actuales:"
curl -s http://localhost:8013/metrics | jq '.'

echo ""
echo "4. 🔍 Ejecuciones Recientes:"
curl -s http://localhost:8013/executions | jq '.[] | {agent: .agent_name, status: .status, created: .created_at}'

echo ""
echo "5. 📋 Templates Disponibles:"
curl -s http://localhost:8013/agents/templates | jq 'keys'

echo ""
echo "🎯 ¡Claudia MCP Frontend está funcionando!"
echo "Puedes instalar más agentes y ejecutar análisis completos."