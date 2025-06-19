 # MCP Broker & Orchestration Engine

Este proyecto implementa un "MCP Broker", una aplicación full-stack diseñada para integrar y gestionar múltiples servidores que siguen el Protocolo de Contexto del Modelo (MCP - Model Context Protocol). Proporciona una API unificada y una interfaz de usuario simple para interactuar con diferentes herramientas MCP, así como una capa de orquestación avanzada para ejecutar flujos de trabajo colaborativos utilizando múltiples LLMs y herramientas reales.

## Estructura del Proyecto

```
mcp-broker/
├── backend/        # Servidor Node.js (Express)
│   ├── src/
│   │   ├── config/     # Configuración (variables de entorno, JSON de adaptadores)
│   │   ├── services/   # Lógica de negocio (broker, adaptadores, orquestación, credenciales, preprocesador de entrada, enrutador de modelos)
│   │   ├── adapters/   # Adaptadores específicos para servidores MCP y herramientas externas
│   │   ├── controllers/ # Manejadores de rutas Express
│   │   ├── routes/     # Definiciones de rutas API
│   │   ├── middleware/ # Middleware de Express (e.g., errorHandler.js, validationMiddleware.js, authMiddleware.js)
│   │   ├── utils/      # Utilidades (e.g., adapterLoader.js, AppError.js, retryUtils.js, logger.js, metrics.js, dockerService.js)
│   │   ├── validation/ # Esquemas de validación (e.g., Zod)
│   │   ├── database/   # Scripts SQL y lógica de inicialización de BD (e.g. create_command_logs_table.sql)
│   │   └── server.cjs  # Punto de entrada del backend
│   ├── logs/         # Directorio para archivos de log (error.log, combined.log, exceptions.log, rejections.log)
│   ├── .env.example
│   ├── package.json
│   └── README.md
├── frontend/       # Aplicación React (Vite)
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── App.jsx
│   ├── dist/
│   ├── vite.config.js
│   ├── package.json
│   └── README.md
├── src/            # Código fuente compartido o de nivel raíz (actualmente supabaseAdapter está aquí)
│   └── adapters/
│   └── services/
├── config/         # Configuración a nivel de proyecto (e.g., JSON de adaptadores)
│   └── adapter_config.json
└── README.md         # Este archivo
```

## Descripción General

El MCP Broker actúa como un intermediario inteligente que facilita la comunicación y la colaboración entre diversos agentes y herramientas basados en el Protocolo de Contexto del Modelo. Su objetivo es simplificar la integración de múltiples LLMs y servicios especializados, permitiendo la creación de flujos de trabajo complejos y automatizados.

*   **Backend (Node.js con Express):**
    *   Proporciona una API RESTful para todas las interacciones con el sistema.
    *   Gestiona el registro y la configuración de adaptadores para diferentes servicios MCP y herramientas externas.
    *   Implementa la lógica de orquestación de flujos de trabajo utilizando LangGraph, permitiendo la colaboración entre múltiples agentes y herramientas.
    *   Maneja la persistencia de datos (configuraciones, logs, credenciales) utilizando Supabase como backend de base de datos principal y archivos JSON como fallback.
    *   Incorpora medidas de seguridad robustas, incluyendo autenticación, autorización, validación de entradas y sandboxing para la ejecución de adaptadores sensibles.
    *   Cuenta con un sistema avanzado de manejo de errores y logging estructurado para mejorar la resiliencia y la observabilidad.
    *   **Servicios Clave (`backend/src/services/`, `backend/src/utils/`, `backend/src/middleware/`):**
        *   `InputPreprocessorService.js`: Analiza y enruta las entradas del usuario al flujo de orquestación o herramienta adecuada.
        *   `orchestrationService.js`: Gestiona la ejecución de flujos de trabajo complejos definidos en LangGraph, coordinando LLMs y herramientas.
        *   `mcpBrokerService.js`: Maneja el registro, la configuración y la ejecución de acciones de los adaptadores MCP.
        *   `ModelRouterService.js`: Selecciona dinámicamente el LLM más adecuado para una tarea específica basado en criterios definidos.
        *   `credentialsService.js`: Gestiona de forma segura las credenciales necesarias para interactuar con servicios externos.
        *   `logService.cjs` (ahora integrado principalmente a través de `logger.js` y `supabaseAdapter.js`): Anteriormente para logging, ahora las funciones de logging de comandos se manejan en `supabaseAdapter.js` y el logging general por `logger.js`.
        *   `adapterLoader.js` (`backend/src/utils/`): Carga y registra adaptadores desde la base de datos o archivos de configuración al inicio de la aplicación.
        *   `AppError.js` (`backend/src/utils/`): Clase de error personalizada para estandarizar los errores en toda la aplicación, facilitando el manejo y la depuración.
        *   `retryUtils.js` (`backend/src/utils/`): Utilidad para reintentar operaciones propensas a fallos transitorios con una estrategia de backoff exponencial.
        *   `logger.js` (`backend/src/utils/`): Módulo de logging centralizado basado en Winston para logging estructurado en JSON, rotación de logs y múltiples transportes (consola, archivos).
        *   `metrics.js` (`backend/src/utils/`): Módulo para la recolección de métricas de la aplicación (actualmente placeholder, con planes de integración con Prometheus).
        *   `dockerService.js` (`backend/src/utils/`): Servicio para gestionar la ejecución de adaptadores sensibles en contenedores Docker aislados, mejorando la seguridad.
        *   `errorHandler.js` (`backend/src/middleware/`): Middleware global de Express para capturar, manejar y formatear errores de manera centralizada y consistente.
        *   `validationMiddleware.js` (`backend/src/middleware/`): Middleware para validar los cuerpos de las solicitudes API y parámetros utilizando esquemas Zod, previniendo datos malformados o maliciosos.
        *   `authMiddleware.js` (`backend/src/middleware/`): Middleware para manejar la autenticación basada en JWT y la autorización básica basada en roles, protegiendo los endpoints de la API.
    *   **`supabaseAdapter.js`** (`src/adapters/`): Encapsula la lógica de interacción con Supabase, incluyendo la inicialización de tablas (credenciales, logs de comandos, registros de adaptadores) y operaciones CRUD.
*   **Frontend (React con Vite):**
    *   Proporciona una interfaz de usuario para interactuar con el broker, enviar comandos y visualizar resultados.
    *   (Actualmente el desarrollo del frontend está en una fase inicial y no es el foco principal).

## Características Clave

1.  **Integración de Múltiples LLMs y Herramientas:** Permite conectar y utilizar diversos LLMs (OpenAI, Anthropic, modelos locales) y herramientas especializadas a través de una API unificada.
2.  **Orquestación Avanzada con LangGraph:** Utiliza LangGraph para definir y ejecutar flujos de trabajo complejos donde múltiples agentes (LLMs) y herramientas colaboran para resolver tareas.
3.  **Adaptadores MCP Flexibles:** Implementa un sistema de adaptadores para interactuar con diferentes servidores que siguen el Protocolo de Contexto del Modelo, así como con APIs externas.
4.  **Preprocesamiento y Enrutamiento Inteligente de Entradas:** Analiza las solicitudes del usuario para determinar el flujo de orquestación o la herramienta más adecuada.
5.  **Enrutador de Modelos Dinámico:** Capacidad para seleccionar el LLM óptimo para una tarea específica en tiempo de ejecución.
6.  **Gestión Segura de Credenciales:** Almacena y gestiona de forma segura las credenciales necesarias para los adaptadores y servicios externos, utilizando Supabase.
7.  **Persistencia de Logs de Comandos:** Registra los comandos ejecutados y sus resultados en Supabase para auditoría y análisis.
8.  **Persistencia de Adaptadores:** Las configuraciones de los adaptadores registrados se almacenan en Supabase y se cargan al inicio, con un fallback a un archivo `adapter_config.json`.

### 9. Manejo Avanzado de Errores y Resiliencia

Se ha implementado un sistema robusto y estandarizado para el manejo de errores en todo el backend, mejorando la resiliencia y la depuración del sistema. Esta arquitectura se centra en la previsibilidad, la información contextual y la capacidad de recuperación ante fallos.

*   **Objetos de Error Estandarizados (`AppError.js`):
    *   Se utiliza una clase `AppError` personalizada que extiende la clase `Error` nativa de JavaScript. Esta clase es fundamental para la estandarización de errores en toda la aplicación.
    *   Permite encapsular información crucial para cada error, incluyendo:
        *   `message`: Una descripción clara y legible del error.
        *   `statusCode`: El código de estado HTTP apropiado para la respuesta API (e.g., 400, 401, 404, 500).
        *   `errorCode`: Un código de error interno, único y específico de la aplicación, para facilitar la identificación y el seguimiento de tipos de error particulares (e.g., "VALIDATION_ERROR", "DB_CONNECTION_FAILED", "LLM_API_TIMEOUT").
        *   `isOperational`: Un booleano que distingue entre errores operativos (esperados y manejables, como una entrada de usuario incorrecta) y errores de programación o del sistema (inesperados, que indican un fallo en el código o en una dependencia crítica).
        *   `details`: Un objeto o cadena opcional para proporcionar contexto adicional o datos específicos sobre el error, útil para la depuración.
    *   Se espera que todos los errores operativos generados intencionalmente por los servicios y controladores sean instancias de `AppError` para asegurar la consistencia.

*   **Middleware Global de Errores (`errorHandler.js`):
    *   Un middleware global de Express, `globalErrorHandler`, se registra en `server.cjs` después de todas las demás rutas y middlewares. Esto asegura que actúe como un colector central para todos los errores que ocurren durante el ciclo de vida de una solicitud.
    *   Intercepta todos los errores pasados a través de `next(error)` desde los controladores o aquellos no capturados que Express propaga automáticamente.
    *   Formatea una respuesta JSON consistente y predecible para el cliente API:
        *   `status`: "fail" (para errores del cliente, típicamente códigos 4xx) o "error" (para errores del servidor, típicamente códigos 5xx).
        *   `message`: El mensaje descriptivo del error, tomado de `AppError.message` o un mensaje genérico para errores no operativos en producción.
        *   `errorCode`: El código interno del error (si está presente en `AppError.errorCode`).
        *   `details`: Detalles adicionales (si están presentes en `AppError.details` y el entorno no es producción para errores no operativos).
    *   En modo de desarrollo (`process.env.NODE_ENV === 'development'`), el manejador puede incluir más detalles en la respuesta, como el stack trace completo, para facilitar la depuración.
    *   En producción, los errores no operativos o aquellos sin un `AppError` específico devuelven un mensaje genérico (e.g., "Internal Server Error") para no exponer detalles sensibles de la implementación o posibles vulnerabilidades.
    *   Este middleware también es responsable de registrar el error utilizando el servicio de logging centralizado (`logger.js`), incluyendo todos los detalles relevantes.

*   **Mecanismos de Reintento (`retryUtils.js`):
    *   Se ha creado una utilidad `retryOperation` en `backend/src/utils/retryUtils.js`. Esta función implementa una lógica de reintentos robusta con una estrategia de backoff exponencial y jitter para evitar la sobrecarga en reintentos sucesivos.
    *   Permite configurar el número máximo de reintentos y el retardo inicial.
    *   Se aplica selectivamente a operaciones que son propensas a fallos transitorios y que son seguras de reintentar (idempotentes o donde el reintento no causa efectos secundarios no deseados):
        *   Llamadas a servicios externos de LLM (e.g., OpenAI, Anthropic) dentro de los nodos del `orchestrationService.js` (como Planner, Refactorer, Judge), ya que estos pueden fallar debido a problemas de red temporales o sobrecarga del servicio API del LLM.
        *   Operaciones de persistencia en la base de datos (e.g., `persistAdapterRegistration` en `mcpBrokerService.js` al interactuar con Supabase), para manejar desconexiones breves o picos de carga en la base de datos.

*   **Propagación Consistente de Errores:
    *   Los controladores (ubicados en `backend/src/controllers/`, como `mcpController.js`, `orchestrateController.js`, `logController.js`, `authController.js`) están diseñados para capturar errores provenientes de las llamadas a los servicios.
    *   Utilizan `next(new AppError(...))` para errores operativos conocidos o `next(error)` para propagar errores inesperados (que serán capturados y estandarizados por el `globalErrorHandler`).
    *   Los servicios (en `backend/src/services/`) han sido refactorizados para lanzar o propagar instancias de `AppError` cuando ocurren errores operativos. Para errores inesperados de dependencias (e.g., una librería externa), estos se envuelven en un `AppError` con `isOperational = false` si es necesario antes de propagarlos hacia arriba.

*   **Degradación Agraciada (Graceful Degradation):
    *   El sistema está diseñado para manejar la indisponibilidad de ciertos componentes o servicios sin un colapso total, siempre que sea posible.
    *   **LLMs no disponibles (`orchestrationService.js`):** Si un LLM esencial para una tarea de orquestación no está configurado o su API no responde (incluso después de reintentos), se genera un `AppError` específico (e.g., con statusCode 503 y errorCode `LLM_UNAVAILABLE`). El grafo de orquestación (LangGraph) está diseñado para tener nodos de manejo de errores o rutas alternativas si un paso crítico falla.
    *   **Supabase no disponible:** Si las credenciales de Supabase no están configuradas o la conexión falla durante el inicio, el servidor registra advertencias claras (`logger.warn`) y continúa operando en un modo degradado. Funcionalidades que dependen de la base de datos (como la persistencia de adaptadores o el logging de comandos) pueden fallar o estar limitadas, pero el sistema intenta recurrir a configuraciones locales (e.g., `adapter_config.json` para `adapterLoader.js`) cuando es posible.
    *   **Fallos de adaptadores individuales:** Errores durante la carga, inicialización o la obtención de herramientas de un adaptador individual se registran (`logger.error`), pero el `mcpBrokerService.js` intenta continuar operando con los demás adaptadores que sí funcionan correctamente.

*   **Registro Mejorado de Errores:
    *   El `globalErrorHandler` utiliza el `logger.js` (Winston) para registrar detalles comprensivos de todos los errores que maneja, incluyendo el stack trace, `requestId`, y cualquier información adicional del `AppError`.
    *   Los servicios y nodos de orquestación también utilizan el logger para registrar errores en su contexto específico, proporcionando información valiosa para la depuración y el monitoreo del sistema.
    *   Los logs de error se escriben en archivos dedicados (e.g., `logs/error.log`, `logs/exceptions.log`) para facilitar su revisión y análisis.

### 10. Seguridad

La seguridad es un pilar fundamental en el diseño y la implementación del MCP Broker. Se han incorporado múltiples capas de defensa para proteger la plataforma, los datos de los usuarios y la integridad de las operaciones.

*   **Autenticación y Autorización (`authController.js`, `authMiddleware.js`, `authRoutes.js`):
    *   **Autenticación Basada en JWT:** Se ha implementado un sistema de autenticación robusto utilizando JSON Web Tokens (JWT) en conjunto con Supabase Auth para la gestión de usuarios y la emisión de tokens.
        *   **Registro de Usuarios (`/auth/register`):** Permite a nuevos usuarios crear cuentas de forma segura. Las contraseñas se almacenan hasheadas por Supabase.
        *   **Inicio de Sesión (`/auth/login`):** Verifica las credenciales del usuario contra Supabase Auth y, si son válidas, emite un JWT (access token) y un refresh token.
        *   **Refresh Token (`/auth/refresh-token`):** Permite a los usuarios obtener un nuevo access token utilizando un refresh token válido, sin necesidad de reingresar credenciales, mejorando la experiencia de usuario y la seguridad al limitar la vida útil de los access tokens.
    *   **Middleware de Autenticación (`authMiddleware.js`):
        *   Un middleware (`protectRoute`) verifica la validez del JWT presente en el encabezado `Authorization` (tipo Bearer) de las solicitudes a rutas protegidas.
        *   Si el token es válido, extrae la información del usuario (e.g., ID de usuario) y la adjunta al objeto `req` para que esté disponible en los controladores subsecuentes.
        *   Si el token es inválido, está ausente o ha expirado, el middleware rechaza la solicitud con un error 401 (No Autorizado).
    *   **Autorización (Base):
        *   El `authMiddleware.js` incluye una función `authorize(...roles)` que sirve como base para la autorización basada en roles. Aunque la gestión detallada de roles y permisos puede expandirse, esta función permite restringir el acceso a ciertas rutas o funcionalidades solo a usuarios con roles específicos.
        *   Actualmente, la protección se centra en asegurar que solo usuarios autenticados puedan acceder a las funcionalidades principales del broker.

*   **Validación Exhaustiva de Entradas (`validationMiddleware.js`, `validation/` schemas):
    *   Se utiliza la librería Zod para definir esquemas de validación para todas las entradas de las API (cuerpos de solicitud, parámetros de ruta, queries).
    *   Se ha creado un `validationMiddleware.js` que se aplica a las rutas API. Este middleware utiliza los esquemas Zod correspondientes para validar los datos de la solicitud antes de que lleguen a los controladores.
    *   Los esquemas de validación se encuentran en el directorio `backend/src/validation/` (e.g., `authSchemas.js`, `logSchemas.js`, `mcpSchemas.js`, `orchestrationSchemas.js`).
    *   Esta validación previene una amplia gama de ataques, incluyendo inyección de datos, y asegura la integridad de los datos procesados por el sistema.
    *   Si la validación falla, el middleware responde con un error 400 (Bad Request) y detalles sobre los campos inválidos.

*   **Sandboxing de Adaptadores (`dockerService.js`, adaptadores sensibles):
    *   Los adaptadores que ejecutan código externo o comandos del sistema potencialmente peligrosos (e.g., `cliAdapter`, `githubAdapter` para ciertas operaciones, `code_interpreter.js` como herramienta LangChain, y el `jupyterAdapter` para ejecución de código Python) operan dentro de contenedores Docker aislados.
    *   El `dockerService.js` gestiona la creación, ejecución y limpieza de estos contenedores efímeros.
    *   Características del Sandboxing:
        *   **Imágenes Docker Configurables:** Se pueden especificar imágenes Docker base para cada tipo de adaptador, permitiendo entornos de ejecución a medida.
        *   **Límites de Recursos:** Se pueden configurar límites de CPU y memoria para cada contenedor, previniendo el abuso de recursos.
        *   **Timeouts de Ejecución:** Se establecen timeouts para las operaciones dentro del contenedor, evitando que procesos colgados afecten al sistema principal.
        *   **Aislamiento de Red y Sistema de Archivos:** Los contenedores operan con un acceso restringido a la red y al sistema de archivos del host, minimizando el impacto de código malicioso.
        *   **Manejo Robusto de Errores:** Errores dentro del contenedor (incluyendo timeouts) son capturados y propagados de forma segura al sistema principal.
    *   Este enfoque de sandboxing es crucial para mitigar los riesgos asociados con la ejecución de código o comandos provenientes de fuentes no completamente confiables o generados por LLMs.

*   **Protección contra Vulnerabilidades Comunes:
    *   **CORS (Cross-Origin Resource Sharing):** Configurado en `server.cjs` para permitir solicitudes solo desde orígenes confiables (configurable, actualmente abierto para desarrollo).
    *   **Seguridad de Dependencias:** Se recomienda el uso regular de `npm audit` para identificar y mitigar vulnerabilidades conocidas en las dependencias del proyecto.
    *   **HTTPS:** Aunque la terminación SSL/TLS se maneja típicamente a nivel de balanceador de carga o proxy inverso en producción, la aplicación está diseñada para funcionar detrás de dicho proxy. Es imperativo que todo el tráfico en producción se sirva exclusivamente sobre HTTPS.

*   **Gestión de Secretos:
    *   Las claves de API, credenciales de base de datos y otros secretos se gestionan a través de variables de entorno, cargadas mediante el paquete `dotenv` desde un archivo `.env` (que no debe incluirse en el control de versiones).
    *   Se recomienda el uso de soluciones de gestión de secretos más robustas (e.g., HashiCorp Vault, AWS Secrets Manager, Azure Key Vault) para entornos de producción.

*   **Prácticas de Desarrollo Seguro:
    *   Se sigue el principio de menor privilegio al configurar permisos.
    *   Se revisa el código para identificar posibles vulnerabilidades antes de los despliegues.

**Recomendaciones Adicionales para Producción:**
*   **Rate Limiting y Protección contra Brute-Force:** Implementar rate limiting en los endpoints de API, especialmente en los de autenticación, para prevenir ataques de denegación de servicio y intentos de fuerza bruta.
*   **Cabeceras de Seguridad HTTP:** Implementar cabeceras HTTP de seguridad como Content Security Policy (CSP), X-Content-Type-Options, X-Frame-Options, Strict-Transport-Security (HSTS).
*   **Auditorías de Seguridad Regulares:** Realizar auditorías de seguridad y pruebas de penetración periódicas.
*   **Monitoreo de Seguridad y Alertas:** Configurar el sistema de logging y monitoreo para detectar y alertar sobre actividades sospechosas o intentos de brecha.

### 11. Logging Estructurado y Métricas (Fase Inicial)

Se ha implementado la Fase 1 de un sistema de logging y métricas avanzado para mejorar la observabilidad y la depuración del sistema.

*   **Logging Estructurado con Winston (`logger.js`):
    *   Se utiliza la librería Winston para un logging robusto y configurable.
    *   Todos los logs se emiten en formato JSON, facilitando su análisis y procesamiento por sistemas externos.
    *   Cada entrada de log incluye campos consistentes como `timestamp`, `level`, `message`, y `requestId` (para trazabilidad).
    *   Se han configurado múltiples transportes:
        *   Consola: Para desarrollo y depuración, con salida coloreada y simplificada.
        *   Archivos: `logs/error.log` (solo errores), `logs/combined.log` (todos los niveles), `logs/exceptions.log` (excepciones no capturadas), `logs/rejections.log` (promesas no manejadas).
        *   Los archivos de log tienen rotación automática por tamaño y número de archivos.
    *   Se ha reemplazado el uso de `console.log` en todo el backend por el nuevo logger.
*   **Trazabilidad de Solicitudes (Request ID):
    *   Se genera un `requestId` (UUID v4) único para cada solicitud HTTP entrante.
    *   Este `requestId` se incluye en todos los logs relevantes generados durante el procesamiento de esa solicitud, permitiendo rastrear el flujo de una operación a través de diferentes componentes.
*   **Logging de Solicitudes HTTP (Morgan):
    *   Se utiliza Morgan, integrado con el stream de Winston, para loguear todas las solicitudes HTTP entrantes, incluyendo método, URL, status, tiempo de respuesta y tamaño del contenido.
*   **Módulo de Métricas Inicial (`metrics.js`):
    *   Se ha creado un módulo `metrics.js` como placeholder para la recolección de métricas.
    *   Actualmente define una estructura básica para métricas como tiempos de respuesta de API, tiempos de ejecución de adaptadores, latencia de LLMs, conteos de uso y tasas de error.
    *   Incluye funciones placeholder como `incrementCounter` y `recordHistogramValue`.
    *   La intención es integrar este módulo con Prometheus en fases posteriores para la recolección y almacenamiento de métricas.

**Próximos Pasos para Logging y Métricas (Según `monitoring_logging_todo.md`):**
*   **Fase 2:** Implementación completa de la recolección de métricas de rendimiento y uso (tiempos de respuesta, ejecución, latencia de LLM, conteos de uso, tasas de error, costos de LLM).
*   **Fase 3:** Configuración de la infraestructura de monitoreo (Prometheus, Grafana) y creación de dashboards.
*   **Fase 4:** Implementación de tracing avanzado con OpenTelemetry.
*   **Fase 5:** Desarrollo de un dashboard de monitoreo simple integrado en la aplicación.

## Configuración e Inicio

Para configurar y ejecutar el backend del MCP Broker:

1.  **Clonar el Repositorio:** (Si aplica)
2.  **Variables de Entorno:**
    *   Navegar a la carpeta `backend`.
    *   Copiar `.env.example` a `.env`.
    *   Completar las variables de entorno en `.env`:
        *   `BACKEND_PORT`: Puerto para el servidor backend (e.g., 3001).
        *   `SUPABASE_URL`: URL de tu instancia de Supabase.
        *   `SUPABASE_KEY`: Clave de servicio (anónima o de servicio, según los permisos necesarios) de Supabase.
        *   `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.: Claves API para los LLMs que se vayan a utilizar.
        *   Credenciales específicas para adaptadores (e.g., `FIRECRAWL_API_KEY`, `TELEGRAM_BOT_TOKEN`).
        *   `LOG_LEVEL`: Nivel de logging para Winston (e.g., `info`, `debug`).
        *   `JWT_SECRET`: Un secreto fuerte y único para firmar los JWTs (si no se usa Supabase Auth para la firma).
        *   `JWT_EXPIRES_IN`: Tiempo de expiración para los JWTs (e.g., `1h`, `7d`).
3.  **Instalar Dependencias:**
    ```bash
    cd backend
    npm install
    ```
4.  **Iniciar el Servidor:**
    ```bash
    npm start
    ```
    El servidor se iniciará y automáticamente intentará:
    *   Conectar con Supabase (si está configurado).
    *   Crear/verificar las tablas necesarias en Supabase (`credentials`, `command_logs`, `adapter_registrations`).
    *   Cargar adaptadores persistidos desde Supabase o `config/adapter_config.json`.

## Flujo de Trabajo Típico (Actualizado)

1.  **Usuario/Cliente envía una solicitud a un endpoint API del MCP Broker.**
    *   Ejemplo: `POST /api/orchestrate` con una tarea compleja.
2.  **Middlewares Iniciales:**
    *   Se genera un `requestId`.
    *   Logging de la solicitud HTTP (Morgan + Winston).
    *   Autenticación (`authMiddleware.js`): Verifica el JWT.
    *   Validación de Entrada (`validationMiddleware.js`): Valida el cuerpo de la solicitud contra el esquema Zod.
3.  **Controlador (`orchestrateController.js`):**
    *   Recibe la solicitud validada.
    *   Llama al `orchestrationService.js` para manejar la tarea.
4.  **Servicio de Orquestación (`orchestrationService.js`):
    *   Utiliza LangGraph para ejecutar un flujo de trabajo definido.
    *   El flujo puede involucrar:
        *   Llamadas a LLMs (a través del `ModelRouterService.js` si es necesario) para planificación, generación de código/contenido, juicio, etc.
        *   Ejecución de herramientas a través del `mcpBrokerService.js` (que a su vez llama a los adaptadores correspondientes).
        *   Nodos de reintento, refactorización, aprobación o escalada.
5.  **Broker y Adaptadores (`mcpBrokerService.js`, `adapters/`):
    *   Si una herramienta necesita ser ejecutada, el `mcpBrokerService` identifica el adaptador correcto.
    *   El adaptador interactúa con el servicio externo o ejecuta la lógica local (posiblemente en un sandbox Docker si es sensible).
    *   Los resultados se devuelven al servicio de orquestación.
6.  **Respuesta y Logging Final:**
    *   El servicio de orquestación compila el resultado final.
    *   El controlador envía la respuesta al cliente.
    *   Todos los errores son capturados y manejados por el `globalErrorHandler.js`, que también los registra.
    *   Los logs de comandos y otros eventos relevantes se registran en Supabase y/o archivos locales.

## Próximos Pasos y Mejoras Potenciales

(La lista de próximos pasos del usuario sigue siendo relevante, y se han completado algunos puntos)

*   **Validación Completa de Persistencia en Supabase:** Asegurar que todas las interacciones con Supabase sean robustas y manejen casos borde.
*   **Gestión de Archivos Real:** Implementar la subida, almacenamiento y recuperación de archivos para los adaptadores que lo necesiten.
*   **Interfaz de Usuario Avanzada:** Desarrollar el frontend para ofrecer una experiencia de usuario completa.
*   **Más Adaptadores y Herramientas:** Expandir la biblioteca de adaptadores para integrar más servicios y herramientas.
*   **Persistencia de Estado del Grafo:** Implementar la capacidad de guardar y reanudar el estado de las ejecuciones de LangGraph.
*   **Testing Exhaustivo:** Desarrollar un conjunto completo de pruebas unitarias y de integración para todos los componentes, incluyendo flujos de error, seguridad y logging.
*   **Mecanismo de Migración de Base de Datos Formal:** Implementar una herramienta como Knex.js o TypeORM para gestionar las migraciones de esquema de la base de datos de forma controlada.
*   **Endpoint de Health Check:** Implementar el endpoint `/health` para monitorear el estado de la aplicación y sus dependencias críticas.
*   **Monitoreo y Logging Avanzado:** (Fase 1 completada, Fases 2-5 pendientes según `monitoring_logging_todo.md`)
    *   Completar la implementación de métricas (Prometheus/Grafana).
    *   Integrar OpenTelemetry para tracing distribuido.
    *   Desarrollar dashboards de monitoreo.
*   **Mejoras de Seguridad Adicionales:** Implementar rate limiting, cabeceras de seguridad HTTP, y considerar auditorías de seguridad.


