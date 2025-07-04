/**
 * Chain-of-Debate Protocol Adapter for UltraMCP
 * 
 * Integrates the CoD Protocol service with the orchestration system,
 * providing standardized interface for multi-LLM debate functionality.
 */

const { IService } = require('../core/interfaces/IService');
const axios = require('axios');
const path = require('path');

class CoDProtocolAdapter extends IService {
    constructor(config = {}) {
        super({
            id: 'cod-protocol',
            name: 'Chain-of-Debate Protocol',
            capabilities: [
                'ai-processing',
                'multi-llm-orchestration',
                'debate-facilitation',
                'consensus-building',
                'bias-detection',
                'risk-assessment',
                'counterfactual-analysis'
            ],
            version: '2.0.0',
            description: 'Advanced multi-LLM orchestration with adversarial criticism and counterfactual analysis',
            ...config
        });

        this.config = {
            servicePath: config.servicePath || path.join(__dirname, '../services/cod-protocol'),
            apiEndpoint: config.apiEndpoint || 'http://sam.chat:5000',
            pythonExecutable: config.pythonExecutable || 'python',
            enableShadowLLM: config.enableShadowLLM !== false,
            enableCounterfactual: config.enableCounterfactual !== false,
            enableCircuitBreaker: config.enableCircuitBreaker !== false,
            enableTelegramBot: config.enableTelegramBot || false,
            maxDebateRounds: config.maxDebateRounds || 3,
            consensusThreshold: config.consensusThreshold || 0.8,
            ...config
        };

        this.pythonProcess = null;
        this.isServiceRunning = false;
        this.lastHealthCheck = null;
        this.circuitBreakerState = 'closed'; // closed, open, half-open
        this.failureCount = 0;
        this.lastFailureTime = null;
    }

    /**
     * Initialize the CoD Protocol service
     */
    async initialize() {
        this.log('info', 'Initializing Chain-of-Debate Protocol adapter...');
        
        try {
            // Validate configuration
            this.validateConfig();
            
            // Start Python service if not already running
            await this.startPythonService();
            
            // Wait for service to be ready
            await this.waitForServiceReady();
            
            this.initialized = true;
            this.log('info', 'CoD Protocol adapter initialized successfully');
            
        } catch (error) {
            this.log('error', 'Failed to initialize CoD Protocol adapter', { error: error.message });
            throw this.createError(
                `CoD Protocol initialization failed: ${error.message}`,
                'INIT_ERROR'
            );
        }
    }

    /**
     * Execute CoD Protocol operation
     */
    async execute(input, context) {
        this.log('debug', 'Executing CoD Protocol operation', { 
            operation: input.operation,
            participants: input.participants?.length 
        });

        // Check circuit breaker
        if (this.circuitBreakerState === 'open') {
            throw this.createError(
                'CoD Protocol service is currently unavailable (circuit breaker open)',
                'SERVICE_UNAVAILABLE'
            );
        }

        const startTime = Date.now();
        
        try {
            let result;
            
            switch (input.operation) {
                case 'debate':
                    result = await this.executeDebate(input, context);
                    break;
                case 'consensus':
                    result = await this.buildConsensus(input, context);
                    break;
                case 'shadow_analysis':
                    result = await this.performShadowAnalysis(input, context);
                    break;
                case 'counterfactual_audit':
                    result = await this.performCounterfactualAudit(input, context);
                    break;
                case 'risk_assessment':
                    result = await this.performRiskAssessment(input, context);
                    break;
                default:
                    throw this.createError(
                        `Unknown CoD Protocol operation: ${input.operation}`,
                        'INVALID_OPERATION'
                    );
            }

            // Reset circuit breaker on success
            this.failureCount = 0;
            if (this.circuitBreakerState === 'half-open') {
                this.circuitBreakerState = 'closed';
                this.log('info', 'Circuit breaker reset to closed state');
            }

            const duration = Date.now() - startTime;
            this.log('debug', 'CoD Protocol operation completed', { 
                operation: input.operation,
                duration: `${duration}ms`
            });

            return result;

        } catch (error) {
            this.handleExecutionError(error);
            throw error;
        }
    }

    /**
     * Execute multi-LLM debate
     */
    async executeDebate(input, context) {
        const requestData = {
            operation: 'debate',
            query: input.query,
            participants: input.participants || ['gpt-4', 'claude-3', 'gemini-pro'],
            max_rounds: input.maxRounds || this.config.maxDebateRounds,
            enable_shadow_llm: this.config.enableShadowLLM,
            context: {
                user_id: context.userId,
                session_id: context.sessionId,
                task_id: context.taskId
            }
        };

        const response = await this.makeAPIRequest('/api/cod/debate', requestData);
        
        return {
            debate_id: response.debate_id,
            rounds: response.rounds,
            consensus: response.consensus,
            shadow_analysis: response.shadow_analysis,
            confidence_score: response.confidence_score,
            bias_detected: response.bias_detected,
            risk_level: response.risk_level
        };
    }

    /**
     * Build consensus from multiple perspectives
     */
    async buildConsensus(input, context) {
        const requestData = {
            operation: 'consensus',
            perspectives: input.perspectives,
            threshold: input.threshold || this.config.consensusThreshold,
            enable_counterfactual: this.config.enableCounterfactual,
            context: {
                user_id: context.userId,
                session_id: context.sessionId,
                task_id: context.taskId
            }
        };

        const response = await this.makeAPIRequest('/api/cod/consensus', requestData);
        
        return {
            consensus_text: response.consensus_text,
            agreement_score: response.agreement_score,
            dissenting_views: response.dissenting_views,
            counterfactual_scenarios: response.counterfactual_scenarios,
            confidence_level: response.confidence_level
        };
    }

    /**
     * Perform Shadow LLM analysis
     */
    async performShadowAnalysis(input, context) {
        if (!this.config.enableShadowLLM) {
            throw this.createError('Shadow LLM analysis is disabled', 'FEATURE_DISABLED');
        }

        const requestData = {
            operation: 'shadow_analysis',
            content: input.content,
            analysis_type: input.analysisType || 'full',
            context: {
                user_id: context.userId,
                session_id: context.sessionId,
                task_id: context.taskId
            }
        };

        const response = await this.makeAPIRequest('/api/cod/shadow', requestData);
        
        return {
            bias_score: response.bias_score,
            risk_factors: response.risk_factors,
            alternative_perspectives: response.alternative_perspectives,
            criticism: response.criticism,
            confidence_assessment: response.confidence_assessment
        };
    }

    /**
     * Perform counterfactual audit
     */
    async performCounterfactualAudit(input, context) {
        if (!this.config.enableCounterfactual) {
            throw this.createError('Counterfactual analysis is disabled', 'FEATURE_DISABLED');
        }

        const requestData = {
            operation: 'counterfactual_audit',
            scenario: input.scenario,
            audit_type: input.auditType || 'comprehensive',
            context: {
                user_id: context.userId,
                session_id: context.sessionId,
                task_id: context.taskId
            }
        };

        const response = await this.makeAPIRequest('/api/cod/counterfactual', requestData);
        
        return {
            audit_results: response.audit_results,
            scenario_variations: response.scenario_variations,
            feasibility_score: response.feasibility_score,
            recommendations: response.recommendations
        };
    }

    /**
     * Perform risk assessment
     */
    async performRiskAssessment(input, context) {
        const requestData = {
            operation: 'risk_assessment',
            content: input.content,
            risk_categories: input.riskCategories || ['bias', 'misinformation', 'ethical'],
            context: {
                user_id: context.userId,
                session_id: context.sessionId,
                task_id: context.taskId
            }
        };

        const response = await this.makeAPIRequest('/api/cod/risk', requestData);
        
        return {
            overall_risk_score: response.overall_risk_score,
            risk_breakdown: response.risk_breakdown,
            mitigation_strategies: response.mitigation_strategies,
            confidence_level: response.confidence_level
        };
    }

    /**
     * Health check for the service
     */
    async healthCheck() {
        try {
            const startTime = Date.now();
            
            const response = await axios.get(`${this.config.apiEndpoint}/health`, {
                timeout: 5000
            });
            
            const duration = Date.now() - startTime;
            this.lastHealthCheck = new Date().toISOString();
            
            if (response.status === 200 && response.data.status === 'healthy') {
                return {
                    status: 'healthy',
                    responseTime: duration,
                    lastCheck: this.lastHealthCheck,
                    details: response.data
                };
            } else {
                throw new Error('Service reported unhealthy status');
            }
            
        } catch (error) {
            this.log('warn', 'Health check failed', { error: error.message });
            return {
                status: 'unhealthy',
                error: error.message,
                lastCheck: new Date().toISOString()
            };
        }
    }

    /**
     * Start Python service process
     */
    async startPythonService() {
        if (this.isServiceRunning) {
            this.log('debug', 'Python service already running');
            return;
        }

        this.log('info', 'Starting CoD Protocol Python service...');
        
        const { spawn } = require('child_process');
        const servicePath = path.join(this.config.servicePath, 'integration_example.py');
        
        this.pythonProcess = spawn(this.config.pythonExecutable, [servicePath], {
            cwd: this.config.servicePath,
            stdio: ['pipe', 'pipe', 'pipe']
        });

        this.pythonProcess.stdout.on('data', (data) => {
            this.log('debug', 'Python service output', { output: data.toString().trim() });
        });

        this.pythonProcess.stderr.on('data', (data) => {
            this.log('warn', 'Python service error output', { error: data.toString().trim() });
        });

        this.pythonProcess.on('exit', (code) => {
            this.isServiceRunning = false;
            this.log('warn', 'Python service exited', { code });
        });

        this.pythonProcess.on('error', (error) => {
            this.isServiceRunning = false;
            this.log('error', 'Python service process error', { error: error.message });
        });

        this.isServiceRunning = true;
        this.log('info', 'Python service started successfully');
    }

    /**
     * Wait for service to be ready
     */
    async waitForServiceReady(maxAttempts = 30, interval = 1000) {
        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                const health = await this.healthCheck();
                if (health.status === 'healthy') {
                    this.log('info', 'CoD Protocol service is ready');
                    return;
                }
            } catch (error) {
                // Continue waiting
            }
            
            this.log('debug', `Waiting for service to be ready (attempt ${attempt}/${maxAttempts})`);
            await new Promise(resolve => setTimeout(resolve, interval));
        }
        
        throw new Error('Service failed to become ready within timeout period');
    }

    /**
     * Make API request to Python service
     */
    async makeAPIRequest(endpoint, data) {
        try {
            const response = await axios.post(`${this.config.apiEndpoint}${endpoint}`, data, {
                timeout: 30000,
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            return response.data;
            
        } catch (error) {
            if (error.response) {
                throw this.createError(
                    `API request failed: ${error.response.data?.error || error.response.statusText}`,
                    'API_ERROR',
                    { statusCode: error.response.status, endpoint }
                );
            } else if (error.request) {
                throw this.createError(
                    'Service is not responding',
                    'SERVICE_UNAVAILABLE',
                    { endpoint }
                );
            } else {
                throw this.createError(
                    `Request setup failed: ${error.message}`,
                    'REQUEST_ERROR',
                    { endpoint }
                );
            }
        }
    }

    /**
     * Handle execution errors and circuit breaker logic
     */
    handleExecutionError(error) {
        this.failureCount++;
        this.lastFailureTime = Date.now();
        
        this.log('error', 'CoD Protocol execution failed', {
            error: error.message,
            failureCount: this.failureCount
        });

        // Circuit breaker logic
        if (this.config.enableCircuitBreaker) {
            const failureThreshold = 5;
            const timeoutDuration = 60000; // 1 minute

            if (this.failureCount >= failureThreshold) {
                this.circuitBreakerState = 'open';
                this.log('warn', 'Circuit breaker opened due to failures');
                
                // Set timer to transition to half-open
                setTimeout(() => {
                    if (this.circuitBreakerState === 'open') {
                        this.circuitBreakerState = 'half-open';
                        this.log('info', 'Circuit breaker transitioned to half-open');
                    }
                }, timeoutDuration);
            }
        }
    }

    /**
     * Get required configuration fields
     */
    getRequiredConfig() {
        return ['servicePath'];
    }

    /**
     * Shutdown the adapter
     */
    async shutdown() {
        this.log('info', 'Shutting down CoD Protocol adapter...');
        
        if (this.pythonProcess && this.isServiceRunning) {
            this.pythonProcess.kill('SIGTERM');
            
            // Wait for graceful shutdown
            await new Promise((resolve) => {
                const timeout = setTimeout(() => {
                    this.pythonProcess.kill('SIGKILL');
                    resolve();
                }, 5000);
                
                this.pythonProcess.on('exit', () => {
                    clearTimeout(timeout);
                    resolve();
                });
            });
        }
        
        this.isServiceRunning = false;
        await super.shutdown();
    }

    /**
     * Get service-specific status
     */
    getStatus() {
        const baseStatus = super.getStatus();
        
        return {
            ...baseStatus,
            serviceRunning: this.isServiceRunning,
            circuitBreakerState: this.circuitBreakerState,
            failureCount: this.failureCount,
            lastHealthCheck: this.lastHealthCheck,
            apiEndpoint: this.config.apiEndpoint,
            features: {
                shadowLLM: this.config.enableShadowLLM,
                counterfactual: this.config.enableCounterfactual,
                circuitBreaker: this.config.enableCircuitBreaker,
                telegramBot: this.config.enableTelegramBot
            }
        };
    }
}

module.exports = CoDProtocolAdapter;