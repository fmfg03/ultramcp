# Audit Report

## 1. Adapters Activos y Herramientas Disponibles

### Lista de todos los adapters registrados en `mcpBrokerService`

### Lista de herramientas por adapter (`getTools()`), confirmando que cada una tenga su implementación correspondiente en `executeAction()`

## 2. Input Preprocessor

### ¿Existe `routing_decision`?

### ¿Qué heurísticas usa? ¿Están alineadas con los adapters actuales?

### ¿Dónde ocurre la invocación de este servicio?

## 3. Orchestration Layer

### ¿Utiliza `routing_decision`?

### ¿Llama a `modelRouterService`?

### ¿Llama a `mcpBrokerService.executeTool()` correctamente?

## 4. Model Router Layer

### ¿Qué condiciones están implementadas (task type, payload size, latency, override)?

### ¿Cómo se integra con `orchestrationService`?

## 5. Credenciales

### ¿Qué adaptadores utilizan `credentialsService`?

### ¿Hay credenciales hardcoded?

## 6. Frontend y Telegram

### ¿Ambas consolas (React y Telegram) pueden invocar `/api/orchestrate`?

### ¿Funcionan los logs en Supabase desde ambos canales?

## 7. Supabase Logging

### ¿Se están registrando los comandos con: `command`, `response`, `timestamp`, `agent`, `llm_used`?

## 8. Documentación vs Implementación

### ¿El README.md está alineado con lo que hay en el código?

### ¿Qué funcionalidades están documentadas pero no implementadas aún?

### ¿Qué partes están implementadas pero no documentadas?


## 1. Adapters Activos y Herramientas Disponibles

### Lista de todos los adapters registrados en `mcpBrokerService`

Según el archivo `/home/ubuntu/project_audit_temp/backend/src/server.cjs`, los siguientes adaptadores están registrados en `mcpBrokerService`:

- `FirecrawlAdapter`
- `TelegramAdapter`
- `EmbeddingSearchAdapter`
- `ClaudeWebSearchAdapter`
- `ClaudeToolAgentAdapter`

### Lista de herramientas por adapter (`getTools()`), confirmando que cada una tenga su implementación correspondiente en `executeAction()`

**1. FirecrawlAdapter (`firecrawl`)**
   - Herramientas obtenidas de `getTools()`:
     - `firecrawl/scrapeUrl`: Scrapes a single URL.
     - `firecrawl/crawlUrl`: Initiates a crawl job for a website.
     - `firecrawl/checkCrawlStatus`: Checks the status of a crawl job.
   - Implementación en `executeAction()`: Confirmado. Las tres herramientas tienen lógica correspondiente en `executeAction`.

**2. TelegramAdapter (`telegram`)**
   - Herramientas obtenidas de `getTools()`:
     - `telegram/sendMessage`: Sends a message to a specified Telegram chat ID.
     - `telegram/startPollingUpdates`: Starts polling for new messages from Telegram.
   - Implementación en `executeAction()`: Confirmado. Ambas herramientas tienen lógica correspondiente en `executeAction`.

**3. EmbeddingSearchAdapter (`embedding_search`)**
   - Herramientas obtenidas de `getTools()`:
     - `embedding_search/ingest_document`: Ingests a document (from URL or text) into the Zep embedding store.
     - `embedding_search/search_documents`: Queries the Zep embedding store for semantically similar documents.
   - Implementación en `executeAction()`: Confirmado. Ambas herramientas (`ingest_document` y `search_documents`) tienen lógica correspondiente en `executeAction`.

**4. ClaudeWebSearchAdapter (`claudeWebSearch`)**
   - Herramientas obtenidas de `getTools()`:
     - `claudeWebSearch/webSearch`: Queries Claude with web search enabled.
   - Implementación en `executeAction()`: Confirmado. La herramienta `webSearch` tiene lógica correspondiente en `executeAction`.

**5. ClaudeToolAgentAdapter (`claude_tool_agent`)**
   - Herramientas obtenidas de `getTools()`:
     - `claude_tool_agent/execute_task_with_tools`: Executes a given task by intelligently using a provided set of tools.
   - Implementación en `executeAction()`: Confirmado. La herramienta `execute_task_with_tools` tiene lógica correspondiente en `executeAction`.




## 2. Input Preprocessor

### ¿Existe `routing_decision`?

Sí, el `InputPreprocessorService` (`/home/ubuntu/project_audit_temp/backend/src/services/InputPreprocessorService.js`) genera un objeto `routing_decision` como parte de su salida en el método `process()`. Este objeto contiene `adapter_id`, `confidence`, `reasoning` y `llm_used` (que en este contexto se refiere al LLM usado por el router interno del preprocesador, no necesariamente el LLM final de la tarea).

### ¿Qué heurísticas usa? ¿Están alineadas con los adapters actuales?

El `InputPreprocessorService` utiliza las siguientes heurísticas principales para determinar la ruta:

- **Presencia de archivos**: Si hay archivos en la entrada, sugiere `embedding_search`.
- **Palabras clave para Embedding Search**: Palabras como "search my documents", "find in my knowledge base" dirigen a `embedding_search`.
- **Palabras clave para Web Search**: Palabras como "search for", "what is", "latest news" dirigen a `claude_web_search`.
- **Palabras clave para Tool Agent (explícitas)**: Frases como "book a", "schedule a", "execute task" dirigen a `claude_tool_agent`.
- **Palabras clave para Tool Agent (condicionales + complejidad)**: La presencia de palabras clave condicionales ("if", "then", "when") combinada con una longitud de consulta mayor a 7 palabras también sugiere `claude_tool_agent`.
- **Consultas cortas y simples**: Consultas de menos de 5 palabras sin datos estructurados ni archivos se dirigen a `default_llm_service` (que podría ser manejado por `orchestration_service` para una respuesta directa de LLM).
- **Ruta por defecto**: Si ninguna regla coincide, se dirige a `orchestration_service` como fallback.

Las heurísticas parecen estar razonablemente alineadas con los adaptadores actualmente implementados (`EmbeddingSearchAdapter`, `ClaudeWebSearchAdapter`, `ClaudeToolAgentAdapter`).

### ¿Dónde ocurre la invocación de este servicio?

- **TelegramAdapter**: El `TelegramAdapter` (`/home/ubuntu/project_audit_temp/backend/src/adapters/TelegramAdapter.js`) invoca `inputPreprocessorService.process()` para cada mensaje nuevo recibido a través del bot de Telegram.
- **API Endpoint (implícito)**: Se espera que el `orchestrateController.js` (o similar, que maneja las peticiones a `/api/orchestrate`) invoque este servicio para las entradas recibidas a través de la API HTTP. Revisando `/home/ubuntu/project_audit_temp/backend/src/controllers/orchestrateController.js` (si existe) o las rutas en `/home/ubuntu/project_audit_temp/backend/src/routes/api.cjs` y `/home/ubuntu/project_audit_temp/backend/src/routes/orchestrateRoutes.js` se confirmaría. (Nota: El contenido de estos archivos de rutas/controladores no se ha inspeccionado explícitamente en los pasos anteriores, pero es la ubicación lógica para la invocación desde la API).




## 3. Orchestration Layer

### ¿Utiliza `routing_decision`?

Sí, el `OrchestrationService` (`/home/ubuntu/project_audit_temp/backend/src/services/orchestrationService.js`) recibe el `processedInput` del `InputPreprocessorService`, que incluye el objeto `routing_decision`. El método `processCommand()` en `OrchestrationService` utiliza `routing_decision.adapter_id` para determinar a qué adaptador o lógica dirigir la solicitud.

### ¿Llama a `modelRouterService`?

No, actualmente el `OrchestrationService` **no** invoca explícitamente al `ModelRouterService` para obtener una selección de modelo dinámico. Aunque el `ModelRouterService` está implementado y define varios modelos y heurísticas de selección, el `OrchestrationService` no utiliza su método `routeLLM()`.
La selección del LLM en `OrchestrationService` parece basarse en `processedInput.llm` (que es un campo que puede venir de la solicitud original o ser sugerido por `InputPreprocessorService` en `routing_decision.llm_used`, aunque este último se refiere al LLM del router del preprocesador) o usa un valor por defecto. No hay una llamada activa a `modelRouterService.routeLLM()` para determinar el modelo basado en `taskType`, `payloadSize`, `latencyTolerance`, etc.

### ¿Llama a `mcpBrokerService.executeTool()` correctamente?

Sí, el `OrchestrationService` llama a `mcpBrokerService.executeTool(toolToExecute, paramsForTool)` para ejecutar la herramienta seleccionada en el adaptador correspondiente. El `toolToExecute` se construye concatenando el `targetAdapterId` (de `routing_decision`) con el nombre de la herramienta específica (por ejemplo, `embedding_search/search_documents`). Los parámetros para la herramienta (`paramsForTool`) también se construyen adecuadamente según el adaptador de destino.

Para el `ClaudeToolAgentAdapter`, el `OrchestrationService` también llama a un método interno `_getToolManifestForClaude()` que a su vez utiliza `mcpBrokerService.getAllAdaptersTools()` para construir el manifiesto de herramientas que se pasa al agente Claude.




## 4. Model Router Layer

### ¿Qué condiciones están implementadas (task type, payload size, latency, override)?

El `ModelRouterService` (`/home/ubuntu/project_audit_temp/backend/src/services/modelRouterService.js`) tiene implementada la lógica para seleccionar un modelo LLM basada en las siguientes condiciones en su método `routeLLM()`:

- **`userOverride`**: Si se proporciona un `userOverride` con `provider` y `model`, este tiene la máxima prioridad y se selecciona el modelo especificado si existe en la configuración del router.
- **`costBudget`**: ("lowCost", "balanced", "performance_first") - Se aplican heurísticas para seleccionar modelos más baratos o más potentes según este parámetro. Por ejemplo, "lowCost" tiende a seleccionar "claude-3-haiku" o "gpt-3.5-turbo".
- **`taskType`**: ("summarization", "code_gen", "search", "complex_reasoning", "general_purpose", "quick_response", "web_search_tasks", "research", "creative_content") - Diferentes tipos de tarea influyen en la selección del modelo. Por ejemplo, "complex_reasoning" o "research" tienden a seleccionar "claude-3-opus" o "gpt-4-turbo".
- **`latencyTolerance`**: ("real-time", "low", "medium", "high") - Si se requiere baja latencia ("real-time" o "low"), y el modelo seleccionado inicialmente tiene un perfil de latencia "moderate" o "slow", el router intenta cambiar a un modelo más rápido como "claude-3-haiku" o "gpt-3.5-turbo".
- **`payloadSize`**: (estimado en tokens o caracteres) - Se utiliza en algunas heurísticas, por ejemplo, para tareas de "complex_reasoning", si el `payloadSize` es grande (> 100,000), se favorece "claude-3-opus".

El servicio define una lista de modelos disponibles (`this.models`) con sus características (proveedor, ventana de contexto, coste, soporte de herramientas, fortalezas, perfil de latencia).

### ¿Cómo se integra con `orchestrationService`?

Actualmente, el `ModelRouterService` **no está integrado** con el `OrchestrationService`. Aunque el `ModelRouterService` está completamente implementado con la lógica para `routeLLM()`, el `OrchestrationService` no realiza ninguna llamada a este método para determinar dinámicamente el modelo LLM a utilizar. La selección del LLM en `OrchestrationService` se basa en parámetros de la solicitud original o valores por defecto, sin consultar al `ModelRouterService`.




## 5. Credenciales

### ¿Qué adaptadores utilizan `credentialsService`?

Los siguientes adaptadores intentan utilizar `credentialsService.js` para obtener credenciales (API keys, tokens) si no se encuentran en las variables de entorno:

- **`ClaudeWebSearchAdapter.js`**: Intenta obtener `claude.apiKey`.
- **`ClaudeToolAgentAdapter.js`**: Intenta obtener `anthropic.apiKey` (aunque el código muestra `credentialsService.getCredential("anthropic", "apiKey")`, la variable de entorno que busca es `ANTHROPIC_API_KEY`, que es más genérica que Claude. Debería ser consistente, o `claude.apiKey` si es específico para Claude).
- **`TelegramAdapter.js`**: Intenta obtener `telegram.botToken`.

El `OrchestrationService.js` también intenta inicializar y utilizar `credentialsService.getCredential`, aunque no se especifica para qué credencial particular lo usaría directamente el orquestador en su lógica actual.

El `FirecrawlAdapter.js` utiliza directamente la variable de entorno `FIRECRAWL_API_KEY` y no parece tener un fallback a `credentialsService.js`.

El `EmbeddingSearchAdapter.js` no maneja directamente credenciales de servicios externos como Firecrawl o Zep; delega estas operaciones al `mcpBrokerService`. Las credenciales para estos servicios serían manejadas por sus respectivos adaptadores (si existieran como adaptadores completos registrados en el broker y llamados por el `EmbeddingSearchAdapter`) o, como es el caso de Firecrawl, por el `FirecrawlAdapter` que sí usa una API key. Para Zep, la configuración se basa en `ZEP_API_URL` (según `server.cjs`), que no es una credencial secreta per se, sino una URL de endpoint.

### ¿Hay credenciales hardcoded?

Tras una revisión del código de los adaptadores y servicios principales, no se han observado credenciales (como API keys o tokens secretos) directamente hardcodeadas en los archivos JavaScript. La práctica general es leerlas desde variables de entorno (`process.env`) o intentar obtenerlas a través del `credentialsService.js`.

Es importante asegurar que el `credentialsService.js` en sí mismo no contenga credenciales hardcodeadas y que las obtenga de forma segura (por ejemplo, de una base de datos segura o un servicio de gestión de secretos), lo cual está fuera del alcance de la revisión de estos archivos específicos pero es crucial para la seguridad general del sistema.




## 6. Frontend y Telegram

### ¿Ambas consolas (React y Telegram) pueden invocar `/api/orchestrate`?

- **React Frontend**: Sí. El componente `CommandConsole.jsx` (`/home/ubuntu/project_audit_temp/frontend/src/components/CommandConsole/CommandConsole.jsx`) realiza una llamada `fetch` al endpoint `/api/orchestrate` cuando se envía un comando. La URL es relativa, por lo que asume que el frontend se sirve desde el mismo dominio o está configurado con un proxy para el backend.

- **Telegram**: Sí. El `TelegramAdapter.js` (`/home/ubuntu/project_audit_temp/backend/src/adapters/TelegramAdapter.js`), en su método `executeAction` para la acción `startPollingUpdates`, configura un listener de mensajes (`this.bot.on("message", async (msg) => { ... })`). Dentro de este listener, tras recibir un mensaje de Telegram, invoca a `inputPreprocessorService.process()` y luego a `orchestrationService.processCommand()`. El `orchestrationService` es el que internamente maneja la lógica que sería equivalente a la invocación del endpoint `/api/orchestrate`.

### ¿Funcionan los logs en Supabase desde ambos canales?

- **React Frontend**: El componente `CommandConsole.jsx` intenta enviar logs al backend a través de una llamada `fetch` al endpoint `/api/logs` después de recibir una respuesta del endpoint `/api/orchestrate`. El payload incluye `timestamp`, `command`, `response`, `llm_used`, y `agent_used`. La efectividad de esto depende de la implementación del backend para `/api/logs` y su conexión con Supabase.

- **Telegram**: El `TelegramAdapter.js` no muestra una invocación explícita al endpoint `/api/logs` o a un servicio de logging centralizado después de procesar un comando y enviar una respuesta al usuario. El logging dentro del `TelegramAdapter` parece ser principalmente a través de `console.log()`, `console.error()`, y los métodos de log heredados de `BaseMCPAdapter` (si se usan, aunque no son evidentes en el fragmento de `on("message")`). Si el `orchestrationService` o los adaptadores subsiguientes invocados por Telegram realizan logging a Supabase, entonces indirectamente se registrarían, pero no hay un log directo desde el `TelegramAdapter` para cada interacción de Telegram al estilo de lo que hace el frontend.

La funcionalidad de logging a Supabase desde ambos canales depende de la implementación del endpoint `/api/logs` y de si el flujo de `orchestrationService` (invocado por Telegram) registra la información requerida en Supabase.




## 7. Supabase Logging

### ¿Se están registrando los comandos con: `command`, `response`, `timestamp`, `agent`, `llm_used`?

Sí, el servicio `logService.cjs` (`/home/ubuntu/project_audit_temp/backend/src/services/logService.cjs`) tiene un método `saveLog(logData)` que inserta registros en una tabla `command_logs` en Supabase. 

Los campos que intenta registrar son:
- `command`
- `response` (se asegura de que sea un string, JSON.stringify si es un objeto)
- `timestamp` (utiliza el proporcionado o `new Date().toISOString()`)
- `user` (opcional, `null` si no se proporciona)
- `llm_used`
- `agent_used` (este campo se llama `agent_used` en el `logService.cjs` y en el frontend, mientras que el requisito de auditoría menciona `agent`. Se asume que `agent_used` cumple el propósito de `agent`).

El `CommandConsole.jsx` del frontend llama al endpoint `/api/logs` (que presumiblemente usa este `logService`) con los campos: `timestamp`, `command`, `response` (como JSON stringified), `llm_used`, y `agent_used`.

Por lo tanto, los campos requeridos (`command`, `response`, `timestamp`, `agent` (como `agent_used`), `llm_used`) están siendo gestionados por el `logService` y enviados desde el frontend. La correcta inserción en Supabase depende de que la tabla `command_logs` tenga las columnas correspondientes y de que el cliente Supabase (`supabaseClient.cjs`) esté correctamente configurado y funcional.




## 8. Documentación vs Implementación

### ¿El README.md está alineado con lo que hay en el código?

En general, el archivo `README.md` (`/home/ubuntu/project_audit_temp/README.md`) está bien alineado con la estructura y las funcionalidades implementadas en el código. Describe correctamente:

- La estructura general del proyecto (directorios `backend`, `frontend`, `src`).
- Los servicios principales del backend como `InputPreprocessorService`, `OrchestrationService`, `mcpBrokerService`, `ModelRouterService`, y `credentialsService`, detallando sus roles y características clave.
- Los adaptadores implementados, incluyendo `FirecrawlAdapter`, `TelegramAdapter`, `EmbeddingSearchAdapter`, `ClaudeWebSearchAdapter`, y `ClaudeToolAgentAdapter`, junto con sus herramientas principales.
- La funcionalidad del `InputPreprocessorService` para generar una `routing_decision`.
- El uso de la `routing_decision` por parte del `OrchestrationService`.
- La lógica del `ModelRouterService` para la selección dinámica de LLMs (aunque su integración completa no está activa).
- La gestión de credenciales y el logging a Supabase.
- La funcionalidad del frontend (Command Console) para interactuar con los endpoints `/api/orchestrate` y `/api/logs`.

### ¿Qué funcionalidades están documentadas pero no implementadas aún (o completamente)?

- **Integración completa del `ModelRouterService`**: El `README.md` menciona explícitamente que la integración completa del `ModelRouterService` con el `OrchestrationService` (para que este último utilice `modelRouterService.routeLLM()` para la selección dinámica de modelos) es una tarea para una fase futura (Fase 9). La auditoría confirmó que, aunque el `ModelRouterService` está implementado, el `OrchestrationService` no lo invoca actualmente. Esto está correctamente reflejado en la documentación como una tarea pendiente.
- **Reformulación con LLM en `InputPreprocessorService`**: El `README.md` indica que la capacidad de reformular la entrada del usuario usando un LLM en `InputPreprocessorService` está "simulada". El código (`_rephraseInputWithLLM`) efectivamente devuelve una respuesta simulada. Esto está alineado.
- **Manejo de Archivos en `InputPreprocessorService`**: El `README.md` menciona "Manejo de Archivos (Simulado): Identificación de placeholders o información sobre archivos adjuntos para su futuro procesamiento." El servicio maneja la subida de archivos guardándolos en `UPLOAD_DIR` y usa su presencia para el enrutamiento. La parte "simulada" o "futuro procesamiento" podría referirse a un análisis de contenido más profundo o a la integración de estos archivos en los prompts de los LLM de manera más sofisticada, lo cual no es evidente actualmente más allá de la ingesta en `EmbeddingSearchAdapter`.

### ¿Qué partes están implementadas pero no documentadas (o no con suficiente detalle en el README.md)?

En general, el `README.md` es bastante completo. Las omisiones son menores y corresponden a detalles de implementación que no necesariamente se esperan en un README de alto nivel:

- **Heurísticas específicas de `InputPreprocessorService`**: Aunque el README menciona el "análisis básico de palabras clave", las listas exactas de palabras clave y la lógica detallada de priorización para el enrutamiento no están en el README. Esto es comprensible, ya que son detalles de implementación.
- **Lógica de fallback específica en `OrchestrationService`**: El `OrchestrationService` tiene una heurística específica en su ruta por defecto/fallback donde puede intentar ejecutar `firecrawl/scrapeUrl` si el agente es "builder-judge" y la solicitud contiene "scrape". Este detalle no está en el README.
- **Flujo interno del `TelegramAdapter`**: El `README.md` describe la funcionalidad del `TelegramAdapter`. El flujo interno específico de cómo invoca `inputPreprocessorService` y luego `orchestrationService` no está detallado, lo cual es normal para un README.

En conclusión, la documentación en `README.md` es de buena calidad y refleja con precisión el estado actual del proyecto, incluyendo las funcionalidades que están completas y las que están planificadas para futuras fases.
