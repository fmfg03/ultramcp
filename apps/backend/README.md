# MCP Broker - Backend

Este directorio contiene el código fuente del servidor backend para la aplicación MCP Broker.

## Tecnologías

*   Node.js
*   Express.js
*   dotenv (para variables de entorno)
*   cors (para habilitar solicitudes de origen cruzado)
*   axios (para realizar solicitudes HTTP desde los adaptadores)
*   serve-static (para servir los archivos del frontend en producción)
*   `@mendable/firecrawl-js` (SDK para Firecrawl)
*   `@browserbasehq/stagehand` (SDK para Stagehand/Browserbase)
*   `chromadb` (Cliente JS para ChromaDB)
*   `ws` (Cliente WebSocket para Jupyter)
*   `uuid` (Para generar IDs únicos, usado en Jupyter y Scheduler)
*   `@langchain/langgraph` (Para definir y ejecutar flujos de trabajo de agentes)
*   `@langchain/openai` (Para integrar modelos OpenAI en LangGraph)
*   `@langchain/anthropic` (Para integrar modelos Anthropic en LangGraph)
*   `@langchain/google-genai` (Para integrar modelos Google GenAI en LangGraph)
*   `@langchain/core` (Dependencia central de LangChain/LangGraph)
*   `node-cron` (Para la funcionalidad de programación nativa en SchedulerAdapter)
*   `nodemailer` (Para enviar correos electrónicos en EmailAdapter)
*   `@notionhq/client` (SDK oficial para interactuar con la API de Notion en NotionAdapter)

## Estructura

*   `src/config/`: Configuración, principalmente para variables de entorno.
*   `src/services/`: Lógica de negocio principal.
    *   `mcpBrokerService.js`: Gestiona el registro y la ejecución de herramientas a través de los adaptadores.
    *   `orchestrationService.js`: Implementa la lógica de orquestación usando LangGraph. Define un grafo con soporte para múltiples LLMs, roles configurables (Planner, Builder, Judge, Ideators) y dos flujos de trabajo principales (Builder/Judge y Ideation).
*   `src/adapters/`: Clases adaptadoras para interactuar con diferentes servidores MCP y servicios. Incluye:
    *   `getzepAdapter.js`
    *   `firecrawlAdapter.js`
    *   `stagehandAdapter.js`
    *   `chromaAdapter.js`
    *   `cliAdapter.js`
    *   `githubAdapter.js`
    *   `jupyterAdapter.js`
    *   `pythonAdapter.js`
    *   `schedulerAdapter.js`: Permite programar flujos de trabajo utilizando `node-cron`.
    *   `emailAdapter.js`: Permite enviar correos electrónicos utilizando `nodemailer`.
    *   `notionAdapter.js`: Permite interactuar con Notion utilizando el SDK `@notionhq/client`.
*   `src/controllers/`: Controladores Express que manejan las solicitudes entrantes y utilizan los servicios.
*   `src/routes/`: Definiciones de las rutas de la API Express.
*   `src/index.js`: Punto de entrada principal del servidor Express. Configura el middleware, registra adaptadores, monta rutas y sirve el frontend.
*   `.env.example`: Archivo de ejemplo para variables de entorno.
*   `package.json`: Define las dependencias y scripts del proyecto.

## API Endpoints

*   `GET /api/mcp/tools`: Lista todas las herramientas disponibles de los adaptadores registrados.
*   `POST /api/mcp/execute`: Ejecuta una acción específica de una herramienta MCP individualmente.
    *   Body: `{ "toolId": "adapterId/toolName", "params": { ... } }`
*   `POST /api/mcp/orchestrate`: Inicia un flujo de trabajo de orquestación basado en una solicitud de usuario.
    *   Body: `{ "request": "user's natural language request" }`
    *   Respuesta: El resultado final del flujo de trabajo de LangGraph (Builder/Judge o Ideation).

## Orquestación (LangGraph)

El servicio `orchestrationService.js` implementa la lógica de orquestación utilizando LangGraph. Las características clave incluyen:

*   **Multi-LLM:** Soporte para OpenAI, Anthropic (Claude) y Google (Gemini).
*   **Roles Configurables:** Permite asignar LLMs específicos (proveedor y modelo) a diferentes roles mediante variables de entorno:
    *   `PLANNER_LLM_PROVIDER`, `PLANNER_LLM_MODEL`
    *   `BUILDER_LLM_PROVIDER`, `BUILDER_LLM_MODEL` (Opcional, para refinamiento)
    *   `JUDGE_LLM_PROVIDER`, `JUDGE_LLM_MODEL`
    *   `IDEATOR_n_LLM_PROVIDER`, `IDEATOR_n_LLM_MODEL` (n de 1 a 5)
*   **Flujos de Trabajo Dinámicos:**
    *   **Builder/Judge:** Se activa para solicitudes orientadas a tareas. Involucra planificación (`Planner`), ejecución de herramientas (`Builder`) y evaluación (`Judge`), con posibilidad de ciclos de refinamiento.
    *   **Ideation:** Se activa si la solicitud contiene "ideate" o "brainstorm". Los LLMs configurados como `Ideator` generan ideas secuencialmente sobre el tema de la solicitud durante un número configurable de rondas.
*   **Estado del Grafo:** Mantiene el estado de la solicitud, el plan, las herramientas ejecutadas, el feedback, el historial de ideación, etc.

## Configuración

1.  **Variables de Entorno:** Crea un archivo `.env` en el directorio `backend/` basado en `.env.example` para configurar las claves de API y URLs necesarias para los adaptadores y la orquestación. Consulta el `README.md` principal para ver la lista completa de variables, incluyendo las específicas para la configuración de LLMs (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `PLANNER_LLM_*`, `JUDGE_LLM_*`, `IDEATOR_*_LLM_*`, etc.), así como las variables para los nuevos adaptadores:
    *   **EmailAdapter:** `EMAIL_SMTP_HOST`, `EMAIL_SMTP_PORT`, `EMAIL_SMTP_USER`, `EMAIL_SMTP_PASS`, `EMAIL_SMTP_SECURE`, `EMAIL_FROM_ADDRESS`.
    *   **NotionAdapter:** `NOTION_API_KEY`.
    *   **SchedulerAdapter:** No requiere variables de entorno específicas para su funcionamiento básico, pero depende del `orchestrationService` para la ejecución de los flujos de trabajo programados.
    *Nota: Si no se proporcionan las claves/URLs/configuraciones de LLM necesarias, los adaptadores o roles correspondientes podrían no funcionar correctamente, utilizando lógica de placeholder o fallando.* 

## Instalación

Desde el directorio `backend/`, ejecuta:

```bash
npm install
```

## Ejecución

### Modo de Desarrollo

Para ejecutar el backend en modo de desarrollo:

```bash
npm start 
# O usando nodemon si está instalado: nodemon src/index.js
```

El servidor se iniciará, típicamente en el puerto 3001 (o el especificado en `.env`).

### Modo de Producción

En producción, el backend también sirve los archivos estáticos del frontend compilado.

1.  Asegúrate de que el frontend haya sido compilado (ejecutando `npm run build` en el directorio `frontend/`).
2.  Desde el directorio `backend/`, ejecuta:

```bash
npm start
```

El servidor se iniciará y servirá tanto la API como la interfaz de usuario React en el puerto especificado (por defecto 3001).

