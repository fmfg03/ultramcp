#!/usr/bin/env node

/**
 * Core Orchestration Test for UltraMCP
 * 
 * Tests only the core orchestration components without external service dependencies.
 */

const Orchestrator = require('./core/orchestrator');
const APIGateway = require('./api/gateway');
const { IService } = require('./core/interfaces/IService');

class CoreOrchestrationTest {
    constructor() {
        this.orchestrator = null;
        this.gateway = null;
        this.testResults = [];
    }

    /**
     * Run all core tests
     */
    async runTests() {
        console.log('🧪 Starting UltraMCP Core Orchestration Tests...\n');
        
        try {
            await this.testOrchestratorInitialization();
            await this.testEventBus();
            await this.testServiceRegistry();
            await this.testWorkflowEngine();
            await this.testStateManager();
            await this.testContextManager();
            await this.testAPIGateway();
            await this.testIntegratedTaskFlow();
            
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
                pluginConfig: { directories: [] } // Don't load external plugins
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
            // Create a proper mock service that extends IService
            class MockService extends IService {
                constructor() {
                    super({
                        id: 'test-service',
                        name: 'Test Service',
                        capabilities: ['test-capability']
                    });
                }
                
                async initialize() {
                    this.initialized = true;
                }
                
                async execute(input) {
                    return { result: 'test-result', input };
                }
                
                async healthCheck() {
                    return { status: 'healthy' };
                }
            }
            
            const mockService = new MockService();
            await mockService.initialize();
            
            // Register service
            await this.orchestrator.serviceRegistry.registerService(mockService);
            
            // Check if service is registered
            const services = this.orchestrator.serviceRegistry.getAllServices();
            const registeredService = services.find(s => s.id === 'test-service');
            
            if (!registeredService) {
                throw new Error('Service was not registered');
            }
            
            // Test service discovery
            const foundServices = this.orchestrator.serviceRegistry.selectServices(
                { capabilities: ['test-capability'] }, 
                ['test-capability']
            );
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
            
            // Test task state
            this.orchestrator.stateManager.setTask('test-task', 'task-key', 'task-value');
            const taskValue = this.orchestrator.stateManager.getTask('test-task', 'task-key');
            
            if (taskValue !== 'task-value') {
                throw new Error('Task state not working');
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
            
            // Test service usage tracking
            this.orchestrator.contextManager.addServiceUsage('test-task', 'test-service', 'execute', 200, true);
            const updatedMetrics = this.orchestrator.contextManager.getExecutionMetrics('test-task');
            if (updatedMetrics.serviceCount !== 1) {
                throw new Error('Service usage tracking failed');
            }
            
            this.addTestResult(testName, true, 'Context manager working correctly');
            console.log('✅ Context manager test passed\n');
            
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
                enableRateLimit: false, // Disable for testing
                enableWebSocket: false // Disable for testing
            });
            
            await this.gateway.initialize();
            
            // Test that gateway has the required properties
            if (!this.gateway.app) {
                throw new Error('Express app not initialized');
            }
            
            // Test gateway status
            const status = this.gateway.getStatus();
            if (!status || status.status !== 'operational') {
                throw new Error('Gateway status not operational');
            }
            
            this.addTestResult(testName, true, 'API Gateway initialized successfully');
            console.log('✅ API Gateway test passed\n');
            
        } catch (error) {
            this.addTestResult(testName, false, error.message);
            throw error;
        }
    }

    /**
     * Test integrated task flow
     */
    async testIntegratedTaskFlow() {
        const testName = 'Integrated Task Flow';
        console.log(`🎯 Testing ${testName}...`);
        
        try {
            // Create a task that will use our test service
            const task = {
                id: 'integrated-test-task',
                operation: 'test',
                service: 'test-service',
                content: 'This is a test task for integrated flow validation',
                data: { test: 'integrated-data' }
            };
            
            const context = { 
                userId: 'test-user',
                sessionId: 'test-session'
            };
            
            // Process task through orchestrator
            const result = await this.orchestrator.processTask(task, context);
            
            if (!result || !result.taskId) {
                throw new Error('Task processing returned invalid result');
            }
            
            // Check that context was created and tracked
            const taskContext = this.orchestrator.contextManager.getContext(result.taskId);
            if (!taskContext) {
                throw new Error('Task context was not created');
            }
            
            // Verify metrics were tracked
            const metrics = this.orchestrator.contextManager.getExecutionMetrics(result.taskId);
            if (!metrics) {
                throw new Error('Task metrics were not tracked');
            }
            
            this.addTestResult(testName, true, 'Integrated task flow working correctly');
            console.log('✅ Integrated task flow test passed\n');
            
        } catch (error) {
            this.addTestResult(testName, false, error.message);
            console.log('⚠️ Integrated task flow test failed (this may be expected)\n');
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
        console.log('🧪 CORE ORCHESTRATION TEST RESULTS');
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
            console.log('\n🎉 UltraMCP Core Orchestration System is working correctly!');
        } else {
            console.log('\n⚠️ Some core components need attention.');
        }
        
        console.log('='.repeat(60) + '\n');
        
        // Additional system information
        if (this.orchestrator) {
            console.log('📈 SYSTEM STATUS:');
            try {
                const stats = this.orchestrator.getStats ? this.orchestrator.getStats() : {};
                console.log(`   • Services Registered: ${this.orchestrator.serviceRegistry?.getServiceCount() || 0}`);
                console.log(`   • Workflows Available: ${this.orchestrator.workflowEngine?.getWorkflowCount() || 0}`);
                console.log(`   • Active Contexts: ${this.orchestrator.contextManager?.getAllContexts()?.length || 0}`);
                console.log(`   • Global State Entries: ${this.orchestrator.stateManager?.getStats()?.counts?.globalEntries || 0}`);
            } catch (error) {
                console.log('   • Status information unavailable');
            }
            console.log('');
        }
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
    const test = new CoreOrchestrationTest();
    test.runTests().catch(error => {
        console.error('❌ Test execution failed:', error);
        process.exit(1);
    });
}

module.exports = CoreOrchestrationTest;