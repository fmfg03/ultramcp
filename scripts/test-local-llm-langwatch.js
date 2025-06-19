#!/usr/bin/env node
/**
 * Test CLI for Local LLM Models with Langwatch Integration
 * 
 * Script de prueba para validar la integración completa de Langwatch
 * con modelos LLM locales (Mistral, LLaMA, DeepSeek)
 * 
 * Uso:
 * node scripts/test-local-llm-langwatch.js <modelo> "<prompt>" [opciones]
 * 
 * Ejemplos:
 * node scripts/test-local-llm-langwatch.js mistral-local "¿Qué es el MCP?"
 * node scripts/test-local-llm-langwatch.js llama-local "Resume este texto: ..."
 * node scripts/test-local-llm-langwatch.js deepseek-local "Explícame la paradoja de Banach-Tarski"
 * node scripts/test-local-llm-langwatch.js auto "Resuelve: 2x + 5 = 15"
 */

import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import process from 'process';
import { 
  callLocalModelWithLangwatch, 
  getAvailableLocalModelsWithLangwatch,
  healthCheckLocalModelsWithLangwatch 
} from '../adapters/enhancedLocalLLMAdapter.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Configuración de pruebas
 */
const TEST_CONFIG = {
  defaultSessionId: `test_session_${Date.now()}`,
  testPrompts: {
    'mistral-local': [
      "Explica qué es el protocolo MCP en 3 pasos",
      "¿Cómo funciona un sistema de orquestación de agentes?",
      "Dame instrucciones para crear una API REST"
    ],
    'llama-local': [
      "Describe las ventajas de usar modelos locales vs APIs",
      "Cuenta una historia sobre inteligencia artificial",
      "Explica el concepto de contradicción explícita"
    ],
    'deepseek-local': [
      "Resuelve: Si x² + 5x - 6 = 0, encuentra x",
      "Demuestra que la suma de números impares es siempre cuadrada",
      "Explica la paradoja de Banach-Tarski paso a paso"
    ]
  },
  contradictionTests: [
    {
      prompt: "Explica qué es 2+2",
      expectedScore: 0.3, // Intencionalmente bajo para activar contradicción
      attempts: 3
    }
  ]
};

/**
 * Colores para output de consola
 */
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

/**
 * Función para imprimir con colores
 */
function colorPrint(text, color = 'reset') {
  console.log(`${colors[color]}${text}${colors.reset}`);
}

/**
 * Función para mostrar ayuda
 */
function showHelp() {
  colorPrint('\n🤖 Test CLI para Local LLM Models con Langwatch', 'cyan');
  colorPrint('='.repeat(60), 'blue');
  
  console.log('\nUso:');
  console.log('  node scripts/test-local-llm-langwatch.js <comando> [argumentos]');
  
  console.log('\nComandos disponibles:');
  console.log('  test <modelo> "<prompt>"     - Probar modelo específico');
  console.log('  auto "<prompt>"              - Auto-detectar mejor modelo');
  console.log('  health                       - Health check de todos los modelos');
  console.log('  available                    - Listar modelos disponibles');
  console.log('  contradiction <modelo>       - Probar contradicción explícita');
  console.log('  benchmark                    - Ejecutar benchmark completo');
  console.log('  stats                        - Mostrar estadísticas de Langwatch');
  
  console.log('\nModelos soportados:');
  console.log('  mistral-local    - Modelo Mistral para tareas generales');
  console.log('  llama-local      - Modelo LLaMA para comprensión de texto');
  console.log('  deepseek-local   - Modelo DeepSeek para matemáticas y lógica');
  console.log('  auto             - Auto-detección basada en el prompt');
  
  console.log('\nEjemplos:');
  console.log('  node scripts/test-local-llm-langwatch.js test mistral-local "¿Qué es el MCP?"');
  console.log('  node scripts/test-local-llm-langwatch.js auto "Resuelve: 2x + 5 = 15"');
  console.log('  node scripts/test-local-llm-langwatch.js health');
  console.log('  node scripts/test-local-llm-langwatch.js benchmark');
}

/**
 * Función para probar un modelo específico
 */
async function testModel(modelType, prompt, options = {}) {
  try {
    colorPrint(`\n🧪 Probando modelo: ${modelType}`, 'yellow');
    colorPrint('-'.repeat(50), 'blue');
    
    const startTime = Date.now();
    
    const result = await callLocalModelWithLangwatch(modelType, prompt, {
      sessionId: options.sessionId || TEST_CONFIG.defaultSessionId,
      maxTokens: options.maxTokens || 256,
      temperature: options.temperature || 0.7,
      tags: ['test', 'cli', ...(options.tags || [])]
    });
    
    const duration = Date.now() - startTime;
    
    if (result.success) {
      colorPrint('✅ Respuesta exitosa:', 'green');
      console.log(`\nModelo: ${result.displayName}`);
      console.log(`Prompt: "${prompt}"`);
      console.log(`\nRespuesta:\n${result.response}`);
      
      console.log('\n📊 Métricas:');
      console.log(`- Duración: ${duration}ms`);
      console.log(`- Tokens prompt: ${result.tokenUsage?.promptTokens || 'N/A'}`);
      console.log(`- Tokens respuesta: ${result.tokenUsage?.completionTokens || 'N/A'}`);
      console.log(`- Tokens totales: ${result.tokenUsage?.totalTokens || 'N/A'}`);
      
      if (result.metadata?.langwatchTracking) {
        const lw = result.metadata.langwatchTracking;
        console.log('\n🔍 Langwatch Tracking:');
        console.log(`- Score: ${lw.score?.toFixed(3) || 'N/A'}`);
        console.log(`- Tracking ID: ${lw.trackingId || 'N/A'}`);
        console.log(`- Contradicción aplicada: ${lw.contradiction?.triggered ? 'Sí' : 'No'}`);
        
        if (lw.contradiction?.triggered) {
          console.log(`- Intensidad: ${lw.contradiction.intensity || 'N/A'}`);
          console.log(`- Intento #: ${lw.contradiction.attemptNumber || 'N/A'}`);
        }
      }
      
      if (result.fallbackUsed) {
        colorPrint(`⚠️ Fallback usado: ${result.originalModel} → ${result.modelType}`, 'yellow');
      }
      
    } else {
      colorPrint('❌ Error en la respuesta:', 'red');
      console.log(`Error: ${result.error}`);
      console.log(`Duración: ${duration}ms`);
    }
    
    return result;
    
  } catch (error) {
    colorPrint(`❌ Error ejecutando test: ${error.message}`, 'red');
    throw error;
  }
}

/**
 * Función para health check
 */
async function healthCheck() {
  try {
    colorPrint('\n🏥 Health Check de Modelos Locales con Langwatch', 'cyan');
    colorPrint('='.repeat(60), 'blue');
    
    const health = await healthCheckLocalModelsWithLangwatch();
    
    if (health.success) {
      colorPrint('✅ Health check completado exitosamente', 'green');
      
      console.log('\n📊 Resultados por modelo:');
      for (const [modelType, result] of Object.entries(health.results)) {
        const status = result.status === 'healthy' ? '✅' : '❌';
        const score = result.langwatchScore ? ` (Score: ${result.langwatchScore.toFixed(3)})` : '';
        
        console.log(`${status} ${modelType}: ${result.status}${score}`);
        if (result.responseTime) {
          console.log(`   Tiempo de respuesta: ${result.responseTime}ms`);
        }
        if (result.error) {
          console.log(`   Error: ${result.error}`);
        }
      }
      
      if (health.overallStats) {
        console.log('\n📈 Estadísticas generales:');
        const stats = health.overallStats;
        console.log(`- Total sesiones: ${stats.totalSessions || 0}`);
        console.log(`- Score promedio: ${stats.averageScore?.toFixed(3) || 'N/A'}`);
        console.log(`- Duración promedio: ${stats.averageDuration?.toFixed(0) || 'N/A'}ms`);
        console.log(`- Tasa de contradicción: ${(stats.contradictionRate * 100)?.toFixed(1) || 0}%`);
      }
      
    } else {
      colorPrint('❌ Health check falló:', 'red');
      console.log(`Error: ${health.error}`);
    }
    
    return health;
    
  } catch (error) {
    colorPrint(`❌ Error en health check: ${error.message}`, 'red');
    throw error;
  }
}

/**
 * Función para listar modelos disponibles
 */
async function listAvailableModels() {
  try {
    colorPrint('\n📋 Modelos Locales Disponibles con Langwatch', 'cyan');
    colorPrint('='.repeat(60), 'blue');
    
    const info = await getAvailableLocalModelsWithLangwatch();
    
    if (info.success) {
      console.log(`\nTotal configurados: ${info.totalConfigured}`);
      console.log(`Total disponibles: ${info.totalAvailable}`);
      console.log(`Langwatch habilitado: ${info.langwatchEnabled ? '✅' : '❌'}`);
      
      console.log('\n🤖 Modelos configurados:');
      for (const model of info.models) {
        const available = info.availability[model.type];
        const status = (available?.modelExists && available?.scriptExists) ? '✅' : '❌';
        
        console.log(`\n${status} ${model.type}:`);
        console.log(`   Nombre: ${model.displayName}`);
        console.log(`   Descripción: ${model.description}`);
        console.log(`   Max tokens: ${model.maxTokens}`);
        console.log(`   Temperatura: ${model.temperature}`);
        console.log(`   Modelo existe: ${available?.modelExists ? '✅' : '❌'}`);
        console.log(`   Script existe: ${available?.scriptExists ? '✅' : '❌'}`);
        console.log(`   Langwatch: ${model.langwatch.enabled ? '✅' : '❌'}`);
      }
      
      if (info.stats && info.stats.totalSessions > 0) {
        console.log('\n📊 Estadísticas de uso:');
        console.log(`- Sesiones totales: ${info.stats.totalSessions}`);
        console.log(`- Score promedio: ${info.stats.averageScore?.toFixed(3)}`);
        console.log(`- Duración promedio: ${info.stats.averageDuration?.toFixed(0)}ms`);
      }
      
    } else {
      colorPrint('❌ Error obteniendo información de modelos:', 'red');
      console.log(`Error: ${info.error}`);
    }
    
    return info;
    
  } catch (error) {
    colorPrint(`❌ Error listando modelos: ${error.message}`, 'red');
    throw error;
  }
}

/**
 * Función para probar contradicción explícita
 */
async function testContradiction(modelType) {
  try {
    colorPrint(`\n🔥 Probando Contradicción Explícita: ${modelType}`, 'magenta');
    colorPrint('='.repeat(60), 'blue');
    
    const sessionId = `contradiction_test_${Date.now()}`;
    const testCase = TEST_CONFIG.contradictionTests[0];
    
    console.log(`Prompt de prueba: "${testCase.prompt}"`);
    console.log(`Intentos planificados: ${testCase.attempts}`);
    
    const results = [];
    
    for (let attempt = 1; attempt <= testCase.attempts; attempt++) {
      colorPrint(`\n📝 Intento ${attempt}/${testCase.attempts}:`, 'yellow');
      
      const result = await testModel(modelType, testCase.prompt, {
        sessionId,
        tags: ['contradiction_test', `attempt_${attempt}`]
      });
      
      results.push(result);
      
      if (result.success && result.metadata?.langwatchTracking) {
        const lw = result.metadata.langwatchTracking;
        console.log(`Score obtenido: ${lw.score?.toFixed(3)}`);
        
        if (lw.contradiction?.triggered) {
          colorPrint(`🔥 Contradicción activada: ${lw.contradiction.intensity}`, 'magenta');
        } else {
          colorPrint('ℹ️ Sin contradicción aplicada', 'blue');
        }
      }
      
      // Pausa entre intentos
      if (attempt < testCase.attempts) {
        console.log('⏳ Esperando 2 segundos...');
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
    
    // Análisis de resultados
    colorPrint('\n📊 Análisis de Contradicción:', 'cyan');
    const scores = results.filter(r => r.success && r.metadata?.langwatchTracking?.score)
                          .map(r => r.metadata.langwatchTracking.score);
    
    if (scores.length > 0) {
      console.log(`Scores obtenidos: ${scores.map(s => s.toFixed(3)).join(' → ')}`);
      
      if (scores.length > 1) {
        const improvement = scores[scores.length - 1] - scores[0];
        const improvementPercent = (improvement / scores[0]) * 100;
        
        if (improvement > 0) {
          colorPrint(`✅ Mejora detectada: +${improvement.toFixed(3)} (+${improvementPercent.toFixed(1)}%)`, 'green');
        } else {
          colorPrint(`❌ Sin mejora: ${improvement.toFixed(3)} (${improvementPercent.toFixed(1)}%)`, 'red');
        }
      }
    }
    
    const contradictionsApplied = results.filter(r => 
      r.success && r.metadata?.langwatchTracking?.contradiction?.triggered
    ).length;
    
    console.log(`Contradicciones aplicadas: ${contradictionsApplied}/${results.length}`);
    
    return results;
    
  } catch (error) {
    colorPrint(`❌ Error en test de contradicción: ${error.message}`, 'red');
    throw error;
  }
}

/**
 * Función para ejecutar benchmark completo
 */
async function runBenchmark() {
  try {
    colorPrint('\n🏁 Benchmark Completo de Modelos Locales con Langwatch', 'cyan');
    colorPrint('='.repeat(70), 'blue');
    
    const results = {};
    const sessionId = `benchmark_${Date.now()}`;
    
    // Probar cada modelo con sus prompts específicos
    for (const [modelType, prompts] of Object.entries(TEST_CONFIG.testPrompts)) {
      colorPrint(`\n🤖 Benchmarking ${modelType}:`, 'yellow');
      results[modelType] = [];
      
      for (let i = 0; i < prompts.length; i++) {
        const prompt = prompts[i];
        console.log(`\n  Test ${i + 1}/${prompts.length}: "${prompt.substring(0, 50)}..."`);
        
        try {
          const result = await testModel(modelType, prompt, {
            sessionId: `${sessionId}_${modelType}_${i}`,
            tags: ['benchmark', modelType, `test_${i + 1}`]
          });
          
          results[modelType].push({
            prompt,
            success: result.success,
            score: result.metadata?.langwatchTracking?.score,
            duration: result.metadata?.duration,
            tokens: result.tokenUsage?.totalTokens,
            error: result.error
          });
          
        } catch (error) {
          results[modelType].push({
            prompt,
            success: false,
            error: error.message
          });
        }
        
        // Pausa entre tests
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    
    // Análisis de resultados
    colorPrint('\n📊 Resultados del Benchmark:', 'cyan');
    colorPrint('='.repeat(50), 'blue');
    
    for (const [modelType, modelResults] of Object.entries(results)) {
      const successful = modelResults.filter(r => r.success);
      const avgScore = successful.length > 0 ? 
        successful.reduce((sum, r) => sum + (r.score || 0), 0) / successful.length : 0;
      const avgDuration = successful.length > 0 ? 
        successful.reduce((sum, r) => sum + (r.duration || 0), 0) / successful.length : 0;
      const avgTokens = successful.length > 0 ? 
        successful.reduce((sum, r) => sum + (r.tokens || 0), 0) / successful.length : 0;
      
      console.log(`\n🤖 ${modelType}:`);
      console.log(`   Tests exitosos: ${successful.length}/${modelResults.length}`);
      console.log(`   Score promedio: ${avgScore.toFixed(3)}`);
      console.log(`   Duración promedio: ${avgDuration.toFixed(0)}ms`);
      console.log(`   Tokens promedio: ${avgTokens.toFixed(0)}`);
      
      if (successful.length < modelResults.length) {
        const failed = modelResults.filter(r => !r.success);
        console.log(`   Errores: ${failed.length}`);
        failed.forEach(f => console.log(`     - ${f.error}`));
      }
    }
    
    return results;
    
  } catch (error) {
    colorPrint(`❌ Error en benchmark: ${error.message}`, 'red');
    throw error;
  }
}

/**
 * Función principal
 */
async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    showHelp();
    return;
  }
  
  const command = args[0];
  
  try {
    switch (command) {
      case 'test':
        if (args.length < 3) {
          colorPrint('❌ Error: Faltan argumentos para test', 'red');
          console.log('Uso: node scripts/test-local-llm-langwatch.js test <modelo> "<prompt>"');
          return;
        }
        await testModel(args[1], args[2]);
        break;
        
      case 'auto':
        if (args.length < 2) {
          colorPrint('❌ Error: Falta prompt para auto-detección', 'red');
          console.log('Uso: node scripts/test-local-llm-langwatch.js auto "<prompt>"');
          return;
        }
        await testModel('auto', args[1]);
        break;
        
      case 'health':
        await healthCheck();
        break;
        
      case 'available':
        await listAvailableModels();
        break;
        
      case 'contradiction':
        if (args.length < 2) {
          colorPrint('❌ Error: Falta modelo para test de contradicción', 'red');
          console.log('Uso: node scripts/test-local-llm-langwatch.js contradiction <modelo>');
          return;
        }
        await testContradiction(args[1]);
        break;
        
      case 'benchmark':
        await runBenchmark();
        break;
        
      case 'help':
      case '--help':
      case '-h':
        showHelp();
        break;
        
      default:
        colorPrint(`❌ Comando desconocido: ${command}`, 'red');
        showHelp();
        process.exit(1);
    }
    
    colorPrint('\n✅ Test completado exitosamente', 'green');
    
  } catch (error) {
    colorPrint(`\n❌ Error ejecutando comando '${command}': ${error.message}`, 'red');
    console.error(error.stack);
    process.exit(1);
  }
}

// Ejecutar si es llamado directamente
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

