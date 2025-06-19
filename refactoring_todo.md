# MCP System Refactoring - Todo List

## Phase 1: Crear servicios de reasoning y reward shells
- [x] 001. Crear reasoningShell.js en backend/src/services/
- [x] 002. Crear rewardShell.js en backend/src/services/
- [ ] 003. Implementar lógica de división de tareas en reasoningShell
- [ ] 004. Implementar lógica de evaluación en rewardShell

## Phase 2: Implementar servicio de memoria y persistencia
- [x] 005. Crear memoryService.js en backend/src/services/
- [x] 006. Crear esquemas de base de datos para sessions, steps, rewards
- [x] 007. Implementar funciones saveStep(), getContext(), saveReward()

## Phase 3: Refactorizar servicio de orquestación
- [x] 008. Refactorizar orchestrationService.js
- [x] 009. Integrar reasoningShell y rewardShell
- [x] 010. Añadir logs entre pasos

## Phase 4: Crear manejo de reintentos y nuevos endpoints
- [x] 011. Crear retryManager.js
- [x] 012. Implementar endpoint /run-task
- [x] 013. Añadir lógica de reintentos automáticos

## Phase 5: Actualizar frontend con vista de orquestación
- [x] 014. Crear componente de vista de orquestación
- [x] 015. Mostrar flujo completo: input → tasks → outputs → feedback → score
- [x] 016. Mostrar información de reintentos

## Phase 6: Probar y validar el sistema completo
- [x] 017. Probar integración completa
- [x] 018. Validar trazabilidad
- [x] 019. Verificar funcionamiento de reintentos

