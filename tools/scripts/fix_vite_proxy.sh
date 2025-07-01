#!/bin/bash

# 🔧 FIX VITE PROXY - CORREGIR PUERTO BACKEND
# El frontend está configurado para puerto 3001 pero backend está en 3000

echo "🔧 FIX VITE PROXY - PUERTO INCORRECTO IDENTIFICADO"
echo "=================================================="

cd /root/supermcp/frontend

# 1. Backup del archivo original
echo "💾 Creando backup de vite.config.js..."
cp vite.config.js vite.config.js.backup.$(date +%Y%m%d_%H%M%S)

# 2. Mostrar configuración actual problemática
echo "❌ CONFIGURACIÓN ACTUAL (PROBLEMÁTICA):"
echo "======================================="
cat vite.config.js

# 3. Crear configuración corregida
echo ""
echo "✅ CREANDO CONFIGURACIÓN CORREGIDA:"
echo "==================================="

cat > vite.config.js << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Proxy /api requests to the backend server running on port 3000 (CORREGIDO)
      '/api': {
        target: 'http://localhost:3000',  // ✅ PUERTO CORREGIDO: 3000 en lugar de 3001
        changeOrigin: true,
        // secure: false, // Uncomment if backend is not HTTPS
        // rewrite: (path) => path.replace(/^\/api/, '') // Uncomment if backend doesn't expect /api prefix
      }
    }
  }
})
EOF

echo "✅ CONFIGURACIÓN CORREGIDA:"
echo "=========================="
cat vite.config.js

# 4. Reiniciar frontend para aplicar cambios
echo ""
echo "🔄 REINICIANDO FRONTEND PARA APLICAR CAMBIOS..."
echo "==============================================="

# Encontrar y matar proceso del frontend
FRONTEND_PID=$(ps aux | grep "vite.*5173" | grep -v grep | awk '{print $2}')
if [ -n "$FRONTEND_PID" ]; then
    echo "🛑 Deteniendo frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID
    sleep 3
else
    echo "⚠️  No se encontró proceso frontend activo"
fi

# Iniciar frontend con nueva configuración
echo "🚀 Iniciando frontend con configuración corregida..."
nohup npm run dev -- --port 5173 --host 0.0.0.0 > ../frontend_fixed.log 2>&1 &
NEW_FRONTEND_PID=$!

echo "🔄 Frontend iniciado con PID: $NEW_FRONTEND_PID"

# Esperar que esté listo
echo "⏳ Esperando que frontend esté listo..."
for i in {1..20}; do
    if netstat -tlnp | grep -q ":5173"; then
        echo "✅ Frontend listo en puerto 5173"
        break
    fi
    echo "  ⏳ Intento $i/20..."
    sleep 3
done

# 5. Verificar que el cambio se aplicó
echo ""
echo "🧪 VERIFICANDO QUE EL CAMBIO SE APLICÓ"
echo "====================================="

# Test de conectividad después del fix
echo "🔍 Test de conectividad frontend → backend (después del fix):"

# Dar tiempo al frontend para inicializar completamente
sleep 5

# Verificar logs del frontend
echo "📝 Últimas líneas del log frontend:"
tail -10 ../frontend_fixed.log

# Test manual del proxy
echo ""
echo "🧪 Test manual del proxy Vite:"
curl -s -H "Host: localhost:5173" "http://localhost:5173/api/tools" | head -1 || echo "Proxy aún inicializando..."

cd /root/supermcp

# 6. Resumen del fix
echo ""
echo "🎯 RESUMEN DEL FIX"
echo "=================="

echo "❌ PROBLEMA IDENTIFICADO:"
echo "  • Frontend configurado para puerto 3001"
echo "  • Backend funcionando en puerto 3000"
echo "  • Error: 'Failed to load tools from backend'"

echo ""
echo "✅ FIX APLICADO:"
echo "  • vite.config.js corregido: 3001 → 3000"
echo "  • Frontend reiniciado con nueva configuración"
echo "  • Proxy ahora apunta al backend correcto"

echo ""
echo "🎉 RESULTADO ESPERADO:"
echo "  • El error 'Failed to load tools from backend' debería desaparecer"
echo "  • Las herramientas MCP deberían cargar correctamente"
echo "  • Frontend → /api/tools → Backend funcionando"

echo ""
echo "🌐 PRUEBA AHORA EL FRONTEND:"
echo "  URL: http://65.109.54.94:5173"
echo "  Sección: Herramientas MCP"
echo "  Esperado: 4 herramientas (firecrawl, telegram, notion, github)"

echo ""
if netstat -tlnp | grep -q ":5173"; then
    echo "🎊 ✅ FRONTEND FUNCIONANDO - READY PARA PRUEBA"
else
    echo "⚠️  Frontend aún iniciando - esperar 30 segundos más"
fi

echo ""
echo "💡 Si aún hay problemas, verificar:"
echo "  • Console del navegador (F12)"
echo "  • Logs: tail -f frontend_fixed.log"
echo "  • Test manual: curl http://localhost:5173/api/tools"
