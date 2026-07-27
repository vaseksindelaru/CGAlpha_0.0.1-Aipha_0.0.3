---
type: learning-note
project: CGAlpha
tags: [proyecto/cgalpha, learning, fase-2, json, oracle-gui]
created: 2026-07-27
part: 1-of-5
---

# Clase Magistral: El Viaje de un Dato — Del Disco a la Pantalla

**Nivel**: S1 (Learning) — Fundamentos  
**Fase**: Fase 2 — Integración GUI  
**Duración estimada**: Sesión completa  
**Prerrequisito**: Dominio de imports (Fase 1 completada)

---

## 0. Objetivo

Entender cómo un número que nace en un cálculo de Random Forest termina, minutos después, siendo una línea legible en tu interfaz de Control Room. Este es el puente entre "el Oracle piensa" y "el operador humano ve lo que pensó".

---

## 1. Antes de la GUI: cómo nacen los datos

### 1.1 El pipeline completo (phase1_oracle_training.py)

```python# Puntos clave
# - seed=42 no es cosmético: firma de reproducibilidad
# - Cada etapa transforma el datos a una forma más útil

logger.info("PASO 1: Generando datos sintéticos (2000 velas)")
df = generate_realistic_ohlcv(n_candles=2000, seed=42)
micro_df = generate_micro_features(df, seed=42)

detector = TripleCoincidenceDetector()
retest_events = detector.process_stream(df, micro_df)
training_samples = _flatten_training_samples(detector.get_training_dataset())
```

### 1.2 La cadena de transformación

| Etapa | Entrada | Salida | Función |
|-------|---------|--------|---------|
| [1] OHLCV crudo | .csv / generado | DataFrame `df` | `generate_realistic_ohlcv()` |
| [2] Micro-features | df | DataFrame `micro_df` | `generate_micro_features()` — VWAP, OBI, delta |
| [3] Detección de patrones | df + micro_df | Eventos de retest | `TripleCoincidenceDetector.process_stream()` |
| [4] Aplanado | Eventos anidados | Tabla plana | `_flatten_training_samples()` |

### 1.3 ¿Por qué flatten?

Los datos de ML casi nunca nacen en la forma tabular que un DataFrame necesita. Nacen anidados — un evento de retest tiene su zona, su régimen, sus features de microestructura, todo en dicts dentro de dicts. "Aplanar" es convertir ese árbol en filas homogéneas, listas para X e y del entrenamiento.

---

## 2. El primer uso de json: logs estructurados

### 2.1 En oracle_v6_skeleton.py

```python
logger.info(json.dumps({
   "event": "prediction",
   "timestamp": time.time(),
   "trade_id": prediction.trade_id,
   "confidence": prediction.confidence,
   "suggested_action": prediction.suggested_action,
   "is_placeholder": False,
   "encoding_inputs": encoding_inputs,
}))
```

### 2.2 ¿Por qué JSON y no string libre?

| Criterio | String libre (`logger.info(f"...")`) | JSON estructurado (`json.dumps()`) |
|----------|--------------------------------------|-------------------------------------|
| Legible humano | ✅ Sí | ⚠️ Menos, pero parseable |
| Parseable por máquina | ❌ Imposible sin regex frágiles | ✅ `json.loads()` línea a línea |
| Dashboard compatible | ❌ | ✅ Grafana, ELK, scripts de análisis |
| Cambio de formato | Rompe el parser | Agregar campos es retrocompatible |

**time.time() vs perf_counter()**: `time.time()` registra un timestamp absoluto (calendario universal). `perf_counter()` mide duración relativa (latencia). Usar la incorrecta produce timestamps que no significan nada al correlacionarlos entre sistemas.

---

## 3. El segundo uso de json: persistencia real

```python
out_path.write_text(
   json.dumps(summary_payload, indent=2, ensure_ascii=False), encoding="utf-8"
)
```

### 3.1 Parámetros deliberados

| Parámetro | Valor | Razón |
|-----------|-------|-------|
| `indent=2` | 2 | Sin esto, una sola línea imposible de leer a simple vista. Con indent, legible como documento escrito a mano. |
| `ensure_ascii=False` | False | Por defecto convierte tildes/ñ a `\u00f1`. En español = ilegible. Con False, las tildes quedan intactas. |

### 3.2 Efímero vs Persistente

```
logger.info(json.dumps(...))  → Efímero: log que rota y se borra
json.dumps() → write_text()   → Persistente: reporte de entrenamiento que sobrevive meses
```

La diferencia clave: el segundo puede ser re-abierto con `json.load()` mucho después, reconstruyendo exactamente la misma estructura de datos.

---

## 4. El puente crítico: Oracle → GUI sin conocerla

### 4.1 El código real (_run_memory_ingestion)

```python
def _run_memory_ingestion(...):
    payload_trading = {
        "content": (
            "Walk-Forward validado: 3 ventanas OOS, "
            f"sharpe_neto_avg={agg_sharpe:.4f}, "
            f"oracle_accuracy_oos={agg_accuracy:.4f}"
        ),
        "field": "trading",
        "source_type": "secondary",
        "tags": ["phase1", "walk_forward", "oos"],
    }
    resp_trading = _call_api("POST", "/learning/memory/ingest", json=payload_trading)
```

### 4.2 ¿Por qué HTTP y no import directo?

El junior pregunta: "¿por qué no `from gui.server import memory_engine; memory_engine.ingest_raw(...)`?"

**Respuesta: acoplamiento débil (loose coupling)**

| Problema si imports directo | Solución HTTP |
|------------------------------|---------------|
| Dependencia obligatoria de Flask — el script de training en un cron sin GUI no puede correr | El script solo necesita una URL |
| Imports circulares: si server.py importa oracle.py y oracle.py importa server.py | No hay ciclo — los procesos son independientes |

### 4.3 El contrato del payload_trading

El payload refleja la arquitectura de 7 niveles de memoria:

| Campo | Significado |
|-------|-------------|
| `"content"` | Texto legible que el humano verá en la pestaña Learning |
| `"field": "trading"` | Clasificación del dominio (ver: trading, architect, codigo, memory_librarian) |
| `"source_type": "secondary"` | Derivado de análisis, no observación primaria del mercado |
| `"tags"` | Etiquetas de búsqueda para MemoryPolicyEngine |

---

## 5. Recorrido completo: la cadena del dato

```
[1] Datos         generate_realistic_ohlcv() + generate_micro_features()
        ↓
[2] Patrones      TripleCoincidenceDetector.process_stream()
        ↓
[3] Tabla plana   _flatten_training_samples()
        ↓
[4] Training      RandomForestClassifier.fit() + walk-forward validation
        ↓
[5a] Log efímero  json.dumps() → logger.info()           [efímero]
[5b] Persistencia json.dumps(indent=2) → write_text()     [persistente]
        ↓
[6] HTTP Bridge   _call_api("POST", "/learning/memory/ingest", json=payload)
        ↓
[7] Recepción     Flask endpoint /learning/memory/ingest
        ↓
[8] Memoria       MemoryPolicyEngine.ingest_raw(field="trading", tags=[...])
        ↓
[9] Renderizado   /learning/operator y /learning/lila leen y muestran
```

---

## 6. El principio arquitectónico clave

> Cada componente se comunica con otro de dos maneras:
> - **Acoplamiento fuerte**: importar código directamente (rápido de escribir, frágil)
> - **Acoplamiento débil**: exponer un contrato HTTP (más código inicial, sistema escalable)

cgAlpha_0.0.1 está construido sobre este patrón repetido: EvolutionOrchestrator, Oracle→GUI, MemoryPolicyEngine, todos usan el mismo principio.

---

## 🔧 Práctica con Graphify

Usa `graphify` para explorar las conexiones de este flujo:

```bash
# Ver cómo TripleCoincidenceDetector conecta con el pipeline
graphify explain "TripleCoincidenceDetector" --graph graphify-out/graph.json

# Encontrar la ruta más corta entre detector y GUI
graphify path "TripleCoincidenceDetector" "server.py" --graph graphify-out/graph.json

# Ver qué módulos importa phase1_oracle_training.py
graphify explain "phase1_oracle_training" --graph graphify-out/graph.json

# Generar nuevo análisis si hiciste cambios
graphify update .
graphify cluster-only .
```

Esto te permitirá visualizar que el "viaje del dato" no es un concepto abstracto — tiene nodos reales, conexiones reales, y comunidades reales en el grafo del código.