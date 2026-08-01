—
type: development-note
project: CGAlpha
tags: [proyecto/cgalpha, development, s2, max-price-since-detection, bug-investigation]
created: 2026-07-27
status: VERIFIED-IN-LIVE
confidence: alta
---

# 🔬 max_price_since_detection — Investigación Verificada

> **Hallazgo**: Discrepancia de 100 puntos (10200.0 obtenido vs 10100.0 esperado).
> **Fecha de verificación**: 2026-07-27, contra repo clonado.
> **Fuente**: Investigación del LLM externo + confirmación local.

## Datos

| Valor | Fuente |
|---|---|
| **Esperado** | 10100.0 (fixture del test) |
| **Obtenido** | 10200.0 (determinista, cada ejecución) |
| **Valor real en idx=0** | 10015.0 (medido con instrumentación) |
| **Valor real en idx=10** | 10100.0 (zona "nace" aquí) |
| **Valor en idx=13** | 10100.0 (retest detectado en idx=13) |
| **Valor final (post-padding)** | 10200.0 (high más alto del dataset, incluyendo velas de padding) |

## Mecanismo exacto (verificado contra código de producción)

### Contexto: el test inyecta una zona antes del loop

```python
# test_clearance_instrumentation.py (líneas ~140-150)
zone = Zone(candle_index=10, ...)   # zona "nace" oficialmente en vela 10
detector.active_zones = [zone]       # inyección manual ANTES de arrancar process_stream
_ = detector.process_stream(df)      # loop empieza en idx=0
```

### Qué pasa paso a paso

1. **`process_stream()` inicia el loop en `idx=0`** — no en `idx=10`. La zona ya está en `active_zones` desde el inicio.

2. **En `idx=0`**, el bloque de retest (línea ~1174) dispara un **retest falso** porque no valida `idx >= zone.candle_index` antes de intentar retest. La zona lleva "existiendo" 0 velas, pero el sistema la trata como si llevara 10.

3. **`max_price_since_detection` se actualiza incondicionalmente** en cada iteración del loop (líneas ~1178-1180). Como el tracking no tiene condición de "zona activa desde cuando", sigue corriendo en cada vela incluyendo las 15 velas de padding que el test añade después del retest (con `high=10200`).

4. **El resultado final es 10200.0** — el high más alto de todo el dataset (las velas de padding), no 10100.0 (el valor esperado del test).

5. **El `max_clearance_atr` del feature se calculó con 10015.0**, no 10100.0 ni 10200.0 — porque el clearance en `idx=0` usa `max_price_since_detection` que todavía no alcanzó el padding.

### ¿Por qué NO es un bug de producción?

El guard `_cleanup_expired_zones()` existe **exactamente para esto**, pero se ejecuta **después** del bloque de retest en la misma iteración (línea ~1235):

```python
# Línea 1174-1230: bloque de retest (se ejecuta primero)
if zone.retest_detected:
    ...

# Línea 1235: purga defensiva para iteraciones FUTURAS
_cleanup_expired_zones()  # ← guarda llega tarde para la iteración actual
```

En producción, una zona genuina **solo** entra en `active_zones` a través de `_detect_new_zones()`, que se llama en el mismo `idx` que la zona se detecta (línea ~1286: `candle_index=candle["index"]`). Una zona "nacida antes de su propio índice" es una condición que **solo** el harness del test puede crear inyectando el objeto manualmente.

### Dato clave para tus datasets reales

Tus 92 + 101 + 122 samples acumulados en `prepared_sets/` **NO están contaminados** por este mecanismo. El bug de fixture requiere que una zona "nacida antes de su propio índice" exista — imposible en pipeline live ni en batch histórico real donde las zonas se detectan en el idx correcto.

## Fix recomendado (en el test, no en producción)

```python
# En lugar de inyectar la zona activa desde idx=0...
detector.active_zones = [zone]
_ = detector.process_stream(df)

# ...procesar en dos tramos:
_ = detector.process_stream(df.iloc[:zone.candle_index])
detector.active_zones = [zone]
_ = detector.process_stream(df.iloc[zone.candle_index:].reset_index(drop=True))

# O alternativa más simple:
zone.candle_index = 0  # aceptar que la zona "nace" en vela 0 del test sintético
detector.active_zones = [zone]
_ = detector.process_stream(df)
```

## Relación con tu crónica de Fase 8

Toca `max_clearance_atr`, la feature de la que depende — según tu propia crónica — cualquier filtro futuro de rebotes prematuros. El valor correcto (4.5, sin leakage) se guarda en el `TrainingSample` del modelo porque el feature se calcula en el snapshot del momento exacto del retest (líneas ~1075-1078 en la ruta live). El mutable `zone.max_price_since_detection` evoluciona después por diseño (soporta `MAX_TOUCHES=3`). Son dos variables distintas:

- **Feature** → snapshot, sin leakage, correcto
- **Atributo mutable de zona** → evoluciona con el loop, puede ser engañoso si la zona se inyecta prematuramente

## Estado en el repo verificado en vivo

- ✅ Archivo test localizado en `tests/` (raíz), no en `cgalpha_v3/tests/`
- ✅ Re-ejecución del test: 10200.0 determinista, no flake
- ✅ `retest_index=0` confirmado (debería ser 13)
- ✅ `max_clearance_atr=0.25` confirmado (no 4.5 ni 9.5)
- ✅ `_check_retest()` instrumentado: dispara en idx=0 cuando zone.candle_index=10
- ✅ `_cleanup_expired_zones()` reconfirmado: guard llega tarde (misma iteración)
- ✅ `classify()` línea 192: Rule 3 bloquea auto-aprobación para `volume_threshold`

## Caveat

Advertencia de `InconsistentVersionWarning` de sklearn (modelo entrenado con 1.7.2, entorno corriendo 1.8.0). No invalida los hallazgos de este test (no carga modelos .joblib), pero podría introducir falsos positivos/negativos en tests que sí cargan modelos serializados.

## Nota de honestidad

Mi diagnóstico inicial (hipótesis de leakage: el feature se contamina con velas posteriores al retest) era **incorrecto**, y lo digo explícitamente porque la evidencia lo refutó. El mecanismo real es distinto: retest falso por inyección prematura en active_zones. Es el mismo estándar que le exijo a la evaluación externa — no especular, verificar contra el código que corre.