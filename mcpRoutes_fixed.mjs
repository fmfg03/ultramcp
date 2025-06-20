// MCP Routes Module - Fixed ES6 Module Version
// This module handles MCP tool routing and execution

import express from 'express';
import { EventEmitter } from 'events';

const router = express.Router();
const mcpEventEmitter = new EventEmitter();

// MCP Tool Registry
class MCPToolRegistry {
    constructor() {
        this.tools = new Map();
        this.adapters = new Map();
        this.executionHistory = [];
        this.metrics = {
            totalExecutions: 0,
            successfulExecutions: 0,
            failedExecutions: 0,
            averageExecutionTime: 0
        };
    }

    registerTool(toolId, toolConfig) {
        this.tools.set(toolId, {
            ...toolConfig,
            registeredAt: new Date().toISOString(),
            status: 'available'
        });
        
        mcpEventEmitter.emit('tool_registered', { toolId, toolConfig });
        console.log(`[MCP Registry] Tool registered: ${toolId}`);
    }

    unregisterTool(toolId) {
        if (this.tools.has(toolId)) {
            this.tools.delete(toolId);
            mcpEventEmitter.emit('tool_unregistered', { toolId });
            console.log(`[MCP Registry] Tool unregistered: ${toolId}`);
            return true;
        }
        return false;
    }

    getTool(toolId) {
        return this.tools.get(toolId);
    }

    getAllTools() {
        return Array.from(this.tools.values());
    }

    registerAdapter(adapterId, adapterConfig) {
        this.adapters.set(adapterId, {
            ...adapterConfig,
            registeredAt: new Date().toISOString(),
            status: 'connected'
        });
        
        mcpEventEmitter.emit('adapter_registered', { adapterId, adapterConfig });
        console.log(`[MCP Registry] Adapter registered: ${adapterId}`);
    }

    getAllAdapters() {
        return Array.from(this.adapters.values());
    }

    recordExecution(toolId, success, executionTime, result = null, error = null) {
        const execution = {
            toolId,
            success,
            executionTime,
            result,
            error,
            timestamp: new Date().toISOString()
        };

        this.executionHistory.push(execution);
        
        // Keep only last 1000 executions
        if (this.executionHistory.length > 1000) {
            this.executionHistory.shift();
        }

        // Update metrics
        this.metrics.totalExecutions++;
        if (success) {
            this.metrics.successfulExecutions++;
        } else {
            this.metrics.failedExecutions++;
        }

        // Calculate average execution time
        const recentExecutions = this.executionHistory.slice(-100);
        this.metrics.averageExecutionTime = Math.round(
            recentExecutions.reduce((sum, exec) => sum + exec.executionTime, 0) / recentExecutions.length
        );

        mcpEventEmitter.emit('execution_recorded', execution);
    }

    getMetrics() {
        return {
            ...this.metrics,
            successRate: this.metrics.totalExecutions > 0 ? 
                ((this.metrics.successfulExecutions / this.metrics.totalExecutions) * 100).toFixed(2) : 0,
            recentExecutions: this.executionHistory.slice(-10)
        };
    }
}

// Global registry instance
const mcpRegistry = new MCPToolRegistry();

// Initialize default tools
mcpRegistry.registerTool('firecrawl', {
    name: 'Firecrawl',
    description: 'Web scraping and crawling tool with advanced features',
    version: '1.0.0',
    category: 'web',
    parameters: {
        url: { type: 'string', required: true, description: 'URL to crawl' },
        options: { type: 'object', required: false, description: 'Crawling options' }
    },
    capabilities: ['scraping', 'crawling', 'content_extraction']
});

mcpRegistry.registerTool('telegram', {
    name: 'Telegram',
    description: 'Telegram messaging and bot integration',
    version: '1.0.0',
    category: 'messaging',
    parameters: {
        message: { type: 'string', required: true, description: 'Message to send' },
        chat_id: { type: 'string', required: true, description: 'Target chat ID' },
        parse_mode: { type: 'string', required: false, description: 'Message parse mode' }
    },
    capabilities: ['messaging', 'bot_integration', 'file_sharing']
});

mcpRegistry.registerTool('notion', {
    name: 'Notion',
    description: 'Notion workspace integration for pages and databases',
    version: '1.0.0',
    category: 'productivity',
    parameters: {
        action: { type: 'string', required: true, description: 'Action to perform' },
        data: { type: 'object', required: true, description: 'Action data' },
        workspace_id: { type: 'string', required: false, description: 'Target workspace' }
    },
    capabilities: ['page_management', 'database_operations', 'content_creation']
});

mcpRegistry.registerTool('github', {
    name: 'GitHub',
    description: 'GitHub repository management and operations',
    version: '1.0.0',
    category: 'development',
    parameters: {
        action: { type: 'string', required: true, description: 'GitHub action to perform' },
        repository: { type: 'string', required: true, description: 'Target repository' },
        data: { type: 'object', required: false, description: 'Action-specific data' }
    },
    capabilities: ['repository_management', 'issue_tracking', 'pull_requests', 'file_operations']
});

// Initialize default adapters
mcpRegistry.registerAdapter('jupyter', {
    name: 'Jupyter Notebook Adapter',
    description: 'Integration with Jupyter notebooks for code execution',
    type: 'notebook',
    version: '1.0.0',
    capabilities: ['code_execution', 'data_analysis', 'visualization']
});

mcpRegistry.registerAdapter('stagehand', {
    name: 'Stagehand Browser Adapter',
    description: 'Browser automation and web interaction adapter',
    type: 'browser',
    version: '1.0.0',
    capabilities: ['browser_automation', 'web_scraping', 'form_interaction']
});

// MCP Tool Execution Engine
class MCPExecutionEngine {
    constructor(registry) {
        this.registry = registry;
        this.activeExecutions = new Map();
    }

    async executeTool(toolId, parameters, options = {}) {
        const startTime = Date.now();
        const executionId = `exec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        try {
            const tool = this.registry.getTool(toolId);
            if (!tool) {
                throw new Error(`Tool '${toolId}' not found in registry`);
            }

            // Validate parameters
            this.validateParameters(tool, parameters);

            // Mark execution as active
            this.activeExecutions.set(executionId, {
                toolId,
                parameters,
                startTime,
                status: 'running'
            });

            console.log(`[MCP Execution] Starting execution: ${toolId} (${executionId})`);

            // Execute tool based on type
            let result;
            switch (toolId) {
                case 'firecrawl':
                    result = await this.executeFirecrawl(parameters, options);
                    break;
                case 'telegram':
                    result = await this.executeTelegram(parameters, options);
                    break;
                case 'notion':
                    result = await this.executeNotion(parameters, options);
                    break;
                case 'github':
                    result = await this.executeGithub(parameters, options);
                    break;
                default:
                    result = await this.executeGenericTool(toolId, parameters, options);
            }

            const executionTime = Date.now() - startTime;
            
            // Record successful execution
            this.registry.recordExecution(toolId, true, executionTime, result);
            
            // Remove from active executions
            this.activeExecutions.delete(executionId);

            console.log(`[MCP Execution] Completed: ${toolId} (${executionTime}ms)`);

            return {
                success: true,
                executionId,
                toolId,
                parameters,
                result,
                executionTime,
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            const executionTime = Date.now() - startTime;
            
            // Record failed execution
            this.registry.recordExecution(toolId, false, executionTime, null, error.message);
            
            // Remove from active executions
            this.activeExecutions.delete(executionId);

            console.error(`[MCP Execution] Failed: ${toolId} - ${error.message}`);

            throw {
                success: false,
                executionId,
                toolId,
                parameters,
                error: error.message,
                executionTime,
                timestamp: new Date().toISOString()
            };
        }
    }

    validateParameters(tool, parameters) {
        if (!tool.parameters) return;

        for (const [paramName, paramConfig] of Object.entries(tool.parameters)) {
            if (paramConfig.required && !(paramName in parameters)) {
                throw new Error(`Required parameter '${paramName}' is missing`);
            }

            if (paramName in parameters) {
                const paramValue = parameters[paramName];
                const expectedType = paramConfig.type;

                if (expectedType === 'string' && typeof paramValue !== 'string') {
                    throw new Error(`Parameter '${paramName}' must be a string`);
                }
                if (expectedType === 'object' && (typeof paramValue !== 'object' || paramValue === null)) {
                    throw new Error(`Parameter '${paramName}' must be an object`);
                }
                if (expectedType === 'number' && typeof paramValue !== 'number') {
                    throw new Error(`Parameter '${paramName}' must be a number`);
                }
                if (expectedType === 'boolean' && typeof paramValue !== 'boolean') {
                    throw new Error(`Parameter '${paramName}' must be a boolean`);
                }
            }
        }
    }

    async executeFirecrawl(parameters, options) {
        // Simulate realistic execution time
        await this.delay(800 + Math.random() * 1200);

        return {
            url: parameters.url,
            status: 'success',
            data: {
                title: `Page Title for ${parameters.url}`,
                content: `Scraped content from ${parameters.url}. This would contain the actual page content in a real implementation.`,
                links: [
                    `${parameters.url}/page1`,
                    `${parameters.url}/page2`,
                    `${parameters.url}/contact`
                ],
                images: [
                    `${parameters.url}/image1.jpg`,
                    `${parameters.url}/image2.png`
                ],
                metadata: {
                    description: `Meta description for ${parameters.url}`,
                    keywords: ['web', 'scraping', 'content'],
                    author: 'Website Author',
                    published: new Date().toISOString()
                }
            },
            options: parameters.options || {},
            crawled_at: new Date().toISOString(),
            execution_mode: 'simulation'
        };
    }

    async executeTelegram(parameters, options) {
        await this.delay(300 + Math.random() * 700);

        return {
            message_id: Math.floor(Math.random() * 100000),
            chat_id: parameters.chat_id,
            message: parameters.message,
            parse_mode: parameters.parse_mode || 'HTML',
            status: 'sent',
            sent_at: new Date().toISOString(),
            bot_info: {
                username: 'mcp_bot',
                id: 123456789
            },
            execution_mode: 'simulation'
        };
    }

    async executeNotion(parameters, options) {
        await this.delay(600 + Math.random() * 1000);

        const actions = {
            'create_page': {
                page_id: `page_${Math.random().toString(36).substr(2, 12)}`,
                title: parameters.data.title || 'New Page',
                url: `https://notion.so/page_${Math.random().toString(36).substr(2, 12)}`
            },
            'update_page': {
                page_id: parameters.data.page_id || `page_${Math.random().toString(36).substr(2, 12)}`,
                changes: parameters.data.changes || {}
            },
            'create_database': {
                database_id: `db_${Math.random().toString(36).substr(2, 12)}`,
                name: parameters.data.name || 'New Database'
            }
        };

        return {
            action: parameters.action,
            status: 'success',
            result: actions[parameters.action] || { message: 'Action completed' },
            workspace: parameters.workspace_id || 'default_workspace',
            data: parameters.data,
            executed_at: new Date().toISOString(),
            execution_mode: 'simulation'
        };
    }

    async executeGithub(parameters, options) {
        await this.delay(500 + Math.random() * 900);

        const actions = {
            'list_repos': {
                repositories: [
                    { name: 'repo1', full_name: `user/${parameters.repository}`, private: false },
                    { name: 'repo2', full_name: `user/repo2`, private: true }
                ]
            },
            'create_issue': {
                issue_id: Math.floor(Math.random() * 1000),
                title: parameters.data?.title || 'New Issue',
                number: Math.floor(Math.random() * 100),
                url: `https://github.com/${parameters.repository}/issues/${Math.floor(Math.random() * 100)}`
            },
            'create_pr': {
                pr_id: Math.floor(Math.random() * 1000),
                title: parameters.data?.title || 'New Pull Request',
                number: Math.floor(Math.random() * 100),
                url: `https://github.com/${parameters.repository}/pull/${Math.floor(Math.random() * 100)}`
            }
        };

        return {
            action: parameters.action,
            repository: parameters.repository,
            status: 'success',
            result: actions[parameters.action] || { message: 'Action completed' },
            data: parameters.data || {},
            executed_at: new Date().toISOString(),
            execution_mode: 'simulation'
        };
    }

    async executeGenericTool(toolId, parameters, options) {
        await this.delay(400 + Math.random() * 800);

        return {
            tool_id: toolId,
            status: 'executed',
            input_parameters: parameters,
            output: `Generic execution result for ${toolId}`,
            metadata: {
                execution_mode: 'simulation',
                version: '1.0.0',
                capabilities: ['generic_execution']
            },
            executed_at: new Date().toISOString()
        };
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    getActiveExecutions() {
        return Array.from(this.activeExecutions.values());
    }
}

// Global execution engine
const mcpExecutionEngine = new MCPExecutionEngine(mcpRegistry);

// Routes

// Get all tools
router.get('/tools', (req, res) => {
    try {
        const tools = mcpRegistry.getAllTools();
        res.json(tools);
    } catch (error) {
        res.status(500).json({ error: 'Failed to retrieve tools', message: error.message });
    }
});

// Get specific tool
router.get('/tools/:toolId', (req, res) => {
    try {
        const tool = mcpRegistry.getTool(req.params.toolId);
        if (!tool) {
            return res.status(404).json({ error: 'Tool not found', toolId: req.params.toolId });
        }
        res.json(tool);
    } catch (error) {
        res.status(500).json({ error: 'Failed to retrieve tool', message: error.message });
    }
});

// Execute tool
router.post('/tools/execute', async (req, res) => {
    try {
        const { tool, parameters, options } = req.body;

        if (!tool) {
            return res.status(400).json({ error: 'Tool parameter is required' });
        }

        const result = await mcpExecutionEngine.executeTool(tool, parameters || {}, options || {});
        res.json(result);

    } catch (error) {
        if (error.success === false) {
            // This is a structured execution error
            res.status(400).json(error);
        } else {
            // This is an unexpected error
            res.status(500).json({
                error: 'Tool execution failed',
                message: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }
});

// Get all adapters
router.get('/adapters', (req, res) => {
    try {
        const adapters = mcpRegistry.getAllAdapters();
        res.json(adapters);
    } catch (error) {
        res.status(500).json({ error: 'Failed to retrieve adapters', message: error.message });
    }
});

// Get execution metrics
router.get('/metrics', (req, res) => {
    try {
        const metrics = mcpRegistry.getMetrics();
        const activeExecutions = mcpExecutionEngine.getActiveExecutions();
        
        res.json({
            ...metrics,
            activeExecutions: activeExecutions.length,
            activeExecutionDetails: activeExecutions
        });
    } catch (error) {
        res.status(500).json({ error: 'Failed to retrieve metrics', message: error.message });
    }
});

// Register new tool
router.post('/tools/register', (req, res) => {
    try {
        const { toolId, toolConfig } = req.body;

        if (!toolId || !toolConfig) {
            return res.status(400).json({ error: 'toolId and toolConfig are required' });
        }

        mcpRegistry.registerTool(toolId, toolConfig);
        res.json({ success: true, message: 'Tool registered successfully', toolId });

    } catch (error) {
        res.status(500).json({ error: 'Failed to register tool', message: error.message });
    }
});

// Unregister tool
router.delete('/tools/:toolId', (req, res) => {
    try {
        const success = mcpRegistry.unregisterTool(req.params.toolId);
        
        if (success) {
            res.json({ success: true, message: 'Tool unregistered successfully' });
        } else {
            res.status(404).json({ error: 'Tool not found', toolId: req.params.toolId });
        }

    } catch (error) {
        res.status(500).json({ error: 'Failed to unregister tool', message: error.message });
    }
});

// Health check
router.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        tools: mcpRegistry.getAllTools().length,
        adapters: mcpRegistry.getAllAdapters().length,
        activeExecutions: mcpExecutionEngine.getActiveExecutions().length
    });
});

// Export router and registry for external use
export { router as mcpRoutes, mcpRegistry, mcpExecutionEngine, mcpEventEmitter };
export default router;

