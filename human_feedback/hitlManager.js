/**
 * Human-in-the-Loop (HITL) System for MCP
 * Preparation for future human feedback integration
 */

class HITLManager {
    constructor() {
        this.pendingInterventions = new Map();
        this.feedbackQueue = [];
        this.interventionHandlers = new Map();
        this.config = {
            autoApproveThreshold: 0.9,
            interventionTimeout: 300000, // 5 minutes
            maxPendingInterventions: 100
        };
    }

    /**
     * Request human intervention
     * @param {Object} context - Context requiring intervention
     * @returns {Promise} Intervention result
     */
    async requestIntervention(context) {
        const interventionId = this.generateInterventionId();
        
        const intervention = {
            id: interventionId,
            timestamp: new Date().toISOString(),
            context: context,
            status: 'pending',
            priority: this.calculatePriority(context),
            timeout: Date.now() + this.config.interventionTimeout
        };

        // Check if auto-approval is possible
        if (context.confidence >= this.config.autoApproveThreshold) {
            intervention.status = 'auto_approved';
            intervention.decision = 'approve';
            intervention.reason = 'High confidence auto-approval';
            return intervention;
        }

        // Add to pending interventions
        this.pendingInterventions.set(interventionId, intervention);

        // Trigger intervention handlers
        await this.triggerInterventionHandlers('intervention_requested', intervention);

        // Return promise that resolves when intervention is complete
        return new Promise((resolve, reject) => {
            intervention.resolve = resolve;
            intervention.reject = reject;

            // Set timeout
            setTimeout(() => {
                if (intervention.status === 'pending') {
                    intervention.status = 'timeout';
                    intervention.decision = 'timeout';
                    this.pendingInterventions.delete(interventionId);
                    resolve(intervention);
                }
            }, this.config.interventionTimeout);
        });
    }

    /**
     * Provide human feedback
     * @param {string} interventionId - Intervention ID
     * @param {Object} feedback - Human feedback
     */
    async provideFeedback(interventionId, feedback) {
        const intervention = this.pendingInterventions.get(interventionId);
        
        if (!intervention) {
            throw new Error(`Intervention ${interventionId} not found`);
        }

        if (intervention.status !== 'pending') {
            throw new Error(`Intervention ${interventionId} is not pending`);
        }

        // Update intervention with feedback
        intervention.status = 'completed';
        intervention.decision = feedback.decision;
        intervention.feedback = feedback;
        intervention.completedAt = new Date().toISOString();
        intervention.humanId = feedback.humanId;

        // Remove from pending
        this.pendingInterventions.delete(interventionId);

        // Store feedback for learning
        this.feedbackQueue.push({
            interventionId,
            feedback,
            context: intervention.context,
            timestamp: new Date().toISOString()
        });

        // Trigger completion handlers
        await this.triggerInterventionHandlers('intervention_completed', intervention);

        // Resolve the promise
        if (intervention.resolve) {
            intervention.resolve(intervention);
        }

        return intervention;
    }

    /**
     * Calculate intervention priority
     * @param {Object} context - Context object
     * @returns {string} Priority level
     */
    calculatePriority(context) {
        // High priority conditions
        if (context.errorCount > 2) return 'high';
        if (context.cost > 1.0) return 'high';
        if (context.userFacing) return 'high';

        // Medium priority conditions
        if (context.confidence < 0.5) return 'medium';
        if (context.complexity > 0.8) return 'medium';

        // Default to low priority
        return 'low';
    }

    /**
     * Generate unique intervention ID
     * @returns {string} Intervention ID
     */
    generateInterventionId() {
        const timestamp = Date.now();
        const random = Math.random().toString(36).substring(2, 8);
        return `hitl_${timestamp}_${random}`;
    }

    /**
     * Register intervention handler
     * @param {string} event - Event type
     * @param {Function} handler - Handler function
     */
    onIntervention(event, handler) {
        if (!this.interventionHandlers.has(event)) {
            this.interventionHandlers.set(event, []);
        }
        this.interventionHandlers.get(event).push(handler);
    }

    /**
     * Trigger intervention handlers
     * @param {string} event - Event type
     * @param {Object} data - Event data
     */
    async triggerInterventionHandlers(event, data) {
        const handlers = this.interventionHandlers.get(event) || [];
        
        for (const handler of handlers) {
            try {
                await handler(data);
            } catch (error) {
                console.error(`HITL handler error for event ${event}:`, error);
            }
        }
    }

    /**
     * Get pending interventions
     * @param {Object} filters - Filter options
     * @returns {Array} Pending interventions
     */
    getPendingInterventions(filters = {}) {
        let interventions = Array.from(this.pendingInterventions.values());

        // Apply filters
        if (filters.priority) {
            interventions = interventions.filter(i => i.priority === filters.priority);
        }

        if (filters.minAge) {
            const minTime = Date.now() - filters.minAge;
            interventions = interventions.filter(i => new Date(i.timestamp).getTime() < minTime);
        }

        // Sort by priority and timestamp
        interventions.sort((a, b) => {
            const priorityOrder = { high: 3, medium: 2, low: 1 };
            const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
            
            if (priorityDiff !== 0) return priorityDiff;
            
            return new Date(a.timestamp) - new Date(b.timestamp);
        });

        return interventions;
    }

    /**
     * Get intervention statistics
     * @returns {Object} Statistics
     */
    getStats() {
        const pending = this.pendingInterventions.size;
        const feedbackCount = this.feedbackQueue.length;
        
        // Calculate feedback stats
        const approvals = this.feedbackQueue.filter(f => f.feedback.decision === 'approve').length;
        const rejections = this.feedbackQueue.filter(f => f.feedback.decision === 'reject').length;
        const modifications = this.feedbackQueue.filter(f => f.feedback.decision === 'modify').length;

        return {
            pending_interventions: pending,
            total_feedback: feedbackCount,
            approval_rate: feedbackCount > 0 ? approvals / feedbackCount : 0,
            rejection_rate: feedbackCount > 0 ? rejections / feedbackCount : 0,
            modification_rate: feedbackCount > 0 ? modifications / feedbackCount : 0,
            avg_response_time: this.calculateAvgResponseTime()
        };
    }

    /**
     * Calculate average response time
     * @returns {number} Average response time in milliseconds
     */
    calculateAvgResponseTime() {
        const completedInterventions = this.feedbackQueue.filter(f => f.feedback.responseTime);
        
        if (completedInterventions.length === 0) return 0;
        
        const totalTime = completedInterventions.reduce((sum, f) => sum + f.feedback.responseTime, 0);
        return totalTime / completedInterventions.length;
    }

    /**
     * Clean up expired interventions
     */
    cleanupExpired() {
        const now = Date.now();
        const expired = [];

        for (const [id, intervention] of this.pendingInterventions) {
            if (now > intervention.timeout) {
                expired.push(id);
            }
        }

        for (const id of expired) {
            const intervention = this.pendingInterventions.get(id);
            intervention.status = 'expired';
            intervention.decision = 'timeout';
            
            if (intervention.resolve) {
                intervention.resolve(intervention);
            }
            
            this.pendingInterventions.delete(id);
        }

        return expired.length;
    }
}

/**
 * HITL Integration Points for MCP Agents
 */
class MCPHITLIntegration {
    constructor(hitlManager) {
        this.hitl = hitlManager;
    }

    /**
     * Check if task requires human intervention
     * @param {Object} taskContext - Task context
     * @returns {boolean} Whether intervention is needed
     */
    requiresIntervention(taskContext) {
        // Low confidence results
        if (taskContext.confidence < 0.6) return true;

        // High cost operations
        if (taskContext.estimatedCost > 0.5) return true;

        // User-facing content
        if (taskContext.userFacing) return true;

        // Sensitive operations
        if (taskContext.sensitive) return true;

        // Multiple failures
        if (taskContext.failureCount > 1) return true;

        return false;
    }

    /**
     * Request intervention for agent decision
     * @param {string} agentName - Agent name
     * @param {Object} decision - Agent decision
     * @param {Object} context - Decision context
     */
    async requestAgentIntervention(agentName, decision, context) {
        const interventionContext = {
            type: 'agent_decision',
            agent: agentName,
            decision: decision,
            context: context,
            confidence: decision.confidence || 0.5,
            userFacing: context.userFacing || false,
            sensitive: context.sensitive || false,
            estimatedCost: context.estimatedCost || 0,
            failureCount: context.failureCount || 0
        };

        return await this.hitl.requestIntervention(interventionContext);
    }

    /**
     * Request intervention for task execution
     * @param {Object} task - Task object
     * @param {Object} result - Task result
     * @param {Object} context - Execution context
     */
    async requestTaskIntervention(task, result, context) {
        const interventionContext = {
            type: 'task_execution',
            task: task,
            result: result,
            context: context,
            confidence: result.confidence || 0.5,
            userFacing: task.userFacing || false,
            sensitive: task.sensitive || false,
            estimatedCost: context.estimatedCost || 0,
            failureCount: context.failureCount || 0
        };

        return await this.hitl.requestIntervention(interventionContext);
    }

    /**
     * Request intervention for content generation
     * @param {Object} content - Generated content
     * @param {Object} context - Generation context
     */
    async requestContentIntervention(content, context) {
        const interventionContext = {
            type: 'content_generation',
            content: content,
            context: context,
            confidence: content.confidence || 0.5,
            userFacing: true, // Content is typically user-facing
            sensitive: context.sensitive || false,
            estimatedCost: context.estimatedCost || 0
        };

        return await this.hitl.requestIntervention(interventionContext);
    }
}

// Global HITL manager instance
const hitlManager = new HITLManager();
const mcpHitlIntegration = new MCPHITLIntegration(hitlManager);

module.exports = {
    HITLManager,
    MCPHITLIntegration,
    hitlManager,
    mcpHitlIntegration
};

