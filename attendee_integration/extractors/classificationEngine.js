/**
 * Classification Engine for Meeting Actions
 * Classifies detected actions and determines intervention strategies
 */

class ClassificationEngine {
  constructor() {
    // Action type classifications with confidence thresholds
    this.actionTypes = {
      task: {
        keywords: ['hacer', 'crear', 'generar', 'desarrollar', 'implementar', 'construir', 'escribir', 'preparar'],
        patterns: [/hay que ([^.!?]+)/, /necesitamos ([^.!?]+)/, /vamos a ([^.!?]+)/],
        confidence: 0.8,
        urgency: 'medium',
        mcpAgent: 'taskBuilderAgent'
      },
      decision: {
        keywords: ['acordar', 'decidir', 'aprobar', 'rechazar', 'confirmar', 'establecer', 'definir'],
        patterns: [/se acordó ([^.!?]+)/, /decidimos ([^.!?]+)/, /se estableció ([^.!?]+)/],
        confidence: 0.9,
        urgency: 'high',
        mcpAgent: 'decisionLoggerAgent'
      },
      calendar: {
        keywords: ['reunión', 'meeting', 'agendar', 'schedule', 'cita', 'appointment', 'call'],
        patterns: [/reunión ([^.!?]+)/, /agendemos ([^.!?]+)/, /meeting ([^.!?]+)/],
        confidence: 0.85,
        urgency: 'medium',
        mcpAgent: 'calendarAgent'
      },
      reminder: {
        keywords: ['recordar', 'reminder', 'avisar', 'notificar', 'alert'],
        patterns: [/recordar ([^.!?]+)/, /reminder ([^.!?]+)/, /no olvides ([^.!?]+)/],
        confidence: 0.8,
        urgency: 'low',
        mcpAgent: 'notifierAgent'
      },
      followup: {
        keywords: ['seguimiento', 'follow', 'revisar', 'check', 'monitorear', 'supervisar'],
        patterns: [/seguimiento ([^.!?]+)/, /follow up ([^.!?]+)/, /revisar ([^.!?]+)/],
        confidence: 0.75,
        urgency: 'medium',
        mcpAgent: 'followupAgent'
      },
      question: {
        keywords: ['pregunta', 'question', 'duda', 'clarificar', 'aclarar'],
        patterns: [/\?$/, /pregunta ([^.!?]+)/, /no está claro ([^.!?]+)/],
        confidence: 0.7,
        urgency: 'high',
        mcpAgent: 'clarificationAgent'
      },
      risk: {
        keywords: ['problema', 'issue', 'riesgo', 'risk', 'blocker', 'impedimento'],
        patterns: [/problema con ([^.!?]+)/, /riesgo de ([^.!?]+)/, /bloqueado ([^.!?]+)/],
        confidence: 0.85,
        urgency: 'high',
        mcpAgent: 'riskManagementAgent'
      }
    }

    // Intervention triggers based on context
    this.interventionTriggers = {
      missing_assignee: {
        pattern: /hay que|necesitamos|vamos a/,
        noAssignee: true,
        confidence: 0.8,
        question: "¿Quién se encarga de esta tarea?"
      },
      unclear_deadline: {
        pattern: /pronto|soon|rápido|quick/,
        noDeadline: true,
        confidence: 0.7,
        question: "¿Cuándo necesitamos esto listo?"
      },
      missing_details: {
        pattern: /esto|eso|that|it/,
        vague: true,
        confidence: 0.6,
        question: "¿Podrías especificar más detalles sobre esto?"
      },
      dependency_conflict: {
        pattern: /depende|depends|necesita|requires/,
        hasDependency: true,
        confidence: 0.9,
        question: "¿Esto podría afectar otros proyectos en curso?"
      },
      resource_concern: {
        pattern: /no tenemos|don't have|falta|missing/,
        resourceIssue: true,
        confidence: 0.85,
        question: "¿Necesitamos conseguir recursos adicionales?"
      }
    }

    // Context awareness patterns
    this.contextPatterns = {
      project_reference: /proyecto\s+([a-zA-Z\s]+)/gi,
      client_reference: /cliente\s+([a-zA-Z\s]+)/gi,
      deadline_reference: /(antes del|para el|by)\s+([a-zA-Z0-9\s]+)/gi,
      team_reference: /(equipo|team)\s+([a-zA-Z\s]+)/gi,
      budget_reference: /(presupuesto|budget)\s+([a-zA-Z0-9\s]+)/gi
    }

    // Meeting flow states
    this.meetingStates = {
      opening: ['comenzamos', 'empezamos', 'start', 'begin'],
      discussion: ['discutir', 'analizar', 'discuss', 'analyze'],
      decision: ['decidir', 'acordar', 'decide', 'agree'],
      planning: ['planificar', 'organizar', 'plan', 'organize'],
      closing: ['terminamos', 'concluir', 'finish', 'conclude']
    }
  }

  /**
   * Classify an action and determine intervention strategy
   * @param {Object} action - The action object
   * @param {Object} meetingContext - Current meeting context
   * @returns {Object} Classification result with intervention suggestions
   */
  classifyAction(action, meetingContext = {}) {
    const classification = {
      action,
      type: 'unknown',
      confidence: 0,
      urgency: 'medium',
      suggestedAgent: null,
      interventionNeeded: false,
      interventionType: null,
      interventionMessage: null,
      contextAnalysis: {},
      recommendations: []
    }

    // Classify action type
    const typeClassification = this._classifyActionType(action.extractedAction)
    Object.assign(classification, typeClassification)

    // Analyze context
    classification.contextAnalysis = this._analyzeContext(action, meetingContext)

    // Determine intervention needs
    const interventionAnalysis = this._analyzeInterventionNeeds(action, meetingContext)
    Object.assign(classification, interventionAnalysis)

    // Generate recommendations
    classification.recommendations = this._generateRecommendations(classification)

    return classification
  }

  /**
   * Classify the type of action
   * @param {string} actionText - The action text
   * @returns {Object} Type classification
   */
  _classifyActionType(actionText) {
    const text = actionText.toLowerCase()
    let bestMatch = { type: 'task', confidence: 0.5, urgency: 'medium', suggestedAgent: 'taskBuilderAgent' }

    for (const [type, config] of Object.entries(this.actionTypes)) {
      let confidence = 0

      // Check keywords
      const keywordMatches = config.keywords.filter(keyword => text.includes(keyword))
      confidence += keywordMatches.length * 0.2

      // Check patterns
      const patternMatches = config.patterns.filter(pattern => pattern.test(text))
      confidence += patternMatches.length * 0.3

      // Normalize confidence
      confidence = Math.min(confidence, 1.0)

      if (confidence > bestMatch.confidence) {
        bestMatch = {
          type,
          confidence,
          urgency: config.urgency,
          suggestedAgent: config.mcpAgent
        }
      }
    }

    return bestMatch
  }

  /**
   * Analyze meeting context for better understanding
   * @param {Object} action - The action object
   * @param {Object} meetingContext - Meeting context
   * @returns {Object} Context analysis
   */
  _analyzeContext(action, meetingContext) {
    const analysis = {
      projectReferences: [],
      clientReferences: [],
      teamReferences: [],
      deadlineReferences: [],
      budgetReferences: [],
      meetingPhase: 'discussion',
      relatedActions: [],
      historicalContext: {}
    }

    const fullText = `${action.extractedAction} ${action.originalText}`.toLowerCase()

    // Extract context references
    for (const [type, pattern] of Object.entries(this.contextPatterns)) {
      const matches = [...fullText.matchAll(pattern)]
      if (matches.length > 0) {
        analysis[type.replace('_reference', 'References')] = matches.map(m => m[1] || m[2]).filter(Boolean)
      }
    }

    // Determine meeting phase
    analysis.meetingPhase = this._determineMeetingPhase(fullText, meetingContext)

    // Find related actions in meeting history
    if (meetingContext.previousActions) {
      analysis.relatedActions = this._findRelatedActions(action, meetingContext.previousActions)
    }

    // Add historical context if available
    if (meetingContext.historicalMeetings) {
      analysis.historicalContext = this._analyzeHistoricalContext(action, meetingContext.historicalMeetings)
    }

    return analysis
  }

  /**
   * Analyze if intervention is needed
   * @param {Object} action - The action object
   * @param {Object} meetingContext - Meeting context
   * @returns {Object} Intervention analysis
   */
  _analyzeInterventionNeeds(action, meetingContext) {
    const intervention = {
      interventionNeeded: false,
      interventionType: null,
      interventionMessage: null,
      interventionConfidence: 0,
      interventionUrgency: 'low'
    }

    const text = action.extractedAction.toLowerCase()
    const entities = action.entities || {}

    // Check each intervention trigger
    for (const [triggerType, config] of Object.entries(this.interventionTriggers)) {
      let shouldTrigger = false
      let confidence = 0

      // Check pattern match
      if (config.pattern && config.pattern.test(text)) {
        confidence += 0.4
      }

      // Check specific conditions
      if (config.noAssignee && (!entities.assignee || entities.assigneeConfidence < 0.7)) {
        shouldTrigger = true
        confidence += 0.3
      }

      if (config.noDeadline && (!entities.dueDate || entities.dueDateConfidence < 0.7)) {
        shouldTrigger = true
        confidence += 0.3
      }

      if (config.vague && this._isVagueReference(text)) {
        shouldTrigger = true
        confidence += 0.2
      }

      if (config.hasDependency && this._hasDependencyIndicators(text)) {
        shouldTrigger = true
        confidence += 0.4
      }

      if (config.resourceIssue && this._hasResourceConcerns(text)) {
        shouldTrigger = true
        confidence += 0.4
      }

      // If trigger conditions are met and confidence is high enough
      if (shouldTrigger && confidence >= config.confidence) {
        if (confidence > intervention.interventionConfidence) {
          intervention.interventionNeeded = true
          intervention.interventionType = triggerType
          intervention.interventionMessage = config.question
          intervention.interventionConfidence = confidence
          intervention.interventionUrgency = confidence > 0.8 ? 'high' : 'medium'
        }
      }
    }

    return intervention
  }

  /**
   * Generate actionable recommendations
   * @param {Object} classification - The classification result
   * @returns {Array} Array of recommendations
   */
  _generateRecommendations(classification) {
    const recommendations = []
    const { action, type, contextAnalysis, interventionNeeded } = classification

    // Basic action recommendation
    recommendations.push({
      type: 'action',
      priority: 'high',
      message: `Crear ${type} usando ${classification.suggestedAgent}`,
      mcpCall: {
        agent: classification.suggestedAgent,
        action: 'create',
        payload: this._generateMCPPayload(classification)
      }
    })

    // Context-based recommendations
    if (contextAnalysis.projectReferences.length > 0) {
      recommendations.push({
        type: 'context',
        priority: 'medium',
        message: `Vincular con proyecto: ${contextAnalysis.projectReferences[0]}`,
        mcpCall: {
          agent: 'projectLinkerAgent',
          action: 'link',
          payload: { project: contextAnalysis.projectReferences[0] }
        }
      })
    }

    if (contextAnalysis.relatedActions.length > 0) {
      recommendations.push({
        type: 'dependency',
        priority: 'medium',
        message: `Considerar dependencias con acciones relacionadas`,
        mcpCall: {
          agent: 'dependencyManagerAgent',
          action: 'analyze',
          payload: { relatedActions: contextAnalysis.relatedActions }
        }
      })
    }

    // Intervention recommendations
    if (interventionNeeded) {
      recommendations.push({
        type: 'intervention',
        priority: 'high',
        message: classification.interventionMessage,
        mcpCall: {
          agent: 'meetingAssistantAgent',
          action: 'intervene',
          payload: {
            type: classification.interventionType,
            message: classification.interventionMessage
          }
        }
      })
    }

    return recommendations
  }

  /**
   * Determine current meeting phase
   * @param {string} text - Current text
   * @param {Object} context - Meeting context
   * @returns {string} Meeting phase
   */
  _determineMeetingPhase(text, context) {
    for (const [phase, indicators] of Object.entries(this.meetingStates)) {
      if (indicators.some(indicator => text.includes(indicator))) {
        return phase
      }
    }
    return 'discussion' // default
  }

  /**
   * Find related actions in meeting history
   * @param {Object} action - Current action
   * @param {Array} previousActions - Previous actions
   * @returns {Array} Related actions
   */
  _findRelatedActions(action, previousActions) {
    const related = []
    const actionText = action.extractedAction.toLowerCase()

    for (const prevAction of previousActions) {
      const prevText = prevAction.extractedAction.toLowerCase()
      
      // Simple similarity check (can be enhanced with NLP)
      const commonWords = this._findCommonWords(actionText, prevText)
      if (commonWords.length >= 2) {
        related.push({
          ...prevAction,
          similarity: commonWords.length / Math.max(actionText.split(' ').length, prevText.split(' ').length)
        })
      }
    }

    return related.sort((a, b) => b.similarity - a.similarity).slice(0, 3)
  }

  /**
   * Analyze historical context from previous meetings
   * @param {Object} action - Current action
   * @param {Array} historicalMeetings - Historical meetings
   * @returns {Object} Historical context
   */
  _analyzeHistoricalContext(action, historicalMeetings) {
    const context = {
      previousDiscussions: [],
      recurringTopics: [],
      unfinishedActions: []
    }

    // This would be enhanced with proper NLP and vector similarity
    // For now, simple keyword matching
    const actionKeywords = action.extractedAction.toLowerCase().split(' ')

    for (const meeting of historicalMeetings) {
      for (const prevAction of meeting.actions || []) {
        const prevKeywords = prevAction.extractedAction.toLowerCase().split(' ')
        const commonKeywords = actionKeywords.filter(word => prevKeywords.includes(word))
        
        if (commonKeywords.length >= 2) {
          context.previousDiscussions.push({
            meetingDate: meeting.date,
            action: prevAction,
            relevance: commonKeywords.length / actionKeywords.length
          })
        }
      }
    }

    return context
  }

  // Helper methods
  _isVagueReference(text) {
    const vagueWords = ['esto', 'eso', 'that', 'it', 'cosa', 'thing']
    return vagueWords.some(word => text.includes(word))
  }

  _hasDependencyIndicators(text) {
    const dependencyWords = ['depende', 'depends', 'necesita', 'requires', 'después', 'after']
    return dependencyWords.some(word => text.includes(word))
  }

  _hasResourceConcerns(text) {
    const resourceWords = ['no tenemos', "don't have", 'falta', 'missing', 'necesitamos', 'need']
    return resourceWords.some(word => text.includes(word))
  }

  _findCommonWords(text1, text2) {
    const words1 = text1.split(' ').filter(word => word.length > 3)
    const words2 = text2.split(' ').filter(word => word.length > 3)
    return words1.filter(word => words2.includes(word))
  }

  _generateMCPPayload(classification) {
    const { action, type, contextAnalysis } = classification
    
    return {
      type,
      title: action.extractedAction,
      assignee: action.entities?.assignee,
      dueDate: action.entities?.dueDate,
      priority: action.entities?.priority || 'medium',
      context: {
        source: 'meeting',
        speaker: action.speaker,
        timestamp: action.timestamp,
        meetingPhase: contextAnalysis.meetingPhase,
        projects: contextAnalysis.projectReferences,
        relatedActions: contextAnalysis.relatedActions.map(a => a.id)
      }
    }
  }

  /**
   * Batch classify multiple actions
   * @param {Array} actions - Array of actions
   * @param {Object} meetingContext - Meeting context
   * @returns {Array} Array of classifications
   */
  batchClassify(actions, meetingContext = {}) {
    return actions.map(action => this.classifyAction(action, meetingContext))
  }

  /**
   * Update meeting context with new classification
   * @param {Object} classification - New classification
   * @param {Object} meetingContext - Current context
   * @returns {Object} Updated context
   */
  updateMeetingContext(classification, meetingContext) {
    const updatedContext = { ...meetingContext }
    
    // Add to previous actions
    if (!updatedContext.previousActions) {
      updatedContext.previousActions = []
    }
    updatedContext.previousActions.push(classification.action)

    // Update meeting phase if detected
    if (classification.contextAnalysis.meetingPhase) {
      updatedContext.currentPhase = classification.contextAnalysis.meetingPhase
    }

    // Track intervention history
    if (classification.interventionNeeded) {
      if (!updatedContext.interventionHistory) {
        updatedContext.interventionHistory = []
      }
      updatedContext.interventionHistory.push({
        timestamp: new Date().toISOString(),
        type: classification.interventionType,
        message: classification.interventionMessage,
        confidence: classification.interventionConfidence
      })
    }

    return updatedContext
  }
}

module.exports = ClassificationEngine

