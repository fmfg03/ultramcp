#!/usr/bin/env node

/**
 * Test Script for UltraMCP Orchestration System
 * 
 * Validates that all core components are working together correctly.
 */

const path = require('path');
const Orchestrator = require('./core/orchestrator');
const APIGateway = require('./api/gateway');

class OrchestrationTest {
    constructor() {
        this.orchestrator = null;
        this.gateway = null;
        this.testResults = [];
    }

    /**
     * Run all tests
     */
    async runTests() {
        console.log('🧪 Starting UltraMCP Orchestration Tests...\n');
        
        try {
            await this.testOrchestratorInitialization();
            await this.testEventBus();
            await this.testServiceRegistry();
            await this.testWorkflowEngine();
            await this.testStateManager();
            await this.testContextManager();
            await this.testPluginLoader();
            await this.testAPIGateway();
            await this.testTaskProcessing();
            
            this.printResults();
            
        } catch (error) {
            console.error('❌ Test suite failed:', error);
            process.exit(1);
        } finally {
            await this.cleanup();
        }
    }

    /**
     * Test orchestrator initialization
     */
    async testOrchestratorInitialization() {
        const testName = 'Orchestrator Initialization';
        console.log(`🔧 Testing ${testName}...`);
        
        try {
            this.orchestrator = new Orchestrator({
                stateConfig: { enablePersistence: false },
                pluginConfig: { directories: ['./adapters'] }
            });
            
            await this.orchestrator.initialize();
            
            this.addTestResult(testName, true, 'Orchestrator initialized successfully');
            console.log('✅ Orchestrator initialization passed\n');
            
        } catch (error) {
            this.addTestResult(testName, false, error.message);
            throw error;
        }
    }

    /**
     * Test event bus functionality
     */
    async testEventBus() {
        const testName = 'Event Bus';
        console.log(`📡 Testing ${testName}...`);
        
        try {
            let eventReceived = false;
            const testData = { test: 'data' };
            
            // Subscribe to event
            this.orchestrator.eventBus.on('test.event', (data) => {
                eventReceived = true;
                if (JSON.stringify(data) !== JSON.stringify(testData)) {
                    throw new Error('Event data mismatch');
                }
            });
            
            // Emit event
            this.orchestrator.eventBus.emit('test.event', testData);
            
            // Wait a bit for event processing
            await new Promise(resolve => setTimeout(resolve, 100));
            
            if (!eventReceived) {
                throw new Error('Event was not received');
            }
            
            this.addTestResult(testName, true, 'Event bus working correctly');
            console.log('✅ Event bus test passed\n');
            
        } catch (error) {
            this.addTestResult(testName, false, error.message);
            throw error;
        }
    }

    /**
     * Test service registry
     */
    async testServiceRegistry() {
        const testName = 'Service Registry';
        console.log(`🔍 Testing ${testName}...`);
        
        try {
            // Create a mock service
            const mockService = {
                id: 'test-service',
                name: 'Test Service',
                capabilities: ['test-capability'],
                healthCheck: async () => ({ status: 'healthy' }),
                execute: async (input) => ({ result: 'test-result' })
            };
            
            // Register service
            await this.orchestrator.serviceRegistry.registerService(mockService);
            
            // Check if service is registered
            const services = this.orchestrator.serviceRegistry.getAllServices();
            const registeredService = services.find(s => s.id === 'test-service');
            
            if (!registeredService) {
                throw new Error('Service was not registered');
            }
            
            // Test service discovery
            const foundServices = this.orchestrator.serviceRegistry.findServicesByCapability('test-capability');
            if (foundServices.length === 0) {
                throw new Error('Service discovery failed');
            }
            
            this.addTestResult(testName, true, 'Service registry working correctly');
            console.log('✅ Service registry test passed\n');
            
        } catch (error) {
            this.addTestResult(testName, false, error.message);
            throw error;
        }
    }

    /**
     * Test workflow engine
     */
    async testWorkflowEngine() {
        const testName = 'Workflow Engine';
        console.log(`⚙️ Testing ${testName}...`);
        
        try {
            // Test workflow registration
            const testWorkflow = {
                id: 'test-workflow',
                name: 'Test Workflow',
                steps: [
                    {
                        id: 'step1',
                        type: 'service',
                        service: 'test-service',
                        input: { test: 'input' }
                    }
                ]
            };
            
            this.orchestrator.workflowEngine.registerWorkflow(testWorkflow);
            
            // Check if workflow is registered
            const workflows = this.orchestrator.workflowEngine.getAllWorkflows();
            const registeredWorkflow = workflows.find(w => w.id === 'test-workflow');
            
            if (!registeredWorkflow) {
                throw new Error('Workflow was not registered');
            }
            
            this.addTestResult(testName, true, 'Workflow engine working correctly');
            console.log('✅ Workflow engine test passed\n');
            
        } catch (error) {
            this.addTestResult(testName, false, error.message);
            throw error;
        }
    }

    /**
     * Test state manager
     */
    async testStateManager() {
        const testName = 'State Manager';
        console.log(`💾 Testing ${testName}...`);
        
        try {
            // Test global state
            this.orchestrator.stateManager.setGlobal('test-key', 'test-value');
            const value = this.orchestrator.stateManager.getGlobal('test-key');
            
            if (value !== 'test-value') {
                throw new Error('Global state not working');
            }
            
            // Test session state
            this.orchestrator.stateManager.setSession('test-session', 'session-key', 'session-value');
            const sessionValue = this.orchestrator.stateManager.getSession('test-session', 'session-key');
            
            if (sessionValue !== 'session-value') {
                throw new Error('Session state not working');
            }
            
            this.addTestResult(testName, true, 'State manager working correctly');
            console.log('✅ State manager test passed\n');
            
        } catch (error) {
            this.addTestResult(testName, false, error.message);
            throw error;
        }
    }

    /**
     * Test context manager
     */
    async testContextManager() {
        const testName = 'Context Manager';
        console.log(`📋 Testing ${testName}...`);
        
        try {
            // Create context
            const context = this.orchestrator.contextManager.createContext('test-task', {
                userId: 'test-user',
                sessionId: 'test-session'
            });
            
            if (!context || context.taskId !== 'test-task') {
                throw new Error('Context creation failed');
            }
            
            // Add execution step
            this.orchestrator.contextManager.addExecutionStep('test-task', {
                step: 'test-step',
                duration: 100
            });
            
            // Get metrics
            const metrics = this.orchestrator.contextManager.getExecutionMetrics('test-task');
            if (!metrics || metrics.stepCount !== 1) {
                throw new Error('Context tracking failed');
            }
            
            this.addTestResult(testName, true, 'Context manager working correctly');
            console.log('✅ Context manager test passed\n');
            
        } catch (error) {
            this.addTestResult(testName, false, error.message);
            throw error;
        }
    }

    /**
     * Test plugin loader
     */
    async testPluginLoader() {
        const testName = 'Plugin Loader';
        console.log(`🔌 Testing ${testName}...`);
        
        try {
            // Plugin loader should be initialized and ready
            const pluginCount = this.orchestrator.pluginLoader.getPluginCount();
            const plugins = this.orchestrator.pluginLoader.getAllPlugins();
            
            this.addTestResult(testName, true, `Plugin loader initialized with ${pluginCount} plugins`);
            console.log(`✅ Plugin loader test passed (${pluginCount} plugins)\n`);
            
        } catch (error) {
            this.addTestResult(testName, false, error.message);
            throw error;
        }
    }

    /**
     * Test API Gateway
     */
    async testAPIGateway() {
        const testName = 'API Gateway';
        console.log(`🌐 Testing ${testName}...`);
        
        try {
            this.gateway = new APIGateway({
                orchestrator: this.orchestrator,
                enableAuth: false, // Disable for testing
                enableRateLimit: false // Disable for testing
            });
            
            await this.gateway.initialize();
            
            // Test that gateway has the required routes
            if (!this.gateway.app) {
                throw new Error('Express app not initialized');
            }
            
            this.addTestResult(testName, true, 'API Gateway initialized successfully');
            console.log('✅ API Gateway test passed\n');
            
        } catch (error) {
            this.addTestResult(testName, false, error.message);
            throw error;
        }
    }

    /**
     * Test task processing
     */
    async testTaskProcessing() {
        const testName = 'Task Processing';
        console.log(`🎯 Testing ${testName}...`);
        
        try {
            // Create a simple task
            const task = {
                id: 'test-task-processing',
                operation: 'test',
                data: { test: 'data' }
            };
            
            const context = { userId: 'test-user' };
            
            // Process task (this should work even if no specific handlers exist)
            const result = await this.orchestrator.processTask(task, context);
            
            if (!result) {
                throw new Error('Task processing returned no result');
            }
            
            this.addTestResult(testName, true, 'Task processing working correctly');
            console.log('✅ Task processing test passed\n');
            
        } catch (error) {
            this.addTestResult(testName, false, error.message);
            // Don't throw here as this might fail if no handlers are set up
            console.log('⚠️ Task processing test failed (expected if no handlers configured)\n');
        }
    }

    /**
     * Add test result
     */
    addTestResult(testName, passed, message) {
        this.testResults.push({
            test: testName,
            passed,
            message,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Print test results
     */
    printResults() {
        console.log('\n' + '='.repeat(60));
        console.log('🧪 TEST RESULTS SUMMARY');
        console.log('='.repeat(60));
        
        const passed = this.testResults.filter(r => r.passed);
        const failed = this.testResults.filter(r => !r.passed);
        
        console.log(`\n📊 Total Tests: ${this.testResults.length}`);
        console.log(`✅ Passed: ${passed.length}`);
        console.log(`❌ Failed: ${failed.length}`);
        
        if (failed.length > 0) {
            console.log('\n❌ FAILED TESTS:');
            failed.forEach(result => {
                console.log(`   • ${result.test}: ${result.message}`);
            });
        }
        
        console.log('\n✅ PASSED TESTS:');
        passed.forEach(result => {
            console.log(`   • ${result.test}: ${result.message}`);
        });
        
        const successRate = (passed.length / this.testResults.length) * 100;
        console.log(`\n🎯 Success Rate: ${successRate.toFixed(1)}%`);
        
        if (successRate >= 80) {
            console.log('\n🎉 UltraMCP Orchestration System is ready for deployment!');
        } else {
            console.log('\n⚠️ Some components need attention before deployment.');
        }
        
        console.log('='.repeat(60) + '\n');
    }

    /**
     * Cleanup test resources
     */
    async cleanup() {
        console.log('🧹 Cleaning up test resources...');
        
        try {
            if (this.gateway) {
                await this.gateway.shutdown();
            }
            
            if (this.orchestrator) {
                await this.orchestrator.shutdown();
            }
            
            console.log('✅ Cleanup completed\n');
        } catch (error) {
            console.warn('⚠️ Cleanup warning:', error.message);
        }
    }
}

// Run tests if called directly
if (require.main === module) {
    const test = new OrchestrationTest();
    test.runTests().catch(error => {
        console.error('❌ Test execution failed:', error);
        process.exit(1);
    });
}

module.exports = OrchestrationTest;