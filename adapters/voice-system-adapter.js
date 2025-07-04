/**
 * Voice System Adapter for UltraMCP
 * 
 * Integrates the Voice System service with the orchestration system,
 * providing speech-to-text, text-to-speech, and voice interaction capabilities.
 */

const { IService } = require('../core/interfaces/IService');
const axios = require('axios');
const path = require('path');
const fs = require('fs').promises;

class VoiceSystemAdapter extends IService {
    constructor(config = {}) {
        super({
            id: 'voice-system',
            name: 'Voice System',
            capabilities: [
                'speech-to-text',
                'text-to-speech',
                'voice-interaction',
                'audio-processing',
                'real-time-streaming',
                'voice-commands',
                'multi-language-support'
            ],
            version: '1.0.0',
            description: 'Comprehensive voice interaction system with STT, TTS, and real-time processing',
            ...config
        });

        this.config = {
            servicePath: config.servicePath || path.join(__dirname, '../services/voice-system'),
            apiEndpoint: config.apiEndpoint || 'http://sam.chat:8000',
            pythonExecutable: config.pythonExecutable || 'python',
            enableSTT: config.enableSTT !== false,
            enableTTS: config.enableTTS !== false,
            enableRealTime: config.enableRealTime !== false,
            supportedLanguages: config.supportedLanguages || ['en', 'es', 'fr', 'de'],
            maxAudioSize: config.maxAudioSize || 10 * 1024 * 1024, // 10MB
            audioFormats: config.audioFormats || ['wav', 'mp3', 'ogg', 'flac'],
            ...config
        };

        this.pythonProcess = null;
        this.isServiceRunning = false;
        this.lastHealthCheck = null;
        this.activeStreams = new Map();
        this.processingQueue = [];
    }

    /**
     * Initialize the Voice System service
     */
    async initialize() {
        this.log('info', 'Initializing Voice System adapter...');
        
        try {
            // Validate configuration
            this.validateConfig();
            
            // Start Python service if not already running
            await this.startPythonService();
            
            // Wait for service to be ready
            await this.waitForServiceReady();
            
            this.initialized = true;
            this.log('info', 'Voice System adapter initialized successfully');
            
        } catch (error) {
            this.log('error', 'Failed to initialize Voice System adapter', { error: error.message });
            throw this.createError(
                `Voice System initialization failed: ${error.message}`,
                'INIT_ERROR'
            );
        }
    }

    /**
     * Execute Voice System operation
     */
    async execute(input, context) {
        this.log('debug', 'Executing Voice System operation', { 
            operation: input.operation,
            language: input.language 
        });

        const startTime = Date.now();
        
        try {
            let result;
            
            switch (input.operation) {
                case 'speech_to_text':
                    result = await this.speechToText(input, context);
                    break;
                case 'text_to_speech':
                    result = await this.textToSpeech(input, context);
                    break;
                case 'voice_command':
                    result = await this.processVoiceCommand(input, context);
                    break;
                case 'start_stream':
                    result = await this.startAudioStream(input, context);
                    break;
                case 'stop_stream':
                    result = await this.stopAudioStream(input, context);
                    break;
                case 'process_audio':
                    result = await this.processAudioFile(input, context);
                    break;
                case 'get_languages':
                    result = await this.getSupportedLanguages();
                    break;
                default:
                    throw this.createError(
                        `Unknown Voice System operation: ${input.operation}`,
                        'INVALID_OPERATION'
                    );
            }

            const duration = Date.now() - startTime;
            this.log('debug', 'Voice System operation completed', { 
                operation: input.operation,
                duration: `${duration}ms`
            });

            return result;

        } catch (error) {
            this.log('error', 'Voice System execution failed', { 
                operation: input.operation,
                error: error.message 
            });
            throw error;
        }
    }

    /**
     * Convert speech to text
     */
    async speechToText(input, context) {
        if (!this.config.enableSTT) {
            throw this.createError('Speech-to-text is disabled', 'FEATURE_DISABLED');
        }

        // Validate audio input
        this.validateAudioInput(input);

        const requestData = {
            operation: 'stt',
            audio_data: input.audioData,
            language: input.language || 'en',
            model: input.model || 'default',
            options: {
                enable_punctuation: input.enablePunctuation !== false,
                enable_timestamps: input.enableTimestamps || false,
                confidence_threshold: input.confidenceThreshold || 0.5
            },
            context: {
                user_id: context.userId,
                session_id: context.sessionId,
                task_id: context.taskId
            }
        };

        const response = await this.makeAPIRequest('/api/voice/stt', requestData);
        
        return {
            text: response.text,
            confidence: response.confidence,
            language_detected: response.language_detected,
            timestamps: response.timestamps,
            alternatives: response.alternatives
        };
    }

    /**
     * Convert text to speech
     */
    async textToSpeech(input, context) {
        if (!this.config.enableTTS) {
            throw this.createError('Text-to-speech is disabled', 'FEATURE_DISABLED');
        }

        if (!input.text || typeof input.text !== 'string') {
            throw this.createError('Text input is required for TTS', 'INVALID_INPUT');
        }

        const requestData = {
            operation: 'tts',
            text: input.text,
            language: input.language || 'en',
            voice: input.voice || 'default',
            options: {
                speed: input.speed || 1.0,
                pitch: input.pitch || 1.0,
                volume: input.volume || 1.0,
                output_format: input.outputFormat || 'wav'
            },
            context: {
                user_id: context.userId,
                session_id: context.sessionId,
                task_id: context.taskId
            }
        };

        const response = await this.makeAPIRequest('/api/voice/tts', requestData);
        
        return {
            audio_data: response.audio_data,
            audio_url: response.audio_url,
            duration: response.duration,
            format: response.format,
            size: response.size
        };
    }

    /**
     * Process voice command
     */
    async processVoiceCommand(input, context) {
        // First convert speech to text
        const sttResult = await this.speechToText({
            audioData: input.audioData,
            language: input.language
        }, context);

        const requestData = {
            operation: 'voice_command',
            text: sttResult.text,
            confidence: sttResult.confidence,
            context: {
                user_id: context.userId,
                session_id: context.sessionId,
                task_id: context.taskId,
                voice_context: input.voiceContext || {}
            }
        };

        const response = await this.makeAPIRequest('/api/voice/command', requestData);
        
        return {
            command: response.command,
            intent: response.intent,
            entities: response.entities,
            confidence: response.confidence,
            response_text: response.response_text,
            original_text: sttResult.text,
            should_respond: response.should_respond
        };
    }

    /**
     * Start audio streaming session
     */
    async startAudioStream(input, context) {
        if (!this.config.enableRealTime) {
            throw this.createError('Real-time streaming is disabled', 'FEATURE_DISABLED');
        }

        const streamId = input.streamId || `stream_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        const requestData = {
            operation: 'start_stream',
            stream_id: streamId,
            options: {
                language: input.language || 'en',
                sample_rate: input.sampleRate || 16000,
                channels: input.channels || 1,
                format: input.format || 'wav'
            },
            context: {
                user_id: context.userId,
                session_id: context.sessionId,
                task_id: context.taskId
            }
        };

        const response = await this.makeAPIRequest('/api/voice/stream/start', requestData);
        
        // Track active stream
        this.activeStreams.set(streamId, {
            streamId,
            startTime: Date.now(),
            userId: context.userId,
            sessionId: context.sessionId,
            options: requestData.options
        });
        
        return {
            stream_id: streamId,
            websocket_url: response.websocket_url,
            status: 'started',
            options: requestData.options
        };
    }

    /**
     * Stop audio streaming session
     */
    async stopAudioStream(input, context) {
        const { streamId } = input;
        
        if (!streamId) {
            throw this.createError('Stream ID is required', 'INVALID_INPUT');
        }

        const requestData = {
            operation: 'stop_stream',
            stream_id: streamId,
            context: {
                user_id: context.userId,
                session_id: context.sessionId,
                task_id: context.taskId
            }
        };

        const response = await this.makeAPIRequest('/api/voice/stream/stop', requestData);
        
        // Remove from active streams
        const streamInfo = this.activeStreams.get(streamId);
        this.activeStreams.delete(streamId);
        
        return {
            stream_id: streamId,
            status: 'stopped',
            duration: streamInfo ? Date.now() - streamInfo.startTime : 0,
            final_transcript: response.final_transcript
        };
    }

    /**
     * Process audio file
     */
    async processAudioFile(input, context) {
        this.validateAudioInput(input);

        const requestData = {
            operation: 'process_audio',
            audio_data: input.audioData,
            processing_type: input.processingType || 'transcribe',
            options: {
                language: input.language || 'auto',
                enhance_audio: input.enhanceAudio || false,
                remove_noise: input.removeNoise || false,
                normalize_volume: input.normalizeVolume || false
            },
            context: {
                user_id: context.userId,
                session_id: context.sessionId,
                task_id: context.taskId
            }
        };

        const response = await this.makeAPIRequest('/api/voice/process', requestData);
        
        return {
            transcript: response.transcript,
            audio_info: response.audio_info,
            processing_results: response.processing_results,
            quality_score: response.quality_score
        };
    }

    /**
     * Get supported languages
     */
    async getSupportedLanguages() {
        const response = await this.makeAPIRequest('/api/voice/languages', {});
        
        return {
            supported_languages: response.supported_languages,
            default_language: response.default_language,
            voice_models: response.voice_models
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
                    features: {
                        stt: response.data.features?.stt || false,
                        tts: response.data.features?.tts || false,
                        streaming: response.data.features?.streaming || false
                    },
                    active_streams: this.activeStreams.size
                };
            } else {
                throw new Error('Service reported unhealthy status');
            }
            
        } catch (error) {
            this.log('warn', 'Health check failed', { error: error.message });
            return {
                status: 'unhealthy',
                error: error.message,
                lastCheck: new Date().toISOString(),
                active_streams: this.activeStreams.size
            };
        }
    }

    /**
     * Validate audio input
     */
    validateAudioInput(input) {
        if (!input.audioData) {
            throw this.createError('Audio data is required', 'INVALID_INPUT');
        }

        // Check audio size
        const audioSize = Buffer.isBuffer(input.audioData) 
            ? input.audioData.length 
            : input.audioData.length;
            
        if (audioSize > this.config.maxAudioSize) {
            throw this.createError(
                `Audio file too large. Maximum size: ${this.config.maxAudioSize} bytes`,
                'AUDIO_TOO_LARGE'
            );
        }

        // Validate language if provided
        if (input.language && !this.config.supportedLanguages.includes(input.language)) {
            throw this.createError(
                `Unsupported language: ${input.language}. Supported: ${this.config.supportedLanguages.join(', ')}`,
                'UNSUPPORTED_LANGUAGE'
            );
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

        this.log('info', 'Starting Voice System Python service...');
        
        const { spawn } = require('child_process');
        const servicePath = path.join(this.config.servicePath, 'main.py');
        
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
            
            // Clean up active streams
            this.activeStreams.clear();
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
                    this.log('info', 'Voice System service is ready');
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
     * Get required configuration fields
     */
    getRequiredConfig() {
        return ['servicePath'];
    }

    /**
     * Shutdown the adapter
     */
    async shutdown() {
        this.log('info', 'Shutting down Voice System adapter...');
        
        // Stop all active streams
        for (const [streamId] of this.activeStreams) {
            try {
                await this.stopAudioStream({ streamId }, { userId: 'system' });
            } catch (error) {
                this.log('warn', `Failed to stop stream ${streamId}`, { error: error.message });
            }
        }
        
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
        this.activeStreams.clear();
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
            activeStreams: this.activeStreams.size,
            lastHealthCheck: this.lastHealthCheck,
            apiEndpoint: this.config.apiEndpoint,
            features: {
                stt: this.config.enableSTT,
                tts: this.config.enableTTS,
                realTime: this.config.enableRealTime
            },
            supportedLanguages: this.config.supportedLanguages,
            streamInfo: Array.from(this.activeStreams.values()).map(stream => ({
                streamId: stream.streamId,
                duration: Date.now() - stream.startTime,
                userId: stream.userId
            }))
        };
    }
}

module.exports = VoiceSystemAdapter;