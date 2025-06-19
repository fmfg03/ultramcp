/**
 * Action Extractor for Attendee Transcriptions
 * Detects action patterns in meeting transcripts
 */

class ActionExtractor {
  constructor() {
    // Action verbs that indicate tasks or decisions
    this.actionVerbs = [
      // Task verbs
      'hacer', 'crear', 'generar', 'desarrollar', 'implementar', 'construir',
      'escribir', 'enviar', 'llamar', 'contactar', 'revisar', 'analizar',
      'preparar', 'organizar', 'planificar', 'coordinar', 'gestionar',
      'actualizar', 'modificar', 'corregir', 'mejorar', 'optimizar',
      
      // Decision verbs  
      'acordar', 'decidir', 'aprobar', 'rechazar', 'confirmar', 'establecer',
      'definir', 'determinar', 'fijar', 'asignar', 'delegar',
      
      // Follow-up verbs
      'seguir', 'monitorear', 'supervisar', 'verificar', 'comprobar',
      'recordar', 'agendar', 'programar', 'planear',
      
      // English equivalents
      'do', 'make', 'create', 'generate', 'develop', 'implement', 'build',
      'write', 'send', 'call', 'contact', 'review', 'analyze', 'prepare',
      'organize', 'plan', 'coordinate', 'manage', 'update', 'modify',
      'agree', 'decide', 'approve', 'reject', 'confirm', 'establish',
      'follow', 'monitor', 'supervise', 'verify', 'check', 'remember',
      'schedule', 'program'
    ]

    // Temporal indicators
    this.timeIndicators = [
      'antes del', 'después del', 'para el', 'hasta el', 'en',
      'mañana', 'hoy', 'ayer', 'próxima semana', 'próximo mes',
      'esta semana', 'este mes', 'fin de semana', 'lunes', 'martes',
      'miércoles', 'jueves', 'viernes', 'sábado', 'domingo',
      'before', 'after', 'by', 'until', 'on', 'tomorrow', 'today',
      'yesterday', 'next week', 'next month', 'this week', 'this month'
    ]

    // Priority indicators
    this.priorityIndicators = {
      high: ['urgente', 'crítico', 'importante', 'prioritario', 'asap', 'urgent', 'critical', 'important', 'priority'],
      medium: ['normal', 'regular', 'estándar', 'medium', 'standard'],
      low: ['cuando puedas', 'sin prisa', 'low priority', 'when possible']
    }
  }

  /**
   * Extract actions from a transcript utterance
   * @param {Object} utterance - The utterance object
   * @returns {Array} Array of detected actions
   */
  extractActions(utterance) {
    const { speaker, text, timestamp } = utterance
    const actions = []

    // Normalize text for analysis
    const normalizedText = text.toLowerCase().trim()
    
    // Skip if text is too short or doesn't contain action indicators
    if (normalizedText.length < 10) {
      return actions
    }

    // Check for action verbs
    const hasActionVerb = this.actionVerbs.some(verb => 
      normalizedText.includes(verb)
    )

    if (!hasActionVerb) {
      return actions
    }

    // Extract potential actions using patterns
    const actionPatterns = this._extractActionPatterns(normalizedText)
    
    for (const pattern of actionPatterns) {
      const action = {
        id: this._generateActionId(utterance, pattern),
        source: 'attendee',
        timestamp,
        speaker,
        originalText: text,
        extractedAction: pattern.action,
        confidence: pattern.confidence,
        type: this._classifyActionType(pattern.action),
        entities: this._extractBasicEntities(pattern.action, normalizedText)
      }

      actions.push(action)
    }

    return actions
  }

  /**
   * Extract action patterns from normalized text
   * @param {string} text - Normalized text
   * @returns {Array} Array of action patterns
   */
  _extractActionPatterns(text) {
    const patterns = []

    // Pattern 1: "hay que [action]"
    const hayQuePattern = /hay que ([^.!?]+)/gi
    let match = hayQuePattern.exec(text)
    while (match) {
      patterns.push({
        action: match[1].trim(),
        confidence: 0.9,
        pattern: 'hay_que'
      })
      match = hayQuePattern.exec(text)
    }

    // Pattern 2: "[person] + action verb"
    const personActionPattern = /(\w+),?\s+(tiene que|debe|va a|necesita)\s+([^.!?]+)/gi
    match = personActionPattern.exec(text)
    while (match) {
      patterns.push({
        action: `${match[1]} ${match[2]} ${match[3]}`.trim(),
        confidence: 0.85,
        pattern: 'person_action',
        assignee: match[1]
      })
      match = personActionPattern.exec(text)
    }

    // Pattern 3: Imperative actions
    const imperativePattern = /(crear|generar|hacer|enviar|llamar|contactar|revisar|preparar)\s+([^.!?]+)/gi
    match = imperativePattern.exec(text)
    while (match) {
      patterns.push({
        action: `${match[1]} ${match[2]}`.trim(),
        confidence: 0.8,
        pattern: 'imperative'
      })
      match = imperativePattern.exec(text)
    }

    // Pattern 4: "vamos a [action]"
    const vamosPattern = /vamos a ([^.!?]+)/gi
    match = vamosPattern.exec(text)
    while (match) {
      patterns.push({
        action: match[1].trim(),
        confidence: 0.75,
        pattern: 'vamos_a'
      })
      match = vamosPattern.exec(text)
    }

    // Pattern 5: "se acordó [decision]"
    const decisionPattern = /(se acordó|se decidió|se estableció|se confirmó)\s+([^.!?]+)/gi
    match = decisionPattern.exec(text)
    while (match) {
      patterns.push({
        action: match[2].trim(),
        confidence: 0.9,
        pattern: 'decision',
        type: 'decision'
      })
      match = decisionPattern.exec(text)
    }

    return patterns
  }

  /**
   * Classify the type of action
   * @param {string} actionText - The action text
   * @returns {string} Action type
   */
  _classifyActionType(actionText) {
    const text = actionText.toLowerCase()

    // Decision indicators
    if (text.includes('acordó') || text.includes('decidió') || text.includes('estableció')) {
      return 'decision'
    }

    // Calendar/meeting indicators
    if (text.includes('reunión') || text.includes('meeting') || text.includes('agendar') || 
        text.includes('schedule') || text.includes('cita')) {
      return 'calendar'
    }

    // Reminder indicators
    if (text.includes('recordar') || text.includes('reminder') || text.includes('avisar')) {
      return 'reminder'
    }

    // Follow-up indicators
    if (text.includes('seguimiento') || text.includes('follow') || text.includes('revisar')) {
      return 'follow-up'
    }

    // Default to task
    return 'task'
  }

  /**
   * Extract basic entities from action text
   * @param {string} actionText - The action text
   * @param {string} fullText - Full utterance text
   * @returns {Object} Extracted entities
   */
  _extractBasicEntities(actionText, fullText) {
    const entities = {
      assignee: null,
      dueDate: null,
      priority: 'medium',
      object: null,
      context: null
    }

    // Extract assignee (simple name detection)
    const namePattern = /\b([A-Z][a-z]+)\b/g
    const names = actionText.match(namePattern)
    if (names && names.length > 0) {
      entities.assignee = names[0]
    }

    // Extract temporal information
    const timeMatch = this.timeIndicators.find(indicator => 
      fullText.includes(indicator)
    )
    if (timeMatch) {
      entities.dueDate = this._parseTemporalExpression(fullText, timeMatch)
    }

    // Extract priority
    for (const [priority, indicators] of Object.entries(this.priorityIndicators)) {
      if (indicators.some(indicator => fullText.includes(indicator))) {
        entities.priority = priority
        break
      }
    }

    // Extract object (what needs to be done)
    const objectPattern = /(reporte|informe|documento|presentación|código|website|app|sistema)/gi
    const objectMatch = actionText.match(objectPattern)
    if (objectMatch) {
      entities.object = objectMatch[0]
    }

    return entities
  }

  /**
   * Parse temporal expressions into dates
   * @param {string} text - Full text
   * @param {string} indicator - Time indicator found
   * @returns {string|null} Parsed date or null
   */
  _parseTemporalExpression(text, indicator) {
    const now = new Date()
    
    if (indicator.includes('mañana') || indicator.includes('tomorrow')) {
      const tomorrow = new Date(now)
      tomorrow.setDate(now.getDate() + 1)
      return tomorrow.toISOString().split('T')[0]
    }

    if (indicator.includes('viernes') || indicator.includes('friday')) {
      const friday = new Date(now)
      const daysUntilFriday = (5 - now.getDay() + 7) % 7
      friday.setDate(now.getDate() + daysUntilFriday)
      return friday.toISOString().split('T')[0]
    }

    if (indicator.includes('próxima semana') || indicator.includes('next week')) {
      const nextWeek = new Date(now)
      nextWeek.setDate(now.getDate() + 7)
      return nextWeek.toISOString().split('T')[0]
    }

    // Add more temporal parsing as needed
    return null
  }

  /**
   * Generate unique action ID
   * @param {Object} utterance - Original utterance
   * @param {Object} pattern - Extracted pattern
   * @returns {string} Unique action ID
   */
  _generateActionId(utterance, pattern) {
    const timestamp = new Date(utterance.timestamp).getTime()
    const hash = this._simpleHash(pattern.action)
    return `action_${timestamp}_${hash}`
  }

  /**
   * Simple hash function for generating IDs
   * @param {string} str - String to hash
   * @returns {string} Hash
   */
  _simpleHash(str) {
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(36)
  }

  /**
   * Batch process multiple utterances
   * @param {Array} utterances - Array of utterances
   * @returns {Array} All extracted actions
   */
  batchExtract(utterances) {
    const allActions = []
    
    for (const utterance of utterances) {
      const actions = this.extractActions(utterance)
      allActions.push(...actions)
    }

    return allActions
  }
}

module.exports = ActionExtractor

