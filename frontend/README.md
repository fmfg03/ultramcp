# MCP Broker - Frontend

Este directorio contiene el código fuente de la interfaz de usuario (frontend) para la aplicación MCP Broker, construida con React y Vite.

## Tecnologías

*   React
*   Vite (como herramienta de construcción y servidor de desarrollo)
*   JavaScript (ES6+)
*   CSS (estilos básicos en línea)

## Estructura

*   `src/components/`: Componentes React reutilizables.
    *   `code/MCPToolSelector.jsx`: Componente principal que:
        *   Obtiene la lista de herramientas disponibles desde el backend.
        *   Muestra un selector desplegable agrupado por adaptador.
        *   Renderiza dinámicamente campos de entrada para los parámetros de la herramienta seleccionada.
        *   Permite al usuario ingresar parámetros (texto, JSON, código).
        *   Envía la solicitud de ejecución al backend.
        *   Muestra el resultado o el error de la ejecución.
*   `src/services/`: (Actualmente vacío, la lógica de API está en el componente).
*   `src/App.jsx`: Componente principal de la aplicación que organiza la interfaz (incluye `MCPToolSelector`).
*   `src/main.jsx`: Punto de entrada de la aplicación React.
*   `index.html`: Plantilla HTML principal.
*   `vite.config.js`: Archivo de configuración de Vite. Incluye la configuración del proxy para redirigir las solicitudes `/api` al backend durante el desarrollo.
*   `package.json`: Define las dependencias y scripts del proyecto.
*   `dist/`: Directorio que contiene los archivos estáticos compilados para producción (generado por `npm run build`).

## Instalación

Desde el directorio `frontend/`, ejecuta:

```bash
npm install
```

## Ejecución (Desarrollo)

Para ejecutar el frontend en modo de desarrollo con recarga en caliente:

```bash
npm run dev
```

Vite iniciará un servidor de desarrollo, típicamente en `http://localhost:5173`. Gracias a la configuración del proxy en `vite.config.js`, las solicitudes a `/api/...` serán redirigidas automáticamente al servidor backend (que se asume está corriendo en `http://localhost:3001`).

**Nota sobre Pruebas sin Proxy:** Durante las pruebas recientes donde el frontend se sirvió manualmente (`python -m http.server`), el código de `MCPToolSelector.jsx` fue modificado temporalmente para usar URLs absolutas (`http://localhost:3001/api/...`) en las llamadas `fetch`. Para el desarrollo normal usando `npm run dev`, las URLs relativas (`/api/...`) deberían funcionar correctamente debido al proxy de Vite.

## Compilación (Producción)

Para compilar la aplicación para producción:

```bash
npm run build
```

Esto generará los archivos estáticos optimizados en el directorio `dist/`. Estos archivos están destinados a ser servidos por el servidor backend Node.js en un entorno de producción.

