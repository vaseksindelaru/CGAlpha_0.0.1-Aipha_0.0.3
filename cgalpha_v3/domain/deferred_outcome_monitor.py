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
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("deferred_labeler")

# __file__ = cgalpha_v3/domain/deferred_outcome_monitor.py
# parent = domain/, parent.parent = cgalpha_v3/, parent.parent.parent = project_root/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PENDING_LABELS_PATH = str(
    _PROJECT_ROOT / "aipha_memory" / "operational" / "pending_labels.json"
)
COMPLETED_SAMPLES_PATH = str(
    _PROJECT_ROOT / "aipha_memory" / "operational" / "training_dataset_v2.jsonl"
)
RAW_BUFFERS_DIR = str(_PROJECT_ROOT / "aipha_memory" / "raw_buffers")


def adaptive_lookahead(zone_width_atr: float) -> int:
    """
    Zonas estrechas se resuelven rápido. Zonas amplias necesitan más tiempo.
    Retorna número de barras de 5min a esperar (D-011: interval_s=300).

    zone_width_atr=0.3 → 5 bars
    zone_width_atr=1.0 → 8 bars
    zone_width_atr=2.0 → 11 bars
    """
    return max(5, min(20, int(5 + zone_width_atr * 3)))


@dataclass
class PendingLabel:
    """Un sample esperando resolución de su outcome."""

    sample_id: str
    capture_ts: float  # Unix seconds
    zone_top: float
    zone_bottom: float
    zone_direction: str  # 'bullish' | 'bearish'
    zone_width_atr: float
    atr_at_detection: float
    lookahead_bars: int
    entry_price: float
    snapshot_path: str = ""  # Path al ReentrySnapshot JSON completo
    bars_elapsed: int = 0
    mfe: float = 0.0  # Max favorable excursion (abs price)
    mae: float = 0.0  # Max adverse excursion (abs price)
    resolved: bool = False
    outcome: Optional[str] = None
    resolution_ts: Optional[float] = None

    # ── Shadow Harvesting: Secuencialidad multi-toque ──────────────────────
    touch_sequence: int = 1
    polarity_flipped: bool = False
    prior_touch_outcomes: list = field(default_factory=list)
    zone_original_direction: str = ""
    hours_since_flip: float = 0.0


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
        self._seen_ids: set = set()
        self._seen_fingerprints: set = set()  # Causal dedup: {ts}_{price}
        self._load_pending()
        self._sync_seen_ids()

    @staticmethod
    def _causal_fingerprint(meta: dict, l2: dict, zg: dict) -> str:
        """Genera huella causal espacio-temporal de un evento físico.

        Dos snapshots con el mismo timestamp y precio de contacto
        representan el mismo evento en el mercado, aunque provengan de
        zonas distintas superpuestas (incluso de disinta polaridad).
        """
        ts = meta.get("capture_ts_unix_ms", 0)
        price = l2.get("retest_price", 0)
        return f"{int(ts)}_{float(price):.2f}"

    def _sync_seen_ids(self):
        """Pre-puebla IDs y huellas causales del dataset persistido."""
        path = Path(COMPLETED_SAMPLES_PATH)
        if not path.exists():
            return
        try:
            with open(path, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        meta = data.get("_meta", {})
                        if "sample_id" in meta:
                            self._seen_ids.add(meta["sample_id"])
                        # Reconstruir huella causal para proteger contra reinicios
                        fp = self._causal_fingerprint(
                            meta,
                            data.get("l2_snapshot_at_touch", {}),
                            data.get("zone_geometry", {}),
                        )
                        self._seen_fingerprints.add(fp)
                    except json.JSONDecodeError:
                        continue
            logger.info(
                f"📊 Dataset sync: {len(self._seen_ids)} IDs, "
                f"{len(self._seen_fingerprints)} huellas causales cargadas."
            )
        except Exception as e:
            logger.error(f"⚠️ Error sincronizando IDs del dataset: {e}")

    # ── Public API ──────────────────────────────────────────────

    def register_retest(
        self,
        snapshot: dict,
        raw_buffer: Optional[list] = None,
        touch_sequence: int = 1,
        polarity_flipped: bool = False,
        prior_touch_outcomes: list = None,
        zone_original_direction: str = "",
        flip_ts: float = None,
    ) -> str:
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
        zg = snapshot.get("zone_geometry", {})
        cl = snapshot.get("clearance", {})
        l2 = snapshot.get("l2_snapshot_at_touch", {})

        sample_id = meta.get("sample_id", f"re_{int(time.time())}")

        # --- DEDUPLICACIÓN DE SEGURIDAD (Triple Barrera) ---
        # 1. Huella causal espacio-temporal (Anti Spatial Multi-Touch)
        #    Mismo instante + mismo precio = mismo evento físico (sin dirección → B-008-v2)
        fingerprint = self._causal_fingerprint(meta, l2, zg)
        if fingerprint in self._seen_fingerprints:
            logger.warning(
                f"🛡️ Spatial Multi-Touch bloqueado: {sample_id} "
                f"(fingerprint={fingerprint} ya registrado)"
            )
            return sample_id

        # 2. Chequeo contra dataset persistido (por sample_id)
        if sample_id in self._seen_ids:
            logger.warning(
                f"⚠️ Intento de registrar ID ya persistido ignorado: {sample_id}"
            )
            return sample_id

        # 3. Chequeo contra cola actual de pending (por sample_id)
        if any(p.sample_id == sample_id for p in self.pending):
            logger.warning(
                f"⚠️ Intento de registrar ID ya en cola pending ignorado: {sample_id}"
            )
            return sample_id

        # ----------------------------------

        zone_width_atr = zg.get("zone_width_atr", 1.0)
        lookahead = adaptive_lookahead(zone_width_atr)

        # Path para el snapshot completo
        snap_path = str(
            _PROJECT_ROOT / "aipha_memory" / "snapshots" / f"{sample_id}.json"
        )
        snap_file = Path(snap_path)
        snap_file.parent.mkdir(parents=True, exist_ok=True)
        snap_file.write_text(json.dumps(snapshot, indent=2, default=str))

        # Persistir raw L2 buffer comprimido (~8KB/retest)
        if raw_buffer is not None:
            raw_path = Path(RAW_BUFFERS_DIR) / f"{sample_id}.json.gz"
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(raw_path, "wt") as f:
                json.dump(raw_buffer, f, default=str)

        hours_since = 0.0
        if flip_ts is not None:
            # D-014: Usar capture_ts_unix_ms del snapshot si está disponible
            # para que hours_since_flip se calcule con el mismo reloj (Binance
            # event time) que el resto del sample. Si no está, fallback a time.time().
            capture_ts_s = meta.get("capture_ts_unix_ms", time.time() * 1000) / 1000.0
            hours_since = (capture_ts_s - flip_ts) / 3600.0

        label = PendingLabel(
            sample_id=sample_id,
            # D-014: Usar capture_ts_unix_ms del snapshot (Binance event time).
            # Si no está, fallback a time.time() con warning (deuda D-014).
            capture_ts=meta.get("capture_ts_unix_ms", time.time() * 1000) / 1000.0,
            zone_top=zg.get("zone_top", 0.0),
            zone_bottom=zg.get("zone_bottom", 0.0),
            zone_direction=zg.get("direction", "bullish"),
            zone_width_atr=zone_width_atr,
            atr_at_detection=cl.get("atr_at_detection", 1.0),
            lookahead_bars=lookahead,
            entry_price=l2.get("retest_price", 0.0),
            snapshot_path=snap_path,
            touch_sequence=touch_sequence,
            polarity_flipped=polarity_flipped,
            prior_touch_outcomes=list(prior_touch_outcomes or []),
            zone_original_direction=zone_original_direction
            or zg.get("direction", "bullish"),
            hours_since_flip=round(hours_since, 2),
        )

        self.pending.append(label)
        # Solo marcamos como visto tras persistir y encolar correctamente.
        self._seen_ids.add(sample_id)
        self._seen_fingerprints.add(fingerprint)
        self._persist_pending()

        logger.info(
            f"📋 Registered pending label: {sample_id} "
            f"(lookahead={lookahead} bars, direction={label.zone_direction})"
        )
        return sample_id

    def tick(
        self,
        current_price: float,
        bar_closed: bool = False,
        binance_ts_ms: float = None,
    ) -> List[dict]:
        """
        Llamar en cada update de precio (o al cierre de cada vela).
        Evalúa si algún pending label se resolvió.

        Args:
            current_price: precio actual (close de la vela o tick price)
            bar_closed: True si una vela acaba de cerrar (incrementa bars_elapsed)
            binance_ts_ms: timestamp de Binance event time en ms (D-014). Si se
                          provee, se usa para resolution_ts en lugar de time.time().

        Returns:
            Lista de samples resueltos en este tick (para logging/GUI)
        """
        newly_resolved = []

        for label in self.pending:
            if label.resolved:
                continue

            # Actualizar MFE/MAE
            mfe_updated = False
            if label.zone_direction == "bullish":
                favorable = current_price - label.entry_price
                adverse = label.entry_price - current_price
            else:
                favorable = label.entry_price - current_price
                adverse = current_price - label.entry_price

            if favorable > label.mfe:
                label.mfe = favorable
                mfe_updated = True

            if adverse > label.mae:
                label.mae = adverse
                mfe_updated = True

            if mfe_updated:
                # Journaling defensivo: guardar progreso para no perder MFE/MAE en reinicios
                self._persist_pending()

            if bar_closed:
                label.bars_elapsed += 1

            # Evaluar condiciones de resolución
            outcome = self._evaluate(label, current_price)
            if outcome is not None:
                label.resolved = True
                label.outcome = outcome
                # D-014: Usar binance_ts_ms si se provee, sino fallback a time.time()
                label.resolution_ts = (
                    binance_ts_ms / 1000.0 if binance_ts_ms is not None else time.time()
                )
                newly_resolved.append(label)
                logger.info(
                    f"🏷️ Label resolved: {label.sample_id} → {outcome} "
                    f"(MFE={label.mfe:.2f}, MAE={label.mae:.2f}, "
                    f"bars={label.bars_elapsed}/{label.lookahead_bars})"
                )

        if newly_resolved:
            flushed_ids = self._flush_resolved(newly_resolved)
            # Actualizar conjunto de IDs vistos para evitar re-registro tras flush satisfactorio
            for sid in flushed_ids:
                self._seen_ids.add(sid)
            # Liberar memoria: remover resueltos de la cola pending
            self.pending = [p for p in self.pending if not p.resolved]
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

    def _flush_resolved(self, resolved: List[PendingLabel]) -> List[str]:
        """Escribe samples resueltos en el dataset de entrenamiento v2."""
        path = Path(COMPLETED_SAMPLES_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        flushed_ids: List[str] = []

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
                    "mfe_atr": round(label.mfe / label.atr_at_detection, 4)
                    if label.atr_at_detection > 0
                    else 0.0,
                    "mae_atr": round(label.mae / label.atr_at_detection, 4)
                    if label.atr_at_detection > 0
                    else 0.0,
                    "bars_to_resolution": label.bars_elapsed,
                    "resolution_ts": label.resolution_ts,
                    "lookahead_bars_used": label.lookahead_bars,
                }

                snapshot["touch_context"] = {
                    "touch_sequence": label.touch_sequence,
                    "polarity_flipped": label.polarity_flipped,
                    "zone_original_direction": label.zone_original_direction,
                    "effective_direction": (
                        (
                            "bearish"
                            if label.zone_original_direction == "bullish"
                            else "bullish"
                        )
                        if label.polarity_flipped
                        else label.zone_original_direction
                    ),
                    "prior_touch_outcomes": label.prior_touch_outcomes,
                    "hours_since_flip": label.hours_since_flip,
                    "is_secondary_retest": label.touch_sequence > 1,
                    "is_tertiary_retest": label.touch_sequence > 2,
                }

                f.write(json.dumps(snapshot, default=str) + "\n")
                flushed_ids.append(label.sample_id)

        logger.info(
            f"💾 Flushed {len(flushed_ids)} resolved samples to {COMPLETED_SAMPLES_PATH}"
        )
        return flushed_ids

    def _persist_pending(self):
        """Guarda estado de pending labels para sobrevivir reinicios."""
        import dataclasses

        path = Path(PENDING_LABELS_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)

        pending_data = []
        for label in self.pending:
            if not label.resolved:
                pending_data.append(
                    {
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
                        "prior_touch_outcomes": [
                            dataclasses.asdict(tr)
                            if hasattr(tr, "__dataclass_fields__")
                            else tr
                            for tr in label.prior_touch_outcomes
                        ],
                        "zone_original_direction": label.zone_original_direction,
                        "hours_since_flip": label.hours_since_flip,
                    }
                )

        try:
            path.write_text(json.dumps(pending_data, indent=2))
            logger.debug(f"✅ Persistido: {path}")
        except TypeError as e:
            logger.critical(
                f"🔴 SERIALIZACIÓN FALLIDA en {path}: {e} — datos: {type(pending_data)}"
            )
            raise
        except IOError as e:
            logger.critical(f"🔴 ESCRITURA FALLIDA en {path}: {e}")
            raise

    def _load_pending(self):
        """Recarga pending labels sobrevivientes a un reinicio."""
        path = Path(PENDING_LABELS_PATH)
        if not path.exists():
            return

        try:
            data = json.loads(path.read_text())
            for item in data:
                # Compatibilidad hacia atrás: añadir defaults para campos nuevos
                item.setdefault("touch_sequence", 1)
                item.setdefault("polarity_flipped", False)
                item.setdefault("prior_touch_outcomes", [])
                item.setdefault(
                    "zone_original_direction", item.get("zone_direction", "")
                )
                item.setdefault("hours_since_flip", 0.0)
                self.pending.append(PendingLabel(**item))

            if self.pending:
                logger.info(
                    f"📋 Recovered {len(self.pending)} pending labels from disk."
                )
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"⚠️ Could not load pending labels: {e}")
