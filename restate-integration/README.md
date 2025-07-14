# 🔥 UltraMCP + Restate Integration

**Orquestación Durable de Agentes Distribuidos para UltraMCP**

Transforma UltraMCP de orquestación manual a workflows durables con Restate, eliminando complejidad y aumentando confiabilidad.

## 🎯 ¿Por qué Restate para UltraMCP?

### Problemas del Sistema Actual
❌ **Estado frágil**: Si un servicio se cae, pierdes el contexto  
❌ **Orquestación manual**: Código boilerplate para manejar flujos  
❌ **Debugging difícil**: Hard to trace multi-agent workflows  
❌ **Escalabilidad limitada**: Locks manuales y coordinación custom  
❌ **Reintentos complejos**: Lógica de retry distribuida por el código  

### Beneficios con Restate
✅ **Durable Functions**: Workflows sobreviven crashes automáticamente  
✅ **Orquestación declarativa**: Define flujos, no implementes FSMs  
✅ **Observabilidad completa**: Tracing automático de cada paso  
✅ **Escalabilidad nativa**: Distribución sin locks manuales  
✅ **Reintentos automáticos**: Retry policies integradas  
✅ **Debugging avanzado**: Replay y rollback de workflows  

## 🚀 Quick Start

### 1. Instalación Completa (Un Comando)
```bash
cd /root/ultramcp/restate-integration
./install-restate.sh install
```

Esto instala:
- ✅ Restate Server (ports 8080, 9070, 8081)
- ✅ PostgreSQL para metadata (port 5433)
- ✅ Jaeger para tracing (port 16686)
- ✅ Ejemplo de workflows TypeScript
- ✅ Scripts de management

### 2. Verificar Instalación
```bash
# Comprobar que todo está funcionando
ultramcp-restate health

# Ver dashboard URLs
ultramcp-restate dashboard
```

### 3. Ejecutar Tests de Integración
```bash
# Tests completos (compara legacy vs Restate)
./test-restate-integration.sh all

# Tests básicos solamente
./test-restate-integration.sh basic
```

### 4. Explorar Dashboards
- **Restate Admin**: http://localhost:9070
- **Jaeger Tracing**: http://localhost:16686
- **Workflow Examples**: http://localhost:9080

## 📋 Componentes Instalados

### Core Restate Infrastructure
```yaml
services:
  restate:           # Restate server (orchestration engine)
  postgres:          # Metadata storage  
  jaeger:            # Distributed tracing
  restate-cli:       # Management tools
```

### Example Workflows
- **UltraMCP Multi-Agent**: Orquestación general de agentes
- **Chain of Debate**: Workflow durable para debates multi-LLM
- **Code Analysis**: Pipeline de análisis de código con checkpoints
- **Security Scanning**: Workflows de escaneo con reintentos

### Management Tools
- `ultramcp-restate start/stop/restart` - Control de servicios
- `ultramcp-restate health` - Health checks
- `ultramcp-restate register <url>` - Registro de servicios
- `ultramcp-restate services` - Lista de servicios registrados

## 🧪 Workflows de Ejemplo

### 1. Chain of Debate Durable
```typescript
const chainOfDebateWorkflow = workflow("chain-of-debate", async (ctx, input) => {
  const debateId = uuidv4();
  ctx.console.log(`Starting Chain of Debate: ${debateId}`);

  const debateResults = [];

  // Cada ronda es durable - si se cae, continúa desde aquí
  for (let round = 1; round <= input.rounds; round++) {
    ctx.console.log(`Round ${round}/${input.rounds}`);

    // Ejecución paralela de participantes
    const roundPromises = input.participants.map(async (participant) => {
      return await ctx.sideEffect(async () => {
        const response = await axios.post(`http://ultramcp-cod:8001/debate`, {
          topic: input.topic,
          participant,
          round,
          debateId,
          previousRounds: debateResults
        });
        return response.data;
      });
    });

    // Checkpoint automático al completar ronda
    const roundResults = await Promise.all(roundPromises);
    debateResults.push({
      round,
      timestamp: new Date().toISOString(),
      results: roundResults
    });

    // Delay entre rondas
    if (round < input.rounds) {
      await ctx.sleep(2000);
    }
  }

  // Síntesis final
  const synthesis = await ctx.sideEffect(async () => {
    const response = await axios.post(`http://ultramcp-cod:8001/synthesize`, {
      topic: input.topic,
      debateResults,
      debateId
    });
    return response.data;
  });

  return { debateId, topic: input.topic, results: debateResults, synthesis };
});
```

### 2. Análisis de Código Multi-Etapa
```typescript
const codeAnalysisWorkflow = workflow("code-analysis", async (ctx, input) => {
  const analysisId = uuidv4();

  // Paso 1: Preparar repositorio (durable)
  const repoData = await ctx.sideEffect(async () => {
    return await cloneRepository(input.repository, input.branch);
  });

  const analysisResults = {};

  // Paso 2: Análisis de seguridad (paralelo y durable)
  if (input.analysisType === "security" || input.analysisType === "all") {
    analysisResults.security = await ctx.sideEffect(async () => {
      return await securityScan(repoData.path, analysisId);
    });
  }

  // Paso 3: Análisis de calidad (durable)
  if (input.analysisType === "quality" || input.analysisType === "all") {
    analysisResults.quality = await ctx.sideEffect(async () => {
      return await qualityAnalysis(repoData.path, analysisId);
    });
  }

  // Paso 4: Análisis de patrones (durable)
  if (input.analysisType === "patterns" || input.analysisType === "all") {
    analysisResults.patterns = await ctx.sideEffect(async () => {
      return await patternAnalysis(repoData.path, analysisId);
    });
  }

  // Paso 5: Generar reporte final
  const report = await ctx.sideEffect(async () => {
    return await generateComprehensiveReport(analysisId, analysisResults);
  });

  return { analysisId, repository: input.repository, results: analysisResults, report };
});
```

### 3. Meta-Workflow de Orquestación Completa
```typescript
const fullAnalysisWorkflow = workflow("full-analysis", async (ctx, input) => {
  const sessionId = uuidv4();
  
  // Workflow anidado: análisis de código
  const codeAnalysis = await ctx.workflowCall("code-analysis", {
    repository: input.repository,
    analysisType: "all",
    sessionId
  });
  
  // Workflow anidado: escaneo de seguridad basado en análisis
  const securityScan = await ctx.workflowCall("security-scan", {
    target: input.repository,
    context: codeAnalysis,
    sessionId
  });
  
  // Workflow anidado: debate sobre hallazgos
  const debate = await ctx.workflowCall("chain-of-debate", {
    topic: `Analysis results for ${input.repository}`,
    context: { codeAnalysis, securityScan },
    participants: ["security-expert", "code-architect", "devops-engineer"],
    rounds: 3,
    sessionId
  });
  
  // Generar recomendaciones finales
  const recommendations = await ctx.sideEffect(async () => {
    return await generateActionableRecommendations({
      codeAnalysis,
      securityScan,
      debate,
      sessionId
    });
  });
  
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

## 🔄 Plan de Migración Gradual

### Fase 1: Proof of Concept (Semana 1) ✅
- [x] Instalar Restate localmente
- [x] Crear workflows de ejemplo
- [x] Tests de integración básicos
- [x] Documentación completa

### Fase 2: Chain of Debate (Semana 2-3)
- [ ] Implementar CoD workflow en producción
- [ ] Mantener fallback al sistema legacy
- [ ] Comparar performance y resultados
- [ ] Monitoring y alerting

### Fase 3: Servicios de Análisis (Semana 4-5)
- [ ] Migrar Security Scanner workflow
- [ ] Migrar Code Intelligence workflow
- [ ] Implementar workflows paralelos
- [ ] Checkpoints en pasos críticos

### Fase 4: Orquestación Compleja (Semana 6-7)
- [ ] Meta-workflows multi-agente
- [ ] Workflows de deployment automatizado
- [ ] Compensation patterns para rollback
- [ ] Integration con servicios externos

### Fase 5: Control Tower Migration (Semana 8)
- [ ] Reemplazar Control Tower con Restate
- [ ] Service discovery via workflows
- [ ] Health monitoring durables
- [ ] Load balancing logic

## 🧪 Testing y Validación

### Tests Automatizados
```bash
# Tests básicos
./test-restate-integration.sh basic

# Tests de workflows
./test-restate-integration.sh workflows

# Tests de durabilidad
./test-restate-integration.sh durability

# Tests de performance
./test-restate-integration.sh performance

# Tests completos
./test-restate-integration.sh all
```

### Comparación Legacy vs Restate
El script de testing ejecuta los mismos workflows en:
1. **Sistema legacy** (UltraMCP actual)
2. **Restate workflows** (nueva implementación)

Y compara:
- ✅ **Resultados**: ¿Son equivalentes?
- ✅ **Performance**: ¿Latencia comparable?
- ✅ **Durabilidad**: ¿Sobrevive crashes?
- ✅ **Observabilidad**: ¿Trazas completas?

### Ejemplo de Resultados de Test
```
============================================
UltraMCP Restate Integration Test Summary
============================================
Tests Passed: 23
Tests Failed: 1
Success Rate: 95%

Performance Comparison:
  Legacy Chain of Debate:   1,234ms
  Restate Chain of Debate:  1,187ms (4% faster)

Durability Test: ✅ PASSED
  Workflow survived container restart and completed successfully

Load Test: ✅ PASSED
  10 concurrent clients: 92% success rate, avg response: 856ms
```

## 📊 Monitoring y Observabilidad

### Jaeger Distributed Tracing
Accede a http://localhost:16686 para ver:
- 🔍 **Trace completo** de cada workflow
- ⏱️ **Timing de cada paso** dentro del workflow
- 🐛 **Errores y excepciones** con stack traces
- 🔄 **Reintentos automáticos** y su progreso

### Restate Admin Dashboard
Accede a http://localhost:9070 para:
- 📋 **Lista de workflows** activos
- 🚀 **Estado de ejecución** en tiempo real
- ❌ **Cancelar workflows** si es necesario
- 📈 **Métricas de performance** de cada servicio

### PostgreSQL Metadata
```sql
-- Ver workflows ejecutados
SELECT * FROM workflow_metadata ORDER BY created_at DESC LIMIT 10;

-- Ver ejecuciones de agentes
SELECT agent_name, COUNT(*) as executions, AVG(duration_ms) as avg_duration
FROM agent_executions 
GROUP BY agent_name;

-- Ver workflows fallidos
SELECT * FROM workflow_metadata WHERE status = 'failed';
```

## 🛠️ API Examples

### Ejecutar Chain of Debate
```bash
curl -X POST http://localhost:8080/chain-of-debate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Should we use microservices or monolith for this project?",
    "participants": ["architect", "developer", "devops"],
    "rounds": 3
  }'
```

### Ejecutar Análisis de Código
```bash
curl -X POST http://localhost:8080/code-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "https://github.com/user/repo.git",
    "branch": "main",
    "analysisType": "all"
  }'
```

### Ejecutar Meta-Workflow Completo
```bash
curl -X POST http://localhost:8080/full-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "https://github.com/user/repo.git",
    "includeDebate": true,
    "generateRecommendations": true
  }'
```

### Monitorear Workflow en Progreso
```bash
# Obtener status de workflow
curl http://localhost:9070/services/chain-of-debate/instances/WORKFLOW_ID

# Listar todos los workflows activos
curl http://localhost:9070/services | jq '.services[].instances'

# Cancelar workflow
curl -X DELETE http://localhost:9070/services/chain-of-debate/instances/WORKFLOW_ID
```

## 🚨 Troubleshooting

### Restate No Inicia
```bash
# Verificar puertos disponibles
netstat -ln | grep :8080
netstat -ln | grep :9070

# Ver logs de Restate
ultramcp-restate logs restate

# Reiniciar servicios
ultramcp-restate restart
```

### Workflows No Se Ejecutan
```bash
# Verificar servicios registrados
curl http://localhost:9070/deployments

# Registrar servicio manualmente
ultramcp-restate register http://localhost:9080

# Ver logs del servicio de workflows
ultramcp-restate logs restate-workflows
```

### Performance Issues
```bash
# Verificar resource usage
docker stats

# Ver métricas en Jaeger
curl http://localhost:16686/api/traces?service=ultramcp-restate

# Optimizar PostgreSQL
docker exec ultramcp-restate-postgres psql -U restate -c "VACUUM ANALYZE;"
```

## 🔄 Roadmap

### Próximas Mejoras
- **Rust SDK Integration**: Cuando madure el SDK de Rust
- **Multi-Region Deployment**: Replicación de workflows
- **Advanced Compensation**: Saga patterns para rollback
- **Custom Metrics**: Métricas específicas de UltraMCP
- **Workflow Versioning**: A/B testing de workflows

### Consideraciones a Largo Plazo
- **Restate Cloud**: Migración al servicio managed
- **Cost Optimization**: Análisis de costos vs. beneficios
- **Team Training**: Capacitación del equipo en Restate
- **Migration Completion**: Eliminación completa del sistema legacy

## 📚 Recursos

### Documentación
- [Restate Official Docs](https://docs.restate.dev/)
- [Restate Examples](https://github.com/restatedev/examples)
- [TypeScript SDK](https://docs.restate.dev/typescript/overview)
- [Rust SDK (Beta)](https://docs.restate.dev/rust/overview)

### UltraMCP Integration
- [Migration Plan](./MIGRATION_PLAN.md) - Plan detallado de migración
- [Test Results](./test-results/) - Resultados de tests de integración
- [Example Workflows](./examples/typescript/src/) - Workflows de ejemplo

---

## 🎉 ¡Empieza Ahora!

```bash
# 1. Instalar Restate
cd /root/ultramcp/restate-integration
./install-restate.sh install

# 2. Ejecutar tests
./test-restate-integration.sh all

# 3. Explorar dashboards
ultramcp-restate dashboard

# 4. Experimentar con workflows
curl -X POST http://localhost:8080/chain-of-debate \
  -H "Content-Type: application/json" \
  -d '{"topic": "Test debate", "participants": ["alice", "bob"], "rounds": 2}'
```

**¡Transforma UltraMCP con workflows durables!** 🚀