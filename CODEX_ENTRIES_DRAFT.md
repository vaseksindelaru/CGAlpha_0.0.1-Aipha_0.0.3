# CODEX ENTRIES DRAFT — Decisiones Arquitectónicas y Bugs

> Documento de preparación para ingestar en MemoryPolicyEngine.
> Todos los campos [COMPLETAR] han sido rellenados con datos reales del proyecto.

---

## D-001 — zigzag_threshold = 0.18%

- **Codex ID:** D-001
- **Tipo:** DECISION
- **Estado:** ACTIVE
- **Fecha de calibración:** 2026-04-29 (commit `a5ed77a`)
- **Título:** Calibración ZigZag threshold al P75 del rango real de vela
- **Statement:** El `zigzag_threshold` del `MiniTrendDetector` se calibró a 0.18% basándose en el percentil 75 del rango de vela BTCUSDT 5m sobre 288 velas. El threshold anterior (0.1%) producía distribuciones artificiales (55.7/44.3). Con 0.18%: distribución 72.7/27.3, 121 samples reales, OOS 0.68.
- **Rationale:** Un threshold por debajo del P75 captura ruido de microestructura como falsos segmentos de tendencia. El P75 (0.1553%) asegura que solo movimientos con amplitud real de mercado generan segmentos ZigZag. Se eligió 0.18% (entre P75 y P90) como margen de seguridad.
- **Script de calibración:** `scripts/sim_zigzag_thresholds.py`
- **Datos de calibración (288 velas BTCUSDT 5m):**
  - Mediana (P50): 0.1091%
  - P75: 0.1553%
  - P25: no registrado en el proyecto — pendiente de re-ejecución del script
  - P90: no registrado explícitamente — threshold 0.18% descrito como "entre P75 y P90"
- **Período del dataset:** 288 velas BTCUSDT 5m (~24 horas)
- **Archivos afectados:** `cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py`
- **Inject when:** `optimizer`, `backtest_config`, `signal_detector`

---

## D-002 — outcome_lookahead_bars → adaptativo

- **Codex ID:** D-002
- **Tipo:** DECISION
- **Estado:** ACTIVE
- **Fecha de la decisión:** 2026-05-04 (commit `807b772` — deferred labeling implementation)
- **Título:** Lookahead adaptativo proporcional al ancho de zona
- **Statement:** El `outcome_lookahead_bars` fijo de 10 barras fue reemplazado por una fórmula adaptativa: `max(5, min(20, int(5 + zone_width_atr * 3)))`. Zonas estrechas (0.3 ATR → 6 bars) se resuelven rápido; zonas amplias (2.0 ATR → 11 bars) necesitan más tiempo.
- **Rationale:** Un lookahead fijo ignora la geometría de la zona. Si la zona es estrecha, 10 barras es excesivo y genera labels INCONCLUSIVE innecesarios. Si es amplia, 10 barras puede ser insuficiente y forzar resoluciones prematuras.
- **Archivos afectados:** `cgalpha_v3/domain/deferred_outcome_monitor.py`
- **Inject when:** `labeling`, `oracle_modification`, `deferred_outcome`

---

## D-003 — OOS mínimo 30 muestras para comparación A/B

- **Codex ID:** D-003
- **Tipo:** DECISION
- **Estado:** ACTIVE
- **Fecha:** 2026-06-01 (A/B training session — reporte `oracle_v5_ab_training_20260601.json`)
- **Título:** Prerequisito OOS ≥ 30 muestras antes de métricas comparativas
- **Statement:** No se puede tomar una decisión de promoción A/B si alguno de los sets tiene menos de 30 muestras en el conjunto OOS (test split). Con n_test < 30, las métricas de accuracy y Brier score tienen varianza demasiado alta para ser estadísticamente significativas.
- **Rationale:** En la sesión del 2026-05-31, Set A tenía n_test=7 y Set B n_test=22. Ambos por debajo de 30. La decisión de "keep_set_b_champion" fue correcta pero basada en métricas poco fiables. El guard `MIN_OOS_SAMPLES = 30` fue implementado en `train_oracle_ab.py` el 2026-06-06.
- **Archivos afectados:** `cgalpha_v3/scripts/train_oracle_ab.py`
- **Inject when:** `oracle_modification`, `model_training`, `ab_testing`

---

## D-004 — Fingerprint sin zone_direction (B-008 v2)

- **Codex ID:** D-004
- **Tipo:** DECISION
- **Estado:** ACTIVE
- **Fecha:** 2026-06-05 (commit `c19f7d6`)
- **Título:** El fingerprint causal mide el evento de mercado, no la interpretación semántica
- **Statement:** El fingerprint de deduplicación usa `f"{int(ts)}_{float(price):.2f}"` — solo timestamp y precio. La `zone_direction` (bullish/bearish) NO forma parte del fingerprint porque dos zonas superpuestas de polaridad opuesta activadas por el mismo tick representan un único evento físico de mercado.
- **Rationale:** Incluir `zone_direction` en el fingerprint generaba Cross-Polarity Clones: dos muestras idénticas en el dataset cuando una zona bullish y una bearish se superponían espacialmente. Primera zona en `active_zones` registra el evento (política FCFS). Se eliminaron 11 Cross-Polarity Clones del dataset (218 → 207 filas).
- **Archivos afectados:** `cgalpha_v3/domain/deferred_outcome_monitor.py`, `scripts/clean_dataset_duplicates.py`
- **Inject when:** `deduplication`, `data_pipeline`, `feature_proposal`

---

## D-005 — DeferredOutcomeMonitor: etiquetado diferido

- **Codex ID:** D-005
- **Tipo:** DECISION
- **Estado:** ACTIVE
- **Fecha:** 2026-05-04 (commit `807b772` — "Tick-level L2 implementation, deferred labeling")
- **Título:** Etiquetado diferido con resolución terciaria
- **Statement:** El outcome de cada retest se determina de forma diferida: el `DeferredOutcomeMonitor` observa el precio post-entrada y asigna label solo cuando se cumplen condiciones de resolución. NUNCA se asigna un label por defecto. Clasificación terciaria: BOUNCE_STRONG (escape > 0.5 ATR), BOUNCE_WEAK (MFE > 0.3 ATR sin escape), BREAKOUT (precio cruza lado opuesto), INCONCLUSIVE (excluido del training).
- **Rationale:** El etiquetado inmediato en el detector (`_determine_outcome` L965) tenía un fallback `return 'BOUNCE'` que contaminaba el dataset con outcomes marginales. El etiquetado diferido elimina esta contaminación al esperar evidencia real de movimiento post-retest.
- **Archivos afectados:** `cgalpha_v3/domain/deferred_outcome_monitor.py`
- **Inject when:** `labeling`, `oracle_modification`, `data_pipeline`

---

## D-006 — ATR capturado en momento de detección, no del retest

- **Codex ID:** D-006
- **Tipo:** DECISION
- **Estado:** ACTIVE
- **Fecha:** 2026-05-03 (commit `59b87ab` — Fase 8: Instrumentación de clearance)
- **Título:** atr_at_detection captura la volatilidad del escape, no del regreso
- **Statement:** El campo `atr_at_detection` se captura exclusivamente en el momento en que la zona es detectada, no cuando ocurre el retest. Todos los cálculos normalizados (clearance, MFE/MAE en ATRs, zone_width_atr) usan este ATR como denominador.
- **Rationale:** El ATR al momento del retest mide la volatilidad cuando el precio ya regresó a la zona — no la fuerza del escape original. Usar el ATR del retest contaminaría las métricas normalizadas con la volatilidad del evento de regreso en lugar del evento causal (la detección de la zona).
- **Archivos afectados:** `cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py`, `cgalpha_v3/domain/deferred_outcome_monitor.py`
- **Inject when:** `signal_detector`, `feature_proposal`, `clearance`

---

## B-008 — Spatial Multi-Touch Duplication (ambas versiones)

- **Codex ID:** B-008
- **Tipo:** BUG
- **Estado:** RESOLVED
- **Título:** Deduplicación Causal: de Same-Direction a Cross-Polarity
- **v1 — Same-Direction Clones:**
  - Fecha: 2026-05-26 (commit `145c455`)
  - Problema: Múltiples zonas del mismo tipo (bullish-bullish) superpuestas generaban muestras duplicadas para el mismo tick.
  - Fix: Fingerprint causal `{ts}_{price}` (sin dirección) en `_causal_fingerprint()` del `DeferredOutcomeMonitor`.
- **v2 — Cross-Polarity Clones:**
  - Fecha: 2026-06-05 (commit `c19f7d6`)
  - Problema: El fingerprint del monitor ya no incluía dirección, pero `clean_dataset_duplicates.py` seguía usando `direction` en su `causal_key`, permitiendo que clones cross-polarity (bullish + bearish, mismo tick) sobrevivieran la limpieza.
  - Fix: `causal_key = f"{int(ts)}_{float(price):.2f}"` en el script de limpieza + casting explícito en el monitor. 11 Cross-Polarity Clones eliminados (218 → 207).
- **Archivos afectados:** `cgalpha_v3/domain/deferred_outcome_monitor.py`, `scripts/clean_dataset_duplicates.py`
- **Inject when:** `deduplication`, `data_pipeline`

---

## Script de Ingesta en MemoryPolicyEngine

```python
import json
import sys
sys.path.insert(0, '.')
from cgalpha_v3.learning.memory_policy import MemoryPolicyEngine, MemoryLevel
from cgalpha_v3.domain.models.signal import MemoryEntry

engine = MemoryPolicyEngine()

entries = [
    {
        "codex_id": "D-001",
        "type": "DECISION",
        "status": "ACTIVE",
        "title": "Calibración ZigZag threshold al P75 del rango real de vela",
        "statement": "zigzag_threshold = 0.18%. Calibrado con P75 de 288 velas BTCUSDT 5m. Mediana=0.1091%, P75=0.1553%. Threshold entre P75 y P90.",
        "rationale": "Un threshold por debajo del P75 captura ruido como falsos segmentos. Con 0.18%: distribución 72.7/27.3, 121 samples reales, OOS 0.68.",
        "schema_version": "1.0.0",
        "harness_inject_when": ["optimizer", "backtest_config", "signal_detector"],
        "affects_files": ["cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py"],
        "evidence_ids": ["commit_a5ed77a", "scripts/sim_zigzag_thresholds.py"]
    },
    {
        "codex_id": "D-002",
        "type": "DECISION",
        "status": "ACTIVE",
        "title": "Lookahead adaptativo proporcional al ancho de zona",
        "statement": "outcome_lookahead_bars = max(5, min(20, int(5 + zone_width_atr * 3))). Zonas estrechas se resuelven rápido, zonas amplias necesitan más tiempo.",
        "rationale": "Un lookahead fijo de 10 barras ignora la geometría de la zona, generando INCONCLUSIVE innecesarios en zonas estrechas y resoluciones prematuras en zonas amplias.",
        "schema_version": "1.0.0",
        "harness_inject_when": ["labeling", "oracle_modification", "deferred_outcome"],
        "affects_files": ["cgalpha_v3/domain/deferred_outcome_monitor.py"],
        "evidence_ids": ["commit_807b772"]
    },
    {
        "codex_id": "D-003",
        "type": "DECISION",
        "status": "ACTIVE",
        "title": "Prerequisito OOS >= 30 muestras para comparación A/B válida",
        "statement": "No se puede tomar decisión de promoción A/B si n_test < 30 en cualquiera de los sets. Guard MIN_OOS_SAMPLES = 30 en _promotion_decision().",
        "rationale": "En sesión 2026-05-31, Set A tenía n_test=7 y Set B n_test=22. Métricas con varianza demasiado alta para ser estadísticamente significativas.",
        "schema_version": "1.0.0",
        "harness_inject_when": ["oracle_modification", "model_training", "ab_testing"],
        "affects_files": ["cgalpha_v3/scripts/train_oracle_ab.py"],
        "evidence_ids": ["oracle_v5_ab_training_20260601.json"]
    },
    {
        "codex_id": "D-004",
        "type": "DECISION",
        "status": "ACTIVE",
        "title": "Fingerprint causal sin zone_direction — mide evento de mercado",
        "statement": "fingerprint = f'{int(ts)}_{float(price):.2f}'. Sin zone_direction. Política FCFS: primera zona registra el evento.",
        "rationale": "Incluir zone_direction generaba Cross-Polarity Clones: 11 duplicados eliminados del dataset (218 a 207 filas).",
        "schema_version": "1.0.0",
        "harness_inject_when": ["deduplication", "data_pipeline", "feature_proposal"],
        "affects_files": ["cgalpha_v3/domain/deferred_outcome_monitor.py", "scripts/clean_dataset_duplicates.py"],
        "evidence_ids": ["commit_c19f7d6", "B-008"]
    },
    {
        "codex_id": "D-005",
        "type": "DECISION",
        "status": "ACTIVE",
        "title": "DeferredOutcomeMonitor: etiquetado diferido terciario",
        "statement": "El outcome se determina de forma diferida. NUNCA se asigna label por defecto. Clasificación: BOUNCE_STRONG, BOUNCE_WEAK, BREAKOUT, INCONCLUSIVE.",
        "rationale": "El fallback 'return BOUNCE' en _determine_outcome L965 contaminaba el dataset con outcomes marginales. El etiquetado diferido espera evidencia real.",
        "schema_version": "1.0.0",
        "harness_inject_when": ["labeling", "oracle_modification", "data_pipeline"],
        "affects_files": ["cgalpha_v3/domain/deferred_outcome_monitor.py"],
        "evidence_ids": ["commit_807b772"]
    },
    {
        "codex_id": "D-006",
        "type": "DECISION",
        "status": "ACTIVE",
        "title": "ATR capturado en momento de detección, no del retest",
        "statement": "atr_at_detection se captura cuando la zona es detectada. Todos los cálculos normalizados (clearance, MFE/MAE, zone_width_atr) usan este ATR.",
        "rationale": "El ATR del retest mide volatilidad del regreso, no del escape. Usar ATR del retest contaminaría métricas con volatilidad del evento incorrecto.",
        "schema_version": "1.0.0",
        "harness_inject_when": ["signal_detector", "feature_proposal", "clearance"],
        "affects_files": ["cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py", "cgalpha_v3/domain/deferred_outcome_monitor.py"],
        "evidence_ids": ["commit_59b87ab"]
    },
    {
        "codex_id": "B-008",
        "type": "BUG",
        "status": "RESOLVED",
        "title": "Spatial Multi-Touch Duplication (v1 Same-Direction + v2 Cross-Polarity)",
        "statement": "v1 (2026-05-26): zonas superpuestas mismo tipo generaban duplicados. Fix: fingerprint causal sin dirección. v2 (2026-06-05): clean_dataset_duplicates.py aún usaba direction en causal_key. Fix: causal_key sin dirección + casting explícito. 11 Cross-Polarity Clones eliminados.",
        "rationale": "El fingerprint debe medir el evento físico de mercado (ts + precio), no la interpretación semántica del detector (dirección de zona).",
        "schema_version": "1.0.0",
        "harness_inject_when": ["deduplication", "data_pipeline"],
        "affects_files": ["cgalpha_v3/domain/deferred_outcome_monitor.py", "scripts/clean_dataset_duplicates.py"],
        "evidence_ids": ["commit_145c455", "commit_c19f7d6"]
    }
]

for content in entries:
    entry = MemoryEntry.new(
        content=json.dumps(content, ensure_ascii=False),
        level=MemoryLevel.RELATIONS,
        field="architect",
        source_id="codex_entries_draft_v1",
        source_type="primary",
        tags=["codex", "codex_decision", "foundation", content["type"].lower()],
        expires_at=None,
    )
    entry.entry_id = content["codex_id"]
    entry.approved_by = "Lila"
    engine.entries[entry.entry_id] = entry
    engine._persist_codex_entry(entry)
    print(f"✓ {content['codex_id']} guardado como {entry.entry_id}")

print(f"\n✅ {len(entries)} entradas Codex guardadas en MemoryPolicyEngine nivel RELATIONS")
```
