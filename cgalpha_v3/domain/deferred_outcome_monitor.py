"""
CGAlpha v3 — Deferred Outcome Monitor
======================================
Monitorea el precio post-entrada y asigna labels cuando se cumplen
las condiciones de resolución. NUNCA asigna label por defecto.

Etiquetado terciario:
  - BOUNCE_STRONG: escape decisivo (> 0.5 ATR fuera de zona)
  - BOUNCE_WEAK:   rebote marginal (MFE > 0.3 ATR pero sin escape decisivo)
  - BREAKOUT:      zona destruida (precio cruza el lado opuesto)
  - INCONCLUSIVE:  sin movimiento suficiente → EXCLUIDO del training set

Lookahead adaptativo: proporcional al ancho de la zona en ATRs.
"""

import gzip
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from pathlib import Path

logger = logging.getLogger("deferred_labeler")

PENDING_LABELS_PATH = "aipha_memory/operational/pending_labels.json"
COMPLETED_SAMPLES_PATH = "aipha_memory/operational/training_dataset_v2.jsonl"
RAW_BUFFERS_DIR = "aipha_memory/raw_buffers"


def adaptive_lookahead(zone_width_atr: float) -> int:
    """
    Zonas estrechas se resuelven rápido. Zonas amplias necesitan más tiempo.
    Retorna número de barras de 5min (o 1min live) a esperar.

    zone_width_atr=0.3 → 6 bars
    zone_width_atr=1.0 → 8 bars
    zone_width_atr=2.0 → 11 bars
    """
    return max(5, min(20, int(5 + zone_width_atr * 3)))


@dataclass
class PendingLabel:
    """Un sample esperando resolución de su outcome."""
    sample_id: str
    capture_ts: float            # Unix seconds
    zone_top: float
    zone_bottom: float
    zone_direction: str          # 'bullish' | 'bearish'
    zone_width_atr: float
    atr_at_detection: float
    lookahead_bars: int
    entry_price: float
    snapshot_path: str           # Path al ReentrySnapshot JSON completo
    bars_elapsed: int = 0
    mfe: float = 0.0            # Max favorable excursion (abs price)
    mae: float = 0.0            # Max adverse excursion (abs price)
    resolved: bool = False
    outcome: Optional[str] = None
    resolution_ts: Optional[float] = None


class DeferredOutcomeMonitor:
    """
    Monitorea el precio post-entrada y asigna labels cuando
    se cumplen las condiciones de resolución.

    Diseño clave: los samples permanecen 'pending' hasta que
    el precio valida o invalida la zona. NUNCA se asigna un
    label por defecto (eliminando el fallback 'BOUNCE' de L965).
    """

    def __init__(self):
        self.pending: List[PendingLabel] = []
        self._load_pending()

    # ── Public API ──────────────────────────────────────────────

    def register_retest(self, snapshot: dict, raw_buffer: Optional[list] = None) -> str:
        """
        Registra un nuevo retest para monitoreo diferido.
        Persiste el snapshot completo en disco y opcionalmente el raw L2 buffer.

        Args:
            snapshot: ReentrySnapshot completo (schema v2.0)
            raw_buffer: Lista cruda del ring buffer L2 (para re-derivación futura)

        Returns:
            sample_id para tracking
        """
        meta = snapshot.get("_meta", {})
        sample_id = meta.get("sample_id", f"re_{int(time.time())}")
        zg = snapshot.get("zone_geometry", {})
        cl = snapshot.get("clearance", {})
        l2 = snapshot.get("l2_snapshot_at_touch", {})

        zone_width_atr = zg.get("zone_width_atr", 1.0)
        lookahead = adaptive_lookahead(zone_width_atr)

        # Path para el snapshot completo
        snap_path = f"aipha_memory/snapshots/{sample_id}.json"
        snap_file = Path(snap_path)
        snap_file.parent.mkdir(parents=True, exist_ok=True)
        snap_file.write_text(json.dumps(snapshot, indent=2, default=str))

        # Persistir raw L2 buffer comprimido (~8KB/retest)
        if raw_buffer:
            raw_path = Path(RAW_BUFFERS_DIR) / f"{sample_id}.json.gz"
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(raw_path, 'wt') as f:
                json.dump(raw_buffer, f, default=str)

        label = PendingLabel(
            sample_id=sample_id,
            capture_ts=meta.get("capture_ts_unix_ms", time.time() * 1000) / 1000.0,
            zone_top=zg.get("zone_top", 0.0),
            zone_bottom=zg.get("zone_bottom", 0.0),
            zone_direction=zg.get("direction", "bullish"),
            zone_width_atr=zone_width_atr,
            atr_at_detection=cl.get("atr_at_detection", 1.0),
            lookahead_bars=lookahead,
            entry_price=l2.get("retest_price", 0.0),
            snapshot_path=snap_path,
        )

        self.pending.append(label)
        self._persist_pending()

        logger.info(
            f"📋 Registered pending label: {sample_id} "
            f"(lookahead={lookahead} bars, direction={label.zone_direction})"
        )
        return sample_id

    def tick(self, current_price: float, bar_closed: bool = False) -> List[dict]:
        """
        Llamar en cada update de precio (o al cierre de cada vela).
        Evalúa si algún pending label se resolvió.

        Args:
            current_price: precio actual (close de la vela o tick price)
            bar_closed: True si una vela acaba de cerrar (incrementa bars_elapsed)

        Returns:
            Lista de samples resueltos en este tick (para logging/GUI)
        """
        newly_resolved = []

        for label in self.pending:
            if label.resolved:
                continue

            # Actualizar MFE/MAE
            if label.zone_direction == "bullish":
                favorable = current_price - label.entry_price
                adverse = label.entry_price - current_price
            else:
                favorable = label.entry_price - current_price
                adverse = current_price - label.entry_price

            label.mfe = max(label.mfe, favorable)
            label.mae = max(label.mae, adverse)

            if bar_closed:
                label.bars_elapsed += 1

            # Evaluar condiciones de resolución
            outcome = self._evaluate(label, current_price)
            if outcome is not None:
                label.resolved = True
                label.outcome = outcome
                label.resolution_ts = time.time()
                newly_resolved.append(label)
                logger.info(
                    f"🏷️ Label resolved: {label.sample_id} → {outcome} "
                    f"(MFE={label.mfe:.2f}, MAE={label.mae:.2f}, "
                    f"bars={label.bars_elapsed}/{label.lookahead_bars})"
                )

        if newly_resolved:
            self._flush_resolved(newly_resolved)
            self._persist_pending()

        return [
            {
                "sample_id": l.sample_id,
                "outcome": l.outcome,
                "mfe": l.mfe,
                "mae": l.mae,
                "bars_elapsed": l.bars_elapsed,
            }
            for l in newly_resolved
        ]

    def get_pending_count(self) -> int:
        """Retorna cuántos labels están pendientes de resolución."""
        return sum(1 for p in self.pending if not p.resolved)

    def get_resolved_count(self) -> int:
        """Retorna cuántos labels han sido resueltos."""
        return sum(1 for p in self.pending if p.resolved)

    def get_pending_summary(self) -> List[dict]:
        """Retorna resumen de pending labels para la GUI."""
        return [
            {
                "sample_id": p.sample_id,
                "direction": p.zone_direction,
                "entry_price": p.entry_price,
                "bars_elapsed": p.bars_elapsed,
                "lookahead_bars": p.lookahead_bars,
                "mfe": round(p.mfe, 2),
                "mae": round(p.mae, 2),
            }
            for p in self.pending
            if not p.resolved
        ]

    # ── Internal Logic ──────────────────────────────────────────

    def _evaluate(self, label: PendingLabel, price: float) -> Optional[str]:
        """
        Determina el outcome sin contaminación.
        Retorna None si aún no se puede resolver.
        """
        atr = label.atr_at_detection
        if atr <= 0:
            atr = label.entry_price * 0.001  # Fallback: 0.1% del precio

        if label.zone_direction == "bullish":
            # BREAKOUT: precio perforó el fondo de la zona
            if price < label.zone_bottom:
                return "BREAKOUT"

            # BOUNCE_STRONG: precio escapó decisivamente hacia arriba
            if price > label.zone_top + 0.5 * atr:
                return "BOUNCE_STRONG"

            # Lookahead expirado
            if label.bars_elapsed >= label.lookahead_bars:
                if label.mfe > 0.3 * atr:
                    return "BOUNCE_WEAK"
                return "INCONCLUSIVE"

        else:  # bearish
            # BREAKOUT: precio rompió hacia arriba
            if price > label.zone_top:
                return "BREAKOUT"

            # BOUNCE_STRONG: precio escapó decisivamente hacia abajo
            if price < label.zone_bottom - 0.5 * atr:
                return "BOUNCE_STRONG"

            # Lookahead expirado
            if label.bars_elapsed >= label.lookahead_bars:
                if label.mfe > 0.3 * atr:
                    return "BOUNCE_WEAK"
                return "INCONCLUSIVE"

        return None  # Aún no resuelto

    def _flush_resolved(self, resolved: List[PendingLabel]):
        """Escribe samples resueltos en el dataset de entrenamiento v2."""
        path = Path(COMPLETED_SAMPLES_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "a") as f:
            for label in resolved:
                # Cargar snapshot original
                snap_file = Path(label.snapshot_path)
                if not snap_file.exists():
                    logger.warning(f"⚠️ Snapshot not found: {label.snapshot_path}")
                    continue

                snapshot = json.loads(snap_file.read_text())

                # Inyectar outcome
                snapshot["outcome"] = {
                    "label": label.outcome,
                    "mfe": round(label.mfe, 4),
                    "mae": round(label.mae, 4),
                    "mfe_atr": round(label.mfe / label.atr_at_detection, 4) if label.atr_at_detection > 0 else 0.0,
                    "mae_atr": round(label.mae / label.atr_at_detection, 4) if label.atr_at_detection > 0 else 0.0,
                    "bars_to_resolution": label.bars_elapsed,
                    "resolution_ts": label.resolution_ts,
                    "lookahead_bars_used": label.lookahead_bars,
                }

                f.write(json.dumps(snapshot, default=str) + "\n")

        logger.info(f"💾 Flushed {len(resolved)} resolved samples to {COMPLETED_SAMPLES_PATH}")

    def _persist_pending(self):
        """Guarda estado de pending labels para sobrevivir reinicios."""
        path = Path(PENDING_LABELS_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)

        pending_data = []
        for label in self.pending:
            if not label.resolved:
                pending_data.append({
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
                })

        path.write_text(json.dumps(pending_data, indent=2))

    def _load_pending(self):
        """Recarga pending labels sobrevivientes a un reinicio."""
        path = Path(PENDING_LABELS_PATH)
        if not path.exists():
            return

        try:
            data = json.loads(path.read_text())
            for item in data:
                self.pending.append(PendingLabel(**item))

            if self.pending:
                logger.info(f"📋 Recovered {len(self.pending)} pending labels from disk.")
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"⚠️ Could not load pending labels: {e}")
