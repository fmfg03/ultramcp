/**
 * Schemas for Attendee Integration
 * Defines data structures for transcriptions, actions, and meeting context
 */

// Base transcript schema from attendee
const TranscriptSchema = {
  type: 'object',
  required: ['timestamp', 'speaker', 'utterance'],
  properties: {
    timestamp: {
      type: 'string',
      format: 'date-time',
      description: 'ISO timestamp of the utterance'
    },
    speaker: {
      type: 'string',
      description: 'Name or identifier of the speaker'
    },
    utterance: {
      type: 'string',
      description: 'The spoken text content'
    },
    confidence: {
      type: 'number',
      minimum: 0,
      maximum: 1,
      description: 'Transcription confidence score'
    },
    language: {
      type: 'string',
      default: 'es',
      description: 'Language code of the utterance'
    },
    metadata: {
      type: 'object',
      properties: {
        audioQuality: { type: 'number' },
        backgroundNoise: { type: 'boolean' },
        speakerEmotion: { type: 'string' }
      }
    }
  }
}

// Extracted action schema
const ActionSchema = {
  type: 'object',
  required: ['id', 'source', 'timestamp', 'speaker', 'extractedAction', 'type'],
  properties: {
    id: {
      type: 'string',
      description: 'Unique action identifier'
    },
    source: {
      type: 'string',
      enum: ['attendee', 'manual', 'ai-generated'],
      description: 'Source of the action'
    },
    timestamp: {
      type: 'string',
      format: 'date-time',
      description: 'When the action was detected'
    },
    speaker: {
      type: 'string',
      description: 'Who mentioned the action'
    },
    originalText: {
      type: 'string',
      description: 'Original utterance text'
    },
    extractedAction: {
      type: 'string',
      description: 'Extracted action text'
    },
    confidence: {
      type: 'number',
      minimum: 0,
      maximum: 1,
      description: 'Extraction confidence'
    },
    type: {
      type: 'string',
      enum: ['task', 'decision', 'calendar', 'reminder', 'followup', 'question', 'risk'],
      description: 'Type of action'
    },
    entities: {
      type: 'object',
      properties: {
        assignee: { type: 'string' },
        assigneeType: { 
          type: 'string',
          enum: ['person', 'team', 'department', 'self', 'unknown']
        },
        assigneeConfidence: { type: 'number' },
        dueDate: { type: 'string', format: 'date-time' },
        dueDateConfidence: { type: 'number' },
        timeframe: { type: 'string' },
        isDeadline: { type: 'boolean' },
        priority: {
          type: 'string',
          enum: ['urgent', 'high', 'medium', 'low']
        },
        priorityConfidence: { type: 'number' },
        priorityReason: { type: 'string' },
        object: { type: 'string' },
        objectType: {
          type: 'string',
          enum: ['document', 'code', 'meeting', 'task', 'event']
        },
        objectConfidence: { type: 'number' },
        deliverables: {
          type: 'array',
          items: { type: 'string' }
        },
        project: { type: 'string' },
        client: { type: 'string' },
        tags: {
          type: 'array',
          items: { type: 'string' }
        },
        dependencies: {
          type: 'array',
          items: { type: 'string' }
        },
        blockers: {
          type: 'array',
          items: { type: 'string' }
        }
      }
    },
    entityConfidence: {
      type: 'number',
      description: 'Overall entity extraction confidence'
    },
    suggestedAgent: {
      type: 'string',
      description: 'Suggested MCP agent for execution'
    }
  }
}

// Meeting context schema
const MeetingContextSchema = {
  type: 'object',
  properties: {
    meetingId: {
      type: 'string',
      description: 'Unique meeting identifier'
    },
    title: {
      type: 'string',
      description: 'Meeting title or subject'
    },
    startTime: {
      type: 'string',
      format: 'date-time',
      description: 'Meeting start time'
    },
    participants: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          role: { type: 'string' },
          department: { type: 'string' },
          email: { type: 'string' }
        }
      }
    },
    currentPhase: {
      type: 'string',
      enum: ['opening', 'discussion', 'decision', 'planning', 'closing'],
      description: 'Current meeting phase'
    },
    previousActions: {
      type: 'array',
      items: ActionSchema,
      description: 'Actions detected earlier in the meeting'
    },
    interventionHistory: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          timestamp: { type: 'string', format: 'date-time' },
          type: { type: 'string' },
          message: { type: 'string' },
          confidence: { type: 'number' },
          response: { type: 'string' }
        }
      }
    },
    historicalMeetings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          date: { type: 'string', format: 'date' },
          title: { type: 'string' },
          actions: {
            type: 'array',
            items: ActionSchema
          },
          decisions: {
            type: 'array',
            items: { type: 'string' }
          }
        }
      }
    },
    projectContext: {
      type: 'object',
      properties: {
        activeProjects: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              name: { type: 'string' },
              status: { type: 'string' },
              deadline: { type: 'string', format: 'date' },
              team: { type: 'array', items: { type: 'string' } }
            }
          }
        },
        recentDecisions: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              decision: { type: 'string' },
              date: { type: 'string', format: 'date' },
              impact: { type: 'string' }
            }
          }
        }
      }
    }
  }
}

// Classification result schema
const ClassificationSchema = {
  type: 'object',
  required: ['action', 'type', 'confidence'],
  properties: {
    action: ActionSchema,
    type: {
      type: 'string',
      enum: ['task', 'decision', 'calendar', 'reminder', 'followup', 'question', 'risk']
    },
    confidence: {
      type: 'number',
      minimum: 0,
      maximum: 1
    },
    urgency: {
      type: 'string',
      enum: ['low', 'medium', 'high', 'urgent']
    },
    suggestedAgent: {
      type: 'string',
      description: 'Recommended MCP agent'
    },
    interventionNeeded: {
      type: 'boolean',
      description: 'Whether AI should intervene'
    },
    interventionType: {
      type: 'string',
      enum: ['missing_assignee', 'unclear_deadline', 'missing_details', 'dependency_conflict', 'resource_concern']
    },
    interventionMessage: {
      type: 'string',
      description: 'Suggested intervention message'
    },
    interventionConfidence: {
      type: 'number',
      minimum: 0,
      maximum: 1
    },
    interventionUrgency: {
      type: 'string',
      enum: ['low', 'medium', 'high']
    },
    contextAnalysis: {
      type: 'object',
      properties: {
        projectReferences: {
          type: 'array',
          items: { type: 'string' }
        },
        clientReferences: {
          type: 'array',
          items: { type: 'string' }
        },
        teamReferences: {
          type: 'array',
          items: { type: 'string' }
        },
        deadlineReferences: {
          type: 'array',
          items: { type: 'string' }
        },
        budgetReferences: {
          type: 'array',
          items: { type: 'string' }
        },
        meetingPhase: {
          type: 'string',
          enum: ['opening', 'discussion', 'decision', 'planning', 'closing']
        },
        relatedActions: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              id: { type: 'string' },
              similarity: { type: 'number' },
              extractedAction: { type: 'string' }
            }
          }
        },
        historicalContext: {
          type: 'object',
          properties: {
            previousDiscussions: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  meetingDate: { type: 'string', format: 'date' },
                  action: ActionSchema,
                  relevance: { type: 'number' }
                }
              }
            },
            recurringTopics: {
              type: 'array',
              items: { type: 'string' }
            },
            unfinishedActions: {
              type: 'array',
              items: ActionSchema
            }
          }
        }
      }
    },
    recommendations: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          type: {
            type: 'string',
            enum: ['action', 'context', 'dependency', 'intervention']
          },
          priority: {
            type: 'string',
            enum: ['low', 'medium', 'high']
          },
          message: { type: 'string' },
          mcpCall: {
            type: 'object',
            properties: {
              agent: { type: 'string' },
              action: { type: 'string' },
              payload: { type: 'object' }
            }
          }
        }
      }
    }
  }
}

// MCP payload schema for agent dispatch
const MCPPayloadSchema = {
  type: 'object',
  required: ['type', 'title'],
  properties: {
    type: {
      type: 'string',
      enum: ['task', 'decision', 'calendar', 'reminder', 'followup', 'question', 'risk']
    },
    title: {
      type: 'string',
      description: 'Action title or description'
    },
    assignee: {
      type: 'string',
      description: 'Person or team assigned'
    },
    dueDate: {
      type: 'string',
      format: 'date-time',
      description: 'Due date for the action'
    },
    priority: {
      type: 'string',
      enum: ['urgent', 'high', 'medium', 'low'],
      default: 'medium'
    },
    context: {
      type: 'object',
      properties: {
        source: {
          type: 'string',
          enum: ['meeting', 'email', 'chat', 'manual']
        },
        speaker: { type: 'string' },
        timestamp: { type: 'string', format: 'date-time' },
        meetingPhase: { type: 'string' },
        projects: {
          type: 'array',
          items: { type: 'string' }
        },
        relatedActions: {
          type: 'array',
          items: { type: 'string' }
        },
        originalText: { type: 'string' }
      }
    },
    metadata: {
      type: 'object',
      properties: {
        extractionConfidence: { type: 'number' },
        classificationConfidence: { type: 'number' },
        interventionTriggered: { type: 'boolean' },
        aiGenerated: { type: 'boolean' }
      }
    }
  }
}

// Real-time meeting state schema
const MeetingStateSchema = {
  type: 'object',
  properties: {
    sessionId: {
      type: 'string',
      description: 'Unique session identifier'
    },
    mode: {
      type: 'string',
      enum: ['ears-only', 'ears-and-mouth'],
      description: 'AI assistant mode'
    },
    isActive: {
      type: 'boolean',
      description: 'Whether meeting is currently active'
    },
    currentSpeaker: {
      type: 'string',
      description: 'Currently speaking participant'
    },
    transcriptionBuffer: {
      type: 'array',
      items: TranscriptSchema,
      description: 'Recent transcription chunks'
    },
    detectedActions: {
      type: 'array',
      items: ActionSchema,
      description: 'Actions detected in current session'
    },
    pendingInterventions: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          type: { type: 'string' },
          message: { type: 'string' },
          confidence: { type: 'number' },
          urgency: { type: 'string' },
          timestamp: { type: 'string', format: 'date-time' }
        }
      }
    },
    executedActions: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          actionId: { type: 'string' },
          mcpAgent: { type: 'string' },
          status: {
            type: 'string',
            enum: ['pending', 'executing', 'completed', 'failed']
          },
          result: { type: 'object' },
          timestamp: { type: 'string', format: 'date-time' }
        }
      }
    },
    settings: {
      type: 'object',
      properties: {
        autoExecuteActions: { type: 'boolean', default: false },
        interventionThreshold: { type: 'number', default: 0.8 },
        maxInterventionsPerMinute: { type: 'number', default: 2 },
        enableContextAwareness: { type: 'boolean', default: true },
        preferredLanguage: { type: 'string', default: 'es' }
      }
    }
  }
}

// Validation functions
const validateTranscript = (data) => {
  // Basic validation - in production would use JSON Schema validator
  const required = ['timestamp', 'speaker', 'utterance']
  return required.every(field => data.hasOwnProperty(field))
}

const validateAction = (data) => {
  const required = ['id', 'source', 'timestamp', 'speaker', 'extractedAction', 'type']
  return required.every(field => data.hasOwnProperty(field))
}

const validateMeetingContext = (data) => {
  return data && typeof data === 'object'
}

const validateClassification = (data) => {
  const required = ['action', 'type', 'confidence']
  return required.every(field => data.hasOwnProperty(field))
}

const validateMCPPayload = (data) => {
  const required = ['type', 'title']
  return required.every(field => data.hasOwnProperty(field))
}

// Schema exports
module.exports = {
  schemas: {
    TranscriptSchema,
    ActionSchema,
    MeetingContextSchema,
    ClassificationSchema,
    MCPPayloadSchema,
    MeetingStateSchema
  },
  validators: {
    validateTranscript,
    validateAction,
    validateMeetingContext,
    validateClassification,
    validateMCPPayload
  },
  
  // Helper functions for schema creation
  createEmptyMeetingContext: () => ({
    meetingId: null,
    title: null,
    startTime: new Date().toISOString(),
    participants: [],
    currentPhase: 'opening',
    previousActions: [],
    interventionHistory: [],
    historicalMeetings: [],
    projectContext: {
      activeProjects: [],
      recentDecisions: []
    }
  }),

  createEmptyMeetingState: (sessionId, mode = 'ears-only') => ({
    sessionId,
    mode,
    isActive: false,
    currentSpeaker: null,
    transcriptionBuffer: [],
    detectedActions: [],
    pendingInterventions: [],
    executedActions: [],
    settings: {
      autoExecuteActions: false,
      interventionThreshold: 0.8,
      maxInterventionsPerMinute: 2,
      enableContextAwareness: true,
      preferredLanguage: 'es'
    }
  }),

  createActionFromTranscript: (transcript, extractedAction, type, confidence) => ({
    id: `action_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    source: 'attendee',
    timestamp: transcript.timestamp,
    speaker: transcript.speaker,
    originalText: transcript.utterance,
    extractedAction,
    confidence,
    type,
    entities: {},
    entityConfidence: 0,
    suggestedAgent: null
  })
}

