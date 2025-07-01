# Agents Catalog - MCP System

## 🤖 **Catálogo Completo de Agentes MCP**

El sistema MCP incluye una colección especializada de agentes autónomos, cada uno diseñado para tareas específicas con capacidades únicas de colaboración y mejora continua.

---

## 🎯 **Agentes Principales**

### **🧠 Complete MCP Agent**
**Archivo:** `langgraph_system/agents/complete_mcp_agent.py`

**Propósito:** Agente maestro que coordina y orquesta todos los demás agentes del sistema.

**Capacidades:**
- 🎭 **Coordinación Multi-Agente**: Decide qué agentes usar para cada tarea
- 🔄 **Gestión de Flujo**: Controla el orden y dependencias entre agentes
- 📊 **Agregación de Resultados**: Combina outputs de múltiples agentes
- 🎯 **Optimización de Recursos**: Balancea carga entre agentes disponibles

**Casos de Uso:**
```python
# Tarea compleja que requiere múltiples agentes
"Crear una landing page con research de mercado y documentación"
→ Perplexity Agent (research)
→ Builder Agent (desarrollo)
→ Notion Agent (documentación)
```

**Input Schema:**
```json
{
  "task": "string",
  "complexity": "simple|medium|complex",
  "agents_required": ["agent1", "agent2"],
  "priority": "low|medium|high"
}
```

**Output Schema:**
```json
{
  "result": "object",
  "agents_used": ["agent1", "agent2"],
  "execution_time": "number",
  "quality_score": "number"
}
```

---

### **🧩 Reasoning Agent**
**Archivo:** `langgraph_system/agents/reasoning_agent.py`

**Propósito:** Especializado en análisis, razonamiento lógico y planificación de tareas complejas.

**Capacidades:**
- 🔍 **Análisis de Problemas**: Descompone tareas complejas en subtareas
- 🧠 **Razonamiento Lógico**: Aplica lógica formal y heurísticas
- 📋 **Planificación**: Crea planes de ejecución detallados
- 🎯 **Toma de Decisiones**: Evalúa opciones y selecciona la mejor estrategia

**Casos de Uso:**
```python
# Análisis de requerimientos complejos
"Analizar los requerimientos para un sistema de e-commerce"
→ Identifica componentes necesarios
→ Evalúa tecnologías apropiadas
→ Crea plan de implementación
→ Estima recursos y tiempo
```

**Especialidades:**
- **Problem Decomposition**: Divide problemas grandes en partes manejables
- **Logical Reasoning**: Aplica reglas lógicas y patrones de razonamiento
- **Strategic Planning**: Crea roadmaps y planes de ejecución
- **Risk Assessment**: Identifica y evalúa riesgos potenciales

**Input Schema:**
```json
{
  "problem": "string",
  "context": "object",
  "constraints": ["constraint1", "constraint2"],
  "goals": ["goal1", "goal2"]
}
```

---

### **🏗️ Builder Agent**
**Archivo:** `langgraph_system/agents/builder_agent.py`

**Propósito:** Especializado en construcción, desarrollo y creación de entregables tangibles.

**Capacidades:**
- 💻 **Desarrollo de Software**: Código, aplicaciones, scripts
- 📄 **Generación de Documentos**: Reports, manuales, especificaciones
- 🌐 **Creación Web**: Landing pages, sitios web, aplicaciones
- 🎨 **Diseño y Prototipado**: Mockups, wireframes, prototipos

**Casos de Uso:**
```python
# Desarrollo completo de aplicación
"Crear una aplicación React para gestión de tareas"
→ Analiza requerimientos
→ Diseña arquitectura
→ Genera código base
→ Implementa funcionalidades
→ Crea documentación
```

**Especialidades:**
- **Frontend Development**: React, Vue, Angular, HTML/CSS
- **Backend Development**: Node.js, Python, APIs REST
- **Database Design**: SQL, NoSQL, schemas
- **Documentation**: Technical writing, API docs, user guides
- **Web Design**: Responsive design, UX/UI principles

**Herramientas Integradas:**
- GitHub Adapter (gestión de código)
- Stagehand Adapter (testing web)
- Local LLM Adapter (generación de código)
- Notion Adapter (documentación)

**Input Schema:**
```json
{
  "project_type": "web|mobile|desktop|document",
  "requirements": "string",
  "technology_stack": ["tech1", "tech2"],
  "deliverables": ["deliverable1", "deliverable2"]
}
```

---

### **🔍 Perplexity Agent**
**Archivo:** `backend/src/services/research/perplexityService.js`

**Propósito:** Agente especializado en research automático con fuentes verificables y citas académicas.

**Capacidades:**
- 🌐 **Research Web**: Búsqueda inteligente en tiempo real
- 📚 **Fuentes Académicas**: Acceso a papers y publicaciones
- 🔗 **Citas Verificables**: Referencias con links y metadatos
- 📊 **Síntesis de Información**: Combina múltiples fuentes

**Casos de Uso:**
```python
# Research automático para análisis
"Analizar las tendencias de IA en 2024"
→ Busca información actualizada
→ Verifica fuentes confiables
→ Extrae insights relevantes
→ Genera reporte con citas
```

**Estrategias de Research:**
1. **Headless Browser**: Perplexity.ai directo
2. **API Fallback**: API oficial (cuando esté disponible)
3. **Serper + DeepSeek**: Búsqueda + síntesis con LLM
4. **ArXiv Search**: Papers académicos especializados

**Fallbacks Automáticos:**
- Perplexity Browser → Serper+DeepSeek → ArXiv → Error handling

**Input Schema:**
```json
{
  "query": "string",
  "research_type": "general|academic|news|technical",
  "max_sources": "number",
  "language": "string"
}
```

**Output Schema:**
```json
{
  "answer": "string",
  "citations": [
    {
      "title": "string",
      "url": "string",
      "snippet": "string",
      "index": "number"
    }
  ],
  "confidence": "number",
  "source": "string"
}
```

---

### **🎧 Attendee Agent**
**Archivo:** `attendee_integration/extractors/`

**Propósito:** Análisis inteligente de reuniones con extracción automática de acciones y decisiones.

**Capacidades:**
- 🎤 **Transcripción en Tiempo Real**: Procesa audio de reuniones
- 📋 **Extracción de Acciones**: Identifica tareas y responsables
- 🤝 **Análisis de Decisiones**: Detecta acuerdos y compromisos
- 🗣️ **Intervención Inteligente**: Participa cuando es necesario

**Modos de Operación:**
- **👂 Ears Only**: Escucha y analiza sin intervenir
- **🗣️ Ears & Mouth**: Participa activamente con preguntas y sugerencias

**Casos de Uso:**
```python
# Reunión de planificación de proyecto
Audio → Transcripción → Análisis
→ "Francisco debe generar el reporte para el viernes"
→ Crea tarea automáticamente
→ Asigna a Francisco
→ Establece deadline
→ Notifica por Telegram
```

**Componentes:**
- **Action Extractor**: Detecta patrones de acción en conversaciones
- **Entity Extractor**: Identifica personas, fechas, proyectos
- **Classification Engine**: Clasifica tipos de acción y urgencia
- **Intervention Engine**: Decide cuándo y cómo intervenir

**Tipos de Acciones Detectadas:**
- **Tasks**: "Hay que hacer X"
- **Decisions**: "Se acordó Y"
- **Calendar**: "Agendemos reunión"
- **Reminders**: "Recordar Z"
- **Follow-ups**: "Dar seguimiento"

---

## 🔧 **Agentes de Soporte**

### **📊 Analytics Agent**
**Archivo:** `backend/src/services/langwatchAnalytics.js`

**Propósito:** Recolección y análisis de métricas del sistema.

**Capacidades:**
- 📈 **Métricas de Rendimiento**: Tiempo de respuesta, throughput
- 🎯 **Análisis de Calidad**: Scores de contradicción y mejora
- 📊 **Dashboards**: Visualización de datos en tiempo real
- 🔍 **Debugging**: Trazas detalladas de ejecución

---

### **🔄 Retry Manager Agent**
**Archivo:** `backend/src/services/retryManager.js`

**Propósito:** Gestión inteligente de reintentos y recuperación de errores.

**Capacidades:**
- 🔄 **Retry Inteligente**: Estrategias adaptativas de reintento
- 🛡️ **Circuit Breaker**: Prevención de cascadas de fallos
- 📊 **Backoff Exponencial**: Espaciado inteligente de reintentos
- 🎯 **Error Classification**: Categorización de tipos de error

---

### **🧠 Memory Agent**
**Archivo:** `backend/src/services/memoryService.js`

**Propósito:** Gestión de contexto y memoria del sistema.

**Capacidades:**
- 💾 **Context Management**: Mantiene contexto entre interacciones
- 🔍 **Information Retrieval**: Búsqueda en memoria histórica
- 📚 **Knowledge Base**: Base de conocimiento acumulativo
- 🎯 **Context Injection**: Inyección inteligente de contexto relevante

---

## 🎭 **Agentes Especializados**

### **🔥 Contradiction Agent**
**Archivo:** `backend/src/services/contradictionService.js`

**Propósito:** Mejora explícita de resultados mediante contradicción intencional.

**Capacidades:**
- 🎯 **Quality Assessment**: Evalúa calidad de resultados
- 🔄 **Contradiction Application**: Aplica contradicción estratégica
- 📈 **Improvement Tracking**: Rastrea mejoras logradas
- 🧠 **Pattern Learning**: Aprende patrones de mejora efectiva

**Niveles de Contradicción:**
- **Mild**: Cuestionamiento suave
- **Moderate**: Contradicción directa
- **Extreme**: Contradicción agresiva
- **Adaptive**: Selección automática según contexto

---

### **🌐 Web Automation Agent**
**Archivo:** `backend/src/adapters/stagehendAdapter.js`

**Propósito:** Automatización web y scraping inteligente.

**Capacidades:**
- 🤖 **Browser Automation**: Control programático de navegadores
- 📊 **Data Extraction**: Extracción de datos de sitios web
- 🔍 **Content Analysis**: Análisis de contenido web
- 📱 **Cross-Platform**: Soporte para desktop y mobile

---

## 🔗 **Integración entre Agentes**

### **Flujos Colaborativos:**

**Research → Build:**
```
Perplexity Agent → Builder Agent
(Research de tecnologías) → (Implementación con mejores prácticas)
```

**Meeting → Action:**
```
Attendee Agent → Complete MCP Agent → Builder Agent
(Extrae acción) → (Coordina) → (Ejecuta tarea)
```

**Build → Validate:**
```
Builder Agent → Contradiction Agent → Builder Agent
(Crea resultado) → (Evalúa y contradice) → (Mejora resultado)
```

### **Comunicación Inter-Agente:**
- **Message Passing**: Comunicación asíncrona entre agentes
- **Shared State**: Estado compartido via LangGraph
- **Event System**: Sistema de eventos para coordinación
- **Result Aggregation**: Combinación de resultados múltiples

---

## 📊 **Métricas y Observabilidad**

### **Por Agente:**
- **Execution Time**: Tiempo promedio de ejecución
- **Success Rate**: Tasa de éxito de tareas
- **Quality Score**: Puntuación de calidad de resultados
- **Resource Usage**: Uso de CPU, memoria, tokens

### **Sistema General:**
- **Agent Utilization**: Uso de cada agente
- **Collaboration Patterns**: Patrones de colaboración
- **Error Rates**: Tasas de error por agente
- **Improvement Metrics**: Métricas de mejora via contradicción

---

## 🚀 **Extensibilidad**

### **Agregar Nuevos Agentes:**
1. Crear archivo en `langgraph_system/agents/`
2. Implementar interface estándar
3. Registrar en orchestration service
4. Configurar en LangGraph workflow

### **Personalizar Agentes Existentes:**
1. Modificar prompts y comportamiento
2. Ajustar parámetros de configuración
3. Agregar nuevas capacidades
4. Integrar herramientas adicionales

**El catálogo de agentes MCP proporciona un ecosistema completo y extensible para automatización inteligente con capacidades únicas de colaboración y mejora continua.** 🎯

