# Perplexity Integration - TODO

## Fase 1: Crear wrapper base y servicio Perplexity
- [ ] Crear perplexityService.js con múltiples estrategias
- [ ] Implementar headless browser wrapper
- [ ] Crear parser para respuestas y citas
- [ ] Implementar fallbacks (DeepSeek, Serper, Arxiv)
- [ ] Testing básico del servicio
- [ ] Configuración de timeouts y rate limiting

## Fase 2: Implementar nodo LangGraph con conditional logic
- [ ] Crear perplexity_research_node.py
- [ ] Implementar conditional logic para research
- [ ] Crear should_use_research() function
- [ ] Integrar con state management
- [ ] Testing de nodos individuales
- [ ] Optimizar flujo de decisión

## Fase 3: Crear endpoint MCP y herramienta
- [ ] Crear perplexityController.js
- [ ] Implementar /mcp/perplexityAgent endpoint
- [ ] Crear perplexityRoutes.js
- [ ] Integrar con sistema MCP existente
- [ ] Documentar API schema
- [ ] Testing de endpoints

## Fase 4: Integrar con agentes existentes y fallbacks
- [ ] Conectar con reasoning_agent
- [ ] Integrar con builder_agent
- [ ] Crear flujos automáticos
- [ ] Implementar error handling robusto
- [ ] Testing de integración completa
- [ ] Optimizar performance

## Fase 5: Testing completo y observabilidad
- [ ] Integrar con Langwatch
- [ ] Crear métricas de research
- [ ] Testing end-to-end
- [ ] Documentación completa
- [ ] Casos de uso de ejemplo
- [ ] Monitoring y alertas

## Casos de Uso Target:
1. "Analiza las tendencias de IA en 2024" → Research automático + análisis
2. "¿Es cierto que GPT-5 salió?" → Fact-checking con fuentes
3. "Investigar competencia" → Research + reporte estructurado
4. "Resumir artículo sobre blockchain" → Análisis + citas verificables
5. "Qué dice la prensa sobre Tesla" → Sentiment analysis + fuentes

