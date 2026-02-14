# Capítulo 10 - Execution Engine (Paper-First, Live-Gated)

## Decisión de Arranque
**Estado actual:** avanzar en diseño e integración controlada.  
**Estado de despliegue real:** `HOLD` para Live/Hybrid hasta que `proceed_v03 = true`.

Esto evita romper la arquitectura y respeta la Constitución:
- Deep Causal Gate obligatorio antes de ejecución real.
- Sin refactor masivo.

## Objetivo del Capítulo
Conectar la capa estratégica (Ghost Architect) con la capa de ejecución (Execution Engine) en dos modos:
1. `Paper` (habilitado desde el inicio).
2. `Live/Hybrid` (bloqueado por gate hasta readiness real).

## Precondiciones Técnicas (No negociables)
1. `cgalpha auto-analyze` debe emitir:
   - `data_alignment`
   - `causal_metrics`
   - `readiness_gates`
2. Para liberar Live/Hybrid:
   - `readiness_gates.data_quality_pass = true`
   - `readiness_gates.causal_quality_pass = true`
   - `readiness_gates.proceed_v03 = true`
3. Persistencia y trazabilidad:
   - Reporte causal guardado en `aipha_memory/evolutionary/causal_reports/`
   - Señales y decisiones auditables (sin data inventada).

## Plan de Implementación (Incremental)

### Etapa 1: Paper Connector
- Consumir salida de `auto-analyze`.
- Traducir hipótesis/propuestas a acciones simuladas.
- Registrar cada decisión en memoria operativa.
- No enviar órdenes reales.

### Etapa 2: Risk Envelope
- Añadir límites previos a ejecución:
  - size máximo
  - pérdida diaria máxima
  - kill switch lógico
- Si gate causal falla: forzar Paper-only.

### Etapa 3: Live Gate Hook
- Hook único de autorización:
  - Si `proceed_v03 = false` -> bloquear Live/Hybrid.
  - Si `proceed_v03 = true` -> permitir transición gradual.

## Checklist de Aprobación
- [ ] Paper mode funcional end-to-end.
- [ ] Live/Hybrid bloqueado cuando gate causal falla.
- [ ] Logs completos de decisión y ejecución.
- [ ] Sin ruptura de `cgalpha auto-analyze`.
- [ ] Compatibilidad `aipha` y `cgalpha` mantenida (alias coexistentes).

## Compatibilidad de Nombres (Unificación sin Fricción)
- `cgalpha` = comando principal de sistema.
- `aipha` = alias de usuario legado, mantenido.
- No renombrar todo el proyecto en esta fase.

## Criterio de “Go Live”
Solo cuando exista evidencia repetible en datos reales de:
1. cobertura de microestructura suficiente,
2. blind ratio controlado,
3. calidad causal aprobada,
4. `PROCEED_V03` sostenido.

Hasta entonces, **Paper-first**.
