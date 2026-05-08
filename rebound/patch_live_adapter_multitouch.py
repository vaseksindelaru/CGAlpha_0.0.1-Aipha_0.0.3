"""
scripts/patch_live_adapter_multitouch.py
=========================================
Shadow Harvesting — Patch 3/3
Objetivo: En live_adapter.py, cuando se detecta un retest con touch_sequence > 1
          (zona en modo HARVESTING), saltarse ShadowTrader y enrutar silenciosamente
          solo al DeferredOutcomeMonitor.

          El capital y las estadísticas de ejecución del primer retest
          permanecen INTACTOS. Los 2do/3er toques solo cosechan datos.

Método: Determinista.

Ejecutar desde la raíz del proyecto:
    python3 scripts/patch_live_adapter_multitouch.py
"""

from pathlib import Path
import shutil
import sys

TARGET = Path("cgalpha_v3/application/live_adapter.py")
BACKUP = TARGET.with_suffix(".py.bak_multitouch")


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 1 — Modificar el método que dispara la ejecución al detectar retest.
#
#            El método puede llamarse _on_retest_detected, _dispatch_kline,
#            o _process_retest. Buscamos el patrón que llama a ShadowTrader.
#
#            ANTES: todos los retests van a ShadowTrader → DeferredMonitor
#            DESPUÉS: solo touch_sequence == 1 → ShadowTrader
#                     touch_sequence > 1       → DeferredMonitor (silente)
# ─────────────────────────────────────────────────────────────────────────────

# Patrón que encontramos: la llamada al ShadowTrader después de Oracle.predict()
# Buscamos la línea que llama open_shadow_trade o similar, precedida por
# la evaluación de confianza del Oracle:

OLD_SHADOW_TRADE_CALL = '''        if oracle_result and oracle_result.confidence >= self.min_oracle_confidence:
            self.shadow_trader.open_shadow_trade(
                entry_price=current_price,
                direction=1 if zone.direction == "bullish" else -1,
                atr=zone.atr_at_detection,
                signal_data=signal_data,
            )'''

NEW_SHADOW_TRADE_CALL = '''        # ── Shadow Harvesting: determinar touch_sequence ─────────────────────
        from cgalpha_v3.infrastructure.signal_detector.triple_coincidence import (
            ZoneLifecycleState,
        )
        touch_seq = zone.touch_count + 1  # +1 porque register_touch() aún no fue llamado
        is_secondary_retest = (
            hasattr(zone, "lifecycle_state")
            and zone.lifecycle_state == ZoneLifecycleState.HARVESTING
        )
        if is_secondary_retest:
            touch_seq = max(2, zone.touch_count + 1)

        if oracle_result and oracle_result.confidence >= self.min_oracle_confidence:
            if not is_secondary_retest:
                # ── Primer toque: ejecutar normalmente ────────────────────
                self.shadow_trader.open_shadow_trade(
                    entry_price=current_price,
                    direction=1 if zone.direction == "bullish" else -1,
                    atr=zone.atr_at_detection,
                    signal_data=signal_data,
                )
            else:
                # ── 2do/3er toque: NO ejecutar, solo loguear ──────────────
                import logging as _log
                _log.getLogger("live_adapter").info(
                    f"[ShadowHarvest] Toque #{touch_seq} en zona {zone.zone_id} "
                    f"(polarity_flipped={zone.polarity_flipped}): "
                    f"confianza {oracle_result.confidence:.3f} — solo cosecha, sin ejecución"
                )'''


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 2 — Pasar touch_sequence al DeferredOutcomeMonitor.
#
#            Buscamos la llamada a self.deferred_monitor.register_retest()
#            y añadimos los nuevos kwargs.
# ─────────────────────────────────────────────────────────────────────────────

OLD_REGISTER_CALL = "            self.deferred_monitor.register_retest(snapshot)"
NEW_REGISTER_CALL = '''            # Registrar toque en la zona (actualiza touch_count y touch_history)
            if hasattr(zone, "register_touch"):
                obi_val = signal_data.get("obi_10", 0.0)
                delta_val = signal_data.get("cumulative_delta", 0.0)
                assigned_seq = zone.register_touch(
                    price=current_price,
                    obi=obi_val,
                    cum_delta=delta_val,
                )
            else:
                assigned_seq = 1

            self.deferred_monitor.register_retest(
                snapshot,
                touch_sequence=assigned_seq,
                polarity_flipped=getattr(zone, "polarity_flipped", False),
                prior_touch_outcomes=getattr(zone, "prior_outcomes", []),
                zone_original_direction=getattr(zone, "direction", ""),
                flip_ts=getattr(zone, "flip_ts", None),
            )'''


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 3 — Alternativa si el patrón de búsqueda del Bloque 1 no coincide.
#            Buscamos el patrón más simple con ShadowTrader directo:
# ─────────────────────────────────────────────────────────────────────────────

OLD_SHADOW_ALT = "        self.shadow_trader.open_shadow_trade("
NEW_SHADOW_ALT = '''        # ── Shadow Harvesting guard ───────────────────────────────────────────
        from cgalpha_v3.infrastructure.signal_detector.triple_coincidence import (
            ZoneLifecycleState,
        )
        _is_secondary = (
            hasattr(zone, "lifecycle_state")
            and zone.lifecycle_state == ZoneLifecycleState.HARVESTING
        )
        if not _is_secondary:
            self.shadow_trader.open_shadow_trade('''

OLD_SHADOW_ALT_CLOSE = '''            )'''
# No cerrar el if aquí — el bloque ya viene cerrado correctamente.


# ─────────────────────────────────────────────────────────────────────────────
# APLICAR PATCHES
# ─────────────────────────────────────────────────────────────────────────────

def apply():
    if not TARGET.exists():
        print(f"❌ No se encontró: {TARGET}")
        sys.exit(1)

    shutil.copy2(TARGET, BACKUP)
    print(f"✅ Backup creado: {BACKUP}\n")

    content = TARGET.read_text(encoding="utf-8")
    original_len = len(content)
    applied = []
    failed = []

    # Patch 1 — Bloqueo condicional de ShadowTrader
    if OLD_SHADOW_TRADE_CALL in content:
        content = content.replace(OLD_SHADOW_TRADE_CALL, NEW_SHADOW_TRADE_CALL, 1)
        applied.append("Bloque 1 (completo): ShadowTrader bloqueado para touch_sequence > 1")
    else:
        # Fallback: patrón alternativo más simple
        count_alt = content.count(OLD_SHADOW_ALT)
        if count_alt == 1:
            content = content.replace(OLD_SHADOW_ALT, NEW_SHADOW_ALT, 1)
            applied.append("Bloque 1 (fallback): Guard de is_secondary insertado antes de open_shadow_trade")
        else:
            failed.append(
                "Bloque 1: No se encontró ni el patrón completo ni el alternativo. "
                "Busca manualmente 'open_shadow_trade' y añade el guard is_secondary."
            )

    # Patch 2 — Pasar touch_sequence a DeferredOutcomeMonitor
    if OLD_REGISTER_CALL in content:
        content = content.replace(OLD_REGISTER_CALL, NEW_REGISTER_CALL, 1)
        applied.append("Bloque 2: register_retest() recibe touch_sequence y context")
    else:
        failed.append(
            "Bloque 2: 'self.deferred_monitor.register_retest(snapshot)' no encontrado. "
            "Busca manualmente register_retest y añade los kwargs."
        )

    if failed:
        print("⚠️  Advertencias — intervención manual requerida:")
        for f in failed:
            print(f"   ✗ {f}")
        print()

    if applied:
        TARGET.write_text(content, encoding="utf-8")
        new_len = len(content)
        print(f"✅ {TARGET} actualizado ({original_len} → {new_len} bytes)")
        print("\nPatches aplicados:")
        for a in applied:
            print(f"   ✓ {a}")
    else:
        print("❌ Ningún patch aplicado. Revirtiendo.")
        shutil.copy2(BACKUP, TARGET)
        sys.exit(1)

    print("\n⚡ Siguiente paso:")
    print("   python3 scripts/verify_shadow_harvesting.py")


if __name__ == "__main__":
    apply()
