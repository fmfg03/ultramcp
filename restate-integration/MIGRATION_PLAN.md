# UltraMCP Restate Migration Plan
## Migración Gradual de Orquestación Manual a Durable Workflows

Este plan describe cómo migrar UltraMCP de orquestación manual a workflows durables con Restate, manteniendo compatibilidad y minimizando riesgos.

## 🎯 Objetivos de la Migración

### Beneficios Esperados
✅ **Durabilidad**: Workflows que sobreviven crashes y reiniciar automáticamente  
✅ **Observabilidad**: Tracing completo de cada paso del workflow  
✅ **Simplicidad**: Menos código boilerplate para manejo de estado  
✅ **Escalabilidad**: Orquestación distribuida sin locks manuales  
✅ **Debugging**: Replay y rollback de workflows para análisis  

### Estado Actual vs. Estado Objetivo

| Componente | Estado Actual | Estado Objetivo |
|------------|---------------|-----------------|
| **Chain of Debate** | Orquestación manual en memoria | Workflow durable con pasos persistentes |
| **Security Scanner** | Ejecución directa | Workflow con reintentos automáticos |
| **Code Intelligence** | Análisis sincrónico | Pipeline asíncrono con checkpoints |
| **Agent Coordination** | Control Tower custom | Restate native orchestration |
| **Error Handling** | Try/catch manual | Automatic compensation patterns |
| **State Management** | Redis + PostgreSQL | Restate internal + metadata DB |

## 📋 Fases de Migración

### Fase 1: Instalación y Setup (Semana 1)
**Objetivo**: Instalar Restate y crear infraestructura base

#### 1.1 Instalación Local
```bash
cd /root/ultramcp/restate-integration
./install-restate.sh install
```

#### 1.2 Verificación de Instalación
```bash
# Verificar servicios
ultramcp-restate health

# Verificar conectividad
curl http://localhost:9070/health

# Verificar tracing
curl http://localhost:16686
```

#### 1.3 Integración con UltraMCP Existente
- Agregar Restate al `docker-compose.hybrid.yml` principal
- Configurar networking entre Restate y servicios UltraMCP
- Setup de métricas y logging

#### 1.4 Criterios de Éxito
- [ ] Restate ejecutándose sin conflictos
- [ ] Servicios UltraMCP pueden conectarse a Restate
- [ ] Dashboard de Jaeger muestra trazas básicas
- [ ] PostgreSQL metadata DB inicializada

---

### Fase 2: Servicio Piloto - Chain of Debate (Semana 2-3)
**Objetivo**: Migrar Chain of Debate como prueba de concepto

#### 2.1 Implementación del Workflow
```typescript
// Nuevo: chain-of-debate-workflow.ts
const chainOfDebateWorkflow = workflow("chain-of-debate", async (ctx, input) => {
  // Paso 1: Preparar debate
  const debateSetup = await ctx.sideEffect(() => setupDebate(input));
  
  // Paso 2: Ejecutar rondas (durable)
  for (let round = 1; round <= input.rounds; round++) {
    const roundResult = await ctx.sideEffect(() => executeRound(round, debateSetup));
    
    // Checkpoint automático después de cada ronda
    await ctx.sleep(1000); // delay entre rondas
  }
  
  // Paso 3: Sintetizar resultado final
  const synthesis = await ctx.sideEffect(() => synthesizeResults(debateSetup));
  
  return synthesis;
});
```

#### 2.2 Mantener Compatibilidad
- Crear adaptador que mantenga API actual del CoD service
- Implementar fallback al sistema actual si Restate falla
- Logging dual (Restate + sistema actual)

#### 2.3 Testing Paralelo
```bash
# Ejecutar debate con sistema actual
curl -X POST http://cod.ultramcp.local/debate -d '{"topic": "test"}'

# Ejecutar mismo debate con Restate
curl -X POST http://localhost:8080/chain-of-debate -d '{"topic": "test"}'

# Comparar resultados
./compare-debate-results.sh
```

#### 2.4 Criterios de Éxito
- [ ] Workflow de CoD ejecuta completamente
- [ ] Resultados equivalentes al sistema actual
- [ ] Workflow sobrevive reinicio de contenedor
- [ ] Tracing completo en Jaeger
- [ ] Performance similar o mejor

---

### Fase 3: Servicios de Análisis (Semana 4-5)
**Objetivo**: Migrar Security Scanner y Code Intelligence

#### 3.1 Security Scanner Workflow
```typescript
const securityScanWorkflow = workflow("security-scan", async (ctx, input) => {
  // Paso 1: Preparar entorno de escaneo
  const scanEnv = await ctx.sideEffect(() => prepareScanEnvironment(input.target));
  
  // Paso 2: Ejecutar escaneos en paralelo
  const [vulnScan, complianceScan, threatScan] = await Promise.all([
    ctx.sideEffect(() => vulnerabilityScan(scanEnv)),
    ctx.sideEffect(() => complianceScan(scanEnv)),
    ctx.sideEffect(() => threatModelingScan(scanEnv))
  ]);
  
  // Paso 3: Consolidar y generar reporte
  const report = await ctx.sideEffect(() => generateSecurityReport({
    vulnerability: vulnScan,
    compliance: complianceScan,
    threats: threatScan
  }));
  
  // Paso 4: Notificar resultados
  await ctx.sideEffect(() => notifySecurityResults(report));
  
  return report;
});
```

#### 3.2 Code Intelligence Workflow
```typescript
const codeAnalysisWorkflow = workflow("code-analysis", async (ctx, input) => {
  // Paso 1: Clonar y preparar repositorio
  const repo = await ctx.sideEffect(() => cloneRepository(input.repository));
  
  // Paso 2: Análisis en pipeline
  const astAnalysis = await ctx.sideEffect(() => parseAST(repo));
  const patternAnalysis = await ctx.sideEffect(() => analyzePatterns(astAnalysis));
  const qualityAnalysis = await ctx.sideEffect(() => analyzeQuality(repo, astAnalysis));
  
  // Paso 3: Generar embeddings semánticos
  const embeddings = await ctx.sideEffect(() => generateEmbeddings(astAnalysis));
  
  // Paso 4: Almacenar en memoria vectorial
  await ctx.sideEffect(() => storeInQdrant(embeddings));
  
  return {
    ast: astAnalysis,
    patterns: patternAnalysis,
    quality: qualityAnalysis,
    embeddings: embeddings.length
  };
});
```

#### 3.3 Criterios de Éxito
- [ ] Ambos workflows ejecutan sin errores
- [ ] Paralelización efectiva de tareas
- [ ] Checkpoints en cada paso crítico
- [ ] Integración con almacenamiento externo (Qdrant)
- [ ] Manejo robusto de errores

---

### Fase 4: Orquestación Compleja (Semana 6-7)
**Objetivo**: Workflows multi-agente y coordinación avanzada

#### 4.1 Meta-Workflow de Análisis Completo
```typescript
const fullAnalysisWorkflow = workflow("full-analysis", async (ctx, input) => {
  const sessionId = uuidv4();
  
  // Paso 1: Análisis inicial de código
  const codeAnalysis = await ctx.workflowCall("code-analysis", {
    repository: input.repository,
    sessionId
  });
  
  // Paso 2: Escaneo de seguridad basado en análisis
  const securityScan = await ctx.workflowCall("security-scan", {
    target: input.repository,
    context: codeAnalysis,
    sessionId
  });
  
  // Paso 3: Chain of Debate sobre hallazgos
  const debate = await ctx.workflowCall("chain-of-debate", {
    topic: `Security and quality analysis of ${input.repository}`,
    context: { codeAnalysis, securityScan },
    participants: ["security-expert", "code-architect", "devops-engineer"],
    sessionId
  });
  
  // Paso 4: Generar recomendaciones finales
  const recommendations = await ctx.sideEffect(() => generateRecommendations({
    codeAnalysis,
    securityScan,
    debate,
    sessionId
  }));
  
  return {
    sessionId,
    repository: input.repository,
    analysis: codeAnalysis,
    security: securityScan,
    debate: debate,
    recommendations,
    completedAt: new Date().toISOString()
  };
});
```

#### 4.2 Workflow de Deployment Automatizado
```typescript
const deploymentWorkflow = workflow("automated-deployment", async (ctx, input) => {
  // Paso 1: Análisis pre-deployment
  const analysis = await ctx.workflowCall("full-analysis", {
    repository: input.repository
  });
  
  // Paso 2: Validación de seguridad
  if (analysis.security.criticalIssues > 0) {
    throw new Error("Critical security issues found, deployment blocked");
  }
  
  // Paso 3: Ejecutar tests
  const testResults = await ctx.sideEffect(() => runTests(input.repository));
  if (!testResults.success) {
    throw new Error("Tests failed, deployment blocked");
  }
  
  // Paso 4: Deploy a staging
  const stagingDeploy = await ctx.sideEffect(() => deployToStaging(input));
  
  // Paso 5: Smoke tests en staging
  const smokeTests = await ctx.sideEffect(() => runSmokeTests(stagingDeploy.url));
  
  // Paso 6: Approval gate (manual o automático)
  const approval = await ctx.sideEffect(() => requestApproval({
    analysis,
    testResults,
    smokeTests
  }));
  
  if (!approval.approved) {
    throw new Error("Deployment not approved");
  }
  
  // Paso 7: Deploy a producción
  const prodDeploy = await ctx.sideEffect(() => deployToProduction(input));
  
  // Paso 8: Post-deployment monitoring
  await ctx.sleep(300000); // 5 minutos
  const healthCheck = await ctx.sideEffect(() => checkProductionHealth(prodDeploy.url));
  
  return {
    repository: input.repository,
    analysis,
    staging: stagingDeploy,
    production: prodDeploy,
    health: healthCheck,
    completedAt: new Date().toISOString()
  };
});
```

#### 4.3 Criterios de Éxito
- [ ] Workflows anidados funcionan correctamente
- [ ] Manejo de errores y rollback automático
- [ ] Timeouts y delays configurables
- [ ] Approval gates implementados
- [ ] Monitoring post-deployment

---

### Fase 5: Integración con Control Tower (Semana 8)
**Objetivo**: Reemplazar Control Tower custom con orquestación Restate

#### 5.1 Migración del Control Tower
- Convertir lógica de coordinación a workflows Restate
- Implementar service discovery via Restate
- Migrar health checking a workflows durables
- Implementar load balancing logic como workflows

#### 5.2 Monitoring y Observabilidad
```typescript
const monitoringWorkflow = workflow("system-monitoring", async (ctx) => {
  // Workflow infinito de monitoreo
  while (true) {
    // Verificar salud de todos los servicios
    const healthChecks = await ctx.sideEffect(() => checkAllServices());
    
    // Verificar métricas
    const metrics = await ctx.sideEffect(() => collectMetrics());
    
    // Alertar si hay problemas
    if (healthChecks.unhealthyServices.length > 0) {
      await ctx.sideEffect(() => sendAlerts(healthChecks.unhealthyServices));
    }
    
    // Esperar antes del siguiente check
    await ctx.sleep(30000); // 30 segundos
  }
});
```

#### 5.3 Criterios de Éxito
- [ ] Control Tower legacy desactivado
- [ ] Todos los workflows ejecutándose via Restate
- [ ] Service discovery funcionando
- [ ] Alerting automático implementado

---

## 🔧 Implementación Técnica

### Estructura de Archivos
```
/root/ultramcp/restate-integration/
├── install-restate.sh              # Script de instalación
├── MIGRATION_PLAN.md               # Este documento
├── docker-compose.yml              # Stack de Restate
├── config/
│   ├── restate.toml               # Configuración de Restate
│   └── init.sql                   # Schema de metadata
├── services/
│   ├── typescript/                # Workflows en TypeScript
│   │   ├── chain-of-debate.ts
│   │   ├── security-scan.ts
│   │   ├── code-analysis.ts
│   │   └── orchestration.ts
│   └── rust/                      # Adaptadores en Rust (futuro)
├── examples/                      # Ejemplos y demos
├── tests/                         # Tests de integración
└── docs/                          # Documentación adicional
```

### Configuración de Red
```yaml
# Adición al docker-compose principal de UltraMCP
services:
  restate:
    image: restatedev/restate:1.0.1
    ports:
      - "8080:8080"
      - "9070:9070"
    networks:
      - ultramcp
      - restate-network

  restate-workflows:
    build: ./restate-integration/services/typescript
    ports:
      - "9080:9080"
    networks:
      - ultramcp
      - restate-network
    depends_on:
      - restate
```

### Variables de Entorno
```bash
# Añadir al .env principal
RESTATE_URL=http://restate:8080
RESTATE_ADMIN_URL=http://restate:9070
RESTATE_WORKFLOWS_URL=http://restate-workflows:9080
ENABLE_RESTATE_INTEGRATION=true
RESTATE_FALLBACK_ENABLED=true
```

## 🧪 Testing y Validación

### Tests de Comparación
```bash
# Script para comparar resultados
./compare-systems.sh chain-of-debate "Test topic"
./compare-systems.sh security-scan "/path/to/code"
./compare-systems.sh code-analysis "github.com/repo/project"
```

### Benchmarks de Performance
```bash
# Medir latencia y throughput
./benchmark-workflows.sh --workflow=chain-of-debate --iterations=100
./benchmark-workflows.sh --workflow=security-scan --iterations=50
```

### Tests de Durabilidad
```bash
# Simular fallos y verificar recuperación
./durability-test.sh --kill-container=restate --after=30s
./durability-test.sh --kill-container=workflows --after=60s
```

## 🚨 Rollback Plan

### Plan de Contingencia
1. **Detección de Problemas**: Monitoring automático detecta degradación
2. **Rollback Automático**: Desactivar Restate workflows, activar sistema legacy
3. **Análisis Post-Mortem**: Investigar causa raíz
4. **Fix y Re-deploy**: Corregir problema y re-intentar migración

### Switches de Feature Flags
```typescript
// En cada workflow
if (!process.env.ENABLE_RESTATE_INTEGRATION) {
  return await legacyChainOfDebate(input);
}

// Fallback automático en caso de error
try {
  return await restateWorkflow(input);
} catch (error) {
  console.error("Restate workflow failed, falling back:", error);
  return await legacyFallback(input);
}
```

## 📊 Métricas de Éxito

### KPIs Técnicos
- **Uptime**: > 99.9% de disponibilidad de workflows
- **Performance**: Latencia similar o mejor al sistema actual
- **Durabilidad**: 100% de workflows completan después de fallos
- **Observabilidad**: 100% de pasos trackeados en Jaeger

### KPIs de Desarrollo
- **Reducción de Código**: -30% líneas de código de orquestación
- **Time to Debug**: -50% tiempo para diagnosticar problemas
- **Developer Experience**: Encuestas de satisfacción del equipo
- **Bug Rate**: Reducción de bugs relacionados con estado

## 🎯 Timeline Completo

| Semana | Fase | Entregables | Criterios de Éxito |
|--------|------|-------------|---------------------|
| 1 | Setup | Restate instalado, networking configurado | ✅ Health checks, conectividad |
| 2-3 | CoD Piloto | Workflow de Chain of Debate funcionando | ✅ Equivalencia de resultados |
| 4-5 | Análisis | Security + Code Intelligence workflows | ✅ Paralelización, checkpoints |
| 6-7 | Orquestación | Meta-workflows, deployment automation | ✅ Workflows anidados |
| 8 | Control Tower | Migración completa del Control Tower | ✅ Sistema legacy desactivado |
| 9 | Testing | Tests exhaustivos, benchmarks | ✅ Performance, durabilidad |
| 10 | Producción | Rollout completo a producción | ✅ Monitoreo, alerting |

## 🚀 Próximos Pasos

### Inmediatos (Esta Semana)
1. **Instalar Restate**: `./install-restate.sh install`
2. **Verificar Instalación**: Confirmar que todos los servicios están up
3. **Explorar Examples**: Revisar los workflows de ejemplo
4. **Primera Prueba**: Ejecutar workflow simple de Chain of Debate

### Siguiente Semana
1. **Implementar CoD Workflow**: Crear primera versión funcional
2. **Setup Testing**: Scripts de comparación y validación
3. **Documentar Hallazgos**: Pros/cons encontrados
4. **Planificar Fase 2**: Refinamiento del plan basado en aprendizajes

### Consideraciones Futuras
- **Rust Integration**: SDKs de Restate para Rust están en desarrollo
- **Cloud Deployment**: Considerar Restate Cloud vs. self-hosted
- **Multi-Region**: Replicación de workflows entre regiones
- **Cost Optimization**: Comparar costos vs. solución actual

---

**¿Listo para empezar?** 🚀

```bash
cd /root/ultramcp/restate-integration
./install-restate.sh install
```