"""
scripts/verify_shadow_harvesting.py
=====================================
Shadow Harvesting — Verificación post-patch
Comprueba que los tres patches se aplicaron correctamente y que el sistema
puede procesar un toque secundario simulado sin lanzar excepciones.

Ejecutar desde la raíz del proyecto:
    python3 scripts/verify_shadow_harvesting.py
"""

import sys
import json
import time
import logging
import tempfile
from pathlib import Path

logging.basicConfig(level=logging.WARNING)
sys.path.insert(0, ".")

PASS = "✅"
FAIL = "❌"
WARN = "⚠️ "
results = []


def check(label: str, condition: bool, detail: str = ""):
    symbol = PASS if condition else FAIL
    results.append((condition, label))
    print(f"  {symbol}  {label}")
    if detail and not condition:
        print(f"       → {detail}")


# ─────────────────────────────────────────────────────────────────────────────
# 1. VERIFICAR QUE LAS CLASES NUEVAS EXISTEN
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 1. Importaciones de Zone Lifecycle ──────────────────────────────────")

try:
    from cgalpha_v3.infrastructure.signal_detector.triple_coincidence import (
        ZoneLifecycleState,
        TouchRecord,
        ActiveZone,
        TripleCoincidenceDetector,
    )
    check("ZoneLifecycleState importado", True)
    check("TouchRecord importado", True)
    check("ActiveZone importado", True)
    check("TripleCoincidenceDetector importado", True)
except ImportError as e:
    check("Importaciones de triple_coincidence", False, str(e))
    print("\n❌ Patch 1 no aplicado correctamente. Detener aquí.")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# 2. VERIFICAR COMPORTAMIENTO DE ActiveZone CON MULTI-TOUCH
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 2. Comportamiento de ActiveZone ─────────────────────────────────────")

# Crear una zona mínima
try:
    zone = ActiveZone(
        candle_index=100,
        zone_top=97250.0,
        zone_bottom=97180.0,
        direction="bullish",
        detection_timestamp=int(time.time()),
        vwap_at_detection=97200.0,
        atr_at_detection=83.0,
        key_candle={},
        accumulation_zone={"quality_score": 0.72},
        mini_trend={},
        zone_id="test_zone_001",
    )

    # Estado inicial
    check("lifecycle_state inicial es ACTIVE",
          zone.lifecycle_state == ZoneLifecycleState.ACTIVE)
    check("touch_count inicial es 0", zone.touch_count == 0)
    check("polarity_flipped inicial es False", not zone.polarity_flipped)
    check("is_exhausted() inicial es False", not zone.is_exhausted())
    check("effective_direction sin flip == direction",
          zone.effective_direction == zone.direction)

    # Simular primer toque
    seq1 = zone.register_touch(price=97248.0, obi=0.25, cum_delta=847.3)
    check("primer toque retorna sequence=1", seq1 == 1)
    check("touch_count es 1 tras primer toque", zone.touch_count == 1)
    check("zone aún no exhausted tras 1 toque", not zone.is_exhausted())

    # Simular breakout → zona pasa a HARVESTING
    zone.register_breakout(breakout_price=97170.0)
    check("lifecycle_state es HARVESTING después de breakout",
          zone.lifecycle_state == ZoneLifecycleState.HARVESTING)
    check("polarity_flipped es True", zone.polarity_flipped)
    check("effective_direction flippeado (bull→bear)",
          zone.effective_direction == "bearish")
    check("harvest_expiry_ts establecido", zone.harvest_expiry_ts is not None)
    check("flip_price registrado", zone.flip_price == 97170.0)

    # Simular segundo toque
    seq2 = zone.register_touch(price=97220.0, obi=-0.12, cum_delta=-450.0)
    check("segundo toque retorna sequence=2", seq2 == 2)
    check("prior_outcomes después de toque 1 (outcome=PENDING)",
          zone.prior_outcomes == [] or all(o == "PENDING" for o in zone.prior_outcomes))

    # Simular tercer toque
    seq3 = zone.register_touch(price=97215.0, obi=-0.08, cum_delta=-200.0)
    check("tercer toque retorna sequence=3", seq3 == 3)
    check("zona EXHAUSTED tras 3 toques",
          zone.lifecycle_state == ZoneLifecycleState.EXHAUSTED)
    check("is_exhausted() retorna True",  zone.is_exhausted())

    # Verificar touch_history
    check("touch_history tiene 3 registros", len(zone.touch_history) == 3)
    check("TouchRecord tiene touch_sequence correcto",
          zone.touch_history[0].touch_sequence == 1
          and zone.touch_history[1].touch_sequence == 2
          and zone.touch_history[2].touch_sequence == 3)
    check("2do TouchRecord tiene polarity_flipped=True",
          zone.touch_history[1].polarity_flipped is True)

except Exception as e:
    check("ActiveZone multi-touch — SIN EXCEPCIÓN", False, str(e))

# ─────────────────────────────────────────────────────────────────────────────
# 2B. VERIFICAR CLEANUP: HARVESTING SOBREVIVE AL TIMEOUT CLÁSICO
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 2B. Cleanup tolerante a HARVESTING ─────────────────────────────────")

try:
    detector = TripleCoincidenceDetector(config={"retest_timeout_bars": 10})

    old_idx = 100
    current_idx = 200  # claramente fuera del timeout clásico

    zone_active = ActiveZone(
        candle_index=old_idx,
        zone_top=100.0,
        zone_bottom=99.0,
        direction="bullish",
        detection_timestamp=int(time.time()),
        vwap_at_detection=99.5,
        atr_at_detection=1.0,
        key_candle={},
        accumulation_zone={"quality_score": 0.7},
        mini_trend={},
        zone_id="cleanup_active",
    )
    zone_harvesting = ActiveZone(
        candle_index=old_idx,
        zone_top=200.0,
        zone_bottom=199.0,
        direction="bearish",
        detection_timestamp=int(time.time()),
        vwap_at_detection=199.5,
        atr_at_detection=1.0,
        key_candle={},
        accumulation_zone={"quality_score": 0.7},
        mini_trend={},
        zone_id="cleanup_harvesting",
    )
    zone_harvesting.register_breakout(breakout_price=201.0)

    detector.active_zones = [zone_active, zone_harvesting]
    detector._cleanup_expired_zones(current_idx=current_idx)

    ids = [z.zone_id for z in detector.active_zones]
    check("zona ACTIVE expirada por timeout clásico se elimina", "cleanup_active" not in ids)
    check("zona HARVESTING se conserva aunque exceda timeout clásico", "cleanup_harvesting" in ids)

    # Forzar expiración por TTL post-flip: ahora sí debe desaparecer.
    zone_harvesting.harvest_expiry_ts = time.time() - 1
    detector._cleanup_expired_zones(current_idx=current_idx)
    ids_after_ttl = [z.zone_id for z in detector.active_zones]
    check("zona HARVESTING expirada por TTL se elimina", "cleanup_harvesting" not in ids_after_ttl)

except Exception as e:
    check("Cleanup HARVESTING — SIN EXCEPCIÓN", False, str(e))

# ─────────────────────────────────────────────────────────────────────────────
# 2C. VERIFICAR FLIP AUTOMÁTICO DESDE check_intra_candle_retest
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 2C. Flip automático por breakout tick-level ─────────────────────────")

try:
    detector = TripleCoincidenceDetector(
        config={
            "retest_timeout_bars": 50,
            "breakout_confirm_atr_buffer": 0.05,  # umbral = 5% ATR
        }
    )
    zone = ActiveZone(
        candle_index=10,
        zone_top=100.0,
        zone_bottom=99.0,
        direction="bullish",
        detection_timestamp=int(time.time()),
        vwap_at_detection=99.5,
        atr_at_detection=1.0,
        key_candle={},
        accumulation_zone={"quality_score": 0.8},
        mini_trend={},
        zone_id="flip_from_tick",
    )
    detector.active_zones = [zone]

    # Tick apenas fuera de la zona, pero dentro del buffer: NO debe flippear.
    detector.check_intra_candle_retest(price=98.96, timestamp_ms=int(time.time() * 1000))
    check("tick fuera por ruido (< buffer) NO flippea",
          zone.lifecycle_state == ZoneLifecycleState.ACTIVE)

    # Tick por debajo del umbral con buffer: ahora sí debe gatillar register_breakout.
    detector.check_intra_candle_retest(price=98.94, timestamp_ms=int(time.time() * 1000))
    check("breakout tick-level cambia lifecycle_state a HARVESTING",
          zone.lifecycle_state == ZoneLifecycleState.HARVESTING)
    check("breakout tick-level marca polarity_flipped=True",
          zone.polarity_flipped is True)
    check("breakout tick-level registra flip_price",
          zone.flip_price == 98.94)

except Exception as e:
    check("Flip automático tick-level — SIN EXCEPCIÓN", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 3. VERIFICAR DeferredOutcomeMonitor CON CAMPOS DE SECUENCIALIDAD
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 3. DeferredOutcomeMonitor — campos de secuencialidad ─────────────────")

try:
    from cgalpha_v3.domain.deferred_outcome_monitor import PendingLabel

    # Crear PendingLabel con campos de Shadow Harvesting
    pl = PendingLabel(
        sample_id="re_test_001",
        capture_ts=time.time(),
        zone_top=97250.0,
        zone_bottom=97180.0,
        zone_direction="bullish",
        zone_width_atr=0.85,
        atr_at_detection=83.0,
        lookahead_bars=8,
        entry_price=97245.0,
        touch_sequence=2,
        polarity_flipped=True,
        prior_touch_outcomes=["BREAKOUT"],
        zone_original_direction="bullish",
        hours_since_flip=4.2,
    )
    check("PendingLabel acepta touch_sequence", pl.touch_sequence == 2)
    check("PendingLabel acepta polarity_flipped", pl.polarity_flipped is True)
    check("PendingLabel acepta prior_touch_outcomes",
          pl.prior_touch_outcomes == ["BREAKOUT"])
    check("PendingLabel acepta hours_since_flip", pl.hours_since_flip == 4.2)
    check("PendingLabel acepta zone_original_direction",
          pl.zone_original_direction == "bullish")

except ImportError as e:
    check("PendingLabel importado", False, str(e))
except TypeError as e:
    check("PendingLabel acepta nuevos campos", False, str(e))
except Exception as e:
    check("DeferredOutcomeMonitor — SIN EXCEPCIÓN", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 4. VERIFICAR GENERACIÓN DE touch_context EN JSONL
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 4. touch_context en el JSONL de entrenamiento ───────────────────────")

try:
    # Simular un flush parcial: si DeferredOutcomeMonitor usa training_dataset_v2.jsonl,
    # verificamos que la estructura es correcta sin necesitar el WS real.
    ds_path = Path("aipha_memory/operational/training_dataset_v2.jsonl")
    if ds_path.exists():
        with open(ds_path) as f:
            lines = f.readlines()
        if lines:
            last = json.loads(lines[-1])
            has_touch_ctx = "touch_context" in last
            check("Último sample tiene 'touch_context'", has_touch_ctx,
                  "El campo se añadirá en el próximo retest resuelto")
            if has_touch_ctx:
                tc = last["touch_context"]
                check("touch_context.touch_sequence existe", "touch_sequence" in tc)
                check("touch_context.polarity_flipped existe", "polarity_flipped" in tc)
                check("touch_context.prior_touch_outcomes existe", "prior_touch_outcomes" in tc)
        else:
            print(f"  {WARN} training_dataset_v2.jsonl existe pero está vacío. OK — se llenará en vivo.")
    else:
        print(f"  {WARN} training_dataset_v2.jsonl no existe aún. Se creará con el primer retest resuelto.")

except Exception as e:
    check("Lectura de training_dataset_v2.jsonl", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 5. VERIFICAR CÓDIGO DE live_adapter.py
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 5. Verificación estática de live_adapter.py ─────────────────────────")

adapter_path = Path("cgalpha_v3/application/live_adapter.py")
if adapter_path.exists():
    adapter_code = adapter_path.read_text()
    check("live_adapter contiene 'is_secondary_retest'",
          "is_secondary_retest" in adapter_code,
          "El guard de ShadowTrader no fue aplicado")
    check("live_adapter contiene 'ShadowHarvest'",
          "ShadowHarvest" in adapter_code,
          "El comentario de logging no fue insertado")
    check("live_adapter pasa 'touch_sequence' a register_retest",
          "touch_sequence=assigned_seq" in adapter_code
          or "touch_sequence=touch_seq" in adapter_code,
          "register_retest no recibe touch_sequence")
else:
    check("live_adapter.py existe", False, str(adapter_path))


# ─────────────────────────────────────────────────────────────────────────────
# RESUMEN
# ─────────────────────────────────────────────────────────────────────────────
total = len(results)
passed = sum(1 for ok, _ in results if ok)
failed = total - passed

print(f"\n{'─'*60}")
print(f"RESULTADO: {passed}/{total} checks pasaron")

if failed == 0:
    print("\n✅ Shadow Harvesting implementado correctamente.")
    print("   El sistema puede cosechar 2dos/3ros retests de forma silente.")
    print("\n   Próximo paso:")
    print("   python3 -m pytest cgalpha_v3/tests/ -q")
    print("   python3 cgalpha_v3/scripts/launch_shadow_live.py")
else:
    print(f"\n⚠️  {failed} check(s) fallaron. Revisar los mensajes anteriores.")
    print("   Si los fallos son del bloque 4 o 5 (JSONL vacío), es normal —")
    print("   se generarán datos cuando el sistema detecte un retest real.")

print()
