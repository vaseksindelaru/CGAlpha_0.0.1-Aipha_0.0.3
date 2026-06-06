# CODEX — Entradas D/B para la Sesión de Reconstrucción
## cgAlpha_0.0.1 — Versión verificada (datos reales del proyecto)

> Estas entradas deben estar en el Codex ANTES de ejecutar la sesión
> de reconstrucción. El modelo las lee para entender POR QUÉ cada
> parámetro tiene el valor que tiene.
>
> Todos los campos [COMPLETAR] del borrador original han sido rellenados
> con datos verificados vía `git log`, `grep` en la crónica, y scripts.
> Las 7 entradas fueron guardadas en MemoryPolicyEngine nivel RELATIONS
> con tag "codex_decision" el 2026-06-06.

---

## DECISIONES DE CALIBRACIÓN EMPÍRICA

---

### D-001 — zigzag_threshold = 0.18%

```json
{
  "codex_id": "D-001",
  "type": "calibration_decision",
  "component": "MiniTrendDetector",
  "parameter": "zigzag_threshold",
  "value": 0.0018,
  "unit": "fracción decimal del precio",
  "status": "activo",
  "fecha": "2026-04-29 (commit a5ed77a)",
  "origen": "empírico — percentil de datos reales",
  "evidencia": {
    "metodo": "P75 del rango relativo de vela (high-low)/close",
    "dataset": "288 velas BTCUSDT 5m",
    "periodo": "~24 horas de datos históricos continuos",
    "script": "scripts/sim_zigzag_thresholds.py",
    "resultado_raw": {
      "P25": "no registrado — pendiente re-ejecución del script",
      "P50_mediana": 0.001091,
      "P75": 0.001553,
      "P90": "no registrado explícitamente",
      "threshold_elegido": "0.0018 — entre P75 y P90 como margen de seguridad"
    }
  },
  "justificacion": "El P75 del rango de vela (0.1553%) representa el movimiento 'típico-alto'. Un threshold inferior captura demasiado ruido microestructural. Uno superior reduce micro-tendencias a cero en mercados laterales. Se eligió 0.18% (entre P75 y P90) como margen.",
  "historia": [
    {
      "valor_previo": 0.02,
      "razon_cambio": "threshold 2% requería movimientos de $1500 — generaba 0 tendencias (686 micro-segmentos filtrados)",
      "fecha": "pre-2026-04-27 (valor original en MiniTrendDetector)"
    },
    {
      "valor_previo": 0.001,
      "razon_cambio": "threshold 0.1% generaba distribución artificial 55.7/44.3 BOUNCE/BREAKOUT. Test accuracy 1.0 (engañoso).",
      "fecha": "2026-04-27 (fix inicial)"
    },
    {
      "valor_final": 0.0018,
      "razon_cambio": "Calibración con P75 de 288 velas reales → distribución 72.7/27.3, 121 samples, OOS 0.68",
      "fecha": "2026-04-29 (commit a5ed77a)"
    }
  ],
  "restriccion": "Cualquier cambio de este valor DEBE justificarse con el mismo análisis empírico sobre datos frescos. No es un número que se razona — se mide.",
  "implementacion_v6": "Convertir en función adaptativa: P75 de las últimas 500 velas, recalculado cada ciclo de pipeline.",
  "tags": ["oracle", "triple_coincidence", "calibration", "zigzag"],
  "harness_inject_when": ["optimizer", "backtest_config", "signal_detector"],
  "affects_files": ["cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py"],
  "evidence_ids": ["commit_a5ed77a", "scripts/sim_zigzag_thresholds.py"]
}
```

> ⚠️ **CORRECCIÓN vs borrador original:** El borrador del zip tenía P75=0.0018.
> Eso es INCORRECTO. P75 real = 0.001553 (0.1553%). El threshold 0.18% está
> ENTRE P75 y P90, no ES el P75. Fuente: crónica §4, líneas 178-180.

---

### D-002 — outcome_lookahead_bars = 10 (fijo → adaptativo en v6)

```json
{
  "codex_id": "D-002",
  "type": "calibration_decision",
  "component": "DeferredOutcomeMonitor / _determine_outcome",
  "parameter": "outcome_lookahead_bars",
  "value": 10,
  "unit": "velas de 5 minutos (50 minutos en total)",
  "status": "activo — candidato a mejora en v6",
  "fecha": "2026-05-04 (commit 807b772 — deferred labeling implementation)",
  "origen": "estimación inicial — pendiente de calibración empírica",
  "limitacion_conocida": {
    "debilidad": "#5 del análisis estructural del Oracle",
    "descripcion": "Trata igual zonas estrechas (0.3 ATR, se resuelven en 15 min) y zonas amplias (2.0 ATR, necesitan 55 min). El modelo asigna INCONCLUSIVE a bounces lentos en zonas amplias.",
    "evidencia": "crónica_desarrollo_cgAlpha.md §8.3"
  },
  "implementacion_v6": "Lookahead adaptativo: max(5, min(20, int(5 + zone_width_atr * 3))). Zonas de 0.3 ATR → 6 velas. Zonas de 2.0 ATR → 11 velas.",
  "tags": ["oracle", "triple_coincidence", "calibration", "labeling"],
  "harness_inject_when": ["labeling", "oracle_modification", "deferred_outcome"],
  "affects_files": ["cgalpha_v3/domain/deferred_outcome_monitor.py"],
  "evidence_ids": ["commit_807b772"]
}
```

---

### D-003 — Set A no se promueve con OOS < 30 muestras

```json
{
  "codex_id": "D-003",
  "type": "governance_invariant",
  "component": "train_oracle_ab.py",
  "parameter": "min_oos_samples_for_comparison",
  "value": 30,
  "status": "invariante — no negociable",
  "fecha": "2026-06-01 (A/B training — reporte oracle_v5_ab_training_20260601.json)",
  "fecha_implementacion": "2026-06-06 (guard MIN_OOS_SAMPLES=30 en _promotion_decision())",
  "origen": "A/B training del 1 junio 2026",
  "evidencia": {
    "descripcion": "Set A tuvo OOS accuracy = 0.7143 sobre 7 muestras. Intervalo de confianza del 95%: ±33%. El número era estadísticamente inútil.",
    "reporte": "aipha_memory/reports/oracle_v5_ab_training_20260601.json",
    "calculo_ic": "Para n=7, IC 95% de una proporción es ±sqrt(p(1-p)/n) * 1.96 ≈ ±0.33",
    "set_a_n_test": 7,
    "set_b_n_test": 22,
    "set_a_brier": 0.184939,
    "set_b_brier": 0.174978,
    "decision": "keep_set_b_champion"
  },
  "restriccion": "Nunca calcular Brier Score ni gap train/OOS como criterio de promoción sobre menos de 30 muestras OOS reales.",
  "implementacion": "Guard en _promotion_decision(): if len(X_test) < MIN_OOS_SAMPLES: return {'status': 'OOS_TOO_SMALL'}",
  "tags": ["oracle", "training", "governance", "oos"],
  "harness_inject_when": ["oracle_modification", "model_training", "ab_testing"],
  "affects_files": ["cgalpha_v3/scripts/train_oracle_ab.py"],
  "evidence_ids": ["oracle_v5_ab_training_20260601.json"]
}
```

---

## DECISIONES DE ARQUITECTURA

---

### D-004 — Fingerprint de deduplicación sin semántica de dirección (B-008 v2)

```json
{
  "codex_id": "D-004",
  "type": "architecture_decision",
  "component": "DeferredOutcomeMonitor",
  "metodo": "_causal_fingerprint",
  "decision": "fingerprint = f'{int(ts)}_{float(price):.2f}'",
  "fecha": "2026-06-05 (commit c19f7d6)",
  "origen": "B-008 v2 — Cross-Polarity Clones",
  "problema_resuelto": {
    "descripcion": "Cuando una zona bullish y una bearish se superponen, un mismo tick activa ambas. El fingerprint con zone_direction generaba dos huellas distintas → dos muestras idénticas en el dataset.",
    "ejemplo": "ts=1779436484504, precio=77439.2 → dos fingerprints → dos muestras (31 mayo 2026)",
    "contaminacion": "11 Cross-Polarity Clones eliminados (218 → 207 filas)"
  },
  "politica_fcfs": {
    "descripcion": "First Come, First Served — la primera zona encontrada en active_zones registra el evento",
    "orden": "Cronológico por orden de inserción en active_zones (Python dict 3.7+)",
    "justificacion": "La frecuencia de empates duales es baja. FCFS es determinista y auditable sin parámetros nuevos.",
    "alternativa_rechazada": "Favorecer la zona con mejor coincidence_score — rechazada por complejidad sin evidencia de mejora"
  },
  "restriccion": "No añadir zone_direction ni ningún campo semántico al fingerprint. El fingerprint mide la convergencia espacio-temporal del mercado, no la interpretación del detector.",
  "tags": ["deduplication", "dataset", "oracle", "B-008"],
  "harness_inject_when": ["deduplication", "data_pipeline", "feature_proposal"],
  "affects_files": ["cgalpha_v3/domain/deferred_outcome_monitor.py", "scripts/clean_dataset_duplicates.py"],
  "evidence_ids": ["commit_c19f7d6", "B-008"]
}
```

---

### D-005 — Etiquetado diferido y terciario (DeferredOutcomeMonitor)

```json
{
  "codex_id": "D-005",
  "type": "architecture_decision",
  "component": "_determine_outcome + DeferredOutcomeMonitor",
  "decision": "Outcome = null hasta resolución real. INCONCLUSIVE excluido del training set.",
  "fecha": "2026-05-04 (commit 807b772 — Tick-level L2 implementation, deferred labeling)",
  "problema_resuelto": {
    "descripcion": "El fallback 'return BOUNCE' en L965 de triple_coincidence.py clasificaba como éxito precios que no se movieron. Un bounce débil de 0.1 ATR recibía el mismo label que uno de 2.0 ATR.",
    "impacto": "Contaminación de la variable target — el Oracle aprendía patrones sobre ruido"
  },
  "clases": {
    "BOUNCE_STRONG": "precio > zone_top + 0.5 * ATR (escape decisivo)",
    "BOUNCE_WEAK": "MFE > 0.3 * ATR pero sin escape (rebote sin convicción)",
    "BREAKOUT": "precio < zone_bottom (ruptura confirmada)",
    "INCONCLUSIVE": "lookahead expiró sin movimiento suficiente — EXCLUIR del training"
  },
  "restriccion": "Nunca asignar un label por defecto. Si no hay resolución dentro del lookahead adaptativo, el sample es INCONCLUSIVE y se excluye.",
  "tags": ["oracle", "labeling", "dataset", "triple_coincidence"],
  "harness_inject_when": ["labeling", "oracle_modification", "data_pipeline"],
  "affects_files": ["cgalpha_v3/domain/deferred_outcome_monitor.py"],
  "evidence_ids": ["commit_807b772"]
}
```

---

### D-006 — ATR capturado al momento de DETECCIÓN, no del retest

```json
{
  "codex_id": "D-006",
  "type": "architecture_decision",
  "component": "ActiveZone",
  "campo": "atr_at_detection",
  "decision": "El ATR se captura exclusivamente cuando la zona se detecta, no cuando se produce el retest.",
  "fecha": "2026-05-03 (commit 59b87ab — Fase 8: Instrumentación de clearance)",
  "justificacion": "El ATR del retest mide la volatilidad del regreso del precio hacia la zona. El ATR de la detección mide la volatilidad cuando el precio escapó — eso es lo causalmente relevante.",
  "ejemplo": {
    "descripcion": "Si el precio escapó 4 ATR (ATR=80 en ese momento) pero al retestar la volatilidad cayó (ATR=30), el clearance real es 4 ATR, no 4*80/30 = 10.7 ATR.",
    "conclusion": "Normalizar clearance por ATR_deteccion da la distancia correcta"
  },
  "restriccion": "atr_at_detection debe capturarse en el mismo ciclo que zone.zone_top y zone.zone_bottom. No recalcular al momento del retest.",
  "tags": ["oracle", "triple_coincidence", "features", "atr"],
  "harness_inject_when": ["signal_detector", "feature_proposal", "clearance"],
  "affects_files": ["cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py", "cgalpha_v3/domain/deferred_outcome_monitor.py"],
  "evidence_ids": ["commit_59b87ab"]
}
```

---

## BUGS DOCUMENTADOS

---

### B-008 — Spatial Multi-Touch y Cross-Polarity Clones

```json
{
  "codex_id": "B-008",
  "type": "bug_documentation",
  "titulo": "Clones de muestras de entrenamiento — dos vectores de ataque",
  "estado": "RESUELTO (ambos vectores)",
  "versiones": [
    {
      "version": "v1 — Spatial Multi-Touch",
      "problema": "El precio rebotaba múltiples veces en la misma zona dentro de una ventana corta, generando muestras duplicadas con casi los mismos features",
      "fix": "Debounce en _check_retest — last_retest_ts_ms por zona",
      "fecha": "2026-05-26 (commit 145c455)",
      "archivos_afectados": ["triple_coincidence.py"]
    },
    {
      "version": "v2 — Cross-Polarity Clones",
      "problema": "Una zona bullish y una bearish superpuestas activaban el detector simultáneamente para el mismo tick. El fingerprint incluía zone_direction, por lo que ambas pasaban el filtro de deduplicación.",
      "ejemplo_real": {
        "fecha": "2026-05-31",
        "sample_1": "re_20260531_164846_BTCUSDT_bullish_332 → BREAKOUT",
        "sample_2": "re_20260531_164846_BTCUSDT_bearish_176 → BREAKOUT",
        "ts_identico": "1779436484504",
        "precio_identico": "77439.2"
      },
      "fix": "Eliminar zone_direction del fingerprint → f'{int(ts)}_{float(price):.2f}' + casting robusto",
      "politica": "FCFS — primera zona en active_zones registra el evento",
      "fecha": "2026-06-05 (commit c19f7d6)",
      "limpieza": "11 Cross-Polarity Clones eliminados del dataset (218 → 207 filas)",
      "archivos_afectados": ["domain/deferred_outcome_monitor.py", "scripts/clean_dataset_duplicates.py"]
    }
  ],
  "leccion": "El fingerprint de deduplicación debe medir el evento de mercado (tiempo + precio), nunca la interpretación semántica del detector (dirección, tipo de zona). Ver D-004.",
  "prevencion": "DuplicateWatchdog — escaneo periódico del dataset. Ver duplicate_watchdog.py.",
  "tags": ["deduplication", "dataset", "oracle", "quality"],
  "harness_inject_when": ["deduplication", "data_pipeline"],
  "affects_files": ["cgalpha_v3/domain/deferred_outcome_monitor.py", "scripts/clean_dataset_duplicates.py"],
  "evidence_ids": ["commit_145c455", "commit_c19f7d6"]
}
```

---

## SCRIPT DE INGESTA EN MEMORYPOLICYENGINE

> ✅ Ejecutado el 2026-06-06. Las 7 entradas están en memoria nivel RELATIONS.
> Verificación: `engine.load_from_disk()` → 7 entradas con tag "codex_decision".

```python
import json
import sys
sys.path.insert(0, "/home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3")

from cgalpha_v3.learning.memory_policy import MemoryPolicyEngine, MemoryLevel
from cgalpha_v3.domain.models.signal import MemoryEntry

engine = MemoryPolicyEngine()

# Los JSONs de arriba van aquí (uno por entrada)
codex_entries = [
    # D-001, D-002, D-003, D-004, D-005, D-006, B-008
]

for content in codex_entries:
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
    print(f"✓ {content['codex_id']} guardado")
```

---

*Versión fusionada: estructura rica del borrador original + datos verificados del proyecto.*
*Última actualización: 2026-06-06*
