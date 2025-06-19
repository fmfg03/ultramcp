/**
 * Enhanced Local LLM Adapter with Langwatch Integration
 * 
 * Adaptador universal para modelos LLM locales (Mistral, LLaMA, DeepSeek)
 * con integración completa de Langwatch para tracking de métricas,
 * scores simulados y contradicción explícita
 * 
 * @module enhancedLocalLLMAdapter
 */

import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import logger from '../backend/src/utils/logger.js';
import { LocalLLMWrapperFactory, withLocalLangwatch } from '../backend/src/services/localLLMWrappers.js';
import { enhancedLangwatchMiddleware } from '../backend/src/middleware/enhancedLangwatchMiddleware.js';
import { contradictionService, detectContradiction, generateContradictionPrompt } from '../backend/src/services/contradictionService.js';

/**
 * Configuración de modelos locales con Langwatch
 */
const ENHANCED_LOCAL_MODELS_CONFIG = {
  'mistral-local': {
    scriptPath: 'scripts/run_local_mistral.py',
    modelPath: 'models/mistral.gguf',
    displayName: 'Mistral Local',
    maxTokens: 512,
    temperature: 0.7,
    description: 'Modelo Mistral local optimizado para tareas generales y razonamiento',
    langwatch: {
      enabled: true,
      modelName: 'mistral-local',
      provider: 'local',
      tags: ['local', 'mistral', 'general', 'reasoning']
    }
  },
  'llama-local': {
    scriptPath: 'scripts/run_local_llama.py',
    modelPath: 'models/llama.gguf',
    displayName: 'LLaMA Local',
    maxTokens: 512,
    temperature: 0.7,
    description: 'Modelo LLaMA local potente para comprensión y generación de texto',
    langwatch: {
      enabled: true,
      modelName: 'llama-local',
      provider: 'local',
      tags: ['local', 'llama', 'comprehension', 'generation']
    }
  },
  'deepseek-local': {
    scriptPath: 'scripts/run_local_deepseek.py',
    modelPath: 'models/deepseek.gguf',
    displayName: 'DeepSeek Local',
    maxTokens: 512,
    temperature: 0.3,
    description: 'Modelo DeepSeek local especializado en matemáticas y lógica compleja',
    langwatch: {
      enabled: true,
      modelName: 'deepseek-local',
      provider: 'local',
      tags: ['local', 'deepseek', 'mathematics', 'logic']
    }
  }
};

/**
 * Configuración por defecto para fallbacks
 */
const DEFAULT_CONFIG = {
  maxTokens: 512,
  temperature: 0.7,
  timeout: 30000, // 30 segundos
  encoding: 'utf-8',
  langwatch: {
    enabled: true,
    trackContradiction: true,
    trackMetrics: true,
    simulateScores: true
  }
};

/**
 * Clase principal del adaptador de LLMs locales con Langwatch
 */
export class EnhancedLocalLLMAdapter {
  constructor() {
    this.modelsConfig = ENHANCED_LOCAL_MODELS_CONFIG;
    this.projectRoot = process.cwd();
    this.isInitialized = false;
    this.langwatchWrappers = {};
    this.sessionHistory = new Map();
  }
  
  /**
   * Inicializa el adaptador con Langwatch
   */
  async initialize() {
    try {
      logger.info('🔧 Inicializando Enhanced LocalLLMAdapter con Langwatch...');
      
      // Verificar directorios
      const requiredDirs = ['scripts', 'models'];
      for (const dir of requiredDirs) {
        const dirPath = path.join(this.projectRoot, dir);
        if (!fs.existsSync(dirPath)) {
          fs.mkdirSync(dirPath, { recursive: true });
          logger.info(`📁 Directorio creado: ${dir}`);
        }
      }
      
      // Inicializar wrappers de Langwatch
      await this.initializeLangwatchWrappers();
      
      // Verificar disponibilidad de modelos
      const availableModels = await this.checkAvailableModels();
      logger.info('📊 Modelos disponibles:', availableModels);
      
      this.isInitialized = true;
      logger.info('✅ Enhanced LocalLLMAdapter inicializado exitosamente');
      
      return {
        success: true,
        availableModels,
        totalModels: Object.keys(this.modelsConfig).length,
        langwatchEnabled: true
      };
      
    } catch (error) {
      logger.error('❌ Error inicializando Enhanced LocalLLMAdapter:', error);
      throw error;
    }
  }
  
  /**
   * Inicializa wrappers de Langwatch para cada modelo
   */
  async initializeLangwatchWrappers() {
    try {
      for (const modelType of Object.keys(this.modelsConfig)) {
        this.langwatchWrappers[modelType] = LocalLLMWrapperFactory.createWrapper(modelType);
        logger.info(`🔍 Wrapper Langwatch inicializado para ${modelType}`);
      }
    } catch (error) {
      logger.error('Error inicializando wrappers Langwatch:', error);
      throw error;
    }
  }
  
  /**
   * Llama a un modelo local con tracking completo de Langwatch
   */
  async callLocalModelWithLangwatch(modelType, prompt, options = {}) {
    try {
      if (!this.isInitialized) {
        await this.initialize();
      }
      
      const startTime = Date.now();
      const sessionId = options.sessionId || `enhanced_${Date.now()}`;
      
      logger.info(`🤖 Llamando modelo local con Langwatch: ${modelType}`);
      
      // Validar modelo
      const modelConfig = this.modelsConfig[modelType];
      if (!modelConfig) {
        throw new Error(`Modelo no soportado: ${modelType}`);
      }
      
      // Verificar disponibilidad
      const availability = await this.checkModelAvailability(modelType);
      if (!availability.available) {
        throw new Error(`Modelo no disponible: ${availability.reason}`);
      }
      
      // Obtener historial de la sesión
      const sessionHistory = this.getSessionHistory(sessionId);
      const currentAttempt = sessionHistory.length + 1;
      
      // Detectar si aplicar contradicción explícita
      const contradictionAnalysis = detectContradiction(
        sessionId,
        currentAttempt,
        sessionHistory
      );
      
      let finalPrompt = prompt;
      let contradictionApplied = false;
      
      // Aplicar contradicción si es necesario
      if (contradictionAnalysis.shouldApply) {
        const contradictionPrompt = generateContradictionPrompt(
          prompt,
          modelType,
          contradictionAnalysis.intensity,
          sessionHistory
        );
        
        finalPrompt = contradictionPrompt.prompt;
        contradictionApplied = true;
        
        logger.info(`🔥 Contradicción ${contradictionAnalysis.intensity} aplicada para ${modelType}`);
      }
      
      // Preparar parámetros para el modelo
      const params = {
        prompt: finalPrompt,
        maxTokens: options.maxTokens || modelConfig.maxTokens || DEFAULT_CONFIG.maxTokens,
        temperature: options.temperature || modelConfig.temperature || DEFAULT_CONFIG.temperature,
        sessionId,
        modelPath: path.join(this.projectRoot, modelConfig.modelPath),
        contradictionApplied,
        attemptNumber: currentAttempt,
        ...options
      };
      
      // Función para ejecutar el modelo
      const executeModel = async (prompt, opts) => {
        return await this.executePythonScript(modelConfig.scriptPath, {
          ...params,
          prompt
        });
      };
      
      // Ejecutar con wrapper de Langwatch
      const wrapper = this.langwatchWrappers[modelType];
      const result = await wrapper.withLangwatch(executeModel, finalPrompt, {
        sessionId,
        modelType,
        previousAttempts: sessionHistory,
        contradictionApplied,
        contradictionIntensity: contradictionAnalysis.intensity,
        tags: [...(modelConfig.langwatch.tags || []), ...(options.tags || [])]
      });
      
      const duration = Date.now() - startTime;
      
      // Procesar respuesta con metadata completa
      const enhancedResponse = {
        success: true,
        modelType,
        displayName: modelConfig.displayName,
        response: result.response,
        tokenUsage: result.tokenUsage,
        metadata: {
          ...result.metadata,
          duration,
          sessionId,
          attemptNumber: currentAttempt,
          contradictionApplied,
          contradictionAnalysis: contradictionApplied ? contradictionAnalysis : null,
          langwatchTracking: result.langwatch
        }
      };
      
      // Evaluar efectividad de contradicción si se aplicó
      if (contradictionApplied && sessionHistory.length > 0) {
        const previousScore = sessionHistory[sessionHistory.length - 1]?.langwatch?.score || 0;
        const effectivenessAnalysis = contradictionService.evaluateContradictionEffectiveness(
          sessionId,
          {
            intensity: contradictionAnalysis.intensity,
            previousScore
          },
          {
            score: result.langwatch.score
          }
        );
        
        enhancedResponse.metadata.contradictionEffectiveness = effectivenessAnalysis;
      }
      
      // Guardar en historial de sesión
      this.saveToSessionHistory(sessionId, enhancedResponse);
      
      logger.info(`✅ Modelo ${modelType} respondió con Langwatch en ${duration}ms - Score: ${result.langwatch.score?.toFixed(3)}`);
      
      return enhancedResponse;
      
    } catch (error) {
      logger.error(`❌ Error en modelo ${modelType} con Langwatch:`, error);
      
      // Tracking de error en Langwatch
      await enhancedLangwatchMiddleware.trackLocalModelError({
        sessionId: options.sessionId || 'unknown',
        modelName: modelType,
        prompt,
        error: error.message,
        duration: Date.now() - (options.startTime || Date.now())
      });
      
      return {
        success: false,
        modelType,
        error: error.message,
        fallbackUsed: false,
        metadata: {
          duration: Date.now() - (options.startTime || Date.now()),
          timestamp: new Date().toISOString(),
          langwatchTracked: true
        }
      };
    }
  }
  
  /**
   * Verifica disponibilidad de modelos
   */
  async checkAvailableModels() {
    const available = {};
    
    for (const [modelType, config] of Object.entries(this.modelsConfig)) {
      const modelPath = path.join(this.projectRoot, config.modelPath);
      const scriptPath = path.join(this.projectRoot, config.scriptPath);
      
      available[modelType] = {
        modelExists: fs.existsSync(modelPath),
        scriptExists: fs.existsSync(scriptPath),
        modelPath: config.modelPath,
        scriptPath: config.scriptPath,
        displayName: config.displayName,
        description: config.description,
        langwatchEnabled: config.langwatch.enabled
      };
    }
    
    return available;
  }
  
  /**
   * Verifica si un modelo específico está disponible
   */
  async checkModelAvailability(modelType) {
    const config = this.modelsConfig[modelType];
    if (!config) {
      return { available: false, reason: 'Modelo no configurado' };
    }
    
    const modelPath = path.join(this.projectRoot, config.modelPath);
    const scriptPath = path.join(this.projectRoot, config.scriptPath);
    
    if (!fs.existsSync(scriptPath)) {
      return { available: false, reason: 'Script Python no encontrado' };
    }
    
    if (!fs.existsSync(modelPath)) {
      return { available: false, reason: 'Archivo de modelo .gguf no encontrado' };
    }
    
    return { available: true, reason: 'Modelo disponible' };
  }
  
  /**
   * Ejecuta un script Python con parámetros
   */
  async executePythonScript(scriptPath, params) {
    return new Promise((resolve, reject) => {
      const fullScriptPath = path.join(this.projectRoot, scriptPath);
      
      // Preparar argumentos como JSON
      const jsonParams = JSON.stringify(params);
      
      logger.info(`🐍 Ejecutando: python3 ${scriptPath}`);
      
      const pythonProcess = spawn('python3', [fullScriptPath], {
        cwd: this.projectRoot,
        stdio: ['pipe', 'pipe', 'pipe']
      });
      
      let stdout = '';
      let stderr = '';
      
      // Enviar parámetros como JSON al stdin
      pythonProcess.stdin.write(jsonParams);
      pythonProcess.stdin.end();
      
      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });
      
      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });
      
      // Timeout
      const timeout = setTimeout(() => {
        pythonProcess.kill('SIGTERM');
        reject(new Error(`Timeout ejecutando ${scriptPath}`));
      }, DEFAULT_CONFIG.timeout);
      
      pythonProcess.on('close', (code) => {
        clearTimeout(timeout);
        
        if (code !== 0) {
          logger.error(`❌ Script Python falló con código ${code}:`, stderr);
          reject(new Error(`Script falló: ${stderr}`));
          return;
        }
        
        try {
          // Parsear respuesta JSON
          const result = JSON.parse(stdout.trim());
          resolve(result);
        } catch (parseError) {
          logger.error('❌ Error parseando respuesta JSON:', parseError);
          logger.error('Raw stdout:', stdout);
          reject(new Error(`Error parseando respuesta: ${parseError.message}`));
        }
      });
      
      pythonProcess.on('error', (error) => {
        clearTimeout(timeout);
        logger.error('❌ Error ejecutando script Python:', error);
        reject(error);
      });
    });
  }
  
  /**
   * Guarda resultado en historial de sesión
   */
  saveToSessionHistory(sessionId, result) {
    if (!this.sessionHistory.has(sessionId)) {
      this.sessionHistory.set(sessionId, []);
    }
    
    this.sessionHistory.get(sessionId).push({
      timestamp: Date.now(),
      attemptNumber: result.metadata.attemptNumber,
      modelType: result.modelType,
      score: result.metadata.langwatchTracking?.score,
      contradictionApplied: result.metadata.contradictionApplied,
      response: result.response,
      tokenUsage: result.tokenUsage,
      duration: result.metadata.duration,
      langwatch: result.metadata.langwatchTracking
    });
  }
  
  /**
   * Obtiene historial de sesión
   */
  getSessionHistory(sessionId) {
    return this.sessionHistory.get(sessionId) || [];
  }
  
  /**
   * Detecta automáticamente el mejor modelo para una tarea
   */
  detectBestModel(prompt, taskType = 'general') {
    const promptLower = prompt.toLowerCase();
    
    // Lógica de detección basada en contenido
    if (promptLower.includes('matemática') || 
        promptLower.includes('cálculo') || 
        promptLower.includes('ecuación') ||
        promptLower.includes('paradoja') ||
        taskType === 'math') {
      return 'deepseek-local';
    }
    
    if (promptLower.includes('código') || 
        promptLower.includes('programación') || 
        promptLower.includes('script') ||
        taskType === 'code') {
      return 'mistral-local';
    }
    
    // Por defecto, usar LLaMA para tareas generales
    return 'llama-local';
  }
  
  /**
   * Maneja fallbacks cuando un modelo no está disponible
   */
  async handleFallback(originalModel, prompt, options) {
    logger.warn(`⚠️ Modelo ${originalModel} no disponible, buscando fallback...`);
    
    const availableModels = await this.checkAvailableModels();
    const fallbackOrder = ['llama-local', 'mistral-local', 'deepseek-local'];
    
    for (const fallbackModel of fallbackOrder) {
      if (fallbackModel !== originalModel && availableModels[fallbackModel]?.modelExists) {
        logger.info(`🔄 Usando fallback: ${fallbackModel}`);
        const result = await this.callLocalModelWithLangwatch(fallbackModel, prompt, options);
        result.fallbackUsed = true;
        result.originalModel = originalModel;
        return result;
      }
    }
    
    throw new Error('No hay modelos locales disponibles');
  }
  
  /**
   * Obtiene estadísticas de Langwatch para modelos locales
   */
  getLangwatchStats() {
    return enhancedLangwatchMiddleware.getLocalModelStats();
  }
  
  /**
   * Obtiene estadísticas de contradicción
   */
  getContradictionStats() {
    return contradictionService.getContradictionStats();
  }
  
  /**
   * Health check con métricas de Langwatch
   */
  async healthCheckWithLangwatch() {
    try {
      const testPrompt = "Hello, this is a test. Please respond with 'OK'.";
      const results = {};
      
      for (const modelType of Object.keys(this.modelsConfig)) {
        try {
          const startTime = Date.now();
          const result = await this.callLocalModelWithLangwatch(modelType, testPrompt, {
            maxTokens: 10,
            temperature: 0.1,
            sessionId: `health_check_${Date.now()}`
          });
          
          results[modelType] = {
            status: result.success ? 'healthy' : 'error',
            responseTime: Date.now() - startTime,
            langwatchScore: result.metadata?.langwatchTracking?.score,
            error: result.error || null
          };
          
        } catch (error) {
          results[modelType] = {
            status: 'error',
            responseTime: null,
            langwatchScore: null,
            error: error.message
          };
        }
      }
      
      return {
        success: true,
        timestamp: new Date().toISOString(),
        results,
        langwatchEnabled: true,
        overallStats: this.getLangwatchStats()
      };
      
    } catch (error) {
      logger.error('❌ Error en health check con Langwatch:', error);
      return {
        success: false,
        error: error.message,
        timestamp: new Date().toISOString(),
        results: {},
        langwatchEnabled: false
      };
    }
  }
}

/**
 * Instancia singleton del adaptador mejorado
 */
export const enhancedLocalLLMAdapter = new EnhancedLocalLLMAdapter();

/**
 * Función principal para llamar modelos locales con Langwatch
 */
export async function callLocalModelWithLangwatch(modelType, prompt, options = {}) {
  try {
    // Auto-detección de modelo
    if (modelType === 'auto') {
      modelType = enhancedLocalLLMAdapter.detectBestModel(prompt, options.taskType);
      logger.info(`🎯 Auto-detectado modelo: ${modelType}`);
    }
    
    // Intentar llamada principal
    const result = await enhancedLocalLLMAdapter.callLocalModelWithLangwatch(modelType, prompt, options);
    
    if (result.success) {
      return result;
    }
    
    // Si falla, intentar fallback
    if (options.allowFallback !== false) {
      return await enhancedLocalLLMAdapter.handleFallback(modelType, prompt, options);
    }
    
    return result;
    
  } catch (error) {
    logger.error('❌ Error en callLocalModelWithLangwatch:', error);
    throw error;
  }
}

/**
 * Función para obtener información de modelos disponibles con Langwatch
 */
export async function getAvailableLocalModelsWithLangwatch() {
  try {
    if (!enhancedLocalLLMAdapter.isInitialized) {
      await enhancedLocalLLMAdapter.initialize();
    }
    
    const available = await enhancedLocalLLMAdapter.checkAvailableModels();
    const modelsInfo = Object.entries(ENHANCED_LOCAL_MODELS_CONFIG).map(([type, config]) => ({
      type,
      displayName: config.displayName,
      description: config.description,
      maxTokens: config.maxTokens,
      temperature: config.temperature,
      modelPath: config.modelPath,
      scriptPath: config.scriptPath,
      langwatch: config.langwatch
    }));
    
    return {
      success: true,
      models: modelsInfo,
      availability: available,
      totalConfigured: modelsInfo.length,
      totalAvailable: Object.values(available).filter(m => m.modelExists && m.scriptExists).length,
      langwatchEnabled: true,
      stats: enhancedLocalLLMAdapter.getLangwatchStats()
    };
    
  } catch (error) {
    logger.error('❌ Error obteniendo modelos disponibles con Langwatch:', error);
    return {
      success: false,
      error: error.message,
      models: [],
      availability: {},
      totalConfigured: 0,
      totalAvailable: 0,
      langwatchEnabled: false
    };
  }
}

/**
 * Función para health check con Langwatch
 */
export async function healthCheckLocalModelsWithLangwatch() {
  return await enhancedLocalLLMAdapter.healthCheckWithLangwatch();
}

export default {
  EnhancedLocalLLMAdapter,
  enhancedLocalLLMAdapter,
  callLocalModelWithLangwatch,
  getAvailableLocalModelsWithLangwatch,
  healthCheckLocalModelsWithLangwatch,
  ENHANCED_LOCAL_MODELS_CONFIG
};

