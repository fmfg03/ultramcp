#!/usr/bin/env node
/**
 * Control Tower Service
 * Central coordination and monitoring service for UltraMCP
 */

const express = require('express');
const WebSocket = require('ws');
const http = require('http');
const cors = require('cors');
const axios = require('axios');

// Initialize Express app
const app = express();
const port = process.env.CONTROL_TOWER_PORT || 8007;
const wsPort = process.env.CONTROL_TOWER_WS_PORT || 8008;

// Middleware
app.use(cors());
app.use(express.json());

// Service URLs from environment
const services = {
    cod: process.env.COD_SERVICE_URL || 'http://sam.chat:8001',
    asterisk: process.env.ASTERISK_SERVICE_URL || 'http://sam.chat:8002',
    blockoli: process.env.BLOCKOLI_SERVICE_URL || 'http://sam.chat:8003',
    voice: process.env.VOICE_SERVICE_URL || 'http://sam.chat:8004',
    deepclaude: process.env.DEEPCLAUDE_SERVICE_URL || 'http://sam.chat:8006'
};

// Global state
const systemStatus = {
    services: {},
    activeConnections: new Set(),
    lastHealthCheck: null,
    systemMetrics: {
        totalRequests: 0,
        activeDebates: 0,
        indexedProjects: 0,
        activeVoiceSessions: 0
    }
};

console.log('🎛️ Starting UltraMCP Control Tower...');

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'control-tower',
        timestamp: new Date().toISOString(),
        version: '1.0.0',
        active_connections: systemStatus.activeConnections.size
    });
});

// System status endpoint
app.get('/api/v1/status', async (req, res) => {
    try {
        // Get status from all services
        await updateSystemStatus();
        
        res.json({
            service: 'control-tower',
            status: 'running',
            services: systemStatus.services,
            metrics: systemStatus.systemMetrics,
            last_health_check: systemStatus.lastHealthCheck,
            active_connections: systemStatus.activeConnections.size,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error('Status check error:', error);
        res.status(500).json({ error: 'Status check failed' });
    }
});

// Service coordination endpoints
app.post('/api/v1/orchestrate/debate', async (req, res) => {
    try {
        const { topic, project, intelligence_mode = 'basic' } = req.body;
        
        // Coordinate multi-service debate
        const result = await orchestrateIntelligentDebate(topic, project, intelligence_mode);
        
        systemStatus.systemMetrics.activeDebates++;
        broadcastUpdate('debate_started', { topic, project, result });
        
        res.json({
            status: 'initiated',
            topic,
            project,
            intelligence_mode,
            result,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error('Debate orchestration error:', error);
        res.status(500).json({ error: error.message });
    }
});

app.post('/api/v1/orchestrate/security-analysis', async (req, res) => {
    try {
        const { target, analysis_type = 'comprehensive' } = req.body;
        
        // Coordinate security analysis across services
        const result = await orchestrateSecurityAnalysis(target, analysis_type);
        
        broadcastUpdate('security_analysis_started', { target, result });
        
        res.json({
            status: 'initiated',
            target,
            analysis_type,
            result,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error('Security analysis error:', error);
        res.status(500).json({ error: error.message });
    }
});

app.post('/api/v1/orchestrate/voice-debate', async (req, res) => {
    try {
        const { topic, session_type = 'debate' } = req.body;
        
        // Coordinate voice-enabled debate
        const result = await orchestrateVoiceDebate(topic, session_type);
        
        systemStatus.systemMetrics.activeVoiceSessions++;
        broadcastUpdate('voice_debate_started', { topic, result });
        
        res.json({
            status: 'initiated',
            topic,
            session_type,
            result,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error('Voice debate error:', error);
        res.status(500).json({ error: error.message });
    }
});

// Service health monitoring
app.get('/api/v1/services/health', async (req, res) => {
    try {
        await updateSystemStatus();
        
        res.json({
            services: systemStatus.services,
            overall_health: calculateOverallHealth(),
            last_check: systemStatus.lastHealthCheck,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error('Health monitoring error:', error);
        res.status(500).json({ error: 'Health monitoring failed' });
    }
});

// Metrics endpoint
app.get('/api/v1/metrics', async (req, res) => {
    try {
        // Aggregate metrics from all services
        const aggregatedMetrics = await aggregateSystemMetrics();
        
        res.json({
            system_metrics: systemStatus.systemMetrics,
            service_metrics: aggregatedMetrics,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error('Metrics error:', error);
        res.status(500).json({ error: 'Metrics collection failed' });
    }
});

// WebSocket server for real-time updates
const server = http.createServer(app);
const wss = new WebSocket.Server({ port: wsPort });

wss.on('connection', (ws) => {
    console.log('🔌 New WebSocket connection established');
    systemStatus.activeConnections.add(ws);
    
    // Send initial system status
    ws.send(JSON.stringify({
        type: 'system_status',
        data: systemStatus,
        timestamp: new Date().toISOString()
    }));
    
    ws.on('close', () => {
        console.log('🔌 WebSocket connection closed');
        systemStatus.activeConnections.delete(ws);
    });
    
    ws.on('message', async (message) => {
        try {
            const data = JSON.parse(message);
            await handleWebSocketMessage(ws, data);
        } catch (error) {
            console.error('WebSocket message error:', error);
            ws.send(JSON.stringify({
                type: 'error',
                error: error.message
            }));
        }
    });
});

// Core orchestration functions
async function orchestrateIntelligentDebate(topic, project, intelligenceMode) {
    console.log(`🎭 Orchestrating intelligent debate: ${topic}`);
    
    const results = {};
    
    try {
        // 1. Index project if needed (Blockoli)
        if (project) {
            console.log('📝 Ensuring project is indexed...');
            const indexResult = await makeServiceRequest(services.blockoli, '/api/v1/projects/list');
            
            const indexedProjects = indexResult.projects || {};
            if (!indexedProjects[project]) {
                console.log(`🔍 Indexing project: ${project}`);
                await makeServiceRequest(services.blockoli, '/api/v1/projects/index', 'POST', {
                    project_path: '/app/project_root',
                    project_name: project
                });
            }
        }
        
        // 2. Start code-intelligent debate (Blockoli + CoD)
        console.log('🧠 Starting code-intelligent debate...');
        const debateResult = await makeServiceRequest(services.blockoli, '/api/v1/debate/code', 'POST', {
            topic,
            project_name: project,
            intelligence_mode: intelligenceMode
        });
        results.debate = debateResult;
        
        // 3. Enhanced reasoning analysis (DeepClaude)
        console.log('🤔 Running metacognitive analysis...');
        const reasoningResult = await makeServiceRequest(services.deepclaude, '/api/v1/reasoning/analyze', 'POST', {
            topic: `Metacognitive analysis of: ${topic}`,
            context: { debate_topic: topic, project: project },
            reasoning_mode: 'metacognitive',
            depth: 'deep'
        });
        results.reasoning = reasoningResult;
        
        // 4. Security analysis if relevant
        if (topic.toLowerCase().includes('security') || intelligenceMode === 'security_focused') {
            console.log('🛡️ Running security analysis...');
            const securityResult = await makeServiceRequest(services.asterisk, '/api/v1/scan/codebase', 'POST', {
                scan_type: 'codebase',
                target: '/app/scan_target',
                options: { focus: topic }
            });
            results.security = securityResult;
        }
        
        return {
            orchestration_id: `debate_${Date.now()}`,
            status: 'coordinated',
            services_involved: Object.keys(results),
            results
        };
        
    } catch (error) {
        console.error('Debate orchestration error:', error);
        throw new Error(`Orchestration failed: ${error.message}`);
    }
}

async function orchestrateSecurityAnalysis(target, analysisType) {
    console.log(`🛡️ Orchestrating security analysis: ${target}`);
    
    const results = {};
    
    try {
        // 1. Run comprehensive security scan (Asterisk)
        console.log('🔍 Running security scan...');
        const scanResult = await makeServiceRequest(services.asterisk, '/api/v1/scan/codebase', 'POST', {
            scan_type: 'codebase',
            target: target,
            options: { analysis_type: analysisType }
        });
        results.scan = scanResult;
        
        // 2. Code intelligence security analysis (Blockoli)
        console.log('🧠 Running code intelligence security analysis...');
        const codeSecurityResult = await makeServiceRequest(services.blockoli, '/api/v1/debate/code', 'POST', {
            topic: `Security analysis of ${target}`,
            project_name: 'security_target',
            intelligence_mode: 'security_focused'
        });
        results.code_intelligence = codeSecurityResult;
        
        // 3. Metacognitive security reasoning (DeepClaude)
        console.log('🤔 Running security reasoning analysis...');
        const reasoningResult = await makeServiceRequest(services.deepclaude, '/api/v1/reasoning/analyze', 'POST', {
            topic: `Security threat modeling for ${target}`,
            context: { target, analysis_type: analysisType },
            reasoning_mode: 'critical',
            depth: 'deep'
        });
        results.reasoning = reasoningResult;
        
        return {
            orchestration_id: `security_${Date.now()}`,
            status: 'coordinated',
            target,
            analysis_type: analysisType,
            services_involved: Object.keys(results),
            results
        };
        
    } catch (error) {
        console.error('Security analysis orchestration error:', error);
        throw new Error(`Security orchestration failed: ${error.message}`);
    }
}

async function orchestrateVoiceDebate(topic, sessionType) {
    console.log(`🎙️ Orchestrating voice debate: ${topic}`);
    
    const results = {};
    
    try {
        // 1. Create voice session
        console.log('🎙️ Creating voice session...');
        const voiceSession = await makeServiceRequest(services.voice, '/api/v1/sessions/create', 'POST', {
            session_type: sessionType,
            ai_enabled: true,
            real_time: true
        });
        results.voice_session = voiceSession;
        
        // 2. Start debate with voice integration
        console.log('🎭 Starting voice-enabled debate...');
        const debateResult = await makeServiceRequest(services.blockoli, '/api/v1/debate/code', 'POST', {
            topic: `Voice debate: ${topic}`,
            project_name: 'voice_project',
            intelligence_mode: 'basic'
        });
        results.debate = debateResult;
        
        // 3. Voice analysis integration
        results.integration = {
            voice_session_id: voiceSession.session_id,
            debate_task_id: debateResult.task_id,
            websocket_url: voiceSession.websocket_url
        };
        
        return {
            orchestration_id: `voice_debate_${Date.now()}`,
            status: 'coordinated',
            topic,
            session_type: sessionType,
            services_involved: Object.keys(results),
            results
        };
        
    } catch (error) {
        console.error('Voice debate orchestration error:', error);
        throw new Error(`Voice orchestration failed: ${error.message}`);
    }
}

// Utility functions
async function makeServiceRequest(baseUrl, endpoint, method = 'GET', data = null) {
    const url = `${baseUrl}${endpoint}`;
    const config = {
        method,
        url,
        timeout: 30000,
        headers: { 'Content-Type': 'application/json' }
    };
    
    if (data && method !== 'GET') {
        config.data = data;
    }
    
    try {
        const response = await axios(config);
        return response.data;
    } catch (error) {
        if (error.response) {
            throw new Error(`Service error: ${error.response.status} - ${error.response.data?.error || error.message}`);
        } else if (error.request) {
            throw new Error(`Service unavailable: ${baseUrl}`);
        } else {
            throw new Error(`Request error: ${error.message}`);
        }
    }
}

async function updateSystemStatus() {
    console.log('🔍 Updating system status...');
    
    const servicePromises = Object.entries(services).map(async ([name, url]) => {
        try {
            const response = await axios.get(`${url}/health`, { timeout: 5000 });
            return [name, {
                status: 'healthy',
                url,
                last_check: new Date().toISOString(),
                response_time: response.headers['x-response-time'] || 'unknown',
                data: response.data
            }];
        } catch (error) {
            return [name, {
                status: 'unhealthy',
                url,
                last_check: new Date().toISOString(),
                error: error.message
            }];
        }
    });
    
    const results = await Promise.all(servicePromises);
    systemStatus.services = Object.fromEntries(results);
    systemStatus.lastHealthCheck = new Date().toISOString();
    
    // Broadcast status update
    broadcastUpdate('system_status', systemStatus);
}

function calculateOverallHealth() {
    const serviceStatuses = Object.values(systemStatus.services);
    const healthyCount = serviceStatuses.filter(s => s.status === 'healthy').length;
    const totalCount = serviceStatuses.length;
    
    if (totalCount === 0) return 'unknown';
    if (healthyCount === totalCount) return 'healthy';
    if (healthyCount > totalCount / 2) return 'degraded';
    return 'unhealthy';
}

async function aggregateSystemMetrics() {
    const metrics = {};
    
    for (const [name, url] of Object.entries(services)) {
        try {
            const response = await axios.get(`${url}/api/v1/status`, { timeout: 5000 });
            metrics[name] = response.data;
        } catch (error) {
            metrics[name] = { error: error.message };
        }
    }
    
    return metrics;
}

function broadcastUpdate(type, data) {
    const message = JSON.stringify({
        type,
        data,
        timestamp: new Date().toISOString()
    });
    
    systemStatus.activeConnections.forEach(ws => {
        if (ws.readyState === WebSocket.OPEN) {
            try {
                ws.send(message);
            } catch (error) {
                console.error('WebSocket broadcast error:', error);
            }
        }
    });
}

async function handleWebSocketMessage(ws, data) {
    switch (data.type) {
        case 'get_status':
            await updateSystemStatus();
            ws.send(JSON.stringify({
                type: 'system_status',
                data: systemStatus,
                timestamp: new Date().toISOString()
            }));
            break;
            
        case 'orchestrate_debate':
            try {
                const result = await orchestrateIntelligentDebate(
                    data.topic,
                    data.project,
                    data.intelligence_mode || 'basic'
                );
                ws.send(JSON.stringify({
                    type: 'orchestration_result',
                    data: result,
                    timestamp: new Date().toISOString()
                }));
            } catch (error) {
                ws.send(JSON.stringify({
                    type: 'error',
                    error: error.message
                }));
            }
            break;
            
        default:
            ws.send(JSON.stringify({
                type: 'error',
                error: `Unknown message type: ${data.type}`
            }));
    }
}

// Start servers
server.listen(port, () => {
    console.log(`✅ Control Tower HTTP server running on port ${port}`);
});

console.log(`✅ Control Tower WebSocket server running on port ${wsPort}`);

// Periodic health checks
setInterval(updateSystemStatus, 30000); // Every 30 seconds

// Initial health check
setTimeout(updateSystemStatus, 5000); // After 5 seconds

console.log('🎛️ UltraMCP Control Tower fully operational!');