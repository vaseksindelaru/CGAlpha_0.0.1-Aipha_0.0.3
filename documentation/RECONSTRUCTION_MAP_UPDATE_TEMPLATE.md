# RECONSTRUCTION_MAP_UPDATE — Template

## Componente
[Nombre del componente reconstruido]

## Fase / Ticket
[EVO-TICKET-XXXX — título]

## 1. Cambios realizados
| Archivo | Cambio | Razón |
|---|---|---|
| `ruta/al/archivo.py` | [breve descripción] | [por qué] |

## 2. Tests

### 2.a — Puerta de Cobertura Base (PRE-RECONSTRUCCIÓN)
Antes de aprobar el CRB de cualquier componente, debe existir una línea de tests que congela el comportamiento actual. Sin esta puerta, el CRB no puede ser aprobado y la Fase de reconstrucción no puede iniciar.

- Cobertura medida sobre el componente ANTES de tocar código: **X%** (umbral mínimo recomendado: 50%, o justificación explícita de impedimento de entorno)
- Tests pasando pre-cambio: **N/N**
- Fecha de medición: [YYYY-MM-DD]
- Si la medición fue bloqueada por entorno (ej. `ImportError` numpy), documentar el error exacto y la sesión de entorno requerida. El bloqueo de entorno **no exime** de la puerta; la aprueba solo tras resolución.

### 2.b — Tests post-cambio
```
[pegar salida de pytest con cobertura]
```

## 3. Decisiones arquitectónicas
- [ ] Ninguna nueva (solo implementación dentro del contrato existente)
- [ ] Nueva decisión documentada en ADR: [ruta al ADR]

## 4. LLM Readability Check (D-010)
Responde con SÍ/NO y una frase de justificación:

1. ¿Un modelo menos capaz puede continuar desde aquí sin reconstruir el contexto completo de esta sesión?  
   **Respuesta:** [SÍ/NO] — [justificación]

2. ¿Los archivos modificados son auto-explicativos sin este RMU?  
   **Respuesta:** [SÍ/NO] — [justificación]

3. ¿Hay decisiones implícitas que deberían convertirse en ADR antes de cerrar?  
   **Respuesta:** [SÍ/NO] — [justificación]

## 5. Estado post-cambio
- Ticket: [EVO-TICKET-XXXX]
- Maturity alcanzada: [MATURITY_X]
- Estado en ciclo: [EXECUTING / IMPLEMENTED / etc.]
- Debt class: [EXPANSION / CONSOLIDATION / EMERGENCY / TOXIC]
- Deuda técnica pendiente: [lista]

## 6. Próximo paso recomendado
[una línea concreta]

## 7. Puerta de Cobertura Base — verificación de cumplimiento
- [ ] La Puerta de Cobertura Base (sección 2.a) fue medida y reportada ANTES de iniciar la Fase de reconstrucción.
- [ ] Si fue bloqueada por entorno, el bloqueo está documentado y la sesión de entorno está agendada antes de cualquier cambio de código.
- [ ] No se aprobó el CRB sin esta puerta.

**Razón de esta puerta:** Exigir un CRB que solo mapea flujos documentados, pero procede a reescribir pipelines sin matriz de tests preexistente, viola la heurística de seguridad (D-008 Causal Closure + D-010 Cognitive Portability). La cobertura post-cambio no detecta regresiones introducidas durante la reconstrucción; solo la línea pre-cambio las hace visibles.
