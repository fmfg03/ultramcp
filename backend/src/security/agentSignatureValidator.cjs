/**
 * Digital Signature Validation System for External Agents
 * Provides cryptographic verification for untrusted agent payloads
 */

const crypto = require('crypto');
const jwt = require('jsonwebtoken');
const fs = require('fs').promises;
const path = require('path');

class AgentSignatureValidator {
    constructor() {
        this.trustedAgents = new Map();
        this.publicKeys = new Map();
        this.signatureAlgorithm = 'RS256';
        this.keyDirectory = path.join(__dirname, '../../../keys');
        this.maxPayloadSize = 10 * 1024 * 1024; // 10MB max
        this.signatureExpiry = 300; // 5 minutes
        
        this.initializeValidator();
    }

    async initializeValidator() {
        try {
            // Ensure keys directory exists
            await fs.mkdir(this.keyDirectory, { recursive: true });
            
            // Load trusted agents configuration
            await this.loadTrustedAgents();
            
            // Load public keys
            await this.loadPublicKeys();
            
            console.log('🔐 Agent Signature Validator initialized');
        } catch (error) {
            console.error('Failed to initialize signature validator:', error);
        }
    }

    async loadTrustedAgents() {
        try {
            const configPath = path.join(this.keyDirectory, 'trusted_agents.json');
            
            // Create default config if it doesn't exist
            try {
                await fs.access(configPath);
            } catch {
                const defaultConfig = {
                    agents: {
                        "external_builder": {
                            "name": "External Builder Agent",
                            "public_key_file": "external_builder_public.pem",
                            "permissions": ["build", "deploy"],
                            "max_payload_size": 5242880,
                            "rate_limit": 100,
                            "enabled": true
                        },
                        "research_agent": {
                            "name": "External Research Agent", 
                            "public_key_file": "research_agent_public.pem",
                            "permissions": ["research", "analyze"],
                            "max_payload_size": 1048576,
                            "rate_limit": 50,
                            "enabled": true
                        },
                        "notification_agent": {
                            "name": "External Notification Agent",
                            "public_key_file": "notification_agent_public.pem", 
                            "permissions": ["notify", "alert"],
                            "max_payload_size": 102400,
                            "rate_limit": 200,
                            "enabled": true
                        }
                    }
                };
                
                await fs.writeFile(configPath, JSON.stringify(defaultConfig, null, 2));
            }
            
            const configData = await fs.readFile(configPath, 'utf8');
            const config = JSON.parse(configData);
            
            for (const [agentId, agentConfig] of Object.entries(config.agents)) {
                if (agentConfig.enabled) {
                    this.trustedAgents.set(agentId, agentConfig);
                }
            }
            
            console.log(`📋 Loaded ${this.trustedAgents.size} trusted agents`);
        } catch (error) {
            console.error('Failed to load trusted agents:', error);
        }
    }

    async loadPublicKeys() {
        try {
            for (const [agentId, agentConfig] of this.trustedAgents.entries()) {
                const keyPath = path.join(this.keyDirectory, agentConfig.public_key_file);
                
                try {
                    const publicKey = await fs.readFile(keyPath, 'utf8');
                    this.publicKeys.set(agentId, publicKey);
                    console.log(`🔑 Loaded public key for agent: ${agentId}`);
                } catch (error) {
                    console.warn(`⚠️ Could not load public key for ${agentId}: ${error.message}`);
                    
                    // Generate example key pair for development
                    if (process.env.NODE_ENV === 'development') {
                        await this.generateExampleKeyPair(agentId, agentConfig.public_key_file);
                    }
                }
            }
        } catch (error) {
            console.error('Failed to load public keys:', error);
        }
    }

    async generateExampleKeyPair(agentId, publicKeyFile) {
        try {
            const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', {
                modulusLength: 2048,
                publicKeyEncoding: {
                    type: 'spki',
                    format: 'pem'
                },
                privateKeyEncoding: {
                    type: 'pkcs8',
                    format: 'pem'
                }
            });

            // Save public key
            const publicKeyPath = path.join(this.keyDirectory, publicKeyFile);
            await fs.writeFile(publicKeyPath, publicKey);
            
            // Save private key for development
            const privateKeyFile = publicKeyFile.replace('_public.pem', '_private.pem');
            const privateKeyPath = path.join(this.keyDirectory, privateKeyFile);
            await fs.writeFile(privateKeyPath, privateKey);
            
            // Load the public key
            this.publicKeys.set(agentId, publicKey);
            
            console.log(`🔧 Generated example key pair for ${agentId} (development only)`);
        } catch (error) {
            console.error(`Failed to generate key pair for ${agentId}:`, error);
        }
    }

    /**
     * Validate a signed payload from an external agent
     */
    async validateSignedPayload(signedPayload) {
        try {
            // Parse the signed payload
            const { signature, payload, metadata } = this.parseSignedPayload(signedPayload);
            
            // Basic validation
            this.validateBasicStructure(payload, metadata);
            
            // Agent validation
            const agentConfig = this.validateAgent(metadata.agent_id);
            
            // Signature validation
            await this.validateSignature(signature, payload, metadata);
            
            // Permission validation
            this.validatePermissions(agentConfig, payload);
            
            // Rate limiting
            await this.checkRateLimit(metadata.agent_id);
            
            // Payload size validation
            this.validatePayloadSize(payload, agentConfig);
            
            // Timestamp validation
            this.validateTimestamp(metadata);
            
            return {
                valid: true,
                agent_id: metadata.agent_id,
                payload: payload,
                metadata: metadata,
                validation_time: new Date().toISOString()
            };
            
        } catch (error) {
            console.error('Signature validation failed:', error);
            
            return {
                valid: false,
                error: error.message,
                validation_time: new Date().toISOString()
            };
        }
    }

    parseSignedPayload(signedPayload) {
        if (typeof signedPayload === 'string') {
            try {
                signedPayload = JSON.parse(signedPayload);
            } catch (error) {
                throw new Error('Invalid JSON in signed payload');
            }
        }

        const { signature, payload, metadata } = signedPayload;
        
        if (!signature || !payload || !metadata) {
            throw new Error('Missing required fields: signature, payload, or metadata');
        }

        return { signature, payload, metadata };
    }

    validateBasicStructure(payload, metadata) {
        // Validate metadata structure
        const requiredMetadata = ['agent_id', 'timestamp', 'nonce', 'version'];
        for (const field of requiredMetadata) {
            if (!metadata[field]) {
                throw new Error(`Missing required metadata field: ${field}`);
            }
        }

        // Validate payload structure
        if (!payload.action) {
            throw new Error('Payload must contain an action field');
        }

        // Validate version compatibility
        if (metadata.version !== '1.0') {
            throw new Error(`Unsupported payload version: ${metadata.version}`);
        }
    }

    validateAgent(agentId) {
        const agentConfig = this.trustedAgents.get(agentId);
        
        if (!agentConfig) {
            throw new Error(`Unknown or untrusted agent: ${agentId}`);
        }

        if (!agentConfig.enabled) {
            throw new Error(`Agent is disabled: ${agentId}`);
        }

        return agentConfig;
    }

    async validateSignature(signature, payload, metadata) {
        const agentId = metadata.agent_id;
        const publicKey = this.publicKeys.get(agentId);
        
        if (!publicKey) {
            throw new Error(`No public key available for agent: ${agentId}`);
        }

        // Create the data to verify (payload + metadata without signature)
        const dataToVerify = JSON.stringify({
            payload: payload,
            metadata: metadata
        });

        try {
            // Verify the signature
            const isValid = crypto.verify(
                'sha256',
                Buffer.from(dataToVerify),
                {
                    key: publicKey,
                    padding: crypto.constants.RSA_PKCS1_PSS_PADDING,
                },
                Buffer.from(signature, 'base64')
            );

            if (!isValid) {
                throw new Error('Invalid signature');
            }
        } catch (error) {
            throw new Error(`Signature verification failed: ${error.message}`);
        }
    }

    validatePermissions(agentConfig, payload) {
        const requiredPermission = this.getRequiredPermission(payload.action);
        
        if (requiredPermission && !agentConfig.permissions.includes(requiredPermission)) {
            throw new Error(`Agent lacks permission for action: ${payload.action}`);
        }
    }

    getRequiredPermission(action) {
        const actionPermissions = {
            'build': 'build',
            'deploy': 'deploy', 
            'research': 'research',
            'analyze': 'analyze',
            'notify': 'notify',
            'alert': 'alert'
        };

        return actionPermissions[action];
    }

    async checkRateLimit(agentId) {
        // Simple in-memory rate limiting
        // In production, use Redis or similar
        const now = Date.now();
        const windowMs = 60 * 1000; // 1 minute window
        
        if (!this.rateLimitData) {
            this.rateLimitData = new Map();
        }

        const agentData = this.rateLimitData.get(agentId) || { requests: [], limit: 100 };
        const agentConfig = this.trustedAgents.get(agentId);
        
        // Remove old requests outside the window
        agentData.requests = agentData.requests.filter(time => now - time < windowMs);
        
        // Check if limit exceeded
        if (agentData.requests.length >= agentConfig.rate_limit) {
            throw new Error(`Rate limit exceeded for agent: ${agentId}`);
        }

        // Add current request
        agentData.requests.push(now);
        this.rateLimitData.set(agentId, agentData);
    }

    validatePayloadSize(payload, agentConfig) {
        const payloadSize = JSON.stringify(payload).length;
        
        if (payloadSize > agentConfig.max_payload_size) {
            throw new Error(`Payload size (${payloadSize}) exceeds limit (${agentConfig.max_payload_size})`);
        }

        if (payloadSize > this.maxPayloadSize) {
            throw new Error(`Payload size (${payloadSize}) exceeds global limit (${this.maxPayloadSize})`);
        }
    }

    validateTimestamp(metadata) {
        const now = Date.now();
        const timestamp = new Date(metadata.timestamp).getTime();
        const age = Math.abs(now - timestamp) / 1000; // age in seconds

        if (age > this.signatureExpiry) {
            throw new Error(`Signature expired (age: ${age}s, max: ${this.signatureExpiry}s)`);
        }
    }

    /**
     * Create a signed payload (for testing or internal agents)
     */
    async createSignedPayload(agentId, payload, privateKeyPath = null) {
        try {
            const agentConfig = this.trustedAgents.get(agentId);
            if (!agentConfig) {
                throw new Error(`Unknown agent: ${agentId}`);
            }

            // Load private key
            let privateKey;
            if (privateKeyPath) {
                privateKey = await fs.readFile(privateKeyPath, 'utf8');
            } else {
                // Try to load development private key
                const devKeyPath = path.join(
                    this.keyDirectory, 
                    agentConfig.public_key_file.replace('_public.pem', '_private.pem')
                );
                privateKey = await fs.readFile(devKeyPath, 'utf8');
            }

            // Create metadata
            const metadata = {
                agent_id: agentId,
                timestamp: new Date().toISOString(),
                nonce: crypto.randomBytes(16).toString('hex'),
                version: '1.0'
            };

            // Create data to sign
            const dataToSign = JSON.stringify({
                payload: payload,
                metadata: metadata
            });

            // Create signature
            const signature = crypto.sign(
                'sha256',
                Buffer.from(dataToSign),
                {
                    key: privateKey,
                    padding: crypto.constants.RSA_PKCS1_PSS_PADDING,
                }
            ).toString('base64');

            return {
                signature: signature,
                payload: payload,
                metadata: metadata
            };

        } catch (error) {
            throw new Error(`Failed to create signed payload: ${error.message}`);
        }
    }

    /**
     * Get validation statistics
     */
    getValidationStats() {
        return {
            trusted_agents: this.trustedAgents.size,
            loaded_keys: this.publicKeys.size,
            rate_limit_data: this.rateLimitData ? this.rateLimitData.size : 0,
            signature_algorithm: this.signatureAlgorithm,
            max_payload_size: this.maxPayloadSize,
            signature_expiry: this.signatureExpiry
        };
    }

    /**
     * Refresh trusted agents and keys
     */
    async refresh() {
        this.trustedAgents.clear();
        this.publicKeys.clear();
        await this.loadTrustedAgents();
        await this.loadPublicKeys();
        console.log('🔄 Agent signature validator refreshed');
    }
}

// Middleware for Express.js
function createSignatureValidationMiddleware(validator) {
    return async (req, res, next) => {
        try {
            // Only validate external agent requests
            const isExternalAgent = req.headers['x-external-agent'] === 'true';
            
            if (!isExternalAgent) {
                return next();
            }

            // Validate the signed payload
            const result = await validator.validateSignedPayload(req.body);
            
            if (!result.valid) {
                return res.status(401).json({
                    error: 'Signature validation failed',
                    details: result.error
                });
            }

            // Add validated data to request
            req.validatedAgent = {
                agent_id: result.agent_id,
                payload: result.payload,
                metadata: result.metadata
            };

            next();
        } catch (error) {
            console.error('Signature validation middleware error:', error);
            res.status(500).json({
                error: 'Internal signature validation error'
            });
        }
    };
}

// Global validator instance
const agentSignatureValidator = new AgentSignatureValidator();

module.exports = {
    AgentSignatureValidator,
    agentSignatureValidator,
    createSignatureValidationMiddleware
};

// Example usage and testing
if (require.main === module) {
    async function testSignatureValidation() {
        console.log('🔄 Testing Agent Signature Validation...');
        
        const validator = new AgentSignatureValidator();
        
        // Wait for initialization
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        try {
            // Create a test payload
            const testPayload = {
                action: 'build',
                parameters: {
                    project: 'test-project',
                    environment: 'development'
                }
            };
            
            // Create signed payload
            const signedPayload = await validator.createSignedPayload('external_builder', testPayload);
            console.log('✅ Created signed payload');
            
            // Validate the signed payload
            const result = await validator.validateSignedPayload(signedPayload);
            
            if (result.valid) {
                console.log('✅ Signature validation successful');
                console.log('Agent ID:', result.agent_id);
                console.log('Action:', result.payload.action);
            } else {
                console.log('❌ Signature validation failed:', result.error);
            }
            
            // Test invalid signature
            const invalidPayload = { ...signedPayload };
            invalidPayload.signature = 'invalid-signature';
            
            const invalidResult = await validator.validateSignedPayload(invalidPayload);
            console.log('❌ Invalid signature correctly rejected:', !invalidResult.valid);
            
            // Show stats
            const stats = validator.getValidationStats();
            console.log('📊 Validation stats:', stats);
            
        } catch (error) {
            console.error('❌ Test failed:', error);
        }
    }
    
    testSignatureValidation();
}

