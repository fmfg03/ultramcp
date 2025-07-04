/**
 * Event Bus System for UltraMCP
 * 
 * Provides event-driven communication between all components
 * with middleware support, event history, and pattern matching.
 */

const { EventEmitter } = require('events');
const { generateEventId } = require('../utils');

class EventBus extends EventEmitter {
    constructor(config = {}) {
        super();
        
        this.config = {
            historyLimit: config.historyLimit || 10000,
            enablePersistence: config.enablePersistence || false,
            persistencePath: config.persistencePath || './data/events',
            maxListeners: config.maxListeners || 100,
            ...config
        };

        // Event storage and middleware
        this.eventHistory = [];
        this.middleware = [];
        this.eventPatterns = new Map();
        this.eventMetrics = {
            totalEvents: 0,
            eventsByType: new Map(),
            lastEventTime: null
        };
        
        // Wait-for-input functionality
        this.pendingInputRequests = new Map();
        this.inputTimeouts = new Map();

        // Set max listeners to prevent warnings
        this.setMaxListeners(this.config.maxListeners);

        // Setup internal event handling
        this.setupInternalEvents();
        
        // Initialize persistence if enabled
        if (this.config.enablePersistence) {
            this.initializePersistence();
        }
    }

    /**
     * Enhanced emit with middleware and history tracking
     */
    emit(event, data = {}) {
        const eventData = {
            event,
            data,
            timestamp: new Date().toISOString(),
            id: generateEventId(),
            source: 'orchestrator'
        };

        try {
            // Apply middleware chain
            for (const middleware of this.middleware) {
                const result = middleware(eventData);
                if (result === false) {
                    // Middleware can cancel event
                    return false;
                }
                if (result && typeof result === 'object') {
                    // Middleware can modify event data
                    Object.assign(eventData, result);
                }
            }

            // Store in history (with size limit)
            this.addToHistory(eventData);

            // Update metrics
            this.updateMetrics(event);

            // Emit to EventEmitter (standard listeners)
            super.emit(event, eventData);

            // Emit to pattern listeners
            this.emitToPatternListeners(event, eventData);

            // Emit wildcard events
            super.emit('*', eventData);
            super.emit('event.*', eventData);

            return true;

        } catch (error) {
            console.error('Error in EventBus.emit:', error);
            
            // Emit error event (avoid infinite loops)
            if (event !== 'eventbus.error') {
                super.emit('eventbus.error', {
                    originalEvent: event,
                    error: error.message,
                    timestamp: new Date().toISOString()
                });
            }
            
            return false;
        }
    }

    /**
     * Add event to history with size management
     */
    addToHistory(eventData) {
        this.eventHistory.push(eventData);
        
        // Trim history if it exceeds limit
        if (this.eventHistory.length > this.config.historyLimit) {
            this.eventHistory = this.eventHistory.slice(-this.config.historyLimit);
        }

        // Persist if enabled
        if (this.config.enablePersistence) {
            this.persistEvent(eventData);
        }
    }

    /**
     * Update event metrics
     */
    updateMetrics(eventType) {
        this.eventMetrics.totalEvents++;
        this.eventMetrics.lastEventTime = new Date();
        
        const count = this.eventMetrics.eventsByType.get(eventType) || 0;
        this.eventMetrics.eventsByType.set(eventType, count + 1);
    }

    /**
     * Emit to pattern-based listeners
     */
    emitToPatternListeners(event, eventData) {
        for (const [pattern, listeners] of this.eventPatterns) {
            if (this.matchesPattern(event, pattern)) {
                for (const listener of listeners) {
                    try {
                        listener(eventData);
                    } catch (error) {
                        console.error(`Error in pattern listener for ${pattern}:`, error);
                    }
                }
            }
        }
    }

    /**
     * Check if event matches pattern
     */
    matchesPattern(event, pattern) {
        // Convert glob-style pattern to regex
        const regexPattern = pattern
            .replace(/\*/g, '.*')
            .replace(/\?/g, '.')
            .replace(/\./g, '\\.');
        
        const regex = new RegExp(`^${regexPattern}$`);
        return regex.test(event);
    }

    /**
     * Enhanced on method with pattern support
     */
    on(event, listener) {
        if (event.includes('*') || event.includes('?')) {
            // Pattern-based listener
            return this.onPattern(event, listener);
        }
        
        return super.on(event, listener);
    }

    /**
     * Pattern-based event listening
     */
    onPattern(pattern, listener) {
        if (!this.eventPatterns.has(pattern)) {
            this.eventPatterns.set(pattern, []);
        }
        
        this.eventPatterns.get(pattern).push(listener);
        
        // Return unsubscribe function
        return () => {
            const listeners = this.eventPatterns.get(pattern);
            if (listeners) {
                const index = listeners.indexOf(listener);
                if (index > -1) {
                    listeners.splice(index, 1);
                }
                
                // Clean up empty pattern arrays
                if (listeners.length === 0) {
                    this.eventPatterns.delete(pattern);
                }
            }
        };
    }

    /**
     * Add middleware to the event processing chain
     */
    use(middleware) {
        if (typeof middleware !== 'function') {
            throw new Error('Middleware must be a function');
        }
        
        this.middleware.push(middleware);
        
        // Return function to remove middleware
        return () => {
            const index = this.middleware.indexOf(middleware);
            if (index > -1) {
                this.middleware.splice(index, 1);
            }
        };
    }

    /**
     * Structured event emitters for different domains
     */
    emitTaskEvent(taskId, event, data = {}) {
        this.emit(`task.${event}`, { taskId, ...data });
    }

    emitServiceEvent(serviceId, event, data = {}) {
        this.emit(`service.${event}`, { serviceId, ...data });
    }

    emitWorkflowEvent(workflowId, event, data = {}) {
        this.emit(`workflow.${event}`, { workflowId, ...data });
    }

    emitSystemEvent(event, data = {}) {
        this.emit(`system.${event}`, data);
    }

    /**
     * Get event history with optional filtering
     */
    getHistory(options = {}) {
        let events = [...this.eventHistory];
        
        // Filter by event type
        if (options.event) {
            const pattern = options.event;
            events = events.filter(e => this.matchesPattern(e.event, pattern));
        }
        
        // Filter by time range
        if (options.since) {
            const since = new Date(options.since);
            events = events.filter(e => new Date(e.timestamp) >= since);
        }
        
        if (options.until) {
            const until = new Date(options.until);
            events = events.filter(e => new Date(e.timestamp) <= until);
        }
        
        // Filter by source
        if (options.source) {
            events = events.filter(e => e.source === options.source);
        }
        
        // Limit results
        if (options.limit && options.limit > 0) {
            events = events.slice(-options.limit);
        }
        
        return events;
    }

    /**
     * Get event metrics and statistics
     */
    getMetrics() {
        const eventsByType = {};
        for (const [type, count] of this.eventMetrics.eventsByType) {
            eventsByType[type] = count;
        }
        
        return {
            totalEvents: this.eventMetrics.totalEvents,
            eventsByType,
            lastEventTime: this.eventMetrics.lastEventTime,
            historySize: this.eventHistory.length,
            activeListeners: this.listenerCount('*'),
            patternListeners: this.eventPatterns.size,
            middleware: this.middleware.length
        };
    }

    /**
     * Wait for a specific event with timeout
     */
    waitFor(event, timeout = 30000) {
        return new Promise((resolve, reject) => {
            let timeoutId;
            
            const listener = (eventData) => {
                clearTimeout(timeoutId);
                this.off(event, listener);
                resolve(eventData);
            };
            
            this.on(event, listener);
            
            timeoutId = setTimeout(() => {
                this.off(event, listener);
                reject(new Error(`Timeout waiting for event: ${event}`));
            }, timeout);
        });
    }

    /**
     * Wait for multiple events (all must occur)
     */
    waitForAll(events, timeout = 30000) {
        return Promise.all(
            events.map(event => this.waitFor(event, timeout))
        );
    }

    /**
     * Wait for any of multiple events (first one wins)
     */
    waitForAny(events, timeout = 30000) {
        return Promise.race(
            events.map(event => this.waitFor(event, timeout))
        );
    }

    /**
     * Setup internal event handling
     */
    setupInternalEvents() {
        // Log important system events
        this.on('orchestrator.*', (eventData) => {
            console.log(`🎯 Orchestrator: ${eventData.event}`, eventData.data);
        });

        this.on('service.failed', (eventData) => {
            console.warn(`⚠️ Service Failed: ${eventData.data.serviceId}`);
        });

        this.on('workflow.failed', (eventData) => {
            console.error(`❌ Workflow Failed: ${eventData.data.workflowId}`);
        });

        // Error handling
        this.on('error', (error) => {
            console.error('💥 EventBus Error:', error);
        });
    }

    /**
     * Initialize event persistence
     */
    initializePersistence() {
        // This would typically use a database or file system
        // For now, we'll implement basic file-based persistence
        console.log(`📁 Event persistence enabled: ${this.config.persistencePath}`);
        
        // Create persistence directory if it doesn't exist
        const fs = require('fs');
        const path = require('path');
        
        try {
            const dir = path.dirname(this.config.persistencePath);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
        } catch (error) {
            console.warn('Failed to create persistence directory:', error.message);
        }
    }

    /**
     * Persist single event (if persistence is enabled)
     */
    persistEvent(eventData) {
        if (!this.config.enablePersistence) return;
        
        try {
            const fs = require('fs');
            const eventLine = JSON.stringify(eventData) + '\n';
            fs.appendFileSync(this.config.persistencePath, eventLine);
        } catch (error) {
            console.warn('Failed to persist event:', error.message);
        }
    }

    /**
     * Load events from persistence
     */
    loadPersistedEvents() {
        if (!this.config.enablePersistence) return [];
        
        try {
            const fs = require('fs');
            if (!fs.existsSync(this.config.persistencePath)) {
                return [];
            }
            
            const content = fs.readFileSync(this.config.persistencePath, 'utf8');
            const lines = content.trim().split('\n').filter(line => line.length > 0);
            
            return lines.map(line => {
                try {
                    return JSON.parse(line);
                } catch (error) {
                    console.warn('Failed to parse persisted event:', line);
                    return null;
                }
            }).filter(event => event !== null);
            
        } catch (error) {
            console.warn('Failed to load persisted events:', error.message);
            return [];
        }
    }

    /**
     * Clear event history
     */
    clearHistory() {
        this.eventHistory = [];
        this.eventMetrics.totalEvents = 0;
        this.eventMetrics.eventsByType.clear();
        this.eventMetrics.lastEventTime = null;
    }

    /**
     * Create event stream (for real-time monitoring)
     */
    createStream(filter = '*') {
        const { Readable } = require('stream');
        
        const stream = new Readable({
            objectMode: true,
            read() {}
        });

        const listener = (eventData) => {
            stream.push(eventData);
        };

        this.onPattern(filter, listener);

        // Cleanup on stream end
        stream.on('close', () => {
            this.off(filter, listener);
        });

        return stream;
    }

    /**
     * Wait for human input with timeout and default response
     * Core functionality for Human-in-the-Loop operations
     * 
     * @param {Object} options - Wait configuration
     * @param {string} options.event_pattern - Event pattern to wait for
     * @param {number} options.timeout_seconds - Timeout in seconds
     * @param {any} options.default_response - Default response on timeout
     * @param {string} options.request_id - Unique request identifier
     * @param {Object} options.metadata - Additional metadata
     * @returns {Promise} Promise that resolves with input data or default response
     */
    async wait_for_input(options = {}) {
        const {
            event_pattern,
            timeout_seconds = 60,
            default_response = { status: 'timeout', reason: 'No response received within timeout' },
            request_id = this.generateRequestId(),
            metadata = {}
        } = options;

        return new Promise((resolve, reject) => {
            // Store the pending request
            const requestData = {
                request_id,
                event_pattern,
                timeout_seconds,
                default_response,
                metadata,
                created_at: new Date().toISOString(),
                resolve,
                reject
            };

            this.pendingInputRequests.set(request_id, requestData);

            // Set up event listener for the expected input
            const inputListener = (eventData) => {
                // Check if this event matches our request
                if (this.matchesInputRequest(eventData, requestData)) {
                    this.resolveInputRequest(request_id, eventData);
                }
            };

            // Listen for the input event
            this.onPattern(event_pattern, inputListener);

            // Set up timeout
            const timeoutId = setTimeout(() => {
                this.timeoutInputRequest(request_id);
            }, timeout_seconds * 1000);

            // Store timeout ID for cleanup
            this.inputTimeouts.set(request_id, { timeoutId, listener: inputListener, event_pattern });

            // Emit notification that we're waiting for input
            this.emit('input.waiting', {
                request_id,
                event_pattern,
                timeout_seconds,
                metadata,
                created_at: requestData.created_at
            });
        });
    }

    /**
     * Provide input for a waiting request
     * 
     * @param {string} request_id - Request identifier
     * @param {any} input_data - Input data to provide
     * @returns {boolean} True if request was found and resolved
     */
    provide_input(request_id, input_data) {
        if (this.pendingInputRequests.has(request_id)) {
            this.resolveInputRequest(request_id, {
                status: 'completed',
                data: input_data,
                provided_at: new Date().toISOString()
            });
            return true;
        }
        return false;
    }

    /**
     * Cancel a pending input request
     * 
     * @param {string} request_id - Request identifier
     * @param {string} reason - Cancellation reason
     * @returns {boolean} True if request was found and cancelled
     */
    cancel_input_request(request_id, reason = 'Cancelled by system') {
        if (this.pendingInputRequests.has(request_id)) {
            this.resolveInputRequest(request_id, {
                status: 'cancelled',
                reason,
                cancelled_at: new Date().toISOString()
            });
            return true;
        }
        return false;
    }

    /**
     * Get information about pending input requests
     * 
     * @returns {Array} Array of pending request information
     */
    get_pending_input_requests() {
        const pending = [];
        for (const [request_id, requestData] of this.pendingInputRequests) {
            pending.push({
                request_id,
                event_pattern: requestData.event_pattern,
                timeout_seconds: requestData.timeout_seconds,
                metadata: requestData.metadata,
                created_at: requestData.created_at,
                time_remaining: this.calculateTimeRemaining(requestData)
            });
        }
        return pending;
    }

    /**
     * Resolve an input request with provided data
     * 
     * @private
     * @param {string} request_id - Request identifier
     * @param {any} response_data - Response data
     */
    resolveInputRequest(request_id, response_data) {
        const requestData = this.pendingInputRequests.get(request_id);
        if (!requestData) return;

        // Clean up timeout and listener
        this.cleanupInputRequest(request_id);

        // Emit resolution event
        this.emit('input.resolved', {
            request_id,
            response_data,
            resolved_at: new Date().toISOString()
        });

        // Resolve the promise
        requestData.resolve(response_data);

        // Remove from pending requests
        this.pendingInputRequests.delete(request_id);
    }

    /**
     * Handle timeout for an input request
     * 
     * @private
     * @param {string} request_id - Request identifier
     */
    timeoutInputRequest(request_id) {
        const requestData = this.pendingInputRequests.get(request_id);
        if (!requestData) return;

        // Emit timeout event
        this.emit('input.timeout', {
            request_id,
            timeout_at: new Date().toISOString(),
            default_response: requestData.default_response
        });

        // Resolve with default response
        this.resolveInputRequest(request_id, requestData.default_response);
    }

    /**
     * Check if an event matches an input request
     * 
     * @private
     * @param {Object} eventData - Event data
     * @param {Object} requestData - Request data
     * @returns {boolean} True if event matches request
     */
    matchesInputRequest(eventData, requestData) {
        // Check if event pattern matches
        if (!this.matchesPattern(eventData.event, requestData.event_pattern)) {
            return false;
        }

        // Check if request_id matches (if present in event data)
        if (eventData.data && eventData.data.request_id) {
            return eventData.data.request_id === requestData.request_id;
        }

        return true;
    }

    /**
     * Clean up timeout and listeners for an input request
     * 
     * @private
     * @param {string} request_id - Request identifier
     */
    cleanupInputRequest(request_id) {
        const timeoutData = this.inputTimeouts.get(request_id);
        if (timeoutData) {
            // Clear timeout
            clearTimeout(timeoutData.timeoutId);
            
            // Remove pattern listener
            const listeners = this.eventPatterns.get(timeoutData.event_pattern);
            if (listeners) {
                const index = listeners.indexOf(timeoutData.listener);
                if (index > -1) {
                    listeners.splice(index, 1);
                    if (listeners.length === 0) {
                        this.eventPatterns.delete(timeoutData.event_pattern);
                    }
                }
            }
            
            this.inputTimeouts.delete(request_id);
        }
    }

    /**
     * Calculate remaining time for a request
     * 
     * @private
     * @param {Object} requestData - Request data
     * @returns {number} Remaining time in seconds
     */
    calculateTimeRemaining(requestData) {
        const created = new Date(requestData.created_at);
        const elapsed = (new Date() - created) / 1000;
        return Math.max(0, requestData.timeout_seconds - elapsed);
    }

    /**
     * Generate unique request ID
     * 
     * @private
     * @returns {string} Unique request identifier
     */
    generateRequestId() {
        return `input_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Enhanced wait for input with human escalation support
     * 
     * @param {Object} options - Wait configuration with escalation
     * @param {string} options.event_pattern - Event pattern to wait for
     * @param {number} options.timeout_seconds - Timeout in seconds
     * @param {any} options.default_response - Default response on timeout
     * @param {boolean} options.enable_escalation - Enable escalation on timeout
     * @param {Array} options.escalation_chain - Chain of escalation targets
     * @param {Object} options.escalation_data - Data for escalation
     * @returns {Promise} Promise that resolves with input data or escalated response
     */
    async wait_for_input_with_escalation(options = {}) {
        const {
            enable_escalation = true,
            escalation_chain = ['team_lead', 'manager', 'director'],
            escalation_data = {},
            ...waitOptions
        } = options;

        try {
            return await this.wait_for_input(waitOptions);
        } catch (error) {
            if (enable_escalation && escalation_chain.length > 0) {
                // Emit escalation event
                this.emit('input.escalation', {
                    original_request: waitOptions,
                    escalation_chain,
                    escalation_data,
                    escalation_reason: error.message || 'timeout',
                    escalated_at: new Date().toISOString()
                });

                // Try with next level in escalation chain
                const nextLevel = escalation_chain[0];
                const remainingChain = escalation_chain.slice(1);

                return this.wait_for_input_with_escalation({
                    ...options,
                    escalation_chain: remainingChain,
                    escalation_data: {
                        ...escalation_data,
                        escalated_from: options.escalation_data?.current_approver || 'system',
                        current_approver: nextLevel,
                        escalation_level: (options.escalation_data?.escalation_level || 0) + 1
                    }
                });
            }

            throw error;
        }
    }

    /**
     * Batch wait for multiple inputs
     * 
     * @param {Array} input_requests - Array of input request configurations
     * @param {Object} options - Batch options
     * @returns {Promise} Promise that resolves with array of responses
     */
    async wait_for_multiple_inputs(input_requests, options = {}) {
        const { 
            wait_for_all = true,
            timeout_seconds = 300,
            enable_partial_results = false 
        } = options;

        const promises = input_requests.map(request => 
            this.wait_for_input({
                timeout_seconds,
                ...request
            }).catch(error => ({ error: error.message, request }))
        );

        if (wait_for_all) {
            return Promise.all(promises);
        } else {
            // Wait for first completed response
            return Promise.race(promises);
        }
    }

    /**
     * Debug helper to list all listeners
     */
    getListenerInfo() {
        const standardEvents = {};
        const patternEvents = {};
        
        // Standard event listeners
        for (const event of this.eventNames()) {
            standardEvents[event] = this.listenerCount(event);
        }
        
        // Pattern listeners
        for (const [pattern, listeners] of this.eventPatterns) {
            patternEvents[pattern] = listeners.length;
        }
        
        return {
            standard: standardEvents,
            patterns: patternEvents,
            pending_inputs: this.pendingInputRequests.size,
            total: Object.values(standardEvents).reduce((a, b) => a + b, 0) +
                   Object.values(patternEvents).reduce((a, b) => a + b, 0)
        };
    }
}

module.exports = EventBus;