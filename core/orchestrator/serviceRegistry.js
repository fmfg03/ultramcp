/**
 * Service Registry for UltraMCP
 * 
 * Manages service discovery, registration, health monitoring, and capability matching.
 * Provides intelligent service selection based on task requirements.
 */

const fs = require('fs').promises;
const path = require('path');
const yaml = require('js-yaml');

class ServiceRegistry {
    constructor(eventBus) {
        this.eventBus = eventBus;
        this.services = new Map();
        this.capabilities = new Map();
        this.healthStatus = new Map();
        this.serviceMetrics = new Map();
        this.loadBalancer = new ServiceLoadBalancer();
        
        // Service discovery configuration
        this.config = {
            serviceDirectories: ['./services', './apps/backend/src/services'],
            healthCheckInterval: 30000, // 30 seconds
            healthCheckTimeout: 10000,  // 10 seconds
            maxRetries: 3,
            defaultCapabilities: ['general']
        };
    }

    /**
     * Discover and register all services
     */
    async discoverServices() {
        console.log('🔍 Starting service discovery...');
        
        for (const directory of this.config.serviceDirectories) {
            try {
                await this.discoverServicesInDirectory(directory);
            } catch (error) {
                console.warn(`Warning: Could not discover services in ${directory}:`, error.message);
            }
        }
        
        console.log(`✅ Service discovery complete. Found ${this.services.size} services.`);
        this.eventBus.emitSystemEvent('service.discovery.completed', {
            serviceCount: this.services.size,
            services: Array.from(this.services.keys())
        });
    }

    /**
     * Discover services in a specific directory
     */
    async discoverServicesInDirectory(directory) {
        try {
            const entries = await fs.readdir(directory, { withFileTypes: true });
            
            for (const entry of entries) {
                if (entry.isDirectory()) {
                    const servicePath = path.join(directory, entry.name);
                    await this.discoverServiceInPath(servicePath, entry.name);
                }
            }
        } catch (error) {
            // Directory might not exist, that's okay
            if (error.code !== 'ENOENT') {
                throw error;
            }
        }
    }

    /**
     * Discover and load a single service
     */
    async discoverServiceInPath(servicePath, serviceName) {
        try {
            // Look for service configuration
            const configPath = path.join(servicePath, 'service.json');
            const yamlConfigPath = path.join(servicePath, 'service.yml');
            const jsServicePath = path.join(servicePath, 'service.js');
            const indexPath = path.join(servicePath, 'index.js');
            
            let serviceConfig = null;
            
            // Try to load configuration
            if (await this.fileExists(configPath)) {
                const configContent = await fs.readFile(configPath, 'utf8');
                serviceConfig = JSON.parse(configContent);
            } else if (await this.fileExists(yamlConfigPath)) {
                const configContent = await fs.readFile(yamlConfigPath, 'utf8');
                serviceConfig = yaml.load(configContent);
            } else {
                // Create default configuration
                serviceConfig = {
                    id: serviceName,
                    name: serviceName,
                    type: 'service',
                    capabilities: this.inferCapabilities(serviceName),
                    path: servicePath
                };
            }
            
            // Try to load service implementation
            let servicePath_impl = null;
            if (await this.fileExists(jsServicePath)) {
                servicePath_impl = jsServicePath;
            } else if (await this.fileExists(indexPath)) {
                servicePath_impl = indexPath;
            }
            
            if (servicePath_impl) {
                await this.registerServiceFromPath(serviceConfig, servicePath_impl);
            } else {
                // Register as external service (might be in different language)
                await this.registerExternalService(serviceConfig);
            }
            
        } catch (error) {
            console.warn(`Failed to discover service in ${servicePath}:`, error.message);
        }
    }

    /**
     * Register a service from a JavaScript file
     */
    async registerServiceFromPath(config, servicePath) {
        try {
            // Load the service class/function
            const ServiceClass = require(path.resolve(servicePath));
            
            let service;
            if (typeof ServiceClass === 'function') {
                service = new ServiceClass(config);
            } else if (ServiceClass.default && typeof ServiceClass.default === 'function') {
                service = new ServiceClass.default(config);
            } else {
                throw new Error('Service module must export a class or function');
            }
            
            await this.registerService(service);
            
        } catch (error) {
            console.warn(`Failed to register service from ${servicePath}:`, error.message);
        }
    }

    /**
     * Register an external service (Python, etc.)
     */
    async registerExternalService(config) {
        const service = new ExternalServiceWrapper(config);
        await this.registerService(service);
    }

    /**
     * Register a service instance
     */
    async registerService(service) {
        try {
            // Validate service interface
            this.validateServiceInterface(service);
            
            // Initialize the service
            await service.initialize();
            
            // Store service and metadata
            this.services.set(service.id, service);
            this.capabilities.set(service.id, service.getCapabilities());
            this.healthStatus.set(service.id, 'unknown');
            this.serviceMetrics.set(service.id, {
                requestCount: 0,
                successCount: 0,
                failureCount: 0,
                averageResponseTime: 0,
                lastRequestTime: null,
                registeredAt: new Date().toISOString()
            });
            
            // Perform initial health check
            await this.performHealthCheck(service.id);
            
            this.eventBus.emitServiceEvent(service.id, 'registered', {
                name: service.name,
                capabilities: service.getCapabilities(),
                metadata: service.getMetadata()
            });
            
            console.log(`✅ Registered service: ${service.id} (${service.name})`);
            
        } catch (error) {
            console.error(`Failed to register service ${service.id}:`, error.message);
            throw error;
        }
    }

    /**
     * Validate that service implements required interface
     */
    validateServiceInterface(service) {
        const requiredMethods = ['initialize', 'execute', 'healthCheck', 'getCapabilities'];
        
        for (const method of requiredMethods) {
            if (typeof service[method] !== 'function') {
                throw new Error(`Service ${service.id} must implement ${method}() method`);
            }
        }
        
        if (!service.id || typeof service.id !== 'string') {
            throw new Error('Service must have a valid string id');
        }
    }

    /**
     * Get a service by ID
     */
    async getService(serviceId) {
        const service = this.services.get(serviceId);
        
        if (!service) {
            throw new Error(`Service ${serviceId} not found`);
        }
        
        if (!this.isHealthy(serviceId)) {
            throw new Error(`Service ${serviceId} is unhealthy`);
        }
        
        return service;
    }

    /**
     * Select services based on task requirements
     */
    selectServices(task, requiredCapabilities = [], options = {}) {
        const capabilities = requiredCapabilities.length > 0 ? 
            requiredCapabilities : this.inferCapabilitiesFromTask(task);
            
        const matchingServices = [];
        
        for (const [serviceId, serviceCaps] of this.capabilities) {
            if (!this.isHealthy(serviceId)) {
                continue; // Skip unhealthy services
            }
            
            const score = this.calculateCompatibilityScore(capabilities, serviceCaps);
            if (score > 0) {
                const service = this.services.get(serviceId);
                const loadScore = this.loadBalancer.getLoadScore(serviceId);
                const finalScore = score * (1 - loadScore); // Lower load = higher score
                
                matchingServices.push({
                    serviceId,
                    service,
                    compatibilityScore: score,
                    loadScore,
                    finalScore,
                    capabilities: serviceCaps
                });
            }
        }
        
        // Sort by final score (higher is better)
        matchingServices.sort((a, b) => b.finalScore - a.finalScore);
        
        // Apply selection strategy
        const strategy = options.strategy || 'best-match';
        const count = options.count || (strategy === 'all' ? matchingServices.length : 1);
        
        switch (strategy) {
            case 'round-robin':
                return this.loadBalancer.selectRoundRobin(matchingServices, count);
            case 'least-loaded':
                return matchingServices.slice(0, count).map(m => m.service);
            case 'all':
                return matchingServices.map(m => m.service);
            default: // 'best-match'
                return matchingServices.slice(0, count).map(m => m.service);
        }
    }

    /**
     * Calculate compatibility score between required and available capabilities
     */
    calculateCompatibilityScore(required, available) {
        if (required.length === 0) {
            return available.includes('general') ? 1 : 0.5;
        }
        
        let exactMatches = 0;
        let partialMatches = 0;
        
        for (const requiredCap of required) {
            if (available.includes(requiredCap)) {
                exactMatches++;
            } else {
                // Check for partial matches (e.g., 'llm' matches 'llm-openai')
                const partialMatch = available.find(cap => 
                    cap.includes(requiredCap) || requiredCap.includes(cap)
                );
                if (partialMatch) {
                    partialMatches++;
                }
            }
        }
        
        // Score: exact matches are worth 1.0, partial matches are worth 0.5
        const score = (exactMatches + (partialMatches * 0.5)) / required.length;
        return Math.min(score, 1.0);
    }

    /**
     * Infer capabilities from task content
     */
    inferCapabilitiesFromTask(task) {
        const capabilities = [];
        const content = (task.content || task.message || '').toLowerCase();
        const type = (task.type || '').toLowerCase();
        
        // Task type mapping
        const typeCapabilities = {
            'debate': ['debate', 'multi-llm', 'consensus'],
            'analysis': ['analysis', 'reasoning', 'data-processing'],
            'chat': ['chat', 'conversation', 'llm'],
            'code': ['code-generation', 'programming', 'analysis'],
            'voice': ['voice-processing', 'speech-to-text', 'text-to-speech'],
            'search': ['search', 'information-retrieval'],
            'translation': ['translation', 'language-processing']
        };
        
        if (typeCapabilities[type]) {
            capabilities.push(...typeCapabilities[type]);
        }
        
        // Content-based inference
        if (content.includes('debate') || content.includes('discuss')) {
            capabilities.push('debate', 'multi-llm');
        }
        
        if (content.includes('analyze') || content.includes('analysis')) {
            capabilities.push('analysis', 'reasoning');
        }
        
        if (content.includes('code') || content.includes('program')) {
            capabilities.push('code-generation', 'programming');
        }
        
        if (content.includes('translate') || content.includes('translation')) {
            capabilities.push('translation');
        }
        
        if (content.includes('voice') || content.includes('speak') || content.includes('audio')) {
            capabilities.push('voice-processing');
        }
        
        // Tools-based inference
        if (task.tools && task.tools.length > 0) {
            capabilities.push('tool-execution');
            
            // Specific tool capabilities
            for (const tool of task.tools) {
                if (tool.includes('github')) capabilities.push('github-integration');
                if (tool.includes('email')) capabilities.push('email-processing');
                if (tool.includes('calendar')) capabilities.push('calendar-management');
            }
        }
        
        // Default to general if no specific capabilities found
        return capabilities.length > 0 ? [...new Set(capabilities)] : ['general'];
    }

    /**
     * Infer capabilities from service name/path
     */
    inferCapabilities(serviceName) {
        const name = serviceName.toLowerCase();
        
        if (name.includes('cod') || name.includes('debate')) {
            return ['debate', 'multi-llm', 'consensus'];
        }
        
        if (name.includes('llm') || name.includes('openai') || name.includes('anthropic')) {
            return ['llm', 'text-generation', 'chat'];
        }
        
        if (name.includes('voice') || name.includes('speech')) {
            return ['voice-processing', 'speech-to-text', 'text-to-speech'];
        }
        
        if (name.includes('memory') || name.includes('analyzer')) {
            return ['memory-management', 'analysis', 'data-processing'];
        }
        
        if (name.includes('mcp') || name.includes('adapter')) {
            return ['mcp-integration', 'tool-execution'];
        }
        
        return ['general'];
    }

    /**
     * Perform health check on a specific service
     */
    async performHealthCheck(serviceId) {
        const service = this.services.get(serviceId);
        if (!service) return false;
        
        try {
            const startTime = Date.now();
            const isHealthy = await Promise.race([
                service.healthCheck(),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Health check timeout')), 
                    this.config.healthCheckTimeout)
                )
            ]);
            
            const responseTime = Date.now() - startTime;
            const previousStatus = this.healthStatus.get(serviceId);
            
            this.healthStatus.set(serviceId, isHealthy ? 'healthy' : 'unhealthy');
            
            // Update metrics
            const metrics = this.serviceMetrics.get(serviceId);
            if (metrics) {
                metrics.lastHealthCheck = new Date().toISOString();
                metrics.healthCheckResponseTime = responseTime;
            }
            
            // Emit events on status change
            if (previousStatus !== 'healthy' && isHealthy) {
                this.eventBus.emitServiceEvent(serviceId, 'recovered', { responseTime });
            } else if (previousStatus === 'healthy' && !isHealthy) {
                this.eventBus.emitServiceEvent(serviceId, 'failed', { 
                    error: 'Health check failed',
                    responseTime 
                });
            }
            
            return isHealthy;
            
        } catch (error) {
            this.healthStatus.set(serviceId, 'unhealthy');
            this.eventBus.emitServiceEvent(serviceId, 'failed', { 
                error: error.message 
            });
            return false;
        }
    }

    /**
     * Perform health checks on all services
     */
    async performHealthChecks() {
        const healthChecks = [];
        
        for (const serviceId of this.services.keys()) {
            healthChecks.push(this.performHealthCheck(serviceId));
        }
        
        const results = await Promise.allSettled(healthChecks);
        const healthy = results.filter(r => r.status === 'fulfilled' && r.value).length;
        const total = results.length;
        
        this.eventBus.emitSystemEvent('health.check.completed', {
            healthy,
            total,
            healthRate: total > 0 ? healthy / total : 0
        });
        
        return { healthy, total };
    }

    /**
     * Check if a service is healthy
     */
    isHealthy(serviceId) {
        return this.healthStatus.get(serviceId) === 'healthy';
    }

    /**
     * Get health status of all services
     */
    getHealthStatus() {
        const status = {};
        for (const [serviceId, health] of this.healthStatus) {
            const service = this.services.get(serviceId);
            status[serviceId] = {
                status: health,
                name: service?.name || serviceId,
                capabilities: this.capabilities.get(serviceId) || [],
                metrics: this.serviceMetrics.get(serviceId)
            };
        }
        return status;
    }

    /**
     * Update service metrics after execution
     */
    updateServiceMetrics(serviceId, success, responseTime) {
        const metrics = this.serviceMetrics.get(serviceId);
        if (!metrics) return;
        
        metrics.requestCount++;
        metrics.lastRequestTime = new Date().toISOString();
        
        if (success) {
            metrics.successCount++;
        } else {
            metrics.failureCount++;
        }
        
        // Update average response time
        const totalRequests = metrics.requestCount;
        const currentAvg = metrics.averageResponseTime;
        metrics.averageResponseTime = ((currentAvg * (totalRequests - 1)) + responseTime) / totalRequests;
        
        // Update load balancer
        this.loadBalancer.updateLoad(serviceId, responseTime);
    }

    /**
     * Get service count
     */
    getServiceCount() {
        return this.services.size;
    }

    /**
     * Get all services
     */
    getAllServices() {
        const services = [];
        for (const [serviceId, service] of this.services) {
            services.push({
                id: serviceId,
                name: service.name,
                capabilities: this.capabilities.get(serviceId),
                health: this.healthStatus.get(serviceId),
                metrics: this.serviceMetrics.get(serviceId)
            });
        }
        return services;
    }

    /**
     * Unregister a service
     */
    async unregisterService(serviceId) {
        const service = this.services.get(serviceId);
        if (!service) return false;
        
        try {
            if (typeof service.shutdown === 'function') {
                await service.shutdown();
            }
            
            this.services.delete(serviceId);
            this.capabilities.delete(serviceId);
            this.healthStatus.delete(serviceId);
            this.serviceMetrics.delete(serviceId);
            
            this.eventBus.emitServiceEvent(serviceId, 'unregistered', {});
            
            return true;
        } catch (error) {
            console.error(`Failed to unregister service ${serviceId}:`, error);
            return false;
        }
    }

    /**
     * Shutdown all services
     */
    async shutdown() {
        console.log('🛑 Shutting down service registry...');
        
        const shutdownPromises = [];
        for (const [serviceId, service] of this.services) {
            if (typeof service.shutdown === 'function') {
                shutdownPromises.push(
                    service.shutdown().catch(error => 
                        console.warn(`Failed to shutdown service ${serviceId}:`, error.message)
                    )
                );
            }
        }
        
        await Promise.allSettled(shutdownPromises);
        
        this.services.clear();
        this.capabilities.clear();
        this.healthStatus.clear();
        this.serviceMetrics.clear();
        
        console.log('✅ Service registry shutdown complete');
    }

    /**
     * Utility method to check if file exists
     */
    async fileExists(filePath) {
        try {
            await fs.access(filePath);
            return true;
        } catch {
            return false;
        }
    }
}

/**
 * External Service Wrapper for non-JavaScript services
 */
class ExternalServiceWrapper {
    constructor(config) {
        this.id = config.id;
        this.name = config.name || config.id;
        this.capabilities = config.capabilities || ['general'];
        this.config = config;
        this.type = config.type || 'external';
        this.initialized = false;
    }

    async initialize() {
        // For external services, we might need to check if they're running
        // This could involve HTTP health checks, process checks, etc.
        this.initialized = true;
    }

    async execute(input, context) {
        // External service execution would depend on the service type
        // Could be HTTP calls, process execution, message queues, etc.
        throw new Error(`External service execution not implemented for ${this.id}`);
    }

    async healthCheck() {
        // Basic health check - could be enhanced for specific service types
        return this.initialized;
    }

    getCapabilities() {
        return this.capabilities;
    }

    getMetadata() {
        return {
            id: this.id,
            name: this.name,
            type: this.type,
            capabilities: this.capabilities,
            initialized: this.initialized
        };
    }

    async shutdown() {
        this.initialized = false;
    }
}

/**
 * Load Balancer for service selection
 */
class ServiceLoadBalancer {
    constructor() {
        this.loads = new Map(); // serviceId -> load score (0-1)
        this.lastSelection = new Map(); // for round-robin
    }

    updateLoad(serviceId, responseTime) {
        // Simple load calculation based on response time
        // Could be enhanced with actual CPU/memory metrics
        const normalizedTime = Math.min(responseTime / 10000, 1); // 10s = 100% load
        this.loads.set(serviceId, normalizedTime);
    }

    getLoadScore(serviceId) {
        return this.loads.get(serviceId) || 0;
    }

    selectRoundRobin(services, count) {
        if (services.length === 0) return [];
        
        const key = services.map(s => s.serviceId).join(',');
        const lastIndex = this.lastSelection.get(key) || 0;
        const selected = [];
        
        for (let i = 0; i < count && i < services.length; i++) {
            const index = (lastIndex + i) % services.length;
            selected.push(services[index].service);
        }
        
        this.lastSelection.set(key, (lastIndex + count) % services.length);
        return selected;
    }
}

module.exports = ServiceRegistry;