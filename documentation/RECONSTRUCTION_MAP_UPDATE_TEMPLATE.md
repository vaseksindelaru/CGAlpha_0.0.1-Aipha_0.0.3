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
