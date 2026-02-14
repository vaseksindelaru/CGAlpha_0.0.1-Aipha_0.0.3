# Fase 8 - Deep Causal v0.3 (Capítulo de Transición)

## Decisión Oficial
**Sí, continuamos.**  
La base actual (Ghost Architect v0.2.2) es válida y se mantiene.  
La evolución a v0.3 será **incremental**, sin reescribir el núcleo.

## Principio Rector
No romper arquitectura para “mejorar”.  
Primero evidencias, luego cambios mínimos.

## Alcance Permitido (IN)
1. Fortalecer ingesta de `order_book_features.jsonl` (calidad de datos).
2. Mejorar clasificación `fakeout` vs `structure_break` con evidencia micro.
3. Mejorar evaluación out-of-sample (OOS) para validar causalidad real.
4. Mantener `cgalpha auto-analyze` como entrada estable.

## Alcance Prohibido (OUT)
1. Refactor total de `simple_causal_analyzer.py`.
2. Cambiar estructura de carpetas o rutas núcleo.
3. Introducir dependencias pesadas no justificadas.
4. Quitar fallback heurístico.

## Checklist Específico v0.3
- [ ] Inyección por `trade_id` o nearest timestamp (±250ms) validada.
- [ ] `BLIND_TEST` marcado cuando no hay evidencia válida.
- [ ] Prompt Deep Causal usa contexto micro completo (book depth + regime + news + MFE/MAE).
- [ ] Distinción operacional:
  - [ ] `fakeout` (ruido microestructural)
  - [ ] `structure_break` (cambio estructural)
- [ ] Métricas mínimas en reporte:
  - [ ] `causal_accuracy_oos`
  - [ ] `precision_fakeout`
  - [ ] `precision_structure_break`
  - [ ] `noise_rejection_rate`
  - [ ] `action_uplift`
- [ ] Gate visible en CLI:
  - [ ] `PROCEED_V03` o `HOLD_V03`
- [ ] Compatibilidad total con `cgalpha auto-analyze`.

## Definición de Éxito del Capítulo
Se considera Fase 8 completada cuando:
1. Los gates de datos y causalidad pasan de forma reproducible.
2. El sistema distingue ruido vs estructura con métricas OOS aceptables.
3. No hay ruptura del flujo actual ni degradación de estabilidad.

## Secuencia de Trabajo Recomendada
1. Auditoría de dataset real (cobertura, lag, blind ratio).
2. Ajuste fino de reglas/LLM prompt (sin refactor masivo).
3. Validación OOS en ventana temporal separada.
4. Cierre con reporte comparativo v0.2.2 vs v0.3.

## Cierre
Este capítulo no busca “reinventar” CGAlpha.  
Busca convertir una base sólida en un motor causal más preciso, con control de riesgo y trazabilidad.
