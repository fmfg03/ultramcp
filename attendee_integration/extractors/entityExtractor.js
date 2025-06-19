/**
 * Entity Extractor for Attendee Actions
 * Extracts and enriches entities from detected actions
 */

class EntityExtractor {
  constructor() {
    // Common names database (can be expanded)
    this.commonNames = [
      'francisco', 'maria', 'juan', 'ana', 'carlos', 'lucia', 'pedro', 'sofia',
      'miguel', 'carmen', 'jose', 'laura', 'antonio', 'elena', 'manuel', 'sara',
      'david', 'patricia', 'rafael', 'monica', 'alejandro', 'cristina',
      'john', 'mary', 'james', 'patricia', 'robert', 'jennifer', 'michael',
      'linda', 'william', 'elizabeth', 'david', 'barbara', 'richard', 'susan'
    ]

    // Department/role indicators
    this.departments = {
      'desarrollo': ['dev', 'developer', 'programador', 'tech', 'engineering'],
      'marketing': ['marketing', 'publicidad', 'social media', 'content'],
      'ventas': ['sales', 'ventas', 'comercial', 'business'],
      'finanzas': ['finance', 'finanzas', 'contabilidad', 'accounting'],
      'recursos humanos': ['hr', 'rrhh', 'recursos humanos', 'human resources'],
      'diseño': ['design', 'diseño', 'ui', 'ux', 'creative'],
      'operaciones': ['ops', 'operations', 'operaciones', 'logistics']
    }

    // Time expressions
    this.timeExpressions = {
      'today': { days: 0 },
      'hoy': { days: 0 },
      'tomorrow': { days: 1 },
      'mañana': { days: 1 },
      'pasado mañana': { days: 2 },
      'day after tomorrow': { days: 2 },
      'next week': { days: 7 },
      'próxima semana': { days: 7 },
      'next month': { days: 30 },
      'próximo mes': { days: 30 },
      'end of week': { days: this._daysUntilEndOfWeek() },
      'fin de semana': { days: this._daysUntilEndOfWeek() },
      'monday': { dayOfWeek: 1 },
      'lunes': { dayOfWeek: 1 },
      'tuesday': { dayOfWeek: 2 },
      'martes': { dayOfWeek: 2 },
      'wednesday': { dayOfWeek: 3 },
      'miércoles': { dayOfWeek: 3 },
      'thursday': { dayOfWeek: 4 },
      'jueves': { dayOfWeek: 4 },
      'friday': { dayOfWeek: 5 },
      'viernes': { dayOfWeek: 5 }
    }

    // Priority keywords
    this.priorityKeywords = {
      urgent: ['urgent', 'urgente', 'asap', 'crítico', 'critical', 'emergency', 'emergencia'],
      high: ['important', 'importante', 'priority', 'prioritario', 'high', 'alto'],
      medium: ['normal', 'regular', 'medium', 'medio', 'standard', 'estándar'],
      low: ['low', 'bajo', 'when possible', 'cuando puedas', 'sin prisa', 'no rush']
    }

    // Object/deliverable types
    this.objectTypes = {
      document: ['documento', 'document', 'reporte', 'report', 'informe', 'presentación', 'presentation', 'propuesta', 'proposal'],
      code: ['código', 'code', 'script', 'programa', 'program', 'app', 'aplicación', 'website', 'web'],
      meeting: ['reunión', 'meeting', 'junta', 'call', 'llamada', 'conference', 'conferencia'],
      task: ['tarea', 'task', 'trabajo', 'work', 'actividad', 'activity'],
      event: ['evento', 'event', 'cita', 'appointment', 'deadline', 'fecha límite']
    }
  }

  /**
   * Extract and enrich entities from an action
   * @param {Object} action - The action object
   * @param {string} fullTranscript - Full transcript context
   * @returns {Object} Enriched action with detailed entities
   */
  enrichAction(action, fullTranscript = '') {
    const enrichedAction = { ...action }
    
    // Enhance existing entities
    enrichedAction.entities = {
      ...action.entities,
      ...this._extractAssignee(action.extractedAction, action.speaker, fullTranscript),
      ...this._extractTemporal(action.extractedAction, fullTranscript),
      ...this._extractPriority(action.extractedAction, fullTranscript),
      ...this._extractObject(action.extractedAction),
      ...this._extractContext(action.extractedAction, fullTranscript),
      ...this._extractDependencies(action.extractedAction, fullTranscript)
    }

    // Add confidence scoring
    enrichedAction.entityConfidence = this._calculateEntityConfidence(enrichedAction.entities)
    
    // Add suggested MCP agent
    enrichedAction.suggestedAgent = this._suggestMCPAgent(enrichedAction)

    return enrichedAction
  }

  /**
   * Extract assignee information
   * @param {string} actionText - Action text
   * @param {string} speaker - Original speaker
   * @param {string} context - Full context
   * @returns {Object} Assignee information
   */
  _extractAssignee(actionText, speaker, context) {
    const assigneeInfo = {
      assignee: null,
      assigneeType: 'unknown', // person, team, department, self
      assigneeConfidence: 0
    }

    const text = actionText.toLowerCase()

    // Check for explicit name mentions
    const nameMatches = this._findNames(text)
    if (nameMatches.length > 0) {
      assigneeInfo.assignee = nameMatches[0]
      assigneeInfo.assigneeType = 'person'
      assigneeInfo.assigneeConfidence = 0.9
      return assigneeInfo
    }

    // Check for pronouns and implicit assignment
    if (text.includes('yo ') || text.includes('i ') || text.includes('me ')) {
      assigneeInfo.assignee = speaker
      assigneeInfo.assigneeType = 'self'
      assigneeInfo.assigneeConfidence = 0.8
    } else if (text.includes('tú ') || text.includes('you ') || text.includes('te ')) {
      // Need more context to determine who "you" refers to
      assigneeInfo.assigneeType = 'person'
      assigneeInfo.assigneeConfidence = 0.6
    } else if (text.includes('nosotros') || text.includes('we ') || text.includes('equipo')) {
      assigneeInfo.assigneeType = 'team'
      assigneeInfo.assigneeConfidence = 0.7
    }

    // Check for department mentions
    const department = this._findDepartment(text)
    if (department) {
      assigneeInfo.assignee = department
      assigneeInfo.assigneeType = 'department'
      assigneeInfo.assigneeConfidence = 0.8
    }

    return assigneeInfo
  }

  /**
   * Extract temporal information
   * @param {string} actionText - Action text
   * @param {string} context - Full context
   * @returns {Object} Temporal information
   */
  _extractTemporal(actionText, context) {
    const temporalInfo = {
      dueDate: null,
      dueDateConfidence: 0,
      timeframe: null,
      isDeadline: false
    }

    const fullText = `${actionText} ${context}`.toLowerCase()

    // Check for explicit dates (YYYY-MM-DD, DD/MM/YYYY, etc.)
    const datePattern = /(\d{4}-\d{2}-\d{2}|\d{1,2}\/\d{1,2}\/\d{4}|\d{1,2}-\d{1,2}-\d{4})/
    const dateMatch = fullText.match(datePattern)
    if (dateMatch) {
      temporalInfo.dueDate = this._parseDate(dateMatch[1])
      temporalInfo.dueDateConfidence = 0.95
      temporalInfo.isDeadline = true
      return temporalInfo
    }

    // Check for relative time expressions
    for (const [expression, timeData] of Object.entries(this.timeExpressions)) {
      if (fullText.includes(expression)) {
        temporalInfo.dueDate = this._calculateDate(timeData)
        temporalInfo.dueDateConfidence = 0.8
        temporalInfo.timeframe = expression
        
        // Check if it's a deadline
        if (fullText.includes('antes del') || fullText.includes('before') || 
            fullText.includes('deadline') || fullText.includes('fecha límite')) {
          temporalInfo.isDeadline = true
        }
        break
      }
    }

    // Check for time of day
    const timePattern = /(\d{1,2}):(\d{2})\s*(am|pm|a\.m\.|p\.m\.)?/i
    const timeMatch = fullText.match(timePattern)
    if (timeMatch && temporalInfo.dueDate) {
      const hour = parseInt(timeMatch[1])
      const minute = parseInt(timeMatch[2])
      const isPM = timeMatch[3] && timeMatch[3].toLowerCase().includes('p')
      
      const date = new Date(temporalInfo.dueDate)
      date.setHours(isPM && hour !== 12 ? hour + 12 : hour, minute, 0, 0)
      temporalInfo.dueDate = date.toISOString()
    }

    return temporalInfo
  }

  /**
   * Extract priority information
   * @param {string} actionText - Action text
   * @param {string} context - Full context
   * @returns {Object} Priority information
   */
  _extractPriority(actionText, context) {
    const priorityInfo = {
      priority: 'medium',
      priorityConfidence: 0.5,
      priorityReason: null
    }

    const fullText = `${actionText} ${context}`.toLowerCase()

    for (const [priority, keywords] of Object.entries(this.priorityKeywords)) {
      for (const keyword of keywords) {
        if (fullText.includes(keyword)) {
          priorityInfo.priority = priority
          priorityInfo.priorityConfidence = 0.9
          priorityInfo.priorityReason = keyword
          return priorityInfo
        }
      }
    }

    // Infer priority from context
    if (fullText.includes('asap') || fullText.includes('ya') || fullText.includes('now')) {
      priorityInfo.priority = 'urgent'
      priorityInfo.priorityConfidence = 0.8
      priorityInfo.priorityReason = 'temporal urgency'
    } else if (fullText.includes('cuando puedas') || fullText.includes('when you can')) {
      priorityInfo.priority = 'low'
      priorityInfo.priorityConfidence = 0.7
      priorityInfo.priorityReason = 'flexible timing'
    }

    return priorityInfo
  }

  /**
   * Extract object/deliverable information
   * @param {string} actionText - Action text
   * @returns {Object} Object information
   */
  _extractObject(actionText) {
    const objectInfo = {
      object: null,
      objectType: null,
      objectConfidence: 0,
      deliverables: []
    }

    const text = actionText.toLowerCase()

    // Find object types
    for (const [type, keywords] of Object.entries(this.objectTypes)) {
      for (const keyword of keywords) {
        if (text.includes(keyword)) {
          objectInfo.object = keyword
          objectInfo.objectType = type
          objectInfo.objectConfidence = 0.8
          objectInfo.deliverables.push(keyword)
          break
        }
      }
      if (objectInfo.object) break
    }

    // Extract specific deliverable names
    const deliverablePattern = /(reporte|informe|documento|presentación|código|app|website)\s+([a-zA-Z\s]+)/gi
    let match = deliverablePattern.exec(text)
    while (match) {
      objectInfo.deliverables.push(match[0].trim())
      match = deliverablePattern.exec(text)
    }

    return objectInfo
  }

  /**
   * Extract context information
   * @param {string} actionText - Action text
   * @param {string} fullContext - Full context
   * @returns {Object} Context information
   */
  _extractContext(actionText, fullContext) {
    const contextInfo = {
      project: null,
      client: null,
      meeting: null,
      tags: [],
      relatedTopics: []
    }

    const text = `${actionText} ${fullContext}`.toLowerCase()

    // Extract project mentions
    const projectPattern = /proyecto\s+([a-zA-Z\s]+)/gi
    const projectMatch = text.match(projectPattern)
    if (projectMatch) {
      contextInfo.project = projectMatch[0].replace('proyecto', '').trim()
    }

    // Extract client mentions
    const clientPattern = /cliente\s+([a-zA-Z\s]+)/gi
    const clientMatch = text.match(clientPattern)
    if (clientMatch) {
      contextInfo.client = clientMatch[0].replace('cliente', '').trim()
    }

    // Extract tags from common business terms
    const businessTerms = ['budget', 'presupuesto', 'deadline', 'milestone', 'launch', 'lanzamiento', 'review', 'revisión']
    for (const term of businessTerms) {
      if (text.includes(term)) {
        contextInfo.tags.push(term)
      }
    }

    return contextInfo
  }

  /**
   * Extract dependencies
   * @param {string} actionText - Action text
   * @param {string} context - Full context
   * @returns {Object} Dependencies information
   */
  _extractDependencies(actionText, context) {
    const dependencyInfo = {
      dependencies: [],
      blockers: [],
      prerequisites: []
    }

    const text = `${actionText} ${context}`.toLowerCase()

    // Look for dependency indicators
    if (text.includes('después de') || text.includes('after')) {
      dependencyInfo.dependencies.push('sequential_dependency')
    }

    if (text.includes('necesita') || text.includes('requires') || text.includes('depende')) {
      dependencyInfo.prerequisites.push('requirement_dependency')
    }

    if (text.includes('bloqueado') || text.includes('blocked') || text.includes('esperando')) {
      dependencyInfo.blockers.push('external_blocker')
    }

    return dependencyInfo
  }

  /**
   * Calculate confidence score for extracted entities
   * @param {Object} entities - Extracted entities
   * @returns {number} Overall confidence score
   */
  _calculateEntityConfidence(entities) {
    const scores = []
    
    if (entities.assigneeConfidence) scores.push(entities.assigneeConfidence)
    if (entities.dueDateConfidence) scores.push(entities.dueDateConfidence)
    if (entities.priorityConfidence) scores.push(entities.priorityConfidence)
    if (entities.objectConfidence) scores.push(entities.objectConfidence)

    return scores.length > 0 ? scores.reduce((a, b) => a + b) / scores.length : 0.5
  }

  /**
   * Suggest appropriate MCP agent based on action type and entities
   * @param {Object} action - Enriched action
   * @returns {string} Suggested MCP agent
   */
  _suggestMCPAgent(action) {
    const { type, entities } = action

    // Calendar events
    if (type === 'calendar' || entities.objectType === 'meeting') {
      return 'calendarAgent'
    }

    // Reminders and notifications
    if (type === 'reminder' || action.extractedAction.includes('recordar')) {
      return 'notifierAgent'
    }

    // Code/development tasks
    if (entities.objectType === 'code' || entities.object?.includes('código')) {
      return 'codeBuilderAgent'
    }

    // Document creation
    if (entities.objectType === 'document') {
      return 'documentBuilderAgent'
    }

    // Default to task builder
    return 'taskBuilderAgent'
  }

  // Helper methods
  _findNames(text) {
    return this.commonNames.filter(name => text.includes(name))
  }

  _findDepartment(text) {
    for (const [dept, keywords] of Object.entries(this.departments)) {
      if (keywords.some(keyword => text.includes(keyword))) {
        return dept
      }
    }
    return null
  }

  _daysUntilEndOfWeek() {
    const today = new Date()
    const dayOfWeek = today.getDay()
    return dayOfWeek === 0 ? 0 : 7 - dayOfWeek // Sunday = 0
  }

  _parseDate(dateString) {
    return new Date(dateString).toISOString()
  }

  _calculateDate(timeData) {
    const now = new Date()
    
    if (timeData.days !== undefined) {
      const targetDate = new Date(now)
      targetDate.setDate(now.getDate() + timeData.days)
      return targetDate.toISOString()
    }
    
    if (timeData.dayOfWeek !== undefined) {
      const targetDate = new Date(now)
      const daysUntilTarget = (timeData.dayOfWeek - now.getDay() + 7) % 7
      targetDate.setDate(now.getDate() + (daysUntilTarget === 0 ? 7 : daysUntilTarget))
      return targetDate.toISOString()
    }
    
    return now.toISOString()
  }

  /**
   * Batch enrich multiple actions
   * @param {Array} actions - Array of actions
   * @param {string} fullTranscript - Full transcript context
   * @returns {Array} Enriched actions
   */
  batchEnrich(actions, fullTranscript = '') {
    return actions.map(action => this.enrichAction(action, fullTranscript))
  }
}

module.exports = EntityExtractor

