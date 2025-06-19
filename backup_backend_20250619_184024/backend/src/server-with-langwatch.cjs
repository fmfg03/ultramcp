/**
 * Server Configuration with Langwatch Middleware
 * 
 * Servidor principal con middleware de Langwatch integrado
 * para monitoreo completo del sistema MCP
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const compression = require('compression');
require('dotenv').config();

// Importar middleware de Langwatch
const { langwatchRequestMiddleware, initializeLangwatch } = require('./src/middleware/langwatchMiddleware.js');

// Importar rutas
const taskRoutes = require('./src/routes/taskRoutes.js');
const mcpRoutes = require('./src/routes/mcpRoutes.js');
const healthRoutes = require('./src/routes/healthRoutes.js');

// Importar servicios
const logger = require('./src/utils/logger.js');

const app = express();
const PORT = process.env.PORT || 3001;

// Inicializar Langwatch
initializeLangwatch();

// Middleware de seguridad
app.use(helmet({
  contentSecurityPolicy: false, // Deshabilitado para desarrollo
  crossOriginEmbedderPolicy: false
}));

// CORS
app.use(cors({
  origin: true, // Permitir todos los orígenes en desarrollo
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutos
  max: 100, // Límite de 100 requests por ventana por IP
  message: {
    error: 'Too many requests from this IP, please try again later.'
  },
  standardHeaders: true,
  legacyHeaders: false
});
app.use('/api/', limiter);

// Compresión
app.use(compression());

// Parsing de JSON
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Middleware de Langwatch para tracking de requests
app.use(langwatchRequestMiddleware());

// Middleware de logging
app.use((req, res, next) => {
  const startTime = Date.now();
  
  res.on('finish', () => {
    const duration = Date.now() - startTime;
    logger.info('HTTP Request', {
      method: req.method,
      url: req.url,
      statusCode: res.statusCode,
      duration: `${duration}ms`,
      userAgent: req.get('User-Agent'),
      ip: req.ip
    });
  });
  
  next();
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: process.env.NODE_ENV || 'development',
    langwatchEnabled: !!process.env.LANGWATCH_API_KEY,
    version: '1.0.0'
  });
});

// Rutas principales
app.use('/api', taskRoutes);
app.use('/api/mcp', mcpRoutes);
app.use('/api/health', healthRoutes);
app.use('/api/analytics', require('./src/routes/analyticsRoutes.js'));

// Ruta de prueba para Langwatch
app.post('/api/test-langwatch', async (req, res) => {
  try {
    const { message } = req.body;
    
    // Simular una operación que se trackea
    logger.info('🔍 Test Langwatch endpoint called', { message });
    
    res.json({
      success: true,
      message: 'Langwatch test completed',
      timestamp: new Date().toISOString(),
      receivedMessage: message
    });
    
  } catch (error) {
    logger.error('Error in Langwatch test endpoint:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Middleware de manejo de errores
app.use((error, req, res, next) => {
  logger.error('Unhandled error:', {
    error: error.message,
    stack: error.stack,
    url: req.url,
    method: req.method
  });
  
  res.status(error.status || 500).json({
    success: false,
    error: process.env.NODE_ENV === 'production' 
      ? 'Internal server error' 
      : error.message,
    timestamp: new Date().toISOString()
  });
});

// Middleware para rutas no encontradas
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    error: 'Route not found',
    path: req.originalUrl,
    timestamp: new Date().toISOString()
  });
});

// Iniciar servidor
app.listen(PORT, '0.0.0.0', () => {
  logger.info(`🚀 MCP Server iniciado en puerto ${PORT}`, {
    environment: process.env.NODE_ENV || 'development',
    langwatchEnabled: !!process.env.LANGWATCH_API_KEY,
    timestamp: new Date().toISOString()
  });
  
  // Log de configuración de Langwatch
  if (process.env.LANGWATCH_API_KEY) {
    logger.info('🔍 Langwatch monitoring habilitado', {
      projectId: process.env.LANGWATCH_PROJECT_ID || 'mcp-recursive-system',
      endpoint: process.env.LANGWATCH_ENDPOINT || 'https://app.langwatch.ai'
    });
  } else {
    logger.warn('⚠️ Langwatch monitoring deshabilitado - LANGWATCH_API_KEY no configurado');
  }
});

// Manejo de señales de terminación
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  process.exit(0);
});

// Manejo de errores no capturados
process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception:', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

module.exports = app;

