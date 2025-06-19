# Attendee + MCP Integration - TODO

## Fase 1: Crear estructura base y extractores de acciones ✅
- [x] Crear directorio attendee_integration
- [x] Implementar actionExtractor.js - Detección de patrones de acción
- [x] Implementar entityExtractor.js - Extracción y enriquecimiento de entidades
- [x] Implementar classificationEngine.js - Clasificación inteligente e intervenciones
- [x] Crear schemas para transcripciones - Estructuras de datos completas
- [x] Testing básico de extractores

## Fase 2: Implementar nodos LangGraph para procesamiento
- [ ] Crear attendee_ingestion_node.py
- [ ] Crear action_extraction_node.py
- [ ] Crear entity_enrichment_node.py
- [ ] Crear classification_node.py
- [ ] Integrar con LLMs locales
- [ ] Testing de nodos individuales

## Fase 3: Crear formatters y dispatchers MCP
- [ ] Implementar mcpPayloadFormatter.js
- [ ] Implementar contextEnricher.js
- [ ] Implementar agentDispatcher.js
- [ ] Crear mcp_dispatch_node.py
- [ ] Integrar con agentes MCP existentes
- [ ] Testing de dispatching

## Fase 4: Integrar validación y logging
- [ ] Implementar validationLayer.js
- [ ] Crear validation_node.py
- [ ] Integrar logging con Supabase
- [ ] Integrar métricas con Langwatch
- [ ] Implementar filtros de seguridad
- [ ] Testing de validación

## Fase 5: Crear agente completo Attendee y testing
- [ ] Crear attendee_complete_agent.py
- [ ] Integrar todos los nodos en grafo
- [ ] Crear endpoint REST para ingestion
- [ ] Testing end-to-end
- [ ] Documentación completa
- [ ] Casos de uso de ejemplo

## Casos de Uso Target:
1. "Francisco, hay que generar el reporte semanal antes del viernes" → Task Creation
2. "Agendemos reunión de seguimiento para el lunes a las 10am" → Calendar Event  
3. "Recordarme revisar el presupuesto mañana" → Notification/Reminder
4. "Se acordó aumentar el presupuesto en 20%" → Decision Logging
5. "Hay que hacer follow-up con el cliente la próxima semana" → Follow-up Task

