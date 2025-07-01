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
            total: Object.values(standardEvents).reduce((a, b) => a + b, 0) +
                   Object.values(patternEvents).reduce((a, b) => a + b, 0)
        };
    }
}

module.exports = EventBus;