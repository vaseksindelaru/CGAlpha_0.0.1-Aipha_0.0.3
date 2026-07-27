---
type: development-index
project: CGAlpha
tags: [proyecto/cgalpha, development, s2, proximos-pasos]
created: 2026-07-27
---

# 🔧 Desarrollo — S2 (Próximos Pasos)

> Área para la fase activa de desarrollo de cgAlpha_0.0.1.
> Mientras `learning/` es teórico, esta es la práctica que transforma teoría en código.

---

## 🔍 Paso inmediato de investigación (previo a cualquier desarrollo nuevo)

### Discrepancia de `max_price_since_detection`

**Contexto**: El test de `ClearanceInstrument` espera `max_price_since_detection = 10100.0`, pero el valor actual del sistema es `10200`. Hay 100 puntos de diferencia.

#### Plan de investigación

1. **Localizar el cálculo**
   - Buscar en `triple_coincidence.py` dónde se actualiza `max_price_since_detection`
   - Buscar en `ShadowTrader/ClearanceInstrument` el mismo campo
   - Determinar si el valor `10200` proviene de un tick de precio real de Binance o de un offset de inicialización/redondeo

2. **Verificar el seed/fixture del test**
   - El test espera `10100.0`
   - ¿El fixture usa un precio de entrada fijo?
   - Si el precio de entrada es `10100` y el máximo observado es `10200`, el test podría tener el valor de entrada wrong (`10000` en vez de `10100`), no el código

3. **Revisar la ventana temporal**
   - `max_price_since_detection` se resetea al detectar una nueva zona
   - ¿El test simula exactamente una ventana donde el precio sube 100 puntos desde el entry, o hay un escenario donde el precio sube más?

4. **Si es un bug real**
   - Ajustar el test o el código según corresponda
   - Documentar en ADR (`aipha_memory/identity/ADR-...`)
   - Correr test suite: `pytest cgalpha_v3/tests/ -q`

5. **Si es un cambio intencional de comportamiento**
   - Verificar si afecta el umbral de `max_clearance_atr`
   - Revisar si los filtros de rebote prematuro que dependen de él siguen siendo válidos con el nuevo offset
   - Actualizar test y documentar como cambio intencional

6. **Si es un cambio intencional que afecta gobernanza**
   - Actualizar SAFETY_THRESHOLS si es necesario
   - Crear nuevo ADR para el cambio de comportamiento

---

## 📋 Roadmap S2 (desarrollos pendientes)

| # | Tarea | Estado | Dependencias |
|---|-------|--------|-------------|
| 1 | Investigar discrepancia `max_price_since_detection` | 🔴 PENDIENTE | Ninguna |
| 2 | [Proxima tarea según resultado de 1] | ⬜ NO DEFINIDA | 1 |
| 3 | [Proxima tarea según resultado de 2] | ⬜ NO DEFINIDA | 2 |

> **Nota**: No hay "siguiente paso genérico". Hay un punto concreto de investigación — la discrepancia de 100 en `max_price_since_detection` — que es la única grieta genuina en lo demás un sistema que ha evolucionado mucho más allá de lo documentado.

---

## 🧪 Testing en S2

Cada fix debe seguir la Triple Barrera:
```
Aplicar cambio → pytest cgalpha_v3/tests/ -q → solo git commit si todos pasan
```

El conteo de tests que pasa es el único criterio de aceptación.