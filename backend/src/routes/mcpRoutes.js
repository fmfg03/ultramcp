// 🔧 MCP Routes - Endpoints para herramientas MCP
const express = require('express');
const router = express.Router();
const fs = require('fs');
const path = require('path');

// Leer configuración de adaptadores
function loadAdapterConfig() {
    try {
        const configPath = path.join(__dirname, '../../../config/adapter_config.json');
        if (fs.existsSync(configPath)) {
            return JSON.parse(fs.readFileSync(configPath, 'utf8'));
        }
        
        // Fallback - configuración mínima
        return {
            adapters: [
                {
                    name: "system",
                    type: "system",
                    enabled: true,
                    description: "System tools",
                    capabilities: ["health_check", "status"]
                }
            ],
            metadata: {
                version: "1.0.0",
                total_adapters: 1,
                enabled_adapters: 1
            }
        };
    } catch (error) {
        console.error('Error loading adapter config:', error);
        return { adapters: [], metadata: { error: "Failed to load config" } };
    }
}

// GET /api/tools - Obtener todas las herramientas disponibles
router.get('/tools', (req, res) => {
    try {
        const config = loadAdapterConfig();
        
        const tools = config.adapters
            .filter(adapter => adapter.enabled)
            .map(adapter => ({
                id: adapter.name,
                name: adapter.name,
                type: adapter.type,
                description: adapter.description,
                capabilities: adapter.capabilities || [],
                enabled: adapter.enabled,
                status: "available"
            }));

        res.json({
            success: true,
            total: tools.length,
            tools: tools,
            metadata: config.metadata
        });
        
        console.log(`[MCP] Tools endpoint called - returned ${tools.length} tools`);
    } catch (error) {
        console.error('[MCP] Error in /api/tools:', error);
        res.status(500).json({
            success: false,
            error: "Failed to load tools",
            message: error.message
        });
    }
});

// GET /api/adapters - Alias para herramientas (compatibilidad)
router.get('/adapters', (req, res) => {
    try {
        const config = loadAdapterConfig();
        
        res.json({
            success: true,
            adapters: config.adapters,
            metadata: config.metadata
        });
        
        console.log(`[MCP] Adapters endpoint called - returned ${config.adapters.length} adapters`);
    } catch (error) {
        console.error('[MCP] Error in /api/adapters:', error);
        res.status(500).json({
            success: false,
            error: "Failed to load adapters"
        });
    }
});

// POST /api/tools/execute - Ejecutar una herramienta específica
router.post('/tools/execute', (req, res) => {
    try {
        const { tool, action, params } = req.body;
        
        console.log(`[MCP] Execute tool request: ${tool}/${action}`, params);
        
        // Por ahora, simular ejecución exitosa
        // En una implementación completa, aquí se llamaría al adaptador específico
        res.json({
            success: true,
            tool: tool,
            action: action,
            result: `Tool ${tool} executed with action ${action}`,
            timestamp: new Date().toISOString(),
            execution_time: "0.1s"
        });
        
    } catch (error) {
        console.error('[MCP] Error executing tool:', error);
        res.status(500).json({
            success: false,
            error: "Tool execution failed",
            message: error.message
        });
    }
});

// GET /api/tools/:toolId - Obtener información específica de una herramienta
router.get('/tools/:toolId', (req, res) => {
    try {
        const { toolId } = req.params;
        const config = loadAdapterConfig();
        
        const tool = config.adapters.find(adapter => adapter.name === toolId);
        
        if (!tool) {
            return res.status(404).json({
                success: false,
                error: "Tool not found",
                toolId: toolId
            });
        }
        
        res.json({
            success: true,
            tool: {
                id: tool.name,
                name: tool.name,
                type: tool.type,
                description: tool.description,
                capabilities: tool.capabilities || [],
                enabled: tool.enabled,
                config: tool.config || {},
                status: "available"
            }
        });
        
    } catch (error) {
        console.error('[MCP] Error getting tool info:', error);
        res.status(500).json({
            success: false,
            error: "Failed to get tool information"
        });
    }
});

// GET /api/mcp/status - Estado del sistema MCP
router.get('/mcp/status', (req, res) => {
    try {
        const config = loadAdapterConfig();
        const enabledAdapters = config.adapters.filter(a => a.enabled);
        
        res.json({
            success: true,
            mcp_status: "operational",
            total_adapters: config.adapters.length,
            enabled_adapters: enabledAdapters.length,
            adapters: enabledAdapters.map(a => ({
                name: a.name,
                type: a.type,
                status: "ready"
            })),
            timestamp: new Date().toISOString()
        });
        
    } catch (error) {
        console.error('[MCP] Error getting MCP status:', error);
        res.status(500).json({
            success: false,
            error: "Failed to get MCP status"
        });
    }
});

module.exports = router;
