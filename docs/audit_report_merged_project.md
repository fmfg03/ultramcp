# Audit Report - Merged Project MCP Broker

**Fecha de Auditoría:** 2025-05-09
**Auditor:** Manus AI
**Versión del Proyecto:** Fusión de Fase 1-8 con componentes legacy y `ModelRouterService` integrado en `OrchestrationService` (LangGraph).

## Resumen Ejecutivo

Esta auditoría técnica evalúa el estado actual del proyecto MCP Broker después de la fusión de varias fases de desarrollo, incluyendo la integración de componentes "legacy" y la reciente incorporación del `ModelRouterService` dentro de un `OrchestrationService` rediseñado con LangGraph. El objetivo es validar el alcance de las capacidades implementadas, identificar discrepancias, y proporcionar recomendaciones para futuras mejoras y estabilización.

Los hallazgos clave indican una arquitectura de backend significativamente evolucionada con la introducción de LangGraph en la orquestación, lo que permite flujos de trabajo más complejos y dinámicos. La integración del `ModelRouterService` para la selección de LLMs es un avance positivo. Sin embargo, existen áreas que requieren atención, particularmente en la cohesión entre el `InputPreprocessorService` y el nuevo `OrchestrationService`, la finalización de la implementación de todos los adaptadores legacy, la robustez de las pruebas, y la actualización completa de la documentación.

## 1. Adapters Activos y Herramientas Disponibles

### 1.1. ¿Qué adaptadores están actualmente activos y qué herramientas exponen cada uno?

*   **Respuesta:** Basado en el análisis de los archivos en `/home/ubuntu/project/backend/src/adapters/` y el `mcpBrokerService.js`:
    *   `ClaudeToolAgentAdapter.js`: Expone `claude_tool_agent/execute_task_with_tools` para la ejecución de tareas complejas utilizando un conjunto de herramientas definidas en un manifiesto, interactuando con la API de Claude. Utiliza `credentialsService` para la API key de Anthropic y `mcpBrokerService` para ejecutar las herramientas delegadas.
    *   `ClaudeWebSearchAdapter.js`: Expone `claudeWebSearch/webSearch` para realizar búsquedas web utilizando la API de Claude y su herramienta interna `anthropic-search`. Utiliza `credentialsService` para la API key de Claude.
    *   `EmbeddingSearchAdapter.js`: Expone `embedding_search/ingest_document` y `embedding_search/search_documents` para interactuar con un almacén de embeddings (Zep). Las operaciones se delegan al `mcpBrokerService` si es necesario para interactuar con otros servicios como Firecrawl para la obtención de contenido.
    *   `TelegramAdapter.js`: Expone `telegram/sendMessage` y `telegram/startPollingUpdates`. Procesa mensajes entrantes y los envía al `InputPreprocessorService` y luego al `OrchestrationService`. Utiliza `credentialsService` para el token del bot.
    *   `baseMCPAdapter.js`: Es una clase base abstracta que define la interfaz común (`getId`, `getTools`, `executeAction`, y métodos de logging) para todos los adaptadores. No expone herramientas directamente.
    *   `chromaAdapter.js`: Parece ser un adaptador para interactuar con ChromaDB. Expone `chroma/add_documents`, `chroma/query_collection`, `chroma/create_collection`, `chroma/delete_collection`. (Requiere revisión de su registro en `mcpBrokerService` y uso real).
    *   `cliAdapter.js`: Expone `cli/execute_command` para ejecutar comandos de shell. Extiende `BaseMCPAdapter`.
    *   `emailAdapter.js`: Expone `email/send_email` para enviar correos electrónicos utilizando nodemailer. Requiere variables de entorno para la configuración SMTP. Extiende `BaseMCPAdapter`.
    *   `firecrawlAdapter.js`: Expone `firecrawl/scrapeUrl`, `firecrawl/crawlUrl`, y `firecrawl/checkCrawlStatus` para interactuar con el servicio Firecrawl. Utiliza la variable de entorno `FIRECRAWL_API_KEY`.
    *   `getzepAdapter.js`: Adaptador para interactuar con Zep para la gestión de memoria y embeddings. Expone `getzep/add_memory`, `getzep/get_memory`, `getzep/search_memory`, `getzep/add_collection`, `getzep/get_collection_documents`. (Requiere revisión de su registro en `mcpBrokerService` y uso real).
    *   `githubAdapter.js`: Expone `github/get_repo_content` para obtener contenido de archivos de repositorios de GitHub utilizando el CLI `gh`. Requiere `GITHUB_TOKEN`. Extiende `BaseMCPAdapter`.
    *   `jupyterAdapter.js`: Expone herramientas como `jupyter/list_kernels`, `jupyter/start_kernel`, `jupyter/get_kernel_info`, `jupyter/stop_kernel`, y `jupyter/execute_code` para interactuar con un Jupyter Kernel Gateway. Requiere URL del gateway y token. Extiende `BaseMCPAdapter`.
    *   `notionAdapter.js`: Adaptador para interactuar con Notion. (Archivos `notionAdapter.js` y `notion_adapter_design.md` existen. Funcionalidad y herramientas específicas por confirmar).
    *   `pythonAdapter.js`: Expone `python/execute_code` para ejecutar código Python en un entorno aislado. (Implementación detallada y aislamiento por confirmar).
    *   `schedulerAdapter.js`: Adaptador para programar tareas. (Archivos `schedulerAdapter.js` y `scheduler_adapter_design.md` existen. Funcionalidad y herramientas específicas por confirmar).
    *   `stagehandAdapter.js`: Adaptador para interactuar con Stagehand para la generación de UI. (Funcionalidad y herramientas específicas por confirmar).

### 1.2. ¿Se han integrado correctamente los adaptadores "legacy" (Jupyter, Email, Git, CLI, etc.) en el `mcpBrokerService`?

*   **Respuesta:** El `mcpBrokerService.js` tiene un mecanismo de registro (`registerAdapter`) y una función `executeTool(toolId, params)` que delega la ejecución al método `executeAction(toolId, params)` del adaptador correspondiente, identificado a partir del `toolId` (e.g., `adapterId/toolName`).
    Los adaptadores legacy examinados (`cliAdapter.js`, `jupyterAdapter.js`, `emailAdapter.js`, `githubAdapter.js`) extienden `BaseMCPAdapter` y exponen sus herramientas a través de `getTools()` y la lógica de ejecución a través de `executeAction()`. Para que estén *correctamente integrados*, deben ser instanciados y registrados con el `mcpBrokerService` en el punto de inicio de la aplicación (e.g., `server.cjs`).
    *Revisión de `server.cjs` (del proyecto fusionado) es necesaria para confirmar cuáles de estos adaptadores legacy están siendo activamente registrados e instanciados.* Sin este registro, el `mcpBrokerService` no los conocerá.

## 2. Input Preprocessor (`InputPreprocessorService.js`)

### 2.1. ¿Cómo funciona el `InputPreprocessorService`?

*   **Respuesta:** El `InputPreprocessorService.js` procesa la entrada cruda del usuario:
    *   **Refraseo (Simulado):** Identifica si la entrada necesita reformulación (longitud, palabras clave condicionales) y simula una llamada LLM.
    *   **Manejo de Archivos:** Procesa adjuntos, sanitiza, verifica tamaño/extensión, mueve a `uploads/`, y verifica scripts en Markdown.
    *   **Extracción de Datos Estructurados:** Intenta extraer JSON, CSV, URLs.
    *   **Determinación de Intención y Enrutamiento:** Genera `routing_decision` (`adapter_id`, `confidence`, `reasoning`) basada en palabras clave, archivos y datos estructurados.

### 2.2. ¿Qué tipo de "routing decision" genera y cómo se utiliza?

*   **Respuesta:** Genera `routing_decision` con `adapter_id` (e.g., `embedding_search`, `claude_web_search`, `claude_tool_agent`, `default_llm_service`, `orchestration_service`), `confidence`, `reasoning`, `llm_used`.
    En la versión fusionada del `orchestrationService.js` (LangGraph), esta `routing_decision` no está directamente conectada al flujo principal del grafo. El `entryNode` del grafo toma su propia decisión inicial. La `routing_decision.adapter_id` no se usa para seleccionar la herramienta inicial en el `plannerNode`. Esta es una desconexión clave.

## 3. Orchestration Layer (`orchestrationService.js`)

### 3.1. ¿Cómo ha cambiado el `orchestrationService.js` después de la fusión con el código legacy que incluye el StateGraph de LangGraph?

*   **Respuesta:** Completamente reescrito usando LangGraph (`StateGraph`). Define `agentState` y nodos (`entryNode`, `plannerNode`, `builderNode`, `judgeNode`, `ideatorNode`, `finalizerNode`). Soporta flujos de "constructor/juez" y "ideación". La ejecución de herramientas se delega al `mcpBrokerService` en `builderNode`. La selección de LLMs usa `ModelRouterService`.

### 3.2. ¿Cómo se integra el `InputPreprocessorService` con este nuevo `orchestrationService`?

*   **Respuesta:** Integración indirecta. El `orchestrationService` recibe la `request` (presumiblemente del preprocesador), pero su `entryNode` decide el flujo (ideación vs. constructor/juez) independientemente de `routing_decision.adapter_id`. El `adapter_id` del preprocesador no guía la selección de la primera herramienta en el grafo. Esto es una brecha.

### 3.3. ¿Cómo se integra el `ModelRouterService` con este nuevo `orchestrationService`?

*   **Respuesta:** Profundamente integrado. `ModelRouterService` se instancia y su método `routeLLM()` es llamado por `configureLlmRole` en `orchestrationService` para cada rol de LLM (Planner, Judge, Builder, Ideators). Los parámetros para `routeLLM` incluyen `taskType` y placeholders para `payloadSize`, `latencyTolerance`, `costBudget`. La salida (`provider`, `model`, `temperature`) se usa para inicializar/reutilizar clientes LLM con las API keys de `process.env`. Hay fallback a `process.env` si el router falla.

## 4. Model Router Layer (`modelRouterService.js`)

### 4.1. ¿El `modelRouterService.js` sigue siendo relevante y funcional en el contexto del `orchestrationService.js` basado en LangGraph?

*   **Respuesta:** Sí, es altamente relevante y funcional. Se utiliza activamente para la selección dinámica de LLMs para los roles en LangGraph.

### 4.2. ¿Cómo se invoca y utiliza su salida (provider, model, temperature) dentro del `orchestrationService.js`?

*   **Respuesta:** Invocado por `modelRouter.routeLLM(routerParams)` en `configureLlmRole`. La salida (`provider`, `model`, `temperature`) se usa para determinar el proveedor, API key, e inicializar el cliente LLM con el `modelName` y `temperature`. Se cachean instancias LLM.

## 5. Credenciales (`credentialsService.js`)

### 5.1. ¿Qué mecanismos de seguridad y acceso a credenciales utiliza el `credentialsService.js`?

*   **Respuesta:** El `credentialsService.js` (ubicado en `/home/ubuntu/project/src/services/credentialsService.js`) es un placeholder. Actualmente, solo define una estructura de clase con un constructor que loguea su inicialización y un método `getCredential(serviceName, credentialType)` que devuelve `null`. **No implementa ningún mecanismo real de obtención segura de credenciales.** Simplemente actúa como una interfaz que podría, en el futuro, conectarse a un almacén seguro.

### 5.2. ¿Cómo se integran los diferentes adaptadores (nuevos y legacy) con este servicio para obtener las claves API necesarias?

*   **Respuesta:** Varios adaptadores intentan usar `credentialsService.getCredential()` como fallback si no encuentran las API keys en `process.env`. Dado que `getCredential()` siempre devuelve `null` en la implementación actual, este fallback **no es funcional**. Los adaptadores dependen enteramente de las variables de entorno para las credenciales.
    *   `ClaudeToolAgentAdapter.js`: Intenta `credentialsService.getCredential("anthropic", "apiKey")`.
    *   `ClaudeWebSearchAdapter.js`: Intenta `credentialsService.getCredential("claude", "apiKey")`.
    *   `TelegramAdapter.js` (del proyecto fusionado): No muestra un uso explícito de `credentialsService` en su código actual; depende de `process.env.TELEGRAM_BOT_TOKEN`.

## 6. Frontend y Telegram

### 6.1. ¿El frontend (`CommandConsole.jsx`) sigue siendo compatible con el backend actual después de la fusión y los cambios en la orquestación?

*   **Respuesta:** El `CommandConsole.jsx` envía solicitudes a `/api/orchestrate`. El `server.cjs` del proyecto fusionado define esta ruta y la dirige a `orchestrateController.handleOrchestrationRequest`. Este controlador, a su vez, llama a `inputPreprocessorService.process()` y luego a `orchestrationService.processCommand()`. El `orchestrationService.processCommand()` ahora invoca el grafo de LangGraph.
    *   **Compatibilidad Parcial:** Si bien el endpoint es invocado, la *naturaleza* de la respuesta del nuevo `orchestrationService` (basado en LangGraph) puede ser diferente de lo que el frontend esperaba originalmente, especialmente si el frontend fue diseñado para un flujo más simple de solicitud-respuesta directa de herramienta. El `finalizerNode` del grafo construye una respuesta, pero su formato y cómo se alinea con las expectativas del frontend necesitarían ser verificados. El frontend espera un JSON con un campo `response` o `error`.

### 6.2. ¿El `TelegramAdapter.js` funciona correctamente con el flujo de orquestación actual, incluyendo el `InputPreprocessorService` y el `ModelRouterService`?

*   **Respuesta:** El `TelegramAdapter.js` (del proyecto fusionado) en su listener de mensajes, llama a `inputPreprocessorService.process()` y luego a `orchestrationService.processCommand(processedInput, msg.chat.id)`. Esto significa que sí se integra con el `InputPreprocessorService` y el `OrchestrationService` (que a su vez usa `ModelRouterService`). La funcionalidad depende de que `orchestrationService.processCommand()` maneje correctamente la invocación del grafo y devuelva una respuesta que el `TelegramAdapter` pueda enviar de vuelta al usuario.

## 7. Supabase Logging (`logService.cjs`)

### 7.1. ¿Sigue funcionando el logging de comandos y respuestas a Supabase con la nueva estructura de orquestación?

*   **Respuesta:** El `logService.cjs` está implementado y puede registrar datos en Supabase si está configurado con `SUPABASE_URL` y `SUPABASE_KEY`. El `orchestrateController.js` (invocado por `/api/orchestrate`) llama a `logService.logInteraction()` después de recibir la respuesta del `orchestrationService`. Esto sugiere que las interacciones a través del frontend (que usa `/api/orchestrate`) deberían ser logueadas.
    Para Telegram, el `TelegramAdapter` llama directamente al `orchestrationService`. Si el `orchestrationService` o los nodos dentro del grafo de LangGraph no invocan explícitamente al `logService` para las interacciones de Telegram, estas podrían no registrarse de la misma manera. El `logService` no parece ser invocado directamente por `TelegramAdapter` después de obtener la respuesta final.

## 8. Documentación vs Implementación (`README.md`)

### 8.1. ¿El `README.md` refleja con precisión el estado actual del proyecto fusionado?

*   **Respuesta:** El `README.md` (actualizado para reflejar la integración de `ModelRouterService` en `OrchestrationService`) es parcialmente preciso. Describe la nueva arquitectura de LangGraph en `OrchestrationService` y el uso de `ModelRouterService`. Sin embargo, la interacción (o falta de ella) entre la `routing_decision` del `InputPreprocessorService` y el flujo de LangGraph no está claramente documentada. La lista de adaptadores y su estado actual (implementados, en diseño, registrados) también podría necesitar más detalle.

### 8.2. ¿Hay discrepancias entre la documentación y el código implementado?

*   **Respuesta:**
    *   **Integración `InputPreprocessorService` y `OrchestrationService`**: El `README.md` podría implicar una conexión más directa de la `routing_decision` del preprocesador con la selección de herramientas en el orquestador de LangGraph, lo cual no es el caso actualmente.
    *   **`CredentialsService`**: La documentación o las expectativas podrían sugerir un servicio de credenciales funcional, pero la implementación actual es un placeholder.
    *   **Registro de Adaptadores Legacy**: El `README.md` menciona adaptadores legacy, pero su registro activo en `mcpBrokerService` necesita confirmación en `server.cjs` para que sean funcionales.

## 9. Pruebas y Estabilidad

### 9.1. ¿Existen pruebas unitarias o de integración para los componentes clave?

*   **Respuesta:** Se creó `test_orchestration_model_router.js` para la integración `ModelRouterService` en `OrchestrationService`. Falló debido a una dependencia faltante (`@langchain/langgraph`), indicando problemas de configuración del entorno de prueba o dependencias no instaladas. No hay evidencia de un conjunto exhaustivo de pruebas unitarias o de integración para el proyecto fusionado, especialmente para el complejo `OrchestrationService` y los diversos adaptadores.

### 9.2. ¿Qué tan estable es el sistema en general después de la fusión?

*   **Respuesta:** La estabilidad es cuestionable. La dependencia faltante en las pruebas, la desconexión entre el preprocesador y el orquestador de LangGraph, el `CredentialsService` no funcional, y la necesidad de verificar el registro de todos los adaptadores sugieren que se requiere trabajo significativo para alcanzar un estado estable y completamente funcional.

## 10. Próximos Pasos y Recomendaciones

### 10.1. ¿Cuáles son los próximos pasos críticos para estabilizar y mejorar el proyecto?

*   **Respuesta:**
    1.  **Resolver Dependencias y Entorno:** Asegurar que todas las dependencias (e.g., `@langchain/langgraph`) estén correctamente instaladas y configuradas en los entornos de desarrollo, prueba y producción. Ejecutar `npm install` en el directorio `backend`.
    2.  **Integrar `InputPreprocessorService` con `OrchestrationService` (LangGraph):** Modificar el `plannerNode` o el `entryNode` del `OrchestrationService` para que considere la `routing_decision.adapter_id` del `InputPreprocessorService` al determinar el plan inicial o la primera herramienta a ejecutar, especialmente si la confianza es alta.
    3.  **Implementar `CredentialsService`:** Reemplazar el placeholder actual con una implementación funcional y segura para la gestión de credenciales, o asegurar que todas las credenciales se manejen consistentemente a través de variables de entorno y que esto esté documentado.
    4.  **Registro y Verificación de Adaptadores:** Revisar `server.cjs` para asegurar que todos los adaptadores implementados (especialmente los legacy como Jupyter, Email, Git, CLI, Chroma, Zep, Python, Scheduler, Notion, Stagehand) estén siendo correctamente instanciados y registrados con el `mcpBrokerService`. Completar la implementación de adaptadores que son solo stubs o diseños si son necesarios.
    5.  **Pruebas Exhaustivas:** Desarrollar y ejecutar pruebas unitarias y de integración para todos los componentes críticos, incluyendo cada adaptador, el `InputPreprocessorService`, `ModelRouterService`, `OrchestrationService` (con sus flujos de LangGraph), y `mcpBrokerService`.
    6.  **Logging Consistente:** Asegurar que las interacciones a través de todos los canales (Frontend, Telegram) se registren consistentemente en Supabase a través del `logService.cjs`. Esto podría requerir invocar `logService` desde el `TelegramAdapter` o dentro del `OrchestrationService` de manera más explícita.

### 10.2. ¿Qué recomendaciones se pueden hacer para futuras fases de desarrollo?

*   **Respuesta:**
    1.  **Documentación Continua:** Mantener la documentación (`README.md` y comentarios en el código JSDoc) actualizada a medida que se realizan cambios. Documentar claramente la arquitectura y los flujos de datos.
    2.  **Gestión de Configuración:** Centralizar y mejorar la gestión de configuración para URLs de servicios, parámetros de LLM por defecto, y otras configuraciones de la aplicación.
    3.  **Monitoreo y Métricas:** Implementar monitoreo y métricas para rastrear el rendimiento de los LLMs, la tasa de éxito de las herramientas, y la salud general del sistema.
    4.  **Seguridad:** Realizar una revisión de seguridad completa, incluyendo la sanitización de entradas, la protección contra vulnerabilidades comunes, y asegurar el acceso a APIs y servicios.
    5.  **Interfaz de Frontend:** Revisar y potencialmente rediseñar la interfaz del frontend para alinearla mejor con las capacidades del backend basado en LangGraph, permitiendo interacciones más complejas y visualización de los flujos de trabajo.
    6.  **Desarrollo Modular:** Continuar desarrollando adaptadores de forma modular, asegurando que sean fácilmente registrables y testeables independientemente.
    7.  **Refinamiento del `ModelRouterService`:** Expandir las capacidades del `ModelRouterService` con heurísticas más sofisticadas, y considerar la posibilidad de que aprenda de interacciones pasadas para mejorar sus decisiones de enrutamiento.


