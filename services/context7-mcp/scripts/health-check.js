#!/usr/bin/env node

/**
 * Context7 MCP Service Health Check
 * Used by Docker healthcheck and monitoring systems
 */

const http = require('http');

const config = {
    host: process.env.MCP_SERVER_HOST || 'localhost',
    port: process.env.MCP_SERVER_PORT || 8003,
    timeout: 5000
};

function checkHealth() {
    return new Promise((resolve, reject) => {
        const req = http.request({
            hostname: config.host,
            port: config.port,
            path: '/health',
            method: 'GET',
            timeout: config.timeout
        }, (res) => {
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                try {
                    const health = JSON.parse(data);
                    
                    if (res.statusCode === 200 && health.status === 'healthy') {
                        resolve(health);
                    } else {
                        reject(new Error(`Health check failed: ${health.status || 'unknown'}`));
                    }
                } catch (error) {
                    reject(new Error(`Invalid health response: ${error.message}`));
                }
            });
        });
        
        req.on('error', (error) => {
            reject(new Error(`Health check request failed: ${error.message}`));
        });
        
        req.on('timeout', () => {
            req.destroy();
            reject(new Error('Health check timeout'));
        });
        
        req.end();
    });
}

// Run health check
checkHealth()
    .then((health) => {
        console.log('✅ Context7 MCP service is healthy');
        console.log(`   Uptime: ${Math.round(health.uptime / 1000)}s`);
        console.log(`   Requests: ${health.stats.requests}`);
        console.log(`   Cache keys: ${health.stats.cache.keys}`);
        process.exit(0);
    })
    .catch((error) => {
        console.error('❌ Context7 MCP service health check failed:', error.message);
        process.exit(1);
    });