/**
 * State Manager for UltraMCP
 * 
 * Manages global, session, and task state with persistence,
 * watchers, and intelligent cleanup mechanisms.
 */

const fs = require('fs').promises;
const path = require('path');
const { generateWatcherId, ensureDirectory } = require('../utils');

class StateManager {
    constructor(config = {}) {
        this.config = {
            enablePersistence: config.enablePersistence || false,
            persistencePath: config.persistencePath || './data/state',
            cleanupInterval: config.cleanupInterval || 3600000, // 1 hour
            maxSessionAge: config.maxSessionAge || 86400000, // 24 hours
            maxTaskAge: config.maxTaskAge || 3600000, // 1 hour
            compressionEnabled: config.compressionEnabled || false,
            ...config
        };

        // State storage
        this.globalState = new Map();
        this.sessionStates = new Map();
        this.taskStates = new Map();
        
        // State metadata
        this.sessionMetadata = new Map(); // creation time, last access, etc.
        this.taskMetadata = new Map();
        
        // Watchers
        this.globalWatchers = new Map();
        this.sessionWatchers = new Map();
        this.taskWatchers = new Map();
        
        // Statistics
        this.stats = {
            globalOperations: 0,
            sessionOperations: 0,
            taskOperations: 0,
            watcherTriggers: 0,
            lastCleanup: null,
            memoryUsage: 0
        };

        // Cleanup timer
        this.cleanupTimer = null;
    }

    /**
     * Initialize state manager
     */
    async initialize() {
        console.log('💾 Initializing State Manager...');
        
        if (this.config.enablePersistence) {
            await this.initializePersistence();
            await this.loadPersistedState();
        }
        
        this.startCleanupTimer();
        this.updateMemoryUsage();
        
        console.log('✅ State Manager initialized');
    }

    /**
     * Initialize persistence directory and files
     */
    async initializePersistence() {
        try {
            await ensureDirectory(this.config.persistencePath);
            
            // Create subdirectories for different state types
            await ensureDirectory(path.join(this.config.persistencePath, 'global'));
            await ensureDirectory(path.join(this.config.persistencePath, 'sessions'));
            await ensureDirectory(path.join(this.config.persistencePath, 'tasks'));
            
            console.log(`📁 State persistence enabled: ${this.config.persistencePath}`);
        } catch (error) {
            console.warn('Failed to initialize state persistence:', error.message);
            this.config.enablePersistence = false;
        }
    }

    /**
     * Load persisted state from disk
     */
    async loadPersistedState() {
        try {
            // Load global state
            const globalStatePath = path.join(this.config.persistencePath, 'global', 'state.json');
            if (await this.fileExists(globalStatePath)) {
                const globalData = JSON.parse(await fs.readFile(globalStatePath, 'utf8'));
                for (const [key, value] of Object.entries(globalData)) {
                    this.globalState.set(key, value);
                }
                console.log(`📥 Loaded ${Object.keys(globalData).length} global state entries`);
            }
            
            // Load recent sessions (within max age)
            const sessionsDir = path.join(this.config.persistencePath, 'sessions');
            try {
                const sessionFiles = await fs.readdir(sessionsDir);
                let loadedSessions = 0;
                
                for (const file of sessionFiles) {
                    if (file.endsWith('.json')) {
                        const sessionId = file.replace('.json', '');
                        const sessionPath = path.join(sessionsDir, file);
                        
                        try {
                            const sessionData = JSON.parse(await fs.readFile(sessionPath, 'utf8'));
                            
                            // Check if session is within max age
                            const sessionAge = Date.now() - new Date(sessionData.metadata.createdAt).getTime();
                            if (sessionAge <= this.config.maxSessionAge) {
                                this.sessionStates.set(sessionId, new Map(Object.entries(sessionData.state)));
                                this.sessionMetadata.set(sessionId, sessionData.metadata);
                                loadedSessions++;
                            }
                        } catch (error) {
                            console.warn(`Failed to load session ${sessionId}:`, error.message);
                        }
                    }
                }
                
                if (loadedSessions > 0) {
                    console.log(`📥 Loaded ${loadedSessions} session states`);
                }
            } catch (error) {
                // Sessions directory might not exist
            }
            
        } catch (error) {
            console.warn('Failed to load persisted state:', error.message);
        }
    }

    // ===== GLOBAL STATE =====

    /**
     * Set global state value
     */
    setGlobal(key, value) {
        const oldValue = this.globalState.get(key);
        this.globalState.set(key, value);
        this.stats.globalOperations++;
        
        this.notifyWatchers('global', key, value, oldValue);
        
        if (this.config.enablePersistence) {
            this.persistGlobalState();
        }
        
        this.updateMemoryUsage();
    }

    /**
     * Get global state value
     */
    getGlobal(key, defaultValue = undefined) {
        return this.globalState.has(key) ? this.globalState.get(key) : defaultValue;
    }

    /**
     * Delete global state key
     */
    deleteGlobal(key) {
        const existed = this.globalState.delete(key);
        if (existed) {
            this.stats.globalOperations++;
            this.notifyWatchers('global', key, undefined, undefined);
            
            if (this.config.enablePersistence) {
                this.persistGlobalState();
            }
        }
        return existed;
    }

    /**
     * Get all global state keys
     */
    getGlobalKeys() {
        return Array.from(this.globalState.keys());
    }

    /**
     * Clear all global state
     */
    clearGlobal() {
        const keys = Array.from(this.globalState.keys());
        this.globalState.clear();
        this.stats.globalOperations++;
        
        // Notify watchers of each cleared key
        for (const key of keys) {
            this.notifyWatchers('global', key, undefined, undefined);
        }
        
        if (this.config.enablePersistence) {
            this.persistGlobalState();
        }
    }

    // ===== SESSION STATE =====

    /**
     * Set session state value
     */
    setSession(sessionId, key, value) {
        if (!this.sessionStates.has(sessionId)) {
            this.sessionStates.set(sessionId, new Map());
            this.sessionMetadata.set(sessionId, {
                createdAt: new Date().toISOString(),
                lastAccessed: new Date().toISOString(),
                operationCount: 0
            });
        }
        
        const sessionState = this.sessionStates.get(sessionId);
        const oldValue = sessionState.get(key);
        sessionState.set(key, value);
        
        // Update metadata
        const metadata = this.sessionMetadata.get(sessionId);
        metadata.lastAccessed = new Date().toISOString();
        metadata.operationCount++;
        
        this.stats.sessionOperations++;
        this.notifyWatchers('session', `${sessionId}:${key}`, value, oldValue);
        
        if (this.config.enablePersistence) {
            this.persistSessionState(sessionId);
        }
        
        this.updateMemoryUsage();
    }

    /**
     * Get session state value
     */
    getSession(sessionId, key, defaultValue = undefined) {
        const sessionState = this.sessionStates.get(sessionId);
        if (!sessionState) {
            return defaultValue;
        }
        
        // Update last accessed
        const metadata = this.sessionMetadata.get(sessionId);
        if (metadata) {
            metadata.lastAccessed = new Date().toISOString();
        }
        
        return sessionState.has(key) ? sessionState.get(key) : defaultValue;
    }

    /**
     * Delete session state key
     */
    deleteSession(sessionId, key) {
        const sessionState = this.sessionStates.get(sessionId);
        if (!sessionState) {
            return false;
        }
        
        const existed = sessionState.delete(key);
        if (existed) {
            this.stats.sessionOperations++;
            this.notifyWatchers('session', `${sessionId}:${key}`, undefined, undefined);
            
            if (this.config.enablePersistence) {
                this.persistSessionState(sessionId);
            }
        }
        
        return existed;
    }

    /**
     * Get all session state keys
     */
    getSessionKeys(sessionId) {
        const sessionState = this.sessionStates.get(sessionId);
        return sessionState ? Array.from(sessionState.keys()) : [];
    }

    /**
     * Clear entire session state
     */
    clearSession(sessionId) {
        const sessionState = this.sessionStates.get(sessionId);
        if (!sessionState) {
            return false;
        }
        
        const keys = Array.from(sessionState.keys());
        this.sessionStates.delete(sessionId);
        this.sessionMetadata.delete(sessionId);
        
        this.stats.sessionOperations++;
        
        // Notify watchers
        for (const key of keys) {
            this.notifyWatchers('session', `${sessionId}:${key}`, undefined, undefined);
        }
        
        if (this.config.enablePersistence) {
            this.deletePersistedSessionState(sessionId);
        }
        
        return true;
    }

    // ===== TASK STATE =====

    /**
     * Set task state value
     */
    setTask(taskId, key, value) {
        if (!this.taskStates.has(taskId)) {
            this.taskStates.set(taskId, new Map());
            this.taskMetadata.set(taskId, {
                createdAt: new Date().toISOString(),
                lastAccessed: new Date().toISOString(),
                operationCount: 0
            });
        }
        
        const taskState = this.taskStates.get(taskId);
        const oldValue = taskState.get(key);
        taskState.set(key, value);
        
        // Update metadata
        const metadata = this.taskMetadata.get(taskId);
        metadata.lastAccessed = new Date().toISOString();
        metadata.operationCount++;
        
        this.stats.taskOperations++;
        this.notifyWatchers('task', `${taskId}:${key}`, value, oldValue);
        
        if (this.config.enablePersistence) {
            this.persistTaskState(taskId);
        }
        
        this.updateMemoryUsage();
    }

    /**
     * Get task state value
     */
    getTask(taskId, key, defaultValue = undefined) {
        const taskState = this.taskStates.get(taskId);
        if (!taskState) {
            return defaultValue;
        }
        
        // Update last accessed
        const metadata = this.taskMetadata.get(taskId);
        if (metadata) {
            metadata.lastAccessed = new Date().toISOString();
        }
        
        return taskState.has(key) ? taskState.get(key) : defaultValue;
    }

    /**
     * Delete task state key
     */
    deleteTask(taskId, key) {
        const taskState = this.taskStates.get(taskId);
        if (!taskState) {
            return false;
        }
        
        const existed = taskState.delete(key);
        if (existed) {
            this.stats.taskOperations++;
            this.notifyWatchers('task', `${taskId}:${key}`, undefined, undefined);
            
            if (this.config.enablePersistence) {
                this.persistTaskState(taskId);
            }
        }
        
        return existed;
    }

    /**
     * Get all task state keys
     */
    getTaskKeys(taskId) {
        const taskState = this.taskStates.get(taskId);
        return taskState ? Array.from(taskState.keys()) : [];
    }

    /**
     * Clear entire task state
     */
    clearTask(taskId) {
        const taskState = this.taskStates.get(taskId);
        if (!taskState) {
            return false;
        }
        
        const keys = Array.from(taskState.keys());
        this.taskStates.delete(taskId);
        this.taskMetadata.delete(taskId);
        
        this.stats.taskOperations++;
        
        // Notify watchers
        for (const key of keys) {
            this.notifyWatchers('task', `${taskId}:${key}`, undefined, undefined);
        }
        
        if (this.config.enablePersistence) {
            this.deletePersistedTaskState(taskId);
        }
        
        return true;
    }

    // ===== WATCHERS =====

    /**
     * Watch for state changes
     */
    watch(scope, pattern, callback) {
        const watcherId = generateWatcherId();
        
        let watcherMap;
        switch (scope) {
            case 'global':
                watcherMap = this.globalWatchers;
                break;
            case 'session':
                watcherMap = this.sessionWatchers;
                break;
            case 'task':
                watcherMap = this.taskWatchers;
                break;
            default:
                throw new Error(`Invalid watcher scope: ${scope}`);
        }
        
        if (!watcherMap.has(pattern)) {
            watcherMap.set(pattern, new Map());
        }
        
        watcherMap.get(pattern).set(watcherId, callback);
        
        // Return unsubscribe function
        return () => {
            const patternWatchers = watcherMap.get(pattern);
            if (patternWatchers) {
                patternWatchers.delete(watcherId);
                if (patternWatchers.size === 0) {
                    watcherMap.delete(pattern);
                }
            }
        };
    }

    /**
     * Notify watchers of state changes
     */
    notifyWatchers(scope, key, newValue, oldValue) {
        let watcherMap;
        switch (scope) {
            case 'global':
                watcherMap = this.globalWatchers;
                break;
            case 'session':
                watcherMap = this.sessionWatchers;
                break;
            case 'task':
                watcherMap = this.taskWatchers;
                break;
            default:
                return;
        }
        
        for (const [pattern, callbacks] of watcherMap) {
            if (this.matchesPattern(key, pattern)) {
                for (const [watcherId, callback] of callbacks) {
                    try {
                        callback(key, newValue, oldValue);
                        this.stats.watcherTriggers++;
                    } catch (error) {
                        console.error(`Error in state watcher ${watcherId}:`, error);
                    }
                }
            }
        }
    }

    /**
     * Check if key matches pattern
     */
    matchesPattern(key, pattern) {
        // Simple glob-style pattern matching
        const regexPattern = pattern
            .replace(/\*/g, '.*')
            .replace(/\?/g, '.')
            .replace(/\./g, '\\.');
        
        const regex = new RegExp(`^${regexPattern}$`);
        return regex.test(key);
    }

    // ===== PERSISTENCE =====

    /**
     * Persist global state to disk
     */
    async persistGlobalState() {
        if (!this.config.enablePersistence) return;
        
        try {
            const globalStatePath = path.join(this.config.persistencePath, 'global', 'state.json');
            const globalData = Object.fromEntries(this.globalState);
            await fs.writeFile(globalStatePath, JSON.stringify(globalData, null, 2));
        } catch (error) {
            console.warn('Failed to persist global state:', error.message);
        }
    }

    /**
     * Persist session state to disk
     */
    async persistSessionState(sessionId) {
        if (!this.config.enablePersistence) return;
        
        try {
            const sessionPath = path.join(this.config.persistencePath, 'sessions', `${sessionId}.json`);
            const sessionState = this.sessionStates.get(sessionId);
            const metadata = this.sessionMetadata.get(sessionId);
            
            const sessionData = {
                sessionId,
                state: Object.fromEntries(sessionState),
                metadata
            };
            
            await fs.writeFile(sessionPath, JSON.stringify(sessionData, null, 2));
        } catch (error) {
            console.warn(`Failed to persist session state ${sessionId}:`, error.message);
        }
    }

    /**
     * Persist task state to disk
     */
    async persistTaskState(taskId) {
        if (!this.config.enablePersistence) return;
        
        try {
            const taskPath = path.join(this.config.persistencePath, 'tasks', `${taskId}.json`);
            const taskState = this.taskStates.get(taskId);
            const metadata = this.taskMetadata.get(taskId);
            
            const taskData = {
                taskId,
                state: Object.fromEntries(taskState),
                metadata
            };
            
            await fs.writeFile(taskPath, JSON.stringify(taskData, null, 2));
        } catch (error) {
            console.warn(`Failed to persist task state ${taskId}:`, error.message);
        }
    }

    /**
     * Delete persisted session state
     */
    async deletePersistedSessionState(sessionId) {
        if (!this.config.enablePersistence) return;
        
        try {
            const sessionPath = path.join(this.config.persistencePath, 'sessions', `${sessionId}.json`);
            await fs.unlink(sessionPath);
        } catch (error) {
            // File might not exist, that's okay
        }
    }

    /**
     * Delete persisted task state
     */
    async deletePersistedTaskState(taskId) {
        if (!this.config.enablePersistence) return;
        
        try {
            const taskPath = path.join(this.config.persistencePath, 'tasks', `${taskId}.json`);
            await fs.unlink(taskPath);
        } catch (error) {
            // File might not exist, that's okay
        }
    }

    // ===== CLEANUP =====

    /**
     * Start automatic cleanup timer
     */
    startCleanupTimer() {
        if (this.cleanupTimer) {
            clearInterval(this.cleanupTimer);
        }
        
        this.cleanupTimer = setInterval(() => {
            this.performCleanup();
        }, this.config.cleanupInterval);
    }

    /**
     * Perform state cleanup
     */
    performCleanup() {
        const now = Date.now();
        let cleanedSessions = 0;
        let cleanedTasks = 0;
        
        // Clean old sessions
        for (const [sessionId, metadata] of this.sessionMetadata) {
            const age = now - new Date(metadata.createdAt).getTime();
            if (age > this.config.maxSessionAge) {
                this.clearSession(sessionId);
                cleanedSessions++;
            }
        }
        
        // Clean old tasks
        for (const [taskId, metadata] of this.taskMetadata) {
            const age = now - new Date(metadata.createdAt).getTime();
            if (age > this.config.maxTaskAge) {
                this.clearTask(taskId);
                cleanedTasks++;
            }
        }
        
        this.stats.lastCleanup = new Date().toISOString();
        this.updateMemoryUsage();
        
        if (cleanedSessions > 0 || cleanedTasks > 0) {
            console.log(`🧹 State cleanup: removed ${cleanedSessions} sessions, ${cleanedTasks} tasks`);
        }
    }

    /**
     * Update memory usage statistics
     */
    updateMemoryUsage() {
        const process = require('process');
        this.stats.memoryUsage = process.memoryUsage().heapUsed;
    }

    // ===== UTILITY METHODS =====

    /**
     * Get state statistics
     */
    getStats() {
        return {
            ...this.stats,
            counts: {
                globalEntries: this.globalState.size,
                sessions: this.sessionStates.size,
                tasks: this.taskStates.size,
                globalWatchers: this.getTotalWatchers(this.globalWatchers),
                sessionWatchers: this.getTotalWatchers(this.sessionWatchers),
                taskWatchers: this.getTotalWatchers(this.taskWatchers)
            }
        };
    }

    /**
     * Get total number of watchers in a watcher map
     */
    getTotalWatchers(watcherMap) {
        let total = 0;
        for (const callbacks of watcherMap.values()) {
            total += callbacks.size;
        }
        return total;
    }

    /**
     * Export state for backup/debugging
     */
    exportState() {
        return {
            global: Object.fromEntries(this.globalState),
            sessions: Object.fromEntries(
                Array.from(this.sessionStates.entries()).map(([id, state]) => [
                    id,
                    {
                        state: Object.fromEntries(state),
                        metadata: this.sessionMetadata.get(id)
                    }
                ])
            ),
            tasks: Object.fromEntries(
                Array.from(this.taskStates.entries()).map(([id, state]) => [
                    id,
                    {
                        state: Object.fromEntries(state),
                        metadata: this.taskMetadata.get(id)
                    }
                ])
            ),
            stats: this.stats
        };
    }

    /**
     * Import state from backup
     */
    importState(stateData) {
        // Clear existing state
        this.globalState.clear();
        this.sessionStates.clear();
        this.taskStates.clear();
        this.sessionMetadata.clear();
        this.taskMetadata.clear();
        
        // Import global state
        if (stateData.global) {
            for (const [key, value] of Object.entries(stateData.global)) {
                this.globalState.set(key, value);
            }
        }
        
        // Import session states
        if (stateData.sessions) {
            for (const [sessionId, sessionData] of Object.entries(stateData.sessions)) {
                this.sessionStates.set(sessionId, new Map(Object.entries(sessionData.state)));
                this.sessionMetadata.set(sessionId, sessionData.metadata);
            }
        }
        
        // Import task states
        if (stateData.tasks) {
            for (const [taskId, taskData] of Object.entries(stateData.tasks)) {
                this.taskStates.set(taskId, new Map(Object.entries(taskData.state)));
                this.taskMetadata.set(taskId, taskData.metadata);
            }
        }
        
        this.updateMemoryUsage();
    }

    /**
     * Check if file exists
     */
    async fileExists(filePath) {
        try {
            await fs.access(filePath);
            return true;
        } catch {
            return false;
        }
    }

    /**
     * Shutdown state manager
     */
    async shutdown() {
        console.log('🛑 Shutting down State Manager...');
        
        // Stop cleanup timer
        if (this.cleanupTimer) {
            clearInterval(this.cleanupTimer);
        }
        
        // Final persist if enabled
        if (this.config.enablePersistence) {
            await this.persistGlobalState();
            
            // Persist all active sessions and tasks
            const sessionPromises = Array.from(this.sessionStates.keys()).map(id => 
                this.persistSessionState(id).catch(err => 
                    console.warn(`Failed to persist session ${id}:`, err.message)
                )
            );
            
            const taskPromises = Array.from(this.taskStates.keys()).map(id => 
                this.persistTaskState(id).catch(err => 
                    console.warn(`Failed to persist task ${id}:`, err.message)
                )
            );
            
            await Promise.allSettled([...sessionPromises, ...taskPromises]);
        }
        
        // Clear all state
        this.globalState.clear();
        this.sessionStates.clear();
        this.taskStates.clear();
        this.sessionMetadata.clear();
        this.taskMetadata.clear();
        this.globalWatchers.clear();
        this.sessionWatchers.clear();
        this.taskWatchers.clear();
        
        console.log('✅ State Manager shutdown complete');
    }
}

module.exports = StateManager;