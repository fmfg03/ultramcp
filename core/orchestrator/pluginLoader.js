/**
 * Plugin Loader for UltraMCP
 * 
 * Manages dynamic loading of plugins, services, workflows, and adapters
 * with dependency resolution and lifecycle management.
 */

const fs = require('fs').promises;
const path = require('path');
const yaml = require('js-yaml');

class PluginLoader {
    constructor(orchestrator) {
        this.orchestrator = orchestrator;
        this.plugins = new Map();
        this.dependencies = new Map(); // plugin -> dependencies
        this.dependents = new Map(); // plugin -> dependents
        this.loadOrder = [];
        
        this.config = {
            pluginDirectories: [
                './plugins',
                './services',
                './adapters',
                './workflows/plugins'
            ],
            enableHotReload: process.env.NODE_ENV === 'development',
            watchInterval: 5000, // 5 seconds
            maxLoadTime: 30000, // 30 seconds
            allowUnsafe: false
        };

        // Plugin watchers for hot reload
        this.watchers = new Map();
    }

    /**
     * Load all plugins from configured directories
     */
    async loadPlugins() {
        console.log('🔌 Loading plugins...');
        
        const discoveredPlugins = new Map();
        
        // Discover all plugins first
        for (const directory of this.config.pluginDirectories) {
            try {
                await this.discoverPluginsInDirectory(directory, discoveredPlugins);
            } catch (error) {
                console.warn(`Warning: Could not discover plugins in ${directory}:`, error.message);
            }
        }
        
        // Resolve dependencies and determine load order
        this.resolveDependencies(discoveredPlugins);
        
        // Load plugins in dependency order
        await this.loadPluginsInOrder(discoveredPlugins);
        
        // Start hot reload if enabled
        if (this.config.enableHotReload) {
            this.startHotReload();
        }
        
        console.log(`✅ Loaded ${this.plugins.size} plugins`);
        this.orchestrator.eventBus.emitSystemEvent('plugins.loaded', {
            count: this.plugins.size,
            plugins: Array.from(this.plugins.keys())
        });
    }

    /**
     * Discover plugins in a directory
     */
    async discoverPluginsInDirectory(directory, discoveredPlugins) {
        try {
            // Handle glob patterns in directory paths
            if (directory.includes('*')) {
                return await this.discoverPluginsWithGlob(directory, discoveredPlugins);
            }
            
            const entries = await fs.readdir(directory, { withFileTypes: true });
            
            for (const entry of entries) {
                if (entry.isDirectory()) {
                    const pluginPath = path.join(directory, entry.name);
                    await this.discoverPlugin(pluginPath, discoveredPlugins);
                }
            }
        } catch (error) {
            if (error.code !== 'ENOENT') {
                throw error;
            }
        }
    }

    /**
     * Discover plugins with glob patterns
     */
    async discoverPluginsWithGlob(globPattern, discoveredPlugins) {
        const parts = globPattern.split('*');
        const basePath = parts[0];
        const suffix = parts[1] || '';
        
        try {
            const entries = await fs.readdir(basePath, { withFileTypes: true });
            
            for (const entry of entries) {
                if (entry.isDirectory()) {
                    const fullPath = path.join(basePath, entry.name, suffix);
                    try {
                        await this.discoverPluginsInDirectory(fullPath, discoveredPlugins);
                    } catch (error) {
                        // Continue if specific directory doesn't exist
                    }
                }
            }
        } catch (error) {
            if (error.code !== 'ENOENT') {
                throw error;
            }
        }
    }

    /**
     * Discover a single plugin
     */
    async discoverPlugin(pluginPath, discoveredPlugins) {
        try {
            // Look for plugin configuration
            const configFiles = ['plugin.json', 'plugin.yml', 'plugin.yaml'];
            let config = null;
            let configPath = null;
            
            for (const configFile of configFiles) {
                const fullConfigPath = path.join(pluginPath, configFile);
                if (await this.fileExists(fullConfigPath)) {
                    configPath = fullConfigPath;
                    config = await this.loadPluginConfig(fullConfigPath);
                    break;
                }
            }
            
            // If no config found, try to infer plugin type
            if (!config) {
                config = await this.inferPluginConfig(pluginPath);
            }
            
            if (config) {
                config.path = pluginPath;
                config.configPath = configPath;
                discoveredPlugins.set(config.id, config);
                console.log(`🔍 Discovered plugin: ${config.id} (${config.type})`);
            }
            
        } catch (error) {
            console.warn(`Failed to discover plugin in ${pluginPath}:`, error.message);
        }
    }

    /**
     * Load plugin configuration
     */
    async loadPluginConfig(configPath) {
        const content = await fs.readFile(configPath, 'utf8');
        
        if (configPath.endsWith('.json')) {
            return JSON.parse(content);
        } else if (configPath.endsWith('.yml') || configPath.endsWith('.yaml')) {
            return yaml.load(content);
        }
        
        throw new Error(`Unsupported config format: ${configPath}`);
    }

    /**
     * Infer plugin configuration from directory structure
     */
    async inferPluginConfig(pluginPath) {
        const pluginName = path.basename(pluginPath);
        const files = await fs.readdir(pluginPath);
        
        // Determine plugin type based on files
        let type = 'unknown';
        let main = null;
        
        if (files.includes('service.js') || files.includes('index.js')) {
            type = 'service';
            main = files.includes('service.js') ? 'service.js' : 'index.js';
        } else if (files.some(f => f.endsWith('.yml') || f.endsWith('.yaml'))) {
            type = 'workflow';
            main = files.find(f => f.endsWith('.yml') || f.endsWith('.yaml'));
        } else if (files.includes('adapter.js')) {
            type = 'adapter';
            main = 'adapter.js';
        }
        
        if (type === 'unknown') {
            return null;
        }
        
        return {
            id: pluginName,
            name: pluginName,
            version: '1.0.0',
            type,
            main,
            capabilities: this.inferCapabilities(pluginName, type),
            dependencies: [],
            auto_discovered: true
        };
    }

    /**
     * Infer capabilities from plugin name and type
     */
    inferCapabilities(pluginName, type) {
        const name = pluginName.toLowerCase();
        
        const capabilityMap = {
            service: ['general'],
            workflow: ['workflow-execution'],
            adapter: ['adapter-integration']
        };
        
        let capabilities = capabilityMap[type] || ['general'];
        
        // Add specific capabilities based on name
        if (name.includes('llm') || name.includes('ai')) {
            capabilities.push('ai-processing');
        }
        if (name.includes('db') || name.includes('database')) {
            capabilities.push('data-storage');
        }
        if (name.includes('api') || name.includes('rest')) {
            capabilities.push('api-integration');
        }
        if (name.includes('auth')) {
            capabilities.push('authentication');
        }
        
        return capabilities;
    }

    /**
     * Resolve plugin dependencies
     */
    resolveDependencies(discoveredPlugins) {
        // Build dependency graph
        for (const [pluginId, config] of discoveredPlugins) {
            const dependencies = config.dependencies || [];
            this.dependencies.set(pluginId, dependencies);
            
            // Build reverse dependency map
            for (const dep of dependencies) {
                if (!this.dependents.has(dep)) {
                    this.dependents.set(dep, []);
                }
                this.dependents.get(dep).push(pluginId);
            }
        }
        
        // Topological sort to determine load order
        this.loadOrder = this.topologicalSort(discoveredPlugins);
        
        console.log(`📋 Plugin load order: ${this.loadOrder.join(' → ')}`);
    }

    /**
     * Topological sort for dependency resolution
     */
    topologicalSort(plugins) {
        const visited = new Set();
        const tempMarked = new Set();
        const result = [];
        
        const visit = (pluginId) => {
            if (tempMarked.has(pluginId)) {
                throw new Error(`Circular dependency detected involving plugin: ${pluginId}`);
            }
            
            if (!visited.has(pluginId)) {
                tempMarked.add(pluginId);
                
                const dependencies = this.dependencies.get(pluginId) || [];
                for (const dep of dependencies) {
                    if (plugins.has(dep)) {
                        visit(dep);
                    } else {
                        console.warn(`Plugin ${pluginId} depends on missing plugin: ${dep}`);
                    }
                }
                
                tempMarked.delete(pluginId);
                visited.add(pluginId);
                result.push(pluginId);
            }
        };
        
        for (const pluginId of plugins.keys()) {
            if (!visited.has(pluginId)) {
                visit(pluginId);
            }
        }
        
        return result;
    }

    /**
     * Load plugins in dependency order
     */
    async loadPluginsInOrder(discoveredPlugins) {
        for (const pluginId of this.loadOrder) {
            const config = discoveredPlugins.get(pluginId);
            if (config) {
                try {
                    await this.loadPlugin(config);
                } catch (error) {
                    console.error(`Failed to load plugin ${pluginId}:`, error.message);
                    
                    // Skip dependents if this plugin failed
                    const dependents = this.dependents.get(pluginId) || [];
                    for (const dependent of dependents) {
                        console.warn(`Skipping plugin ${dependent} due to failed dependency: ${pluginId}`);
                    }
                }
            }
        }
    }

    /**
     * Load a single plugin
     */
    async loadPlugin(config) {
        const startTime = Date.now();
        
        try {
            console.log(`🔄 Loading plugin: ${config.id}`);
            
            // Validate plugin configuration
            this.validatePluginConfig(config);
            
            let plugin;
            
            // Load plugin based on type
            switch (config.type) {
                case 'service':
                    plugin = await this.loadServicePlugin(config);
                    break;
                case 'workflow':
                    plugin = await this.loadWorkflowPlugin(config);
                    break;
                case 'adapter':
                    plugin = await this.loadAdapterPlugin(config);
                    break;
                default:
                    throw new Error(`Unknown plugin type: ${config.type}`);
            }
            
            // Store plugin info
            this.plugins.set(config.id, {
                config,
                plugin,
                loadTime: Date.now() - startTime,
                loadedAt: new Date().toISOString()
            });
            
            this.orchestrator.eventBus.emitSystemEvent('plugin.loaded', {
                pluginId: config.id,
                type: config.type,
                loadTime: Date.now() - startTime
            });
            
            console.log(`✅ Loaded plugin: ${config.id} (${Date.now() - startTime}ms)`);
            
            return plugin;
            
        } catch (error) {
            this.orchestrator.eventBus.emitSystemEvent('plugin.load.failed', {
                pluginId: config.id,
                error: error.message,
                loadTime: Date.now() - startTime
            });
            
            throw new Error(`Plugin ${config.id} load failed: ${error.message}`);
        }
    }

    /**
     * Load service plugin
     */
    async loadServicePlugin(config) {
        const servicePath = path.join(config.path, config.main || 'service.js');
        
        if (!await this.fileExists(servicePath)) {
            throw new Error(`Service file not found: ${servicePath}`);
        }
        
        // Clear require cache for hot reload
        delete require.cache[require.resolve(path.resolve(servicePath))];
        
        const ServiceClass = require(path.resolve(servicePath));
        
        // Handle different export patterns
        let ServiceConstructor;
        if (typeof ServiceClass === 'function') {
            ServiceConstructor = ServiceClass;
        } else if (ServiceClass.default && typeof ServiceClass.default === 'function') {
            ServiceConstructor = ServiceClass.default;
        } else if (ServiceClass.Service && typeof ServiceClass.Service === 'function') {
            ServiceConstructor = ServiceClass.Service;
        } else {
            throw new Error('Service module must export a class constructor');
        }
        
        // Create service instance
        const serviceConfig = {
            ...config.config,
            id: config.id,
            name: config.name,
            capabilities: config.capabilities
        };
        
        const service = new ServiceConstructor(serviceConfig);
        
        // Register with service registry
        await this.orchestrator.serviceRegistry.registerService(service);
        
        return service;
    }

    /**
     * Load workflow plugin
     */
    async loadWorkflowPlugin(config) {
        const workflowPath = path.join(config.path, config.main || 'workflow.yml');
        
        if (!await this.fileExists(workflowPath)) {
            throw new Error(`Workflow file not found: ${workflowPath}`);
        }
        
        const workflowContent = await fs.readFile(workflowPath, 'utf8');
        const workflow = yaml.load(workflowContent);
        
        // Merge plugin config with workflow definition
        workflow.id = workflow.id || config.id;
        workflow.name = workflow.name || config.name;
        workflow.pluginId = config.id;
        
        // Register with workflow engine
        this.orchestrator.workflowEngine.registerWorkflow(workflow);
        
        return workflow;
    }

    /**
     * Load adapter plugin
     */
    async loadAdapterPlugin(config) {
        const adapterPath = path.join(config.path, config.main || 'adapter.js');
        
        if (!await this.fileExists(adapterPath)) {
            throw new Error(`Adapter file not found: ${adapterPath}`);
        }
        
        // Clear require cache for hot reload
        delete require.cache[require.resolve(path.resolve(adapterPath))];
        
        const AdapterClass = require(path.resolve(adapterPath));
        
        // Handle different export patterns
        let AdapterConstructor;
        if (typeof AdapterClass === 'function') {
            AdapterConstructor = AdapterClass;
        } else if (AdapterClass.default && typeof AdapterClass.default === 'function') {
            AdapterConstructor = AdapterClass.default;
        } else {
            throw new Error('Adapter module must export a class constructor');
        }
        
        // Create adapter instance
        const adapterConfig = {
            ...config.config,
            id: config.id,
            name: config.name,
            capabilities: config.capabilities
        };
        
        const adapter = new AdapterConstructor(adapterConfig);
        
        // Initialize adapter
        if (typeof adapter.initialize === 'function') {
            await adapter.initialize();
        }
        
        return adapter;
    }

    /**
     * Validate plugin configuration
     */
    validatePluginConfig(config) {
        const required = ['id', 'name', 'type'];
        
        for (const field of required) {
            if (!config[field]) {
                throw new Error(`Plugin missing required field: ${field}`);
            }
        }
        
        const validTypes = ['service', 'workflow', 'adapter'];
        if (!validTypes.includes(config.type)) {
            throw new Error(`Invalid plugin type: ${config.type}. Must be one of: ${validTypes.join(', ')}`);
        }
        
        // Security check
        if (!this.config.allowUnsafe && config.unsafe) {
            throw new Error(`Unsafe plugin ${config.id} not allowed`);
        }
    }

    /**
     * Start hot reload monitoring
     */
    startHotReload() {
        console.log('🔥 Hot reload enabled for plugins');
        
        for (const [pluginId, pluginInfo] of this.plugins) {
            const { config } = pluginInfo;
            
            if (config.configPath) {
                this.watchFile(config.configPath, () => {
                    this.reloadPlugin(pluginId);
                });
            }
            
            // Watch main plugin file
            const mainFile = path.join(config.path, config.main || 'index.js');
            if (this.fileExists(mainFile)) {
                this.watchFile(mainFile, () => {
                    this.reloadPlugin(pluginId);
                });
            }
        }
    }

    /**
     * Watch file for changes
     */
    watchFile(filePath, callback) {
        if (this.watchers.has(filePath)) {
            return; // Already watching
        }
        
        const fs = require('fs');
        
        try {
            const watcher = fs.watchFile(filePath, { interval: this.config.watchInterval }, () => {
                console.log(`🔄 File changed: ${filePath}`);
                callback();
            });
            
            this.watchers.set(filePath, watcher);
        } catch (error) {
            console.warn(`Failed to watch file ${filePath}:`, error.message);
        }
    }

    /**
     * Reload a plugin
     */
    async reloadPlugin(pluginId) {
        try {
            console.log(`🔄 Reloading plugin: ${pluginId}`);
            
            // Unload first
            await this.unloadPlugin(pluginId);
            
            // Discover and load again
            const pluginInfo = this.plugins.get(pluginId);
            if (pluginInfo) {
                const config = await this.loadPluginConfig(pluginInfo.config.configPath);
                config.path = pluginInfo.config.path;
                config.configPath = pluginInfo.config.configPath;
                
                await this.loadPlugin(config);
                
                this.orchestrator.eventBus.emitSystemEvent('plugin.reloaded', {
                    pluginId
                });
            }
            
        } catch (error) {
            console.error(`Failed to reload plugin ${pluginId}:`, error.message);
        }
    }

    /**
     * Unload a plugin
     */
    async unloadPlugin(pluginId) {
        const pluginInfo = this.plugins.get(pluginId);
        if (!pluginInfo) {
            return false;
        }
        
        try {
            const { config, plugin } = pluginInfo;
            
            // Unload based on type
            switch (config.type) {
                case 'service':
                    await this.orchestrator.serviceRegistry.unregisterService(plugin.id);
                    break;
                case 'workflow':
                    this.orchestrator.workflowEngine.unregisterWorkflow(plugin.id);
                    break;
                case 'adapter':
                    if (typeof plugin.shutdown === 'function') {
                        await plugin.shutdown();
                    }
                    break;
            }
            
            this.plugins.delete(pluginId);
            
            this.orchestrator.eventBus.emitSystemEvent('plugin.unloaded', {
                pluginId,
                type: config.type
            });
            
            console.log(`🗑️ Unloaded plugin: ${pluginId}`);
            return true;
            
        } catch (error) {
            console.error(`Failed to unload plugin ${pluginId}:`, error.message);
            return false;
        }
    }

    /**
     * Get plugin information
     */
    getPlugin(pluginId) {
        return this.plugins.get(pluginId);
    }

    /**
     * Get all plugins
     */
    getAllPlugins() {
        const plugins = [];
        for (const [pluginId, pluginInfo] of this.plugins) {
            plugins.push({
                id: pluginId,
                name: pluginInfo.config.name,
                type: pluginInfo.config.type,
                capabilities: pluginInfo.config.capabilities,
                loadTime: pluginInfo.loadTime,
                loadedAt: pluginInfo.loadedAt
            });
        }
        return plugins;
    }

    /**
     * Get plugin count
     */
    getPluginCount() {
        return this.plugins.size;
    }

    /**
     * Get plugins by type
     */
    getPluginsByType(type) {
        return Array.from(this.plugins.values())
            .filter(p => p.config.type === type)
            .map(p => ({ id: p.config.id, config: p.config, plugin: p.plugin }));
    }

    /**
     * Check if file exists
     */
    async fileExists(filePath) {
        try {
            await fs.access(filePath);
            return true;
        } catch {
            return false;
        }
    }

    /**
     * Stop hot reload and cleanup
     */
    stopHotReload() {
        const fs = require('fs');
        
        for (const [filePath, watcher] of this.watchers) {
            fs.unwatchFile(filePath, watcher);
        }
        
        this.watchers.clear();
        console.log('🛑 Hot reload stopped');
    }

    /**
     * Shutdown plugin loader
     */
    async shutdown() {
        console.log('🛑 Shutting down plugin loader...');
        
        // Stop hot reload
        this.stopHotReload();
        
        // Unload all plugins
        const unloadPromises = [];
        for (const pluginId of this.plugins.keys()) {
            unloadPromises.push(
                this.unloadPlugin(pluginId).catch(error => 
                    console.warn(`Failed to unload plugin ${pluginId}:`, error.message)
                )
            );
        }
        
        await Promise.allSettled(unloadPromises);
        
        this.plugins.clear();
        this.dependencies.clear();
        this.dependents.clear();
        this.loadOrder = [];
        
        console.log('✅ Plugin loader shutdown complete');
    }
}

module.exports = PluginLoader;