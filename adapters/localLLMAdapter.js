/**
 * Local LLM Adapter
 * 
 * Adaptador universal para modelos LLM locales (Mistral, LLaMA, DeepSeek)
 * Ejecuta scripts Python correspondientes y maneja respuestas
 * 
 * @module localLLMAdapter
 */

import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import logger from '../backend/src/utils/logger.js';

/**
 * Configuración de modelos locales
 */
const LOCAL_MODELS_CONFIG = {
  'mistral-local': {
    scriptPath: 'scripts/run_local_mistral.py',
    modelPath: 'models/mistral.gguf',
    displayName: 'Mistral Local',
    maxTokens: 512,
    temperature: 0.7,
    description: 'Modelo Mistral local optimizado para tareas generales y razonamiento'
  },
  'llama-local': {
    scriptPath: 'scripts/run_local_llama.py',
    modelPath: 'models/llama.gguf',
    displayName: 'LLaMA Local',
    maxTokens: 512,
    temperature: 0.7,
    description: 'Modelo LLaMA local potente para comprensión y generación de texto'
  },
  'deepseek-local': {
    scriptPath: 'scripts/run_local_deepseek.py',
    modelPath: 'models/deepseek.gguf',
    displayName: 'DeepSeek Local',
    maxTokens: 512,
    temperature: 0.3,
    description: 'Modelo DeepSeek local especializado en matemáticas y lógica compleja'
  }
};

/**
 * Configuración por defecto para fallbacks
 */
const DEFAULT_CONFIG = {
  maxTokens: 512,
  temperature: 0.7,
  timeout: 30000, // 30 segundos
  encoding: 'utf-8'
};

/**
 * Clase principal del adaptador de LLMs locales
 */
export class LocalLLMAdapter {
  constructor() {
    this.modelsConfig = LOCAL_MODELS_CONFIG;
    this.projectRoot = process.cwd();
    this.isInitialized = false;
  }
  
  /**
   * Inicializa el adaptador verificando paths y modelos
   */
  async initialize() {
    try {
      logger.info('🔧 Inicializando LocalLLMAdapter...');
      
      // Verificar que existan los directorios necesarios
      const requiredDirs = ['scripts', 'models'];
      for (const dir of requiredDirs) {
        const dirPath = path.join(this.projectRoot, dir);
        if (!fs.existsSync(dirPath)) {
          fs.mkdirSync(dirPath, { recursive: true });
          logger.info(`📁 Directorio creado: ${dir}`);
        }
      }
      
      // Verificar disponibilidad de modelos
      const availableModels = await this.checkAvailableModels();
      logger.info('📊 Modelos disponibles:', availableModels);
      
      this.isInitialized = true;
      logger.info('✅ LocalLLMAdapter inicializado exitosamente');
      
      return {
        success: true,
        availableModels,
        totalModels: Object.keys(this.modelsConfig).length
      };
      
    } catch (error) {
      logger.error('❌ Error inicializando LocalLLMAdapter:', error);
      throw error;
    }
  }
  
  /**
   * Verifica qué modelos están disponibles
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
        description: config.description
      };
    }
    
    return available;
  }
  
  /**
   * Llama a un modelo local específico
   * 
   * @param {string} modelType - Tipo de modelo (mistral-local, llama-local, deepseek-local)
   * @param {string} prompt - Prompt para el modelo
   * @param {Object} options - Opciones adicionales
   * @returns {Promise<Object>} Respuesta del modelo
   */
  async callLocalModel(modelType, prompt, options = {}) {
    try {
      if (!this.isInitialized) {
        await this.initialize();
      }
      
      const startTime = Date.now();
      logger.info(`🤖 Llamando modelo local: ${modelType}`);
      
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
      
      // Preparar parámetros
      const params = {
        prompt,
        maxTokens: options.maxTokens || modelConfig.maxTokens || DEFAULT_CONFIG.maxTokens,
        temperature: options.temperature || modelConfig.temperature || DEFAULT_CONFIG.temperature,
        sessionId: options.sessionId || `session_${Date.now()}`,
        modelPath: path.join(this.projectRoot, modelConfig.modelPath),
        ...options
      };
      
      // Ejecutar script Python
      const result = await this.executePythonScript(modelConfig.scriptPath, params);
      
      const duration = Date.now() - startTime;
      
      // Procesar respuesta
      const response = {
        success: true,
        modelType,
        displayName: modelConfig.displayName,
        response: result.response,
        tokenUsage: {
          promptTokens: result.promptTokens || this.estimateTokens(prompt),
          completionTokens: result.completionTokens || this.estimateTokens(result.response),
          totalTokens: result.totalTokens || (this.estimateTokens(prompt) + this.estimateTokens(result.response))
        },
        metadata: {
          duration,
          temperature: params.temperature,
          maxTokens: params.maxTokens,
          modelPath: modelConfig.modelPath,
          sessionId: params.sessionId,
          timestamp: new Date().toISOString()
        }
      };
      
      logger.info(`✅ Modelo ${modelType} respondió en ${duration}ms`);
      return response;
      
    } catch (error) {
      logger.error(`❌ Error en modelo ${modelType}:`, error);
      
      return {
        success: false,
        modelType,
        error: error.message,
        fallbackUsed: false,
        metadata: {
          duration: Date.now() - (options.startTime || Date.now()),
          timestamp: new Date().toISOString()
        }
      };
    }
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
   * Estima el número de tokens en un texto
   */
  estimateTokens(text) {
    if (!text) return 0;
    // Estimación simple: ~4 caracteres por token
    return Math.ceil(text.length / 4);
  }
  
  /**
   * Obtiene información de todos los modelos configurados
   */
  getModelsInfo() {
    return Object.entries(this.modelsConfig).map(([type, config]) => ({
      type,
      displayName: config.displayName,
      description: config.description,
      maxTokens: config.maxTokens,
      temperature: config.temperature,
      modelPath: config.modelPath,
      scriptPath: config.scriptPath
    }));
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
        const result = await this.callLocalModel(fallbackModel, prompt, options);
        result.fallbackUsed = true;
        result.originalModel = originalModel;
        return result;
      }
    }
    
    throw new Error('No hay modelos locales disponibles');
  }
}

/**
 * Instancia singleton del adaptador
 */
export const localLLMAdapter = new LocalLLMAdapter();

/**
 * Función principal para llamar modelos locales
 * 
 * @param {string} modelType - Tipo de modelo o 'auto' para detección automática
 * @param {string} prompt - Prompt para el modelo
 * @param {Object} options - Opciones adicionales
 * @returns {Promise<Object>} Respuesta del modelo
 */
export async function callLocalModel(modelType, prompt, options = {}) {
  try {
    // Auto-detección de modelo
    if (modelType === 'auto') {
      modelType = localLLMAdapter.detectBestModel(prompt, options.taskType);
      logger.info(`🎯 Auto-detectado modelo: ${modelType}`);
    }
    
    // Intentar llamada principal
    const result = await localLLMAdapter.callLocalModel(modelType, prompt, options);
    
    if (result.success) {
      return result;
    }
    
    // Si falla, intentar fallback
    if (options.allowFallback !== false) {
      return await localLLMAdapter.handleFallback(modelType, prompt, options);
    }
    
    return result;
    
  } catch (error) {
    logger.error('❌ Error en callLocalModel:', error);
    throw error;
  }
}

/**
 * Función para obtener información de modelos disponibles
 */
export async function getAvailableLocalModels() {
  try {
    if (!localLLMAdapter.isInitialized) {
      await localLLMAdapter.initialize();
    }
    
    const available = await localLLMAdapter.checkAvailableModels();
    const modelsInfo = localLLMAdapter.getModelsInfo();
    
    return {
      success: true,
      models: modelsInfo,
      availability: available,
      totalConfigured: modelsInfo.length,
      totalAvailable: Object.values(available).filter(m => m.modelExists && m.scriptExists).length
    };
    
  } catch (error) {
    logger.error('❌ Error obteniendo modelos disponibles:', error);
    return {
      success: false,
      error: error.message,
      models: [],
      availability: {},
      totalConfigured: 0,
      totalAvailable: 0
    };
  }
}

/**
 * Función para verificar el estado de salud de los modelos locales
 */
export async function healthCheckLocalModels() {
  try {
    const testPrompt = "Hello, this is a test. Please respond with 'OK'.";
    const results = {};
    
    for (const modelType of Object.keys(LOCAL_MODELS_CONFIG)) {
      try {
        const startTime = Date.now();
        const result = await localLLMAdapter.callLocalModel(modelType, testPrompt, {
          maxTokens: 10,
          temperature: 0.1
        });
        
        results[modelType] = {
          status: result.success ? 'healthy' : 'error',
          responseTime: Date.now() - startTime,
          error: result.error || null
        };
        
      } catch (error) {
        results[modelType] = {
          status: 'error',
          responseTime: null,
          error: error.message
        };
      }
    }
    
    return {
      success: true,
      timestamp: new Date().toISOString(),
      results
    };
    
  } catch (error) {
    logger.error('❌ Error en health check:', error);
    return {
      success: false,
      error: error.message,
      timestamp: new Date().toISOString(),
      results: {}
    };
  }
}

export default {
  LocalLLMAdapter,
  localLLMAdapter,
  callLocalModel,
  getAvailableLocalModels,
  healthCheckLocalModels,
  LOCAL_MODELS_CONFIG
};

