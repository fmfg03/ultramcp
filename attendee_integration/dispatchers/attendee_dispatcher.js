// Auto-Dispatch System for Attendee Actions
// Handles automatic dispatching of extracted actions from meetings

class AttendeeDispatcher {
  constructor(config = {}) {
    this.config = {
      autoDispatch: true,
      batchSize: 10,
      retryAttempts: 3,
      priorityLevels: ['low', 'medium', 'high', 'critical'],
      ...config
    };
    this.queue = [];
    this.processing = false;
  }

  // Add action to dispatch queue
  addAction(action) {
    const dispatchAction = {
      id: this.generateId(),
      ...action,
      status: 'pending',
      createdAt: new Date().toISOString(),
      attempts: 0
    };
    
    this.queue.push(dispatchAction);
    
    if (this.config.autoDispatch) {
      this.processQueue();
    }
    
    return dispatchAction.id;
  }

  // Process dispatch queue
  async processQueue() {
    if (this.processing) return;
    
    this.processing = true;
    
    try {
      const batch = this.queue
        .filter(action => action.status === 'pending')
        .sort((a, b) => this.getPriorityWeight(b.priority) - this.getPriorityWeight(a.priority))
        .slice(0, this.config.batchSize);
      
      for (const action of batch) {
        await this.dispatchAction(action);
      }
    } catch (error) {
      console.error('Error processing dispatch queue:', error);
    } finally {
      this.processing = false;
    }
  }

  // Dispatch individual action
  async dispatchAction(action) {
    try {
      action.status = 'dispatching';
      action.attempts++;
      
      // Simulate API call to dispatch action
      const result = await this.sendToAssignee(action);
      
      if (result.success) {
        action.status = 'dispatched';
        action.dispatchedAt = new Date().toISOString();
        console.log(`✅ Action dispatched: ${action.text} to ${action.assignee}`);
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      console.error(`❌ Failed to dispatch action ${action.id}:`, error);
      
      if (action.attempts < this.config.retryAttempts) {
        action.status = 'pending';
        setTimeout(() => this.processQueue(), 5000); // Retry after 5 seconds
      } else {
        action.status = 'failed';
        action.error = error.message;
      }
    }
  }

  // Send action to assignee (mock implementation)
  async sendToAssignee(action) {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, Math.random() * 1000));
    
    // Simulate 90% success rate
    if (Math.random() > 0.1) {
      return { success: true };
    } else {
      return { success: false, error: 'Network timeout' };
    }
  }

  // Get priority weight for sorting
  getPriorityWeight(priority) {
    const weights = { low: 1, medium: 2, high: 3, critical: 4 };
    return weights[priority] || 1;
  }

  // Generate unique ID
  generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  // Get queue status
  getQueueStatus() {
    const statusCounts = this.queue.reduce((acc, action) => {
      acc[action.status] = (acc[action.status] || 0) + 1;
      return acc;
    }, {});
    
    return {
      total: this.queue.length,
      processing: this.processing,
      statusCounts
    };
  }

  // Clear completed actions
  clearCompleted() {
    this.queue = this.queue.filter(action => 
      !['dispatched', 'failed'].includes(action.status)
    );
  }
}

module.exports = AttendeeDispatcher;

