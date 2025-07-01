/**
 * Utility functions for UltraMCP Core
 */

const crypto = require('crypto');
const fs = require('fs').promises;
const path = require('path');
const yaml = require('js-yaml');

/**
 * Generate unique task ID
 */
function generateTaskId() {
    const timestamp = Date.now().toString(36);
    const random = crypto.randomBytes(4).toString('hex');
    return `task_${timestamp}_${random}`;
}

/**
 * Generate unique event ID
 */
function generateEventId() {
    const timestamp = Date.now().toString(36);
    const random = crypto.randomBytes(3).toString('hex');
    return `evt_${timestamp}_${random}`;
}

/**
 * Generate unique session ID
 */
function generateSessionId() {
    return crypto.randomBytes(16).toString('hex');
}

/**
 * Generate unique execution ID
 */
function generateExecutionId() {
    const timestamp = Date.now().toString(36);
    const random = crypto.randomBytes(4).toString('hex');
    return `exec_${timestamp}_${random}`;
}

/**
 * Generate unique watcher ID
 */
function generateWatcherId() {
    return crypto.randomBytes(8).toString('hex');
}

/**
 * Load configuration from file
 */
async function loadConfig(configPath) {
    try {
        const content = await fs.readFile(configPath, 'utf8');
        
        if (configPath.endsWith('.json')) {
            return JSON.parse(content);
        } else if (configPath.endsWith('.yml') || configPath.endsWith('.yaml')) {
            return yaml.load(content);
        } else {
            throw new Error(`Unsupported config file format: ${configPath}`);
        }
    } catch (error) {
        if (error.code === 'ENOENT') {
            throw new Error(`Configuration file not found: ${configPath}`);
        }
        throw new Error(`Failed to load configuration: ${error.message}`);
    }
}

/**
 * Deep merge objects
 */
function deepMerge(target, source) {
    const result = { ...target };
    
    for (const key in source) {
        if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
            result[key] = deepMerge(result[key] || {}, source[key]);
        } else {
            result[key] = source[key];
        }
    }
    
    return result;
}

/**
 * Validate required environment variables
 */
function validateEnvironment(requiredVars) {
    const missing = [];
    
    for (const varName of requiredVars) {
        if (!process.env[varName]) {
            missing.push(varName);
        }
    }
    
    if (missing.length > 0) {
        throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
    }
}

/**
 * Create directory if it doesn't exist
 */
async function ensureDirectory(dirPath) {
    try {
        await fs.mkdir(dirPath, { recursive: true });
    } catch (error) {
        if (error.code !== 'EEXIST') {
            throw error;
        }
    }
}

/**
 * Check if file exists
 */
async function fileExists(filePath) {
    try {
        await fs.access(filePath);
        return true;
    } catch {
        return false;
    }
}

/**
 * Retry function with exponential backoff
 */
async function retry(fn, options = {}) {
    const {
        maxAttempts = 3,
        baseDelay = 1000,
        maxDelay = 10000,
        exponential = true
    } = options;
    
    let lastError;
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            return await fn();
        } catch (error) {
            lastError = error;
            
            if (attempt === maxAttempts) {
                break;
            }
            
            const delay = exponential 
                ? Math.min(baseDelay * Math.pow(2, attempt - 1), maxDelay)
                : baseDelay;
                
            await sleep(delay);
        }
    }
    
    throw lastError;
}

/**
 * Sleep for specified milliseconds
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Timeout wrapper for promises
 */
function withTimeout(promise, timeoutMs, errorMessage = 'Operation timed out') {
    return Promise.race([
        promise,
        new Promise((_, reject) => 
            setTimeout(() => reject(new Error(errorMessage)), timeoutMs)
        )
    ]);
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function
 */
function throttle(func, limit) {
    let inThrottle;
    
    return function executedFunction(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Format bytes to human readable string
 */
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Format duration to human readable string
 */
function formatDuration(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) {
        return `${days}d ${hours % 24}h ${minutes % 60}m`;
    } else if (hours > 0) {
        return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${seconds % 60}s`;
    } else {
        return `${seconds}s`;
    }
}

/**
 * Sanitize string for safe usage
 */
function sanitizeString(str, maxLength = 1000) {
    if (typeof str !== 'string') {
        str = String(str);
    }
    
    // Remove control characters and limit length
    return str
        .replace(/[\x00-\x1F\x7F]/g, '') // Remove control characters
        .substring(0, maxLength)
        .trim();
}

/**
 * Parse key-value pairs from string
 */
function parseKeyValuePairs(str, delimiter = '=', separator = ',') {
    const pairs = {};
    
    if (!str) return pairs;
    
    const items = str.split(separator);
    for (const item of items) {
        const [key, ...valueParts] = item.split(delimiter);
        if (key && valueParts.length > 0) {
            pairs[key.trim()] = valueParts.join(delimiter).trim();
        }
    }
    
    return pairs;
}

/**
 * Convert camelCase to snake_case
 */
function camelToSnake(str) {
    return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
}

/**
 * Convert snake_case to camelCase
 */
function snakeToCamel(str) {
    return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

/**
 * Get nested property value safely
 */
function getNestedProperty(obj, path, defaultValue = undefined) {
    const keys = path.split('.');
    let current = obj;
    
    for (const key of keys) {
        if (current == null || typeof current !== 'object') {
            return defaultValue;
        }
        current = current[key];
    }
    
    return current !== undefined ? current : defaultValue;
}

/**
 * Set nested property value
 */
function setNestedProperty(obj, path, value) {
    const keys = path.split('.');
    let current = obj;
    
    for (let i = 0; i < keys.length - 1; i++) {
        const key = keys[i];
        if (!(key in current) || typeof current[key] !== 'object') {
            current[key] = {};
        }
        current = current[key];
    }
    
    current[keys[keys.length - 1]] = value;
}

/**
 * Create a simple LRU cache
 */
function createLRUCache(maxSize = 100) {
    const cache = new Map();
    
    return {
        get(key) {
            if (cache.has(key)) {
                const value = cache.get(key);
                cache.delete(key);
                cache.set(key, value); // Move to end
                return value;
            }
            return undefined;
        },
        
        set(key, value) {
            if (cache.has(key)) {
                cache.delete(key);
            } else if (cache.size >= maxSize) {
                const firstKey = cache.keys().next().value;
                cache.delete(firstKey);
            }
            cache.set(key, value);
        },
        
        has(key) {
            return cache.has(key);
        },
        
        delete(key) {
            return cache.delete(key);
        },
        
        clear() {
            cache.clear();
        },
        
        size() {
            return cache.size;
        }
    };
}

/**
 * Create a rate limiter
 */
function createRateLimiter(maxRequests = 100, windowMs = 60000) {
    const requests = new Map();
    
    return {
        isAllowed(key) {
            const now = Date.now();
            const windowStart = now - windowMs;
            
            // Clean old entries
            for (const [reqKey, timestamps] of requests) {
                const validTimestamps = timestamps.filter(t => t > windowStart);
                if (validTimestamps.length === 0) {
                    requests.delete(reqKey);
                } else {
                    requests.set(reqKey, validTimestamps);
                }
            }
            
            // Check current key
            const keyRequests = requests.get(key) || [];
            const validRequests = keyRequests.filter(t => t > windowStart);
            
            if (validRequests.length >= maxRequests) {
                return false;
            }
            
            validRequests.push(now);
            requests.set(key, validRequests);
            return true;
        },
        
        getUsage(key) {
            const now = Date.now();
            const windowStart = now - windowMs;
            const keyRequests = requests.get(key) || [];
            const validRequests = keyRequests.filter(t => t > windowStart);
            
            return {
                current: validRequests.length,
                max: maxRequests,
                remaining: Math.max(0, maxRequests - validRequests.length),
                resetTime: new Date(now + windowMs)
            };
        }
    };
}

/**
 * Hash object to create consistent string
 */
function hashObject(obj) {
    const str = JSON.stringify(obj, Object.keys(obj).sort());
    return crypto.createHash('sha256').update(str).digest('hex');
}

/**
 * Safe JSON parse with default value
 */
function safeJSONParse(str, defaultValue = null) {
    try {
        return JSON.parse(str);
    } catch {
        return defaultValue;
    }
}

/**
 * Safe JSON stringify
 */
function safeJSONStringify(obj, space = 0) {
    try {
        return JSON.stringify(obj, null, space);
    } catch (error) {
        return JSON.stringify({ error: 'Serialization failed', message: error.message });
    }
}

module.exports = {
    generateTaskId,
    generateEventId,
    generateSessionId,
    generateExecutionId,
    generateWatcherId,
    loadConfig,
    deepMerge,
    validateEnvironment,
    ensureDirectory,
    fileExists,
    retry,
    sleep,
    withTimeout,
    debounce,
    throttle,
    formatBytes,
    formatDuration,
    sanitizeString,
    parseKeyValuePairs,
    camelToSnake,
    snakeToCamel,
    getNestedProperty,
    setNestedProperty,
    createLRUCache,
    createRateLimiter,
    hashObject,
    safeJSONParse,
    safeJSONStringify
};