/**
 * A2A Integration Test Suite
 * Tests the integrated A2A service within SUPERmcp
 */

const axios = require('axios');
const { v4: uuidv4 } = require('uuid');

const BASE_URL = 'http://localhost:3000';
const A2A_BASE_URL = `${BASE_URL}/api/a2a`;

// Test configuration
const TEST_CONFIG = {
    timeout: 10000,
    retryCount: 3,
    testSession: uuidv4()
};

class A2AIntegrationTester {
    constructor() {
        this.results = {
            passed: 0,
            failed: 0,
            total: 0,
            details: []
        };
    }
    
    log(message, level = 'info') {
        const timestamp = new Date().toISOString();
        const prefix = level === 'error' ? '❌' : level === 'warning' ? '⚠️' : level === 'success' ? '✅' : 'ℹ️';
        console.log(`[${timestamp}] ${prefix} ${message}`);
    }
    
    async runTest(testName, testFunction) {
        this.results.total++;
        this.log(`Running test: ${testName}`);
        
        try {
            const startTime = Date.now();
            await testFunction();
            const duration = Date.now() - startTime;
            
            this.results.passed++;
            this.results.details.push({
                name: testName,
                status: 'passed',
                duration,
                error: null
            });
            
            this.log(`✅ ${testName} passed (${duration}ms)`, 'success');
        } catch (error) {
            this.results.failed++;
            this.results.details.push({
                name: testName,
                status: 'failed',
                duration: 0,
                error: error.message
            });
            
            this.log(`❌ ${testName} failed: ${error.message}`, 'error');
        }
    }
    
    async testServiceHealth() {
        const response = await axios.get(`${BASE_URL}/health`, { timeout: TEST_CONFIG.timeout });
        
        if (response.status !== 200) {
            throw new Error(`Health check failed with status: ${response.status}`);
        }
        
        if (response.data.status !== 'healthy') {
            throw new Error(`Service not healthy: ${response.data.status}`);
        }
    }
    
    async testA2AServiceStatus() {
        const response = await axios.get(`${A2A_BASE_URL}/status`, { timeout: TEST_CONFIG.timeout });
        
        if (response.status !== 200) {
            throw new Error(`A2A status check failed with status: ${response.status}`);
        }
        
        if (!response.data.success) {
            throw new Error(`A2A service not successful: ${JSON.stringify(response.data)}`);
        }
    }
    
    async testA2AInitialization() {
        const response = await axios.post(`${A2A_BASE_URL}/initialize`, {}, { 
            timeout: TEST_CONFIG.timeout,
            headers: { 'Authorization': 'Bearer dev-token' }
        });
        
        if (response.status !== 200) {
            throw new Error(`A2A initialization failed with status: ${response.status}`);
        }
        
        if (!response.data.success) {
            throw new Error(`A2A initialization not successful: ${response.data.message}`);
        }
    }
    
    async testAgentDiscovery() {
        const response = await axios.get(`${A2A_BASE_URL}/discover`, { 
            timeout: TEST_CONFIG.timeout,
            headers: { 'Authorization': 'Bearer dev-token' }
        });
        
        if (response.status !== 200) {
            throw new Error(`Agent discovery failed with status: ${response.status}`);
        }
        
        if (!response.data.success) {
            throw new Error(`Agent discovery not successful`);
        }
        
        // Discovery may return empty list if no agents are registered yet
        this.log(`Discovered ${response.data.agents.length} agents`);
    }
    
    async testHealthCheckTask() {
        const taskPayload = {
            task_type: 'health_check',
            payload: {
                include_agent_details: true,
                include_metrics: true
            },
            priority: 5,
            metadata: {
                session_id: TEST_CONFIG.testSession,
                source: 'integration_test'
            }
        };
        
        const response = await axios.post(`${A2A_BASE_URL}/task`, taskPayload, {
            timeout: TEST_CONFIG.timeout,
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': 'Bearer dev-token'
            }
        });
        
        if (response.status !== 200) {
            throw new Error(`Health check task failed with status: ${response.status}`);
        }
        
        if (!response.data.success) {
            throw new Error(`Health check task not successful: ${JSON.stringify(response.data)}`);
        }
        
        this.log(`Health check task completed in ${response.data.duration}ms`);
    }
    
    async testMCPOrchestrationTask() {
        const taskPayload = {
            task_type: 'mcp_orchestration',
            payload: {
                message: 'Test A2A integration with MCP orchestration system',
                session_id: TEST_CONFIG.testSession,
                context: {
                    test_mode: true,
                    a2a_integration: true
                }
            },
            priority: 3
        };
        
        const response = await axios.post(`${A2A_BASE_URL}/task`, taskPayload, {
            timeout: TEST_CONFIG.timeout * 2, // MCP tasks may take longer
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': 'Bearer dev-token'
            }
        });
        
        if (response.status !== 200) {
            throw new Error(`MCP orchestration task failed with status: ${response.status}`);
        }
        
        if (!response.data.success) {
            throw new Error(`MCP orchestration task not successful: ${JSON.stringify(response.data)}`);
        }
        
        this.log(`MCP orchestration task completed in ${response.data.duration}ms`);
    }
    
    async testMonitoringDashboard() {
        const response = await axios.get(`${A2A_BASE_URL}/monitoring/dashboard`, { 
            timeout: TEST_CONFIG.timeout 
        });
        
        if (response.status !== 200) {
            throw new Error(`Monitoring dashboard failed with status: ${response.status}`);
        }
        
        if (!response.data.success) {
            throw new Error(`Monitoring dashboard not successful`);
        }
        
        if (!response.data.dashboard) {
            throw new Error(`Dashboard data missing`);
        }
        
        this.log(`Dashboard status: ${response.data.dashboard.status?.overall || 'unknown'}`);
    }
    
    async testMetricsEndpoint() {
        const response = await axios.get(`${A2A_BASE_URL}/metrics`, { 
            timeout: TEST_CONFIG.timeout,
            headers: { 'Authorization': 'Bearer dev-token' }
        });
        
        if (response.status !== 200) {
            throw new Error(`Metrics endpoint failed with status: ${response.status}`);
        }
        
        if (!response.data.success) {
            throw new Error(`Metrics endpoint not successful`);
        }
        
        const overview = response.data.metrics?.overview;
        if (overview) {
            this.log(`Total requests: ${overview.total_requests}, Success rate: ${overview.success_rate?.toFixed(2)}%`);
        }
    }
    
    async testActiveTraces() {
        const response = await axios.get(`${A2A_BASE_URL}/monitoring/traces`, { 
            timeout: TEST_CONFIG.timeout 
        });
        
        if (response.status !== 200) {
            throw new Error(`Active traces endpoint failed with status: ${response.status}`);
        }
        
        if (!response.data.success) {
            throw new Error(`Active traces endpoint not successful`);
        }
        
        this.log(`Active traces: ${response.data.count}`);
    }
    
    async testMultiAgentWorkflow() {
        const workflowPayload = {
            workflow_steps: [
                {
                    id: 'step1',
                    task_data: {
                        task_type: 'health_check',
                        payload: { quick_check: true }
                    },
                    delegate_to_a2a: false
                },
                {
                    id: 'step2',
                    task_data: {
                        task_type: 'general',
                        payload: { message: 'Test workflow step 2' }
                    },
                    delegate_to_a2a: false
                }
            ],
            coordination_type: 'sequential',
            priority: 4
        };
        
        const response = await axios.post(`${A2A_BASE_URL}/workflow`, workflowPayload, {
            timeout: TEST_CONFIG.timeout * 3,
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': 'Bearer dev-token'
            }
        });
        
        if (response.status !== 200) {
            throw new Error(`Multi-agent workflow failed with status: ${response.status}`);
        }
        
        if (!response.data.success) {
            throw new Error(`Multi-agent workflow not successful`);
        }
        
        this.log(`Workflow completed with ${response.data.result?.results?.length || 0} steps`);
    }
    
    async runAllTests() {
        this.log('🚀 Starting A2A Integration Test Suite');
        this.log(`Test session: ${TEST_CONFIG.testSession}`);
        
        // Basic connectivity tests
        await this.runTest('Service Health Check', () => this.testServiceHealth());
        await this.runTest('A2A Service Status', () => this.testA2AServiceStatus());
        await this.runTest('A2A Service Initialization', () => this.testA2AInitialization());
        
        // Agent discovery and communication
        await this.runTest('Agent Discovery', () => this.testAgentDiscovery());
        
        // Task execution tests
        await this.runTest('Health Check Task', () => this.testHealthCheckTask());
        await this.runTest('MCP Orchestration Task', () => this.testMCPOrchestrationTask());
        await this.runTest('Multi-Agent Workflow', () => this.testMultiAgentWorkflow());
        
        // Monitoring and observability
        await this.runTest('Monitoring Dashboard', () => this.testMonitoringDashboard());
        await this.runTest('Metrics Endpoint', () => this.testMetricsEndpoint());
        await this.runTest('Active Traces', () => this.testActiveTraces());
        
        // Print results
        this.printResults();
    }
    
    printResults() {
        console.log('\n' + '='.repeat(60));
        this.log('🧪 A2A Integration Test Results');
        console.log('='.repeat(60));
        
        this.log(`Total Tests: ${this.results.total}`);
        this.log(`Passed: ${this.results.passed}`, 'success');
        this.log(`Failed: ${this.results.failed}`, this.results.failed > 0 ? 'error' : 'info');
        this.log(`Success Rate: ${((this.results.passed / this.results.total) * 100).toFixed(2)}%`);
        
        if (this.results.failed > 0) {
            console.log('\n❌ Failed Tests:');
            this.results.details
                .filter(test => test.status === 'failed')
                .forEach(test => {
                    console.log(`  • ${test.name}: ${test.error}`);
                });
        }
        
        console.log('\n📊 Test Details:');
        this.results.details.forEach(test => {
            const status = test.status === 'passed' ? '✅' : '❌';
            const duration = test.duration > 0 ? ` (${test.duration}ms)` : '';
            console.log(`  ${status} ${test.name}${duration}`);
        });
        
        const overallStatus = this.results.failed === 0 ? 'PASSED' : 'FAILED';
        const statusIcon = this.results.failed === 0 ? '🎉' : '💥';
        
        console.log('\n' + '='.repeat(60));
        this.log(`${statusIcon} Overall Result: ${overallStatus}`, this.results.failed === 0 ? 'success' : 'error');
        console.log('='.repeat(60));
        
        // Exit with appropriate code
        if (this.results.failed > 0) {
            process.exit(1);
        }
    }
}

// Run tests if script is executed directly
if (require.main === module) {
    const tester = new A2AIntegrationTester();
    
    // Handle graceful shutdown
    process.on('SIGINT', () => {
        console.log('\n⚠️ Test interrupted by user');
        tester.printResults();
        process.exit(1);
    });
    
    // Handle unhandled errors
    process.on('unhandledRejection', (error) => {
        console.error('❌ Unhandled error:', error.message);
        process.exit(1);
    });
    
    // Run the test suite
    tester.runAllTests().catch((error) => {
        console.error('💥 Test suite failed:', error.message);
        process.exit(1);
    });
}

module.exports = A2AIntegrationTester;