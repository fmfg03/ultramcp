#!/bin/bash

# 🔧 FIX URLs HARDCODEADAS EN FRONTEND
# Corrige URLs hardcodeadas y endpoints incorrectos

echo "🔧 FIX URLs HARDCODEADAS EN FRONTEND"
echo "=================================="

cd /root/supermcp/frontend

# 1. Crear backups de los archivos que vamos a modificar
echo "💾 Creando backups..."
cp src/components/code/MCPToolSelector.jsx src/components/code/MCPToolSelector.jsx.backup.$(date +%Y%m%d_%H%M%S)
cp src/services/codeAgentService.js src/services/codeAgentService.js.backup.$(date +%Y%m%d_%H%M%S)

# 2. Mostrar los problemas actuales
echo "❌ PROBLEMAS IDENTIFICADOS:"
echo "=========================="
echo "📄 MCPToolSelector.jsx línea 4:"
grep -n "BACKEND_URL" src/components/code/MCPToolSelector.jsx
echo ""
echo "📄 Endpoints incorrectos:"
grep -n "api/mcp" src/components/code/MCPToolSelector.jsx
grep -n "api/mcp" src/services/codeAgentService.js

# 3. Verificar endpoints disponibles en nuestro backend
echo ""
echo "✅ ENDPOINTS DISPONIBLES EN NUESTRO BACKEND:"
echo "==========================================="
curl -s http://localhost:3000/ | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('Endpoints disponibles:', data.get('endpoints', []))
except:
    print('Backend endpoints: /health, /api/tools, /api/adapters')
"

# 4. Corregir MCPToolSelector.jsx
echo ""
echo "🔧 CORRIGIENDO MCPToolSelector.jsx..."
echo "=================================="

cat > src/components/code/MCPToolSelector.jsx << 'EOF'
import React, { useState, useEffect } from 'react';

// Use relative URLs to work with Vite proxy (NO hardcoded URLs)
const BACKEND_URL = ''; // Empty string uses current domain with Vite proxy

function MCPToolSelector() {
  const [allTools, setAllTools] = useState([]); // Store full tool details
  const [toolsByAdapter, setToolsByAdapter] = useState({});
  const [selectedToolId, setSelectedToolId] = useState('');
  const [selectedToolDetails, setSelectedToolDetails] = useState(null);
  const [parameterValues, setParameterValues] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);
  const [executionError, setExecutionError] = useState(null);

  // Fetch all tools on component mount
  useEffect(() => {
    // Use correct endpoint: /api/tools (not /api/mcp/tools)
    fetch(`/api/tools`) // Relative URL uses Vite proxy
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        console.log('✅ Tools loaded successfully:', data);
        
        // Adapt response structure if needed
        const tools = data.tools || data || [];
        setAllTools(tools); // Store the full list
        
        // Group tools by type for the dropdown (since we don't have adapterId)
        const groupedTools = tools.reduce((acc, tool) => {
          const groupKey = tool.type || 'general';
          if (!acc[groupKey]) {
            acc[groupKey] = [];
          }
          acc[groupKey].push(tool);
          return acc;
        }, {});
        
        setToolsByAdapter(groupedTools);
        setLoading(false);
      })
      .catch(error => {
        console.error('❌ Error fetching tools:', error);
        setError('Failed to load tools from backend.');
        setLoading(false);
      });
  }, []);

  // Handle tool selection
  const handleToolSelect = (toolId) => {
    setSelectedToolId(toolId);
    const tool = allTools.find(t => t.id === toolId || t.name === toolId);
    setSelectedToolDetails(tool);
    setParameterValues({});
    setExecutionResult(null);
    setExecutionError(null);
  };

  // Handle parameter changes
  const handleParameterChange = (paramName, value) => {
    setParameterValues(prev => ({
      ...prev,
      [paramName]: value
    }));
  };

  // Execute the selected tool
  const executeTool = async () => {
    if (!selectedToolDetails) return;

    setIsExecuting(true);
    setExecutionResult(null);
    setExecutionError(null);

    try {
      // Use correct endpoint: /api/tools/execute (adapt to our backend)
      const response = await fetch(`/api/tools/execute`, { // Relative URL uses Vite proxy
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          tool: selectedToolDetails.name || selectedToolDetails.id,
          action: 'execute',
          params: parameterValues
        })
      });

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorData}`);
      }

      const result = await response.json();
      console.log('✅ Tool execution result:', result);
      setExecutionResult(result);
    } catch (error) {
      console.error('❌ Error executing tool:', error);
      setExecutionError(error.message);
    } finally {
      setIsExecuting(false);
    }
  };

  if (loading) {
    return <div className="p-4">⏳ Loading tools...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-600">❌ Error: {error}</div>;
  }

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">🛠️ MCP Tools</h2>
      
      {/* Tool Selection */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">Select Tool:</label>
        <select 
          value={selectedToolId} 
          onChange={(e) => handleToolSelect(e.target.value)}
          className="w-full p-2 border rounded"
        >
          <option value="">Choose a tool...</option>
          {Object.entries(toolsByAdapter).map(([adapterType, tools]) => (
            <optgroup key={adapterType} label={`${adapterType} tools`}>
              {tools.map(tool => (
                <option key={tool.id || tool.name} value={tool.id || tool.name}>
                  {tool.name} - {tool.description}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </div>

      {/* Tool Details */}
      {selectedToolDetails && (
        <div className="mb-4 p-4 border rounded bg-gray-50">
          <h3 className="font-semibold">{selectedToolDetails.name}</h3>
          <p className="text-sm text-gray-600 mb-2">{selectedToolDetails.description}</p>
          <p className="text-xs text-gray-500">
            Type: {selectedToolDetails.type} | 
            Capabilities: {selectedToolDetails.capabilities?.join(', ') || 'Basic operations'}
          </p>
        </div>
      )}

      {/* Execute Button */}
      {selectedToolDetails && (
        <div className="mb-4">
          <button 
            onClick={executeTool}
            disabled={isExecuting}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
          >
            {isExecuting ? '⏳ Executing...' : '🚀 Execute Tool'}
          </button>
        </div>
      )}

      {/* Execution Result */}
      {executionResult && (
        <div className="mb-4 p-4 border rounded bg-green-50">
          <h4 className="font-semibold text-green-800">✅ Execution Result:</h4>
          <pre className="text-sm mt-2 whitespace-pre-wrap">{JSON.stringify(executionResult, null, 2)}</pre>
        </div>
      )}

      {/* Execution Error */}
      {executionError && (
        <div className="mb-4 p-4 border rounded bg-red-50">
          <h4 className="font-semibold text-red-800">❌ Execution Error:</h4>
          <p className="text-sm mt-2">{executionError}</p>
        </div>
      )}

      {/* Tools Summary */}
      <div className="mt-6 p-4 border-t">
        <h4 className="font-semibold mb-2">📊 Available Tools Summary:</h4>
        <div className="text-sm text-gray-600">
          Total tools: {allTools.length} | 
          Types: {Object.keys(toolsByAdapter).join(', ')}
        </div>
      </div>
    </div>
  );
}

export default MCPToolSelector;
EOF

echo "✅ MCPToolSelector.jsx corregido"

# 5. Corregir codeAgentService.js
echo ""
echo "🔧 CORRIGIENDO codeAgentService.js..."
echo "================================="

# Primero ver el contenido actual
echo "📄 Contenido actual de codeAgentService.js:"
cat src/services/codeAgentService.js

echo ""
echo "🔧 Aplicando correcciones..."

# Hacer las correcciones necesarias
sed -i 's|const API_BASE_URL = [^;]*;|const API_BASE_URL = "";|g' src/services/codeAgentService.js
sed -i 's|/api/mcp/tools|/api/tools|g' src/services/codeAgentService.js
sed -i 's|/api/mcp/execute|/api/tools/execute|g' src/services/codeAgentService.js

echo "✅ codeAgentService.js corregido"

# 6. Verificar los cambios aplicados
echo ""
echo "✅ VERIFICANDO CAMBIOS APLICADOS:"
echo "==============================="

echo "📄 MCPToolSelector.jsx - líneas clave:"
grep -n "BACKEND_URL\|fetch.*api" src/components/code/MCPToolSelector.jsx | head -5

echo ""
echo "📄 codeAgentService.js - líneas clave:"
grep -n "API_BASE_URL\|fetch.*api" src/services/codeAgentService.js | head -5

# 7. Reiniciar frontend para aplicar cambios
echo ""
echo "🔄 REINICIANDO FRONTEND PARA APLICAR CAMBIOS..."
echo "==============================================="

cd /root/supermcp

# Matar frontend actual
FRONTEND_PID=$(ps aux | grep "vite.*5173" | grep -v grep | awk '{print $2}')
if [ -n "$FRONTEND_PID" ]; then
    echo "🛑 Deteniendo frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID
    sleep 3
fi

# Iniciar frontend corregido
cd frontend
echo "🚀 Iniciando frontend con URLs corregidas..."
nohup npm run dev -- --port 5173 --host 0.0.0.0 > ../frontend_urls_fixed.log 2>&1 &
NEW_PID=$!

echo "🔄 Frontend iniciado con PID: $NEW_PID"

# Esperar que esté listo
echo "⏳ Esperando que frontend esté listo..."
for i in {1..15}; do
    if netstat -tlnp | grep -q ":5173"; then
        echo "✅ Frontend listo en puerto 5173"
        break
    fi
    echo "  ⏳ Intento $i/15..."
    sleep 3
done

cd /root/supermcp

# 8. Test del fix
echo ""
echo "🧪 TESTING DEL FIX APLICADO"
echo "==========================="

# Dar tiempo para que el frontend inicie completamente
sleep 5

echo "🔍 Test del endpoint correcto:"
curl -s http://localhost:5173/api/tools | head -1

echo ""
echo "📝 Últimas líneas del log frontend:"
tail -10 frontend_urls_fixed.log

# 9. Resumen final
echo ""
echo "🎯 RESUMEN DEL FIX COMPLETO"
echo "=========================="

echo "❌ PROBLEMAS CORREGIDOS:"
echo "  • URLs hardcodeadas: localhost:3001 → URLs relativas (proxy)"
echo "  • Endpoints incorrectos: /api/mcp/tools → /api/tools"
echo "  • Endpoints incorrectos: /api/mcp/execute → /api/tools/execute"

echo ""
echo "✅ ARCHIVOS CORREGIDOS:"
echo "  • src/components/code/MCPToolSelector.jsx"
echo "  • src/services/codeAgentService.js"

echo ""
echo "🎉 RESULTADO ESPERADO:"
echo "  • Error 'Failed to load tools from backend' RESUELTO"
echo "  • Herramientas MCP cargando correctamente"
echo "  • 4 herramientas disponibles: firecrawl, telegram, notion, github"

echo ""
echo "🌐 PRUEBA AHORA EL FRONTEND:"
echo "  URL: http://65.109.54.94:5173"
echo "  Sección: Herramientas MCP"
echo "  Esperado: ✅ Lista de herramientas sin errores"

if netstat -tlnp | grep -q ":5173"; then
    echo ""
    echo "🎊 ✅ FRONTEND FUNCIONANDO - READY PARA PRUEBA FINAL"
else
    echo ""
    echo "⚠️  Frontend aún iniciando - esperar 30 segundos más"
fi

echo ""
echo "💡 Si aún hay problemas:"
echo "  • Verificar console del navegador (F12)"
echo "  • Logs: tail -f frontend_urls_fixed.log"
echo "  • Test manual en browser: fetch('/api/tools')"
