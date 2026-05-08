"""
scripts/patch_deferred_monitor_multitouch.py
=============================================
Shadow Harvesting — Patch 2/3
Objetivo: Extender PendingLabel y build_reentry_snapshot con metadatos de
          secuencialidad (touch_sequence, polarity_flipped, touch_context).

Método: Determinista — sin LLM.
        Las cadenas de búsqueda son fragmentos exactos del código producido
        en la Fase Puente (cronica_desarrollo_cgAlpha.md).

Ejecutar desde la raíz del proyecto:
    python3 scripts/patch_deferred_monitor_multitouch.py
"""

from pathlib import Path
import shutil
import sys

TARGET = Path("cgalpha_v3/domain/deferred_outcome_monitor.py")
BACKUP = TARGET.with_suffix(".py.bak_multitouch")


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 1 — Extender PendingLabel con campos de secuencialidad.
#            Buscamos el campo "resolved: bool = False" (último campo antes
#            de outcome) y añadimos los nuevos campos debajo.
# ─────────────────────────────────────────────────────────────────────────────

# Buscar el campo existente que marca el final del grupo de estado:
OLD_PENDING_LABEL_TAIL = '''    resolved: bool = False
    outcome: Optional[str] = None  # BOUNCE_STRONG | BOUNCE_WEAK | BREAKOUT | INCONCLUSIVE
    resolution_ts: Optional[float] = None
    
    # El snapshot completo se guarda aparte (no en memoria)
    snapshot_path: Optional[str] = None'''

NEW_PENDING_LABEL_TAIL = '''    resolved: bool = False
    outcome: Optional[str] = None  # BOUNCE_STRONG | BOUNCE_WEAK | BREAKOUT | INCONCLUSIVE
    resolution_ts: Optional[float] = None
    
    # El snapshot completo se guarda aparte (no en memoria)
    snapshot_path: Optional[str] = None

    # ── Shadow Harvesting: Secuencialidad multi-toque ──────────────────────
    touch_sequence: int = 1             # 1=primer retest, 2=post-flip, 3=terciario
    polarity_flipped: bool = False      # True si la zona había flippeado de polaridad
    prior_touch_outcomes: list = None   # Outcomes de toques previos (legado histórico)
    zone_original_direction: str = ""   # Dirección original antes del flip
    hours_since_flip: float = 0.0       # Tiempo desde el Breakout confirmado

    def __post_init__(self):
        if self.prior_touch_outcomes is None:
            object.__setattr__(self, "prior_touch_outcomes", [])'''


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 2 — Extender register_retest() para aceptar parámetros de zona
#            y construir el contexto multi-toque.
#
#            Buscamos la firma original y la extendemos con kwargs opcionales.
# ─────────────────────────────────────────────────────────────────────────────

OLD_REGISTER_RETEST_SIG = "    def register_retest(self, snapshot: dict) -> str:"
NEW_REGISTER_RETEST_SIG = '''    def register_retest(
        self,
        snapshot: dict,
        touch_sequence: int = 1,
        polarity_flipped: bool = False,
        prior_touch_outcomes: list = None,
        zone_original_direction: str = "",
        flip_ts: float = None,
    ) -> str:
        """
        Registra un nuevo retest para monitoreo diferido.
        
        Parámetros nuevos (Shadow Harvesting):
          touch_sequence:          1 = primer retest, 2 = post-flip, 3 = terciario
          polarity_flipped:        True si la zona había cambiado de polaridad antes de este toque
          prior_touch_outcomes:    Lista de outcomes de toques previos
          zone_original_direction: Dirección original de la zona (antes del flip)
          flip_ts:                 Unix timestamp del Breakout que causó el flip
        """'''


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 3 — Dentro de register_retest(), extender el PendingLabel creado
#            con los nuevos campos de secuencialidad.
#
#            Buscamos la construcción del PendingLabel y añadimos los nuevos kwargs.
# ─────────────────────────────────────────────────────────────────────────────

OLD_PENDING_LABEL_INIT = '''        label = PendingLabel(
            sample_id=snapshot["_meta"]["sample_id"],
            capture_ts=snapshot["_meta"]["capture_ts_unix_ms"] / 1000.0,
            zone_top=zg["zone_top"],
            zone_bottom=zg["zone_bottom"],
            zone_direction=zg["direction"],
            zone_width_atr=zone_width_atr,
            atr_at_detection=cl["atr_at_detection"],
            lookahead_bars=lookahead,
            entry_price=l2["retest_price"],
            snapshot_path=f"aipha_memory/snapshots/{snapshot['_meta']['sample_id']}.json",
        )'''

NEW_PENDING_LABEL_INIT = '''        import time as _time
        hours_since = 0.0
        if flip_ts is not None:
            hours_since = (_time.time() - flip_ts) / 3600.0

        label = PendingLabel(
            sample_id=snapshot["_meta"]["sample_id"],
            capture_ts=snapshot["_meta"]["capture_ts_unix_ms"] / 1000.0,
            zone_top=zg["zone_top"],
            zone_bottom=zg["zone_bottom"],
            zone_direction=zg["direction"],
            zone_width_atr=zone_width_atr,
            atr_at_detection=cl["atr_at_detection"],
            lookahead_bars=lookahead,
            entry_price=l2["retest_price"],
            snapshot_path=f"aipha_memory/snapshots/{snapshot['_meta']['sample_id']}.json",
            # ── Shadow Harvesting ──────────────────────────────────────────
            touch_sequence=touch_sequence,
            polarity_flipped=polarity_flipped,
            prior_touch_outcomes=list(prior_touch_outcomes or []),
            zone_original_direction=zone_original_direction or zg["direction"],
            hours_since_flip=round(hours_since, 2),
        )'''


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 4 — En _flush_resolved(), añadir touch_context al snapshot guardado
#            en training_dataset_v2.jsonl.
#
#            Buscamos donde se inyecta el outcome y añadimos touch_context.
# ─────────────────────────────────────────────────────────────────────────────

OLD_OUTCOME_INJECTION = '''                # Inyectar outcome  
                snapshot["outcome"] = {
                    "label": label.outcome,
                    "mfe": round(label.mfe, 4),
                    "mae": round(label.mae, 4),
                    "mfe_atr": round(label.mfe / label.atr_at_detection, 4),
                    "mae_atr": round(label.mae / label.atr_at_detection, 4),
                    "bars_to_resolution": label.bars_elapsed,
                    "resolution_ts": label.resolution_ts,
                    "lookahead_bars_used": label.lookahead_bars,
                }'''

NEW_OUTCOME_INJECTION = '''                # Inyectar outcome  
                snapshot["outcome"] = {
                    "label": label.outcome,
                    "mfe": round(label.mfe, 4),
                    "mae": round(label.mae, 4),
                    "mfe_atr": round(label.mfe / label.atr_at_detection, 4),
                    "mae_atr": round(label.mae / label.atr_at_detection, 4),
                    "bars_to_resolution": label.bars_elapsed,
                    "resolution_ts": label.resolution_ts,
                    "lookahead_bars_used": label.lookahead_bars,
                }

                # ── Shadow Harvesting: contexto de secuencialidad ─────────
                snapshot["touch_context"] = {
                    "touch_sequence": label.touch_sequence,
                    "polarity_flipped": label.polarity_flipped,
                    "zone_original_direction": label.zone_original_direction,
                    "effective_direction": (
                        ("bearish" if label.zone_original_direction == "bullish" else "bullish")
                        if label.polarity_flipped
                        else label.zone_original_direction
                    ),
                    "prior_touch_outcomes": label.prior_touch_outcomes,
                    "hours_since_flip": label.hours_since_flip,
                    "is_secondary_retest": label.touch_sequence > 1,
                    "is_tertiary_retest": label.touch_sequence > 2,
                }'''


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 5 — En _persist_pending(), serializar los nuevos campos de PendingLabel
# ─────────────────────────────────────────────────────────────────────────────

OLD_PERSIST_ITEM = '''                pending_data.append({
                    "sample_id": label.sample_id,
                    "capture_ts": label.capture_ts,
                    "zone_top": label.zone_top,
                    "zone_bottom": label.zone_bottom,
                    "zone_direction": label.zone_direction,
                    "zone_width_atr": label.zone_width_atr,
                    "atr_at_detection": label.atr_at_detection,
                    "lookahead_bars": label.lookahead_bars,
                    "bars_elapsed": label.bars_elapsed,
                    "mfe": label.mfe,
                    "mae": label.mae,
                    "entry_price": label.entry_price,
                    "snapshot_path": label.snapshot_path,
                })'''

NEW_PERSIST_ITEM = '''                pending_data.append({
                    "sample_id": label.sample_id,
                    "capture_ts": label.capture_ts,
                    "zone_top": label.zone_top,
                    "zone_bottom": label.zone_bottom,
                    "zone_direction": label.zone_direction,
                    "zone_width_atr": label.zone_width_atr,
                    "atr_at_detection": label.atr_at_detection,
                    "lookahead_bars": label.lookahead_bars,
                    "bars_elapsed": label.bars_elapsed,
                    "mfe": label.mfe,
                    "mae": label.mae,
                    "entry_price": label.entry_price,
                    "snapshot_path": label.snapshot_path,
                    # ── Shadow Harvesting ──────────────────────────────────
                    "touch_sequence": label.touch_sequence,
                    "polarity_flipped": label.polarity_flipped,
                    "prior_touch_outcomes": label.prior_touch_outcomes,
                    "zone_original_direction": label.zone_original_direction,
                    "hours_since_flip": label.hours_since_flip,
                })'''


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 6 — En _load_pending(), deserializar los nuevos campos con defaults
#            seguros (retrocompatibilidad con archivos previos sin estos campos)
# ─────────────────────────────────────────────────────────────────────────────

OLD_LOAD_LINE = "            self.pending.append(PendingLabel(**item))"
NEW_LOAD_LINE = '''            # Compatibilidad hacia atrás: añadir defaults para campos nuevos
            item.setdefault("touch_sequence", 1)
            item.setdefault("polarity_flipped", False)
            item.setdefault("prior_touch_outcomes", [])
            item.setdefault("zone_original_direction", item.get("zone_direction", ""))
            item.setdefault("hours_since_flip", 0.0)
            self.pending.append(PendingLabel(**item))'''


# ─────────────────────────────────────────────────────────────────────────────
# APLICAR PATCHES
# ─────────────────────────────────────────────────────────────────────────────

PATCHES = [
    (OLD_PENDING_LABEL_TAIL, NEW_PENDING_LABEL_TAIL,
     "Bloque 1: PendingLabel extendido con touch_sequence + polarity_flipped"),
    (OLD_REGISTER_RETEST_SIG, NEW_REGISTER_RETEST_SIG,
     "Bloque 2: register_retest() con nuevos kwargs de secuencialidad"),
    (OLD_PENDING_LABEL_INIT, NEW_PENDING_LABEL_INIT,
     "Bloque 3: PendingLabel.__init__ incluye campos de Shadow Harvesting"),
    (OLD_OUTCOME_INJECTION, NEW_OUTCOME_INJECTION,
     "Bloque 4: touch_context añadido al JSONL al resolver outcome"),
    (OLD_PERSIST_ITEM, NEW_PERSIST_ITEM,
     "Bloque 5: _persist_pending() serializa campos de secuencialidad"),
    (OLD_LOAD_LINE, NEW_LOAD_LINE,
     "Bloque 6: _load_pending() con defaults retrocompatibles"),
]


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

    for old, new, label in PATCHES:
        count = content.count(old)
        if count == 1:
            content = content.replace(old, new, 1)
            applied.append(f"✓ {label}")
        elif count == 0:
            failed.append(f"✗ No encontrado: {label}")
        else:
            failed.append(f"✗ Múltiples ocurrencias ({count}x) — omitido: {label}")

    if failed:
        print("⚠️  Advertencias:")
        for f in failed:
            print(f"   {f}")
        print()

    if applied:
        TARGET.write_text(content, encoding="utf-8")
        new_len = len(content)
        print(f"✅ {TARGET} actualizado ({original_len} → {new_len} bytes)")
        print("\nPatches aplicados:")
        for a in applied:
            print(f"   {a}")
    else:
        print("❌ Ningún patch aplicado. Revirtiendo.")
        shutil.copy2(BACKUP, TARGET)
        sys.exit(1)

    print("\n⚡ Siguiente paso:")
    print("   python3 scripts/patch_live_adapter_multitouch.py")


if __name__ == "__main__":
    apply()
