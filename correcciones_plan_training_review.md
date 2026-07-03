# Plan de Ejecución P0: Training Review → Transición L2 (CORREGIDO)

## Diagnóstico: Plan Original vs Código Real

| Afirmación del plan | Código real | Consecuencia |
|---|---|---|
| "Endpoints de curation son stubs" | ❌ **FALSO** — `approve` y `reject` ya existen y son funciones reales | No hay que crearlos, solo conectarlos |
| "Pasar de stub a persistencia útil" | ⚠️ **PARCIAL** — Ya persisten en `retests_dataset.json` + `jsonl` | El problema es que buscan en el dataset equivocado |
| "review-data ahora deriva direction" | ✅ **CIERTO** — `_direction_from_zone_id()` funciona | Solo funciona para phase0 (`318_bearish`), no para operacionales (`re_4377_xxxxx`) |

## Bugs Críticos que Bloquean el Plan

### Bug 1: `POST /approve/reject` devuelve 404 para samples operacionales
```
_curate_training_retest() → _load_training_retests()
                            → lee phase0_results/retests_dataset.json (7 samples)
                            → zone_ids: ["318_bearish", "323_bearish", ...]
                            → busca retest_id "re_4377_14a6e5" → 404
```

### Bug 2: `GET /review-data` no reporta `data_source`
El plan pide esto correctamente, pero no se implementó en el parche anterior.

### Bug 3: Key_idx crash en phase 0 (ya parcheado parcialmente)
```python
# ANTES (crash):
key_idx = int(zid.split("_")[0])  # int("re") → ValueError

# DESPUÉS (fix):
for part in zid.split("_"):
    if part.isdigit():
        key_idx = int(part)
        break
```

---

## Fase 1: Conectar curation a datos operacionales (CORREGIDO)

**Lo que el plan dice mal:** "Pasar de stub a persistencia" → Los endpoints ya existen.

**Lo que realmente falta:**

### 1.1 Crear `_load_operational_retests()`
```python
def _load_operational_retests() -> tuple[list[Dict], Path]:
    """Load retests from training_dataset_v2.jsonl for curation search."""
    path = project_root / "aipha_memory/operational/training_dataset_v2.jsonl"
    if not path.exists():
        return [], path
    retests = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            sample = json.loads(line)
            snap = sample.get("l2_snapshot_at_touch", {})
            zg = sample.get("zone_geometry", {})
            out = sample.get("outcome", {})
            meta = sample.get("_meta", {})
            retests.append({
                "sample_id": meta.get("sample_id", f"re_{i}_x"),
                "zone_id": meta.get("sample_id", f"re_{i}_x"),
                "retest_index": int(meta.get("sample_id", "re_0_x").split("_")[1]) if "_" in meta.get("sample_id", "re_0_x") else i,
                "retest_price": snap.get("retest_price", 0),
                "direction": zg.get("direction", "unknown"),
                "zone_top": zg.get("zone_top", 0),
                "zone_bottom": zg.get("zone_bottom", 0),
                "outcome": out.get("label", "UNKNOWN"),
                "dataset_source": "operational",
            })
    return retests, path
```

### 1.2 Parchear `_curate_training_retest()` — Búsqueda dual
```python
def _curate_training_retest(retest_id: str, decision: str):
    # Intentar primero en phase0 (legacy)
    retests, path = _load_training_retests()
    matches = [rt for rt in retests if retest_id in _retest_id_candidates(rt)]
    
    # Si no encuentra, buscar en operacionales
    if not matches:
        op_retests, op_path = _load_operational_retests()
        matches = [rt for rt in op_retests if retest_id == rt.get("sample_id") or 
                   retest_id in _retest_id_candidates(rt)]
    
    if not matches:
        return error_404(retest_id)
    
    # ... persistir curation ...
```

### 1.3 Índice materializado
Crear `_build_curation_index()` que lee `retest_curation.jsonl` una vez y construye dict en memoria:
```python
def _build_curation_index() -> dict[str, dict]:
    """Build in-memory index from retest_curation.jsonl for fast lookup."""
    index = {}
    path = project_root / "aipha_memory/evolutionary/retest_curation.jsonl"
    if not path.exists():
        return index
    with open(path) as f:
        for line in f:
            entry = json.loads(line)
            index[entry["retest_id"]] = {
                "curation_status": entry["status"],
                "curation_decision": entry["decision"],
                "label_status": entry["label_status"],
                "curated_at": entry["ts"],
            }
    return index
```

---

## Fase 2: Fuente de datos con metadata (CORREGIDO)

**Lo que el plan dice bien:** Necesitamos `data_source` en la respuesta.

**Lo que falta agregar:**

### 2.1 Añadir `data_source` en respuesta
```python
return jsonify({
    "data_source": "operational",  # o "phase0_fallback"
    "phase0_samples": 7,
    "operational_samples": 343,
    "ohlcv": ohlcv,
    "retests": retests,
    # ... resto de campos ...
})
```

### 2.2 Lógica de fallback explícita
```python
data_source = "phase0_fallback"
if training_v2_path.exists():
    data_source = "operational"
    # ... leer operacionales ...
else:
    logger.warning("⚠️ No operational dataset, using phase0 fallback")
```

---

## Fase 3: Hygiene de schema (ya mayormente hecho)

Lo que ya existe:
- `_direction_from_zone_id()` ✅ (para phase0)
- Mapeo desde `zone_geometry.direction` ✅ (para operacionales)
- Fallback a `unknown` si no se puede derivar ✅

**Solo falta verificar:** que funcione para ambos formatos de zone_id simultáneamente.

---

## Fase 4: Guardrails legacy → L2 (CORREGIDO)

**Lo que el plan dice bien:** Mantener Training Review como pantalla mínima.

**Corrección importante:** No invertir más en UI visual. El layout side-by-side ya está implementado. Toda la inversión debe ser en backend (datos + curation).

**Contract API para L2:**
- `GET /api/training/review-data` → payload estable con `data_source`
- `POST /api/training/retest/<id>/approve|reject` → respuesta estructurada
- `retest_curation.jsonl` → source of truth para pipeline

---

## Pasos de Verificación

1. `POST /approve` sample operacional → NO 404, persiste en curation
2. `GET /review-data` → sin crashes, `data_source: "operational"`, precios ~$60k
3. Refrescar → decisiones previas aparecen consistentemente
4. Fallback → sin `training_dataset_v2.jsonl` usa phase0 con log

## Riesgos y Mitigaciones

| Riesgo | Mitigación |
|---|---|
| Búsqueda dual rompe compatibilidad | Mantener phase0 como primario, operacionales como fallback |
| Crecimiento jsonl degrade | Índice materializado en memoria |
| Formato zone_id diferente | Cada dataset usa su formato, normalizar en endpoint |
| Doble escritura legacy/L2 | Un único contrato API, consumidores read-only |
